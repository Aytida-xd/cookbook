#!/usr/bin/env python3
"""
Jarvis Voice Assistant

A wake word activated voice assistant demonstrating how to build voice assistants
with Smallest AI's speech APIs.

Architecture:
- STT: WebSocket streaming for low-latency transcription (stt.py)
- LLM: Groq API with vision support for screenshots (llm.py)
- TTS: HTTP POST for simplicity - upgrade to WebSocket for lower latency (tts.py)

State Machine:
- LISTENING: Waiting for wake word "Jarvis"
- CAPTURING: Recording user's query until silence
- PROCESSING: Getting LLM response and speaking it

Usage: python jarvis.py
"""

import asyncio
import json
import re
import time

from dotenv import load_dotenv

from llm import LLMClient
from stt import STTClient
from tts import TTSClient

load_dotenv()

# Configuration - customize these for your use case
WAKE_WORD = "jarvis"
SILENCE_TIMEOUT = 5.0       # Seconds of silence to end query capture
CONVERSATION_TIMEOUT = 60.0  # Seconds before resetting conversation context


class JarvisAssistant:
    """
    Wake word activated voice assistant.
    
    States:
        LISTENING: Waiting for wake word
        CAPTURING: Recording user query after wake word
        PROCESSING: Getting LLM response and speaking
    """

    def __init__(self):
        self.llm = LLMClient()
        self.stt = STTClient()

        self.state = "LISTENING"
        self.query_buffer = []
        self.conversation_history = []
        self.last_transcript_time = 0
        self.last_conversation_time = 0

        self.running = False
        self.jarvis_speaking = False
        self.silence_task = None
        self.timer_version = 0

    async def run(self):
        """Start the voice assistant main loop."""
        self.running = True

        print("=" * 50)
        print("JARVIS VOICE ASSISTANT")
        print("=" * 50)
        print(f"Wake word: \"{WAKE_WORD}\"")
        print("Press Ctrl+C to exit.")
        print("-" * 50)
        print("[LISTENING] Waiting for wake word...")

        while self.running:
            try:
                await self._stt_session()
            except Exception as e:
                print(f"[STT] Reconnecting... ({e})")
                await asyncio.sleep(1)

    async def _stt_session(self):
        """Run STT session with send/receive loop."""
        await self.stt.connect()

        async def send_audio():
            while self.running:
                if self.jarvis_speaking:
                    self.stt.clear_queue()
                    await asyncio.sleep(0.05)
                    continue

                while not self.stt.audio_queue.empty():
                    await self.stt.ws.send(self.stt.audio_queue.get_nowait())
                await asyncio.sleep(0.05)

        async def receive_transcripts():
            async for message in self.stt.ws:
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

        try:
            await asyncio.gather(send_audio(), receive_transcripts())
        finally:
            await self.stt.close()

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
        """Wait for silence timeout, then process query if no new speech detected."""
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
                    print("\n[TIMEOUT] Erasing context and returning to wake word detection...")
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

        tts = TTSClient()
        try:
            tts.start()
            await tts.speak(response)
        finally:
            tts.stop()
            self.stt.clear_queue()
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
