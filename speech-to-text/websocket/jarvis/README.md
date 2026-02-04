# Jarvis Voice Assistant

A background AI assistant powered by Smallest AI that can understand what's on your screen through screenshots.

Say "Jarvis" followed by your question to get a spoken response. Mention "screenshot" in your query, and Jarvis will prompt you to capture part of your screen for visual context.

## Features

- **Wake Word Activation**: Triggered by saying "Jarvis"
- **Screenshot Analysis**: Say "screenshot" to capture and analyze part of your screen
- **Conversation Memory**: Stores previous context for follow-up questions
- **Voice Response**: Speaks responses aloud via TTS

## Pipeline

```
Microphone → Pulse STT → Wake Word → [Screenshot?] → Vision + LLM → TTS → Speaker
```

## Requirements

```bash
pip install -r python/requirements.txt
```

**System dependencies:**

```bash
# Ubuntu/Debian
sudo apt install portaudio19-dev flameshot

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
3. **Query Capture**: Collects speech until 5 seconds of silence
4. **Screenshot (Optional)**: If query contains "screenshot":
   - Opens native screenshot tool (flameshot/scrot/etc.)
   - Select the region you want to capture
   - Press Enter or click to confirm
   - Vision model extracts text and describes the image
5. **LLM Response**: Query + image context sent to Groq (Llama 3.3 70B)
6. **TTS Playback**: Response spoken via Lightning TTS
7. **Follow-up**: Stays in conversation mode for 60 seconds - you can ask follow-ups on the screenshot or previous responses

## Screenshot Example

```
[LISTENING] Waiting for wake word...
[STT] Jarvis take a screenshot and explain this code

[WAKE] Detected! Listening...
[CAPTURE] take a screenshot and explain this code

[QUERY] take a screenshot and explain this code
[LLM] Screenshot requested...
[Vision] 1200ms
[LLM] 450ms
[RESPONSE] This is a Python function that calculates fibonacci numbers using recursion...
[TTS] Connected
...
[LISTENING] Ready for follow-up...
[STT] How can I optimize it

[CAPTURE] how can i optimize it

[QUERY] how can i optimize it
[LLM] 380ms
[RESPONSE] You can optimize it using memoization or convert it to an iterative approach...
```

## Project Structure

```
python/
├── jarvis.py        # Main assistant (wake word, state machine)
├── stt.py           # Pulse STT WebSocket client
├── llm.py           # Groq LLM + vision with screenshot support
├── tts.py           # Lightning TTS WebSocket client
└── requirements.txt
```

## Configuration

| File | Variable | Default | Description |
|------|----------|---------|-------------|
| `jarvis.py` | `WAKE_WORD` | `"jarvis"` | Trigger phrase (case-insensitive) |
| `jarvis.py` | `SILENCE_TIMEOUT` | `5.0` | Seconds of silence to end query |
| `jarvis.py` | `CONVERSATION_TIMEOUT` | `60.0` | Seconds before returning to wake word mode |
| `tts.py` | `TTS_VOICE` | `"sophia"` | Lightning TTS voice ID |
| `llm.py` | `LLM_MODEL` | `"llama-3.3-70b-versatile"` | Text model |
| `llm.py` | `LLM_VISION_MODEL` | `"llama-4-scout-17b-16e"` | Vision model for screenshots |

## API References

- [Pulse STT WebSocket](https://waves-docs.smallest.ai/content/api-references/pulse-asr)
- [Lightning TTS](https://waves-docs.smallest.ai/content/api-references/lightning-tts)
- [Groq API](https://console.groq.com/docs/api-reference)
