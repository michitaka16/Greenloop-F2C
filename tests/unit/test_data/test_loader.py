"""Tests for data loader module."""

import pytest
import pandas as pd

from greenloop.data.loader import (
    load_crops,
    load_electricity,
    load_sensors,
    load_shipments,
    load_staff,
)
from greenloop.utils.config import DATA_DIR


class TestLoadCrops:
    def test_returns_dataframe(self):
        df = load_crops()
        assert isinstance(df, pd.DataFrame)

    def test_has_5_crops(self):
        df = load_crops()
        assert len(df) == 5

    def test_has_required_columns(self):
        df = load_crops()
        required = ["crop_id", "name", "growth_days", "optimal_temp",
                     "water_per_tray", "led_hours_per_day", "price_sgd_per_kg", "spoilage_rate"]
        for col in required:
            assert col in df.columns

    def test_crop_ids_match_expected(self):
        df = load_crops()
        expected = {"kai_lan", "baby_spinach", "lettuce_mambo", "chye_sim", "arugula"}
        assert set(df["crop_id"]) == expected


class TestLoadShipments:
    def test_returns_dataframe(self):
        df = load_shipments()
        assert isinstance(df, pd.DataFrame)

    def test_has_at_least_840_rows(self):
        df = load_shipments()
        assert len(df) >= 840  # 24 weeks * 5 crops * 7 days

    def test_date_column_is_datetime(self):
        df = load_shipments()
        assert pd.api.types.is_datetime64_any_dtype(df["date"])

    def test_no_negative_shipments(self):
        df = load_shipments()
        assert (df["kg_shipped"] >= 0).all()


class TestLoadElectricity:
    def test_returns_dataframe(self):
        df = load_electricity()
        assert isinstance(df, pd.DataFrame)

    def test_has_correct_row_count(self):
        df = load_electricity()
        assert len(df) == 4032  # 24 weeks * 7 days * 24 hours

    def test_tariff_values_are_valid(self):
        df = load_electricity()
        assert df["tariff_rate_sgd_per_kwh"].isin([0.18, 0.28]).all()


class TestLoadStaff:
    def test_returns_dataframe(self):
        df = load_staff()
        assert isinstance(df, pd.DataFrame)

    def test_has_8_staff(self):
        df = load_staff()
        assert len(df) == 8

    def test_availability_contains_valid_shifts(self):
        df = load_staff()
        valid_shifts = {"morning", "afternoon", "night"}
        for avail in df["availability"]:
            shifts = set(avail.split(","))
            assert shifts.issubset(valid_shifts)


class TestLoadSensors:
    def test_returns_dataframe(self):
        df = load_sensors()
        assert isinstance(df, pd.DataFrame)

    def test_has_1440_rows(self):
        df = load_sensors()
        assert len(df) == 1440

    def test_temperature_in_reasonable_range(self):
        df = load_sensors()
        assert df["temp_c"].between(10, 45).all()
