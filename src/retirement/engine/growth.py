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


def _merge_cash_holdings(holdings: list[Holding]) -> list[Holding]:
    """
    Merge multiple CASH/HYCASH holdings for the same account into one.
    Called at the start of each year so accumulated prior-year dividend cash
    consolidates into a single balance before growth is applied.
    """
    non_cash: list[Holding] = []
    cash_map: dict[tuple[str, str], Holding] = {}
    for h in holdings:
        if h.ticker in ("CASH", "HYCASH"):
            key = (h.account_name, h.ticker)
            if key in cash_map:
                existing = cash_map[key]
                cash_map[key] = replace(
                    existing,
                    qty=existing.qty + h.qty,
                    cost_basis_total=existing.cost_basis_total + h.cost_basis_total,
                )
            else:
                cash_map[key] = h
        else:
            non_cash.append(h)
    return non_cash + list(cash_map.values())


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
    Merge accumulated cash holdings from the prior year, then apply year-end price growth
    (prorated by fraction). Clears is_new_dividend_cash so prior-year dividend cash
    becomes a regular HOLDING this year.
    """
    merged = _merge_cash_holdings(holdings)
    result = []
    for h in merged:
        rate = get_growth_rate(h, year, scenario)
        result.append(replace(h, price=h.price * (1 + rate * fraction), is_new_dividend_cash=False))
    return result
