from __future__ import annotations
from dataclasses import replace
from datetime import date
from retirement.models.holding import Holding
from retirement.models.scenario import Scenario
from retirement.models.snapshot import DividendRecord

DIVIDEND_MONTHS: tuple[int, ...] = (1, 4, 7, 10)


def quarters_remaining(run_date: date, year: int) -> int:
    if year > run_date.year:
        return 4
    return sum(1 for m in DIVIDEND_MONTHS if date(year, m, 1) > run_date)


def get_dividend_rate(holding: Holding, year: int, scenario: Scenario) -> float:
    if holding.ticker == "HYCASH":
        return scenario.tickers.hycash_interest_rate
    if holding.ticker == "CASH":
        return scenario.tickers.cash_interest_rates_by_account_type.get(holding.account_type, 0.0)
    custom_div = scenario.custom_rates_by_year.get(year, {}).get("dividend_rates", {})
    if holding.ticker in custom_div:
        return custom_div[holding.ticker]
    return scenario.tickers.default_dividend_rates.get(holding.ticker, 0.0)


def calculate_dividends(
    holdings: list[Holding],
    year: int,
    scenario: Scenario,
) -> tuple[list[Holding], list[DividendRecord], float]:
    """
    Apply dividends/interest for the year.

    Returns:
        updated_holdings: original holdings with reinvested amounts merged in
        dividend_records: separate output records for each dividend/interest payment
        taxable_dividend_income: total from SAVINGS, BROKERAGE, HY_SAVINGS accounts
    """
    run_date = date.fromisoformat(scenario.run_date)
    fraction = quarters_remaining(run_date, year) / 4.0
    reinvest_set = set(scenario.tickers.reinvest_dividends_accounts)

    updated: list[Holding] = []
    dividend_records: list[DividendRecord] = []
    taxable_income = 0.0

    for h in holdings:
        rate = get_dividend_rate(h, year, scenario)
        div_amount = h.amount * rate * fraction

        is_cash_ticker = h.ticker in ("CASH", "HYCASH")
        reinvest = h.account_name in reinvest_set

        if div_amount > 0:
            dividend_records.append(
                DividendRecord(
                    account_name=h.account_name,
                    owner=h.owner,
                    counterparty=h.counterparty,
                    account_type=h.account_type,
                    ticker=h.ticker,
                    amount=div_amount,
                    reinvested=reinvest,
                )
            )
            if h.dividends_taxable:
                taxable_income += div_amount

        if reinvest and div_amount > 0:
            if is_cash_ticker:
                updated.append(
                    replace(
                        h,
                        qty=h.qty + div_amount,
                        cost_basis_total=h.cost_basis_total + div_amount,
                    )
                )
            else:
                new_shares = div_amount / h.price if h.price > 0 else 0.0
                updated.append(
                    replace(
                        h,
                        qty=h.qty + new_shares,
                        cost_basis_total=h.cost_basis_total + div_amount,
                    )
                )
        else:
            updated.append(h)
            if div_amount > 0 and not reinvest:
                updated.append(
                    Holding(
                        account_name=h.account_name,
                        owner=h.owner,
                        counterparty=h.counterparty,
                        account_type=h.account_type,
                        ticker="CASH",
                        qty=div_amount,
                        price=1.0,
                        cost_basis_total=div_amount,
                    )
                )

    return updated, dividend_records, taxable_income
