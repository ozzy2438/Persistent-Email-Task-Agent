from persistent_agent.models.repair import parse_with_repair, try_parse_step


class RepairingClient:
    def generate(self, messages):
        return '{"step_type":"final_answer","final_answer":{"response":"repaired"}}'


CATALOG_MESSAGES = [
    {"role": "system", "content": "Available tools:\n- list_open_tasks(keyword): List tasks\n- search_memory(query): Search memory"},
]


def test_parser_accepts_json_code_fence() -> None:
    step = try_parse_step(
        '```json\n{"step_type":"final_answer","final_answer":{"response":"ok"}}\n```'
    )
    assert step.final_answer.response == "ok"


def test_invalid_json_is_repaired_once() -> None:
    outcome = parse_with_repair("not-json", RepairingClient(), [])
    assert outcome.attempts == 1
    assert outcome.step.final_answer.response == "repaired"


def test_parser_rejects_extra_fields() -> None:
    step = try_parse_step(
        '{"step_type":"final_answer","final_answer":{"response":"ok","extra":"nope"}}'
    )
    assert step is None


def test_parser_rejects_contradictory_payload() -> None:
    step = try_parse_step(
        '{"step_type":"tool_call","tool_call":{"tool_name":"list_open_tasks","arguments":{},"reasoning":"check"},"final_answer":{"response":"ok"}}'
    )
    assert step is None


def test_parser_rejects_unknown_tool_name() -> None:
    step = try_parse_step(
        '{"step_type":"tool_call","tool_call":{"tool_name":"delete_everything","arguments":{},"reasoning":"bad"}}',
        CATALOG_MESSAGES,
    )
    assert step is None


def test_parser_rejects_invalid_task_reference() -> None:
    messages = CATALOG_MESSAGES + [
        {
            "role": "user",
            "content": "[tool_result:list_open_tasks] [task-123] Prepare Acme proposal - deadline: Friday",
        }
    ]
    step = try_parse_step(
        '{"step_type":"final_answer","final_answer":{"response":"done","referenced_tasks":["task-999"]}}',
        messages,
    )
    assert step is None
