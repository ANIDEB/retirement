from __future__ import annotations
import csv
from pathlib import Path
import streamlit as st

OUTPUT_DIR = Path("data/output")


def _latest_summary() -> Path | None:
    files = sorted(OUTPUT_DIR.glob("summary_*.csv"), reverse=True)
    return files[0] if files else None


def _load_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    with open(path, newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)
    return headers, rows


def _to_float(v: str) -> float:
    try:
        return float(v)
    except ValueError:
        return 0.0


st.set_page_config(page_title="Retirement Projection", layout="wide")
st.title("Retirement Financial Projection")

summary_path = _latest_summary()
if summary_path is None:
    st.warning("No projection data found. Run `python main.py` first.")
    st.stop()

headers, rows = _load_csv(summary_path)
col_idx = {name: i for i, name in enumerate(headers)}

years = [int(r[col_idx["year"]]) for r in rows]
portfolio = [_to_float(r[col_idx["total_portfolio_value"]]) for r in rows]
withdrawals = [_to_float(r[col_idx["withdrawals"]]) for r in rows]
total_tax = [_to_float(r[col_idx["total_tax"]]) for r in rows]
expenses = [_to_float(r[col_idx["expenses"]]) for r in rows]
roth_conv = [_to_float(r[col_idx["roth_converted"]]) for r in rows]
lt_gains = [_to_float(r[col_idx["lt_gains_harvested"]]) for r in rows]

col1, col2, col3 = st.columns(3)
col1.metric("Starting Portfolio", f"${portfolio[0]:,.0f}")
col2.metric("Portfolio in 30 Years", f"${portfolio[-1]:,.0f}")
col3.metric("First Year Withdrawal", f"${withdrawals[0]:,.0f}")

st.subheader("Portfolio Value Over Time")
st.line_chart({"Portfolio Value ($)": dict(zip(years, portfolio))})

st.subheader("Annual Cash Flows")
st.bar_chart({
    "Withdrawals ($)": dict(zip(years, withdrawals)),
    "Total Tax ($)": dict(zip(years, total_tax)),
    "Expenses ($)": dict(zip(years, expenses)),
})

st.subheader("Tax Strategy")
st.bar_chart({
    "Roth Conversion ($)": dict(zip(years, roth_conv)),
    "LT Gains Harvested ($)": dict(zip(years, lt_gains)),
})

st.subheader("Year-by-Year Summary")
st.dataframe(
    [dict(zip(headers, row)) for row in rows],
    use_container_width=True,
)
