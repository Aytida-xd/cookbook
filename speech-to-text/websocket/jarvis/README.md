# Jarvis Voice Assistant

Always-on voice assistant powered by Smallest AI. Say "Hey Jarvis" followed by your question to get a spoken response.

## Pipeline

```
Microphone → Pulse STT (WebSocket) → Wake Word Detection → LLM (Groq) → Lightning TTS → Speaker
```

## Requirements

```bash
pip install websockets pyaudio numpy groq python-dotenv requests
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

### Run in Foreground

```bash
python python/jarvis.py
```

### Run in Background

```bash
# Start in background
nohup python python/jarvis.py > jarvis.log 2>&1 &

# View logs
tail -f jarvis.log

# Stop
pkill -f "python python/jarvis.py"
```

### Run with systemd (Linux)

Create `/etc/systemd/system/jarvis.service`:

```ini
[Unit]
Description=Jarvis Voice Assistant
After=network.target sound.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/jarvis
Environment="SMALLEST_API_KEY=your-key"
Environment="GROQ_API_KEY=your-key"
ExecStart=/usr/bin/python3 python/jarvis.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable jarvis
sudo systemctl start jarvis
sudo journalctl -u jarvis -f  # View logs
```

## How It Works

1. **Continuous Listening**: Microphone audio streams to Pulse STT via WebSocket
2. **Wake Word Detection**: Listens for "Hey Jarvis" in transcriptions
3. **Query Capture**: After wake word, collects speech until 2 seconds of silence
4. **LLM Response**: Query sent to Groq (Llama 3.3) for a concise answer
5. **TTS Playback**: Response spoken aloud via Lightning TTS v3.1

## Configuration

Edit `python/jarvis.py` to customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `WAKE_WORD` | `"hey jarvis"` | Trigger phrase (case-insensitive) |
| `SILENCE_TIMEOUT` | `2.0` | Seconds of silence to end query |
| `TTS_VOICE` | `"emily"` | Lightning TTS voice ID |
| `LLM_MODEL` | `"llama-3.3-70b-versatile"` | Groq model |

## Output

```
============================================================
🤖 JARVIS VOICE ASSISTANT
============================================================
Wake word: "hey jarvis"
Say the wake word followed by your question.
Press Ctrl+C to exit.
------------------------------------------------------------
[LISTENING] Waiting for wake word...

[WAKE WORD] Detected! Listening for your query...

[QUERY] "what's the weather like today"
[LLM] Thinking...
[RESPONSE] I don't have access to real-time weather data, but you can check your local weather app or website for the current conditions in your area.
[TTS] Speaking...

[LISTENING] Waiting for wake word...
```

## API References

- [Authentication](https://waves-docs.smallest.ai/v4.0.0/content/api-references/authentication)
- [Pulse STT WebSocket](https://waves-docs.smallest.ai/v4.0.0/content/api-references/pulse-asr)
- [Lightning TTS](https://waves-docs.smallest.ai/v4.0.0/content/api-references/lightning-tts)
- [Groq API](https://console.groq.com/docs/api-reference)



