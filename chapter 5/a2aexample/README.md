# A2A Travel Agent Example

A multi-agent travel planner demonstrating the **Agent-to-Agent (A2A) protocol** using [Strands Agents](https://github.com/strands-agents/sdk-python).

Two specialized agents (Weather and Flights) run as independent A2A servers. A travel orchestrator acts as the A2A client, connecting to both over HTTP to gather information and present a trip summary.

## Architecture

```
                    ┌──────────────────────────┐
                    │   Travel Orchestrator     │
                    │      (A2A Client)         │
                    │                           │
                    │  1. Discover agent cards   │
                    │  2. Send A2A messages      │
                    │  3. Extract responses      │
                    │  4. Print trip summary     │
                    └─────┬──────────────┬──────┘
                          │ HTTP         │ HTTP
                          │ (A2A)        │ (A2A)
                          ▼              ▼
                 ┌──────────────┐ ┌──────────────┐
                 │ Weather Agent│ │ Flights Agent│
                 │  :9001       │ │  :9002       │
                 │              │ │              │
                 │ Strands Agent│ │ Strands Agent│
                 │ + A2AServer  │ │ + A2AServer  │
                 │              │ │              │
                 │ Tool:        │ │ Tools:       │
                 │  get_weather │ │ search_flights│
                 │              │ │  book_flight │
                 └──────────────┘ └──────────────┘
```

## Files

| File | Role | Description |
|---|---|---|
| `weather_agent_server.py` | A2A Server | Weather lookup agent on port 9001 |
| `flights_agent_server.py` | A2A Server | Flight search & booking agent on port 9002 |
| `travel_orchestrator.py` | A2A Client | Calls both agents and prints a trip summary |

---

## How the Code Works

### 1. Weather Agent Server (`weather_agent_server.py`)

Creates a Strands `Agent` with a `@tool` called `get_weather` that looks up weather from a dictionary. The agent is wrapped in `A2AServer` and served on port 9001.

The server explicitly defines its **skills** — these get published in the **agent card** at `/.well-known/agent-card.json` so any A2A client can discover what this agent can do before sending a message.

```python
from a2a.types import AgentSkill

# Define skills that describe what this agent can do
WEATHER_SKILLS = [
    AgentSkill(
        id="get_weather",
        name="Get Weather",
        description="Returns current weather conditions for a given city...",
        tags=["weather", "temperature", "forecast", "travel"],
        examples=[
            "What is the weather in London?",
            "How hot is it in Dubai right now?",
        ],
    ),
]

# Create the Strands Agent with the tool
weather_agent = Agent(name="Weather Agent", tools=[get_weather], callback_handler=None)

# Serve it as an A2A server with explicit skills in the agent card
server = A2AServer(
    agent=weather_agent,
    host="127.0.0.1",
    port=9001,
    skills=WEATHER_SKILLS,   # <-- published in the agent card
    version="1.0.0",
)
server.serve()
```

The agent card served at `http://127.0.0.1:9001/.well-known/agent-card.json` looks like:

```json
{
  "name": "Weather Agent",
  "description": "Provides current weather information for cities around the world.",
  "version": "1.0.0",
  "protocolVersion": "0.3.0",
  "capabilities": { "streaming": true },
  "skills": [
    {
      "id": "get_weather",
      "name": "Get Weather",
      "description": "Returns current weather conditions...",
      "tags": ["weather", "temperature", "forecast", "travel"],
      "examples": ["What is the weather in London?", "..."]
    }
  ],
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"],
  "url": "http://127.0.0.1:9001/"
}
```

Key points:
- `AgentSkill` defines each capability with an id, name, description, tags, and example prompts
- `skills=WEATHER_SKILLS` passes them to `A2AServer` so they appear in the agent card
- The agent card is the A2A discovery mechanism — clients fetch it first to understand what the agent can do
- `@tool` registers a Python function as a tool the LLM can call at runtime
- `callback_handler=None` disables streaming output on the server side

### 2. Flights Agent Server (`flights_agent_server.py`)

Same pattern as the weather agent but with two tools and two skills. Runs on port 9002.

```python
FLIGHTS_SKILLS = [
    AgentSkill(
        id="search_flights",
        name="Search Flights",
        description="Searches for available flights between two cities...",
        tags=["flights", "search", "travel", "airlines", "booking"],
        examples=["Find flights from New York to London"],
    ),
    AgentSkill(
        id="book_flight",
        name="Book Flight",
        description="Books a specific flight for a passenger...",
        tags=["booking", "reservation", "flights", "travel"],
        examples=["Book flight AE303 for John Smith"],
    ),
]

flights_agent = Agent(name="Flights Agent", tools=[search_flights, book_flight], callback_handler=None)
server = A2AServer(agent=flights_agent, host="127.0.0.1", port=9002, skills=FLIGHTS_SKILLS, version="1.0.0")
server.serve()
```

### 3. Travel Orchestrator (`travel_orchestrator.py`)

This is the A2A client. It does not use an LLM — it simply sends A2A messages to the two agent servers and prints the results. Here's the flow:

#### Step 1: Build an A2A message

```python
def make_message(text: str) -> Message:
    return Message(
        kind="message",
        role=Role.user,
        parts=[Part(TextPart(kind="text", text=text))],
        message_id=uuid4().hex,
    )
```

This creates a standard A2A `Message` object with a text part, just like a user typing in a chat.

#### Step 2: Discover the agent and send the message

```python
async def send_a2a_message(base_url: str, text: str) -> str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as hc:
        # 1. Fetch the agent card from /.well-known/agent-card.json
        resolver = A2ACardResolver(httpx_client=hc, base_url=base_url)
        card = await resolver.get_agent_card()

        # 2. Create a non-streaming A2A client from the card
        config = ClientConfig(httpx_client=hc, streaming=False)
        client = ClientFactory(config).create(card)

        # 3. Send the message and iterate over response events
        msg = make_message(text)
        async for event in client.send_message(msg):
            ...
```

- `A2ACardResolver` fetches the agent card — a JSON document describing the agent's capabilities
- `ClientFactory` creates an A2A client configured for that specific agent
- `send_message` sends a JSON-RPC `message/send` request and yields response events

#### Step 3: Extract text from the response

The A2A server returns a **task** object containing **artifacts** (the final output). The orchestrator extracts the text:

```python
def extract_text(result) -> str:
    if hasattr(result, "artifacts") and result.artifacts:
        texts = []
        for artifact in result.artifacts:
            for part in artifact.parts:
                texts.append(part.root.text)
        return "".join(texts)
```

#### Step 4: Print the trip summary

```python
async def main(city, origin, destination):
    weather = await send_a2a_message(WEATHER_URL, f"What is the weather in {city}?")
    flights = await send_a2a_message(FLIGHTS_URL, f"Search flights from {origin} to {destination}")
    print(f"Weather: {weather}")
    print(f"Flights: {flights}")
```

---

## A2A Protocol Flow (What Happens on the Wire)

```
Orchestrator                          Weather Agent (:9001)
     │                                       │
     │  GET /.well-known/agent-card.json     │
     │ ────────────────────────────────────►  │
     │  ◄──── { name, description, skills }  │
     │                                       │
     │  POST / (JSON-RPC: message/send)      │
     │  { "What is the weather in London?" } │
     │ ────────────────────────────────────►  │
     │         Agent calls get_weather tool   │
     │  ◄──── { task with artifacts }        │
     │        "15°C, cloudy with rain"       │
     │                                       │
```

1. The client fetches the **agent card** to discover what the agent can do
2. The client sends a **message/send** JSON-RPC request with the user's question
3. The server's Strands Agent processes the message, calls its tools, and returns a **task** with **artifacts** containing the final text response

---

## Setup & Running

```bash
pip install -r requirements.txt
```

You need a Strands-compatible model provider configured (e.g. AWS Bedrock credentials).

Open three terminals:

```bash
# Terminal 1
python weather_agent_server.py

# Terminal 2
python flights_agent_server.py

# Terminal 3 — default demo (New York → London)
python travel_orchestrator.py

# Or specify city, origin, destination
python travel_orchestrator.py "Rome" "Paris" "Rome"
```

## Available Data

**Weather cities:** London, Paris, Tokyo, New York, Dubai, Sydney, Cancun, Rome, Bangkok, Reykjavik

**Flight routes:** London→Paris, New York→London, Tokyo→Sydney, Paris→Rome, Dubai→Bangkok, New York→Cancun
