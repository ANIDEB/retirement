from __future__ import annotations
from dataclasses import dataclass
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
class Transaction:
    year: int
    transaction_type: str  # LT_HARVEST | ROTH_CONVERSION | WITHDRAWAL | HSA_WITHDRAWAL
    account_name: str
    owner: str
    account_type: str
    ticker: str
    shares: float
    price: float
    amount: float
    cost_basis: float
    gain_loss: float
    note: str


@dataclass
class YearEndSnapshot:
    year: int
    ani_age: int
    nup_age: int
    ani_retired: bool
    nup_retired: bool
    holdings: list[Holding]
    dividend_records: list[DividendRecord]
    transactions: list[Transaction]
    expenses: float
    medical_oop: float
    ani_medical_premium: float
    nup_medical_premium: float
    taxable_dividend_income: float
    nup_salary: float
    lt_gains_harvested: float
    roth_converted: float
    hsa_used: float
    withdrawals: float
    tax_result: TaxResult

    @property
    def medical_premium(self) -> float:
        return self.ani_medical_premium + self.nup_medical_premium

    @property
    def total_expenses(self) -> float:
        return self.expenses + self.medical_oop + self.medical_premium

    @property
    def total_portfolio_value(self) -> float:
        return sum(h.amount for h in self.holdings)
