import pytest
from retirement.models.holding import Holding
from retirement.models.scenario import (
    LTHarvestConfig, MedicalConfig, MedicareConfig, MedicarePart,
    PersonConfig, RothConversionConfig, Scenario, TaxConfig, TickerConfig,
)


def make_holding(
    account_name="ACC",
    owner="ANI",
    counterparty="ETrade",
    account_type="BROKERAGE",
    ticker="VFIAX",
    qty=100.0,
    price=100.0,
    cost_basis=5000.0,
) -> Holding:
    return Holding(account_name, owner, counterparty, account_type, ticker, qty, price, cost_basis)


def make_scenario(
    ani_retirement_year=2028,
    nup_retirement_year=2030,
    run_date="2026-04-26",
    projection_years=5,
    custom_rates_by_year=None,
) -> Scenario:
    if custom_rates_by_year is None:
        custom_rates_by_year = {2029: {"growth_rates": {"VFIAX": 0.05}}}
    return Scenario(
        ani=PersonConfig(birth_year=1966, retirement_year=ani_retirement_year),
        nup=PersonConfig(birth_year=1969, retirement_year=nup_retirement_year,
                         assumed_salary_when_ani_retired=50_000),
        run_date=run_date,
        projection_years=projection_years,
        expenses_default=100_000,
        expenses_by_year={2026: 100_000},
        inflation_default=0.03,
        inflation_by_year={2026: 0.03},
        medical=MedicalConfig(
            out_of_pocket_default=5_000,
            out_of_pocket_by_year={2026: 5_000},
            insurance_monthly_per_person_if_uninsured=1_000,
            medicare=MedicareConfig(
                start_age=65,
                part_b=MedicarePart(standard_monthly=185.0, irmaa_monthly_surcharge_per_person=74.0),
                part_d=MedicarePart(standard_monthly=0.0, base_plan_monthly=35.0,
                                    irmaa_monthly_surcharge_per_person=12.9),
            ),
        ),
        tickers=TickerConfig(
            default_growth_rates={"VFIAX": 0.07, "CASH": 0.0, "HYCASH": 0.0, "QQQ": 0.08},
            default_dividend_rates={"VFIAX": 0.014, "CASH": 0.0, "HYCASH": 0.0, "QQQ": 0.006},
            cash_interest_rates_by_account_type={"SAVINGS": 0.045, "BROKERAGE": 0.02},
            hycash_interest_rate=0.035,
            reinvest_dividends_accounts=["ANI_VAN", "ANI_AMEX", "NUP_AMEX"],
        ),
        custom_rates_by_year=custom_rates_by_year,
        tax=TaxConfig(
            filing_status="married_filing_jointly",
            federal_rate_year=2026,
            state="Arizona",
            state_rate_year=2026,
            roth_conversion=RothConversionConfig(target_ticker="VFIAX", fill_to_bracket_rate=0.22),
            lt_gain_harvesting=LTHarvestConfig(
                max_lt_gain_rate=0.15,
                avoid_niit=True,
                niit_threshold_mfj=250_000,
            ),
        ),
    )


@pytest.fixture
def scenario() -> Scenario:
    return make_scenario()
