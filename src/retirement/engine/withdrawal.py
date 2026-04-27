from __future__ import annotations
from dataclasses import replace
from retirement.models.holding import Holding

HSA_ACCOUNT_TYPE = "HSA"


def withdraw_from_hsa(
    holdings: list[Holding],
    amount_needed: float,
) -> tuple[list[Holding], float]:
    """Drain HSA cash first, then HSA equities (for medical expenses only)."""
    updated = {id(h): h for h in holdings}
    withdrawn = 0.0
    remaining = amount_needed

    for h in [x for x in holdings if x.account_type == HSA_ACCOUNT_TYPE and x.ticker in ("CASH", "HYCASH")]:
        if remaining <= 0:
            break
        take = min(h.qty, remaining)
        updated[id(h)] = replace(h, qty=h.qty - take, cost_basis_total=h.cost_basis_total - take)
        withdrawn += take
        remaining -= take

    for h in sorted(
        [x for x in holdings if x.account_type == HSA_ACCOUNT_TYPE and x.ticker not in ("CASH", "HYCASH") and x.qty > 0],
        key=lambda x: x.return_pct,
    ):
        if remaining <= 0:
            break
        sell_value = min(h.amount, remaining)
        shares = sell_value / h.price if h.price > 0 else 0.0
        shares = min(shares, h.qty)
        actual = shares * h.price
        new_cost = h.cost_basis_total * (1 - shares / h.qty) if h.qty > 0 else 0.0
        updated[id(h)] = replace(h, qty=h.qty - shares, cost_basis_total=max(0.0, new_cost))
        withdrawn += actual
        remaining -= actual

    return list(updated.values()), withdrawn


def withdraw_funds(
    holdings: list[Holding],
    amount_needed: float,
) -> tuple[list[Holding], float]:
    """
    Withdraw needed funds from non-HSA accounts.
    Order: BROKERAGE cash → SAVINGS/HY_SAVINGS cash → BROKERAGE equities (lowest return first)
           → TAX_DEFRD cash → TAX_DEFRD equities → ROTH cash → ROTH equities.
    """
    if amount_needed <= 0:
        return holdings, 0.0

    updated = {id(h): h for h in holdings}
    remaining = amount_needed
    total_withdrawn = 0.0

    def _drain_cash(account_types: list[str]) -> None:
        nonlocal remaining, total_withdrawn
        for atype in account_types:
            for h in [x for x in list(updated.values()) if x.account_type == atype and x.ticker in ("CASH", "HYCASH") and x.qty > 0]:
                if remaining <= 0:
                    return
                take = min(h.qty, remaining)
                updated[id(h)] = replace(h, qty=h.qty - take, cost_basis_total=h.cost_basis_total - take)
                total_withdrawn += take
                remaining -= take

    def _sell_equities(account_types: list[str]) -> None:
        nonlocal remaining, total_withdrawn
        candidates = sorted(
            [x for x in list(updated.values())
             if x.account_type in account_types and x.ticker not in ("CASH", "HYCASH") and x.qty > 0],
            key=lambda x: x.return_pct,
        )
        for h in candidates:
            if remaining <= 0:
                return
            sell_value = min(h.amount, remaining)
            shares = sell_value / h.price if h.price > 0 else 0.0
            shares = min(shares, h.qty)
            actual = shares * h.price
            cost_fraction = shares / h.qty if h.qty > 0 else 0.0
            new_cost = h.cost_basis_total * (1 - cost_fraction)
            updated[id(h)] = replace(h, qty=h.qty - shares, cost_basis_total=max(0.0, new_cost))
            total_withdrawn += actual
            remaining -= actual

    _drain_cash(["BROKERAGE"])
    _drain_cash(["SAVINGS", "HY_SAVINGS"])
    _sell_equities(["BROKERAGE"])
    _drain_cash(["TAX_DEFRD"])
    _sell_equities(["TAX_DEFRD"])
    _drain_cash(["ROTH"])
    _sell_equities(["ROTH"])

    return list(updated.values()), total_withdrawn
