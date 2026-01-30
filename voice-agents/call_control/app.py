"""Call Control Example - End calls and transfer to humans."""

from support_agent import SupportAgent
from loguru import logger

from smallestai.atoms.agent.events import SDKEvent, SDKSystemUserJoinedEvent
from smallestai.atoms.agent.server import AtomsApp
from smallestai.atoms.agent.session import AgentSession


async def setup_session(session: AgentSession):
    """Configure support agent with call control capabilities."""
    
    # Configure transfer numbers
    agent = SupportAgent(
        cold_transfer_number="+1234567890",   # General support
        warm_transfer_number="+1987654321"    # Supervisor/escalation
    )
    
    session.add_node(agent)
    await session.start()

    @session.on_event("on_event_received")
    async def on_event_received(_, event: SDKEvent):
        logger.info(f"Event received: {event.type}")

        if isinstance(event, SDKSystemUserJoinedEvent):
            await agent.speak(
                "Hi! I'm your support agent. I can help with orders, "
                "or connect you to a human. How can I assist?"
            )

    await session.wait_until_complete()
    logger.success("Session complete")


if __name__ == "__main__":
    app = AtomsApp(setup_handler=setup_session)
    app.run()
