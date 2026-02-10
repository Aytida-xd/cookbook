# Getting Started

Your first Atoms agent — from zero to a running AI assistant.

## Features

- **OutputAgentNode** — The base class for conversational agents
- **generate_response()** — Streaming LLM responses
- **AtomsApp** — Running the agent server
- **Event handling** — Greeting users on join

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

- Your starting point — the simplest possible Atoms agent with LLM responses
- Learning the core concepts: `OutputAgentNode`, `generate_response()`, `AtomsApp`
- For function calling, [Agent with Tools](../agent_with_tools/) is recommended

## Key Snippets

### Define an Agent

```python
from smallestai.atoms.agent.nodes import OutputAgentNode
from smallestai.atoms.agent.clients.openai import OpenAIClient

class MyAgent(OutputAgentNode):
    def __init__(self):
        super().__init__(name="my-agent")
        self.llm = OpenAIClient(model="gpt-4o-mini")

    async def generate_response(self):
        response = await self.llm.chat(
            messages=self.context.messages,
            stream=True
        )
        async for chunk in response:
            if chunk.content:
                yield chunk.content
```

### Run the Server

```python
from smallestai.atoms.agent.server import AtomsApp
from smallestai.atoms.agent.session import AgentSession

async def setup_session(session: AgentSession):
    agent = MyAgent()
    session.add_node(agent)
    await session.start()
    await session.wait_until_complete()

if __name__ == "__main__":
    app = AtomsApp(setup_handler=setup_session)
    app.run()
```

## Structure

```
getting_started/
├── app.py       # Server entry point
└── my_agent.py  # Simple conversational agent
```

## Example Output

```
Assistant: Hello! I'm your AI assistant. How can I help you today?
You: What's the capital of France?
Assistant: The capital of France is Paris.
```

## API Reference

- [Atoms SDK — Quick Start](https://atoms-docs.smallest.ai/dev/introduction/quickstart)
- [Core Concepts — Nodes](https://atoms-docs.smallest.ai/dev/introduction/core-concepts/nodes)

## Next Steps

- [Agent with Tools](../agent_with_tools/) — Add custom function tools the LLM can call
- [Call Control](../call_control/) — End calls and transfer to humans
