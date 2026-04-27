from retirement.engine.projector import run_projection
from tests.conftest import make_holding, make_scenario


def _portfolio():
    return [
        make_holding(account_name="ANI_VAN", account_type="BROKERAGE",
                     ticker="VFIAX", qty=1000, price=100, cost_basis=50_000),
        make_holding(account_name="ANI_FID", account_type="TAX_DEFRD",
                     ticker="VFIAX", qty=500, price=100, cost_basis=0),
        make_holding(account_name="ANI_ROTH", account_type="ROTH",
                     ticker="QQQ", qty=200, price=100, cost_basis=0),
        make_holding(account_name="ANI_BOA", account_type="SAVINGS",
                     ticker="CASH", qty=50_000, price=1.0, cost_basis=50_000),
        make_holding(account_name="HEALTH_EQTY", account_type="HSA",
                     ticker="CASH", qty=30_000, price=1.0, cost_basis=30_000),
    ]


def test_returns_correct_number_of_snapshots():
    s = make_scenario(projection_years=5)
    snaps = run_projection(_portfolio(), s)
    assert len(snaps) == 5


def test_portfolio_grows_pre_retirement():
    s = make_scenario(ani_retirement_year=2030, projection_years=3)
    snaps = run_projection(_portfolio(), s)
    assert snaps[2].total_portfolio_value > snaps[0].total_portfolio_value


def test_no_withdrawals_pre_retirement():
    s = make_scenario(ani_retirement_year=2030, projection_years=2)
    snaps = run_projection(_portfolio(), s)
    for snap in snaps:
        assert snap.withdrawals == 0.0
        assert snap.lt_gains_harvested == 0.0
        assert snap.roth_converted == 0.0


def test_withdrawals_start_after_ani_retires():
    s = make_scenario(ani_retirement_year=2027, projection_years=5)
    snaps = run_projection(_portfolio(), s)
    pre = [sn for sn in snaps if not sn.ani_retired]
    post = [sn for sn in snaps if sn.ani_retired]
    assert all(sn.withdrawals == 0.0 for sn in pre)
    assert any(sn.withdrawals > 0 or sn.lt_gains_harvested > 0 for sn in post)


def test_ani_age_increments():
    s = make_scenario(projection_years=3)
    snaps = run_projection(_portfolio(), s)
    assert snaps[1].ani_age == snaps[0].ani_age + 1


def test_retirement_flags_correct():
    s = make_scenario(ani_retirement_year=2027, nup_retirement_year=2029, projection_years=5)
    snaps = run_projection(_portfolio(), s)
    snap_2028 = snaps[2]  # year 2028
    assert snap_2028.ani_retired is True
    assert snap_2028.nup_retired is False


def test_snapshot_has_dividend_records():
    s = make_scenario(projection_years=2)
    snaps = run_projection(_portfolio(), s)
    assert len(snaps[0].dividend_records) > 0


def test_snapshot_has_transactions_after_retirement():
    s = make_scenario(ani_retirement_year=2027, projection_years=5)
    snaps = run_projection(_portfolio(), s)
    post = [sn for sn in snaps if sn.ani_retired]
    assert any(len(sn.transactions) > 0 for sn in post)


def test_snapshot_nup_salary_when_ani_retired_nup_not():
    s = make_scenario(ani_retirement_year=2027, nup_retirement_year=2030, projection_years=5)
    snaps = run_projection(_portfolio(), s)
    snap_2028 = snaps[2]
    assert snap_2028.ani_retired and not snap_2028.nup_retired
    assert snap_2028.nup_salary == 50_000
