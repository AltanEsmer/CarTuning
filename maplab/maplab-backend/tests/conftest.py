"""
Pytest configuration and fixtures.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_csv_path(temp_dir):
    """Create a sample valid CSV file for testing."""
    data = {
        "RPM": [1000, 2000, 1000, 2000],
        "Load": [20, 20, 40, 40],
        "Timing": [3.0, 4.0, 5.0, 6.0],
    }
    df = pd.DataFrame(data)
    csv_path = temp_dir / "sample.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

