import csv
import tempfile
from pathlib import Path
from retirement.loaders.asset_loader import load_holdings, _parse_dollar


def _write_csv(rows: list[dict]) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="")
    writer = csv.DictWriter(tmp, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    tmp.close()
    return Path(tmp.name)


def _row(**kwargs):
    defaults = {
        "Name": "ACC1", "OWNER": "ANI", "Counterparty": "ETrade",
        "Type": "BROKERAGE", "Ticker": "AAPL", "Qty": "10",
        "Rate": "150.00", " AMOUNT ": "$1,500.00", " Cost Basis ": "$500.00",
    }
    defaults.update(kwargs)
    return defaults


def test_load_basic_holding():
    path = _write_csv([_row()])
    holdings = load_holdings(path)
    assert len(holdings) == 1
    h = holdings[0]
    assert h.account_name == "ACC1"
    assert h.owner == "ANI"
    assert h.ticker == "AAPL"
    assert h.qty == 10.0
    assert h.price == 150.0
    assert h.cost_basis_total == 500.0


def test_skip_empty_name():
    path = _write_csv([_row(Name="")])
    assert load_holdings(path) == []


def test_skip_empty_ticker():
    path = _write_csv([_row(Ticker="")])
    assert load_holdings(path) == []


def test_skip_invalid_qty():
    path = _write_csv([_row(Qty="N/A")])
    assert load_holdings(path) == []


def test_parse_dollar_plain():
    assert _parse_dollar(" $1,234.56 ") == 1234.56


def test_parse_dollar_empty():
    assert _parse_dollar("") == 0.0


def test_parse_dollar_dash():
    assert _parse_dollar(" $-   ") == 0.0


def test_parse_dollar_no_symbol():
    assert _parse_dollar("573.9") == 573.9


def test_multiple_rows():
    path = _write_csv([_row(Name="A", Ticker="X"), _row(Name="B", Ticker="Y")])
    holdings = load_holdings(path)
    assert len(holdings) == 2
    assert holdings[0].account_name == "A"
    assert holdings[1].account_name == "B"
