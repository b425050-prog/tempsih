# 01 — Operating and Demonstrating KrishiSetu

## Starting the application

### Packaged application

1. Open the `KrishiSetu` release folder.
2. Double-click `KrishiSetu.exe`.
3. The application opens maximized and automatically adapts to the monitor resolution.

The packaged application requires no Python installation, package installation, account, network request, or remote server.

### Source-code launch

1. Install Python 3 with Tkinter.
2. Open the source folder.
3. Run `run.pyw`.

## Operating the Decision desk

The default values reproduce the handbook’s Tomato example:

- Crop: Tomato
- Market: Pune APMC
- Yesterday’s price: ₹2,200 per quintal
- Today’s arrivals: 500 quintals
- Weather shock index: +1.5

To calculate a price:

1. Enter or confirm the five Model-1 inputs.
2. Select **Run offline model**.
3. Read the rounded fair mandi price in the large result card.
4. Review the centered equation and the five-term calculation below it.
5. Select **Show full reasoning** for the substituted equation.

Each completed calculation is saved to the local `model_runs` table.

## Operating the Model lab

Select **Model lab** in the left navigation. The popup shows:

- the complete Model-1 equation;
- the four active coefficients;
- the number of calibration rows;
- the coefficients recovered by ordinary least squares;
- formula-check RMSE and R²;
- the explicit warning that the calibration rows are synthetic checks, not field-accuracy evidence.

## Operating the Data console

1. Select **Local data** or **Data console**.
2. Choose a table on the left.
3. Use **Calibration Observations** to inspect all 15 coefficient-recovery records.
4. Use **Model Parameters** to inspect the active coefficients.
5. Use **Model Runs** to inspect calculations saved during the demonstration.
6. Select **Back to decision desk** to return.

The database is stored as `data/krishisetu.db` beside the packaged application.

## Recommended three-minute judge demonstration

### 0:00–0:30 — Explain the problem

Say:

> “Before negotiating, a farmer needs a mathematically defensible fair mandi price. Model-1 turns yesterday’s price, today’s arrivals, and a weather shock into one transparent baseline.”

Point to the **Model 1 ready** indicator and the five input values.

### 0:30–1:15 — Run the handbook example

1. Keep the default values unchanged.
2. Select **Run offline model**.
3. Point to the rounded result: **₹2,197 per quintal**.
4. Point to the centered equation and term-by-term calculation.

Say:

> “The exact result is approximately ₹2,196.78, which rounds to ₹2,197 per quintal.”

### 1:15–2:00 — Defend the mathematics

Select **Show full reasoning** and explain:

- Intercept: `250`
- Price memory: `0.90 × 2,200 = 1,980`
- Arrival effect: `−15 × ln(500)`
- Weather effect: `40 × 1.5 = 60`

Say:

> “Every coefficient, input, and rupee contribution is visible. The calculation is deterministic and reproducible.”

Select **Model lab** and point out the coefficient-recovery diagnostics from the 15 local records.

### 2:00–2:40 — Prove offline persistence

1. Open **Data console**.
2. Select **Calibration Observations** and show the 15 rows.
3. Select **Model Runs** and show the newly saved result.

Say:

> “The interface, coefficients, calibration records, and run history remain in one SQLite file on this device.”

### 2:40–3:00 — State the boundary honestly

Select **Markets & routes** once to display the **Available soon** message.

Say:

> “This submission intentionally implements Model-1 only. Routing, lots, matching, and transactions remain visible as the planned product shell and are not presented as working features.”

## Offline proof

Disconnect Wi-Fi before launching. Run Model-1, open the Data console, close the application, reopen it, and show that the saved run remains available.

## Recovery

- If the release database is removed, close and reopen the application. It is recreated automatically.
- To restore the source database, run `initialize_database.py`.
- To restore the handbook inputs, enter `2200`, `500`, and `1.5`.
- If the window is behind another program, use Alt+Tab and select **KrishiSetu — Fair Mandi Price**.

## Claims to avoid

- Do not call the illustrative records live market data.
- Do not claim that Models 2 or 3 are implemented.
- Do not claim measured farmer-income impact.
- Do not describe the synthetic formula-check rows as field validation.
- Present ₹2,197 per quintal as the handbook example, not a current market quotation.
