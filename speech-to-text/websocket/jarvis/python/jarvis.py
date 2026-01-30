#!/usr/bin/env python3
"""
Smallest AI Jarvis - Voice Assistant

Always-on voice assistant that listens for "Jarvis" wake word,
transcribes your query, sends it to an LLM, and speaks the response.

Usage: python jarvis.py

Terminology:
- Partial transcript: is_final=false (ignored for processing)
- Transcript: is_final=true (used for wake word detection and query capture)

Pipeline:
1. Continuous microphone → Pulse STT (WebSocket)
2. Wake word detection in transcripts
3. Query capture (accumulate transcripts until silence)
4. LLM response (GPT-4o)
5. TTS playback (Lightning v3.1)
6. Return to wake word detection

API References:
- Pulse STT WebSocket: https://waves-docs.smallest.ai/v4.0.0/content/api-references/pulse-asr
- Lightning TTS: https://waves-docs.smallest.ai/v4.0.0/content/api-references/lightning-tts
"""

import asyncio
import json
import os
import re
import sys
import threading
import queue
import time
from urllib.parse import urlencode

import pyaudio
import websockets
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

WAKE_WORD = "jarvis"
SILENCE_TIMEOUT = 4.0

STT_WS_URL = "wss://waves-api.smallest.ai/api/v1/pulse/get_text"
STT_SAMPLE_RATE = 16000
STT_LANGUAGE = "en"

TTS_API_URL = "https://waves-api.smallest.ai/api/v1/lightning/get_speech"
TTS_MODEL = "lightning"
TTS_VOICE = "emily"
TTS_SAMPLE_RATE = 24000

LLM_MODEL = "gpt-4o"
LLM_SYSTEM_PROMPT = """You are Jarvis, a helpful AI assistant.

IMPORTANT: Start EVERY response with exactly one of these words:
- "SPEAK:" if the user's message is a question/command directed at you OR a follow-up to the conversation
- "STOP:" if the user's message is unrelated background speech, talking to someone else, or not meant for you

After the prefix, provide your response. Keep responses concise (1-3 sentences).

Examples:
User: "What's the weather like?"
Response: "SPEAK: I don't have access to weather data, but you can check your phone's weather app."

User: "The tomoato is read"
Response: "STOP: (unrelated conversation)"
Such a respsonse because tomato is not related to the conversation of weather.

User: "Yeah I'll be there in 5 minutes"
Response: "STOP: (unrelated conversation)"

User: "Tell me more about that"
Response: "SPEAK: Sure! [continues previous topic]"
Unless the user is explicitly asking a question on an unrelated topic, respond with "STOP: (unrelated conversation)".
"""

CONVERSATION_TIMEOUT = 30.0

CHUNK_SIZE = 1600
CHANNELS = 1
FORMAT = pyaudio.paInt16


def text_to_speech(text: str, api_key: str) -> bytes:
    """Convert text to speech using Smallest AI Lightning TTS."""
    import requests
    
    response = requests.post(
        TTS_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "voice_id": TTS_VOICE,
            "sample_rate": TTS_SAMPLE_RATE,
            "model": TTS_MODEL,
        },
        timeout=30,
    )
    
    if response.status_code != 200:
        print(f"[TTS Error] {response.status_code}: {response.text}")
        return b""
    
    return response.content


def play_audio(audio_bytes: bytes):
    """Play audio bytes through speakers."""
    if not audio_bytes:
        return
        
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=TTS_SAMPLE_RATE,
        output=True,
    )
    
    stream.write(audio_bytes)
    stream.stop_stream()
    stream.close()
    p.terminate()


