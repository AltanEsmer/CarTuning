"""
ECU Map Parser Service.

Loads and parses ECU map CSV files, converting them into grid format for analysis.
Handles deduplication, interpolation, and data cleaning.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import griddata


class MapParseError(Exception):
    """Raised when map parsing fails due to malformed or invalid data."""

    pass


def load_and_parse_map(filepath: str | Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load and parse an ECU map CSV file into grid format.

    Args:
        filepath: Path to CSV file with columns: RPM, Load, Timing

    Returns:
        Tuple of (X_grid, Y_grid, Z_grid) as numpy arrays where:
        - X_grid: RPM axis (columns)
        - Y_grid: Load axis (rows)
        - Z_grid: Timing values in grid form

    Raises:
        MapParseError: If the file cannot be parsed or is malformed
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise MapParseError(f"File not found: {filepath}")

    if filepath.stat().st_size == 0:
        raise MapParseError(f"File is empty: {filepath}")

    try:
        # Read CSV
        df = pd.read_csv(filepath)

        # Validate required columns
        required_cols = ["RPM", "Load", "Timing"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise MapParseError(
                f"Missing required columns: {missing_cols}. Found columns: {list(df.columns)}"
            )

        # Coerce to numeric, converting errors to NaN
        df["RPM"] = pd.to_numeric(df["RPM"], errors="coerce")
        df["Load"] = pd.to_numeric(df["Load"], errors="coerce")
        df["Timing"] = pd.to_numeric(df["Timing"], errors="coerce")

        # Check if we have any valid data after coercion
        valid_mask = df[["RPM", "Load", "Timing"]].notna().all(axis=1)
        if not valid_mask.any():
            raise MapParseError("No valid numeric data found in CSV after parsing")

        # Report rows with invalid data (optional, for debugging)
        invalid_count = (~valid_mask).sum()
        if invalid_count > 0:
            # Filter to only valid rows
            df = df[valid_mask].copy()

        # Deduplicate by averaging duplicate (RPM, Load) pairs
        df_grouped = df.groupby(["RPM", "Load"], as_index=False)["Timing"].mean()

        # Sort axes ascending
        df_grouped = df_grouped.sort_values(["Load", "RPM"])

        # Pivot to matrix format
        pivot_table = df_grouped.pivot_table(
            index="Load", columns="RPM", values="Timing", dropna=False
        )

        # Extract unique RPM and Load values (sorted)
        rpm_values = pivot_table.columns.values  # RPM values (X axis)
        load_values = pivot_table.index.values  # Load values (Y axis)

        # Create meshgrid for output
        X_grid, Y_grid = np.meshgrid(rpm_values, load_values)

        # Extract Z values (timing)
        Z_grid = pivot_table.values

        # Fill NaNs using interpolation
        if np.isnan(Z_grid).any():
            # Get valid points for interpolation
            valid_mask = ~np.isnan(Z_grid)
            valid_points = np.column_stack([X_grid[valid_mask], Y_grid[valid_mask]])
            valid_values = Z_grid[valid_mask]

            # Get all grid points (including NaN locations)
            all_points = np.column_stack([X_grid.ravel(), Y_grid.ravel()])

            if len(valid_points) >= 3:  # Need at least 3 points for interpolation
                # Use linear interpolation
                interpolated = griddata(
                    valid_points, valid_values, all_points, method="linear", fill_value=np.nan
                )

                # Fill in interpolated values
                nan_mask = np.isnan(Z_grid.ravel())
                interpolated_values = interpolated[nan_mask]

                # If some NaNs remain at edges, use nearest neighbor
                still_nan = np.isnan(interpolated_values)
                if still_nan.any():
                    nearest = griddata(
                        valid_points,
                        valid_values,
                        all_points[nan_mask][still_nan],
                        method="nearest",
                    )
                    interpolated_values[still_nan] = nearest

                Z_grid.ravel()[nan_mask] = interpolated_values
            else:
                # Not enough points for interpolation, raise error
                raise MapParseError(
                    f"Insufficient valid data points ({len(valid_points)}) for interpolation"
                )

        # Verify final grid has no NaNs
        if np.isnan(Z_grid).any():
            raise MapParseError("Unable to completely fill all NaN values in grid")

        return X_grid, Y_grid, Z_grid

    except pd.errors.EmptyDataError:
        raise MapParseError(f"CSV file is empty or has no data rows: {filepath}")
    except pd.errors.ParserError as e:
        raise MapParseError(f"CSV parsing error: {e}")
    except Exception as e:
        if isinstance(e, MapParseError):
            raise
        raise MapParseError(f"Unexpected error parsing map: {e}")

