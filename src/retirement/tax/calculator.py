from __future__ import annotations
from dataclasses import dataclass
from retirement.tax.brackets import (
    FEDERAL_MFJ_BRACKETS,
    FEDERAL_MFJ_STANDARD_DEDUCTION,
    FEDERAL_SINGLE_BRACKETS,
    FEDERAL_SINGLE_STANDARD_DEDUCTION,
    FEDERAL_MFJ_LT_BRACKETS,
    AZ_FLAT_RATE,
    NIIT_RATE,
    NIIT_THRESHOLD_MFJ,
    TaxBracket,
)


def _tax_on_income(income: float, brackets: list[TaxBracket]) -> float:
    tax = 0.0
    for bracket in brackets:
        if income <= bracket.min_income:
            break
        taxable = min(income, bracket.max_income) - bracket.min_income
        tax += taxable * bracket.rate
    return tax


def _bracket_top_for_rate(rate: float, brackets: list[TaxBracket]) -> float:
    for bracket in brackets:
        if bracket.rate == rate:
            return bracket.max_income
    return float("inf")


@dataclass
class TaxResult:
    ordinary_income: float
    lt_gain_income: float
    federal_ordinary_tax: float
    federal_lt_tax: float
    az_tax: float
    niit: float

    @property
    def total_tax(self) -> float:
        return self.federal_ordinary_tax + self.federal_lt_tax + self.az_tax + self.niit


def calculate_tax_mfj(
    ordinary_income: float,
    lt_gain_income: float,
    net_investment_income: float,
) -> TaxResult:
    taxable_ordinary = max(0.0, ordinary_income - FEDERAL_MFJ_STANDARD_DEDUCTION)
    federal_ordinary_tax = _tax_on_income(taxable_ordinary, FEDERAL_MFJ_BRACKETS)

    # LT gains are stacked on top of taxable ordinary income for bracket placement
    lt_tax_with = _tax_on_income(taxable_ordinary + lt_gain_income, FEDERAL_MFJ_LT_BRACKETS)
    lt_tax_without = _tax_on_income(taxable_ordinary, FEDERAL_MFJ_LT_BRACKETS)
    federal_lt_tax = lt_tax_with - lt_tax_without

    az_tax = (ordinary_income + lt_gain_income) * AZ_FLAT_RATE

    magi = ordinary_income + lt_gain_income
    niit_base = min(net_investment_income, max(0.0, magi - NIIT_THRESHOLD_MFJ))
    niit = niit_base * NIIT_RATE

    return TaxResult(
        ordinary_income=ordinary_income,
        lt_gain_income=lt_gain_income,
        federal_ordinary_tax=federal_ordinary_tax,
        federal_lt_tax=federal_lt_tax,
        az_tax=az_tax,
        niit=niit,
    )


def calculate_tax_single(ordinary_income: float) -> float:
    taxable = max(0.0, ordinary_income - FEDERAL_SINGLE_STANDARD_DEDUCTION)
    return _tax_on_income(taxable, FEDERAL_SINGLE_BRACKETS)


def mfj_bracket_top_income(rate: float) -> float:
    """Gross income (before deduction) at the top of the given MFJ bracket rate."""
    return _bracket_top_for_rate(rate, FEDERAL_MFJ_BRACKETS) + FEDERAL_MFJ_STANDARD_DEDUCTION


def lt_gain_room_within_rate(ordinary_taxable_income: float, target_lt_rate: float) -> float:
    """How much LT gain can be added before exceeding the target LT bracket."""
    bracket_top = _bracket_top_for_rate(target_lt_rate, FEDERAL_MFJ_LT_BRACKETS)
    return max(0.0, bracket_top - ordinary_taxable_income)
