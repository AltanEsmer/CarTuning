from __future__ import annotations

from pathlib import Path

import pandas as pd


def main() -> None:
    rpm_axis = list(range(1000, 7000, 1000))  # 1000..6000
    load_axis = [20, 40, 60, 80, 100]

    rows = []
    for load in load_axis:
        for rpm in rpm_axis:
            timing = (rpm / 1000.0) + (load / 10.0)
            rows.append({"RPM": rpm, "Load": load, "Timing": timing})

    df = pd.DataFrame(rows, columns=["RPM", "Load", "Timing"])
    out_path = Path("stock_map.csv").resolve()
    df.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()


