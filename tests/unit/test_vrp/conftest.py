"""Shared fixtures for VRP tests."""
import pandas as pd
import pytest
import sys
from pathlib import Path



@pytest.fixture
def customers_30():
    csv_path = Path(__file__).parents[3] / "data" / "customers_geo.csv"
    if not csv_path.exists():
        pytest.fail(
            "data/customers_geo.csv not found. "
            "Run Task 08 (generate customers_geo.csv) first."
        )
    return pd.read_csv(csv_path).to_dict("records")
