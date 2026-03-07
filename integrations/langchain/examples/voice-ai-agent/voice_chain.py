#!/usr/bin/env python3
"""
Voice AI agent chain: LangChain agent with voice-optimized prompt,
conversation memory, and tool calling.

This is the "brain" — it takes text input (from STT) and returns
text output (for TTS). STT and TTS happen outside this module.

Usage:
    from voice_chain import VoiceAgent

    agent = VoiceAgent()
    response = agent.turn("Hi, what's the weather in San Francisco?")
"""

import re
import uuid
from typing import Optional

from dotenv import load_dotenv
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from tools import get_all_tools

load_dotenv()


SYSTEM_PROMPT = """\
You are a voice AI assistant. Your responses are spoken aloud via \
Smallest AI's Lightning TTS, so they must sound natural when spoken.

Rules:
- Keep responses to 1-3 sentences. Users are listening, not reading.
- Use natural, conversational language. Write the way people talk.
- Never use markdown, bullet points, numbered lists, or any formatting.
- Never mention URLs, links, or ask users to "click" anything.
- Spell out numbers that sound awkward as digits ("twenty three" not "23"). \
  Keep prices and phone numbers as digits ("$49", "415-555-1234").
- Avoid abbreviations. Say "for example" not "e.g.".
- End with a clear question or pause point so the user knows it's their turn.
- If you don't know something, say so briefly.
- Use the available tools when the user asks about weather, orders, or appointments.
- When transferring to a human, use the transfer tool and let the caller know."""


def clean_for_voice(text: str) -> str:
    """
    Strip formatting artifacts that shouldn't be spoken.
    
    Note: This is a simplified version. For the full implementation with
    more edge cases handled, see ../voice-optimized-prompts/prompts.py
    """
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"`[^`]*`", lambda m: m.group(0).strip("`"), text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"#{1,6}\s+", "", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


class VoiceAgent:
    """
    LangChain agent configured for voice conversations.

    - Voice-optimized system prompt (short, no formatting)
    - In-memory conversation persistence via LangGraph checkpointer
    - Tool calling (weather, orders, appointments, transfer)
    - Post-processing to strip any formatting artifacts

    Usage:
        agent = VoiceAgent()
        r1 = agent.turn("Hi, what's the weather?")
        r2 = agent.turn("Check order 45678 for me.")
        agent.reset()  # between calls

    Note: This uses LangGraph's InMemorySaver for memory persistence.
    For standalone memory without a full agent, see:
    ../conversation-memory-for-voice/memory.py (WindowMemory, TokenBufferMemory)
    """

    def __init__(
        self,
        model: str = "openai:gpt-4o-mini",
        system_prompt: str = SYSTEM_PROMPT,
    ):
        self.checkpointer = InMemorySaver()
        self.thread_id = str(uuid.uuid4())

        self.agent = create_agent(
            model=model,
            tools=get_all_tools(),
            system_prompt=system_prompt,
            checkpointer=self.checkpointer,
        )

    def turn(self, user_message: str) -> str:
        """
        Process one turn of voice conversation.

        Args:
            user_message: What the user said (STT transcript).

        Returns:
            Agent response text (ready for TTS).
        """
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]},
            config={"configurable": {"thread_id": self.thread_id}},
        )
        
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "type") and msg.type == "ai":
                return clean_for_voice(msg.content)
            elif isinstance(msg, dict) and msg.get("role") == "assistant":
                return clean_for_voice(msg.get("content", ""))
        return ""

    async def aturn(self, user_message: str) -> str:
        """Async version of turn()."""
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": user_message}]},
            config={"configurable": {"thread_id": self.thread_id}},
        )
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "type") and msg.type == "ai":
                return clean_for_voice(msg.content)
            elif isinstance(msg, dict) and msg.get("role") == "assistant":
                return clean_for_voice(msg.get("content", ""))
        return ""

    def reset(self):
        """Clear memory between calls / sessions by creating a new thread."""
        self.thread_id = str(uuid.uuid4())


if __name__ == "__main__":
    agent = VoiceAgent()

    test_turns = [
        "Hi, what's the weather like in San Francisco?",
        "Can you check on order number 45678?",
        "Book me an appointment for next Monday at 2 PM.",
        "Thanks, that's all I needed!",
    ]

    for msg in test_turns:
        print(f"\nYou:   {msg}")
        resp = agent.turn(msg)
        print(f"Agent: {resp}")
