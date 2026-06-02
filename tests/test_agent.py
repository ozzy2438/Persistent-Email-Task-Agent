from persistent_agent.agent.bootstrap import build_agent, seed_acme_scenario


def test_agent_carries_acme_task_forward() -> None:
    agent = build_agent()
    seed_acme_scenario(agent)

    trace = agent.run("Where did that Acme thing land?")

    assert trace.tool_calls == ["list_open_tasks", "search_memory"]
    assert "Acme proposal is still open" in trace.final_response
    assert "Friday" in trace.final_response

