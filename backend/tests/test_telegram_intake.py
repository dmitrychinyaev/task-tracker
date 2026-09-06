import base64
import io

from PIL import Image as PILImage


def _png_base64() -> str:
    buffer = io.BytesIO()
    PILImage.new("RGB", (2, 2), color=(255, 0, 0)).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _intake_payload(**overrides):
    payload = {
        "message_id": 101,
        "chat_id": 12345,
        "sender_user_id": 555,
        "sender_name": "Test User",
        "text": "Fix the login page",
    }
    payload.update(overrides)
    return payload


def test_telegram_intake_creates_inbox_task(client):
    resp = client.post("/api/telegram/intake", json=_intake_payload())
    assert resp.status_code == 201
    data = resp.json()
    assert data["created"] is True

    task = client.get(f"/api/tasks/{data['task_id']}").json()
    assert task["is_inbox"] is True
    assert task["source"] == "telegram"
    assert task["status"] == "backlog"
    assert task["assignee_id"] is None
    assert task["title"] == "Задача из Telegram - разобрать"
    assert task["telegram_metadata"]["sender_user_id"] == 555

    inbox = client.get("/api/tasks", params={"location": "inbox"}).json()
    assert any(t["id"] == task["id"] for t in inbox)


def test_telegram_intake_deduplicates_by_message_id(client):
    first = client.post("/api/telegram/intake", json=_intake_payload()).json()
    second = client.post("/api/telegram/intake", json=_intake_payload()).json()

    assert first["created"] is True
    assert second["created"] is False
    assert second["task_id"] == first["task_id"]


def test_telegram_intake_rejects_empty_message(client):
    resp = client.post("/api/telegram/intake", json=_intake_payload(text=""))
    assert resp.status_code == 400


def test_telegram_intake_with_photo(client):
    payload = _intake_payload(
        text="Screenshot attached",
        photos=[
            {
                "filename": "shot.png",
                "content_type": "image/png",
                "content": _png_base64(),
            }
        ],
    )
    resp = client.post("/api/telegram/intake", json=payload)
    assert resp.status_code == 201
    task = client.get(f"/api/tasks/{resp.json()['task_id']}").json()
    assert any(b["type"] == "image" for b in task["description"])


def test_inbox_task_can_move_to_backlog(client, assignee):
    task_id = client.post("/api/telegram/intake", json=_intake_payload()).json()["task_id"]

    resp = client.post(f"/api/tasks/{task_id}/move-to-backlog")
    assert resp.status_code == 400

    client.patch(f"/api/tasks/{task_id}", json={"assignee_id": assignee["id"]})

    resp = client.post(f"/api/tasks/{task_id}/move-to-backlog")
    assert resp.status_code == 200
    assert resp.json()["is_inbox"] is False
    assert resp.json()["status"] == "backlog"

    inbox = client.get("/api/tasks", params={"location": "inbox"}).json()
    assert all(t["id"] != task_id for t in inbox)

    backlog = client.get("/api/tasks", params={"location": "backlog"}).json()
    assert any(t["id"] == task_id for t in backlog)


def test_inbox_move_to_backlog_requires_assignee(client):
    task_id = client.post("/api/telegram/intake", json=_intake_payload()).json()["task_id"]

    resp = client.post(f"/api/tasks/{task_id}/move-to-backlog")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Assign an assignee before moving the task to backlog"


def test_move_to_backlog_rejects_non_inbox_task(client, assignee):
    task_id = client.post("/api/tasks", json={"title": "Manual", "assignee_id": assignee["id"]}).json()["id"]

    resp = client.post(f"/api/tasks/{task_id}/move-to-backlog")
    assert resp.status_code == 400
