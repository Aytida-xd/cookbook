# Call Control

Agent that can end calls and transfer to human agents.

## Overview

This example demonstrates:
- **SDKAgentEndCallEvent** for ending calls
- **SDKAgentTransferConversationEvent** for transfers
- **TransferOption** for cold/warm transfers

## Files

- `app.py` - Server entry point
- `support_agent.py` - Agent with call control tools
- `pyproject.toml` - Project dependencies

## Tools Included

| Tool | Description |
|------|-------------|
| `end_call` | End the call gracefully |
| `transfer_to_human` | Cold transfer to human agent |
| `lookup_order` | Look up order status |

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

## Example Interactions

**End Call**:
```
User: That's all I needed, goodbye!
Assistant: Great, glad I could help! Goodbye!
[Call ends]
```

**Transfer to Human**:
```
User: I need to speak to a real person
Assistant: I'll connect you to a human agent right now.
[Call transfers to +1234567890]
```

## Key Code

### End Call Event

```python
from smallestai.atoms.agent.events import SDKAgentEndCallEvent
from smallestai.atoms.agent.tools import function_tool

@function_tool()
async def end_call(self) -> None:
    """End the call gracefully."""
    await self.send_event(SDKAgentEndCallEvent())
    return None
```

### Transfer to Human

```python
from smallestai.atoms.agent.events import (
    SDKAgentTransferConversationEvent,
    TransferOption,
    TransferOptionType,
)

@function_tool()
async def transfer_to_human(self) -> None:
    """Transfer to a human agent."""
    await self.send_event(
        SDKAgentTransferConversationEvent(
            transfer_call_number="+1234567890",
            transfer_options=TransferOption(type=TransferOptionType.COLD_TRANSFER),
            on_hold_music="relaxing_sound"
        )
    )
    return None
```

### Transfer Types

| Type | Description |
|------|-------------|
| `COLD_TRANSFER` | Immediate handoff |
| `WARM_TRANSFER` | Agent briefs human first |

### On-Hold Music Options

- `"ringtone"` - Standard ring tone
- `"relaxing_sound"` - Calm hold music
- `"uplifting_beats"` - Energetic music
- `"none"` - Silence

## Next Steps

- See [Agent with Tools](../agent_with_tools) for custom tools
- See [Getting Started](../getting_started) for basic SDK usage
