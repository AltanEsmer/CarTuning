from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd


def read_csv_map(path: str | Path) -> pd.DataFrame:
    """Read a CSV map into a tidy DataFrame with columns: RPM, Load, Timing.

    The function defers validation to callers; MVP only ensures the file is
    readable and returns a DataFrame.
    """
    return pd.read_csv(path)


def write_csv_map(path: str | Path, rows: Iterable[Mapping[str, float]]) -> None:
    """Write a tidy CSV from rows of {RPM, Load, Timing}."""
    df = pd.DataFrame(list(rows), columns=["RPM", "Load", "Timing"])
    df.to_csv(path, index=False)


def save_plot_png(fig, path: str | Path, dpi: int = 150) -> None:
    """Save a matplotlib figure to PNG."""
    fig.savefig(path, dpi=dpi, bbox_inches="tight")


def save_json_metadata(path: str | Path, data: Mapping) -> None:
    """Save a small JSON metadata file."""
    import json

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


