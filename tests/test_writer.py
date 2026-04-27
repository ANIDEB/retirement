import csv
import tempfile
from pathlib import Path
from retirement.output.writer import write_snapshots, _fmt
from retirement.models.snapshot import YearEndSnapshot, DividendRecord, Transaction
from retirement.tax.calculator import TaxResult
from tests.conftest import make_holding


def _make_tx(year=2026):
    return Transaction(
        year=year, transaction_type="LT_HARVEST",
        account_name="ACC", owner="ANI", account_type="BROKERAGE",
        ticker="AAPL", shares=10.0, price=200.0, amount=2000.0,
        cost_basis=500.0, gain_loss=1500.0, note="test harvest",
    )


def _make_snapshot(year=2026):
    return YearEndSnapshot(
        year=year,
        ani_age=60, nup_age=57, ani_retired=False, nup_retired=False,
        holdings=[make_holding(ticker="VFIAX", qty=100, price=200, cost_basis=5000)],
        dividend_records=[
            DividendRecord("ACC", "ANI", "ETrade", "BROKERAGE", "VFIAX", amount=500.0, reinvested=True),
            DividendRecord("ACC2", "ANI", "ETrade", "BROKERAGE", "VFIAX", amount=200.0, reinvested=False),
        ],
        transactions=[_make_tx(year)],
        expenses=100_000.0,
        medical_oop=5_000.0,
        ani_medical_premium=0.0,
        nup_medical_premium=0.0,
        taxable_dividend_income=700.0,
        nup_salary=0.0,
        lt_gains_harvested=1_500.0,
        roth_converted=0.0,
        hsa_used=0.0,
        withdrawals=0.0,
        tax_result=TaxResult(
            ordinary_income=700.0, lt_gain_income=1_500.0,
            federal_ordinary_tax=0.0, federal_lt_tax=225.0, az_tax=55.0, niit=0.0,
        ),
    )


def test_write_creates_three_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        write_snapshots([_make_snapshot()], out)
        assert len(list(out.glob("detail_*.csv"))) == 1
        assert len(list(out.glob("expenses_*.csv"))) == 1
        assert len(list(out.glob("transactions_*.csv"))) == 1


def test_detail_file_has_holding_rows():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        write_snapshots([_make_snapshot()], out)
        detail = list(out.glob("detail_*.csv"))[0]
        rows = list(csv.DictReader(open(detail)))
        assert any(r["record_type"] == "HOLDING" for r in rows)


def test_detail_skips_new_dividend_cash_holdings():
    from dataclasses import replace as dc_replace
    snap = _make_snapshot()
    div_cash_holding = dc_replace(
        make_holding(ticker="CASH", qty=450, price=1.0, cost_basis=450),
        is_new_dividend_cash=True,
    )
    snap2 = snap.__class__(
        **{**snap.__dict__, "holdings": snap.holdings + [div_cash_holding]}
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        write_snapshots([snap2], out)
        detail = list(out.glob("detail_*.csv"))[0]
        rows = list(csv.DictReader(open(detail)))
        holding_rows = [r for r in rows if r["record_type"] == "HOLDING"]
        # dividend-cash holding should be skipped
        assert len(holding_rows) == len(snap.holdings)


def test_detail_file_has_div_cash_rows_only():
    """DIV_REINVESTED is suppressed from detail file; only DIV_CASH rows appear."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        write_snapshots([_make_snapshot()], out)
        detail = list(out.glob("detail_*.csv"))[0]
        rows = list(csv.DictReader(open(detail)))
        div_rows = [r for r in rows if "DIV" in r["record_type"]]
        assert len(div_rows) == 1  # only the DIV_CASH record (reinvested suppressed)
        assert div_rows[0]["record_type"] == "DIV_CASH"


def test_expense_file_has_correct_columns():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        write_snapshots([_make_snapshot()], out)
        exp = list(out.glob("expenses_*.csv"))[0]
        rows = list(csv.DictReader(open(exp)))
        assert rows[0]["year"] == "2026"
        assert "total_cash_needed" in rows[0]
        assert "net_withdrawal_needed" in rows[0]
        assert "total_income_available" in rows[0]


def test_expense_file_two_years():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        write_snapshots([_make_snapshot(2026), _make_snapshot(2027)], out)
        exp = list(out.glob("expenses_*.csv"))[0]
        rows = list(csv.DictReader(open(exp)))
        assert len(rows) == 2


def test_transactions_file_has_tx():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        write_snapshots([_make_snapshot()], out)
        txf = list(out.glob("transactions_*.csv"))[0]
        rows = list(csv.DictReader(open(txf)))
        assert len(rows) == 1
        assert rows[0]["transaction_type"] == "LT_HARVEST"
        assert rows[0]["gain_loss"] == "1500.00"


def test_snapshot_total_expenses():
    snap = _make_snapshot()
    assert abs(snap.total_expenses - (100_000 + 5_000 + 0)) < 0.01


def test_snapshot_total_portfolio_value():
    snap = _make_snapshot()
    assert abs(snap.total_portfolio_value - 100 * 200) < 0.01


def test_snapshot_medical_premium_sum():
    snap = _make_snapshot()
    snap2 = YearEndSnapshot(
        **{**snap.__dict__, "ani_medical_premium": 3_000.0, "nup_medical_premium": 2_000.0}
    )
    assert snap2.medical_premium == 5_000.0


def test_fmt_rounds_to_two_decimals():
    assert _fmt(1234.5678) == "1234.57"


def test_fmt_zero():
    assert _fmt(0.0) == "0.00"


def test_write_creates_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "new_subdir"
        write_snapshots([_make_snapshot()], out)
        assert out.exists()
