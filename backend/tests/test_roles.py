def test_create_and_list_roles(client):
    client.post("/api/roles", json={"name": "Designer"})
    client.post("/api/roles", json={"name": "Analyst"})

    resp = client.get("/api/roles")
    assert resp.status_code == 200
    assert [r["name"] for r in resp.json()] == ["Analyst", "Designer"]


def test_create_duplicate_role_name(client):
    client.post("/api/roles", json={"name": "QA"})

    resp = client.post("/api/roles", json={"name": "QA"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Role with this name already exists"


def test_create_role_requires_name(client):
    assert client.post("/api/roles", json={"name": ""}).status_code == 422


def test_rename_role_updates_all_assignees(client, role):
    assignee = client.post("/api/assignees", json={"name": "Ivan", "role_id": role["id"]}).json()

    resp = client.patch(f"/api/roles/{role['id']}", json={"name": "Backend Developer"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Backend Developer"

    assignees = client.get("/api/assignees").json()
    assert assignees[0]["id"] == assignee["id"]
    assert assignees[0]["role"]["name"] == "Backend Developer"


def test_rename_role_to_existing_name_is_rejected(client):
    first = client.post("/api/roles", json={"name": "QA"}).json()
    client.post("/api/roles", json={"name": "Designer"})

    resp = client.patch(f"/api/roles/{first['id']}", json={"name": "Designer"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Role with this name already exists"


def test_rename_unknown_role_returns_404(client):
    assert client.patch("/api/roles/999", json={"name": "QA"}).status_code == 404


def test_delete_role_with_assignees_is_forbidden(client, role):
    client.post("/api/assignees", json={"name": "Ivan", "role_id": role["id"]})

    resp = client.delete(f"/api/roles/{role['id']}")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Cannot delete role with assigned assignees"
    assert len(client.get("/api/roles").json()) == 1


def test_delete_unused_role(client):
    role = client.post("/api/roles", json={"name": "Temporary"}).json()

    assert client.delete(f"/api/roles/{role['id']}").status_code == 204
    assert client.get("/api/roles").json() == []


def test_delete_unknown_role_returns_404(client):
    assert client.delete("/api/roles/999").status_code == 404


def test_assignee_with_unknown_role_id_is_rejected(client):
    resp = client.post("/api/assignees", json={"name": "Ivan", "role_id": 999})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Role not found"


def test_assignee_without_role(client):
    resp = client.post("/api/assignees", json={"name": "Petr"})
    assert resp.status_code == 201
    assert resp.json()["role"] is None


def test_assignee_role_can_be_cleared(client, assignee, role):
    resp = client.patch(f"/api/assignees/{assignee['id']}", json={"role_id": None})
    assert resp.status_code == 200
    assert resp.json()["role"] is None
