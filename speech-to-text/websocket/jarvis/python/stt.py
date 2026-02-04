"""Pulse STT WebSocket client."""

import asyncio
import json
import os
import queue
import threading
from urllib.parse import urlencode

import pyaudio
import websockets

STT_WS_URL = "wss://waves-api.smallest.ai/api/v1/pulse/get_text"
STT_SAMPLE_RATE = 16000
STT_LANGUAGE = "en"

CHUNK_SIZE = 1600
CHANNELS = 1
FORMAT = pyaudio.paInt16


class STTWebSocket:
    """STT WebSocket client with microphone capture."""

    def __init__(self, language: str = STT_LANGUAGE, sample_rate: int = STT_SAMPLE_RATE):
        api_key = os.environ.get("SMALLEST_API_KEY")
        if not api_key:
            raise ValueError("SMALLEST_API_KEY environment variable not set")
        self.api_key = api_key
        self.language = language
        self.sample_rate = sample_rate
        self.ws = None
        self.audio_queue = queue.Queue()
        self.running = False
        self.paused = False
        self.capture_thread = None

    def _capture_audio(self):
        """Capture microphone audio in a background thread."""
        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )

        while self.running:
            try:
                self.audio_queue.put(stream.read(CHUNK_SIZE, exception_on_overflow=False))
            except Exception as e:
                print(f"[Audio Error] {e}")
                break

        stream.stop_stream()
        stream.close()
        p.terminate()

    async def connect(self):
        """Connect to STT WebSocket."""
        params = {
            "language": self.language,
            "encoding": "linear16",
            "sample_rate": self.sample_rate,
        }
        url = f"{STT_WS_URL}?{urlencode(params)}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        self.ws = await websockets.connect(url, additional_headers=headers, ping_interval=20)
        self.running = True

        self.capture_thread = threading.Thread(target=self._capture_audio, daemon=True)
        self.capture_thread.start()
        print("[STT] Connected")

    async def send_audio(self):
        """Send audio chunks to STT WebSocket. Skips while paused."""
        while self.running:
            if self.paused:
                while not self.audio_queue.empty():
                    self.audio_queue.get_nowait()
                await asyncio.sleep(0.05)
                continue

            while not self.audio_queue.empty():
                await self.ws.send(self.audio_queue.get_nowait())
            await asyncio.sleep(0.05)

    async def receive_transcripts(self, on_transcript):
        """Process incoming transcripts. Calls on_transcript(transcript, is_final)."""
        async for message in self.ws:
            if not self.running:
                break

            result = json.loads(message)
            transcript = result.get("transcript", "").strip()
            is_final = result.get("is_final", False)

            if transcript:
                on_transcript(transcript, is_final)

    def pause(self):
        """Pause audio capture (e.g., while TTS is speaking)."""
        self.paused = True

    def resume(self):
        """Resume audio capture."""
        self.paused = False

    def clear_queue(self):
        """Clear any buffered audio."""
        while not self.audio_queue.empty():
            self.audio_queue.get_nowait()

    async def close(self):
        """Close WebSocket connection."""
        self.running = False
        if self.ws:
            await self.ws.close()
