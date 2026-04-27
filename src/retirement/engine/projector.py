from __future__ import annotations
from datetime import date
from retirement.models.holding import Holding
from retirement.models.scenario import Scenario
from retirement.models.snapshot import YearEndSnapshot
from retirement.engine.growth import apply_growth
from retirement.engine.dividends import calculate_dividends
from retirement.engine.medical import get_expenses, get_medical_oop, calculate_medical_premium
from retirement.engine.lt_harvesting import harvest_lt_gains
from retirement.engine.roth_conversion import do_roth_conversion
from retirement.engine.withdrawal import withdraw_from_hsa, withdraw_funds
from retirement.tax.calculator import calculate_tax_mfj, TaxResult


def _zero_tax() -> TaxResult:
    return TaxResult(
        ordinary_income=0.0,
        lt_gain_income=0.0,
        federal_ordinary_tax=0.0,
        federal_lt_tax=0.0,
        az_tax=0.0,
        niit=0.0,
    )


def run_projection(
    holdings: list[Holding],
    scenario: Scenario,
) -> list[YearEndSnapshot]:
    run_date = date.fromisoformat(scenario.run_date)
    run_year = run_date.year

    current = list(holdings)
    snapshots: list[YearEndSnapshot] = []

    for offset in range(scenario.projection_years):
        year = run_year + offset

        ani_age = year - scenario.ani.birth_year
        nup_age = year - scenario.nup.birth_year
        ani_retired = year > scenario.ani.retirement_year
        nup_retired = year > scenario.nup.retirement_year
        both_retired = ani_retired and nup_retired

        # 1. Apply price growth
        current = apply_growth(current, year, scenario)

        # 2. Dividends / interest
        current, div_records, taxable_div = calculate_dividends(current, year, scenario)

        # 3. Expense and medical figures (in nominal dollars for this year)
        expenses = get_expenses(year, scenario, run_year)
        medical_oop = get_medical_oop(year, scenario, run_year)
        medical_premium = calculate_medical_premium(ani_age, nup_age, ani_retired, nup_retired, scenario)

        lt_harvested = 0.0
        roth_converted = 0.0
        tax_result = _zero_tax()
        total_withdrawn = 0.0

        if not ani_retired:
            # All expenses covered by salary; no withdrawals or conversions needed
            pass
        else:
            nup_salary = scenario.nup.assumed_salary_when_ani_retired if not nup_retired else 0.0

            # 4. LT gain harvesting (brokerage gains within 15% bracket / NIIT limit)
            ordinary_taxable = max(0.0, taxable_div + nup_salary)
            current, lt_harvested = harvest_lt_gains(current, ordinary_taxable, scenario)

            # 5. Roth conversion (fill 22% bracket)
            ordinary_before_conversion = taxable_div + nup_salary + lt_harvested
            current, roth_converted = do_roth_conversion(current, ordinary_before_conversion, scenario)

            # 6. Tax on investment activity (dividends + LT gains + Roth conversion + NUP salary)
            total_ordinary = taxable_div + roth_converted + nup_salary
            net_inv_income = taxable_div + lt_harvested
            tax_result = calculate_tax_mfj(
                ordinary_income=total_ordinary,
                lt_gain_income=lt_harvested,
                net_investment_income=net_inv_income,
            )

            # 7. Withdrawal needed after accounting for investment income and salary
            income_available = nup_salary + taxable_div + lt_harvested
            total_needed = expenses + medical_premium + tax_result.total_tax
            after_income = max(0.0, total_needed - income_available)

            # HSA covers medical costs (out-of-pocket + premium) when both are retired
            if both_retired:
                hsa_needed = medical_oop + medical_premium
                current, hsa_withdrawn = withdraw_from_hsa(current, hsa_needed)
                after_income = max(0.0, after_income - hsa_withdrawn)
            else:
                # Medical OOP covered by salary; add it to the non-HSA withdrawal need
                after_income = max(0.0, after_income + medical_oop)

            current, total_withdrawn = withdraw_funds(current, after_income)

        snapshots.append(
            YearEndSnapshot(
                year=year,
                ani_age=ani_age,
                nup_age=nup_age,
                ani_retired=ani_retired,
                nup_retired=nup_retired,
                holdings=list(current),
                dividend_records=div_records,
                expenses=expenses,
                medical_oop=medical_oop,
                medical_premium=medical_premium,
                taxable_dividend_income=taxable_div,
                lt_gains_harvested=lt_harvested,
                roth_converted=roth_converted,
                withdrawals=total_withdrawn,
                tax_result=tax_result,
            )
        )

    return snapshots
