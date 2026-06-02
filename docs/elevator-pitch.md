# Elevator Pitch

I built a proactive assistant that remembers incoming work and carries it
forward over time. In the core scenario, an email arrives Tuesday asking for an
Acme proposal by Friday. On Thursday, the user asks vaguely where the Acme item
landed. The agent checks structured open tasks, retrieves the original context,
remembers the deadline, and proposes the next action.

The engineering point is the separation between semantic memory and task state.
Retrieval answers what we discussed; structured state answers what remains
unfinished. The agent loop validates each model response with Pydantic, repairs
malformed JSON once, falls back safely, and records a trace that feeds a small
eval harness. The repository runs without a GPU or API key and can switch to an
OpenAI-compatible endpoint such as vLLM for backend comparisons.

