from retirement.tax.calculator import (
    calculate_tax_mfj,
    calculate_tax_single,
    mfj_bracket_top_income,
    lt_gain_room_within_rate,
    _tax_on_income,
    _bracket_top_for_rate,
)
from retirement.tax.brackets import FEDERAL_MFJ_BRACKETS, FEDERAL_MFJ_LT_BRACKETS


def test_zero_income_mfj():
    result = calculate_tax_mfj(0.0, 0.0, 0.0)
    assert result.total_tax == 0.0


def test_ordinary_income_10pct_bracket():
    result = calculate_tax_mfj(40_000.0, 0.0, 0.0)
    taxable = 40_000 - 30_000  # after standard deduction = 10_000
    expected_federal = 10_000 * 0.10
    assert abs(result.federal_ordinary_tax - expected_federal) < 0.01


def test_lt_gain_income_stacked():
    # Ordinary income just at standard deduction — all lt gains in 0% bracket
    result = calculate_tax_mfj(30_000.0, 50_000.0, 50_000.0)
    assert result.federal_lt_tax == 0.0


def test_lt_gain_income_into_15pct():
    # Ordinary taxable = 0 (income = deduction), lt gains exceed 0% bracket top
    result = calculate_tax_mfj(30_000.0, 200_000.0, 200_000.0)
    assert result.federal_lt_tax > 0


def test_az_tax():
    result = calculate_tax_mfj(100_000.0, 0.0, 0.0)
    assert abs(result.az_tax - 100_000 * 0.025) < 0.01


def test_niit_not_triggered_below_threshold():
    result = calculate_tax_mfj(200_000.0, 0.0, 0.0)
    assert result.niit == 0.0


def test_niit_triggered_above_threshold():
    result = calculate_tax_mfj(300_000.0, 0.0, 10_000.0)
    assert result.niit > 0


def test_total_tax_sum():
    result = calculate_tax_mfj(150_000.0, 20_000.0, 20_000.0)
    assert abs(result.total_tax - (result.federal_ordinary_tax + result.federal_lt_tax + result.az_tax + result.niit)) < 0.01


def test_calculate_tax_single_zero():
    assert calculate_tax_single(0.0) == 0.0


def test_calculate_tax_single_basic():
    tax = calculate_tax_single(50_000.0)
    taxable = 50_000 - 15_000  # = 35_000
    expected = 11_925 * 0.10 + (35_000 - 11_925) * 0.12
    assert abs(tax - expected) < 0.01


def test_mfj_bracket_top_income():
    top = mfj_bracket_top_income(0.22)
    assert top == 206_700 + 30_000


def test_lt_gain_room_within_rate():
    # 15% LT bracket top is $600,050; room from taxable income of 0 is $600,050
    room = lt_gain_room_within_rate(0.0, 0.15)
    assert room == 600_050.0


def test_lt_gain_room_partial():
    room = lt_gain_room_within_rate(50_000.0, 0.15)
    assert abs(room - (600_050 - 50_000)) < 0.01


def test_lt_gain_room_zero_when_exceeded():
    room = lt_gain_room_within_rate(700_000.0, 0.15)
    assert room == 0.0


def test_tax_on_income_zero():
    assert _tax_on_income(0.0, FEDERAL_MFJ_BRACKETS) == 0.0


def test_bracket_top_for_missing_rate():
    assert _bracket_top_for_rate(0.99, FEDERAL_MFJ_BRACKETS) == float("inf")
