"""Groq LLM client for Jarvis."""

import os
import time
from groq import Groq

LLM_MODEL = "llama-3.3-70b-versatile"
LLM_SYSTEM_PROMPT = """You are Jarvis, a helpful AI assistant.

Start EVERY response with exactly one of these prefixes:
- "SPEAK:" if the user's message is directed at you
- "STOP:" if it's unrelated background speech or not meant for you

Keep responses concise (1-3 sentences)."""


def get_context_history(history: list) -> list:
    """
    Get conversation context: first pair + last 3 pairs.
    
    Keeps the initial context for continuity while including
    recent exchanges for relevance. Avoids overlap.
    """
    n = len(history)
    
    if n <= 2:
        return history
    
    first_pair = history[:2]
    remaining_start = 2
    last_pairs_start = max(remaining_start, n - 6)
    last_pairs = history[last_pairs_start:]
    
    return first_pair + last_pairs


class LLMClient:
    """Groq LLM client for generating responses."""

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        self.client = Groq(api_key=api_key)

    def get_response(self, query: str, history: list) -> tuple[str, bool]:
        """
        Get LLM response for a query.
        
        Args:
            query: User's question or statement
            history: Conversation history as list of {role, content} dicts
            
        Returns:
            Tuple of (response_text, is_stop) where is_stop indicates
            the speech was not directed at the assistant.
        """

        # Context management
        # You can write your custom logic here
        context = get_context_history(history)
        if context:
            history_text = "\n".join(
                f"{'User' if m['role'] == 'user' else 'Jarvis'}: {m['content']}"
                for m in context
            )
            content = f"CONVERSATION HISTORY:\n{history_text}\n\nCURRENT QUERY: {query}"
        else:
            content = f"CURRENT QUERY: {query}"

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
        print(f"[LLM] Response in {(time.time() - start)*1000:.0f}ms")

        if text.upper().startswith("STOP:"):
            return None, True
        if text.upper().startswith("SPEAK:"):
            text = text[6:].strip()
        return text, False
