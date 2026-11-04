import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def error_client(db_session):
    """Client that returns 500 responses instead of re-raising the exception.

    Starlette hands unhandled exceptions to ServerErrorMiddleware, which sends
    the response but still re-raises, so the error handlers can only be
    asserted with raise_server_exceptions=False.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def role(client):
    resp = client.post("/api/roles", json={"name": "Developer"})
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def assignee(client, role):
    resp = client.post("/api/assignees", json={"name": "Ivan", "role_id": role["id"]})
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def tag(client):
    resp = client.post("/api/tags", json={"name": "payment"})
    assert resp.status_code == 201
    return resp.json()
