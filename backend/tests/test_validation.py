def test_sprint_end_date_must_not_precede_start(client):
    resp = client.post(
        "/api/sprints",
        json={"name": "Sprint 1", "start_date": "2026-09-10", "end_date": "2026-09-01"},
    )
    assert resp.status_code == 400


def test_sprint_valid_dates(client):
    resp = client.post(
        "/api/sprints",
        json={"name": "Sprint 1", "start_date": "2026-09-01", "end_date": "2026-09-10"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "planned"


def test_duplicate_assignee_rejected(client):
    assert client.post("/api/assignees", json={"name": "Ivan"}).status_code == 201
    resp = client.post("/api/assignees", json={"name": "Ivan"})
    assert resp.status_code == 400


def test_duplicate_tag_rejected(client):
    assert client.post("/api/tags", json={"name": "bug"}).status_code == 201
    resp = client.post("/api/tags", json={"name": "bug"})
    assert resp.status_code == 400


def test_task_requires_existing_assignee(client):
    resp = client.post("/api/tasks", json={"title": "No assignee", "assignee_id": 9999})
    assert resp.status_code == 400
