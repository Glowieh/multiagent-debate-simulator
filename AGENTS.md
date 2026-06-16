# Project description

This project is a work-in-progress, LangGraph based multi-agent debating simulator.

The basic application flow is:

- the user gives a topic for the debate
- two agents debate from different points of view in a LangGraph loop for 3 turns each
- debaters can optionally call a Wikipedia tool for factual lookups (once per turn, limited loops)
- a separate agent summarizes the debate at the end

The debate is streamed to a simple React frontend as it happens via SSE.

# Project technologies

## Core stack

- Python 3.12 (AgentCore runtime)
- LangGraph + `langchain_core` (graph orchestration, messages, prompts)
- Provider adapters: `langchain-aws` (Bedrock), `langchain-ollama` (local)
- FastAPI + sse-starlette (local dev API)
- React 19 + TypeScript + Vite (frontend)
- uv for Python (installed on the machine)
- pnpm workspace for Node (installed on the machine) — sole package manager, never use npm
- Pyright for typing. Always use typing in Python and TypeScript.
- Ruff for linting / formatting in Python
- ESLint for frontend linting
- pytest for Python tests

## LLMs

- **Local dev:** Ollama `qwen2.5:3b` (`USE_LOCAL_LLM=true` in `.env`)
- **Production:** Amazon Bedrock Amazon Nova Micro (`eu.amazon.nova-micro-v1:0`)

## AWS & infrastructure

- AWS Bedrock AgentCore (`bedrock-agentcore` SDK, `@aws/agentcore` CLI, `@aws/agentcore-cdk`)
- Terraform — API Gateway, Lambda, Secrets Manager; S3 + CloudFront for frontend
- Lambda API proxy (`lambda/api-proxy/`) — JWT auth + SSE stream to AgentCore
- LangSmith tracing (API key via `.env` locally; Secrets Manager in production via `runtime_env.py`)
- GitHub Actions CI on pull requests (Python tests/lint/typecheck; frontend lint/build)

# Project structure

```
├── agentcore/           # AgentCore config, CDK stack, deploy targets
├── app/DebateAgent/     # Python agent
│   ├── main.py          # AgentCore entrypoint (streaming)
│   ├── api/             # FastAPI server (local dev SSE)
│   ├── debate/          # LangGraph domain (state, graph, nodes, agents, tools)
│   └── model/           # LLM provider wiring (Bedrock vs Ollama)
├── frontend/            # React + Vite UI
├── lambda/api-proxy/    # Auth + stream proxy Lambdas
├── terraform/
│   ├── frontend/        # S3 + CloudFront
│   └── api/             # API Gateway + Lambda + Secrets Manager
├── scripts/             # Build and deploy helpers
└── package.json         # pnpm workspace root + scripts
```

# Architecture

## Debate graph

- A single LangGraph (`debate/graph.py`) orchestrates the full debate flow.
- Two debater agents (red/green) alternate; each may invoke a Wikipedia tool node before finishing a turn.
- After both debaters complete `max_turns_per_debater` (default 3), a summarizer agent runs.
- The code is split into classes and different files under `debate/` for maintainability.

## Streaming & entrypoints

- **`main.py`** — AgentCore runtime entrypoint; streams debate events for AWS deployment.
- **`api/server.py`** — FastAPI SSE server for local development (`pnpm dev:api`).
- Shared streaming logic lives in `api/streaming/`.

## Local development

Run three processes from the repo root (see [README.md](README.md)):

1. AgentCore entrypoint or `pnpm agentcore:dev` — validates the deploy path
2. `pnpm dev:api` — FastAPI on port 8000
3. `pnpm dev:frontend` — Vite dev server (proxies `/api` to port 8000)

Set `USE_LOCAL_LLM=true` in `.env` to route agent calls to Ollama instead of Bedrock.

## Production (three AWS layers)

1. **AgentCore runtime** — runs `main.py`; LangGraph agent calls Bedrock.
2. **API Gateway + Lambda** (`terraform/api`) — password login (`POST /api/auth/login`), JWT-gated SSE proxy (`POST /api/debate/stream`) that invokes the AgentCore runtime. CORS allows a single CloudFront origin (`cors_allowed_origins[0]`).
3. **CloudFront + S3** (`terraform/frontend`) — hosts the React UI; built with `VITE_API_BASE_URL` pointing at the API Gateway base URL.

Operational deploy steps: [deployment-checklist.md](deployment-checklist.md).

# Deployment

- **AgentCore:** `pnpm agentcore:validate` / `pnpm agentcore:deploy` (CDK in `agentcore/cdk/`)
- **API & frontend infra:** Terraform in `terraform/api` and `terraform/frontend`
- **Frontend publish:** GitHub Actions on the `production` branch, or `pnpm deploy:frontend`

Deploy order: AgentCore runtime → frontend hosting (for CORS origin) → API (needs runtime ARN) → frontend build/deploy.

# Rules

- Never install global npm packages
- Always use virtual environments with Python (using uv)
- Never use classic LangChain high-level APIs (e.g. `AgentExecutor`); use LangGraph and `langchain_core` instead
- Always prefer top of the file imports in Python over importing inside functions
- Do not commit secrets (`.env`, real account IDs in `agentcore/aws-targets.json`, demo passwords)

# Planning instructions

- Ask questions if you're unsure or notice that there are tradeoffs involved
