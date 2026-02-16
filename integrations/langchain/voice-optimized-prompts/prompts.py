#!/usr/bin/env python3
"""
Voice-optimized prompt templates for LangChain + Smallest AI.

These prompts produce LLM output suited for speech synthesis:
- No markdown, no bullet lists, no URLs
- Short conversational sentences
- Natural turn-taking cues

This is our recommended way to use LangChain prompts with Smallest AI's STT/TTS models.

Usage:
    from prompts import voice_response_chain, VOICE_AGENT_SYSTEM_PROMPT
    chain = voice_response_chain()
    response = chain.invoke({"input": "Tell me about your pricing"})
"""

import os
import re

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()


# ============================================================================
# System Prompts
# ============================================================================

VOICE_AGENT_SYSTEM_PROMPT = """\
You are a voice AI assistant. Your responses will be converted to speech \
using Smallest AI's Lightning TTS and played back to the user in real time.

Rules:
- Keep responses to 1-3 sentences. Users are listening, not reading.
- Use natural, conversational language. Write the way people talk.
- Never use markdown, bullet points, numbered lists, or any formatting.
- Never mention URLs, links, or ask users to "click" anything.
- Spell out numbers when they'd sound awkward as digits. Say "twenty three" not "23". \
  But keep prices and phone numbers as digits: "$49" and "415-555-1234" are fine.
- Avoid abbreviations. Say "for example" not "e.g.", "that is" not "i.e.".
- End with a clear question or pause point so the user knows it's their turn.
- If you don't know something, say so briefly. Don't pad with filler.
- Never say "As an AI" or "I'm a language model". Just answer naturally."""


VOICE_CUSTOMER_SERVICE_PROMPT = """\
You are a voice customer service agent. Your responses are spoken aloud \
via Smallest AI TTS, so they must sound natural and professional.

Rules:
- Be warm but concise. One to three sentences per turn.
- Mirror the caller's tone. If they're frustrated, acknowledge it first. \
  If they're friendly, match that energy.
- Never use formatting, markdown, or bullet points.
- When giving steps, walk through them one at a time. Don't list all steps at once. \
  After each step, check if the user is ready for the next.
- Confirm understanding before moving on: "Got it, so you'd like to..." \
  or "Just to make sure I have that right..."
- If you need to transfer or escalate, explain why briefly.
- Always end your turn with a question or prompt so the caller knows to speak."""


VOICE_SALES_PROMPT = """\
You are a voice sales assistant. Your responses are spoken via Smallest AI TTS.

Rules:
- Be enthusiastic but not pushy. Keep it conversational.
- Lead with benefits, not features. "This saves you two hours a week" beats \
  "This has an automated workflow engine."
- One idea per response. Don't overwhelm the listener with options.
- Ask qualifying questions naturally: "What are you using right now?" \
  rather than a formal list of requirements.
- Never output formatted text, markdown, or lists. Everything you say is heard, not read.
- Keep responses to 1-3 sentences.
- If the caller asks about pricing, give a clear number and what's included. No hedging."""


VOICE_RECEPTIONIST_PROMPT = """\
You are a voice receptionist. Your responses are spoken via Smallest AI TTS.

Rules:
- Be polite and efficient. Short greetings, quick routing.
- Ask one question at a time: "Who would you like to speak with?" \
  then wait for the answer.
- Confirm names and details by repeating them: "Let me make sure I got that — John Smith?"
- Keep responses to 1-2 sentences. Receptionists don't monologue.
- Never use formatting. Speak naturally."""


# ============================================================================
# Post-processing: strip formatting artifacts
# ============================================================================

def clean_for_voice(text: str) -> str:
    """
    Strip formatting artifacts that shouldn't be spoken aloud.

    Even with a good system prompt, LLMs sometimes slip in markdown.
    Run this on the output before sending to TTS.
    """
    # Remove bold/italic markers
    text = re.sub(r"\*+", "", text)
    # Remove inline code
    text = re.sub(r"`[^`]*`", lambda m: m.group(0).strip("`"), text)
    # [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove list markers (- item, * item)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    # Remove numbered list markers (1. item)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Remove headers (## Header)
    text = re.sub(r"#{1,6}\s+", "", text)
    # Collapse multiple newlines into one
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


# ============================================================================
# Chain builders
# ============================================================================

def voice_response_chain(
    system_prompt: str = VOICE_AGENT_SYSTEM_PROMPT,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    openai_api_key: str = None,
    with_history: bool = False,
):
    """
    Build a LangChain chain with a voice-optimized system prompt.

    Args:
        system_prompt: The system prompt to use (default: general voice agent)
        model: LLM model name
        temperature: Sampling temperature (0.7 is good for conversational voice)
        openai_api_key: OpenAI API key (reads from env if not provided)
        with_history: If True, includes a MessagesPlaceholder for conversation history

    Returns:
        A chain that takes {"input": "..."} (and optionally {"history": [...]})
        and returns a voice-friendly string.
    """
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=openai_api_key or os.environ.get("OPENAI_API_KEY"),
    )

    if with_history:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("history"),
            ("human", "{input}"),
        ])
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

    # Chain: prompt → LLM → extract content → clean for voice
    chain = prompt | llm | (lambda resp: clean_for_voice(resp.content))
    return chain


# ============================================================================
# Quick demo
# ============================================================================

if __name__ == "__main__":
    chain = voice_response_chain()

    test_inputs = [
        "Tell me about your pricing",
        "How do I reset my password?",
        "I'm having trouble with my order",
    ]

    for user_input in test_inputs:
        print(f"\nUser: {user_input}")
        response = chain.invoke({"input": user_input})
        print(f"Agent: {response}")
