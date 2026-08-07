from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
import threading

from app.models.event import HockeyEvent


DB_PATH = Path(__file__).resolve().parents[2] / "hockeytime_cache.db"
_LOCK = threading.Lock()


def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_cache():
    with _LOCK, _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS cached_events (
                event_key TEXT PRIMARY KEY,
                source_name TEXT NOT NULL,
                event_json TEXT NOT NULL,
                start_time TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_cached_source
            ON cached_events(source_name);

            CREATE INDEX IF NOT EXISTS idx_cached_start
            ON cached_events(start_time);

            CREATE TABLE IF NOT EXISTS cache_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )
        conn.commit()


def _key(event: HockeyEvent) -> str:
    return f"{event.provider}|{event.rink}|{event.id}"


def replace_source_events(source_name: str, events: list[HockeyEvent]):
    """
    Replace one provider/source atomically.

    Only call this after that source refreshed successfully. If the source fails,
    leave its previous cached data untouched.
    """
    init_cache()
    now = datetime.now(timezone.utc).isoformat()

    rows = [
        (
            _key(event),
            source_name,
            event.model_dump_json(),
            event.start.isoformat(),
            now,
        )
        for event in events
    ]

    with _LOCK, _connect() as conn:
        conn.execute(
            "DELETE FROM cached_events WHERE source_name = ?",
            (source_name,),
        )
        if rows:
            conn.executemany(
                """
                INSERT OR REPLACE INTO cached_events
                (event_key, source_name, event_json, start_time, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                rows,
            )
        conn.commit()


def get_cached_events() -> list[HockeyEvent]:
    init_cache()
    with _LOCK, _connect() as conn:
        rows = conn.execute(
            """
            SELECT event_json
            FROM cached_events
            ORDER BY start_time ASC
            """
        ).fetchall()

    events = []
    for row in rows:
        try:
            events.append(HockeyEvent.model_validate_json(row["event_json"]))
        except Exception:
            continue
    return events


def set_meta(key: str, value):
    init_cache()
    if not isinstance(value, str):
        value = json.dumps(value)

    with _LOCK, _connect() as conn:
        conn.execute(
            """
            INSERT INTO cache_meta(key, value)
            VALUES(?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        conn.commit()


def get_meta(key: str, default=None):
    init_cache()
    with _LOCK, _connect() as conn:
        row = conn.execute(
            "SELECT value FROM cache_meta WHERE key = ?",
            (key,),
        ).fetchone()

    if not row:
        return default

    raw = row["value"]
    try:
        return json.loads(raw)
    except Exception:
        return raw


def cache_count() -> int:
    init_cache()
    with _LOCK, _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM cached_events"
        ).fetchone()
    return int(row["total"])


def source_counts() -> dict[str, int]:
    init_cache()
    with _LOCK, _connect() as conn:
        rows = conn.execute(
            """
            SELECT source_name, COUNT(*) AS total
            FROM cached_events
            GROUP BY source_name
            ORDER BY source_name
            """
        ).fetchall()
    return {row["source_name"]: int(row["total"]) for row in rows}
