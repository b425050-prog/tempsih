# 03 — Offline Database Design

## Storage

The prototype uses Python’s built-in SQLite support. The database file is `data/krishisetu.db`. No network connection, database server, or user account is required.

## Tables

| Table | Purpose | Seed rows |
|---|---|---:|
| `model_parameters` | Active Model-1 coefficients and scope | 1 |
| `calibration_observations` | Synthetic coefficient-recovery dataset | 15 |
| `model_presets` | Handbook input preset | 1 |
| `model_runs` | Results created by the user | 0 initially |
| `buyers` | Earlier prototype buyer records | 3 |
| `supplies` | Earlier prototype supply records | 3 |
| `demands` | Earlier prototype demand records | 3 |
| `app_metadata` | Offline storage and dataset labels | 4 |

## Calibration record fields

Each of the 15 calibration rows stores:

- record identifier and display label;
- crop and market;
- previous price;
- arrival quantity;
- weather index;
- observed formula-check price;
- dataset-role label.

## Persistence behavior

- Database creation and seed insertion are idempotent.
- Existing `model_runs` are not deleted when the application restarts.
- Every successful Model-1 calculation inserts one timestamped run.
- Invalid inputs are rejected before anything is written.
- The packaged application creates the database beside its executable.

## Source file

Schema creation, the 15 seed rows, model-parameter loading, run persistence, and table viewing are implemented in `offline_database.py`.
