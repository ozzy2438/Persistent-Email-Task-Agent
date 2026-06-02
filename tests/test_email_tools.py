from persistent_agent.memory.store import MemoryStore
from persistent_agent.tools.email_tools import DraftReply, ReadEmails, SummarizeThread


def seed_email_memory() -> MemoryStore:
    memory = MemoryStore()
    memory.save_email(
        sender="manager@company.com",
        subject="Acme proposal",
        body="Please send the Acme proposal by Friday.",
    )
    memory.save_email(
        sender="manager@company.com",
        subject="Acme proposal follow-up",
        body="Please include the pricing appendix as well.",
    )
    return memory


def test_read_emails_returns_typed_email_records() -> None:
    memory = seed_email_memory()
    output = ReadEmails().run(ReadEmails.args_schema(query="Acme", limit=2), memory=memory)

    assert "From: manager@company.com" in output
    assert "Acme proposal" in output


def test_summarize_thread_uses_local_email_store() -> None:
    memory = seed_email_memory()
    output = SummarizeThread().run(
        SummarizeThread.args_schema(query="appendix", limit=2),
        memory=memory,
    )

    assert "Thread summary for appendix" in output
    assert "pricing appendix" in output


def test_draft_reply_is_draft_only() -> None:
    memory = seed_email_memory()
    output = DraftReply().run(
        DraftReply.args_schema(query="Acme", guidance="Confirm that the revised draft will be sent today."),
        memory=memory,
    )

    assert output.startswith("DRAFT ONLY - NOT SENT")
    assert "Re: Acme proposal" in output
    assert "Confirm that the revised draft will be sent today." in output
