import json
import tempfile
from pathlib import Path
from retirement.loaders.scenario_loader import load_scenario


def _write_scenario(data: dict) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, tmp)
    tmp.close()
    return Path(tmp.name)


def _base_scenario():
    return {
        "people": {
            "ANI": {"birth_year": 1966, "retirement_year": 2028},
            "NUP": {"birth_year": 1969, "retirement_year": 2030,
                    "assumed_salary_when_ani_retired_and_nup_working": 50000},
        },
        "projection": {"run_date": "2026-04-26", "years": 30},
        "expenses": {"default": 100000, "by_year": {"2026": 100000}},
        "inflation": {"default": 0.03, "by_year": {"2026": 0.03}},
        "medical": {
            "out_of_pocket_excluding_premium": {"default": 5000, "by_year": {"2026": 5000}},
            "insurance_monthly_per_person_if_uninsured": 1000,
            "medicare": {
                "start_age": 65,
                "part_b": {"standard_monthly": 185.0, "irmaa_monthly_surcharge_per_person": 74.0},
                "part_d": {"base_plan_monthly": 35.0, "irmaa_monthly_surcharge_per_person": 12.9},
            },
        },
        "tickers": {
            "default_growth_rates": {"VFIAX": 0.07, "CASH": 0.0},
            "default_dividend_rates": {"VFIAX": 0.014, "CASH": 0.0},
            "cash_interest_rates_by_account_type": {"SAVINGS": 0.045},
            "hycash_interest_rate": {"rate": 0.035},
            "reinvest_dividends_accounts": {"accounts": ["ANI_VAN"]},
        },
        "custom_rates_by_year": {
            "example_2028": {"growth_rates": {"VFIAX": 0.05}},
            "2029": {"growth_rates": {"AAPL": 0.06}},
        },
        "tax": {
            "filing_status": "married_filing_jointly",
            "federal_rate_year": 2026,
            "state": "Arizona",
            "state_rate_year": 2026,
            "roth_conversion": {"target_ticker": "VFIAX", "fill_to_bracket_rate": 0.22},
            "lt_gain_harvesting": {
                "max_lt_gain_rate": 0.15,
                "avoid_niit": True,
                "niit_threshold_mfj": 250000,
            },
        },
    }


def test_load_people():
    s = load_scenario(_write_scenario(_base_scenario()))
    assert s.ani.birth_year == 1966
    assert s.ani.retirement_year == 2028
    assert s.nup.birth_year == 1969
    assert s.nup.retirement_year == 2030
    assert s.nup.assumed_salary_when_ani_retired == 50000


def test_load_projection():
    s = load_scenario(_write_scenario(_base_scenario()))
    assert s.run_date == "2026-04-26"
    assert s.projection_years == 30


def test_load_expenses():
    s = load_scenario(_write_scenario(_base_scenario()))
    assert s.expenses_default == 100000
    assert s.expenses_by_year[2026] == 100000


def test_load_inflation():
    s = load_scenario(_write_scenario(_base_scenario()))
    assert s.inflation_default == 0.03
    assert s.inflation_by_year[2026] == 0.03


def test_load_medical():
    s = load_scenario(_write_scenario(_base_scenario()))
    assert s.medical.out_of_pocket_default == 5000
    assert s.medical.out_of_pocket_by_year[2026] == 5000
    assert s.medical.insurance_monthly_per_person_if_uninsured == 1000
    assert s.medical.medicare.start_age == 65
    assert s.medical.medicare.part_b.standard_monthly == 185.0
    assert s.medical.medicare.part_b.irmaa_monthly_surcharge_per_person == 74.0
    assert s.medical.medicare.part_d.base_plan_monthly == 35.0


def test_load_tickers():
    s = load_scenario(_write_scenario(_base_scenario()))
    assert s.tickers.default_growth_rates["VFIAX"] == 0.07
    assert s.tickers.hycash_interest_rate == 0.035
    assert "ANI_VAN" in s.tickers.reinvest_dividends_accounts


def test_custom_rates_skips_non_numeric_keys():
    s = load_scenario(_write_scenario(_base_scenario()))
    assert "example_2028" not in str(s.custom_rates_by_year)
    assert 2029 in s.custom_rates_by_year


def test_load_tax():
    s = load_scenario(_write_scenario(_base_scenario()))
    assert s.tax.filing_status == "married_filing_jointly"
    assert s.tax.roth_conversion.target_ticker == "VFIAX"
    assert s.tax.lt_gain_harvesting.avoid_niit is True
