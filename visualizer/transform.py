from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class MapGrids:
    X: np.ndarray
    Y: np.ndarray
    Z: np.ndarray
    meta: dict[str, Any]


def load_and_parse_map(filepath: str, smoothing_sigma: float | None = None) -> MapGrids:  # noqa: ARG001 - placeholder impl
    """Placeholder signature: load CSV, coerce, pivot, interpolate, smooth.

    To be implemented in Milestone 3. For MVP and earlier milestones, plotting
    occurs directly in the app after a simple pivot.
    """
    raise NotImplementedError("Implemented in Milestone 3")


