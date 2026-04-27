from __future__ import annotations
import json
from pathlib import Path
from retirement.models.scenario import (
    LTHarvestConfig,
    MedicalConfig,
    MedicareConfig,
    MedicarePart,
    PersonConfig,
    RothConversionConfig,
    Scenario,
    TaxConfig,
    TickerConfig,
)


def load_scenario(json_path: Path) -> Scenario:
    with open(json_path) as f:
        data = json.load(f)

    ani_d = data["people"]["ANI"]
    nup_d = data["people"]["NUP"]
    ani = PersonConfig(birth_year=ani_d["birth_year"], retirement_year=ani_d["retirement_year"])
    nup = PersonConfig(
        birth_year=nup_d["birth_year"],
        retirement_year=nup_d["retirement_year"],
        assumed_salary_when_ani_retired=nup_d.get(
            "assumed_salary_when_ani_retired_and_nup_working", 0.0
        ),
    )

    oop_d = data["medical"]["out_of_pocket_excluding_premium"]
    med_d = data["medical"]
    part_b_d = med_d["medicare"]["part_b"]
    part_d_d = med_d["medicare"]["part_d"]
    medical = MedicalConfig(
        out_of_pocket_default=oop_d["default"],
        out_of_pocket_by_year={int(k): v for k, v in oop_d.get("by_year", {}).items()},
        insurance_monthly_per_person_if_uninsured=med_d["insurance_monthly_per_person_if_uninsured"],
        medicare=MedicareConfig(
            start_age=med_d["medicare"]["start_age"],
            part_b=MedicarePart(
                standard_monthly=part_b_d["standard_monthly"],
                irmaa_monthly_surcharge_per_person=part_b_d["irmaa_monthly_surcharge_per_person"],
            ),
            part_d=MedicarePart(
                standard_monthly=0.0,
                base_plan_monthly=part_d_d["base_plan_monthly"],
                irmaa_monthly_surcharge_per_person=part_d_d["irmaa_monthly_surcharge_per_person"],
            ),
        ),
    )

    ticker_d = data["tickers"]
    tickers = TickerConfig(
        default_growth_rates=ticker_d["default_growth_rates"],
        default_dividend_rates=ticker_d["default_dividend_rates"],
        cash_interest_rates_by_account_type=ticker_d["cash_interest_rates_by_account_type"],
        hycash_interest_rate=ticker_d["hycash_interest_rate"]["rate"],
        reinvest_dividends_accounts=ticker_d["reinvest_dividends_accounts"]["accounts"],
    )

    custom_rates: dict[int, dict] = {}
    for k, v in data.get("custom_rates_by_year", {}).items():
        if k.lstrip("-").isdigit():
            custom_rates[int(k)] = v

    tax_d = data["tax"]
    tax = TaxConfig(
        filing_status=tax_d["filing_status"],
        federal_rate_year=tax_d["federal_rate_year"],
        state=tax_d["state"],
        state_rate_year=tax_d["state_rate_year"],
        roth_conversion=RothConversionConfig(
            target_ticker=tax_d["roth_conversion"]["target_ticker"],
            fill_to_bracket_rate=tax_d["roth_conversion"]["fill_to_bracket_rate"],
        ),
        lt_gain_harvesting=LTHarvestConfig(
            max_lt_gain_rate=tax_d["lt_gain_harvesting"]["max_lt_gain_rate"],
            avoid_niit=tax_d["lt_gain_harvesting"]["avoid_niit"],
            niit_threshold_mfj=tax_d["lt_gain_harvesting"]["niit_threshold_mfj"],
        ),
    )

    proj_d = data["projection"]
    exp_d = data["expenses"]
    inf_d = data["inflation"]

    return Scenario(
        ani=ani,
        nup=nup,
        run_date=proj_d["run_date"],
        projection_years=proj_d["years"],
        expenses_default=exp_d["default"],
        expenses_by_year={int(k): v for k, v in exp_d.get("by_year", {}).items()},
        inflation_default=inf_d["default"],
        inflation_by_year={int(k): v for k, v in inf_d.get("by_year", {}).items()},
        medical=medical,
        tickers=tickers,
        custom_rates_by_year=custom_rates,
        tax=tax,
    )
