# LangGraph Debate Simulator

A LangGraph-based multi-agent debating simulator with a React frontend and AWS Bedrock AgentCore deployment target.

See [AGENTS.md](AGENTS.md) for project overview and conventions.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python dependencies and virtual envs
- Node.js 20+
- [pnpm](https://pnpm.io/) — sole Node package manager (no npm, no global installs)
- [Ollama](https://ollama.com/) with `llama3.2` pulled (for local LLM development)
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
ollama pull llama3.2
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
│   ├── main.py          # AgentCore entrypoint
│   ├── api/             # FastAPI server (local dev + streaming)
│   └── debate/          # LangGraph domain (state, graph, nodes, agents)
├── frontend/            # React + Vite UI
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
