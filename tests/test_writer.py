import csv
import tempfile
from pathlib import Path
from retirement.output.writer import write_snapshots, _fmt
from retirement.models.snapshot import YearEndSnapshot, DividendRecord
from retirement.tax.calculator import TaxResult
from tests.conftest import make_holding


def _make_snapshot(year=2026):
    return YearEndSnapshot(
        year=year,
        ani_age=60,
        nup_age=57,
        ani_retired=False,
        nup_retired=False,
        holdings=[make_holding(ticker="VFIAX", qty=100, price=200, cost_basis=5000)],
        dividend_records=[
            DividendRecord("ACC", "ANI", "ETrade", "BROKERAGE", "VFIAX",
                           amount=500.0, reinvested=True),
            DividendRecord("ACC2", "ANI", "ETrade", "BROKERAGE", "VFIAX",
                           amount=200.0, reinvested=False),
        ],
        expenses=100_000.0,
        medical_oop=5_000.0,
        medical_premium=0.0,
        taxable_dividend_income=700.0,
        lt_gains_harvested=0.0,
        roth_converted=0.0,
        withdrawals=0.0,
        tax_result=TaxResult(
            ordinary_income=700.0, lt_gain_income=0.0,
            federal_ordinary_tax=0.0, federal_lt_tax=0.0, az_tax=17.5, niit=0.0,
        ),
    )


def test_write_creates_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        write_snapshots([_make_snapshot()], out)
        assert len(list(out.glob("detail_*.csv"))) == 1
        assert len(list(out.glob("summary_*.csv"))) == 1


def test_detail_file_has_holding_rows():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        write_snapshots([_make_snapshot()], out)
        detail = list(out.glob("detail_*.csv"))[0]
        with open(detail) as f:
            rows = list(csv.DictReader(f))
        holding_rows = [r for r in rows if r["record_type"] == "HOLDING"]
        assert len(holding_rows) == 1


def test_detail_file_has_dividend_rows():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        write_snapshots([_make_snapshot()], out)
        detail = list(out.glob("detail_*.csv"))[0]
        with open(detail) as f:
            rows = list(csv.DictReader(f))
        div_rows = [r for r in rows if "DIV" in r["record_type"]]
        assert len(div_rows) == 2


def test_summary_file_has_year():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir)
        write_snapshots([_make_snapshot(2026), _make_snapshot(2027)], out)
        summary = list(out.glob("summary_*.csv"))[0]
        with open(summary) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert rows[0]["year"] == "2026"


def test_snapshot_total_expenses():
    snap = _make_snapshot()
    assert abs(snap.total_expenses - (100_000 + 5_000 + 0)) < 0.01


def test_snapshot_total_portfolio_value():
    snap = _make_snapshot()
    assert abs(snap.total_portfolio_value - 100 * 200) < 0.01


def test_fmt_rounds_to_two_decimals():
    assert _fmt(1234.5678) == "1234.57"


def test_fmt_zero():
    assert _fmt(0.0) == "0.00"


def test_write_creates_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "new_subdir"
        write_snapshots([_make_snapshot()], out)
        assert out.exists()
