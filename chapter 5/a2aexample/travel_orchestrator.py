"""
Travel Orchestrator — A2A client that talks to Weather + Flights agents.

This is the A2A CLIENT side. It connects to two remote A2A agent servers,
sends them messages using the A2A protocol, and prints the results.

No LLM here — just direct A2A request/response.

Prerequisites:
    1. Start weather agent:  python weather_agent_server.py
    2. Start flights agent:  python flights_agent_server.py
    3. Run this:             python travel_orchestrator.py

Usage:
    python travel_orchestrator.py
    python travel_orchestrator.py "London" "New York" "London"
"""

import sys
import asyncio
import logging
from uuid import uuid4

# httpx: async HTTP client used to make requests to the A2A servers
import httpx

# A2ACardResolver: fetches the agent card from /.well-known/agent-card.json
# ClientConfig: configures the A2A client (streaming vs sync, timeout, etc.)
# ClientFactory: creates an A2A client from an agent card
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory

# A2A message types used to construct the request
# Message: the envelope for a user or agent message
# Part/TextPart: wraps the actual text content
# Role: identifies the sender (user or agent)
from a2a.types import Message, Part, Role, TextPart

# Set up logging so we can see A2A protocol activity
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URLs of the two A2A agent servers
WEATHER_URL = "http://127.0.0.1:9001"
FLIGHTS_URL = "http://127.0.0.1:9002"

# Timeout for HTTP requests (5 minutes — agents may take time with LLM calls)
TIMEOUT = 300


# --- Helper: Build an A2A Message ----------------------------------------
# Creates a standard A2A Message object that the server expects.
# This is the equivalent of a user typing a question in a chat.

def make_message(text: str) -> Message:
    return Message(
        kind="message",          # Always "message" for chat messages
        role=Role.user,          # We're the user sending a question
        parts=[Part(TextPart(    # Wrap the text in a TextPart inside a Part
            kind="text",
            text=text,
        ))],
        message_id=uuid4().hex,  # Unique ID for this message
    )


# --- Helper: Extract Text from A2A Response ------------------------------
# A2A servers return a "task" object. The actual answer text lives inside
# task.artifacts[].parts[].text. This function digs it out.

def extract_text(result) -> str:
    """Pull text out of an A2A task response (from artifacts)."""
    if hasattr(result, "artifacts") and result.artifacts:
        texts = []
        for artifact in result.artifacts:
            for part in artifact.parts:
                # The a2a SDK wraps parts in a discriminated union (Part.root)
                if hasattr(part, "root") and hasattr(part.root, "text"):
                    texts.append(part.root.text)
                elif hasattr(part, "text"):
                    texts.append(part.text)
        if texts:
            return "".join(texts)
    # Fallback: return the raw string representation
    return str(result)


# --- Core: Send a Message to an A2A Agent --------------------------------
# This is the main A2A client logic. It:
#   1. Fetches the agent card to discover capabilities
#   2. Auto-selects streaming or sync mode based on the card
#   3. Sends the message using the A2A protocol
#   4. Extracts and returns the text response

async def send_a2a_message(base_url: str, text: str) -> str:
    """Send a message to an A2A agent, auto-selecting streaming or sync based on the agent card."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as hc:

        # Step 1: Fetch the agent card from /.well-known/agent-card.json
        # This tells us the agent's name, skills, and whether it supports streaming
        resolver = A2ACardResolver(httpx_client=hc, base_url=base_url)
        card = await resolver.get_agent_card()

        # Step 2: Check the agent card capabilities to decide the mode
        # If the server advertises {"capabilities": {"streaming": true}},
        # we use SSE streaming; otherwise we use sync (single response)
        use_streaming = bool(card.capabilities and card.capabilities.streaming)
        mode = "streaming" if use_streaming else "sync"
        logger.info(f"Connected to: {card.name} — mode: {mode}")

        # Step 3: Create an A2A client configured for this agent
        # ClientConfig sets streaming mode; ClientFactory builds the client from the card
        config = ClientConfig(httpx_client=hc, streaming=use_streaming)
        client = ClientFactory(config).create(card)

        # Step 4: Send the message and process response events
        # In sync mode: yields one task with artifacts (the final answer)
        # In streaming mode: yields intermediate Messages + final task with artifacts
        msg = make_message(text)
        final_text = ""

        async for event in client.send_message(msg):
            # Task with artifacts — this is the final complete response
            if hasattr(event, "artifacts") and event.artifacts:
                final_text = extract_text(event)

            # (Task, UpdateEvent) tuple — check for artifacts on the task
            elif isinstance(event, tuple) and len(event) == 2:
                task, _ = event
                if hasattr(task, "artifacts") and task.artifacts:
                    final_text = extract_text(task)

            # Intermediate streaming Message — we skip these and wait for
            # the final artifacts which contain the complete answer
            elif isinstance(event, Message):
                pass

        return final_text if final_text else "No response received."


# --- Main: Orchestrate Calls to Both Agents ------------------------------
# Sends one request to the Weather Agent and one to the Flights Agent,
# then prints a combined trip summary.

async def main(city: str, origin: str, destination: str):
    print("=" * 60)
    print("  Travel Orchestrator (A2A)")
    print("=" * 60)

    # 1. Ask Weather Agent for current conditions at the destination
    print(f"\n>>> Asking Weather Agent: weather in {city}")
    weather = await send_a2a_message(WEATHER_URL, f"What is the weather in {city}?")
    print(f"<<< Weather Agent response:\n{weather}")

    # 2. Ask Flights Agent for available flights on the route
    print(f"\n>>> Asking Flights Agent: flights from {origin} to {destination}")
    flights = await send_a2a_message(FLIGHTS_URL, f"Search flights from {origin} to {destination}")
    print(f"<<< Flights Agent response:\n{flights}")

    # 3. Print a combined trip summary
    print("\n" + "=" * 60)
    print("  Trip Summary")
    print("=" * 60)
    print(f"\nDestination: {city}")
    print(f"Weather: {weather.strip()}")
    print(f"\nFlights ({origin} → {destination}):")
    print(flights.strip())


# --- Entry Point ---------------------------------------------------------
# Supports two modes:
#   - Default: demo with London / New York → London
#   - Custom:  pass city, origin, destination as arguments

if __name__ == "__main__":
    if len(sys.argv) == 4:
        # python travel_orchestrator.py <city> <origin> <destination>
        asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3]))
    else:
        # Default demo
        asyncio.run(main("London", "New York", "London"))
