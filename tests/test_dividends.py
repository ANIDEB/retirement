from datetime import date
from retirement.engine.dividends import quarters_remaining, get_dividend_rate, calculate_dividends
from tests.conftest import make_holding, make_scenario


def test_quarters_remaining_future_year():
    assert quarters_remaining(date(2026, 4, 26), 2027) == 4


def test_quarters_remaining_before_july():
    assert quarters_remaining(date(2026, 4, 26), 2026) == 2  # Jul, Oct remaining


def test_quarters_remaining_after_october():
    assert quarters_remaining(date(2026, 11, 1), 2026) == 0


def test_quarters_remaining_exactly_on_dividend_month():
    assert quarters_remaining(date(2026, 3, 31), 2026) == 3  # Apr, Jul, Oct


def test_get_dividend_rate_hycash(scenario):
    h = make_holding(ticker="HYCASH", account_type="HY_SAVINGS")
    assert get_dividend_rate(h, 2026, scenario) == 0.035


def test_get_dividend_rate_cash_savings(scenario):
    h = make_holding(ticker="CASH", account_type="SAVINGS")
    assert get_dividend_rate(h, 2026, scenario) == 0.045


def test_get_dividend_rate_cash_unknown_type(scenario):
    h = make_holding(ticker="CASH", account_type="ROTH")
    assert get_dividend_rate(h, 2026, scenario) == 0.0


def test_get_dividend_rate_custom_override(scenario):
    s = make_scenario(custom_rates_by_year={2026: {"dividend_rates": {"VFIAX": 0.02}}})
    h = make_holding(ticker="VFIAX")
    assert get_dividend_rate(h, 2026, s) == 0.02


def test_get_dividend_rate_default(scenario):
    h = make_holding(ticker="VFIAX")
    assert get_dividend_rate(h, 2026, scenario) == 0.014


def test_get_dividend_rate_missing_ticker(scenario):
    h = make_holding(ticker="UNKNOWN")
    assert get_dividend_rate(h, 2026, scenario) == 0.0


def test_dividends_reinvest_adds_shares(scenario):
    h = make_holding(account_name="ANI_VAN", ticker="VFIAX", qty=100.0, price=100.0)
    updated, records, txs, taxable = calculate_dividends([h], 2026, scenario)
    reinvested = next(x for x in updated if x.ticker == "VFIAX")
    assert reinvested.qty > 100.0
    assert len(records) == 1
    assert records[0].reinvested is True
    assert taxable > 0  # BROKERAGE is taxable


def test_dividends_reinvest_creates_transaction(scenario):
    h = make_holding(account_name="ANI_VAN", ticker="VFIAX", qty=100.0, price=100.0)
    _, _, txs, _ = calculate_dividends([h], 2026, scenario)
    assert len(txs) == 1
    assert txs[0].transaction_type == "DIV_REINVESTED"
    assert txs[0].year == 2026


def test_dividends_non_reinvest_no_transaction(scenario):
    h = make_holding(account_name="OTHER_ACC", ticker="VFIAX", qty=100.0, price=100.0)
    _, _, txs, _ = calculate_dividends([h], 2026, scenario)
    assert txs == []


def test_dividends_amount_uses_pre_growth_price(scenario):
    """Dividend amount should use the pre-growth (beginning-of-year) price, not post-growth."""
    pre = make_holding(ticker="VFIAX", qty=100.0, price=100.0)
    post = make_holding(ticker="VFIAX", qty=100.0, price=110.0)  # after 10% growth
    _, records, _, taxable = calculate_dividends([post], 2027, scenario, base_holdings=[pre])
    assert abs(records[0].amount - 140.0) < 0.01
    assert abs(taxable - 140.0) < 0.01


