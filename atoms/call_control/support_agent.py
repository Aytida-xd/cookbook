"""Support agent with call control capabilities."""

import os
from typing import List

from dotenv import load_dotenv

from smallestai.atoms.agent.clients.openai import OpenAIClient
from smallestai.atoms.agent.clients.types import ToolCall, ToolResult
from smallestai.atoms.agent.events import (
    SDKAgentEndCallEvent,
    SDKAgentTransferConversationEvent,
    TransferOption,
    TransferOptionType,
)
from smallestai.atoms.agent.nodes import OutputAgentNode
from smallestai.atoms.agent.tools import ToolRegistry, function_tool

load_dotenv()


class SupportAgent(OutputAgentNode):
    """Customer support agent with call control capabilities."""

    def __init__(self, transfer_number: str = "+1234567890"):
        super().__init__(name="support-agent")
        self.transfer_number = transfer_number
        
        self.llm = OpenAIClient(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self.tool_registry.discover(self)
        self.tool_schemas = self.tool_registry.get_schemas()

        self.context.add_message({
            "role": "system",
            "content": """You are a customer support agent for TechCo.

You can help with:
- Product information
- Order status
- Technical issues

CALL CONTROL RULES:
1. When user says "goodbye", "bye", "that's all" → Use end_call tool
2. When user asks for "human", "supervisor", "real person" → Use transfer_to_human tool

Always be helpful and professional. Before ending, confirm the user doesn't need anything else.
Before transferring, let them know you're connecting them to a human.""",
        })

    async def generate_response(self):
        """Generate response with tool calling support."""

        response = await self.llm.chat(
            messages=self.context.messages,
            stream=True,
            tools=self.tool_schemas
        )

        tool_calls: List[ToolCall] = []

        async for chunk in response:
            if chunk.content:
                yield chunk.content
            if chunk.tool_calls:
                tool_calls.extend(chunk.tool_calls)

        if tool_calls:
            results: List[ToolResult] = await self.tool_registry.execute(
                tool_calls=tool_calls, parallel=True
            )

            self.context.add_messages([
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": str(tc.arguments),
                            },
                        }
                        for tc in tool_calls
                    ],
                },
                *[
                    {"role": "tool", "tool_call_id": tc.id, "content": str(result)}
                    for tc, result in zip(tool_calls, results)
                ],
            ])

            final_response = await self.llm.chat(
                messages=self.context.messages, stream=True
            )

            async for chunk in final_response:
                if chunk.content:
                    yield chunk.content

    @function_tool()
    async def end_call(self) -> None:
        """End the call gracefully. Use when the conversation is complete 
        and user says goodbye."""
        await self.send_event(SDKAgentEndCallEvent())
        return None

    @function_tool()
    async def transfer_to_human(self) -> None:
        """Transfer the call to a human support agent. Use when user 
        explicitly asks for a real person or supervisor."""
        await self.send_event(
            SDKAgentTransferConversationEvent(
                transfer_call_number=self.transfer_number,
                transfer_options=TransferOption(type=TransferOptionType.COLD_TRANSFER),
                on_hold_music="relaxing_sound"
            )
        )
        return None

    @function_tool()
    def lookup_order(self, order_id: str) -> str:
        """Look up order status.
        
        Args:
            order_id: The order ID to look up.
        """
        # Mock order data
        return f"Order {order_id}: Shipped on Jan 10, arriving Jan 15"
