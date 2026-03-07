# Conversation Memory for Voice — Recommended Way to Use LangChain Memory with Smallest AI

Memory strategies for voice conversations — our recommended way to use LangChain memory with Smallest AI.

## Why This Matters

Voice conversations have different constraints than text chats — they're real-time, the user can't scroll back, and every token adds latency. Memory strategy directly impacts response time: more tokens = slower LLM = longer silence before TTS speaks.

## Requirements

> Base dependencies are installed via the root `requirements.txt`. See the [main README](../../../README.md#usage) for setup. Install LangChain deps from `integrations/langchain/`. Copy `../.env.sample` to `.env` and add your API keys.

## Usage

```python
from memory import create_voice_memory, VoiceConversationRunner

# Quick setup — window memory keeps last 8 exchanges
memory = create_voice_memory(strategy="window", k=8)

# Full runner with prompt + LLM + memory
runner = VoiceConversationRunner()
response = runner.turn("Hi, I'm calling about my order.")
```

## Structure

```
conversation-memory-for-voice/
└── memory.py    # Memory classes + voice-optimized helpers
```

## Why Voice Memory Is Different

| Text chat | Voice conversation |
|-----------|--------------------|
| User can scroll up | User can't "replay" what was said |
| Long context is fine | Long context = slow responses = awkward pauses |
| Session can last hours | Calls are usually 2-15 minutes |
| Exact quotes matter | Gist and intent matter more |

Memory strategy directly impacts latency with more tokens leading to slower LLM response which leads to longer silence before TTS speaks.

## Recommended Strategies

### 1. Sliding Window — Short Calls (< 5 min)

Keep the last k exchanges verbatim. Simple, fast, no LLM overhead.

**When to use:** Quick interactions, transactional calls, IVR-style flows.

```python
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import trim_messages, HumanMessage, AIMessage

chat_history = InMemoryChatMessageHistory()

# Add messages
chat_history.add_message(HumanMessage(content="Hi, I need help"))
chat_history.add_message(AIMessage(content="Of course! What can I help with?"))

# Trim to last k exchanges (k*2 messages)
trimmed = trim_messages(
    chat_history.messages,
    max_tokens=8 * 2,       # 8 exchanges = 16 messages
    token_counter=len,      # count messages, not tokens
    strategy="last",
    start_on="human",
)
```

### 2. Token Buffer — Latency-Sensitive

Hard token cap on memory. Guarantees consistent LLM input size.

**When to use:** When response time is critical and you need predictable latency.

```python
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import trim_messages
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")
chat_history = InMemoryChatMessageHistory()

# Trim to token limit using LLM's tokenizer
trimmed = trim_messages(
    chat_history.messages,
    max_tokens=400,
    token_counter=llm,      # use LLM for accurate token counting
    strategy="last",
    start_on="human",
)
```

### 3. Summary Buffer — Longer Calls (15+ min)

Keep recent messages verbatim, summarize older ones. Balances full context with manageable size.

**When to use:** Support calls, consultations, any conversation that might go long.

```python
from memory import create_voice_memory

# Summarizes when history exceeds 400 tokens
memory = create_voice_memory(strategy="summary_buffer", max_token_limit=400)
```

Or use the class directly:

```python
from memory import SummaryBufferMemory
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
memory = SummaryBufferMemory(max_token_limit=400, llm=llm)

# Use with a chain
history = memory.load_memory_variables({}).get("history", [])
# ... invoke chain ...
memory.save_context({"input": user_msg}, {"output": response})
```

How it works:
- Keeps recent messages verbatim until token limit is exceeded
- When over limit, summarizes older messages using the LLM
- Prepends summary to recent messages as context

### 4. LangGraph Checkpointer — For Agents

When using `create_agent`, use a checkpointer for automatic conversation persistence.

**When to use:** Voice agents with tool calling, multi-turn reasoning.

```python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
thread_id = "call-12345"  # unique per conversation

agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=[...],
    system_prompt="You are a voice assistant...",
    checkpointer=checkpointer,
)

# Each invoke with same thread_id continues the conversation
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Hi!"}]},
    config={"configurable": {"thread_id": thread_id}},
)

# New thread_id = new conversation (clears memory)
new_thread_id = "call-67890"
```

## Recommended Practices

- **Keep system prompts short** — prompts + memory + user message compete for context
- **Don't store confirmations** — "I confirmed email is X" doubles context for no benefit
- **Trim aggressively** — set `max_tokens` low (200-400) for voice
- **Clear memory between calls** — each call is a new session (new thread_id for agents)
- **Use checkpointer for agents** — handles persistence automatically

## API Reference

- [LangChain Memory Concepts](https://python.langchain.com/docs/concepts/memory/)
- [LangGraph Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [trim_messages](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.utils.trim_messages.html)

## Next Steps

- [Voice-Optimized Prompts](../voice-optimized-prompts/) — Pair these memory strategies with the right prompts
- [Voice AI Agent](../examples/voice-ai-agent/) — Full end-to-end example with memory + tools + STT/TTS
