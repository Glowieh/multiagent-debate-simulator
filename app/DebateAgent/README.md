# DebateAgent

Python LangGraph agent packaged for Amazon Bedrock AgentCore.

## Entrypoint

`main.py` is the AgentCore streaming entrypoint (`@app.entrypoint`). It is not a standalone Starlette/FastAPI server.

## Local development

Use the repo root [README.md](../../README.md):

- `pnpm dev:api` — FastAPI SSE server on port 8000
- `pnpm dev:frontend` — Vite dev UI (proxies `/api` to the API)

Optional: `pnpm agentcore:dev` to exercise the AgentCore dev path.

## Environment variables

See [.env.example](../../.env.example) at the repo root. Set `USE_LOCAL_LLM=true` to route LLM calls to Ollama locally.

## Deployment

Follow [deployment-checklist.md](../../deployment-checklist.md). Copy `agentcore/aws-targets.example.json` to `agentcore/aws-targets.json` and fill in your account/region before `pnpm agentcore:deploy`.
