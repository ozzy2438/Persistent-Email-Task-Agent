from persistent_agent.memory.store import MemoryStore


def test_memory_keeps_semantic_notes_and_task_state_separate() -> None:
    memory = MemoryStore()
    memory.remember("Tuesday email: send the Acme proposal by Friday.")
    task = memory.save_task("Prepare Acme proposal", "manager email", "Friday")

    assert "Tuesday email" in memory.semantic_search("Acme")[0]
    assert memory.list_tasks(keyword="acme")[0].id == task.id

    memory.close_task(task.id)
    assert memory.list_tasks(keyword="acme") == []

