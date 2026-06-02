from __future__ import annotations

import argparse
import json

from persistent_agent.agent.bootstrap import build_agent, seed_acme_scenario


def run_demo() -> None:
    agent = build_agent()
    seed_acme_scenario(agent)
    trace = agent.run("Where did that Acme thing land?")
    print(json.dumps(trace.model_dump(mode="json"), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Persistent email task agent")
    parser.add_argument("command", choices=["demo"], nargs="?", default="demo")
    args = parser.parse_args()
    if args.command == "demo":
        run_demo()


if __name__ == "__main__":
    main()

