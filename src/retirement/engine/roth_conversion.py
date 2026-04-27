from __future__ import annotations
from dataclasses import replace
from retirement.models.holding import Holding
from retirement.models.scenario import Scenario
from retirement.tax.calculator import mfj_bracket_top_income


def _tax_deferred_holdings(holdings: list[Holding]) -> list[Holding]:
    return [h for h in holdings if h.account_type == "TAX_DEFRD" and h.qty > 0]


def _find_or_create_roth_holding(
    holdings: list[Holding],
    target_ticker: str,
    owner: str,
) -> tuple[Holding | None, list[Holding]]:
    for h in holdings:
        if h.account_type == "ROTH" and h.ticker == target_ticker and h.owner == owner:
            return h, holdings
    return None, holdings


def do_roth_conversion(
    holdings: list[Holding],
    ordinary_income_before_conversion: float,
    scenario: Scenario,
) -> tuple[list[Holding], float]:
    """
    Convert from TAX_DEFRD to ROTH (target_ticker) up to fill the target bracket.

    Returns:
        updated holdings, amount converted (taxable ordinary income)
    """
    cfg = scenario.tax.roth_conversion
    bracket_top = mfj_bracket_top_income(cfg.fill_to_bracket_rate)
    room = max(0.0, bracket_top - ordinary_income_before_conversion)
    if room <= 0:
        return holdings, 0.0

    deferred = sorted(
        _tax_deferred_holdings(holdings),
        key=lambda h: h.return_pct,
    )

    remaining_room = room
    updated = {id(h): h for h in holdings}
    total_converted = 0.0

    for src in deferred:
        if remaining_room <= 0:
            break
        convert_value = min(src.amount, remaining_room)
        shares_to_sell = convert_value / src.price if src.price > 0 else 0.0
        shares_to_sell = min(shares_to_sell, src.qty)
        actual_value = shares_to_sell * src.price

        new_src_qty = src.qty - shares_to_sell
        updated[id(src)] = replace(src, qty=new_src_qty, cost_basis_total=0.0 if new_src_qty == 0 else src.cost_basis_total)

        roth_existing, _ = _find_or_create_roth_holding(list(updated.values()), cfg.target_ticker, src.owner)
        roth_price = roth_existing.price if roth_existing else src.price
        new_roth_shares = actual_value / roth_price if roth_price > 0 else 0.0

        if roth_existing is not None:
            updated[id(roth_existing)] = replace(
                roth_existing,
                qty=roth_existing.qty + new_roth_shares,
                cost_basis_total=roth_existing.cost_basis_total + actual_value,
            )
        else:
            new_roth = Holding(
                account_name=f"{src.owner}_ROTH_CONV",
                owner=src.owner,
                counterparty=src.counterparty,
                account_type="ROTH",
                ticker=cfg.target_ticker,
                qty=new_roth_shares,
                price=roth_price,
                cost_basis_total=actual_value,
            )
            updated[id(new_roth)] = new_roth

        total_converted += actual_value
        remaining_room -= actual_value

    return list(updated.values()), total_converted
