"""
Flights Agent — A2A Server on port 9002.

Exposes flight search and booking tools via the Strands A2A protocol.

Run:  python flights_agent_server.py
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

# --- Fake Flight Data ----------------------------------------------------
# In a real app this would query a flights API or database.
# Here we use a dictionary keyed by (origin, destination) tuples.

FAKE_FLIGHTS = {
    ("london", "paris"): [
        {"airline": "AirEurope", "flight": "AE101", "depart": "08:00", "arrive": "10:30", "price": "$120"},
        {"airline": "SkyWings", "flight": "SW202", "depart": "14:00", "arrive": "16:30", "price": "$95"},
    ],
    ("new york", "london"): [
        {"airline": "TransAtlantic", "flight": "TA501", "depart": "22:00", "arrive": "10:00+1", "price": "$450"},
        {"airline": "AirEurope", "flight": "AE303", "depart": "18:00", "arrive": "06:00+1", "price": "$380"},
    ],
    ("tokyo", "sydney"): [
        {"airline": "PacificAir", "flight": "PA701", "depart": "09:00", "arrive": "20:00", "price": "$520"},
    ],
    ("paris", "rome"): [
        {"airline": "AirEurope", "flight": "AE150", "depart": "07:30", "arrive": "09:30", "price": "$85"},
        {"airline": "MedFly", "flight": "MF44", "depart": "12:00", "arrive": "14:00", "price": "$70"},
    ],
    ("dubai", "bangkok"): [
        {"airline": "GulfAir", "flight": "GA880", "depart": "02:00", "arrive": "12:00", "price": "$340"},
    ],
    ("new york", "cancun"): [
        {"airline": "SunJet", "flight": "SJ610", "depart": "06:00", "arrive": "10:00", "price": "$250"},
        {"airline": "SkyWings", "flight": "SW415", "depart": "11:00", "arrive": "15:00", "price": "$210"},
    ],
}


# --- Flight Tools --------------------------------------------------------
# Each @tool-decorated function becomes a tool the LLM can call.
# The docstring is what the LLM sees when deciding which tool to use.
# Args/Returns are parsed to build the tool's input schema automatically.


@tool
def search_flights(origin: str, destination: str) -> str:
    """Search for available flights between two cities.

    Args:
        origin: Departure city name.
        destination: Arrival city name.

    Returns:
        A formatted list of available flights or a message if none found.
    """
    # Normalize both cities to lowercase for dictionary lookup
    key = (origin.strip().lower(), destination.strip().lower())
    flights = FAKE_FLIGHTS.get(key)

    # If no flights found, show the user what routes are available
    if not flights:
        available = [f"{o.title()} -> {d.title()}" for o, d in FAKE_FLIGHTS.keys()]
        return (
            f"No flights found from {origin} to {destination}. "
            f"Available routes: {', '.join(available)}"
        )

    # Format each flight as a readable line
    lines = [f"Flights from {origin.title()} to {destination.title()}:"]
    for f in flights:
        lines.append(
            f"  {f['airline']} {f['flight']}: depart {f['depart']}, "
            f"arrive {f['arrive']}, price {f['price']}"
        )
    return "\n".join(lines)


@tool
def book_flight(flight_number: str, passenger_name: str) -> str:
    """Book a specific flight for a passenger.

    Args:
        flight_number: The flight number to book (e.g. AE101).
        passenger_name: Name of the passenger.

    Returns:
        Booking confirmation or error message.
    """
    # Search all routes for the matching flight number
    for flights in FAKE_FLIGHTS.values():
        for f in flights:
            if f["flight"].upper() == flight_number.strip().upper():
                # Generate a fake confirmation number from a hash
                return (
                    f"Booking confirmed! {passenger_name} is booked on "
                    f"{f['airline']} flight {f['flight']} "
                    f"(depart {f['depart']}, arrive {f['arrive']}). "
                    f"Total: {f['price']}. Confirmation #: TRV-{hash(flight_number + passenger_name) % 100000:05d}"
                )
    return f"Flight {flight_number} not found. Please search for available flights first."


# --- Agent Card Skills ---------------------------------------------------
# Skills are published in the agent card at /.well-known/agent-card.json.
# Any A2A client fetches this card first to discover what the agent can do
# BEFORE sending any messages. Think of it like an API spec for agents.

FLIGHTS_SKILLS = [
    AgentSkill(
        # Unique identifier for this skill
        id="search_flights",
        # Human-readable name shown in the agent card
        name="Search Flights",
        # Detailed description — helps clients understand what this skill does
        description=(
            "Searches for available flights between two cities. "
            "Returns airline, flight number, departure/arrival times, and price. "
            "Available routes: London→Paris, New York→London, Tokyo→Sydney, "
            "Paris→Rome, Dubai→Bangkok, New York→Cancun."
        ),
        # Tags for categorization and discovery
        tags=["flights", "search", "travel", "airlines", "booking"],
        # Example prompts — hints to clients on how to use this skill
        examples=[
            "Find flights from New York to London",
            "Search for flights from Paris to Rome",
            "What flights go from Dubai to Bangkok?",
        ],
    ),
    AgentSkill(
        id="book_flight",
        name="Book Flight",
        description=(
            "Books a specific flight for a passenger given a flight number "
            "and passenger name. Returns a booking confirmation with a "
            "confirmation number."
        ),
        tags=["booking", "reservation", "flights", "travel"],
        examples=[
            "Book flight AE303 for John Smith",
            "Reserve flight TA501 for Jane Doe",
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
# search_flights or book_flight. The tool runs, and the LLM formats the answer.

flights_agent = Agent(
    # Name and description — used in the A2A agent card
    name="Flights Agent",
    description="Searches for flights between cities and handles bookings.",
    # System prompt — instructions the LLM follows for every request
    system_prompt=(
        "You are a helpful flight booking assistant. Use search_flights to find "
        "available flights between cities, and book_flight to make reservations. "
        "Be concise and provide clear flight options."
    ),
    # Register both tools so the LLM can call them
    tools=[search_flights, book_flight],
    # Disable streaming callback on the server side (responses are collected, not printed)
    callback_handler=None,
)

# --- A2A Server ----------------------------------------------------------
# Only runs when you execute this file directly (python flights_agent_server.py).

if __name__ == "__main__":
    # A2AServer wraps the Strands Agent into an HTTP server that:
    #   1. Serves an agent card at GET /.well-known/agent-card.json
    #   2. Accepts A2A messages at POST / (JSON-RPC: message/send, message/sendStream)
    #   3. Routes messages through the Strands Agent (LLM + tools)
    #   4. Returns responses as A2A task objects with artifacts
    server = A2AServer(
        # The Strands Agent that handles all incoming messages
        agent=flights_agent,
        # Bind to localhost only (use "0.0.0.0" to expose to network)
        host="127.0.0.1",
        # HTTP port to listen on
        port=9002,
        # Skills published in the agent card for client discovery
        skills=FLIGHTS_SKILLS,
        # Version string in the agent card
        version="1.0.0",
        # Use A2A-spec-compliant SSE streaming with artifact updates
        enable_a2a_compliant_streaming=True,
    )
    print("Flights Agent A2A server starting on http://127.0.0.1:9002")
    # Start the uvicorn HTTP server — blocking call, runs until Ctrl+C
    server.serve()
