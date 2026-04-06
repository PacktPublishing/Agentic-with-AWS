# Chapter 2: Building Agents with Tools

Code examples from Chapter 2 of *Agents on AWS*.

## Notebooks

| Notebook | What It Covers |
|----------|---------------|
| `01_building_tools.ipynb` | Function → tool transformation, tip calculator, multi-tool sales assistant, custom inventory checker |
| `02_prebuilt_and_aws_tools.ipynb` | Pre-built community tools (calculator, http_request, file_write), AWS integration (S3, DynamoDB, Lambda) |
| `03_advanced_tool_patterns.ipynb` | Class-based tools for shared resources, async tools for parallel execution |

## Setup

```bash
pip install -r requirements.txt
```

AWS credentials must be configured for the AWS integration examples in notebook 02.

> **Note on Bedrock models:** The notebooks use `Agent()` with no model specified — Strands defaults to Claude. If you get a `ResourceNotFoundException: Legacy model` error, the default model has expired. Set an explicit active model at the top of the notebook:
> ```python
> from strands.models.bedrock import BedrockModel
> model = BedrockModel(model_id="us.amazon.nova-lite-v1:0")
> agent = Agent(model=model, tools=[...])
> ```

## Prerequisites

- Python 3.10+
- AWS account with Bedrock access
- Completed Chapter 1 setup
