# Getting Started

Complete quickstart: initialize the SDK, make an outbound call, and retrieve analytics.

## Overview

This example demonstrates:
- **AtomsClient** initialization
- **Outbound calls** to phone numbers
- **Analytics** retrieval via REST API

## Files

- `app.py` - Main entry point with full workflow
- `pyproject.toml` - Project dependencies

## Setup

1. Install dependencies:
```bash
pip install smallestai python-dotenv requests loguru
```

2. Create `.env` file:
```bash
SMALLEST_API_KEY=your_api_key
AGENT_ID=your_agent_id
PHONE_NUMBER=+1234567890
```

## Running the Example

```bash
python app.py
```

The script will:
1. Initialize the AtomsClient
2. Make an outbound call to the configured phone number
3. Wait for the call to complete
4. Retrieve and display call analytics

## Example Output

```
2024-01-15 10:30:00 | INFO | ==================================================
2024-01-15 10:30:00 | INFO | ATOMS SDK - Getting Started
2024-01-15 10:30:00 | INFO | ==================================================
2024-01-15 10:30:00 | INFO | 1. Initializing client...
2024-01-15 10:30:00 | SUCCESS | Client ready
2024-01-15 10:30:01 | INFO | 2. Calling +1234567890...
2024-01-15 10:30:02 | SUCCESS | Call started: CALL-1767900635803-8a3bee
2024-01-15 10:30:02 | INFO | 3. Waiting for call to complete...
2024-01-15 10:30:32 | INFO | 4. Getting call analytics...
2024-01-15 10:30:33 | INFO | Status: completed
2024-01-15 10:30:33 | INFO | Duration: 28s
2024-01-15 10:30:33 | SUCCESS | Done!
```

## Key Code

### Initialize Client

```python
from smallestai.atoms import AtomsClient

client = AtomsClient()
```

### Make Outbound Call

```python
response = client.start_outbound_call(
    conversation_outbound_post_request={
        "agentId": agent_id,
        "phoneNumber": "+1234567890"
    }
)
call_id = response.data.conversation_id
```

### Get Analytics

```python
import requests

resp = requests.get(
    f"https://atoms.smallest.ai/api/v1/conversation/{call_id}",
    headers={"Authorization": f"Bearer {api_key}"}
)
data = resp.json()["data"]
print(f"Duration: {data['duration']}s")
print(f"Status: {data['status']}")
```

## Next Steps

- See [Agent with Tools](../agent_with_tools) for adding custom tools
- See [Call Control](../call_control) for ending calls and transfers
