"""Chapter 1: Hello World Agent using LangGraph with Amazon Bedrock."""

from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent


# Define a simple tool
@tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}! Welcome to the world of AI agents."


# Initialize the LLM via Bedrock
llm = init_chat_model(
    "anthropic.claude-3-5-haiku-20241022-v1:0",
    model_provider="bedrock_converse",
)

# Create a ReAct agent with the tool
agent = create_react_agent(model=llm, tools=[greet])

# Run the agent
response = agent.invoke(
    {"messages": [{"role": "user", "content": "Please greet Alice and Bob."}]}
)

# Print the final response
for message in response["messages"]:
    print(f"{message.type}: {message.text()}")
