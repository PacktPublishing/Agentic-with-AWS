# AI Agents on AWS

A collection of examples for building agentic AI applications using AWS services including Amazon Bedrock, SageMaker, and AgentCore.

## Chapters

| Chapter | Topic | Key Concepts |
|---|---|---|
| [Chapter 1](chapter%201/) | Hello World Agents | First agent with Strands, LangGraph basics |
| [Chapter 2](chapter%202/) | Building Agents with Tools | `@tool` decorator, prebuilt tools, AWS integration |
| [Chapter 3](chapter%203/) | Agent Memory | Short-term memory with LangGraph + AgentCore, long-term memory with Mem0 |
| [Chapter 4](chapter%204/) | Advanced Agent Patterns | Supervisor-worker, agent-as-tool, graph-based routing, swarm |
| [Chapter 5](chapter%205/) | MCP and A2A Protocols | MCP server/client, Agent-to-Agent communication |
| [Chapter 6](chapter%206/) | Deploying Agents to Production | AgentCore Runtime, ECS, Lambda deployments |
| [Chapter 7](chapter%207/) | Evaluation, Observability, and Governance | LLM-as-judge evaluation, OpenTelemetry tracing, Bedrock Guardrails, AgentCore Policy |

---

## Setup Guide

### Option 1: Amazon SageMaker Studio

#### Step 1: Create or update your SageMaker execution role

Your Studio domain execution role needs the following permissions. Add this as an inline policy in IAM:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:InvokeEndpoint",
        "sagemaker:DescribeEndpoint",
        "sagemaker:ListInferenceComponents",
        "sagemaker:DescribeInferenceComponent"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": ["arn:aws:s3:::*", "arn:aws:s3:::*/*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeAgentRuntime",
        "bedrock-agentcore:CreateAgentRuntime",
        "bedrock-agentcore:GetAgentRuntime"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Step 2: Enable Bedrock model access

Go to **AWS Console → Amazon Bedrock → Model Access** and enable:
- Amazon Nova Lite / Pro
- Anthropic Claude Haiku / Sonnet
- Any other models used in the examples

> **Important:** Bedrock model access must be enabled per region. If you get a `ResourceNotFoundException` with "Legacy model" or "Access denied", the model access has expired (Bedrock revokes access after 15 days of inactivity). Re-request access in the console or switch to an active model like `us.amazon.nova-lite-v1:0` which doesn't require approval.

**Recommended active models (no approval required):**
- `us.amazon.nova-lite-v1:0` — fast, cheap, always available
- `us.amazon.nova-pro-v1:0` — more capable

**Models requiring approval (may expire after inactivity):**
- `us.anthropic.claude-3-5-haiku-20241022-v1:0`
- `us.anthropic.claude-3-5-sonnet-20241022-v2:0`

#### Step 3: Configure your Studio Space

- Instance type: `ml.t3.medium` minimum (use `ml.g5.2xlarge` for local model testing)
- Disk size: at least **50 GB** (increase in Space settings)

#### Step 4: Clone and install

```bash
git clone https://github.com/PacktPublishing/Agentic-with-AWS
cd Agentic-with-AWS
pip install -r requirements.txt
```

Or install per chapter:

```bash
pip install strands-agents strands-agents-tools boto3 \
            langchain langchain-aws langgraph \
            bedrock-agentcore bedrock-agentcore-starter-toolkit
```

#### Step 5: Set environment variables

```bash
export AWS_DEFAULT_REGION=us-east-1
export BYPASS_TOOL_CONSENT=true   # required for Strands agents
```

---

### Option 2: Local IDE (VS Code, Kiro, or any IDE)

#### Step 1: Configure AWS credentials

**Option A — AWS CLI (recommended):**

```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region, output format
```

**Option B — AWS SSO:**

```bash
aws configure sso
aws sso login --profile your-profile
export AWS_PROFILE=your-profile
```

**Option C — Environment variables:**

```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1
```

#### Step 2: IAM permissions for your user/role

Your IAM user or role needs the following policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:InvokeEndpoint",
        "sagemaker:DescribeEndpoint",
        "sagemaker:ListInferenceComponents",
        "sagemaker:DescribeInferenceComponent",
        "sagemaker:CreateTrainingJob",
        "sagemaker:DescribeTrainingJob"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": ["arn:aws:s3:::*", "arn:aws:s3:::*/*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeAgentRuntime",
        "bedrock-agentcore:CreateAgentRuntime",
        "bedrock-agentcore:GetAgentRuntime",
        "bedrock-agentcore:ListAgentRuntimes"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::*:role/SageMaker*",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "sagemaker.amazonaws.com"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:GetLogEvents",
        "logs:DescribeLogStreams",
        "logs:DescribeLogGroups"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Step 3: Enable Bedrock model access

Same as SageMaker Studio — go to **AWS Console → Amazon Bedrock → Model Access** and enable the models you need. Make sure the region matches your `AWS_DEFAULT_REGION`.

> **Important:** Model access is per-region and expires after 15 days of inactivity. If you get `ResourceNotFoundException: Legacy model`, re-request access or use `us.amazon.nova-lite-v1:0` which is always available without approval.

#### Step 4: Install dependencies

```bash
pip install strands-agents strands-agents-tools boto3 \
            langchain langchain-aws langgraph \
            bedrock-agentcore bedrock-agentcore-starter-toolkit \
            sagemaker
```

#### Step 5: Set environment variables

Add to your shell profile (`~/.bashrc`, `~/.zshrc`) or a `.env` file:

```bash
export AWS_DEFAULT_REGION=us-east-1
export BYPASS_TOOL_CONSENT=true
```

For Kiro, credentials are picked up automatically from `~/.aws/credentials` or environment variables — no additional configuration needed.

#### Step 6: Verify your setup

```python
import boto3

# Test Bedrock
bedrock = boto3.client("bedrock", region_name="us-east-1")
models = bedrock.list_foundation_models()
print(f"✅ Bedrock OK — {len(models['modelSummaries'])} models available")

# Test SageMaker
sm = boto3.client("sagemaker", region_name="us-east-1")
endpoints = sm.list_endpoints()
print(f"✅ SageMaker OK — {len(endpoints['Endpoints'])} endpoints")
```

---

## Prerequisites Summary

| Requirement | SageMaker Studio | Local IDE |
|---|---|---|
| AWS credentials | Automatic (execution role) | `aws configure` or env vars |
| IAM permissions | Attach to execution role | Attach to IAM user/role |
| Bedrock model access | Enable in console | Enable in console |
| Python packages | `pip install` in notebook | `pip install` locally |
| Region | Set in Studio domain | `AWS_DEFAULT_REGION` env var |
| `BYPASS_TOOL_CONSENT` | Set in terminal | Set in shell profile |

## Requirements

- Python 3.10+
- AWS account with access to Amazon Bedrock
- AWS credentials configured (see Setup Guide above)
