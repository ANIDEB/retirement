from __future__ import annotations
from retirement.models.scenario import MedicalConfig, Scenario


def get_inflated_value(
    base_value: float,
    base_year: int,
    target_year: int,
    scenario: Scenario,
) -> float:
    value = base_value
    for yr in range(base_year + 1, target_year + 1):
        rate = scenario.inflation_by_year.get(yr, scenario.inflation_default)
        value *= 1 + rate
    return value


def get_expenses(year: int, scenario: Scenario, run_year: int) -> float:
    base = scenario.expenses_by_year.get(run_year, scenario.expenses_default)
    return get_inflated_value(base, run_year, year, scenario)


def get_medical_oop(year: int, scenario: Scenario, run_year: int) -> float:
    base = scenario.medical.out_of_pocket_by_year.get(run_year, scenario.medical.out_of_pocket_default)
    return get_inflated_value(base, run_year, year, scenario)


def _person_premium(
    age: int,
    is_employed: bool,
    medical: MedicalConfig,
    insurance_monthly: float,
) -> float:
    if is_employed:
        return 0.0
    if age >= medical.medicare.start_age:
        return medical.medicare.total_monthly_per_person() * 12
    return insurance_monthly * 12


def calculate_medical_premium(
    ani_age: int,
    nup_age: int,
    ani_retired: bool,
    nup_retired: bool,
    scenario: Scenario,
) -> float:
    uninsured_monthly = scenario.medical.insurance_monthly_per_person_if_uninsured
    ani_premium = _person_premium(ani_age, not ani_retired, scenario.medical, uninsured_monthly)
    nup_premium = _person_premium(nup_age, not nup_retired, scenario.medical, uninsured_monthly)
    return ani_premium + nup_premium
