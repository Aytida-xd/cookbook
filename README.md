![Smallest AI](assets/smallest-banner.png)

<div align="center">
  <a href="https://twitter.com/smallest_AI">
    <img src="https://img.shields.io/twitter/url/https/twitter.com/smallest_AI.svg?style=social&label=Follow%20smallest_AI" alt="Twitter">
  </a>
  <a href="https://discord.gg/ywShEyXHBW">
    <img src="https://img.shields.io/discord/1212257329559642112?style=flat&logo=discord&logoColor=white&label=Discord&color=5865F2" alt="Discord">
  </a>
  <a href="https://www.linkedin.com/company/smallest">
    <img src="https://img.shields.io/badge/LinkedIn-Connect-blue" alt="LinkedIn">
  </a>
  <a href="https://www.youtube.com/@smallest_ai">
    <img src="https://img.shields.io/static/v1?message=smallest_ai&logo=youtube&label=&color=FF0000&logoColor=white&labelColor=&style=for-the-badge" height=20 alt="YouTube">
  </a>
</div>

# Smallest AI Cookbook

Practical examples and tutorials for building with Smallest AI's APIs. Each example is self-contained and demonstrates a real-world use case.

**For comprehensive documentation, visit [smallest.ai/docs](https://waves-docs.smallest.ai).**

---

## Usage

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Python >= 3.10 (install via `uv python install 3.13` if needed)
- A Smallest AI API key — get one at [smallest.ai/console](https://smallest.ai/console)

### Step 1: Create env + install base deps

```bash
uv venv
uv pip install -r requirements.txt
```

This installs common dependencies (`requests`, `websockets`, `python-dotenv`, `smallestai`, `openai`, `groq`, `loguru`, `streamlit`, `gradio`) shared across examples.

### Step 2: Run an example

```bash
# Set your API key
export SMALLEST_API_KEY="your-api-key-here"

# Run any example directly
uv run speech-to-text/getting-started/python/transcribe.py recording.wav
```

Some examples require extra dependencies. Install them first:

```bash
uv pip install -r speech-to-text/websocket/jarvis/requirements.txt
uv run speech-to-text/websocket/jarvis/jarvis.py
```

Later, for another example:

```bash
uv pip install -r speech-to-text/youtube-summarizer/requirements.txt
uv run speech-to-text/youtube-summarizer/app.py
```

### Step 3: Set up API keys

Each example includes a `.env.sample` file. Copy it and add your keys:

```bash
cd speech-to-text/getting-started
cp .env.sample .env
# Edit .env with your API keys
```

Or export directly:

```bash
export SMALLEST_API_KEY="your-api-key-here"
```

**API keys used across examples:**

| Key | Where to get it | Used by |
|-----|-----------------|---------|
| `SMALLEST_API_KEY` | [smallest.ai/console](https://smallest.ai/console) | All examples |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) | Podcast Summarizer, Meeting Notes, Voice Agents |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | YouTube Summarizer, Jarvis |
| `RECALL_API_KEY` | [recall.ai](https://recall.ai) | Meeting Notes |

---

## Speech-to-Text Examples

Convert audio and video to text with industry-leading accuracy. Supports 30+ languages. Powered by [Pulse STT](https://waves-docs.smallest.ai/v4.0.0/content/speech-to-text-new/overview).

| Example | Description |
|---------|-------------|
| [Getting Started](./speech-to-text/getting-started/) | Basic transcription — the simplest way to start |
| [Online Meeting Notetaker](./speech-to-text/online-meeting-notetaking-bot/) | Join meetings via Recall.ai, auto-identify speakers by name |
| [Jarvis Voice Assistant](./speech-to-text/websocket/jarvis/) | Always-on assistant with wake word, LLM, and TTS |

**[See all 10 Speech-to-Text examples &rarr;](./speech-to-text/)**

---

## Voice Agents Examples

Build voice AI agents with the [Atoms SDK](https://atoms-docs.smallest.ai/dev).

| Example | What You'll Learn |
|---------|-------------------|
| [Getting Started](./voice-agents/getting_started/) | `OutputAgentNode`, `generate_response()`, `AtomsApp` |
| [Agent with Tools](./voice-agents/agent_with_tools/) | `@function_tool`, `ToolRegistry`, tool execution |

**[See all 10 Voice Agents examples &rarr;](./voice-agents/)**

---

## Language Support

Each example includes implementations in:

- **Python** — Uses `requests`, `websockets`, and standard libraries
- **JavaScript** — Uses `node-fetch`, `ws`, and Node.js built-ins

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines. In short:

1. Create a folder with a descriptive name
2. Add implementations in `python/` and/or `javascript/` subdirectories
3. Include a `README.md` and `.env.sample`
4. If the example needs deps beyond the root `requirements.txt`, add a local `requirements.txt`
5. Update this root README with your new example

---

## Get Help

- [Discord Community](https://discord.gg/5evETqguJs)
- [Contact Support](https://smallest.ai/contact)
