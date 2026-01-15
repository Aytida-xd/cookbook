# STT-01: Batch Transcription Basics

Transcribe audio files using the Smallest AI Lightning STT API with language parameter support.

## Overview

This cookbook demonstrates how to:
- Transcribe pre-recorded audio files using the Lightning STT API
- Use the language parameter for improved accuracy
- Save transcription results to text and JSON files

## Prerequisites

- A Smallest AI API key ([get one here](https://smallest.ai/console))
- Python 3.8+ **or** Node.js 18+

## Setup

Set your API key as an environment variable:

```bash
export SMALLEST_API_KEY="your-api-key-here"
```

---

## Python

### Install

```bash
pip install requests
```

### Usage

```bash
cd python

# Basic transcription
python transcribe.py audio.wav

# With language parameter
python transcribe.py audio.wav --language en

# Custom output directory
python transcribe.py audio.wav --output-dir ./results
```

---

## JavaScript

### Install

```bash
cd javascript
npm install
```

### Usage

```bash
# Basic transcription
node transcribe.js audio.wav

# With language parameter
node transcribe.js audio.wav --language en

# Custom output directory
node transcribe.js audio.wav --output-dir ./results
```

---

## Supported Languages

The API supports 30+ languages. Common language codes:
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `hi` - Hindi
- `zh` - Chinese
- `ja` - Japanese
- `ko` - Korean
- `pt` - Portuguese
- `ar` - Arabic

Use `multi` for automatic language detection (default).

## Output

Both scripts produce two output files:

1. **transcript.txt** - Plain text transcription
2. **result.json** - Full API response

## API Reference

- [Lightning STT Documentation](https://waves-docs.smallest.ai/v4.0.0/content/speech-to-text-new/pre-recorded/quickstart)
- [API Reference](https://waves-docs.smallest.ai/v4.0.0/content/api-references/lightning-asr)

## License

Apache 2.0