def get_llm_response(query: str, openai_client: OpenAI, conversation_history: list) -> str:
    """Get LLM response for the user's query with conversation context."""
    try:
        user_content = ""
        
        if conversation_history:
            history_text = "\n".join(
                f"{'User' if msg['role'] == 'user' else 'Jarvis'}: {msg['content']}"
                for msg in conversation_history
            )
            user_content = f"CONVERSATION HISTORY:\n{history_text}\n\nCURRENT QUERY: {query}"
        else:
            user_content = f"CURRENT QUERY: {query}"
        
        messages = [
            {"role": "system", "content": LLM_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
        
        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            max_tokens=256,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[LLM Error] {e}")
        return "SPEAK: I'm sorry, I couldn't process that request."


class JarvisAssistant:
    """
    Voice assistant that listens for wake word and processes queries.
    
    States: LISTENING → CAPTURING → PROCESSING → CAPTURING (for follow-ups) → LISTENING
    """
    
    def __init__(self, smallest_api_key: str, openai_api_key: str):
        self.smallest_api_key = smallest_api_key
        self.openai_client = OpenAI(api_key=openai_api_key)
        
        self.state = "LISTENING"
        self.query_buffer = []
        self.last_transcript_time = 0
        self.last_conversation_time = 0
        self.conversation_history = []
        self.running = False
        self.is_speaking = False
        
        self.audio_queue = queue.Queue()
        
    async def run(self):
        """Main loop: connect to STT and process transcriptions."""
        self.running = True
        
        print("=" * 60)
        print("🤖 JARVIS VOICE ASSISTANT")
        print("=" * 60)
        print(f"Wake word: \"{WAKE_WORD}\"")
        print("Say the wake word followed by your question.")
        print("Press Ctrl+C to exit.")
        print("-" * 60)
        print("[LISTENING] Waiting for wake word...")
        
        audio_thread = threading.Thread(target=self._capture_audio, daemon=True)
        audio_thread.start()
        
        while self.running:
            try:
                await self._stt_session()
            except websockets.exceptions.ConnectionClosed:
                print("[STT] Connection closed, reconnecting...")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"[Error] {e}")
                await asyncio.sleep(1)
    
    def _capture_audio(self):
        """Capture microphone audio in a separate thread."""
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
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                self.audio_queue.put(data)
            except Exception as e:
                print(f"[Audio Error] {e}")
                break
        
        stream.stop_stream()
        stream.close()
        p.terminate()
    
    async def _stt_session(self):
        """Run a single STT WebSocket session."""
        params = {
            "language": STT_LANGUAGE,
            "encoding": "linear16",
            "sample_rate": STT_SAMPLE_RATE,
        }
        url = f"{STT_WS_URL}?{urlencode(params)}"
        headers = {"Authorization": f"Bearer {self.smallest_api_key}"}
        
        print(f"[WS] Connecting to {STT_WS_URL}...")
        async with websockets.connect(
            url, 
            additional_headers=headers,
            ping_interval=20,
            ping_timeout=10,
        ) as ws:
            print("[WS] Connected successfully!")
            send_task = asyncio.create_task(self._send_audio(ws))
            receive_task = asyncio.create_task(self._receive_transcripts(ws))
            
            done, pending = await asyncio.wait(
                [send_task, receive_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            
            for task in done:
                if task.exception():
                    print(f"[WS] Task ended with error: {task.exception()}")
                else:
                    print("[WS] Task ended normally")
            
            for task in pending:
                task.cancel()
    
    async def _send_audio(self, ws):
        """Send audio chunks to WebSocket."""
        while self.running:
            try:
                if self.is_speaking:
                    while not self.audio_queue.empty():
                        self.audio_queue.get_nowait()
                    await asyncio.sleep(0.05)
                    continue
                
                while not self.audio_queue.empty():
                    chunk = self.audio_queue.get_nowait()
                    await ws.send(chunk)
                await asyncio.sleep(0.05)
            except Exception:
                break
    
    async def _receive_transcripts(self, ws):
        """Receive and process transcription responses."""
        try:
            async for message in ws:
                if not self.running:
                    break
                
                result = json.loads(message)
                transcript = result.get("transcript", "").strip()
                is_final = result.get("is_final", False)
                
                if not is_final or not transcript:
                    continue
                
                print(f"[STT] {transcript}")
                
                if self.state == "LISTENING":
                    await self._check_wake_word(transcript)
                elif self.state == "CAPTURING":
                    await self._capture_query(transcript)
                
        except Exception as e:
            print(f"[WS RECV] Error: {e}")
    
    async def _check_wake_word(self, transcript: str):
        """Check if transcript contains the wake word."""
        text_lower = transcript.lower()
        
        if WAKE_WORD in text_lower:
            print(f"\n[WAKE WORD] Detected! Listening for your query...")
            self.state = "CAPTURING"
            self.query_buffer = []
            self.conversation_history = []
            self.last_transcript_time = time.time()
            self.last_conversation_time = time.time()
            
            after_wake = text_lower.split(WAKE_WORD, 1)[-1].strip()
            if after_wake:
                self.query_buffer.append(after_wake)
                print(f"[CAPTURING] Added: \"{after_wake}\"")
            
            asyncio.create_task(self._check_silence())
    
    async def _capture_query(self, transcript: str):
        """Capture the user's query after wake word, process after silence."""
        clean = re.sub(rf"^.*{WAKE_WORD}", "", transcript.lower(), flags=re.IGNORECASE).strip()
        if clean:
            self.query_buffer.append(clean)
            print(f"[CAPTURING] Added: \"{clean}\"")
        
        self.last_transcript_time = time.time()
        asyncio.create_task(self._check_silence())
    
    async def _check_silence(self):
        """Check if user has stopped speaking (silence detected)."""
        await asyncio.sleep(SILENCE_TIMEOUT)
        
        if self.state == "CAPTURING":
            elapsed = time.time() - self.last_transcript_time
            if elapsed >= SILENCE_TIMEOUT:
                if self.query_buffer:
                    await self._process_query()
                elif time.time() - self.last_conversation_time > CONVERSATION_TIMEOUT:
                    print("\n[TIMEOUT] No activity, returning to wake word detection...")
                    self.state = "LISTENING"
                    self.conversation_history = []
                    print("[LISTENING] Waiting for wake word...")
    
    async def _process_query(self):
        """Process the captured query through LLM and TTS."""
        query = " ".join(self.query_buffer).strip()
        self.query_buffer = []
        
        if not query:
            print("[QUERY] Empty query, continuing to listen...")
            self.state = "CAPTURING"
            self.last_transcript_time = time.time()
            asyncio.create_task(self._check_silence())
            return
        
        if time.time() - self.last_conversation_time > CONVERSATION_TIMEOUT:
            self.conversation_history = []
            print("[CONTEXT] Conversation reset (timeout)")
        
        self.state = "PROCESSING"
        print(f"\n[QUERY] \"{query}\"")
        print("[LLM] Thinking...")
        
        response = await asyncio.to_thread(
            get_llm_response, query, self.openai_client, self.conversation_history
        )
        print(f"[LLM RAW] {response}")
        
        if response.upper().startswith("SPEAK:"):
            speech_text = response[6:].strip()
            print(f"[RESPONSE] {speech_text}")
            
            self.conversation_history.append({"role": "user", "content": query})
            self.conversation_history.append({"role": "assistant", "content": speech_text})
            
            print("[TTS] Speaking...")
            audio = text_to_speech(speech_text, self.smallest_api_key)
            self._play_and_clear(audio)
            
            self.last_conversation_time = time.time()
            self.state = "CAPTURING"
            self.last_transcript_time = time.time()
            asyncio.create_task(self._check_silence())
            print("[CAPTURING] Listening for follow-up...")
            
        elif response.upper().startswith("STOP:"):
            print("[STOP] Unrelated speech, ignoring...")
            self.state = "CAPTURING"
            self.last_transcript_time = time.time()
            asyncio.create_task(self._check_silence())
            
        else:
            speech_text = response.strip()
            print(f"[RESPONSE] {speech_text}")
            
            self.conversation_history.append({"role": "user", "content": query})
            self.conversation_history.append({"role": "assistant", "content": speech_text})
            
            print("[TTS] Speaking...")
            audio = text_to_speech(speech_text, self.smallest_api_key)
            self._play_and_clear(audio)
            
            self.last_conversation_time = time.time()
            self.state = "CAPTURING"
            self.last_transcript_time = time.time()
            asyncio.create_task(self._check_silence())
            print("[CAPTURING] Listening for follow-up...")
    
    def _play_and_clear(self, audio: bytes):
        """Play audio and clear any captured TTS echo from the queue."""
        self.is_speaking = True
        play_audio(audio)
        time.sleep(0.5)
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except:
                break
        self.is_speaking = False
    
    def stop(self):
        """Stop the assistant."""
        self.running = False


def main():
    smallest_api_key = os.environ.get("SMALLEST_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    if not smallest_api_key:
        print("Error: SMALLEST_API_KEY environment variable not set")
        print("Get your key at: https://console.smallest.ai/apikeys")
        sys.exit(1)
    
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Get your key at: https://platform.openai.com/api-keys")
        sys.exit(1)
    
    assistant = JarvisAssistant(smallest_api_key, openai_api_key)
    
    try:
        asyncio.run(assistant.run())
    except KeyboardInterrupt:
        print("\n\n[EXIT] Goodbye!")
        assistant.stop()


if __name__ == "__main__":
    main()
