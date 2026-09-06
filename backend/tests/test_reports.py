def test_kanban_report_generated(client, assignee):
    task_id = client.post("/api/tasks", json={"title": "Задача с кириллицей", "assignee_id": assignee["id"]}).json()["id"]
    client.post(f"/api/tasks/{task_id}/add-to-board", json={"status": "in_progress"})

    resp = client.get("/api/reports/kanban")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")


def test_task_report_generated(client, assignee):
    task_id = client.post("/api/tasks", json={"title": "Task with images", "assignee_id": assignee["id"]}).json()["id"]
    resp = client.get(f"/api/reports/task/{task_id}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")


def test_sprint_report_generated(client, assignee):
    sprint = client.post(
        "/api/sprints",
        json={"name": "Sprint A", "start_date": "2026-09-01", "end_date": "2026-09-14"},
    ).json()
    client.post(
        "/api/tasks",
        json={"title": "In sprint", "assignee_id": assignee["id"], "sprint_id": sprint["id"]},
    )
    resp = client.get(f"/api/reports/sprint/{sprint['id']}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")


def test_activity_report_generated(client, assignee):
    client.post("/api/tasks", json={"title": "Activity task", "assignee_id": assignee["id"]})
    resp = client.get("/api/reports/activity", params={"start": "2026-01-01", "end": "2026-12-31"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")
