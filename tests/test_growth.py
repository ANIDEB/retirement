from datetime import date
from retirement.models.holding import Holding
from retirement.engine.growth import apply_growth, get_growth_rate, year_growth_fraction
from tests.conftest import make_scenario, make_holding


def test_get_growth_rate_default(scenario):
    h = make_holding(ticker="VFIAX")
    assert get_growth_rate(h, 2026, scenario) == 0.07


def test_get_growth_rate_custom_override(scenario):
    h = make_holding(ticker="VFIAX")
    rate = get_growth_rate(h, 2029, scenario)
    assert rate == 0.05


def test_get_growth_rate_missing_ticker(scenario):
    h = make_holding(ticker="UNKNOWN")
    assert get_growth_rate(h, 2026, scenario) == 0.0


def test_apply_growth_full_year(scenario):
    holdings = [make_holding(ticker="VFIAX", price=100.0)]
    result = apply_growth(holdings, 2026, scenario, fraction=1.0)
    assert abs(result[0].price - 107.0) < 0.001


def test_apply_growth_partial_year(scenario):
    holdings = [make_holding(ticker="VFIAX", price=100.0)]
    result = apply_growth(holdings, 2026, scenario, fraction=0.5)
    assert abs(result[0].price - 103.5) < 0.001


def test_apply_growth_qty_unchanged(scenario):
    holdings = [make_holding(ticker="VFIAX", qty=50.0, price=100.0)]
    result = apply_growth(holdings, 2026, scenario, fraction=1.0)
    assert result[0].qty == 50.0


def test_apply_growth_cost_basis_unchanged(scenario):
    holdings = [make_holding(ticker="VFIAX", price=100.0, cost_basis=4000.0)]
    result = apply_growth(holdings, 2026, scenario, fraction=1.0)
    assert result[0].cost_basis_total == 4000.0


def test_apply_growth_clears_dividend_cash_flag(scenario):
    from dataclasses import replace
    h = replace(make_holding(ticker="CASH"), is_new_dividend_cash=True)
    result = apply_growth([h], 2027, scenario, fraction=1.0)
    assert result[0].is_new_dividend_cash is False


def test_apply_growth_multiple(scenario):
    holdings = [make_holding(ticker="VFIAX", price=100.0), make_holding(ticker="CASH", price=1.0)]
    result = apply_growth(holdings, 2026, scenario, fraction=1.0)
    assert len(result) == 2
    assert abs(result[0].price - 107.0) < 0.001
    assert result[1].price == 1.0


def test_year_growth_fraction_future_year():
    run = date(2026, 4, 26)
    assert year_growth_fraction(run, 2027) == 1.0


def test_year_growth_fraction_partial_year():
    run = date(2026, 4, 26)
    fraction = year_growth_fraction(run, 2026)
    # (Dec 31 - Apr 26) = 249 days / 365
    assert abs(fraction - 249 / 365) < 0.001


def test_year_growth_fraction_leap_year():
    run = date(2028, 4, 26)
    fraction = year_growth_fraction(run, 2028)
    # 2028 is a leap year (366 days)
    remaining = (date(2028, 12, 31) - date(2028, 4, 26)).days
    assert abs(fraction - remaining / 366) < 0.001
