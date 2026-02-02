#!/usr/bin/env python3
"""
Jarvis Voice Assistant

Wake word activated voice assistant using:
- Pulse STT (WebSocket) for speech recognition
- Groq LLM for responses  
- Lightning TTS (WebSocket) for speech synthesis

Usage: python jarvis.py
"""

import asyncio
import json
import os
import queue
import re
import threading
import time
from urllib.parse import urlencode

import pyaudio
import websockets
from dotenv import load_dotenv

from llm import LLMClient
from tts import TTSWebSocket, chunk_text

load_dotenv()

WAKE_WORD = "jarvis"
SILENCE_TIMEOUT = 5.0
CONVERSATION_TIMEOUT = 60.0

STT_WS_URL = "wss://waves-api.smallest.ai/api/v1/pulse/get_text"
STT_SAMPLE_RATE = 16000
STT_LANGUAGE = "en"

CHUNK_SIZE = 1600
CHANNELS = 1
FORMAT = pyaudio.paInt16


class JarvisAssistant:
    """
    Wake word activated voice assistant.
    
    States:
        LISTENING: Waiting for wake word
        CAPTURING: Recording user query after wake word
        PROCESSING: Getting LLM response and speaking
    """

    def __init__(self):
        self.api_key = os.environ.get("SMALLEST_API_KEY")
        if not self.api_key:
            raise ValueError("SMALLEST_API_KEY environment variable not set")
        
        self.llm = LLMClient()

        self.state = "LISTENING"
        self.query_buffer = []
        self.conversation_history = []
        self.last_transcript_time = 0
        self.last_conversation_time = 0

        self.running = False
        self.jarvis_speaking = False
        self.silence_task = None
        self.timer_version = 0
        self.audio_queue = queue.Queue()

    async def run(self):
        self.running = True

        print("=" * 50)
        print("JARVIS VOICE ASSISTANT")
        print("=" * 50)
        print(f"Wake word: \"{WAKE_WORD}\"")
        print("Press Ctrl+C to exit.")
        print("-" * 50)
        print("[LISTENING] Waiting for wake word...")

        threading.Thread(target=self._capture_audio, daemon=True).start()

        while self.running:
            try:
                await self._stt_session()
            except websockets.exceptions.ConnectionClosed:
                print("[STT] Reconnecting...")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"[Error] {e}")
                await asyncio.sleep(1)

    def _capture_audio(self):
        """Capture microphone audio in a background thread."""
        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=STT_SAMPLE_RATE,
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

    async def _stt_session(self):
        """Establish STT WebSocket connection and handle audio streaming."""
        params = {"language": STT_LANGUAGE, "encoding": "linear16", "sample_rate": STT_SAMPLE_RATE}
        url = f"{STT_WS_URL}?{urlencode(params)}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with websockets.connect(url, additional_headers=headers, ping_interval=20) as ws:
            print("[STT] Connected")
            await asyncio.gather(self._send_audio(ws), self._receive_transcripts(ws))

    async def _send_audio(self, ws):
        """Send audio chunks to STT WebSocket. Pauses while Jarvis is speaking."""
        while self.running:
            if self.jarvis_speaking:
                while not self.audio_queue.empty():
                    self.audio_queue.get_nowait()
                await asyncio.sleep(0.05)
                continue

            while not self.audio_queue.empty():
                await ws.send(self.audio_queue.get_nowait())
            await asyncio.sleep(0.05)

    async def _receive_transcripts(self, ws):
        """Process incoming transcripts from STT WebSocket."""
        async for message in ws:
            if not self.running:
                break

            result = json.loads(message)
            transcript = result.get("transcript", "").strip()

            if not result.get("is_final") or not transcript:
                continue

            print(f"[STT] {transcript}")

            if self.state == "LISTENING":
                self._handle_wake_word(transcript)
            elif self.state == "CAPTURING":
                self._handle_capture(transcript)

    def _handle_wake_word(self, transcript: str):
        """Check for wake word and transition to CAPTURING state."""
        if WAKE_WORD not in transcript.lower():
            return

        print("\n[WAKE] Detected! Listening...")
        self.state = "CAPTURING"
        self.query_buffer = []
        self.conversation_history = []
        self.last_transcript_time = time.time()
        self.last_conversation_time = time.time()

        after = transcript.lower().split(WAKE_WORD, 1)[-1].strip()
        if after:
            self.query_buffer.append(after)
            print(f"[CAPTURE] {after}")

        self._restart_timer()

    def _handle_capture(self, transcript: str):
        """Add transcript to query buffer and reset silence timer."""
        clean = re.sub(rf"^.*{WAKE_WORD}", "", transcript.lower(), flags=re.IGNORECASE).strip()
        if clean:
            self.query_buffer.append(clean)
            print(f"[CAPTURE] {clean}")

        self.last_transcript_time = time.time()
        self._restart_timer()

    def _restart_timer(self):
        """Cancel existing silence timer and start a new one."""
        self.timer_version += 1
        my_version = self.timer_version

        if self.silence_task and not self.silence_task.done():
            self.silence_task.cancel()
        self.silence_task = asyncio.create_task(self._silence_check(my_version))

    async def _silence_check(self, my_version: int):
        """
        Wait for silence timeout, then process query if no new speech detected.
        
        Uses timer_version to handle race conditions when timer is restarted.
        """
        try:
            await asyncio.sleep(SILENCE_TIMEOUT)

            if self.timer_version != my_version:
                return

            if self.state != "CAPTURING":
                return

            if time.time() - self.last_transcript_time >= SILENCE_TIMEOUT - 0.1:
                if self.query_buffer:
                    await self._process_query()
                elif time.time() - self.last_conversation_time > CONVERSATION_TIMEOUT:
                    print("\n[TIMEOUT] Returning to wake word detection...")
                    self.state = "LISTENING"
                    self.conversation_history = []
                    print("[LISTENING] Waiting for wake word...")
                else:
                    self._restart_timer()
        except asyncio.CancelledError:
            pass

    async def _process_query(self):
        """Send query to LLM and speak response via TTS."""
        query = " ".join(self.query_buffer).strip()
        self.query_buffer = []

        if not query:
            self.state = "CAPTURING"
            self._restart_timer()
            return

        if time.time() - self.last_conversation_time > CONVERSATION_TIMEOUT:
            self.conversation_history = []

        self.state = "PROCESSING"
        print(f"\n[QUERY] {query}")
        self.jarvis_speaking = True

        response, is_stop = self.llm.get_response(query, self.conversation_history)

        if is_stop:
            print("[STOP] Ignoring unrelated speech")
            self.jarvis_speaking = False
            self.state = "CAPTURING"
            self.last_transcript_time = time.time()
            self._restart_timer()
            return

        print(f"[RESPONSE] {response}")

        tts = TTSWebSocket()
        try:
            await tts.connect()
            await tts.speak_all(chunk_text(response, n=10))
        finally:
            await tts.close()
            while not self.audio_queue.empty():
                self.audio_queue.get_nowait()
            self.jarvis_speaking = False

        self.conversation_history.append({"role": "user", "content": query})
        self.conversation_history.append({"role": "assistant", "content": response})

        self.last_conversation_time = time.time()
        self.state = "CAPTURING"
        self.last_transcript_time = time.time()
        self._restart_timer()
        print("[LISTENING] Ready for follow-up...")

    def stop(self):
        """Stop the assistant."""
        self.running = False


def main():
    try:
        assistant = JarvisAssistant()
        asyncio.run(assistant.run())
    except ValueError as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\n[EXIT] Goodbye!")


if __name__ == "__main__":
    main()
