# 2025 federal brackets used as proxy for 2026 (official 2026 rates not yet published).
# Update these when IRS announces 2026 inflation adjustments.

from dataclasses import dataclass


@dataclass
class TaxBracket:
    rate: float
    min_income: float
    max_income: float  # float("inf") for the top bracket


FEDERAL_MFJ_BRACKETS: list[TaxBracket] = [
    TaxBracket(0.10,      0,      23_850),
    TaxBracket(0.12,  23_850,     96_950),
    TaxBracket(0.22,  96_950,    206_700),
    TaxBracket(0.24, 206_700,    394_600),
    TaxBracket(0.32, 394_600,    501_050),
    TaxBracket(0.35, 501_050,    751_600),
    TaxBracket(0.37, 751_600, float("inf")),
]

FEDERAL_MFJ_STANDARD_DEDUCTION: float = 30_000

FEDERAL_SINGLE_BRACKETS: list[TaxBracket] = [
    TaxBracket(0.10,      0,      11_925),
    TaxBracket(0.12,  11_925,     48_475),
    TaxBracket(0.22,  48_475,    103_350),
    TaxBracket(0.24, 103_350,    197_300),
    TaxBracket(0.32, 197_300,    250_525),
    TaxBracket(0.35, 250_525,    626_350),
    TaxBracket(0.37, 626_350, float("inf")),
]

FEDERAL_SINGLE_STANDARD_DEDUCTION: float = 15_000

# LT Capital Gains brackets (MFJ, 2025) — applied to taxable income including LT gains
FEDERAL_MFJ_LT_BRACKETS: list[TaxBracket] = [
    TaxBracket(0.00,       0,      96_700),
    TaxBracket(0.15,  96_700,     600_050),
    TaxBracket(0.20, 600_050, float("inf")),
]

AZ_FLAT_RATE: float = 0.025  # Arizona flat income tax rate

NIIT_RATE: float = 0.038
NIIT_THRESHOLD_MFJ: float = 250_000
