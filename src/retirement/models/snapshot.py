from __future__ import annotations
from dataclasses import dataclass, field
from retirement.models.holding import Holding
from retirement.tax.calculator import TaxResult


@dataclass
class DividendRecord:
    account_name: str
    owner: str
    counterparty: str
    account_type: str
    ticker: str
    amount: float
    reinvested: bool


@dataclass
class YearEndSnapshot:
    year: int
    ani_age: int
    nup_age: int
    ani_retired: bool
    nup_retired: bool
    holdings: list[Holding]
    dividend_records: list[DividendRecord]
    expenses: float
    medical_oop: float
    medical_premium: float
    taxable_dividend_income: float
    lt_gains_harvested: float
    roth_converted: float
    withdrawals: float
    tax_result: TaxResult

    @property
    def total_expenses(self) -> float:
        return self.expenses + self.medical_oop + self.medical_premium

    @property
    def total_portfolio_value(self) -> float:
        return sum(h.amount for h in self.holdings)
