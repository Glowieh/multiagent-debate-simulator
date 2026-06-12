# Project description

This project is a work-in-progress, LangGraph based multi-agent debating simulator.

The basic application flow is:

- the user gives a topic for the debate
- two agents debate from different points of view in a LangGraph loop for 3 turns each
- a separate agent summarizes the debate at the end

The debate is streamed to a simple React frontend as it happens.

# Project technologies

- Python
- LangGraph
- FastAPI
- React
- uv for Python (installed on the machine)
- pnpm for all React / Node related things, never use npm (pnpm is installed on the machine)
- Pyright for typing. Always use typing in Python and Typescript.
- Ruff for linting / formatting in Python
- Ollama llama3.2 for local development and testing purposes

# Architecture

- A single graph takes care of the debate flow.
- The code is split into classes and different files for maintainability

# Deployment

- The application will be deployed to AWS Bedrock AgentCore

# Rules

- Never install global npm packages
- Always use virtual environments with Python (using uv)
- Never use classic LangChain
- Always prefer top of the file imports in Python over importing inside functions

# Planning instructions

- Ask questions if you're unsure or notice that there are tradeoffs involved