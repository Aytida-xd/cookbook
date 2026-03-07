#!/usr/bin/env python3
"""
LangChain tools for the voice AI agent.

These are example tools the agent can call during a voice conversation.
Replace with your own tools (CRM lookup, database queries, APIs, etc.).

Usage:
    from tools import get_all_tools
    tools = get_all_tools()

Related integrations from this directory:
    - For STT/TTS as LangChain tools (so the agent can transcribe audio or
      generate speech), see:
      - ../stt-as-langchain-tool/stt_tool.py (PulseSTTTool)
      - ../tts-as-langchain-tool/tts_tool.py (LightningTTSTool)
    - Minimal copy-paste snippets: ../snippets/
"""

from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The city name to check weather for (e.g. "San Francisco", "New York")
    """
    weather_data = {
        "new york": "Sunny, 72°F (22°C)",
        "london": "Cloudy, 58°F (14°C)",
        "tokyo": "Clear, 68°F (20°C)",
        "paris": "Rainy, 55°F (13°C)",
        "san francisco": "Foggy, 62°F (17°C)",
        "los angeles": "Sunny, 78°F (26°C)",
        "chicago": "Windy, 65°F (18°C)",
    }
    city_lower = city.lower().strip()
    if city_lower in weather_data:
        return f"Weather in {city}: {weather_data[city_lower]}"
    return f"Weather in {city}: Partly cloudy, 65°F (18°C)"


@tool
def check_order(order_number: str) -> str:
    """Check the status of a customer order.

    Args:
        order_number: The order number to look up (e.g. "45678")
    """
    orders = {
        "45678": {
            "status": "shipped",
            "shipped_date": "yesterday",
            "expected_delivery": "Thursday",
            "tracking": "1Z999AA10123456784",
        },
        "12345": {
            "status": "processing",
            "expected_ship": "tomorrow",
            "tracking": None,
        },
        "99999": {
            "status": "delivered",
            "delivered_date": "last Monday",
            "tracking": "1Z999AA10123456999",
        },
    }

    order = orders.get(order_number.strip())
    if not order:
        return f"Order {order_number} not found. Please check the number and try again."

    status = order["status"]
    if status == "shipped":
        return (
            f"Order {order_number}: Shipped {order['shipped_date']}. "
            f"Expected delivery: {order['expected_delivery']}. "
            f"Tracking: {order['tracking']}."
        )
    elif status == "processing":
        return f"Order {order_number}: Still processing. Expected to ship {order['expected_ship']}."
    elif status == "delivered":
        return f"Order {order_number}: Delivered {order['delivered_date']}."
    return f"Order {order_number}: Status is {status}."


@tool
def book_appointment(date: str, time: str, service: str = "general") -> str:
    """Book an appointment for the caller.

    Args:
        date: Date for the appointment (e.g. "next Monday", "2025-03-15")
        time: Time for the appointment (e.g. "2 PM", "14:00")
        service: Type of service (e.g. "general", "consultation", "follow-up")
    """
    return f"Appointment booked: {service} on {date} at {time}. Confirmation will be sent."


@tool
def transfer_to_human(department: str = "support") -> str:
    """Transfer the caller to a human agent in the specified department.

    Args:
        department: Department to transfer to (e.g. "support", "sales", "billing")
    """
    return f"Transferring to {department}. A human agent will be with you shortly."


def get_all_tools() -> list:
    """Return all available tools for the voice agent."""
    return [get_weather, check_order, book_appointment, transfer_to_human]
