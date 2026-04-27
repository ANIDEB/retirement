from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class PersonConfig:
    birth_year: int
    retirement_year: int
    assumed_salary_when_ani_retired: float = 0.0


@dataclass
class MedicarePart:
    standard_monthly: float
    irmaa_monthly_surcharge_per_person: float
    base_plan_monthly: float = 0.0

    @property
    def total_monthly_per_person(self) -> float:
        return self.standard_monthly + self.base_plan_monthly + self.irmaa_monthly_surcharge_per_person


@dataclass
class MedicareConfig:
    start_age: int
    part_b: MedicarePart
    part_d: MedicarePart

    def total_monthly_per_person(self) -> float:
        return self.part_b.total_monthly_per_person + self.part_d.total_monthly_per_person


@dataclass
class MedicalConfig:
    out_of_pocket_default: float
    out_of_pocket_by_year: dict[int, float]
    insurance_monthly_per_person_if_uninsured: float
    medicare: MedicareConfig


@dataclass
class RothConversionConfig:
    target_ticker: str
    fill_to_bracket_rate: float


@dataclass
class LTHarvestConfig:
    max_lt_gain_rate: float
    avoid_niit: bool
    niit_threshold_mfj: float


@dataclass
class TaxConfig:
    filing_status: str
    federal_rate_year: int
    state: str
    state_rate_year: int
    roth_conversion: RothConversionConfig
    lt_gain_harvesting: LTHarvestConfig


@dataclass
class TickerConfig:
    default_growth_rates: dict[str, float]
    default_dividend_rates: dict[str, float]
    cash_interest_rates_by_account_type: dict[str, float]
    hycash_interest_rate: float
    reinvest_dividends_accounts: list[str]


@dataclass
class Scenario:
    ani: PersonConfig
    nup: PersonConfig
    run_date: str
    projection_years: int
    expenses_default: float
    expenses_by_year: dict[int, float]
    inflation_default: float
    inflation_by_year: dict[int, float]
    medical: MedicalConfig
    tickers: TickerConfig
    custom_rates_by_year: dict[int, dict]
    tax: TaxConfig
