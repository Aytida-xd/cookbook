# Background Agent

Multi-node architecture with real-time sentiment analysis running alongside the main agent.

## Features

- **BackgroundAgentNode** — Processes events without producing audio output
- **Multi-node sessions** — Multiple agents running in parallel
- **Event handling** — Reacting to `UserStartedSpeaking`, `UserStoppedSpeaking`, `TranscriptUpdate`
- **Cross-agent communication** — Main agent queries background agent state
- **Auto-escalation** — Transfer based on detected frustration

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     AgentSession                        │
│                                                         │
│  ┌─────────────────────┐   ┌─────────────────────────┐  │
│  │  SentimentAnalyzer  │   │     SupportAgent        │  │
│  │  (BackgroundNode)   │   │    (OutputAgentNode)    │  │
│  │                     │   │                         │  │
│  │  - Listens to all   │   │  - Handles conversation │  │
│  │    events           │◄──│  - Queries sentiment    │  │
│  │  - Analyzes text    │   │  - Auto-escalates       │  │
│  │  - Stores state     │   │                         │  │
│  └─────────────────────┘   └─────────────────────────┘  │
│            ▲                          ▲                 │
│            │      Events flow to      │                 │
│            └──────── both nodes ──────┘                 │
└─────────────────────────────────────────────────────────┘
```

## Requirements

> Base dependencies are installed via the root `requirements.txt`. See the [main README](../../README.md#usage) for setup. Add `OPENAI_API_KEY` to your `.env`.

## Usage

Start the server:

```bash
uv run app.py
```

Connect with the CLI:

```bash
smallestai agent chat
```

## Recommended Usage

- Background processing alongside your main agent — sentiment analysis, compliance monitoring, real-time analytics
- Multi-node sessions where agents run in parallel and share state
- For sequential pipeline processing, [Language Switching](../language_switching/) is recommended

## Key Snippets

### BackgroundAgentNode

Unlike `OutputAgentNode`, background agents:
- Don't produce audio output
- Don't auto-handle interrupts
- Process events silently in the background
- Store state for other agents to query

```python
from smallestai.atoms.agent.nodes import BackgroundAgentNode

class SentimentAnalyzer(BackgroundAgentNode):
    def __init__(self):
        super().__init__(name="sentiment-analyzer")
        self.current_sentiment = "neutral"

    async def process_event(self, event: SDKEvent):
        if isinstance(event, SDKAgentTranscriptUpdateEvent):
            if event.role == "user":
                self.current_sentiment = await self._analyze(event.content)
```

### Multi-Node Session

Add multiple nodes to run them in parallel:

```python
async def setup_session(session: AgentSession):
    background_agent = SentimentAnalyzer()
    main_agent = SupportAgent(sentiment_analyzer=background_agent)
    
    # Both nodes receive all events
    session.add_node(background_agent)
    session.add_node(main_agent)
    
    await session.start()
```

### Speaking Events

React to user speaking state:

```python
async def process_event(self, event: SDKEvent):
    if isinstance(event, SDKSystemUserStartedSpeakingEvent):
        # User started talking
        pass
    elif isinstance(event, SDKSystemUserStoppedSpeakingEvent):
        # User finished talking
        pass
```

## Example Output

```
Assistant: Hello! I'm here to help. What can I assist you with today?
User: I've been waiting for my order for 3 weeks and nobody will help me!
[SentimentAnalyzer] Detected frustrated sentiment (frustration count: 1)
Assistant: I completely understand your frustration, and I'm sorry for the delay...

User: This is ridiculous! I want a refund now!
[SentimentAnalyzer] Detected frustrated sentiment (frustration count: 2)
Assistant: I hear you, and I want to make this right...

User: I can't believe how terrible this service is!
[SentimentAnalyzer] Detected frustrated sentiment (frustration count: 3)
[Auto-escalation triggered]
Assistant: I can hear this has been frustrating. Let me connect you with a supervisor...
```

## Use Cases

- **Escalation triggers** — Auto-transfer when frustration is high
- **Call quality monitoring** — Track sentiment across calls
- **Agent coaching** — Real-time feedback for human agents
- **Analytics** — Post-call sentiment reports

## Structure

```
background_agent/
├── app.py                  # Session setup with multi-node architecture
├── sentiment_analyzer.py   # BackgroundAgentNode for sentiment analysis
└── support_agent.py        # OutputAgentNode with sentiment-aware responses
```

## API Reference

- [Agents — Overview](https://atoms-docs.smallest.ai/dev/build/agents/overview)
- [Core Concepts — Nodes](https://atoms-docs.smallest.ai/dev/introduction/core-concepts/nodes)

## Next Steps

- [Language Switching](../language_switching/) — Chained node pipelines with `add_edge()`
- [Interrupt Control](../interrupt_control/) — Mute/unmute control
