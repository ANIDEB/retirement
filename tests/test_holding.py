from dataclasses import replace
from retirement.models.holding import Holding, TAXABLE_ACCOUNT_TYPES


def _make(account_type="BROKERAGE", ticker="AAPL", qty=10.0, price=100.0, cost_basis=500.0):
    return Holding("ACC", "ANI", "ETrade", account_type, ticker, qty, price, cost_basis)


def test_amount():
    assert _make(qty=10, price=50).amount == 500.0


def test_cost_basis_per_share():
    h = _make(qty=10, price=100, cost_basis=400)
    assert h.cost_basis_per_share == 40.0


def test_cost_basis_per_share_zero_qty():
    h = _make(qty=0, cost_basis=0)
    assert h.cost_basis_per_share == 0.0


def test_unrealized_gain():
    h = _make(qty=10, price=100, cost_basis=400)
    assert h.unrealized_gain == 600.0


def test_return_pct():
    h = _make(qty=10, price=100, cost_basis=500)
    assert h.return_pct == 1.0


def test_return_pct_zero_cost_basis():
    h = _make(qty=10, price=100, cost_basis=0)
    assert h.return_pct == float("inf")


def test_dividends_taxable_brokerage():
    assert _make(account_type="BROKERAGE").dividends_taxable is True


def test_dividends_taxable_savings():
    assert _make(account_type="SAVINGS").dividends_taxable is True


def test_dividends_taxable_hy_savings():
    assert _make(account_type="HY_SAVINGS").dividends_taxable is True


def test_dividends_not_taxable_roth():
    assert _make(account_type="ROTH").dividends_taxable is False


def test_dividends_not_taxable_tax_defrd():
    assert _make(account_type="TAX_DEFRD").dividends_taxable is False


def test_dividends_not_taxable_hsa():
    assert _make(account_type="HSA").dividends_taxable is False


def test_is_new_dividend_cash_default_false():
    assert _make().is_new_dividend_cash is False


def test_is_new_dividend_cash_can_be_set():
    h = replace(_make(), is_new_dividend_cash=True)
    assert h.is_new_dividend_cash is True


def test_is_new_dividend_cash_excluded_from_equality():
    h1 = _make()
    h2 = replace(_make(), is_new_dividend_cash=True)
    assert h1 == h2  # compare=False so flag doesn't affect equality
