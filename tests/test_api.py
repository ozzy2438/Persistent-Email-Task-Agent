from pathlib import Path

from fastapi.testclient import TestClient

from persistent_agent.app.api import app


def test_api_ingests_email_and_lists_task(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MEMORY_DB_PATH", str(tmp_path / "memory.db"))
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        response = client.post(
            "/emails",
            json={
                "sender": "manager@company.com",
                "subject": "Acme proposal",
                "body": "Send it by Friday.",
                "task_title": "Prepare and send the Acme proposal",
                "deadline": "Friday",
            },
        )
        assert response.status_code == 200
        tasks = client.get("/tasks").json()
        assert tasks[0]["deadline"] == "Friday"

