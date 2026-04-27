from __future__ import annotations
from dataclasses import replace
from datetime import date
from retirement.models.holding import Holding
from retirement.models.scenario import Scenario


def year_growth_fraction(run_date: date, year: int) -> float:
    """Fraction of the annual growth rate to apply for a partial first year."""
    if year > run_date.year:
        return 1.0
    year_end = date(year, 12, 31)
    total_days = 366 if year % 4 == 0 else 365
    remaining_days = (year_end - run_date).days
    return remaining_days / total_days


def get_growth_rate(holding: Holding, year: int, scenario: Scenario) -> float:
    custom_growth = scenario.custom_rates_by_year.get(year, {}).get("growth_rates", {})
    if holding.ticker in custom_growth:
        return custom_growth[holding.ticker]
    return scenario.tickers.default_growth_rates.get(holding.ticker, 0.0)


def apply_growth(
    holdings: list[Holding],
    year: int,
    scenario: Scenario,
    fraction: float = 1.0,
) -> list[Holding]:
    """
    Apply year-end price growth, prorated by fraction.
    Also clears is_new_dividend_cash so last year's dividend cash
    becomes a regular HOLDING this year.
    """
    result = []
    for h in holdings:
        rate = get_growth_rate(h, year, scenario)
        result.append(replace(h, price=h.price * (1 + rate * fraction), is_new_dividend_cash=False))
    return result
