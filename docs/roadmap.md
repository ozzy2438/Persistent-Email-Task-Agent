# Roadmap

The repository intentionally ships a narrow end-to-end slice first. The next
iterations should be measured against a broader eval set before adding surface
area.

## Priority 1: Retrieval Backend Comparison

- Add a `QdrantMemoryStore` adapter behind the current memory interface.
- Add an embedding provider and cache.
- Compare lexical SQLite retrieval with vector retrieval on paraphrased queries.

## Priority 2: Email and Scheduling Integrations

- Connect an email provider through OAuth.
- Add explicit user approval before sending replies or creating calendar events.
- Run reminder checks in a background worker with idempotency keys.

## Priority 3: Eval Coverage

- Grow the scenario set across task detection, memory carry-forward, tool
  selection, malformed structured output, and refusal behavior.
- Add backend-specific latency and cost reports.
- Calibrate an optional LLM judge against a small human-labeled set.

## Priority 4: Operations

- Add OpenTelemetry traces and structured logs.
- Track repair frequency, tool errors, model latency, and retrieval hit rate.
- Add durable migrations and a queue for background work.

