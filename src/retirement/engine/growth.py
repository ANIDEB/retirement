from __future__ import annotations
from dataclasses import replace
from retirement.models.holding import Holding
from retirement.models.scenario import Scenario


def get_growth_rate(holding: Holding, year: int, scenario: Scenario) -> float:
    custom_growth = scenario.custom_rates_by_year.get(year, {}).get("growth_rates", {})
    if holding.ticker in custom_growth:
        return custom_growth[holding.ticker]
    return scenario.tickers.default_growth_rates.get(holding.ticker, 0.0)


def apply_growth(holdings: list[Holding], year: int, scenario: Scenario) -> list[Holding]:
    result = []
    for h in holdings:
        rate = get_growth_rate(h, year, scenario)
        result.append(replace(h, price=h.price * (1 + rate)))
    return result
