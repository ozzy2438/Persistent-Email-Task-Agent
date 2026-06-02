from pathlib import Path

from persistent_agent.eval.harness import run_all


def test_eval_scenarios_pass(tmp_path: Path) -> None:
    summary = run_all(Path("eval/scenarios"), tmp_path / "report.md")
    assert len(summary.results) == 2
    assert summary.pass_rate() == 1.0

