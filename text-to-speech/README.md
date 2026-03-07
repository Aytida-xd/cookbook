# Text-to-Speech

> **Powered by [Waves TTS](https://waves-docs.smallest.ai/v4.0.0/content/text-to-speech/overview)**

Generate natural-sounding speech from text using Smallest AI's Waves TTS API. Supports Lightning v2 and Lightning v3.1 models with 100+ voices across multiple languages.

## Examples

| Example | Description |
|---------|-------------|
| [Voice Explorer](./voice-explorer/) | Interactive browser to preview all voices, search by use case or emotion, and play audio inline |
| [News Voice App](./news-voice-app/) | Web dashboard that groups headlines into story clusters and plays each as a 2-3 min audio summary |

## Quick Start

> **Prerequisites:** Make sure you've run `uv venv && uv pip install -r requirements.txt` at the repo root. See the [main README](../README.md#usage) for full setup.

```bash
export SMALLEST_API_KEY="your-api-key-here"
```

Get your API key at [smallest.ai/console](https://smallest.ai/console).

## Documentation

- [Waves TTS Overview](https://waves-docs.smallest.ai/v4.0.0/content/text-to-speech/overview)
- [Get Voices API](https://waves-docs.smallest.ai/v4.0.0/content/api-references/get-voices-api)
- [TTS API Reference](https://waves-docs.smallest.ai/v4.0.0/content/api-references/tts-api)
- [Lightning v3.1 WebSocket](https://waves-docs.smallest.ai/v4.0.0/content/api-references/lightning-v3.1-ws)
