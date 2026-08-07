from contextlib import asynccontextmanager
from pathlib import Path
import threading

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.services.event_cache import cache_count, init_cache
from app.services.refresh_service import refresh_cache
from app.services.scheduler_service import start_scheduler, stop_scheduler


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_cache()
    start_scheduler()

    # On first run, seed the cache without holding up application startup.
    if cache_count() == 0:
        threading.Thread(
            target=refresh_cache,
            kwargs={"reason": "startup"},
            daemon=True,
        ).start()

    yield

    stop_scheduler()


app = FastAPI(
    title="HockeyTime Finder API",
    version="0.6.0",
    description="Cached hockey session finder and calendar feed.",
    lifespan=lifespan,
)

app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "healthy"}
