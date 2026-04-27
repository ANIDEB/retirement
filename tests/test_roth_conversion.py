from retirement.engine.roth_conversion import do_roth_conversion
from tests.conftest import make_holding, make_scenario


def _defrd(ticker="VFIAX", qty=1000.0, price=100.0, cost_basis=0.0):
    return make_holding(account_type="TAX_DEFRD", ticker=ticker, qty=qty,
                        price=price, cost_basis=cost_basis)


def _roth(ticker="VFIAX", qty=10.0, price=100.0):
    return make_holding(account_name="ANI_ROTH", account_type="ROTH", ticker=ticker,
                        qty=qty, price=price, cost_basis=0.0)


def test_no_conversion_when_bracket_full(scenario):
    # Fill 22% bracket fully before conversion
    bracket_top = 206_700 + 30_000  # = 236_700
    updated, converted = do_roth_conversion([_defrd()], bracket_top + 1, scenario)
    assert converted == 0.0


def test_converts_to_fill_bracket(scenario):
    updated, converted = do_roth_conversion([_defrd(qty=10000, price=100)], 0.0, scenario)
    assert converted > 0
    assert converted <= 206_700 + 30_000  # within bracket top


def test_roth_holding_added(scenario):
    updated, _ = do_roth_conversion([_defrd(qty=10000, price=100)], 0.0, scenario)
    roth = [h for h in updated if h.account_type == "ROTH"]
    assert len(roth) > 0


def test_existing_roth_updated(scenario):
    holdings = [_defrd(qty=10000, price=100), _roth(qty=10, price=100)]
    updated, _ = do_roth_conversion(holdings, 0.0, scenario)
    roth = next(h for h in updated if h.account_type == "ROTH" and h.ticker == "VFIAX")
    assert roth.qty > 10


def test_tax_deferred_reduced(scenario):
    h = _defrd(qty=10000, price=100)
    updated, _ = do_roth_conversion([h], 0.0, scenario)
    defrd = next(x for x in updated if x.account_type == "TAX_DEFRD")
    assert defrd.qty < 10000


def test_no_tax_deferred_no_conversion(scenario):
    h = make_holding(account_type="BROKERAGE", ticker="AAPL", qty=100, price=100)
    updated, converted = do_roth_conversion([h], 0.0, scenario)
    assert converted == 0.0
