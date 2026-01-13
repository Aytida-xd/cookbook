# Getting Started

Your first Atoms agent - from zero to a running AI assistant.

## Overview

This example demonstrates:
- **OutputAgentNode** - The base class for conversational agents
- **generate_response()** - Streaming LLM responses
- **AtomsApp** - Running the agent server
- **Event handling** - Greeting users on join

## Files

- `app.py` - Server entry point
- `my_agent.py` - Simple conversational agent
- `pyproject.toml` - Project dependencies

## Setup

1. Install dependencies:
```bash
pip install smallestai python-dotenv loguru
```

2. Create `.env` file:
```bash
OPENAI_API_KEY=your_openai_key
```

## Running the Example

Start the server:
```bash
python app.py
```

Connect with the CLI:
```bash
smallestai agent chat
```

## Example Interaction

```
Assistant: Hello! I'm your AI assistant. How can I help you today?
You: What's the capital of France?
Assistant: The capital of France is Paris.
```

## Key Code

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

## Next Steps

- See [Agent with Tools](../agent_with_tools) for adding custom tools
- See [Call Control](../call_control) for ending calls and transfers
