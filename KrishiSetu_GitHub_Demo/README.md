# KrishiSetu Model-1 Offline Demo

KrishiSetu is a native offline Python prototype of the Autoregressive Fair Mandi Price Predictor:

`Pₜ = α₀ + α₁Pₜ₋₁ − γ ln(Aₜ) + βWₜ`

The demo includes the Model-1 calculation, transparent term breakdown, 15 local calibration records, coefficient-recovery diagnostics, SQLite persistence, DPI-aware scaling through 8K, and placeholders for future modules.

## Fastest Windows launch

1. Download or clone this repository.
2. Extract `KrishiSetu_Windows_Portable.zip`.
3. Open the extracted `KrishiSetu` folder.
4. Double-click `KrishiSetu.exe`.

Keep the entire extracted folder together. The executable requires its adjacent `_internal`, `data`, and `docs` folders. It does not require a Python installation or network connection.

## Run directly from Python source

Requirements:

- Python 3.10 or later
- Tkinter, normally included with Windows and macOS Python distributions

Run:

```text
python run.pyw
```

On systems where the `python` command is named `python3`, run:

```text
python3 run.pyw
```

No third-party Python package is required. The local database is created automatically if `data/krishisetu.db` is missing.

## Handbook demonstration values

| Input | Value |
|---|---:|
| Crop | Tomato |
| Market | Pune APMC |
| Yesterday’s price | ₹2,200/q |
| Today’s arrivals | 500 q |
| Weather shock index | +1.5 |

Expected exact result: approximately `₹2,196.78/q`  
Displayed rounded result: `₹2,197/q`

## Repository contents

| Path | Purpose |
|---|---|
| `run.pyw` | Source launcher |
| `desktop_app.py` | DPI-aware desktop interface |
| `model_1_implementation.py` | Model equation, validation, calibration and diagnostics |
| `offline_database.py` | SQLite schema, 15-record seed dataset and run persistence |
| `initialize_database.py` | Manual database initialization utility |
| `assets/farmer-emblem.png` | Local agriculture emblem |
| `data/krishisetu.db` | Seeded offline database |
| `docs/` | Operating, demonstration, model and database documentation |
| `KrishiSetu_Windows_Portable.zip` | Standalone Windows demo |

## Documentation

- Start with `docs/01_OPERATING_AND_DEMONSTRATION_GUIDE.md`.
- Mathematical details are in `docs/02_MODEL_1_IMPLEMENTATION.md`.
- Database details are in `docs/03_OFFLINE_DATABASE.md`.
- The file inventory is in `docs/04_FILE_INDEX.md`.

## Prototype boundary

Only Model-1 is implemented. Markets and routes, lots, FPO matching, and transactions display an **Available soon** message. The 15 calibration rows are synthetic coefficient-recovery checks and must not be described as live market data or field-accuracy evidence.
