from persistent_agent.agent.bootstrap import build_agent, seed_acme_scenario


def main() -> None:
    agent = build_agent()
    seed_acme_scenario(agent)
    trace = agent.run("Where did that Acme thing land?")
    print("=== AGENT TRACE ===")
    for step in trace.steps:
        action = step.parsed_step.step_type
        if step.parsed_step.tool_call:
            action += f" -> {step.parsed_step.tool_call.tool_name}"
        print(f"[step {step.index}] {action} ({step.latency_ms:.2f}ms)")
        if step.tool_result:
            print(f"  {step.tool_result}")
    print(f"\n{trace.final_response}")


if __name__ == "__main__":
    main()

