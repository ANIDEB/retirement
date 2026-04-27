from retirement.engine.withdrawal import withdraw_funds, withdraw_from_hsa
from tests.conftest import make_holding


def _cash(account_type="BROKERAGE", qty=10_000.0):
    return make_holding(account_type=account_type, ticker="CASH", qty=qty, price=1.0, cost_basis=qty)


def _equity(account_type="BROKERAGE", ticker="AAPL", qty=100.0, price=200.0, cost_basis=5000.0):
    return make_holding(account_type=account_type, ticker=ticker, qty=qty, price=price, cost_basis=cost_basis)


def test_no_withdrawal_needed():
    holdings = [_cash()]
    updated, withdrawn, txs = withdraw_funds(holdings, 0.0, 2029)
    assert withdrawn == 0.0
    assert txs == []


def test_withdraw_brokerage_cash_first():
    holdings = [_cash("BROKERAGE", 50_000), _cash("SAVINGS", 50_000)]
    updated, withdrawn, txs = withdraw_funds(holdings, 10_000, 2029)
    brok = next(h for h in updated if h.account_type == "BROKERAGE" and h.ticker == "CASH")
    assert brok.qty == 40_000


def test_withdraw_equities_after_cash():
    holdings = [_cash("BROKERAGE", 1_000), _equity("BROKERAGE")]
    updated, withdrawn, txs = withdraw_funds(holdings, 5_000, 2029)
    assert withdrawn >= 5_000


def test_withdraw_tax_deferred_after_brokerage():
    holdings = [_equity("TAX_DEFRD", qty=100, price=100, cost_basis=0)]
    updated, withdrawn, txs = withdraw_funds(holdings, 5_000, 2029)
    assert withdrawn > 0


def test_withdraw_roth_last():
    holdings = [
        _equity("BROKERAGE", qty=1, price=100, cost_basis=50),
        _equity("ROTH", qty=100, price=100, cost_basis=0),
    ]
    updated, _, txs = withdraw_funds(holdings, 50, 2029)
    roth = next(h for h in updated if h.account_type == "ROTH")
    assert roth.qty == 100


def test_withdraw_from_hsa_cash_first():
    hsa_cash = make_holding(account_name="HSA", account_type="HSA", ticker="CASH",
                            qty=10_000, price=1.0, cost_basis=10_000)
    updated, withdrawn, txs = withdraw_from_hsa([hsa_cash], 3_000, 2029)
    assert abs(withdrawn - 3_000) < 0.01
    cash = next(h for h in updated if h.account_type == "HSA" and h.ticker == "CASH")
    assert abs(cash.qty - 7_000) < 0.01


def test_withdraw_from_hsa_equity_when_cash_insufficient():
    hsa_cash = make_holding(account_type="HSA", ticker="CASH", qty=500, price=1.0, cost_basis=500)
    hsa_eq = make_holding(account_type="HSA", ticker="VIIIX", qty=10, price=500, cost_basis=0)
    updated, withdrawn, txs = withdraw_from_hsa([hsa_cash, hsa_eq], 2_000, 2029)
    assert withdrawn >= 2_000


def test_withdraw_funds_negative_amount():
    holdings = [_cash()]
    updated, withdrawn, txs = withdraw_funds(holdings, -100, 2029)
    assert withdrawn == 0.0


def test_withdraw_from_hsa_break_on_second_cash():
    hsa1 = make_holding(account_type="HSA", ticker="CASH", qty=5_000, price=1.0, cost_basis=5_000)
    hsa2 = make_holding(account_type="HSA", ticker="CASH", qty=5_000, price=1.0, cost_basis=5_000)
    updated, withdrawn, txs = withdraw_from_hsa([hsa1, hsa2], 3_000, 2029)
    assert abs(withdrawn - 3_000) < 0.01
    remaining = sum(h.qty for h in updated if h.account_type == "HSA" and h.ticker == "CASH")
    assert abs(remaining - 7_000) < 0.01


def test_transactions_recorded_on_withdrawal():
    holdings = [_cash("BROKERAGE", 10_000)]
    _, _, txs = withdraw_funds(holdings, 5_000, 2029)
    assert len(txs) == 1
    assert txs[0].transaction_type == "WITHDRAWAL"
    assert txs[0].year == 2029


def test_hsa_transactions_recorded():
    hsa = make_holding(account_type="HSA", ticker="CASH", qty=10_000, price=1.0, cost_basis=10_000)
    _, _, txs = withdraw_from_hsa([hsa], 3_000, 2029)
    assert len(txs) == 1
    assert txs[0].transaction_type == "HSA_WITHDRAWAL"
