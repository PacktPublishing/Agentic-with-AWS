# Chapter 1: Hello World Agents

Minimal examples of building AI agents with Amazon Bedrock using two different frameworks.

## Examples

### 1. Strands Agents (`hello_world_agent.py`)

The simplest possible agent — one import, two lines of code. Uses the [Strands Agents SDK](https://github.com/strands-agents/sdk-python) with Bedrock as the default model provider.

```bash
python hello_world_agent.py
```

### 2. LangGraph Agent (`hello_world_langgraph_agent.py`)

A ReAct agent built with [LangGraph](https://github.com/langchain-ai/langgraph) that uses a custom tool. Demonstrates the graph-based agent pattern with Amazon Bedrock.

```bash
python hello_world_langgraph_agent.py
```

## Strands vs LangChain vs LangGraph

| | Strands Agents | LangChain | LangGraph |
|---|---|---|---|
| Approach | Simple agent-first SDK | Linear chain-based pipelines | Stateful graph-based orchestration |
| Complexity | Minimal boilerplate | Moderate | More setup, more control |
| State management | Built-in | Manual | Built-in with checkpointers |
| Best for | Quick agents, AWS-native workflows | Simple LLM chains, prompt templates | Complex multi-step agents with branching/cycles |
| Status | Active | Legacy `AgentExecutor` being phased out | Recommended for LangChain-ecosystem agents |

## When to Use Which

### Use Strands Agents when:
- You want the fastest path from zero to a working agent
- Your stack is AWS-native (Bedrock, SageMaker, AgentCore)
- You need built-in tool support (file I/O, web search, code execution) with minimal wiring
- You're building internal tools, prototypes, or single-purpose agents
- You prefer convention over configuration — sensible defaults, less boilerplate

### Use LangChain when:
- You need prompt templates, output parsers, or document loaders — not a full agent
- You're building a simple linear pipeline (e.g., RAG: retrieve → augment → generate)
- You want to use LangChain's ecosystem of integrations (vector stores, embeddings, retrievers)
- You don't need cycles, branching, or persistent state in your workflow

### Use LangGraph when:
- You need multi-step agents with complex control flow (loops, conditionals, parallel branches)
- Your agent requires persistent state or conversation memory across sessions
- You're building multi-agent systems where agents hand off tasks to each other
- You need human-in-the-loop approval steps mid-workflow
- You want fine-grained control over the execution graph (which node runs when, retry logic, error handling)
- You're already in the LangChain ecosystem and need to graduate from simple chains to full agents

### Quick Decision Guide

```
Need an agent fast on AWS?                    → Strands
Need a simple LLM chain (no agent loop)?      → LangChain
Need complex orchestration or multi-agent?    → LangGraph
Need persistent state across sessions?        → LangGraph or Strands (with AgentCore)
Building a prototype or demo?                 → Strands
Going to production with complex workflows?   → LangGraph
```

## Prerequisites

- Python 3.10+
- AWS account with access to Amazon Bedrock models
- AWS credentials configured (`aws configure` or environment variables)

## Getting Started

```bash
pip install -r requirements.txt
```

> **Note on Bedrock model access:** Models require explicit access in the AWS Console (Bedrock → Model Access). Access can expire after 15 days of inactivity — if you get a `ResourceNotFoundException: Legacy model` error, re-enable the model or switch to `us.amazon.nova-lite-v1:0` which is always available without approval.
