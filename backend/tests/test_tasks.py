def test_create_task_records_history(client, assignee):
    resp = client.post("/api/tasks", json={"title": "New task", "assignee_id": assignee["id"]})
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "backlog"
    assert data["is_on_board"] is False
    assert data["is_archived"] is False

    detail = client.get(f"/api/tasks/{data['id']}").json()
    events = [h["event_type"] for h in detail["history"]]
    assert "task_created" in events


def test_move_to_blocked_requires_reason(client, assignee):
    task_id = client.post("/api/tasks", json={"title": "T", "assignee_id": assignee["id"]}).json()["id"]
    client.post(f"/api/tasks/{task_id}/add-to-board", json={"status": "todo"})

    resp = client.post(f"/api/tasks/{task_id}/move", json={"status": "blocked"})
    assert resp.status_code == 400

    resp = client.post(
        f"/api/tasks/{task_id}/move",
        json={"status": "blocked", "blocking_reason": "Waiting for API keys"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "blocked"
    assert data["blocked_reason"] == "Waiting for API keys"
    assert data["previous_status"] == "todo"


def test_unblock_clears_block_fields(client, assignee):
    task_id = client.post("/api/tasks", json={"title": "T", "assignee_id": assignee["id"]}).json()["id"]
    client.post(f"/api/tasks/{task_id}/add-to-board", json={"status": "in_progress"})
    client.post(f"/api/tasks/{task_id}/move", json={"status": "blocked", "blocking_reason": "Blocked"})

    resp = client.post(f"/api/tasks/{task_id}/move", json={"status": "todo"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "todo"
    assert data["blocked_reason"] is None
    assert data["previous_status"] is None

    detail = client.get(f"/api/tasks/{task_id}").json()
    events = [h["event_type"] for h in detail["history"]]
    assert "task_blocked" in events
    assert "task_unblocked" in events


def test_move_to_done_auto_archives(client, assignee):
    task_id = client.post("/api/tasks", json={"title": "T", "assignee_id": assignee["id"]}).json()["id"]
    client.post(f"/api/tasks/{task_id}/add-to-board", json={"status": "qa"})

    resp = client.post(f"/api/tasks/{task_id}/move", json={"status": "done"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert data["is_archived"] is True
    assert data["completed_at"] is not None

    # It should no longer appear on the active board.
    board = client.get("/api/tasks", params={"location": "board"}).json()
    assert all(t["id"] != task_id for t in board)

    # But it should appear in the archive.
    archive = client.get("/api/tasks", params={"location": "archive"}).json()
    assert any(t["id"] == task_id for t in archive)


def test_search_filters_by_title(client, assignee):
    client.post("/api/tasks", json={"title": "Fix payment bug", "assignee_id": assignee["id"]})
    client.post("/api/tasks", json={"title": "Write docs", "assignee_id": assignee["id"]})

    result = client.get("/api/tasks", params={"search": "payment"}).json()
    assert len(result) == 1
    assert result[0]["title"] == "Fix payment bug"
