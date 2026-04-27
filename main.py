from pathlib import Path
from retirement.loaders.asset_loader import load_holdings
from retirement.loaders.scenario_loader import load_scenario
from retirement.engine.projector import run_projection
from retirement.output.writer import write_snapshots

DATA_DIR = Path("data")
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

ASSET_FILE = INPUT_DIR / "current_asset.csv"
SCENARIO_FILE = INPUT_DIR / "default_scenario.json"


def main() -> None:
    holdings = load_holdings(ASSET_FILE)
    scenario = load_scenario(SCENARIO_FILE)
    snapshots = run_projection(holdings, scenario)
    write_snapshots(snapshots, OUTPUT_DIR)
    print(f"Projection complete — {len(snapshots)} years written to {OUTPUT_DIR}")


if __name__ == "__main__":  # pragma: no cover
    main()
