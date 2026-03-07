# Snippets

Reusable code snippets for combining LangChain with Smallest AI's STT and TTS. Copy-paste these into your projects.

## Structure

```
snippets/
├── stt_tool.py      # Pulse STT as a LangChain Tool (minimal, copy-paste ready)
├── tts_tool.py      # Lightning TTS as a LangChain Tool (minimal, copy-paste ready)
└── voice_prompt.py  # Prompt templates optimized for voice output
```

## Usage

### STT Tool (Pulse)

```python
from stt_tool import PulseSTTTool

stt = PulseSTTTool(api_key="your_key")
transcript = stt.run("recording.wav")
# "Hello, I'd like to place an order..."
```

### TTS Tool (Lightning)

```python
from tts_tool import LightningTTSTool

tts = LightningTTSTool(api_key="your_key")
audio_path = tts.run("Your order has been confirmed.")
# "output/tts_output.wav"
```

### Voice-Optimized Prompts

```python
from voice_prompt import VOICE_AGENT_SYSTEM_PROMPT, voice_response_chain

chain = voice_response_chain(openai_api_key="your_key")
response = chain.invoke({"input": "What are your plans today?"})
# "I was thinking about going for a walk. How about you?"
```

## Environment Variables

See [../.env.sample](../.env.sample) for the common set:

- `SMALLEST_API_KEY` — For Pulse STT and Lightning TTS
- `OPENAI_API_KEY` — For LangChain LLM calls

## Next Steps

- [STT as LangChain Tool](../stt-as-langchain-tool/) — Full integration with examples
- [TTS as LangChain Tool](../tts-as-langchain-tool/) — Full integration with examples
- [Voice-Optimized Prompts](../voice-optimized-prompts/) — Deep dive on voice prompts
- [Conversation Memory](../conversation-memory-for-voice/) — Memory strategies for voice
- [Voice AI Agent](../examples/voice-ai-agent/) — Full end-to-end example
