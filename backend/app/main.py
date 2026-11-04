import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.api import assignees, health, images, prompts, reports, roles, sprints, tags, tasks, telegram
from app.config import settings
from app.core.logging_config import redact_database_url, setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Bwanabet Task Tracker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (assignees.router, roles.router, tags.router, sprints.router, tasks.router, images.router, reports.router, prompts.router, telegram.router, health.router):
    app.include_router(router)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Turn database failures into a safe JSON response with a logged traceback."""
    logger.exception("Database error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Database error occurred"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all handler: full traceback in the logs, no internals in the response."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Please contact support."},
    )

_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend_dist")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="static")

logger.info(
    "Bwanabet Task Tracker starting, database=%s",
    redact_database_url(settings.database_url),
)
