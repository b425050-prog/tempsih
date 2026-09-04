# 02 — Model-1 Implementation and Calibration

## Implemented equation

The prototype implements only the handbook’s Autoregressive Fair Mandi Price Predictor:

`Pₜ = α₀ + α₁Pₜ₋₁ − γ ln(Aₜ) + βWₜ`

Where:

- `Pₜ` is today’s predicted fair mandi price in rupees per quintal.
- `Pₜ₋₁` is yesterday’s official modal mandi price.
- `Aₜ` is today’s total arrivals in quintals.
- `ln(Aₜ)` is the natural logarithm of arrivals.
- `Wₜ` is the weather anomaly index.

## Active coefficients

| Coefficient | Stored value | Meaning |
|---|---:|---|
| `α₀` | 250 | Intercept |
| `α₁` | 0.90 | Autoregressive price weight |
| `γ` | 15 | Arrival elasticity |
| `β` | 40 | Weather weight |

## Handbook calculation

For `Pₜ₋₁ = 2200`, `Aₜ = 500`, and `Wₜ = 1.5`:

`Pₜ = 250 + (0.90 × 2200) − (15 × ln(500)) + (40 × 1.5)`

The implementation uses the full-precision natural logarithm:

`Pₜ ≈ 2196.7809`

The user interface therefore displays the rounded baseline **₹2,197 per quintal**.

## Coefficient calibration check

The local database contains 15 synthetic formula-recovery observations. For each observation, the design row is:

`xᵢ = [1, Pᵢ₋₁, −ln(Aᵢ), Wᵢ]`

The coefficient vector is:

`θ = [α₀, α₁, γ, β]ᵀ`

Ordinary least squares solves:

`(XᵀX)θ = Xᵀy`

The implementation constructs the normal matrix and solves its four-variable linear system using Gaussian elimination with partial pivoting. This avoids a dependency on external numerical packages while preserving deterministic offline execution.

Because the 15 bundled records are deliberately generated from the handbook equation, the recovered values are approximately:

- `α₀ = 250.000000`
- `α₁ = 0.900000`
- `γ = 15.000000`
- `β = 40.000000`
- Formula-check RMSE: below `0.000000001`
- Formula-check R²: `1.000000`

These diagnostics prove that the implementation and coefficient recovery are mathematically consistent. They are not a claim of predictive accuracy on real market data.

## Validation rules

- Yesterday’s price must be greater than zero.
- Arrivals must be greater than zero because `ln(0)` is undefined.
- Weather index must remain between `−10` and `+10`.
- The database must provide at least four independent calibration observations.
- Singular calibration systems are rejected instead of producing unstable coefficients.

## Source file

The complete formula, calibration solver, validation rules, and diagnostic calculations are in `model_1_implementation.py`.
