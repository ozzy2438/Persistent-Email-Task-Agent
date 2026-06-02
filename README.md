# Persistent Email Task Agent

A proactive assistant that remembers incoming work, tracks open tasks, and
carries context forward across conversations.

The core scenario is deliberately concrete: an email arrives Tuesday asking for
an Acme proposal by Friday. On Thursday the user asks, "Where did that Acme
thing land?" The agent checks open tasks, retrieves the original email context,
remembers the deadline, and offers the next action.

## Why This Project

The interesting problem is not a generic chat UI. It is reliable behavior over
time: context retrieval, durable task state, tool selection, structured model
output, debugging traces, and measurable evals.

See [the architecture notes](docs/architecture.md) and
[the interview pitch](docs/elevator-pitch.md). The [roadmap](docs/roadmap.md)
keeps production follow-ups explicit.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run the Demo

```bash
python demo.py
persistent-agent demo
```

The default `demo` backend is deterministic and needs no API key or GPU.

## Run the Evals

```bash
pytest
ruff check .
persistent-agent-eval
```

The eval harness checks the behavior chain, not only the final response. It
asserts required tool calls, response content, and latency budgets, then writes
`eval/reports/latest.md`.

## Run the API

```bash
uvicorn persistent_agent.app.api:app --reload --port 8080
```

Useful endpoints:

- `GET /health`
- `GET /tasks`
- `POST /emails`
- `POST /chat`

Example ingestion:

```bash
curl -X POST http://localhost:8080/emails \
  -H "content-type: application/json" \
  --data @data/sample_emails/acme_proposal.json
```

The same API runs in Docker:

```bash
docker compose up --build app
```

## Model Backends

Use the self-contained demo backend by default:

```bash
MODEL_BACKEND=demo persistent-agent demo
```

For OpenAI or an OpenAI-compatible local vLLM endpoint, set:

```bash
MODEL_BACKEND=vllm
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_MODEL=Qwen/Qwen2.5-7B-Instruct
```

`docker compose --profile gpu up vllm` starts the optional vLLM service.
`docker compose --profile production up qdrant` starts Qdrant for the documented
production vector-store extension.

## Current Scope

The repository ships a complete, runnable MVP. It uses lexical retrieval over a
separate SQLite semantic-memory table so reviewers can run it immediately.
Production extensions are explicit: add a Qdrant adapter and embeddings cache,
connect a real email provider, add background reminders, and compare model
backends with a broader eval set.
