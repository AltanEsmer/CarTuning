"""
Mock data generator for ECU map testing.

Generates sample stock_map.csv and tuned_map.csv files with RPM, Load, and Timing values.
Formula: Timing = (RPM / 1000) + (Load / 10)
Tuned map adds +1 to timing values for variation.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def main() -> None:
    """Generate mock stock and tuned map CSV files."""
    # Define axes
    rpm_axis = list(range(1000, 7000, 1000))  # 1000, 2000, ..., 6000
    load_axis = [20, 40, 60, 80, 100]

    # Base output directory
    base_dir = Path(__file__).parent.parent
    sample_data_dir = base_dir / "sample_data"
    sample_data_dir.mkdir(exist_ok=True)

    # Generate stock map data
    stock_rows = []
    for load in load_axis:
        for rpm in rpm_axis:
            timing = (rpm / 1000.0) + (load / 10.0)
            stock_rows.append({"RPM": rpm, "Load": load, "Timing": timing})

    df_stock = pd.DataFrame(stock_rows, columns=["RPM", "Load", "Timing"])
    stock_path = sample_data_dir / "stock_map.csv"
    df_stock.to_csv(stock_path, index=False)
    print(f"Wrote stock map to {stock_path}")

    # Generate tuned map data (add +1 to timing)
    tuned_rows = []
    for load in load_axis:
        for rpm in rpm_axis:
            timing = (rpm / 1000.0) + (load / 10.0) + 1.0
            tuned_rows.append({"RPM": rpm, "Load": load, "Timing": timing})

    df_tuned = pd.DataFrame(tuned_rows, columns=["RPM", "Load", "Timing"])
    tuned_path = sample_data_dir / "tuned_map.csv"
    df_tuned.to_csv(tuned_path, index=False)
    print(f"Wrote tuned map to {tuned_path}")


if __name__ == "__main__":
    main()

