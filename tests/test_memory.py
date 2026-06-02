from persistent_agent.memory.store import MemoryStore


def test_memory_keeps_semantic_notes_and_task_state_separate() -> None:
    memory = MemoryStore()
    memory.remember("Tuesday email: send the Acme proposal by Friday.")
    email = memory.save_email("manager@company.com", "Acme proposal", "Send it by Friday.")
    task = memory.save_task("Prepare Acme proposal", "manager email", "Friday", source_email_id=email.id)

    assert "Tuesday email" in memory.semantic_search("Acme")[0]
    assert memory.list_tasks(keyword="acme")[0].id == task.id
    assert memory.list_tasks(keyword="acme")[0].source_email_id == email.id
    assert memory.get_email(email.id).subject == "Acme proposal"
    assert memory.search_email_text("Friday")[0].id == email.id

    memory.close_task(task.id)
    assert memory.list_tasks(keyword="acme") == []
