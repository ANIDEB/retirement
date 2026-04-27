from __future__ import annotations
from dataclasses import replace
from retirement.models.holding import Holding
from retirement.models.scenario import Scenario
from retirement.models.snapshot import Transaction
from retirement.tax.calculator import lt_gain_room_within_rate


def _brokerage_holdings_with_gains(holdings: list[Holding]) -> list[Holding]:
    return [
        h for h in holdings
        if h.account_type == "BROKERAGE"
        and h.ticker != "CASH"
        and h.unrealized_gain > 0
    ]


def harvest_lt_gains(
    holdings: list[Holding],
    ordinary_taxable_income: float,
    scenario: Scenario,
    year: int,
) -> tuple[list[Holding], float, list[Transaction]]:
    """
    Sell brokerage LT gains staying within the 15% LT bracket and below NIIT threshold.

    Returns updated holdings, total lt_gains_harvested, and transaction records.
    """
    cfg = scenario.tax.lt_gain_harvesting

    lt_room = lt_gain_room_within_rate(ordinary_taxable_income, cfg.max_lt_gain_rate)

    if cfg.avoid_niit:
        niit_room = max(0.0, cfg.niit_threshold_mfj - ordinary_taxable_income)
        lt_room = min(lt_room, niit_room)

    if lt_room <= 0:
        return holdings, 0.0, []

    candidates = sorted(
        _brokerage_holdings_with_gains(holdings),
        key=lambda h: h.return_pct,
    )

    remaining_room = lt_room
    updated = {id(h): h for h in holdings}
    transactions: list[Transaction] = []
    total_harvested = 0.0

    for h in candidates:
        if remaining_room <= 0:
            break
        harvestable_gain = min(h.unrealized_gain, remaining_room)
        gain_per_share = h.price - h.cost_basis_per_share
        shares_to_sell = harvestable_gain / gain_per_share
        shares_to_sell = min(shares_to_sell, h.qty)
        proceeds = shares_to_sell * h.price
        cost = shares_to_sell * h.cost_basis_per_share
        gain = proceeds - cost

        new_qty = h.qty - shares_to_sell
        new_cost = h.cost_basis_total - cost
        updated[id(h)] = replace(h, qty=new_qty, cost_basis_total=max(0.0, new_cost))

        cash_record = Holding(
            account_name=h.account_name,
            owner=h.owner,
            counterparty=h.counterparty,
            account_type=h.account_type,
            ticker="CASH",
            qty=proceeds,
            price=1.0,
            cost_basis_total=proceeds,
        )
        updated[id(cash_record)] = cash_record

        transactions.append(Transaction(
            year=year,
            transaction_type="LT_HARVEST",
            account_name=h.account_name,
            owner=h.owner,
            account_type=h.account_type,
            ticker=h.ticker,
            shares=shares_to_sell,
            price=h.price,
            amount=proceeds,
            cost_basis=cost,
            gain_loss=gain,
            note=f"LT gain harvest — {h.return_pct:.0%} historical return",
        ))

        total_harvested += gain
        remaining_room -= gain

    return list(updated.values()), total_harvested, transactions
