from __future__ import annotations
from dataclasses import dataclass

TAXABLE_ACCOUNT_TYPES: frozenset[str] = frozenset({"SAVINGS", "BROKERAGE", "HY_SAVINGS"})


@dataclass
class Holding:
    account_name: str
    owner: str
    counterparty: str
    account_type: str
    ticker: str
    qty: float
    price: float
    cost_basis_total: float

    @property
    def amount(self) -> float:
        return self.qty * self.price

    @property
    def cost_basis_per_share(self) -> float:
        return self.cost_basis_total / self.qty if self.qty else 0.0

    @property
    def unrealized_gain(self) -> float:
        return self.amount - self.cost_basis_total

    @property
    def return_pct(self) -> float:
        if self.cost_basis_total == 0:
            return float("inf")
        return self.unrealized_gain / self.cost_basis_total

    @property
    def dividends_taxable(self) -> bool:
        return self.account_type in TAXABLE_ACCOUNT_TYPES
