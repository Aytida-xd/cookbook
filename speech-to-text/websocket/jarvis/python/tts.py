"""Lightning TTS WebSocket client."""

import asyncio
import base64
import json
import os
import queue
import threading

import pyaudio
import websockets

TTS_WS_URL = "wss://waves-api.smallest.ai/api/v1/lightning-v3.1/get_speech/stream"
TTS_VOICE = "sophia"
TTS_SAMPLE_RATE = 24000


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

        async def send():
            for i, chunk in enumerate(chunks):
                print(f"[TTS] {i+1}/{len(chunks)}: {chunk}")
                await self.ws.send(json.dumps({
                    "text": chunk,
                    "voice_id": self.voice,
                    "sample_rate": self.sample_rate,
                    "speed": 1.0,
                }))

        async def receive():
            while True:
                try:
                    response = await asyncio.wait_for(self.ws.recv(), timeout=30.0)
                    data = json.loads(response)

                    if data.get("status") == "error":
                        print(f"[TTS ERROR] {data}")
                        break

                    audio = data.get("data", {}).get("audio")
                    if audio:
                        self.audio_queue.put(base64.b64decode(audio))

                    if data.get("status") == "complete":
                        print("[TTS] Complete")
                        break
                except asyncio.TimeoutError:
                    print("[TTS] Timeout")
                    break
                except Exception as e:
                    print(f"[TTS Error] {e}")
                    break

        await asyncio.gather(send(), receive())

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
