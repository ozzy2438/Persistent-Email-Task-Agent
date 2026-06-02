from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScenarioResult:
    id: str
    category: str
    passed: bool
    latency_ms: float
    cost_usd: float
    failures: list[str] = field(default_factory=list)


@dataclass
class EvalSummary:
    results: list[ScenarioResult]

    def pass_rate(self, category: str | None = None) -> float:
        items = [item for item in self.results if category is None or item.category == category]
        return sum(item.passed for item in items) / len(items) if items else 0.0

    def latency_percentile(self, percentile: float) -> float:
        latencies = sorted(item.latency_ms for item in self.results)
        if not latencies:
            return 0.0
        index = min(int(len(latencies) * percentile), len(latencies) - 1)
        return latencies[index]

    def total_cost(self) -> float:
        return sum(item.cost_usd for item in self.results)

