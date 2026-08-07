from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="HockeyTime Finder API",
    version="0.2.0",
    description="Aggregated hockey session finder and calendar feed.",
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "name": "HockeyTime Finder",
        "status": "ok",
        "docs": "/docs",
        "events": "/api/events",
        "calendar": "/calendar.ics",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
