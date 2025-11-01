from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 - required for 3D projection


class MapVisualizerApp(tk.Tk):
    """Minimal MVP Tkinter app embedding a matplotlib 3D surface plot.

    Features in MVP:
    - Load a stock CSV named "stock_map.csv" from the working directory
    - Pivot to a 2D grid and plot a single 3D surface with a colorbar
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("Ignition Timing Map 3D Visualizer - MVP")
        self.geometry("1000x700")

        # UI: top frame with buttons
        controls = ttk.Frame(self)
        controls.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

        self.load_button = ttk.Button(controls, text="Load Stock Map", command=self.on_load_clicked)
        self.load_button.pack(side=tk.LEFT)

        ttk.Label(controls, text="Colormap:").pack(side=tk.LEFT, padx=(12, 4))
        self.cmap_var = tk.StringVar(value="viridis")
        self.cmap_combo = ttk.Combobox(controls, textvariable=self.cmap_var, values=["viridis", "plasma", "coolwarm"], state="readonly", width=10)
        self.cmap_combo.pack(side=tk.LEFT)
        self.cmap_combo.bind("<<ComboboxSelected>>", lambda _: self.refresh_colormap_alpha())

        ttk.Label(controls, text="Alpha:").pack(side=tk.LEFT, padx=(12, 4))
        self.alpha_var = tk.DoubleVar(value=1.0)
        self.alpha_scale = ttk.Scale(controls, from_=0.1, to=1.0, orient=tk.HORIZONTAL, variable=self.alpha_var, command=lambda _=None: self.refresh_colormap_alpha())
        self.alpha_scale.pack(side=tk.LEFT, fill=tk.X, expand=False)

        # Figure/Canvas area
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.figure.add_subplot(111, projection="3d")
        self.ax.set_xlabel("RPM")
        self.ax.set_ylabel("Load")
        self.ax.set_zlabel("Timing")

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._mappable = None  # track last surface for colorbar
        self._colorbar = None
        self._last_X = None
        self._last_Y = None
        self._last_Z = None

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status = ttk.Label(self, textvariable=self.status_var, anchor="w")
        self.status.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=4)

        # Disable cmap/alpha until data is loaded
        self._set_controls_enabled(False)

    def on_load_clicked(self) -> None:
        """Load a stock CSV, pivot to grid, and render a 3D surface.

        Search order:
        1) CWD: `stock_map.csv`
        2) Repo root `scripts/stock_map.csv` (based on this file location)
        """
        candidates = [
            Path("stock_map.csv"),
            Path(__file__).resolve().parents[1] / "scripts" / "stock_map.csv",
        ]

        loaded_path: Path | None = None
        last_exc: Exception | None = None
        for path in candidates:
            try:
                df = pd.read_csv(path)
                loaded_path = path
                break
            except Exception as exc:  # keep trying fallbacks
                last_exc = exc
                continue

        if loaded_path is None:
            attempted = "\n".join(str(p) for p in candidates)
            messagebox.showerror(
                "Load Error",
                f"Failed to read a CSV from any of the expected locations.\n\n"
                f"Tried:\n{attempted}\n\nLast error: {last_exc}",
            )
            return

        required_cols = {"RPM", "Load", "Timing"}
        if not required_cols.issubset(df.columns):
            messagebox.showerror("Format Error", "CSV must contain columns: RPM, Load, Timing")
            return

        try:
            pivot = df.pivot(index="Load", columns="RPM", values="Timing")
            X, Y = np.meshgrid(pivot.columns.values, pivot.index.values)
            Z = pivot.values
        except Exception as exc:
            messagebox.showerror("Transform Error", f"Pivot/meshgrid failed: {exc}")
            return

        # Plot surface
        self.ax.clear()
        self.ax.set_xlabel("RPM")
        self.ax.set_ylabel("Load")
        self.ax.set_zlabel("Timing")
        cmap = self.cmap_var.get()
        alpha = float(self.alpha_var.get())
        surf = self.ax.plot_surface(X, Y, Z, cmap=cmap, alpha=alpha)

        # Update colorbar
        if self._colorbar is not None:
            try:
                self._colorbar.remove()
            except Exception:
                pass
            self._colorbar = None
        self._mappable = surf
        self._colorbar = self.figure.colorbar(self._mappable, ax=self.ax, shrink=0.7, pad=0.1)

        self._last_X, self._last_Y, self._last_Z = X, Y, Z
        self.status_var.set(
            f"Loaded: {loaded_path} — min: {np.nanmin(Z):.3f}, max: {np.nanmax(Z):.3f}"
        )
        self._set_controls_enabled(True)
        self.canvas.draw_idle()

    def refresh_colormap_alpha(self) -> None:
        if self._last_Z is None:
            return
        # Re-render with new cmap/alpha
        X, Y, Z = self._last_X, self._last_Y, self._last_Z
        self.ax.clear()
        self.ax.set_xlabel("RPM")
        self.ax.set_ylabel("Load")
        self.ax.set_zlabel("Timing")
        cmap = self.cmap_var.get()
        alpha = float(self.alpha_var.get())
        surf = self.ax.plot_surface(X, Y, Z, cmap=cmap, alpha=alpha)
        if self._colorbar is not None:
            try:
                self._colorbar.remove()
            except Exception:
                pass
            self._colorbar = None
        self._mappable = surf
        self._colorbar = self.figure.colorbar(self._mappable, ax=self.ax, shrink=0.7, pad=0.1)
        self.canvas.draw_idle()

    def _set_controls_enabled(self, enabled: bool) -> None:
        state = "readonly" if enabled else "disabled"
        scale_state = tk.NORMAL if enabled else tk.DISABLED
        self.cmap_combo.configure(state=state)
        self.alpha_scale.configure(state=scale_state)


def main() -> None:
    app = MapVisualizerApp()
    app.mainloop()


if __name__ == "__main__":
    main()


