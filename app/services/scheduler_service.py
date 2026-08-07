from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.refresh_service import refresh_cache


_scheduler: BackgroundScheduler | None = None


def start_scheduler():
    global _scheduler

    if _scheduler and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler(
        timezone="UTC",
        daemon=True,
    )

    _scheduler.add_job(
        refresh_cache,
        trigger=IntervalTrigger(hours=6),
        kwargs={"reason": "scheduled"},
        id="calendar_refresh",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )

    _scheduler.start()
    return _scheduler


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
