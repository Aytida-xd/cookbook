"""Groq LLM client for Jarvis."""

import base64
import os
import platform
import shutil
import subprocess
import tempfile
import time
from groq import Groq

LLM_MODEL = "llama-3.3-70b-versatile"
LLM_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
LLM_SYSTEM_PROMPT = """You are Jarvis, a helpful AI assistant.

Start EVERY response with exactly one of these prefixes:
- "SPEAK:" if the user's message is directed at you
- "STOP:" if it's unrelated background speech or not meant for you

Keep responses concise (1-3 sentences)."""

VISION_EXTRACTION_PROMPT = """Analyze this image and provide:
1. ALL TEXT visible in the image (extract exactly as written)
2. A brief description of what the image shows

Format:
TEXT IN IMAGE:
<extracted text or "No text visible">

IMAGE DESCRIPTION:
<brief description>"""


def take_screenshot() -> str | None:
    """Capture screen region using native tools. Returns base64 image or None."""
    system = platform.system()
    filepath = tempfile.mktemp(suffix=".png")

    try:
        if system == "Windows":
            subprocess.run(["snippingtool", "/clip"], check=True)
            ps_cmd = f'''
            Add-Type -AssemblyName System.Windows.Forms
            $img = [System.Windows.Forms.Clipboard]::GetImage()
            if ($img) {{ $img.Save("{filepath}") }}
            '''
            subprocess.run(["powershell", "-Command", ps_cmd], check=True)

        elif system == "Linux":
            if shutil.which("flameshot"):
                result = subprocess.run(["flameshot", "gui", "--raw"], capture_output=True)
                if result.returncode == 0 and result.stdout:
                    with open(filepath, "wb") as f:
                        f.write(result.stdout)
            elif shutil.which("spectacle"):
                subprocess.run(["spectacle", "-r", "-b", "-o", filepath], check=True)
            elif shutil.which("gnome-screenshot"):
                subprocess.run(["gnome-screenshot", "-a", "-f", filepath], check=True)
            elif shutil.which("scrot"):
                subprocess.run(["scrot", "-s", filepath], check=True)
            elif shutil.which("import"):
                subprocess.run(["import", filepath], check=True)
            else:
                print("[Screenshot] No tool found")
                return None

        elif system == "Darwin":
            subprocess.run(["screencapture", "-i", filepath], check=True)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            with open(filepath, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        return None

    except Exception as e:
        print(f"[Screenshot] Error: {e}")
        return None
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


def get_context_history(history: list) -> list:
    """Get first query-response pair + last 3 pairs from history."""
    n = len(history)
    if n <= 2:
        return history

    first_pair = history[:2]
    last_pairs_start = max(2, n - 6)
    return first_pair + history[last_pairs_start:]


class LLMClient:
    """Groq LLM client with vision support."""

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        self.client = Groq(api_key=api_key)

    def get_response(self, query: str, history: list) -> tuple[str, bool]:
        """Get LLM response. Captures screenshot if 'screenshot' in query."""
        context = get_context_history(history)
        if context:
            history_text = "\n".join(
                f"{'User' if m['role'] == 'user' else 'Jarvis'}: {m['content']}"
                for m in context
            )
            text_content = f"CONVERSATION HISTORY:\n{history_text}\n\nCURRENT QUERY: {query}"
        else:
            text_content = f"CURRENT QUERY: {query}"

        if "screenshot" in query.lower():
            print("[LLM] Screenshot requested...")
            image_b64 = take_screenshot()
            if image_b64:
                return self._vision_request(query, image_b64)
            print("[LLM] Screenshot failed, using text model")

        return self._text_request(text_content)

    def _text_request(self, content: str) -> tuple[str, bool]:
        """Text-only LLM request."""
        start = time.time()
        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": LLM_SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            max_tokens=256,
            temperature=0.7,
        )
        text = response.choices[0].message.content.strip()
        print(f"[LLM] {(time.time() - start)*1000:.0f}ms")
        return self._parse_response(text)

    def _vision_request(self, query: str, image_b64: str) -> tuple[str, bool]:
        """Two-step: vision model extracts content, text model responds."""
        try:
            start = time.time()
            vision_response = self.client.chat.completions.create(
                model=LLM_VISION_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_EXTRACTION_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                    ],
                }],
                max_tokens=1024,
                temperature=0.3,
            )
            extraction = vision_response.choices[0].message.content.strip()
            print(f"[Vision] {(time.time() - start)*1000:.0f}ms")

            start = time.time()
            combined = f"Screenshot content:\n\n{extraction}\n\nUser's question: {query}"
            text_response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": combined},
                ],
                max_tokens=512,
                temperature=0.7,
            )
            text = text_response.choices[0].message.content.strip()
            print(f"[LLM] {(time.time() - start)*1000:.0f}ms")
            return self._parse_response(text)

        except Exception as e:
            print(f"[Vision] Error: {e}")
            return f"Sorry, I couldn't analyze the screenshot: {e}", False

    def _parse_response(self, text: str) -> tuple[str, bool]:
        """Parse SPEAK:/STOP: prefix from response."""
        if text.upper().startswith("STOP:"):
            return None, True
        if text.upper().startswith("SPEAK:"):
            text = text[6:].strip()
        return text, False
