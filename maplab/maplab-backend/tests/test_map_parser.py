"""
Unit tests for map_parser module.
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.services.map_parser import MapParseError, load_and_parse_map


class TestNormalParsing:
    """Test normal CSV parsing scenarios."""

    def test_parse_valid_csv(self, temp_dir):
        """Test parsing a valid CSV file."""
        # Create a simple valid CSV
        data = {
            "RPM": [1000, 2000, 3000, 1000, 2000, 3000],
            "Load": [20, 20, 20, 40, 40, 40],
            "Timing": [3.0, 4.0, 5.0, 5.0, 6.0, 7.0],
        }
        df = pd.DataFrame(data)
        csv_path = temp_dir / "test.csv"
        df.to_csv(csv_path, index=False)

        # Parse
        X_grid, Y_grid, Z_grid = load_and_parse_map(csv_path)

        # Verify shapes match
        assert X_grid.shape == Y_grid.shape == Z_grid.shape

        # Verify no NaNs
        assert not np.isnan(Z_grid).any()

        # Verify RPM axis is sorted
        rpm_axis = X_grid[0, :]
        assert np.all(rpm_axis[:-1] <= rpm_axis[1:])

        # Verify Load axis is sorted
        load_axis = Y_grid[:, 0]
        assert np.all(load_axis[:-1] <= load_axis[1:])


class TestDuplicateHandling:
    """Test handling of duplicate (RPM, Load) pairs."""

    def test_duplicate_rows_averaged(self, temp_dir):
        """Test that duplicate rows are averaged."""
        # Create CSV with duplicates
        data = {
            "RPM": [1000, 1000, 1000, 2000, 2000],
            "Load": [20, 20, 20, 30, 30],
            "Timing": [3.0, 5.0, 7.0, 4.0, 6.0],  # Duplicates should average
        }
        df = pd.DataFrame(data)
        csv_path = temp_dir / "test_dup.csv"
        df.to_csv(csv_path, index=False)

        # Parse
        X_grid, Y_grid, Z_grid = load_and_parse_map(csv_path)

        # Find the value at (RPM=1000, Load=20)
        # Average of [3.0, 5.0, 7.0] = 5.0
        rpm_axis = X_grid[0, :]
        load_axis = Y_grid[:, 0]

        if 1000 in rpm_axis and 20 in load_axis:
            rpm_idx = np.where(rpm_axis == 1000)[0][0]
            load_idx = np.where(load_axis == 20)[0][0]
            timing_value = Z_grid[load_idx, rpm_idx]
            # Should be approximately 5.0 (average of 3, 5, 7)
            assert abs(timing_value - 5.0) < 0.01


class TestNaNHandling:
    """Test handling of NaN values in CSV."""

    def test_csv_with_nans_gets_filled(self, temp_dir):
        """Test that NaNs in CSV are filled via interpolation."""
        # Create CSV with some NaN values
        data = {
            "RPM": [1000, 2000, 3000, 4000, 1000, 2000, 3000, 4000],
            "Load": [20, 20, 20, 20, 40, 40, 40, 40],
            "Timing": [3.0, 4.0, np.nan, 6.0, 5.0, np.nan, 7.0, 8.0],
        }
        df = pd.DataFrame(data)
        csv_path = temp_dir / "test_nan.csv"
        df.to_csv(csv_path, index=False)

        # Parse - should not raise and should fill NaNs
        X_grid, Y_grid, Z_grid = load_and_parse_map(csv_path)

        # Verify no NaNs in final output
        assert not np.isnan(Z_grid).any()

        # Verify shapes are consistent
        assert X_grid.shape == Y_grid.shape == Z_grid.shape

    def test_sparse_data_interpolation(self, temp_dir):
        """Test interpolation with sparse data."""
        # Create CSV with few points that need interpolation
        data = {
            "RPM": [1000, 3000, 5000, 1000, 3000, 5000],
            "Load": [20, 20, 20, 60, 60, 60],
            "Timing": [3.0, 5.0, 7.0, 7.0, 9.0, 11.0],
        }
        df = pd.DataFrame(data)
        csv_path = temp_dir / "test_sparse.csv"
        df.to_csv(csv_path, index=False)

        # Parse should succeed
        X_grid, Y_grid, Z_grid = load_and_parse_map(csv_path)

        # Should have no NaNs
        assert not np.isnan(Z_grid).any()


class TestMalformedCSV:
    """Test handling of malformed CSV files."""

    def test_missing_file_raises_error(self):
        """Test that missing file raises MapParseError."""
        with pytest.raises(MapParseError, match="File not found"):
            load_and_parse_map("nonexistent_file.csv")

    def test_empty_file_raises_error(self, temp_dir):
        """Test that empty file raises MapParseError."""
        csv_path = temp_dir / "empty.csv"
        csv_path.touch()  # Create empty file

        with pytest.raises(MapParseError):
            load_and_parse_map(csv_path)

    def test_missing_columns_raises_error(self, temp_dir):
        """Test that missing required columns raises error."""
        # Create CSV with wrong columns
        data = {"X": [1, 2, 3], "Y": [4, 5, 6], "Z": [7, 8, 9]}
        df = pd.DataFrame(data)
        csv_path = temp_dir / "wrong_cols.csv"
        df.to_csv(csv_path, index=False)

        with pytest.raises(MapParseError, match="Missing required columns"):
            load_and_parse_map(csv_path)

    def test_all_non_numeric_raises_error(self, temp_dir):
        """Test that CSV with all non-numeric values raises error."""
        data = {
            "RPM": ["abc", "def", "ghi"],
            "Load": ["xyz", "uvw", "rst"],
            "Timing": ["one", "two", "three"],
        }
        df = pd.DataFrame(data)
        csv_path = temp_dir / "non_numeric.csv"
        df.to_csv(csv_path, index=False)

        with pytest.raises(MapParseError, match="No valid numeric data"):
            load_and_parse_map(csv_path)

    def test_malformed_csv_structure_raises_error(self, temp_dir):
        """Test that malformed CSV structure raises error."""
        csv_path = temp_dir / "malformed.csv"
        # Write invalid CSV content
        csv_path.write_text("RPM,Load,Timing\n1000,20\n2000")  # Incomplete rows

        with pytest.raises(MapParseError):
            load_and_parse_map(csv_path)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_row_csv(self, temp_dir):
        """Test parsing CSV with single row."""
        data = {"RPM": [1000], "Load": [20], "Timing": [3.0]}
        df = pd.DataFrame(data)
        csv_path = temp_dir / "single_row.csv"
        df.to_csv(csv_path, index=False)

        # Should parse successfully (though grid will be 1x1)
        X_grid, Y_grid, Z_grid = load_and_parse_map(csv_path)

        assert X_grid.shape == (1, 1)
        assert Y_grid.shape == (1, 1)
        assert Z_grid.shape == (1, 1)
        assert Z_grid[0, 0] == 3.0

    def test_csv_with_extra_columns_ignored(self, temp_dir):
        """Test that extra columns are ignored (only RPM, Load, Timing used)."""
        data = {
            "RPM": [1000, 2000],
            "Load": [20, 40],
            "Timing": [3.0, 5.0],
            "Extra": ["a", "b"],  # Extra column
        }
        df = pd.DataFrame(data)
        csv_path = temp_dir / "extra_cols.csv"
        df.to_csv(csv_path, index=False)

        # Should parse successfully
        X_grid, Y_grid, Z_grid = load_and_parse_map(csv_path)

        assert not np.isnan(Z_grid).any()
        assert X_grid.shape == Y_grid.shape == Z_grid.shape

