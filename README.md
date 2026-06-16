# LangGraph Debate Simulator

A LangGraph-based multi-agent debating simulator with a React frontend and AWS Bedrock AgentCore deployment target.

See [AGENTS.md](AGENTS.md) for project overview and conventions.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python dependencies and virtual envs
- Node.js 20+
- [pnpm](https://pnpm.io/) — sole Node package manager (no npm, no global installs)
- [Ollama](https://ollama.com/) with `qwen2.5:3b` pulled (for local LLM development)
- AWS credentials configured for Bedrock (production / when `USE_LOCAL_LLM` is unset)

## Setup

```bash
# Install Node dependencies (AgentCore CLI + frontend workspace)
pnpm install

# Install Python dependencies
cd app/DebateAgent && uv sync
```

Copy environment template:

```bash
cp .env.example .env
```

## Local development

Ensure Ollama is running and the model is available:

```bash
ollama serve          # if not already running
ollama pull qwen2.5:3b
```

Set `USE_LOCAL_LLM=true` in `.env` (the default in `.env.example`) to route agent calls to Ollama instead of Bedrock.

Run in three terminals from the repo root:

```bash
# 1 — AgentCore entrypoint (validates deploy path)
cd app/DebateAgent && uv run python main.py
# or: AGENTCORE_SKIP_INSTALL=1 pnpm agentcore:dev

# 2 — FastAPI SSE server for the React UI
pnpm dev:api

# 3 — React frontend (proxies /api to port 8000)
pnpm dev:frontend
```

Open http://localhost:5173, enter a debate topic, and watch the debate stream in via SSE.

## Project structure

```
├── agentcore/           # AgentCore config and CDK (deploy)
├── app/DebateAgent/     # Python agent
│   ├── main.py          # AgentCore entrypoint (streaming)
│   ├── api/             # FastAPI server (local dev + streaming)
│   └── debate/          # LangGraph domain (state, graph, nodes, agents)
├── frontend/            # React + Vite UI
├── lambda/api-proxy/    # Auth + stream proxy Lambdas (API Gateway)
├── terraform/
│   ├── frontend/        # S3 + CloudFront for static UI
│   └── api/             # API Gateway + Lambda + Secrets Manager
└── package.json         # pnpm workspace root + scripts
```

## AgentCore commands

All via locally installed CLI (no global install):

```bash
pnpm agentcore:validate
pnpm agentcore:invoke '{"topic":"Should AI replace teachers?"}'
pnpm agentcore:deploy   # requires AWS credentials and configured targets
```

Before deploy, install CDK dependencies:

```bash
pnpm install   # includes agentcore/cdk workspace
```

## Architecture

- **Single LangGraph** (`app/DebateAgent/debate/graph.py`) orchestrates the debate flow
- **FastAPI** streams debate events to React via SSE during local development
- **AgentCore** wraps the same graph for AWS deployment via `main.py`

A 3-turn debate loop runs two debater agents against each other, then a summarizer agent produces a final summary. Set `USE_LOCAL_LLM=false` to use Bedrock instead of Ollama.

## Production deployment

Operational steps: see [deployment-checklist.md](deployment-checklist.md).

Production splits the stack into three AWS layers:

1. **AgentCore runtime** — runs `main.py` and streams debate events from the LangGraph agent via Bedrock.
2. **API Gateway + Lambda** (`terraform/api`) — password login (`POST /api/auth/login`) and an SSE proxy (`POST /api/debate/stream`) that invokes the AgentCore runtime.
3. **CloudFront + S3** (`terraform/frontend`) — hosts the React UI; the UI calls the API Gateway base URL at build time.

Deploy in this order (each step produces values needed by the next):

### Prerequisites

- AWS CLI v2 and [Terraform](https://www.terraform.io/) ≥ 1.5
- Both Terraform stacks (`terraform/api` and `terraform/frontend`) pin `hashicorp/aws` `~> 6.26`
- AWS credentials with Bedrock, AgentCore, Lambda, API Gateway, S3, CloudFront, and Secrets Manager access
- `pnpm install` and `cd app/DebateAgent && uv sync` (same as local setup)
- Bedrock model access for **Amazon Nova Micro** (`eu.amazon.nova-micro-v1:0` in `.env.example`)

### 1. Deploy AgentCore runtime

Create a deployment target (once per account/region) in `agentcore/aws-targets.json`:

```json
[
  {
    "name": "default",
    "description": "Production",
    "account": "123456789012",
    "region": "eu-west-1"
  }
]
```

Validate and deploy (uses Bedrock — do **not** set `USE_LOCAL_LLM` for this path):

```bash
pnpm agentcore:validate
pnpm agentcore:deploy
```

Note the **runtime ARN** from deploy output or:

```bash
pnpm agentcore status --json
```

It looks like `arn:aws:bedrock-agentcore:eu-west-1:123456789012:runtime/...`.

### 2. Provision frontend hosting (S3 + CloudFront)

```bash
cd terraform/frontend
cp terraform.tfvars.example terraform.tfvars   # edit region/environment if needed
terraform init
terraform apply
terraform output frontend_url                # e.g. https://dxxx.cloudfront.net
```

Save `frontend_url` — API Gateway CORS must allow this origin.

### 3. Provision API (auth + stream proxy)

```bash
cd terraform/api
cp terraform.tfvars.example terraform.tfvars   # set agent_runtime_arn; optional overrides
terraform init
TF_VAR_demo_password='your-demo-password' terraform apply \
  -var="agent_runtime_arn=arn:aws:bedrock-agentcore:..." \
  -var='cors_allowed_origins=["https://dxxx.cloudfront.net"]'
terraform output api_base_url
```

`TF_VAR_demo_password` is the shared demo login password (stored in Secrets Manager; never commit it). Terraform builds the Lambda packages automatically via `scripts/build-api-proxy.sh`.

Copy `api_base_url` (no trailing slash) — the frontend needs it at build time.

#### CORS

The API allows exactly one browser origin for CORS. Deploy frontend hosting (step 2) before the API so you have a real CloudFront URL.

- Pass that URL as `cors_allowed_origins` — only the **first** list element is used; extra entries are ignored.
- The value must match the browser origin exactly (`https://dxxx.cloudfront.net`, including scheme).
- Terraform applies it to API Gateway OPTIONS preflight responses and to Lambda response headers via `CORS_ALLOWED_ORIGIN`.

Example (use your `terraform output frontend_url`):

```bash
-var='cors_allowed_origins=["https://dxxx.cloudfront.net"]'
```

### 4. Deploy the frontend

**Option A — GitHub Actions** (push to `production` branch)

One-time setup (see also `.github/workflows/deploy-frontend.yml`):

1. IAM role with GitHub OIDC trust for this repo’s `production` branch.
2. Role permissions: S3 sync on the frontend bucket, CloudFront invalidation on the distribution.
3. GitHub **Secrets**: `AWS_ROLE_ARN`, `FRONTEND_S3_BUCKET`, `FRONTEND_CLOUDFRONT_DISTRIBUTION_ID` (from `terraform/frontend` outputs).
4. GitHub **Variables**: `AWS_REGION`, `VITE_API_BASE_URL` (from `terraform output api_base_url`).

Push to `production` to build and deploy automatically.

**Option B — Manual deploy**

Add to the repo root `.env`:

```bash
FRONTEND_S3_BUCKET=...                      # terraform output frontend_bucket_name
FRONTEND_CLOUDFRONT_DISTRIBUTION_ID=...     # terraform output frontend_cloudfront_distribution_id
VITE_API_BASE_URL=...                       # terraform output api_base_url
```

Then:

```bash
pnpm deploy:frontend
```

### Verify

Open `frontend_url` in a browser, sign in with the demo password, and start a debate. The UI streams SSE from `api_base_url/api/debate/stream`, which proxies to the AgentCore runtime.

### Updating after code changes

| Change | Redeploy |
|--------|----------|
| Agent / graph (`app/DebateAgent/`) | `pnpm agentcore:deploy` |
| API proxy (`lambda/api-proxy/`) | `cd terraform/api && terraform apply` (rebuilds Lambdas) |
| Frontend (`frontend/`) | Push to `production` or `pnpm deploy:frontend` |
| Demo password | `TF_VAR_demo_password='...' terraform apply` in `terraform/api` |
