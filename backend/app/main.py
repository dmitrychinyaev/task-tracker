from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assignees, images, prompts, reports, sprints, tags, tasks, telegram

app = FastAPI(title="Bwanabet Task Tracker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (assignees.router, tags.router, sprints.router, tasks.router, images.router, reports.router, prompts.router, telegram.router):
    app.include_router(router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
