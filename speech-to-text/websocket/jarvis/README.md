# Jarvis Voice Assistant

Always-on voice assistant powered by Smallest AI. Say "Jarvis" followed by your question to get a spoken response. Supports follow-up questions within a conversation session.

## Pipeline

```
Microphone → Pulse STT (WebSocket) → Wake Word Detection → LLM (Groq) → Lightning TTS (WebSocket) → Speaker
```

## Requirements

```bash
pip install -r python/requirements.txt
```

**System dependency:** PortAudio (required by PyAudio)

```bash
# Ubuntu/Debian
sudo apt install portaudio19-dev

# macOS
brew install portaudio
```

## Setup

```bash
cp .env.sample .env
# Edit .env with your API keys
```

## Usage

```bash
python python/jarvis.py
```

## How It Works

1. **Continuous Listening**: Microphone audio streams to Pulse STT via WebSocket
2. **Wake Word Detection**: Listens for "Jarvis" in transcriptions
3. **Query Capture**: After wake word, collects speech until 5 seconds of silence
4. **LLM Response**: Query sent to Groq (Llama 3.3 70B) with conversation context
5. **TTS Playback**: Response spoken via Lightning TTS v3.1 with concurrent streaming
6. **Follow-up**: Stays in conversation mode for 30 seconds, allowing follow-up questions without wake word

## Project Structure

```
python/
├── jarvis.py      # Main assistant (STT, wake word, state machine)
├── llm.py         # Groq LLM client with context management
├── tts.py         # Lightning TTS WebSocket client
└── requirements.txt
```

## Configuration

| File | Variable | Default | Description |
|------|----------|---------|-------------|
| `jarvis.py` | `WAKE_WORD` | `"jarvis"` | Trigger phrase (case-insensitive) |
| `jarvis.py` | `SILENCE_TIMEOUT` | `5.0` | Seconds of silence to end query |
| `jarvis.py` | `CONVERSATION_TIMEOUT` | `30.0` | Seconds before returning to wake word mode |
| `tts.py` | `TTS_VOICE` | `"sophia"` | Lightning TTS voice ID |
| `llm.py` | `LLM_MODEL` | `"llama-3.3-70b-versatile"` | Groq model |

## Example Output

```
==================================================
JARVIS VOICE ASSISTANT
==================================================
Wake word: "jarvis"
Press Ctrl+C to exit.
--------------------------------------------------
[LISTENING] Waiting for wake word...
[STT] Hey Jarvis what is the capital of France

[WAKE] Detected! Listening...
[CAPTURE] what is the capital of france

[QUERY] what is the capital of france
[LLM] Response in 245ms
[RESPONSE] The capital of France is Paris.
[TTS] Connected
[TTS] 1/1: The capital of France is Paris.
[TTS] Complete
[LISTENING] Ready for follow-up...
[STT] and what about Germany

[CAPTURE] and what about germany

[QUERY] and what about germany
[LLM] Response in 198ms
[RESPONSE] The capital of Germany is Berlin.
...
```

## API References

- [Pulse STT WebSocket](https://waves-docs.smallest.ai/content/api-references/pulse-asr)
- [Lightning TTS](https://waves-docs.smallest.ai/content/api-references/lightning-tts)
- [Groq API](https://console.groq.com/docs/api-reference)
