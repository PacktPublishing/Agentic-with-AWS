"""
Weather Agent — A2A Server on port 9001.

Exposes a weather lookup tool via the Strands A2A protocol.

Run:  python weather_agent_server.py
"""

import logging

# Agent: the core Strands agent class that wraps an LLM with tools
# tool: decorator that registers a Python function as a tool the LLM can call
from strands import Agent, tool

# A2AServer: wraps a Strands Agent into an HTTP server that speaks the A2A protocol
from strands.multiagent.a2a import A2AServer

# AgentSkill: A2A SDK type that describes a capability in the agent card
from a2a.types import AgentSkill

# Set up logging so we can see what's happening during requests
logging.basicConfig(level=logging.INFO)

# --- Fake Weather Data ---------------------------------------------------
# In a real app this would call a weather API.
# Here we use a dictionary for demo purposes.

FAKE_WEATHER = {
    "london": "15°C, cloudy with occasional rain",
    "paris": "18°C, sunny with light breeze",
    "tokyo": "22°C, humid and partly cloudy",
    "new york": "12°C, windy and cool",
    "dubai": "38°C, hot and sunny",
    "sydney": "20°C, mild and clear",
    "cancun": "30°C, tropical and sunny",
    "rome": "24°C, warm and sunny",
    "bangkok": "33°C, hot and humid",
    "reykjavik": "5°C, cold and overcast",
}


# --- Weather Tool --------------------------------------------------------
# The @tool decorator registers this function so the LLM can call it.
# The docstring becomes the tool description the LLM sees when deciding
# which tool to use. Args/Returns are parsed for the tool's input schema.

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city.

    Args:
        city: Name of the city to get weather for.

    Returns:
        A string describing the current weather conditions.
    """
    # Normalize input: strip whitespace, lowercase for dictionary lookup
    result = FAKE_WEATHER.get(city.strip().lower())
    if result:
        return f"Weather in {city}: {result}"
    # If city not found, tell the user what cities are available
    return f"No weather data available for '{city}'. Available cities: {', '.join(FAKE_WEATHER.keys())}"


# --- Agent Card Skills ---------------------------------------------------
# Skills are published in the agent card at /.well-known/agent-card.json.
# Any A2A client fetches this card first to discover what the agent can do
# BEFORE sending any messages. Think of it like an API spec for agents.

WEATHER_SKILLS = [
    AgentSkill(
        # Unique identifier for this skill
        id="get_weather",
        # Human-readable name shown in the agent card
        name="Get Weather",
        # Detailed description — helps clients understand what this skill does
        description=(
            "Returns current weather conditions (temperature, sky, wind) "
            "for a given city. Supports: London, Paris, Tokyo, New York, "
            "Dubai, Sydney, Cancun, Rome, Bangkok, Reykjavik."
        ),
        # Tags for categorization and discovery
        tags=["weather", "temperature", "forecast", "travel"],
        # Example prompts — hints to clients on how to use this skill
        examples=[
            "What is the weather in London?",
            "How hot is it in Dubai right now?",
            "Tell me the weather conditions in Tokyo",
        ],
    ),
]

# --- Strands Agent -------------------------------------------------------
# This is the actual AI agent. It combines:
#   - An LLM (defaults to AWS Bedrock Claude if no model= is specified)
#   - A system prompt (instructions for the LLM)
#   - Tools (functions the LLM can call)
#
# When a message comes in, the agent sends it to the LLM. The LLM reads
# the system prompt, sees the available tools, and decides whether to call
# get_weather. If it does, the tool runs, and the LLM formats the final answer.

weather_agent = Agent(
    # Name and description — used in the A2A agent card
    name="Weather Agent",
    description="Provides current weather information for cities around the world.",
    # System prompt — instructions the LLM follows for every request
    system_prompt=(
        "You are a helpful weather assistant. Use the get_weather tool to look up "
        "weather conditions for any city the user asks about. Be concise and friendly."
    ),
    # Register the get_weather tool so the LLM can call it
    tools=[get_weather],
    # Disable streaming callback on the server side (responses are collected, not printed)
    callback_handler=None,
)

# --- A2A Server ----------------------------------------------------------
# Only runs when you execute this file directly (python weather_agent_server.py).
# Importing this file from another module won't start the server.

if __name__ == "__main__":
    # A2AServer wraps the Strands Agent into an HTTP server that:
    #   1. Serves an agent card at GET /.well-known/agent-card.json
    #   2. Accepts A2A messages at POST / (JSON-RPC: message/send, message/sendStream)
    #   3. Routes messages through the Strands Agent (LLM + tools)
    #   4. Returns responses as A2A task objects with artifacts
    server = A2AServer(
        # The Strands Agent that handles all incoming messages
        agent=weather_agent,
        # Bind to localhost only (use "0.0.0.0" to expose to network)
        host="127.0.0.1",
        # HTTP port to listen on
        port=9001,
        # Skills published in the agent card for client discovery
        skills=WEATHER_SKILLS,
        # Version string in the agent card
        version="1.0.0",
        # Use A2A-spec-compliant SSE streaming with artifact updates
        # (vs legacy status-only streaming). The agent card will advertise
        # {"capabilities": {"streaming": true}} so clients know SSE is supported.
        enable_a2a_compliant_streaming=True,
    )
    print("Weather Agent A2A server starting on http://127.0.0.1:9001")
    # Start the uvicorn HTTP server. This is a blocking call —
    # the process stays alive serving requests until you Ctrl+C.
    server.serve()
