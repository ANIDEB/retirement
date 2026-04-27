from retirement.engine.lt_harvesting import harvest_lt_gains
from tests.conftest import make_holding, make_scenario


def _brokerage(ticker="AAPL", qty=100.0, price=200.0, cost_basis=5000.0):
    return make_holding(account_type="BROKERAGE", ticker=ticker, qty=qty,
                        price=price, cost_basis=cost_basis)


def test_no_harvest_when_no_gains(scenario):
    h = _brokerage(price=50.0, cost_basis=10000.0)  # underwater
    updated, harvested = harvest_lt_gains([h], 0.0, scenario)
    assert harvested == 0.0


def test_harvest_within_room(scenario):
    h = _brokerage(qty=100, price=200, cost_basis=5000)  # gain = 15000
    updated, harvested = harvest_lt_gains([h], 0.0, scenario)
    assert harvested > 0
    assert harvested <= 96_700  # stays within 0%/15% boundary


def test_harvest_respects_niit_threshold(scenario):
    # Ordinary income already at 240k — only 10k room before NIIT
    h = _brokerage(qty=1000, price=200, cost_basis=1000)  # huge gain
    updated, harvested = harvest_lt_gains([h], 240_000.0, scenario)
    assert harvested <= 10_001  # NIIT kicks in at 250k


def test_harvest_no_room_when_income_high(scenario):
    h = _brokerage(qty=100, price=200, cost_basis=5000)
    updated, harvested = harvest_lt_gains([h], 300_000.0, scenario)
    assert harvested == 0.0


def test_harvest_cash_added_to_holdings(scenario):
    h = _brokerage(qty=100, price=200, cost_basis=5000)
    updated, _ = harvest_lt_gains([h], 0.0, scenario)
    cash_records = [x for x in updated if x.ticker == "CASH"]
    assert len(cash_records) > 0


def test_non_brokerage_not_harvested(scenario):
    h = make_holding(account_type="TAX_DEFRD", ticker="VFIAX", qty=100, price=200, cost_basis=5000)
    updated, harvested = harvest_lt_gains([h], 0.0, scenario)
    assert harvested == 0.0


def test_cash_ticker_skipped(scenario):
    h = _brokerage(ticker="CASH", qty=1000, price=1.0, cost_basis=0.0)
    updated, harvested = harvest_lt_gains([h], 0.0, scenario)
    assert harvested == 0.0


def test_lowest_return_sold_first(scenario):
    # Set ordinary income near NIIT threshold so only $1,000 room remains.
    # BAC has enough gain to fill it; AAPL should be untouched.
    low = _brokerage(ticker="BAC", qty=100, price=110, cost_basis=1000)   # 10% gain ($10k)
    high = _brokerage(ticker="AAPL", qty=100, price=300, cost_basis=1000)  # 200% gain ($29k)
    updated, harvested = harvest_lt_gains([low, high], 249_000.0, scenario)
    bac = next(x for x in updated if x.ticker == "BAC" and x.account_type == "BROKERAGE")
    aapl = next(x for x in updated if x.ticker == "AAPL" and x.account_type == "BROKERAGE")
    assert bac.qty < 100   # partially sold first
    assert aapl.qty == 100  # untouched — room exhausted by BAC
