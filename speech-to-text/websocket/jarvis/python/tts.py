"""Lightning TTS WebSocket client."""

import asyncio
import base64
import json
import os
import queue
import threading
import time as time_module

import pyaudio
import websockets

TTS_WS_URL = "wss://waves-api.smallest.ai/api/v1/lightning-v3.1/get_speech/stream"
TTS_VOICE = "sophia"
TTS_SAMPLE_RATE = 24000
DEBUG_AUDIO_DIR = "debug_audio"


class TTSWebSocket:
    """
    TTS WebSocket client with concurrent send/receive.
    
    Sends text chunks to the TTS API and plays received audio
    in a background thread for low-latency playback.
    """

    def __init__(self, voice: str = TTS_VOICE, sample_rate: int = TTS_SAMPLE_RATE):
        api_key = os.environ.get("SMALLEST_API_KEY")
        if not api_key:
            raise ValueError("SMALLEST_API_KEY environment variable not set")
        self.api_key = api_key
        self.voice = voice
        self.sample_rate = sample_rate
        self.ws = None
        self.audio_queue = queue.Queue()
        self.playback_thread = None
        self.pyaudio_instance = None
        self.audio_stream = None
        self.stop_playback = False

    def _play_audio(self):
        """Background thread that plays audio from the queue."""
        while not self.stop_playback:
            try:
                data = self.audio_queue.get(timeout=0.1)
                if data is None:
                    break
                self.audio_stream.write(data)
            except queue.Empty:
                continue

    async def connect(self):
        """Connect to TTS WebSocket and initialize audio playback."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        self.ws = await websockets.connect(TTS_WS_URL, additional_headers=headers)

        self.pyaudio_instance = pyaudio.PyAudio()
        self.audio_stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            output=True,
        )

        self.stop_playback = False
        self.playback_thread = threading.Thread(target=self._play_audio, daemon=True)
        self.playback_thread.start()
        print("[TTS] Connected")

    async def speak_all(self, chunks: list):
        """
        Send all text chunks and receive audio concurrently.
        
        Sends chunks to TTS API while simultaneously receiving and
        queueing audio for playback. Waits for playback to complete.
        """
        if not chunks:
            return

        send_complete = asyncio.Event()

        async def send():
            for i, chunk in enumerate(chunks):
                await self.ws.send(json.dumps({
                    "text": chunk,
                    "voice_id": self.voice,
                    "sample_rate": self.sample_rate,
                    "speed": 1.0,
                }))
                print(f"[TTS] Sent {i+1}/{len(chunks)}: {chunk}")
                await asyncio.sleep(0.05)
            send_complete.set()

        all_audio_bytes = []

        async def receive():
            import time
            first_audio = True
            start_time = time.time()
            audio_chunks = 0
            
            while True:
                try:
                    response = await asyncio.wait_for(self.ws.recv(), timeout=30.0)
                    data = json.loads(response)

                    if data.get("status") == "error":
                        print(f"[TTS ERROR] {data}")
                        break

                    audio = data.get("data", {}).get("audio")
                    if audio:
                        if first_audio:
                            print(f"[TTS] First audio: {(time.time() - start_time)*1000:.0f}ms")
                            first_audio = False
                        audio_chunks += 1
                        decoded = base64.b64decode(audio)
                        all_audio_bytes.append(decoded)
                        self.audio_queue.put(decoded)

                    if data.get("status") == "complete":
                        if not send_complete.is_set():
                            print(f"[TTS] Warning: complete received before all chunks sent")
                        print(f"[TTS] Complete ({audio_chunks} chunks, {(time.time() - start_time)*1000:.0f}ms)")
                        # break
                except asyncio.TimeoutError:
                    print("[TTS] Timeout")
                    break
                except Exception as e:
                    print(f"[TTS Error] {e}")
                    break

        await asyncio.gather(send(), receive())

        # Save debug audio file
        if all_audio_bytes:
            os.makedirs(DEBUG_AUDIO_DIR, exist_ok=True)
            timestamp = time_module.strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(DEBUG_AUDIO_DIR, f"tts_{timestamp}.raw")
            with open(filepath, "wb") as f:
                f.write(b"".join(all_audio_bytes))
            print(f"[TTS] Debug audio saved: {filepath}")

        while not self.audio_queue.empty():
            await asyncio.sleep(0.1)
        await asyncio.sleep(0.3)

    async def close(self):
        """Close WebSocket connection and clean up audio resources."""
        self.stop_playback = True
        self.audio_queue.put(None)

        if self.playback_thread:
            self.playback_thread.join(timeout=2.0)
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
        if self.ws:
            await self.ws.close()


def chunk_text(text: str, n: int = 10) -> list[str]:
    """Split text into chunks of n words for TTS processing."""
    words = text.split()
    return [" ".join(words[i:i+n]) for i in range(0, len(words), n)]
