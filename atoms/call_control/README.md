# Call Control

Comprehensive call control: end calls, cold transfers, and warm transfers.

## Overview

This example demonstrates:
- **SDKAgentEndCallEvent** - End calls gracefully
- **Cold Transfer** - Immediate handoff to another agent
- **Warm Transfer** - Brief the receiving agent before handoff
- **Hold Music Options** - Different music styles while transferring

## Files

- `app.py` - Server entry point with transfer number configuration
- `support_agent.py` - Agent with all call control tools
- `pyproject.toml` - Project dependencies

## Tools Included

| Tool | Description | When to Use |
|------|-------------|-------------|
| `end_call` | End the call gracefully | User says "goodbye" |
| `cold_transfer` | Immediate transfer | User asks for "human" |
| `warm_transfer` | Brief supervisor first | User asks for "manager" |
| `lookup_order` | Look up order status | Business logic example |

## Setup

1. Install dependencies:
```bash
pip install smallestai python-dotenv loguru
```

2. Create `.env` file:
```bash
OPENAI_API_KEY=your_openai_key
```

3. Configure transfer numbers in `app.py`:
```python
agent = SupportAgent(
    cold_transfer_number="+1234567890",   # General support
    warm_transfer_number="+1987654321"    # Supervisor
)
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
Assistant: Great, glad I could help! Take care!
[Call ends]
```

**Cold Transfer**:
```
User: I need to speak to a real person
Assistant: I'll connect you to a human agent now. Please hold.
[User hears relaxing music, then connects to +1234567890]
```

**Warm Transfer**:
```
User: I need to speak to a supervisor about my billing issue
Assistant: I'll brief my supervisor and connect you right away.
[Supervisor receives: "Customer escalation: billing issue"]
[User hears uplifting music, then connects to supervisor]
```

## Key Code

### End Call

```python
from smallestai.atoms.agent.events import SDKAgentEndCallEvent

@function_tool()
async def end_call(self) -> None:
    """End the call gracefully."""
    await self.send_event(SDKAgentEndCallEvent())
```

### Cold Transfer (Immediate)

```python
from smallestai.atoms.agent.events import (
    SDKAgentTransferConversationEvent,
    TransferOption,
    TransferOptionType,
)

@function_tool()
async def cold_transfer(self) -> None:
    """Immediate transfer to human agent."""
    await self.send_event(
        SDKAgentTransferConversationEvent(
            transfer_call_number="+1234567890",
            transfer_options=TransferOption(
                type=TransferOptionType.COLD_TRANSFER
            ),
            on_hold_music="relaxing_sound"
        )
    )
```

### Warm Transfer (With Briefing)

```python
@function_tool()
async def warm_transfer(self, reason: str) -> None:
    """Brief supervisor first, then transfer."""
    await self.send_event(
        SDKAgentTransferConversationEvent(
            transfer_call_number="+1987654321",
            transfer_options=TransferOption(
                type=TransferOptionType.WARM_TRANSFER,
                private_handoff_option={
                    "type": "prompt",
                    "prompt": f"Customer escalation: {reason}"
                }
            ),
            on_hold_music="uplifting_beats"
        )
    )
```

## Transfer Types

| Type | Description | Use Case |
|------|-------------|----------|
| `COLD_TRANSFER` | Immediate handoff | Quick transfers, general support |
| `WARM_TRANSFER` | Agent briefs human first | Escalations, complex issues |

## Hold Music Options

| Option | Description |
|--------|-------------|
| `"ringtone"` | Standard ring tone |
| `"relaxing_sound"` | Calm, ambient music |
| `"uplifting_beats"` | Energetic, positive music |
| `"none"` | Silence |

## Next Steps

- See [Agent with Tools](../agent_with_tools) for custom business tools
- See [Getting Started](../getting_started) for basic agent setup
