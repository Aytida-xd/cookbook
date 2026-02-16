#!/usr/bin/env python3
"""
Conversation memory strategies for voice AI with LangChain + Smallest AI.

Voice conversations are real-time — long context means slow LLM responses
means awkward pauses before TTS speaks. These helpers configure LangChain
memory for the constraints of voice.

This is our recommended way to use LangChain memory with Smallest AI's models.

Usage:
    from memory import create_voice_memory, VoiceConversationRunner

    # Quick setup
    memory = create_voice_memory(strategy="window", k=8)

    # Full runner with prompt + LLM + memory
    runner = VoiceConversationRunner()
    response = runner.turn("Hi, I'm calling about my order.")
"""

import os
from typing import Literal, List

from dotenv import load_dotenv
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, trim_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

load_dotenv()


class WindowMemory:
    """
    Conversation memory that keeps the last k exchanges.
    
    Best for short voice calls (< 5 min) where recent context matters most.
    Uses langchain_core.messages.trim_messages for efficient windowing.
    """

    def __init__(self, k: int = 8):
        """
        Args:
            k: Number of recent exchanges to keep (1 exchange = 1 human + 1 AI message).
        """
        self.k = k
        self.chat_history = InMemoryChatMessageHistory()

    def load_memory_variables(self, inputs: dict = None) -> dict:
        """Return trimmed message history."""
        messages = self.chat_history.messages
        trimmed = trim_messages(
            messages,
            max_tokens=self.k * 2,
            token_counter=len,  # Count messages, not tokens
            strategy="last",
            start_on="human",
            include_system=True,
        )
        return {"history": trimmed}

    def save_context(self, inputs: dict, outputs: dict) -> None:
        """Save a conversation turn."""
        self.chat_history.add_message(HumanMessage(content=inputs.get("input", "")))
        self.chat_history.add_message(AIMessage(content=outputs.get("output", "")))

    def clear(self) -> None:
        """Clear all messages."""
        self.chat_history.clear()

    @property
    def messages(self) -> List[BaseMessage]:
        """Get all messages (not trimmed)."""
        return self.chat_history.messages


class TokenBufferMemory:
    """
    Conversation memory with a hard token limit.
    
    Best for latency-sensitive voice apps where you need predictable context size.
    """

    def __init__(self, max_tokens: int = 400, llm: ChatOpenAI = None):
        """
        Args:
            max_tokens: Maximum tokens to keep in history.
            llm: LLM to use for token counting (uses its tokenizer).
        """
        self.max_tokens = max_tokens
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini")
        self.chat_history = InMemoryChatMessageHistory()

    def load_memory_variables(self, inputs: dict = None) -> dict:
        """Return trimmed message history within token limit."""
        messages = self.chat_history.messages
        trimmed = trim_messages(
            messages,
            max_tokens=self.max_tokens,
            token_counter=self.llm,
            strategy="last",
            start_on="human",
            include_system=True,
        )
        return {"history": trimmed}

    def save_context(self, inputs: dict, outputs: dict) -> None:
        """Save a conversation turn."""
        self.chat_history.add_message(HumanMessage(content=inputs.get("input", "")))
        self.chat_history.add_message(AIMessage(content=outputs.get("output", "")))

    def clear(self) -> None:
        """Clear all messages."""
        self.chat_history.clear()


class SummaryBufferMemory:
    """
    Conversation memory that summarizes older messages while keeping recent ones verbatim.
    
    Best for longer voice calls (15+ min) where you need full context but can't
    keep all messages. Uses an LLM to generate summaries when history exceeds
    the token limit.
    """

    SUMMARY_PROMPT = """Summarize the following conversation in 2-3 sentences, 
capturing the key points, any names/numbers mentioned, and what was decided or requested:

{conversation}

Summary:"""

    def __init__(self, max_token_limit: int = 400, llm: ChatOpenAI = None):
        """
        Args:
            max_token_limit: Token threshold before summarization kicks in.
            llm: LLM to use for summarization and token counting.
        """
        self.max_token_limit = max_token_limit
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.chat_history = InMemoryChatMessageHistory()
        self.summary = ""

    def _count_tokens(self, messages: List[BaseMessage]) -> int:
        """Count tokens in messages using the LLM's tokenizer."""
        if not messages:
            return 0
        text = "\n".join(m.content for m in messages)
        return self.llm.get_num_tokens(text)

    def _summarize_messages(self, messages: List[BaseMessage]) -> str:
        """Generate a summary of the given messages."""
        if not messages:
            return ""
        conversation = "\n".join(
            f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
            for m in messages
        )
        prompt = self.SUMMARY_PROMPT.format(conversation=conversation)
        response = self.llm.invoke(prompt)
        return response.content.strip()

    def load_memory_variables(self, inputs: dict = None) -> dict:
        """
        Return message history, summarizing older messages if over token limit.
        
        Returns recent messages verbatim, prepended with a summary of older
        messages if the full history exceeds max_token_limit.
        """
        messages = self.chat_history.messages
        
        if not messages:
            if self.summary:
                return {"history": [AIMessage(content=f"[Previous conversation summary: {self.summary}]")]}
            return {"history": []}

        total_tokens = self._count_tokens(messages)
        if self.summary:
            total_tokens += self.llm.get_num_tokens(self.summary)

        if total_tokens <= self.max_token_limit:
            if self.summary:
                summary_msg = AIMessage(content=f"[Previous conversation summary: {self.summary}]")
                return {"history": [summary_msg] + list(messages)}
            return {"history": list(messages)}

        # Over limit — need to summarize older messages
        # Keep trimming from the front until we're under limit
        recent_messages = list(messages)
        messages_to_summarize = []

        while recent_messages and self._count_tokens(recent_messages) > self.max_token_limit // 2:
            messages_to_summarize.append(recent_messages.pop(0))

        if messages_to_summarize:
            old_summary = self.summary
            new_summary_part = self._summarize_messages(messages_to_summarize)
            if old_summary:
                self.summary = f"{old_summary} {new_summary_part}"
            else:
                self.summary = new_summary_part

            self.chat_history.clear()
            for msg in recent_messages:
                self.chat_history.add_message(msg)

        if self.summary:
            summary_msg = AIMessage(content=f"[Previous conversation summary: {self.summary}]")
            return {"history": [summary_msg] + list(self.chat_history.messages)}
        return {"history": list(self.chat_history.messages)}

    def save_context(self, inputs: dict, outputs: dict) -> None:
        """Save a conversation turn."""
        self.chat_history.add_message(HumanMessage(content=inputs.get("input", "")))
        self.chat_history.add_message(AIMessage(content=outputs.get("output", "")))

    def clear(self) -> None:
        """Clear all messages and summary."""
        self.chat_history.clear()
        self.summary = ""

    @property
    def messages(self) -> List[BaseMessage]:
        """Get all current messages (not including summarized ones)."""
        return self.chat_history.messages


