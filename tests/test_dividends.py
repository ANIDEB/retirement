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
    # April 1 is before April div, so April counts
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
    from retirement.models.scenario import Scenario
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
    updated, records, taxable = calculate_dividends([h], 2026, scenario)
    reinvested = next(x for x in updated if x.ticker == "VFIAX")
    assert reinvested.qty > 100.0
    assert len(records) == 1
    assert records[0].reinvested is True
    assert taxable > 0  # BROKERAGE is taxable


def test_dividends_non_reinvest_creates_cash(scenario):
    h = make_holding(account_name="OTHER_ACC", ticker="VFIAX", qty=100.0, price=100.0)
    updated, records, taxable = calculate_dividends([h], 2026, scenario)
    cash_records = [x for x in updated if x.ticker == "CASH"]
    assert len(cash_records) == 1
    assert cash_records[0].qty > 0


def test_dividends_cash_ticker_reinvested(scenario):
    h = make_holding(account_name="ANI_AMEX", ticker="HYCASH", account_type="HY_SAVINGS",
                     qty=10000.0, price=1.0)
    updated, records, taxable = calculate_dividends([h], 2026, scenario)
    hycash = next(x for x in updated if x.ticker == "HYCASH")
    assert hycash.qty > 10000.0


def test_dividends_zero_rate_no_record(scenario):
    h = make_holding(ticker="CASH", account_type="ROTH", qty=100.0, price=1.0)
    updated, records, taxable = calculate_dividends([h], 2026, scenario)
    assert len(records) == 0
    assert taxable == 0.0


def test_full_year_has_more_dividends_than_partial(scenario):
    h = make_holding(ticker="VFIAX", qty=100.0, price=100.0)
    _, _, tax_partial = calculate_dividends([h], 2026, scenario)  # 2 quarters
    _, _, tax_full = calculate_dividends([h], 2027, scenario)     # 4 quarters
    assert tax_full > tax_partial
