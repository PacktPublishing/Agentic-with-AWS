"""Chapter 1: Hello World Agent using Strands Agents SDK."""

from strands import Agent
from strands.models.bedrock import BedrockModel

# Use Nova Lite — always available, no approval expiry
# To use Claude instead: BedrockModel(model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0")
model = BedrockModel(model_id="us.amazon.nova-lite-v1:0")

agent = Agent(model=model)

response = agent("Hello! Tell me a fun fact about AI agents.")
print(response)
