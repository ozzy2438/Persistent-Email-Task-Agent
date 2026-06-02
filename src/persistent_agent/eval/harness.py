from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import yaml

from persistent_agent.agent.bootstrap import build_agent, seed_acme_scenario
from persistent_agent.eval.metrics import EvalSummary, ScenarioResult


def run_scenario(scenario: dict) -> ScenarioResult:
    agent = build_agent()
    if scenario.get("seed") == "acme":
        seed_acme_scenario(agent)
    started = time.perf_counter()
    trace = agent.run(scenario["input"])
    latency_ms = (time.perf_counter() - started) * 1000
    expectations = scenario["expectations"]
    failures = []
    for tool in expectations.get("must_call_tools", []):
        if tool not in trace.tool_calls:
            failures.append(f"missing_tool:{tool}")
    for tool in expectations.get("must_not_call_tools", []):
        if tool in trace.tool_calls:
            failures.append(f"unexpected_tool:{tool}")
    for phrase in expectations.get("response_must_mention", []):
        if phrase.lower() not in trace.final_response.lower():
            failures.append(f"missing_phrase:{phrase}")
    if latency_ms > expectations.get("max_latency_ms", float("inf")):
        failures.append(f"latency_exceeded:{latency_ms:.0f}ms")
    return ScenarioResult(
        id=scenario["id"],
        category=scenario["category"],
        passed=not failures,
        latency_ms=latency_ms,
        cost_usd=trace.cost_usd,
        failures=failures,
    )


def write_report(summary: EvalSummary, report_path: Path) -> None:
    categories = sorted({result.category for result in summary.results})
    lines = [
        "# Eval Report",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Scenarios | {len(summary.results)} |",
        f"| Overall pass rate | {summary.pass_rate():.0%} |",
        f"| Latency p50 | {summary.latency_percentile(0.50):.2f} ms |",
        f"| Latency p95 | {summary.latency_percentile(0.95):.2f} ms |",
        f"| Total model cost | ${summary.total_cost():.4f} |",
        "",
        "## Categories",
        "",
    ]
    lines.extend(f"- `{category}`: {summary.pass_rate(category):.0%}" for category in categories)
    lines.extend(["", "## Scenario Results", ""])
    for result in summary.results:
        status = "PASS" if result.passed else "FAIL"
        failures = ", ".join(result.failures) if result.failures else "none"
        lines.append(f"- `{result.id}`: {status} ({result.latency_ms:.2f} ms); failures: {failures}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n")


def run_all(scenario_dir: Path, report_path: Path) -> EvalSummary:
    scenarios = [yaml.safe_load(path.read_text()) for path in sorted(scenario_dir.glob("*.yaml"))]
    summary = EvalSummary([run_scenario(scenario) for scenario in scenarios])
    write_report(summary, report_path)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run persistent-agent eval scenarios")
    parser.add_argument("--scenarios", type=Path, default=Path("eval/scenarios"))
    parser.add_argument("--report", type=Path, default=Path("eval/reports/latest.md"))
    args = parser.parse_args()
    summary = run_all(args.scenarios, args.report)
    print(json.dumps({"scenarios": len(summary.results), "pass_rate": summary.pass_rate()}, indent=2))
    raise SystemExit(0 if summary.pass_rate() == 1 else 1)


if __name__ == "__main__":
    main()

