from __future__ import annotations
import csv
from pathlib import Path
from datetime import date
from retirement.models.snapshot import YearEndSnapshot


def _fmt(v: float) -> str:
    return f"{v:.2f}"


# ── Detail file (holdings + dividend records per year) ───────────────────────

_DETAIL_COLS = [
    "year", "record_type", "account_name", "owner", "counterparty",
    "account_type", "ticker", "qty", "price", "amount",
    "cost_basis", "unrealized_gain",
]


def _write_detail(snapshots: list[YearEndSnapshot], path: Path) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(_DETAIL_COLS)
        for snap in snapshots:
            for h in snap.holdings:
                if h.is_new_dividend_cash:
                    continue  # shown only as DIV_CASH record, not a duplicate HOLDING
                w.writerow([
                    snap.year, "HOLDING", h.account_name, h.owner, h.counterparty,
                    h.account_type, h.ticker,
                    _fmt(h.qty), _fmt(h.price), _fmt(h.amount),
                    _fmt(h.cost_basis_total), _fmt(h.unrealized_gain),
                ])
            for dr in snap.dividend_records:
                label = "DIV_REINVESTED" if dr.reinvested else "DIV_CASH"
                w.writerow([
                    snap.year, label, dr.account_name, dr.owner, dr.counterparty,
                    dr.account_type, dr.ticker,
                    _fmt(dr.amount), "1.00", _fmt(dr.amount), _fmt(dr.amount), "0.00",
                ])


# ── Expense detail file (one row per year) ───────────────────────────────────

_EXPENSE_COLS = [
    "year", "ani_age", "nup_age", "ani_retired", "nup_retired",
    # Expense components
    "expenses", "medical_oop", "ani_medical_premium", "nup_medical_premium",
    "total_medical_premium", "total_expenses",
    # Income available before withdrawals
    "nup_salary", "taxable_dividends", "lt_gains_harvested", "total_income_available",
    # Tax breakdown
    "federal_ordinary_tax", "federal_lt_tax", "az_tax", "niit", "total_tax",
    # Cash flow summary
    "total_cash_needed",     # total_expenses + total_tax
    "income_covers",         # min(income_available, total_cash_needed)
    "hsa_covers",            # medical costs covered by HSA
    "net_withdrawal_needed", # what must come from non-HSA portfolio
    "actual_withdrawal",     # what was actually withdrawn
    # Portfolio
    "roth_converted", "total_portfolio_value",
]


def _write_expense_detail(snapshots: list[YearEndSnapshot], path: Path) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(_EXPENSE_COLS)
        for snap in snapshots:
            t = snap.tax_result
            income_avail = snap.nup_salary + snap.taxable_dividend_income + snap.lt_gains_harvested
            total_cash_needed = snap.total_expenses + t.total_tax
            income_covers = min(income_avail, total_cash_needed)
            net_wd_needed = max(0.0, total_cash_needed - income_covers - snap.hsa_used)
            w.writerow([
                snap.year, snap.ani_age, snap.nup_age, snap.ani_retired, snap.nup_retired,
                _fmt(snap.expenses), _fmt(snap.medical_oop),
                _fmt(snap.ani_medical_premium), _fmt(snap.nup_medical_premium),
                _fmt(snap.medical_premium), _fmt(snap.total_expenses),
                _fmt(snap.nup_salary), _fmt(snap.taxable_dividend_income),
                _fmt(snap.lt_gains_harvested), _fmt(income_avail),
                _fmt(t.federal_ordinary_tax), _fmt(t.federal_lt_tax),
                _fmt(t.az_tax), _fmt(t.niit), _fmt(t.total_tax),
                _fmt(total_cash_needed), _fmt(income_covers),
                _fmt(snap.hsa_used), _fmt(net_wd_needed), _fmt(snap.withdrawals),
                _fmt(snap.roth_converted), _fmt(snap.total_portfolio_value),
            ])


# ── Transactions file ─────────────────────────────────────────────────────────

_TX_COLS = [
    "year", "transaction_type", "account_name", "owner", "account_type",
    "ticker", "shares", "price", "amount", "cost_basis", "gain_loss", "note",
]


def _write_transactions(snapshots: list[YearEndSnapshot], path: Path) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(_TX_COLS)
        for snap in snapshots:
            for tx in snap.transactions:
                w.writerow([
                    tx.year, tx.transaction_type, tx.account_name, tx.owner, tx.account_type,
                    tx.ticker, _fmt(tx.shares), _fmt(tx.price), _fmt(tx.amount),
                    _fmt(tx.cost_basis), _fmt(tx.gain_loss), tx.note,
                ])


# ── Public entry point ────────────────────────────────────────────────────────

def write_snapshots(snapshots: list[YearEndSnapshot], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_tag = date.today().isoformat()

    _write_detail(snapshots, output_dir / f"detail_{run_tag}.csv")
    _write_expense_detail(snapshots, output_dir / f"expenses_{run_tag}.csv")
    _write_transactions(snapshots, output_dir / f"transactions_{run_tag}.csv")
