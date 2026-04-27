from dataclasses import replace as dc_replace
from datetime import date
from retirement.engine.growth import apply_growth, get_growth_rate, year_growth_fraction, _merge_cash_holdings
from tests.conftest import make_scenario, make_holding


def test_get_growth_rate_default(scenario):
    h = make_holding(ticker="VFIAX")
    assert get_growth_rate(h, 2026, scenario) == 0.07


def test_get_growth_rate_custom_override(scenario):
    h = make_holding(ticker="VFIAX")
    assert get_growth_rate(h, 2029, scenario) == 0.05


def test_get_growth_rate_missing_ticker(scenario):
    h = make_holding(ticker="UNKNOWN")
    assert get_growth_rate(h, 2026, scenario) == 0.0


def test_apply_growth_full_year(scenario):
    result = apply_growth([make_holding(ticker="VFIAX", price=100.0)], 2026, scenario, fraction=1.0)
    assert abs(result[0].price - 107.0) < 0.001


def test_apply_growth_partial_year(scenario):
    result = apply_growth([make_holding(ticker="VFIAX", price=100.0)], 2026, scenario, fraction=0.5)
    assert abs(result[0].price - 103.5) < 0.001


def test_apply_growth_qty_unchanged(scenario):
    result = apply_growth([make_holding(ticker="VFIAX", qty=50.0, price=100.0)], 2026, scenario, fraction=1.0)
    assert result[0].qty == 50.0


def test_apply_growth_cost_basis_unchanged(scenario):
    result = apply_growth([make_holding(ticker="VFIAX", price=100.0, cost_basis=4000.0)], 2026, scenario, fraction=1.0)
    assert result[0].cost_basis_total == 4000.0


def test_apply_growth_clears_dividend_cash_flag(scenario):
    h = dc_replace(make_holding(ticker="CASH"), is_new_dividend_cash=True)
    result = apply_growth([h], 2027, scenario, fraction=1.0)
    assert result[0].is_new_dividend_cash is False


def test_apply_growth_merges_cash_before_growth(scenario):
    cash1 = dc_replace(make_holding(account_name="ACC", ticker="CASH", qty=500, price=1.0, cost_basis=500), is_new_dividend_cash=True)
    cash2 = make_holding(account_name="ACC", ticker="CASH", qty=300, price=1.0, cost_basis=300)
    result = apply_growth([cash1, cash2], 2027, scenario, fraction=1.0)
    cash = [h for h in result if h.ticker == "CASH"]
    assert len(cash) == 1
    assert cash[0].qty == 800.0
    assert cash[0].is_new_dividend_cash is False


def test_apply_growth_multiple(scenario):
    holdings = [make_holding(ticker="VFIAX", price=100.0), make_holding(ticker="CASH", price=1.0)]
    result = apply_growth(holdings, 2026, scenario, fraction=1.0)
    assert len(result) == 2
    assert abs(result[0].price - 107.0) < 0.001
    assert result[1].price == 1.0


def test_year_growth_fraction_future_year():
    assert year_growth_fraction(date(2026, 4, 26), 2027) == 1.0


def test_year_growth_fraction_partial_year():
    fraction = year_growth_fraction(date(2026, 4, 26), 2026)
    assert abs(fraction - 249 / 365) < 0.001


def test_year_growth_fraction_leap_year():
    run = date(2028, 4, 26)
    remaining = (date(2028, 12, 31) - date(2028, 4, 26)).days
    assert abs(year_growth_fraction(run, 2028) - remaining / 366) < 0.001


def test_merge_cash_combines_same_account():
    cash1 = make_holding(account_name="ACC", ticker="CASH", qty=500, price=1.0, cost_basis=500)
    cash2 = make_holding(account_name="ACC", ticker="CASH", qty=300, price=1.0, cost_basis=300)
    result = _merge_cash_holdings([cash1, cash2])
    cash = [h for h in result if h.ticker == "CASH"]
    assert len(cash) == 1
    assert cash[0].qty == 800.0
    assert cash[0].cost_basis_total == 800.0


def test_merge_cash_different_accounts_not_merged():
    cash1 = make_holding(account_name="ACC1", ticker="CASH", qty=500, price=1.0, cost_basis=500)
    cash2 = make_holding(account_name="ACC2", ticker="CASH", qty=300, price=1.0, cost_basis=300)
    result = _merge_cash_holdings([cash1, cash2])
    assert len([h for h in result if h.ticker == "CASH"]) == 2


def test_merge_cash_and_hycash_not_merged():
    cash = make_holding(account_name="ACC", ticker="CASH", qty=500, price=1.0, cost_basis=500)
    hycash = make_holding(account_name="ACC", ticker="HYCASH", qty=300, price=1.0, cost_basis=300)
    result = _merge_cash_holdings([cash, hycash])
    assert len(result) == 2


def test_merge_cash_preserves_order():
    """CASH must stay in its original position — not moved to the end."""
    equity1 = make_holding(account_name="ACC", ticker="VFIAX", qty=100, price=200)
    cash = make_holding(account_name="ACC", ticker="CASH", qty=500, price=1.0, cost_basis=500)
    equity2 = make_holding(account_name="ACC", ticker="QQQ", qty=50, price=300)
    result = _merge_cash_holdings([equity1, cash, equity2])
    assert result[0].ticker == "VFIAX"
    assert result[1].ticker == "CASH"   # stays in position, not moved to end
    assert result[2].ticker == "QQQ"
