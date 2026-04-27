from retirement.models.holding import Holding
from retirement.engine.growth import apply_growth, get_growth_rate
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


def test_apply_growth_price(scenario):
    holdings = [make_holding(ticker="VFIAX", price=100.0)]
    result = apply_growth(holdings, 2026, scenario)
    assert abs(result[0].price - 107.0) < 0.001


def test_apply_growth_qty_unchanged(scenario):
    holdings = [make_holding(ticker="VFIAX", qty=50.0, price=100.0)]
    result = apply_growth(holdings, 2026, scenario)
    assert result[0].qty == 50.0


def test_apply_growth_cost_basis_unchanged(scenario):
    holdings = [make_holding(ticker="VFIAX", price=100.0, cost_basis=4000.0)]
    result = apply_growth(holdings, 2026, scenario)
    assert result[0].cost_basis_total == 4000.0


def test_apply_growth_multiple(scenario):
    holdings = [make_holding(ticker="VFIAX", price=100.0), make_holding(ticker="CASH", price=1.0)]
    result = apply_growth(holdings, 2026, scenario)
    assert len(result) == 2
    assert abs(result[0].price - 107.0) < 0.001
    assert result[1].price == 1.0