def create_voice_memory(
    strategy: Literal["window", "token_buffer", "summary_buffer"] = "window",
    k: int = 8,
    max_token_limit: int = 400,
    model: str = "gpt-4o-mini",
):
    """
    Create a memory instance optimized for voice conversations.

    Strategies:
        window:         Keep last k exchanges. Best for short calls (< 5 min).
        token_buffer:   Hard token cap. Best for latency-sensitive apps.
        summary_buffer: Summarize older messages. Best for longer calls (15+ min).

    Args:
        strategy: Which memory strategy to use.
        k: Number of recent exchanges to keep (for "window").
        max_token_limit: Token limit (for "token_buffer" and "summary_buffer").
        model: LLM model used for token counting / summarization.
    """
    if strategy == "window":
        return WindowMemory(k=k)

    elif strategy == "token_buffer":
        llm = ChatOpenAI(model=model, temperature=0)
        return TokenBufferMemory(max_tokens=max_token_limit, llm=llm)

    elif strategy == "summary_buffer":
        llm = ChatOpenAI(model=model, temperature=0)
        return SummaryBufferMemory(max_token_limit=max_token_limit, llm=llm)

    else:
        raise ValueError(f"Unknown strategy: {strategy}. Use: window, token_buffer, summary_buffer")


VOICE_SYSTEM_PROMPT = """\
You are a voice AI assistant. Your responses are spoken aloud via Smallest AI TTS.
Keep responses to 1-3 sentences. No formatting, no markdown, no bullet points.
Use natural conversational language. End with a question or pause point."""


class VoiceConversationRunner:
    """
    Runs a multi-turn voice conversation with LangChain memory.

    Handles the prompt + LLM + memory loop. Feed in user transcripts (from STT),
    get back response text (for TTS).

    Example:
        runner = VoiceConversationRunner()
        response1 = runner.turn("Hi, I need help with my account.")
        response2 = runner.turn("My account number is 12345.")
        response3 = runner.turn("I want to upgrade to the pro plan.")
    """

    def __init__(
        self,
        system_prompt: str = VOICE_SYSTEM_PROMPT,
        memory_strategy: str = "window",
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        k: int = 8,
        max_token_limit: int = 400,
    ):
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        self.memory = create_voice_memory(
            strategy=memory_strategy,
            k=k,
            max_token_limit=max_token_limit,
            model=model,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("history"),
            ("human", "{input}"),
        ])
        self.chain = self.prompt | self.llm

    def turn(self, user_message: str) -> str:
        """
        Process one turn of conversation.

        Args:
            user_message: What the user said (from STT transcript).

        Returns:
            Agent response text (ready for TTS).
        """
        history = self.memory.load_memory_variables({}).get("history", [])
        response = self.chain.invoke({"input": user_message, "history": history})
        text = response.content

        self.memory.save_context(
            {"input": user_message},
            {"output": text},
        )

        return text

    async def aturn(self, user_message: str) -> str:
        """Async version of turn()."""
        history = self.memory.load_memory_variables({}).get("history", [])
        response = await self.chain.ainvoke({"input": user_message, "history": history})
        text = response.content

        self.memory.save_context(
            {"input": user_message},
            {"output": text},
        )

        return text

    def reset(self):
        """Clear memory. Call this between phone calls / sessions."""
        self.memory.clear()


if __name__ == "__main__":
    print("Voice Conversation Demo (window memory, k=8)")
    print("=" * 50)

    runner = VoiceConversationRunner(memory_strategy="window", k=8)

    turns = [
        "Hi, I'm calling about a problem with my recent order.",
        "The order number is 45678.",
        "It was supposed to arrive last Tuesday but it never showed up.",
        "Can you check on the status for me?",
        "And actually, while you're at it, can you update my shipping address?",
        "It's 123 Main Street, Apartment 4B.",
        "Perfect. And what was the order number I gave you earlier?",
    ]

    for user_msg in turns:
        response = runner.turn(user_msg)
        print(f"\nCaller: {user_msg}")
        print(f"Agent:  {response}")
