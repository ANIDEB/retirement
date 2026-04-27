from __future__ import annotations
import csv
from pathlib import Path
from datetime import date
from retirement.models.snapshot import YearEndSnapshot


_DETAIL_COLS = [
    "year", "record_type", "account_name", "owner", "counterparty",
    "account_type", "ticker", "qty", "price", "amount",
    "cost_basis", "unrealized_gain",
]

_SUMMARY_COLS = [
    "year", "ani_age", "nup_age", "ani_retired", "nup_retired",
    "total_portfolio_value", "expenses", "medical_oop", "medical_premium",
    "taxable_dividend_income", "lt_gains_harvested", "roth_converted",
    "withdrawals", "federal_ordinary_tax", "federal_lt_tax",
    "az_tax", "niit", "total_tax",
]


def _fmt(v: float) -> str:
    return f"{v:.2f}"


def write_snapshots(snapshots: list[YearEndSnapshot], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_tag = date.today().isoformat()

    detail_path = output_dir / f"detail_{run_tag}.csv"
    summary_path = output_dir / f"summary_{run_tag}.csv"

    with open(detail_path, "w", newline="") as df, open(summary_path, "w", newline="") as sf:
        detail_writer = csv.writer(df)
        summary_writer = csv.writer(sf)
        detail_writer.writerow(_DETAIL_COLS)
        summary_writer.writerow(_SUMMARY_COLS)

        for snap in snapshots:
            for h in snap.holdings:
                detail_writer.writerow([
                    snap.year, "HOLDING", h.account_name, h.owner, h.counterparty,
                    h.account_type, h.ticker,
                    _fmt(h.qty), _fmt(h.price), _fmt(h.amount),
                    _fmt(h.cost_basis_total), _fmt(h.unrealized_gain),
                ])

            for dr in snap.dividend_records:
                label = "DIV_REINVESTED" if dr.reinvested else "DIV_CASH"
                detail_writer.writerow([
                    snap.year, label, dr.account_name, dr.owner, dr.counterparty,
                    dr.account_type, dr.ticker,
                    _fmt(dr.amount), "1.00", _fmt(dr.amount),
                    _fmt(dr.amount), "0.00",
                ])

            t = snap.tax_result
            summary_writer.writerow([
                snap.year, snap.ani_age, snap.nup_age,
                snap.ani_retired, snap.nup_retired,
                _fmt(snap.total_portfolio_value),
                _fmt(snap.expenses), _fmt(snap.medical_oop), _fmt(snap.medical_premium),
                _fmt(snap.taxable_dividend_income), _fmt(snap.lt_gains_harvested),
                _fmt(snap.roth_converted), _fmt(snap.withdrawals),
                _fmt(t.federal_ordinary_tax), _fmt(t.federal_lt_tax),
                _fmt(t.az_tax), _fmt(t.niit), _fmt(t.total_tax),
            ])
