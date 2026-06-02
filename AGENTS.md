# Persistent Email Task Agent Working Rules

## Coordination

- The main coordinator owns integration, verification, commits, and pushes.
- Use project-scoped subagents for bounded layer-specific work.
- Subagents must stay inside their assigned layer and must not commit or push.
- Prefer read-only parallel audits before starting a new implementation phase.
- Run only one write-heavy implementation stream at a time unless file ownership is disjoint.

## Delivery

- Keep each development step small enough for one focused commit.
- Run `pytest`, `ruff check .`, `persistent-agent-eval`, and `docker compose config`
  before pushing runtime changes.
- Use a separate commit and push for every completed development step.
- Do not claim metric improvements unless an eval report measures them.

## Architecture

- Keep semantic recall separate from structured task state.
- Treat model output as untrusted input. Validate it before tool execution or
  final-answer acceptance.
- Keep external side effects draft-only until explicit user approval exists.
- Preserve the API-key-free deterministic demo path.
