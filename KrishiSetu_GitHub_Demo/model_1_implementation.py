"""Model-1 implementation and coefficient-calibration mathematics."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


@dataclass(frozen=True)
class Coefficients:
    intercept: float
    autoregressive_weight: float
    arrival_elasticity: float
    weather_weight: float


@dataclass(frozen=True)
class ModelInput:
    crop: str
    market: str
    previous_price: float
    arrival_quantity: float
    weather_index: float


@dataclass(frozen=True)
class Prediction:
    fair_price: float
    intercept_term: float
    previous_price_term: float
    arrival_term: float
    weather_term: float
    log_arrivals: float


@dataclass(frozen=True)
class CalibrationSample:
    previous_price: float
    arrival_quantity: float
    weather_index: float
    observed_price: float


@dataclass(frozen=True)
class CalibrationReport:
    record_count: int
    mean_absolute_error: float
    root_mean_squared_error: float
    maximum_absolute_error: float
    r_squared: float


def predict_fair_price(values: ModelInput, coefficients: Coefficients) -> Prediction:
    """Evaluate P_t = a0 + a1*P_(t-1) - gamma*ln(A_t) + beta*W_t."""
    if values.previous_price <= 0:
        raise ValueError("Yesterday's mandi price must be greater than zero.")
    if values.arrival_quantity <= 0:
        raise ValueError("Today's arrivals must be greater than zero.")
    if not -10 <= values.weather_index <= 10:
        raise ValueError("Weather index must be between -10 and 10.")

    log_arrivals = math.log(values.arrival_quantity)
    intercept_term = coefficients.intercept
    previous_price_term = coefficients.autoregressive_weight * values.previous_price
    arrival_term = -coefficients.arrival_elasticity * log_arrivals
    weather_term = coefficients.weather_weight * values.weather_index
    fair_price = intercept_term + previous_price_term + arrival_term + weather_term

    return Prediction(
        fair_price=fair_price,
        intercept_term=intercept_term,
        previous_price_term=previous_price_term,
        arrival_term=arrival_term,
        weather_term=weather_term,
        log_arrivals=log_arrivals,
    )


def _solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Solve a small dense system using Gaussian elimination with pivoting."""
    size = len(vector)
    augmented = [matrix[row][:] + [vector[row]] for row in range(size)]
    for pivot_column in range(size):
        pivot_row = max(
            range(pivot_column, size),
            key=lambda row: abs(augmented[row][pivot_column]),
        )
        if abs(augmented[pivot_row][pivot_column]) < 1e-12:
            raise ValueError("Calibration inputs do not identify all four coefficients.")
        augmented[pivot_column], augmented[pivot_row] = (
            augmented[pivot_row],
            augmented[pivot_column],
        )
        pivot = augmented[pivot_column][pivot_column]
        augmented[pivot_column] = [value / pivot for value in augmented[pivot_column]]
        for row in range(size):
            if row == pivot_column:
                continue
            factor = augmented[row][pivot_column]
            augmented[row] = [
                augmented[row][column] - factor * augmented[pivot_column][column]
                for column in range(size + 1)
            ]
    return [augmented[row][-1] for row in range(size)]


def calibrate_coefficients(samples: Iterable[CalibrationSample]) -> Coefficients:
    """Recover Model-1 coefficients by ordinary least squares.

    The design row is [1, previous_price, -ln(arrivals), weather_index], so the
    solved parameter order is [alpha_0, alpha_1, gamma, beta].
    """
    rows = list(samples)
    if len(rows) < 4:
        raise ValueError("At least four calibration records are required.")
    design = [
        [1.0, row.previous_price, -math.log(row.arrival_quantity), row.weather_index]
        for row in rows
    ]
    normal_matrix = [
        [sum(row[i] * row[j] for row in design) for j in range(4)]
        for i in range(4)
    ]
    normal_vector = [
        sum(row[i] * sample.observed_price for row, sample in zip(design, rows))
        for i in range(4)
    ]
    intercept, autoregressive_weight, arrival_elasticity, weather_weight = (
        _solve_linear_system(normal_matrix, normal_vector)
    )
    return Coefficients(
        intercept=intercept,
        autoregressive_weight=autoregressive_weight,
        arrival_elasticity=arrival_elasticity,
        weather_weight=weather_weight,
    )


def evaluate_calibration(
    samples: Iterable[CalibrationSample], coefficients: Coefficients
) -> CalibrationReport:
    rows = list(samples)
    if not rows:
        raise ValueError("Calibration records are required.")
    predictions = [
        coefficients.intercept
        + coefficients.autoregressive_weight * row.previous_price
        - coefficients.arrival_elasticity * math.log(row.arrival_quantity)
        + coefficients.weather_weight * row.weather_index
        for row in rows
    ]
    residuals = [row.observed_price - prediction for row, prediction in zip(rows, predictions)]
    squared = [residual * residual for residual in residuals]
    mean_observed = sum(row.observed_price for row in rows) / len(rows)
    total_variation = sum((row.observed_price - mean_observed) ** 2 for row in rows)
    residual_variation = sum(squared)
    r_squared = 1.0 if total_variation == 0 else 1.0 - residual_variation / total_variation
    return CalibrationReport(
        record_count=len(rows),
        mean_absolute_error=sum(abs(value) for value in residuals) / len(rows),
        root_mean_squared_error=math.sqrt(sum(squared) / len(rows)),
        maximum_absolute_error=max(abs(value) for value in residuals),
        r_squared=r_squared,
    )
