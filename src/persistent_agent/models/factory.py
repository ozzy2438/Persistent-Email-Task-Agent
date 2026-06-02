from __future__ import annotations

import os

from openai import OpenAI

from persistent_agent.models.client import DemoModelClient, OpenAIStyleClient


def build_model_client():
    backend = os.getenv("MODEL_BACKEND", "demo").lower()
    if backend == "demo":
        return DemoModelClient()
    if backend not in {"openai", "vllm"}:
        raise ValueError(f"Unsupported MODEL_BACKEND: {backend}")

    api_key = os.getenv("OPENAI_API_KEY", "not-needed-for-local-vllm")
    base_url = os.getenv("OPENAI_BASE_URL") or None
    model = os.getenv("OPENAI_MODEL")
    if not model:
        raise ValueError("OPENAI_MODEL is required for openai and vllm backends")
    return OpenAIStyleClient(OpenAI(api_key=api_key, base_url=base_url), model=model)