def test_dividends_reinvest_uses_post_growth_price(scenario):
    """Reinvested shares should be bought at the post-growth year-end price."""
    pre = make_holding(account_name="ANI_VAN", ticker="VFIAX", qty=100.0, price=100.0)
    post = make_holding(account_name="ANI_VAN", ticker="VFIAX", qty=100.0, price=110.0)
    div_amount = 100.0 * 100.0 * 0.014 * 1.0  # 140 using pre-growth
    updated, _, _, _ = calculate_dividends([post], 2027, scenario, base_holdings=[pre])
    vfiax = next(x for x in updated if x.ticker == "VFIAX")
    expected_new_shares = div_amount / 110.0  # bought at post-growth price
    assert abs(vfiax.qty - (100.0 + expected_new_shares)) < 0.001


def test_dividends_non_reinvest_no_extra_holding(scenario):
    """Equity dividend in non-reinvest account should NOT create duplicate HOLDING."""
    h = make_holding(account_name="OTHER_ACC", ticker="VFIAX", qty=100.0, price=100.0)
    updated, records, _, taxable = calculate_dividends([h], 2026, scenario)
    # The new CASH holding should be flagged — not a second HOLDING
    cash_holdings = [x for x in updated if x.ticker == "CASH"]
    assert len(cash_holdings) == 1
    assert cash_holdings[0].is_new_dividend_cash is True


def test_dividends_non_reinvest_creates_new_cash_alongside_existing(scenario):
    """Equity dividend creates a separate is_new_dividend_cash=True holding; existing CASH not merged."""
    # Use TAX_DEFRD (rate=0) so existing CASH earns no interest — isolates the equity dividend effect.
    equity = make_holding(account_name="OTHER_ACC", account_type="TAX_DEFRD", ticker="VFIAX", qty=100.0, price=100.0)
    existing_cash = make_holding(account_name="OTHER_ACC", account_type="TAX_DEFRD", ticker="CASH", qty=500.0, price=1.0, cost_basis=500.0)
    updated, records, _, taxable = calculate_dividends([equity, existing_cash], 2026, scenario)
    cash_holdings = [x for x in updated if x.ticker == "CASH"]
    assert len(cash_holdings) == 2  # existing + new dividend cash (not merged)
    old_cash = next(c for c in cash_holdings if not c.is_new_dividend_cash)
    new_cash = next(c for c in cash_holdings if c.is_new_dividend_cash)
    assert old_cash.qty == 500.0  # existing not touched by equity dividend
    assert new_cash.qty > 0       # new dividend amount kept separate


def test_dividends_cash_ticker_interest_stays_in_holding(scenario):
    """CASH interest always increases the same holding, regardless of reinvest list."""
    h = make_holding(account_name="ANI_BOA", account_type="SAVINGS", ticker="CASH",
                     qty=10_000.0, price=1.0)
    s = make_scenario(custom_rates_by_year={})
    # set a non-zero savings rate to see it accumulate
    s.tickers.cash_interest_rates_by_account_type["SAVINGS"] = 0.04
    updated, records, _, _ = calculate_dividends([h], 2027, s)
    cash = next(x for x in updated if x.ticker == "CASH")
    assert cash.qty > 10_000.0
    # No duplicate: should be exactly one CASH record for this account
    assert sum(1 for x in updated if x.account_name == "ANI_BOA" and x.ticker == "CASH") == 1


def test_dividends_hycash_interest_reinvested_in_same_holding(scenario):
    h = make_holding(account_name="ANI_AMEX", ticker="HYCASH", account_type="HY_SAVINGS",
                     qty=10_000.0, price=1.0)
    updated, records, _, taxable = calculate_dividends([h], 2026, scenario)
    hycash = next(x for x in updated if x.ticker == "HYCASH")
    assert hycash.qty > 10_000.0


def test_dividends_zero_rate_no_record(scenario):
    h = make_holding(ticker="CASH", account_type="ROTH", qty=100.0, price=1.0)
    updated, records, _, taxable = calculate_dividends([h], 2026, scenario)
    assert len(records) == 0
    assert taxable == 0.0


def test_full_year_has_more_dividends_than_partial(scenario):
    h = make_holding(ticker="VFIAX", qty=100.0, price=100.0)
    _, _, _, tax_partial = calculate_dividends([h], 2026, scenario)  # 2 quarters
    _, _, _, tax_full = calculate_dividends([h], 2027, scenario)     # 4 quarters
    assert tax_full > tax_partial
