# Chapter 4: Advanced Agent Architecture Patterns

Code examples from Chapter 4 of *Agents on AWS*.

## Notebooks

| Notebook | What It Covers |
|----------|---------------|
| `01_supervisor_worker.ipynb` | Supervisor-worker pattern — market research assistant with news, financial, and sentiment agents |
| `02_swarm_pattern.ipynb` | Swarm pattern — game level design with agents handing off to each other |
| `03_graph_pattern.ipynb` | Graph pattern — e-commerce order processing with explicit, auditable routing |

## Setup

```bash
pip install -r requirements.txt
```

Notebook 01 requires a Tavily API key for web search. Get one free at https://www.tavily.com/

> **Note on Bedrock models:** The notebooks use `Agent()` with no model specified — Strands defaults to Claude. If you get a `ResourceNotFoundException: Legacy model` error, set an explicit active model:
> ```python
> from strands.models.bedrock import BedrockModel
> model = BedrockModel(model_id="us.amazon.nova-lite-v1:0")
> agent = Agent(model=model, tools=[...])
> ```

## Prerequisites

- Python 3.10+
- AWS account with Bedrock access
- Completed Chapters 1-3
