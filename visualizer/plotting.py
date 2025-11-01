from __future__ import annotations

from typing import Optional

import numpy as np
from matplotlib.axes import Axes


def clear_axes(ax: Axes) -> None:
    ax.clear()


def draw_surface(ax: Axes, X: np.ndarray, Y: np.ndarray, Z: np.ndarray, *, cmap: str = "viridis", alpha: float = 1.0):
    """Draw a 3D surface on an Axes that has projection='3d'."""
    surf = ax.plot_surface(X, Y, Z, cmap=cmap, alpha=alpha)
    return surf


