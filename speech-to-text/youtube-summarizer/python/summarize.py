#!/usr/bin/env python3
"""
Smallest AI Speech-to-Text - YouTube Summarizer

Download a YouTube video, transcribe it with Pulse STT, and generate
a concise summary using Groq.

Usage: python summarize.py <youtube_url>

Environment Variables:
- SMALLEST_API_KEY: Smallest AI API key
- GROQ_API_KEY: Groq API key

Requirements:
- yt-dlp (YouTube downloader)
- groq Python package

Output:
- Console output with summary
- {video_id}_summary.md - Markdown summary file
- {video_id}_transcript.txt - Full transcript
- {video_id}.mp3 - Downloaded audio (optional, can be deleted)
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://waves-api.smallest.ai/api/v1/pulse/get_text"

LANGUAGE = "en"  # Use ISO 639-1 codes or "multi" for auto-detect

SUMMARIZE_PROMPT = """You are an expert video summarizer. Analyze the following transcript and create a concise, well-structured summary.

Your task:
1. Extract the KEY POINTS and main topics discussed
2. Remove all filler words, tangents, and unnecessary content
3. Keep only the valuable, actionable insights
4. Organize the summary with clear sections
5. Include any notable quotes if they add value

Format your response as:

## Summary
A 2-3 sentence overview of what the video is about.

## Key Points
- Bullet points of the main takeaways
- Focus on actionable insights
- Remove redundant information

## Topics Discussed
Brief description of each major topic covered.

## Notable Quotes (if any)
Include 1-2 impactful quotes from the video.

---

TRANSCRIPT:
{transcript}
"""


def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def download_audio(url: str, output_path: str) -> str:
    """
    Download audio from YouTube using yt-dlp.
    
    Returns the path to the downloaded audio file.
    """
    print("Downloading audio from YouTube...")
    
    # Check if yt-dlp is installed
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("Error: yt-dlp not installed. Run: pip install yt-dlp")
        sys.exit(1)
    
    # Download audio only, convert to mp3
    cmd = [
        "yt-dlp",
        "-x",                          # Extract audio
        "--audio-format", "mp3",       # Convert to mp3
        "--audio-quality", "0",        # Best quality
        "-o", output_path,             # Output path
        "--no-playlist",               # Don't download playlists
        "--quiet",                     # Suppress output
        "--progress",                  # Show progress
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error downloading: {result.stderr}")
        sys.exit(1)
    
    print(f"Downloaded: {output_path}")
    return output_path


def transcribe(audio_file: str, api_key: str) -> str:
    """Transcribe audio using Pulse STT API."""
    print("Transcribing with Pulse STT...")
    
    with open(audio_file, "rb") as f:
        file_data = f.read()
    
    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/octet-stream",
        },
        params={
            "language": LANGUAGE,
        },
        data=file_data,
        timeout=600,
    )
    
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    result = response.json()
    
    if result.get("status") != "success":
        raise Exception(f"Transcription failed: {result}")
    
    transcript = result.get("transcription", "")
    print(f"Transcription complete: {len(transcript)} characters")
    return transcript


def summarize_with_groq(transcript: str, groq_api_key: str) -> str:
    """Generate summary using Groq."""
    print("Generating summary with Groq...")
    
    try:
        from groq import Groq
    except ImportError:
        print("Error: groq package not installed. Run: pip install groq")
        sys.exit(1)
    
    client = Groq(api_key=groq_api_key)
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an expert video summarizer who extracts key insights and removes unnecessary content."
            },
            {
                "role": "user",
                "content": SUMMARIZE_PROMPT.format(transcript=transcript)
            }
        ],
        temperature=0.3,
        max_tokens=2000,
    )
    
    summary = response.choices[0].message.content
    print("Summary generated successfully")
    return summary


def main():
    if len(sys.argv) < 2:
        print("Usage: python summarize.py <youtube_url>")
        print("Example: python summarize.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        sys.exit(1)
    
    youtube_url = sys.argv[1]
    smallest_api_key = os.environ.get("SMALLEST_API_KEY")
    groq_api_key = os.environ.get("GROQ_API_KEY")
    
    if not smallest_api_key:
        print("Error: SMALLEST_API_KEY environment variable not set")
        sys.exit(1)
    
    if not groq_api_key:
        print("Error: GROQ_API_KEY environment variable not set")
        sys.exit(1)
    
    # Extract video ID for naming files
    try:
        video_id = extract_video_id(youtube_url)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    print(f"Processing YouTube video: {video_id}")
    print("=" * 60)
    
    # Step 1: Download audio
    audio_path = f"{video_id}.mp3"
    download_audio(youtube_url, audio_path)
    
    # Step 2: Transcribe
    transcript = transcribe(audio_path, smallest_api_key)
    
    # Save transcript
    transcript_path = f"{video_id}_transcript.txt"
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcript)
    print(f"Saved transcript: {transcript_path}")
    
    # Step 3: Summarize
    summary = summarize_with_groq(transcript, groq_api_key)
    
    # Save summary
    summary_path = f"{video_id}_summary.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# YouTube Video Summary\n\n")
        f.write(f"**Video:** https://youtube.com/watch?v={video_id}\n\n")
        f.write(summary)
    print(f"Saved summary: {summary_path}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("VIDEO SUMMARY")
    print("=" * 60)
    print(summary)
    print("=" * 60)
    print("\nDone!")


if __name__ == "__main__":
    main()

