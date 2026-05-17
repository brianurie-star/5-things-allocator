"""Retirement portfolio Monte Carlo simulation for probability study reports."""

import random
from typing import Any


def _f(value, default=0.0):
    try:
        if value in ("", None):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def run_retirement_monte_carlo(
    data,
    simulations=1500,
    max_years=35,
) -> dict[str, Any]:
    investable = _f(data.get("investable_assets"))
    his_age = _f(data.get("his_age"), 65)
    her_age = _f(data.get("her_age"), 65)
    his_le = _f(data.get("his_life_expectancy"), 90)
    her_le = _f(data.get("her_life_expectancy"), 90)
    planning_age = max(his_age, her_age)
    years = int(min(max(max(his_le, her_le) - planning_age, 10), max_years))

    guaranteed_rate = _f(data.get("guaranteed_withdrawal_rate"), 0.06)
    unprotected_rate = _f(data.get("unprotected_withdrawal_rate"), 0.04)
    guaranteed_alloc = _f(data.get("guaranteed_income_allocation"), 0.15)
    inflation = _f(data.get("inflation"), 0.03)

    prefix = data.get("risk_profile") or "growth"
    mean_return = _f(data.get(f"{prefix}_mean"), 9.89) / 100.0
    stdev = _f(data.get(f"{prefix}_stdev"), 12.37) / 100.0

    annual_withdrawal = investable * (
        guaranteed_alloc * guaranteed_rate
        + (1 - guaranteed_alloc) * unprotected_rate
    )

    if annual_withdrawal <= 0 and investable > 0:
        annual_withdrawal = investable * 0.04

    endings = []
    successes = 0
    depletion_years = []

    for _ in range(simulations):
        balance = investable
        withdrawal = annual_withdrawal
        depleted_at = None
        for year in range(1, years + 1):
            if balance <= 0:
                depleted_at = depleted_at or year
                balance = 0
                break
            balance -= withdrawal
            if balance <= 0:
                depleted_at = year
                balance = 0
                break
            annual_return = random.gauss(mean_return, stdev)
            balance *= 1 + annual_return
            withdrawal *= 1 + inflation

        endings.append(max(balance, 0))
        if balance > 0:
            successes += 1
        if depleted_at is not None:
            depletion_years.append(depleted_at)

    endings.sort()
    n = len(endings)

    def percentile(p):
        if n == 0:
            return 0.0
        idx = min(max(int(round((p / 100.0) * (n - 1))), 0), n - 1)
        return endings[idx]

    return {
        "simulations": simulations,
        "planning_years": years,
        "initial_assets": round(investable, 2),
        "annual_withdrawal_start": round(annual_withdrawal, 2),
        "mean_return_pct": round(mean_return * 100, 2),
        "stdev_pct": round(stdev * 100, 2),
        "success_rate_pct": round(100.0 * successes / simulations, 1) if simulations else 0,
        "median_ending": round(percentile(50), 0),
        "p10_ending": round(percentile(10), 0),
        "p90_ending": round(percentile(90), 0),
        "median_depletion_year": (
            round(sorted(depletion_years)[len(depletion_years) // 2], 0)
            if depletion_years
            else None
        ),
    }
