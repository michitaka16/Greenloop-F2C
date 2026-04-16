"""Data loader module — loads CSV seed files into pandas DataFrames with validation."""

from pathlib import Path

import pandas as pd

from greenloop.utils.config import DATA_DIR


def _validate_columns(df: pd.DataFrame, expected: list[str], file_name: str) -> None:
    """Validate that DataFrame has expected columns."""
    missing = set(expected) - set(df.columns)
    if missing:
        raise ValueError(f"{file_name} missing columns: {missing}")


def load_crops(data_dir: Path | None = None) -> pd.DataFrame:
    """Load crops.csv with schema validation."""
    path = (data_dir or DATA_DIR) / "crops.csv"
    df = pd.read_csv(path)
    _validate_columns(
        df,
        ["crop_id", "name", "growth_days", "optimal_temp", "water_per_tray",
         "led_hours_per_day", "price_sgd_per_kg", "spoilage_rate"],
        "crops.csv",
    )
    return df


def load_shipments(data_dir: Path | None = None) -> pd.DataFrame:
    """Load shipments.csv with schema validation and date parsing."""
    path = (data_dir or DATA_DIR) / "shipments.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    _validate_columns(
        df,
        ["date", "crop_id", "kg_shipped", "price_sgd_per_kg"],
        "shipments.csv",
    )
    return df


def load_electricity(data_dir: Path | None = None) -> pd.DataFrame:
    """Load electricity.csv with schema validation."""
    path = (data_dir or DATA_DIR) / "electricity.csv"
    df = pd.read_csv(path, parse_dates=["date"])
    _validate_columns(
        df,
        ["date", "hour", "tariff_rate_sgd_per_kwh"],
        "electricity.csv",
    )
    return df


def load_staff(data_dir: Path | None = None) -> pd.DataFrame:
    """Load staff.csv with schema validation."""
    path = (data_dir or DATA_DIR) / "staff.csv"
    df = pd.read_csv(path)
    _validate_columns(
        df,
        ["staff_id", "name", "availability", "hourly_rate_sgd"],
        "staff.csv",
    )
    return df


def load_sensors(data_dir: Path | None = None) -> pd.DataFrame:
    """Load sensors_sim.csv with schema validation."""
    path = (data_dir or DATA_DIR) / "sensors_sim.csv"
    df = pd.read_csv(path, parse_dates=["timestamp"])
    _validate_columns(
        df,
        ["timestamp", "temp_c", "humidity_pct", "co2_ppm",
         "moisture_zone1", "moisture_zone2", "moisture_zone3", "moisture_zone4"],
        "sensors_sim.csv",
    )
    return df
