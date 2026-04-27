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

    Rules:
    - CASH/HYCASH: interest always increases the existing holding (regardless of reinvest list).
    - Equity in reinvest account: dividend buys more shares at year-end price.
    - Equity in non-reinvest account: dividend is added to the account's CASH balance.
      If the account has an existing CASH holding it is merged in; otherwise a new
      CASH holding is created and flagged is_new_dividend_cash=True so the writer
      shows it only as a DIV record (not a duplicate HOLDING row).

    Returns updated_holdings, dividend_records, taxable_dividend_income.
    """
    run_date = date.fromisoformat(scenario.run_date)
    fraction = quarters_remaining(run_date, year) / 4.0
    reinvest_set = set(scenario.tickers.reinvest_dividends_accounts)

    updated: list[Holding] = []
    dividend_records: list[DividendRecord] = []
    taxable_income = 0.0
    # Accumulate cash additions per account for equity dividends
    cash_additions: dict[str, float] = {}  # account_name -> total cash to add

    for h in holdings:
        rate = get_dividend_rate(h, year, scenario)
        div_amount = h.amount * rate * fraction
        is_cash = h.ticker in ("CASH", "HYCASH")

        if div_amount > 0:
            dividend_records.append(DividendRecord(
                account_name=h.account_name,
                owner=h.owner,
                counterparty=h.counterparty,
                account_type=h.account_type,
                ticker=h.ticker,
                amount=div_amount,
                reinvested=h.account_name in reinvest_set,
            ))
            if h.dividends_taxable:
                taxable_income += div_amount

        if is_cash:
            # Interest always stays in the same CASH/HYCASH holding
            if div_amount > 0:
                updated.append(replace(h, qty=h.qty + div_amount, cost_basis_total=h.cost_basis_total + div_amount))
            else:
                updated.append(h)
        elif h.account_name in reinvest_set and div_amount > 0:
            # Buy more shares at year-end price
            new_shares = div_amount / h.price if h.price > 0 else 0.0
            updated.append(replace(h, qty=h.qty + new_shares, cost_basis_total=h.cost_basis_total + div_amount))
        else:
            updated.append(h)
            if div_amount > 0:
                cash_additions[h.account_name] = cash_additions.get(h.account_name, 0.0) + div_amount

    # Merge equity-dividend cash into existing CASH holdings or create new flagged ones
    if cash_additions:
        merged: list[Holding] = []
        absorbed: set[str] = set()

        for h in updated:
            if h.ticker == "CASH" and h.account_name in cash_additions:
                add = cash_additions[h.account_name]
                merged.append(replace(h, qty=h.qty + add, cost_basis_total=h.cost_basis_total + add))
                absorbed.add(h.account_name)
            else:
                merged.append(h)

        # Accounts with no existing CASH holding get a new one flagged as dividend cash
        for acct, add in cash_additions.items():
            if acct not in absorbed:
                src = next(h for h in updated if h.account_name == acct)
                merged.append(Holding(
                    account_name=src.account_name,
                    owner=src.owner,
                    counterparty=src.counterparty,
                    account_type=src.account_type,
                    ticker="CASH",
                    qty=add,
                    price=1.0,
                    cost_basis_total=add,
                    is_new_dividend_cash=True,
                ))

        updated = merged

    return updated, dividend_records, taxable_income
