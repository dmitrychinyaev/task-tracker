"""Application-wide logging configuration.

Every log record goes to stdout in a single, predictable format:

    [2026-11-04 12:00:00] INFO in main: Bwanabet Task Tracker starting

Uvicorn installs its own handlers, so those are detached and re-attached to
the root logger; otherwise messages such as "Application startup complete"
would keep the library default format.
"""

import logging
import os
import sys
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LEVEL = "INFO"

_UVICORN_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access")


def redact_database_url(url: str) -> str:
    """Return ``url`` with the password replaced by ``***``.

    Used for the single startup log line, so the database target stays
    observable without leaking credentials into the container logs.
    """
    if not url:
        return ""
    try:
        parts = urlsplit(url)
    except ValueError:  # pragma: no cover - defensive, malformed URL
        return "***"
    if parts.password is None:
        return url

    host = parts.hostname or ""
    if parts.port:
        host = f"{host}:{parts.port}"
    user = parts.username
    netloc = f"{user}:***@{host}" if user else f":***@{host}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def setup_logging(level: Optional[str] = None) -> None:
    """Configure stdout logging for the application and uvicorn.

    Safe to call more than once: previous handlers are dropped, so repeated
    calls (tests, reloads, imports) never duplicate log lines.
    """
    resolved = (level or os.getenv("LOG_LEVEL") or DEFAULT_LEVEL).upper()
    level_value = getattr(logging, resolved, None)
    if not isinstance(level_value, int):
        level_value = logging.INFO

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    logging.basicConfig(
        level=level_value,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=sys.stdout,
        force=True,
    )

    root = logging.getLogger()
    for handler in root.handlers:
        handler.setFormatter(formatter)

    for name in _UVICORN_LOGGERS:
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
        uvicorn_logger.setLevel(level_value)
