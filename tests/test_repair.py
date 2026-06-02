from persistent_agent.models.repair import parse_with_repair, try_parse_step


class RepairingClient:
    def generate(self, messages):
        return '{"step_type":"final_answer","final_answer":{"response":"repaired"}}'


def test_parser_accepts_json_code_fence() -> None:
    step = try_parse_step(
        '```json\n{"step_type":"final_answer","final_answer":{"response":"ok"}}\n```'
    )
    assert step.final_answer.response == "ok"


def test_invalid_json_is_repaired_once() -> None:
    outcome = parse_with_repair("not-json", RepairingClient(), [])
    assert outcome.attempts == 1
    assert outcome.step.final_answer.response == "repaired"

