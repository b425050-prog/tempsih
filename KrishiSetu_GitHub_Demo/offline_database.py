"""Offline SQLite database, seed records, and persistence helpers."""

from __future__ import annotations

from datetime import datetime
import math
from pathlib import Path
import sqlite3
import sys
from typing import Any

from model_1_implementation import (
    CalibrationSample,
    Coefficients,
    ModelInput,
    Prediction,
)


APP_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)
DATA_DIR = APP_DIR / "data"
DATABASE_PATH = DATA_DIR / "krishisetu.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS app_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS model_parameters (
    id INTEGER PRIMARY KEY,
    model_name TEXT NOT NULL,
    crop TEXT NOT NULL,
    market TEXT NOT NULL,
    intercept REAL NOT NULL,
    autoregressive_weight REAL NOT NULL,
    arrival_elasticity REAL NOT NULL,
    weather_weight REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS model_presets (
    id INTEGER PRIMARY KEY,
    crop TEXT NOT NULL,
    market TEXT NOT NULL,
    previous_price REAL NOT NULL,
    arrival_quantity REAL NOT NULL,
    weather_index REAL NOT NULL,
    note TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS calibration_observations (
    id INTEGER PRIMARY KEY,
    record_label TEXT NOT NULL,
    crop TEXT NOT NULL,
    market TEXT NOT NULL,
    previous_price REAL NOT NULL,
    arrival_quantity REAL NOT NULL,
    weather_index REAL NOT NULL,
    observed_price REAL NOT NULL,
    dataset_role TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS buyers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    verified INTEGER NOT NULL,
    active_demand_quintal REAL NOT NULL,
    grade TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS supplies (
    id TEXT PRIMARY KEY,
    farmer TEXT NOT NULL,
    quantity_quintal REAL NOT NULL,
    grade TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS demands (
    id TEXT PRIMARY KEY,
    buyer TEXT NOT NULL,
    capacity_quintal REAL NOT NULL,
    grade TEXT NOT NULL,
    surplus REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS model_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    crop TEXT NOT NULL,
    market TEXT NOT NULL,
    previous_price REAL NOT NULL,
    arrival_quantity REAL NOT NULL,
    weather_index REAL NOT NULL,
    predicted_price REAL NOT NULL
);
"""


CALIBRATION_INPUTS = [
    (1, "Record 01", 2200.0, 500.0, 1.5),
    (2, "Record 02", 2180.0, 540.0, 0.8),
    (3, "Record 03", 2215.0, 470.0, -0.3),
    (4, "Record 04", 2250.0, 430.0, 1.0),
    (5, "Record 05", 2130.0, 620.0, -1.2),
    (6, "Record 06", 2290.0, 390.0, 1.8),
    (7, "Record 07", 2240.0, 455.0, 0.4),
    (8, "Record 08", 2165.0, 575.0, -0.7),
    (9, "Record 09", 2310.0, 365.0, 2.1),
    (10, "Record 10", 2195.0, 510.0, 0.0),
    (11, "Record 11", 2275.0, 410.0, 1.3),
    (12, "Record 12", 2110.0, 690.0, -1.6),
    (13, "Record 13", 2235.0, 485.0, 0.6),
    (14, "Record 14", 2145.0, 640.0, -0.9),
    (15, "Record 15", 2300.0, 380.0, 1.9),
]


def _calibration_rows() -> list[tuple[Any, ...]]:
    """Build exact formula-check observations from the handbook coefficients."""
    rows: list[tuple[Any, ...]] = []
    for record_id, label, previous, arrivals, weather in CALIBRATION_INPUTS:
        observed = 250.0 + 0.90 * previous - 15.0 * math.log(arrivals) + 40.0 * weather
        rows.append(
            (
                record_id,
                label,
                "Tomato",
                "Pune APMC",
                previous,
                arrivals,
                weather,
                observed,
                "Synthetic coefficient-recovery check",
            )
        )
    return rows


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    """Create and seed the local dataset without any network access."""
    with connect() as connection:
        connection.executescript(SCHEMA)
        connection.executemany(
            "INSERT OR REPLACE INTO app_metadata(key, value) VALUES (?, ?)",
            [
                ("storage", "This device only"),
                ("dataset", "Illustrative prototype records"),
                ("model_scope", "Model-1 only"),
                ("calibration_records", "15 synthetic coefficient-recovery rows"),
            ],
        )
        connection.execute(
            """
            INSERT OR REPLACE INTO model_parameters(
                id, model_name, crop, market, intercept,
                autoregressive_weight, arrival_elasticity, weather_weight, active
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                "Autoregressive Fair Mandi Price Predictor",
                "Tomato",
                "Pune APMC",
                250.0,
                0.90,
                15.0,
                40.0,
            ),
        )
        connection.executemany(
            """
            INSERT OR REPLACE INTO calibration_observations(
                id, record_label, crop, market, previous_price,
                arrival_quantity, weather_index, observed_price, dataset_role
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            _calibration_rows(),
        )
        connection.execute("DELETE FROM calibration_observations WHERE id > 15")
        connection.execute(
            """
            INSERT OR REPLACE INTO model_presets(
                id, crop, market, previous_price, arrival_quantity,
                weather_index, note
            ) VALUES (1, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Tomato",
                "Pune APMC",
                2200.0,
                500.0,
                1.5,
                "Handbook worked example; illustrative values",
            ),
        )
        connection.executemany(
            "INSERT OR REPLACE INTO buyers VALUES (?, ?, ?, ?, ?)",
            [
                ("buyer-1", "Sahyadri Foods", 1, 24.0, "A"),
                ("buyer-2", "FreshCart Pune", 1, 15.0, "A"),
                ("buyer-3", "Nashik Processors", 1, 12.0, "B"),
            ],
        )
        connection.executemany(
            "INSERT OR REPLACE INTO supplies VALUES (?, ?, ?, ?)",
            [
                ("s1", "Savita Patil", 18.0, "A"),
                ("s2", "Ramesh Jadhav", 12.0, "A"),
                ("s3", "Meera Kale", 9.0, "B"),
            ],
        )
        connection.executemany(
            "INSERT OR REPLACE INTO demands VALUES (?, ?, ?, ?, ?)",
            [
                ("d1", "Sahyadri Foods", 24.0, "A", 312.0),
                ("d2", "FreshCart Pune", 15.0, "A", 238.0),
                ("d3", "Nashik Processors", 12.0, "B", 174.0),
            ],
        )


def get_coefficients() -> Coefficients:
    initialize_database()
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM model_parameters WHERE active = 1 ORDER BY id LIMIT 1"
        ).fetchone()
    if row is None:
        raise RuntimeError("No active Model-1 parameters were found.")
    return Coefficients(
        intercept=row["intercept"],
        autoregressive_weight=row["autoregressive_weight"],
        arrival_elasticity=row["arrival_elasticity"],
        weather_weight=row["weather_weight"],
    )


def get_preset() -> ModelInput:
    initialize_database()
    with connect() as connection:
        row = connection.execute("SELECT * FROM model_presets WHERE id = 1").fetchone()
    if row is None:
        raise RuntimeError("The demonstration preset is missing.")
    return ModelInput(
        crop=row["crop"],
        market=row["market"],
        previous_price=row["previous_price"],
        arrival_quantity=row["arrival_quantity"],
        weather_index=row["weather_index"],
    )


def get_calibration_samples() -> list[CalibrationSample]:
    initialize_database()
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT previous_price, arrival_quantity, weather_index, observed_price
            FROM calibration_observations ORDER BY id
            """
        ).fetchall()
    return [
        CalibrationSample(
            previous_price=row["previous_price"],
            arrival_quantity=row["arrival_quantity"],
            weather_index=row["weather_index"],
            observed_price=row["observed_price"],
        )
        for row in rows
    ]


def save_run(values: ModelInput, result: Prediction) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO model_runs(
                created_at, crop, market, previous_price,
                arrival_quantity, weather_index, predicted_price
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().astimezone().isoformat(timespec="seconds"),
                values.crop,
                values.market,
                values.previous_price,
                values.arrival_quantity,
                values.weather_index,
                result.fair_price,
            ),
        )


def recent_runs(limit: int = 8) -> list[sqlite3.Row]:
    initialize_database()
    with connect() as connection:
        return connection.execute(
            "SELECT * FROM model_runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()


def table_rows(table: str, limit: int = 100) -> tuple[list[str], list[tuple[Any, ...]]]:
    allowed = {
        "model_parameters",
        "model_presets",
        "calibration_observations",
        "model_runs",
        "buyers",
        "supplies",
        "demands",
        "app_metadata",
    }
    if table not in allowed:
        raise ValueError("Unknown local table.")
    initialize_database()
    with connect() as connection:
        cursor = connection.execute(f"SELECT * FROM {table} LIMIT ?", (limit,))
        columns = [item[0] for item in cursor.description]
        rows = [tuple(row) for row in cursor.fetchall()]
    return columns, rows


def database_counts() -> dict[str, int]:
    tables = [
        "model_parameters",
        "model_presets",
        "calibration_observations",
        "model_runs",
        "buyers",
        "supplies",
        "demands",
    ]
    initialize_database()
    with connect() as connection:
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in tables
        }
