from __future__ import annotations
import csv
import re
from pathlib import Path
from retirement.models.holding import Holding


def _parse_dollar(value: str) -> float:
    cleaned = re.sub(r"[\$,\s]", "", value.strip())
    if cleaned in ("", "-"):
        return 0.0
    return float(cleaned)


def load_holdings(csv_path: Path) -> list[Holding]:
    holdings: list[Holding] = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items() if k and k.strip()}
            name = row.get("Name", "")
            ticker = row.get("Ticker", "")
            if not name or not ticker:
                continue
            try:
                qty = float(row.get("Qty", "0"))
            except ValueError:
                continue
            price = _parse_dollar(row.get("Rate", "0"))
            cost_basis = _parse_dollar(row.get("Cost Basis", "0"))
            holdings.append(
                Holding(
                    account_name=name,
                    owner=row.get("OWNER", ""),
                    counterparty=row.get("Counterparty", ""),
                    account_type=row.get("Type", ""),
                    ticker=ticker,
                    qty=qty,
                    price=price,
                    cost_basis_total=cost_basis,
                )
            )
    return holdings
