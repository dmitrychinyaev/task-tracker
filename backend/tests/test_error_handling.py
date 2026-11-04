import logging
from urllib.parse import urlsplit

from sqlalchemy.exc import OperationalError

from app.config import settings
from app.core.logging_config import LOG_FORMAT, redact_database_url, setup_logging
from app.database import get_db
from app.main import app


def test_health_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_unhandled_error_returns_json(error_client, caplog):
    with caplog.at_level(logging.ERROR, logger="app.main"):
        resp = error_client.get("/api/health/error")

    assert resp.status_code == 500
    assert resp.headers["content-type"].startswith("application/json")
    assert resp.json() == {"detail": "Internal Server Error. Please contact support."}


def test_unhandled_error_is_logged_with_traceback(error_client, caplog):
    with caplog.at_level(logging.ERROR, logger="app.main"):
        error_client.get("/api/health/error")

    assert "ValueError: Test exception" in caplog.text
    assert "GET /api/health/error" in caplog.text
    assert any(record.exc_info for record in caplog.records)


def test_database_error_returns_safe_json(error_client, caplog):
    def broken_db():
        raise OperationalError("SELECT 1", {}, Exception("connection lost"))
        yield  # pragma: no cover - keeps the dependency a generator

    app.dependency_overrides[get_db] = broken_db
    try:
        with caplog.at_level(logging.ERROR, logger="app.main"):
            resp = error_client.get("/api/assignees")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 500
    assert resp.json() == {"detail": "Database error occurred"}
    assert "OperationalError" in caplog.text
    assert any(record.exc_info for record in caplog.records)


def test_database_url_is_redacted():
    redacted = redact_database_url("postgresql://user:sup3rsecret@db.example.com:5432/tasktracker")

    assert "sup3rsecret" not in redacted
    assert redacted == "postgresql://user:***@db.example.com:5432/tasktracker"


def test_configured_database_url_password_is_not_redacted_to_plaintext():
    password = urlsplit(settings.database_url).password
    if not password:  # pragma: no cover - local sqlite style DSN without password
        return

    assert password not in redact_database_url(settings.database_url)


def test_error_logs_do_not_contain_database_password(error_client, caplog):
    password = urlsplit(settings.database_url).password
    with caplog.at_level(logging.DEBUG):
        resp = error_client.get("/api/health/error")

    assert resp.status_code == 500
    if password:  # pragma: no cover - DSN without password
        assert password not in caplog.text


def test_setup_logging_uses_single_stdout_handler_with_project_format():
    setup_logging("INFO")

    root = logging.getLogger()
    assert len(root.handlers) == 1
    handler = root.handlers[0]
    assert handler.formatter._fmt == LOG_FORMAT
    assert root.level == logging.INFO
