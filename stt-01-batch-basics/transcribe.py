#!/usr/bin/env python3
"""
Smallest AI Lightning STT - Batch Transcription

Transcribe audio files using the Lightning STT API.
Outputs both a plain text transcript and a JSON result file.

Setup:
    pip install requests

    export SMALLEST_API_KEY="your-api-key-here"
    # Get your API key at: https://smallest.ai/console

Usage:
    python transcribe.py <audio_file> [--language <code>] [--output-dir <dir>]

Examples:
    python transcribe.py recording.wav
    python transcribe.py podcast.mp3 --language en
    python transcribe.py meeting.wav --language auto --output-dir ./results
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests

# API Configuration
API_URL = "https://waves-api.smallest.ai/api/v1/lightning/get_text"


def get_api_key() -> str:
    """Get API key from environment variable."""
    api_key = os.environ.get("SMALLEST_API_KEY")
    if not api_key:
        print("Error: SMALLEST_API_KEY environment variable not set.")
        print("Get your API key at: https://smallest.ai/console")
        sys.exit(1)
    return api_key


def transcribe_audio(
    audio_path: str,
    language: str = "auto",
    api_key: str | None = None,
) -> dict:
    """
    Transcribe an audio file using the Lightning STT API.

    Args:
        audio_path: Path to the audio file
        language: Language code (e.g., 'en', 'es', 'fr') or 'auto' for detection
        api_key: Smallest AI API key (uses env var if not provided)

    Returns:
        API response as a dictionary
    """
    if api_key is None:
        api_key = get_api_key()

    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Read audio file
    with open(audio_path, "rb") as f:
        audio_data = f.read()

    # Prepare request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/octet-stream",
    }

    # Build query parameters
    params = {}
    if language and language.lower() != "auto":
        params["language"] = language

    # Make API request
    print(f"Transcribing: {audio_path.name}")
    if language and language.lower() != "auto":
        print(f"Language: {language}")
    else:
        print("Language: auto-detect")

    response = requests.post(
        API_URL,
        headers=headers,
        params=params,
        data=audio_data,
        timeout=300,  # 5 minute timeout for large files
    )

    if response.status_code != 200:
        error_msg = f"API request failed with status {response.status_code}"
        try:
            error_detail = response.json()
            error_msg += f": {error_detail}"
        except Exception:
            error_msg += f": {response.text}"
        raise RuntimeError(error_msg)

    return response.json()


def save_results(result: dict, output_dir: str = ".") -> tuple[str, str]:
    """
    Save transcription results to files.

    Args:
        result: API response dictionary
        output_dir: Directory to save output files

    Returns:
        Tuple of (transcript_path, json_path)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save plain text transcript
    transcript_path = output_dir / "transcript.txt"
    transcription = result.get("transcription", "")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcription)
    print(f"Saved transcript: {transcript_path}")

    # Save full JSON result
    json_path = output_dir / "result.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Saved result: {json_path}")

    return str(transcript_path), str(json_path)


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe audio files using Smallest AI Lightning STT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python transcribe.py recording.wav
  python transcribe.py podcast.mp3 --language en
  python transcribe.py meeting.wav --output-dir ./results

Supported audio formats: WAV, MP3, FLAC, OGG, WebM, M4A
        """,
    )
    parser.add_argument(
        "audio_file",
        help="Path to the audio file to transcribe",
    )
    parser.add_argument(
        "--language",
        "-l",
        default="auto",
        help="Language code (e.g., 'en', 'es', 'fr') or 'auto' for detection (default: auto)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default=".",
        help="Directory to save output files (default: current directory)",
    )

    args = parser.parse_args()

    try:
        # Transcribe audio
        result = transcribe_audio(
            audio_path=args.audio_file,
            language=args.language,
        )

        # Check for successful response
        if result.get("status") != "success":
            print(f"Transcription failed: {result}")
            sys.exit(1)

        # Display results
        transcription = result.get("transcription", "")
        audio_length = result.get("audio_length", 0)

        print("\n" + "=" * 60)
        print("TRANSCRIPTION")
        print("=" * 60)
        print(transcription)
        print("=" * 60)
        print(f"Audio length: {audio_length:.2f} seconds")
        print(f"Words: {len(result.get('words', []))}")
        print(f"Utterances: {len(result.get('utterances', []))}")

        # Save results
        print()
        save_results(result, args.output_dir)

        print("\nDone!")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)


if __name__ == "__main__":
    main()

