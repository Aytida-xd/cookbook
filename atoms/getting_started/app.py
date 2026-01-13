"""Getting Started Example - SDK setup and outbound calls."""

import os
import time
import requests
from dotenv import load_dotenv
from loguru import logger

from smallestai.atoms import AtomsClient

load_dotenv()


def main():
    """Complete quickstart: initialize client, make outbound call, check analytics."""
    
    api_key = os.getenv("SMALLEST_API_KEY")
    agent_id = os.getenv("AGENT_ID")
    phone_number = os.getenv("PHONE_NUMBER", "+1234567890")
    
    logger.info("=" * 50)
    logger.info("ATOMS SDK - Getting Started")
    logger.info("=" * 50)
    
    # 1. Initialize client
    logger.info("1. Initializing client...")
    client = AtomsClient()
    logger.success("   Client ready")
    
    # 2. Make outbound call
    logger.info(f"2. Calling {phone_number}...")
    response = client.start_outbound_call(
        conversation_outbound_post_request={
            "agentId": agent_id,
            "phoneNumber": phone_number
        }
    )
    call_id = response.data.conversation_id
    logger.success(f"   Call started: {call_id}")
    
    # 3. Wait for call
    logger.info("3. Waiting for call to complete...")
    logger.info("   (Answer your phone and have a conversation)")
    time.sleep(30)
    
    # 4. Get analytics
    logger.info("4. Getting call analytics...")
    resp = requests.get(
        f"https://atoms.smallest.ai/api/v1/conversation/{call_id}",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    
    if resp.status_code == 200:
        data = resp.json()["data"]
        logger.info(f"   Status: {data.get('status')}")
        logger.info(f"   Duration: {data.get('duration')}s")
        
        transcript = data.get("transcript", [])
        if transcript:
            logger.info("   Transcript:")
            for msg in transcript[:5]:
                logger.info(f"   {msg.get('role')}: {msg.get('content', '')[:50]}...")
    else:
        logger.warning(f"   Call still in progress or failed: {resp.status_code}")
    
    logger.success("Done!")


if __name__ == "__main__":
    main()
