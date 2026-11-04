from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api import assignees, images, prompts, reports, roles, sprints, tags, tasks, telegram

app = FastAPI(title="Bwanabet Task Tracker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (assignees.router, roles.router, tags.router, sprints.router, tasks.router, images.router, reports.router, prompts.router, telegram.router):
    app.include_router(router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend_dist")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="static")