
"""Persistencia SQLite para Industrial IoT Platform."""

import csv
import io
import sqlite3
import threading

from datetime import datetime, timezone
from pathlib import Path


DATABASE_PATH = (
    Path(__file__).resolve().parent / "industrial_iot.db"
)

_db_lock = threading.RLock()


def connect():
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10
    )

    connection.row_factory = sqlite3.Row
    connection.execute(
        "PRAGMA busy_timeout = 10000"
    )

    return connection


def initialize_database():
    with _db_lock, connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                temperature_c REAL NOT NULL,
                air_speed_ms REAL NOT NULL,
                power_percent REAL NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS alarm_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                active INTEGER NOT NULL
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_measurements_time
            ON measurements(timestamp)
        """)

        conn.commit()


def save_measurement(state):
    with _db_lock, connect() as conn:
        conn.execute("""
            INSERT INTO measurements (
                timestamp,
                temperature_c,
                air_speed_ms,
                power_percent
            )
            VALUES (?, ?, ?, ?)
        """, (
            state["timestamp"],
            state["temperature_c"],
            state["air_speed_ms"],
            state["power_percent"]
        ))

        conn.commit()


def save_alarm_event(timestamp, alarm):
    with _db_lock, connect() as conn:
        conn.execute("""
            INSERT INTO alarm_events (
                timestamp,
                level,
                message,
                active
            )
            VALUES (?, ?, ?, ?)
        """, (
            timestamp,
            str(alarm.get("level", "DESCONOCIDO")),
            str(alarm.get("message", "")),
            int(bool(alarm.get("active", False)))
        ))

        conn.commit()


def get_measurements(limit=100):
    with connect() as conn:
        rows = conn.execute("""
            SELECT *
            FROM measurements
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return [dict(row) for row in rows]


def get_alarm_events(limit=100):
    with connect() as conn:
        rows = conn.execute("""
            SELECT *
            FROM alarm_events
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return [dict(row) for row in rows]


def get_statistics():
    with connect() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*) AS total_measurements,
                ROUND(AVG(temperature_c), 2)
                    AS avg_temperature_c,
                ROUND(MAX(temperature_c), 2)
                    AS max_temperature_c,
                ROUND(AVG(air_speed_ms), 2)
                    AS avg_air_speed_ms
            FROM measurements
        """).fetchone()

    return dict(row)


def export_measurements_csv():
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "id",
        "timestamp",
        "datetime_utc",
        "temperature_c",
        "air_speed_ms",
        "power_percent"
    ])

    with connect() as conn:
        cursor = conn.execute("""
            SELECT *
            FROM measurements
            ORDER BY id ASC
        """)

        for row in cursor:
            timestamp = row["timestamp"]

            date = datetime.fromtimestamp(
                timestamp,
                tz=timezone.utc
            ).isoformat()

            writer.writerow([
                row["id"],
                timestamp,
                date,
                row["temperature_c"],
                row["air_speed_ms"],
                row["power_percent"]
            ])

    return output.getvalue()
