from retirement.engine.medical import (
    get_inflated_value,
    get_expenses,
    get_medical_oop,
    calculate_medical_premium,
    calculate_medical_premium_detail,
    _person_premium,
)
from tests.conftest import make_scenario


def test_get_inflated_value_same_year(scenario):
    assert get_inflated_value(100_000, 2026, 2026, scenario) == 100_000


def test_get_inflated_value_one_year(scenario):
    result = get_inflated_value(100_000, 2026, 2027, scenario)
    assert abs(result - 103_000) < 1.0


def test_get_inflated_value_two_years(scenario):
    result = get_inflated_value(100_000, 2026, 2028, scenario)
    assert abs(result - 100_000 * 1.03 * 1.03) < 1.0


def test_get_expenses_uses_run_year_base(scenario):
    result = get_expenses(2026, scenario, 2026)
    assert result == 100_000.0


def test_get_expenses_inflated(scenario):
    result = get_expenses(2027, scenario, 2026)
    assert abs(result - 103_000) < 1.0


def test_get_expenses_missing_year_uses_default(scenario):
    result = get_expenses(2035, scenario, 2026)
    assert result > 100_000  # inflated default


def test_get_medical_oop_run_year(scenario):
    assert get_medical_oop(2026, scenario, 2026) == 5_000.0


def test_get_medical_oop_inflated(scenario):
    result = get_medical_oop(2027, scenario, 2026)
    assert abs(result - 5_150) < 1.0


def test_person_premium_employed():
    from retirement.models.scenario import MedicalConfig, MedicareConfig, MedicarePart
    med = MedicalConfig(
        out_of_pocket_default=0, out_of_pocket_by_year={},
        insurance_monthly_per_person_if_uninsured=1000,
        medicare=MedicareConfig(
            start_age=65,
            part_b=MedicarePart(185, 74),
            part_d=MedicarePart(0, 35, 12.9),
        ),
    )
    assert _person_premium(60, is_employed=True, medical=med, insurance_monthly=1000) == 0.0


def test_person_premium_under_65_not_employed():
    from retirement.models.scenario import MedicalConfig, MedicareConfig, MedicarePart
    med = MedicalConfig(
        out_of_pocket_default=0, out_of_pocket_by_year={},
        insurance_monthly_per_person_if_uninsured=1000,
        medicare=MedicareConfig(start_age=65, part_b=MedicarePart(185, 74),
                                part_d=MedicarePart(0, 35, 12.9)),
    )
    assert _person_premium(60, is_employed=False, medical=med, insurance_monthly=1000) == 12_000.0


def test_person_premium_on_medicare():
    from retirement.models.scenario import MedicalConfig, MedicareConfig, MedicarePart
    med = MedicalConfig(
        out_of_pocket_default=0, out_of_pocket_by_year={},
        insurance_monthly_per_person_if_uninsured=1000,
        medicare=MedicareConfig(start_age=65, part_b=MedicarePart(185, 74),
                                part_d=MedicarePart(0, 35, 12.9)),
    )
    premium = _person_premium(65, is_employed=False, medical=med, insurance_monthly=1000)
    expected = (185 + 74 + 35 + 12.9) * 12
    assert abs(premium - expected) < 0.01


def test_calculate_medical_premium_both_employed(scenario):
    assert calculate_medical_premium(60, 57, False, False, scenario) == 0.0


def test_calculate_medical_premium_ani_retired_nup_employed(scenario):
    premium = calculate_medical_premium(62, 59, True, False, scenario)
    assert premium == 12_000.0  # ANI not on Medicare, NUP employed


def test_calculate_medical_premium_both_retired_no_medicare(scenario):
    premium = calculate_medical_premium(62, 59, True, True, scenario)
    assert premium == 24_000.0  # both uninsured, $1000/person/month


def test_calculate_medical_premium_ani_on_medicare(scenario):
    premium = calculate_medical_premium(65, 62, True, True, scenario)
    ani_premium = (185 + 74 + 35 + 12.9) * 12
    nup_premium = 12_000.0
    assert abs(premium - (ani_premium + nup_premium)) < 0.01


def test_calculate_medical_premium_detail_returns_separate(scenario):
    ani, nup = calculate_medical_premium_detail(65, 62, True, True, scenario)
    total = calculate_medical_premium(65, 62, True, True, scenario)
    assert abs(ani + nup - total) < 0.01


def test_calculate_medical_premium_detail_both_employed(scenario):
    ani, nup = calculate_medical_premium_detail(60, 57, False, False, scenario)
    assert ani == 0.0
    assert nup == 0.0
