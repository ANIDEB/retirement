from __future__ import annotations
from datetime import date
from retirement.models.holding import Holding
from retirement.models.scenario import Scenario
from retirement.models.snapshot import Transaction, YearEndSnapshot
from retirement.engine.growth import apply_growth, year_growth_fraction
from retirement.engine.dividends import calculate_dividends
from retirement.engine.medical import get_expenses, get_medical_oop, calculate_medical_premium_detail
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

        # 1. Apply price growth (prorated for partial first year)
        fraction = year_growth_fraction(run_date, year)
        pre_growth = list(current)
        current = apply_growth(current, year, scenario, fraction)

        lt_harvested = 0.0
        roth_converted = 0.0
        tax_result = _zero_tax()
        hsa_used = 0.0
        total_withdrawn = 0.0
        nup_salary = 0.0
        all_transactions: list[Transaction] = []

        # 2. Dividends — amounts based on pre-growth values; reinvestment at year-end price
        current, div_records, div_txs, taxable_div = calculate_dividends(
            current, year, scenario, base_holdings=pre_growth
        )
        all_transactions.extend(div_txs)

        # 3. Expense and medical figures (nominal dollars for this year)
        expenses = get_expenses(year, scenario, run_year)
        medical_oop = get_medical_oop(year, scenario, run_year)
        ani_premium, nup_premium = calculate_medical_premium_detail(
            ani_age, nup_age, ani_retired, nup_retired, scenario
        )

        if not ani_retired:
            pass  # all expenses covered by salary; no portfolio activity needed
        else:
            nup_salary = scenario.nup.assumed_salary_when_ani_retired if not nup_retired else 0.0

            # 4. LT gain harvesting
            ordinary_taxable = max(0.0, taxable_div + nup_salary)
            current, lt_harvested, lt_txs = harvest_lt_gains(current, ordinary_taxable, scenario, year)
            all_transactions.extend(lt_txs)

            # 5. Roth conversion (fill 22% bracket)
            ordinary_before_conv = taxable_div + nup_salary + lt_harvested
            current, roth_converted, roth_txs = do_roth_conversion(
                current, ordinary_before_conv, scenario, year
            )
            all_transactions.extend(roth_txs)

            # 6. Tax on investment activity
            total_ordinary = taxable_div + roth_converted + nup_salary
            net_inv_income = taxable_div + lt_harvested
            tax_result = calculate_tax_mfj(
                ordinary_income=total_ordinary,
                lt_gain_income=lt_harvested,
                net_investment_income=net_inv_income,
            )

            # 7. Determine withdrawal needed
            income_available = nup_salary + taxable_div + lt_harvested
            total_needed = expenses + ani_premium + nup_premium + tax_result.total_tax
            after_income = max(0.0, total_needed - income_available)

            if both_retired:
                # HSA covers medical OOP + premium when both retired
                hsa_needed = medical_oop + ani_premium + nup_premium
                current, hsa_used, hsa_txs = withdraw_from_hsa(current, hsa_needed, year)
                all_transactions.extend(hsa_txs)
                # Reduce what still needs to come from regular accounts
                after_income = max(0.0, after_income - hsa_used)
            else:
                # Medical OOP covered by salary; include in what must be withdrawn
                after_income = max(0.0, after_income + medical_oop)

            current, total_withdrawn, wd_txs = withdraw_funds(current, after_income, year)
            all_transactions.extend(wd_txs)

        snapshots.append(
            YearEndSnapshot(
                year=year,
                ani_age=ani_age,
                nup_age=nup_age,
                ani_retired=ani_retired,
                nup_retired=nup_retired,
                holdings=list(current),
                dividend_records=div_records,
                transactions=all_transactions,
                expenses=expenses,
                medical_oop=medical_oop,
                ani_medical_premium=ani_premium,
                nup_medical_premium=nup_premium,
                taxable_dividend_income=taxable_div,
                nup_salary=nup_salary,
                lt_gains_harvested=lt_harvested,
                roth_converted=roth_converted,
                hsa_used=hsa_used,
                withdrawals=total_withdrawn,
                tax_result=tax_result,
            )
        )

    return snapshots
