"""Tests for the 10-rack grid view in the crop diagnosis panel."""

from __future__ import annotations

import pytest
from pathlib import Path

from adoptakale.layer1b.simulation import (
    mock_diagnose_from_image,
    diagnose_batch,
    parse_filename_to_crop,
    parse_rack_number,
    filename_to_rack_id,
)
from adoptakale.layer1b.architecture import DiagnosisResult


class TestFilenameParsing:
    """Filename → rack/crop parsing for auto-assignment."""

    def test_parse_rack_number_rack_format(self):
        assert parse_rack_number("rack_3.jpg") == 3
        assert parse_rack_number("rack_0.png") == 0
        assert parse_rack_number("RACK_9.jpeg") == 9

    def test_parse_rack_number_tier_format(self):
        assert parse_rack_number("tier_3.jpg") == 3
        assert parse_rack_number("tier_0.png") == 0

    def test_parse_rack_number_with_underscore(self):
        assert parse_rack_number("rack_3_upload.jpg") == 3
        assert parse_rack_number("img_tier_7_test.png") == 7

    def test_parse_rack_number_invalid(self):
        assert parse_rack_number("rack_10.jpg") is None  # out of range
        assert parse_rack_number("rack.jpg") is None
        assert parse_rack_number("demo_spinach.jpg") is None

    def test_parse_filename_to_crop_spinach(self):
        assert parse_filename_to_crop("demo_spinach_nitrogen.jpg") == "baby_spinach"
        assert parse_filename_to_crop("spinach_upload.png") == "baby_spinach"

    def test_parse_filename_to_crop_kailan(self):
        assert parse_filename_to_crop("demo_kailan_healthy.jpg") == "kai_lan"
        assert parse_filename_to_crop("kailan_001.png") == "kai_lan"

    def test_parse_filename_to_crop_lettuce(self):
        assert parse_filename_to_crop("demo_lettuce_wilt.jpg") == "lettuce_mambo"
        assert parse_filename_to_crop("lettuce_wilt_001.png") == "lettuce_mambo"

    def test_parse_filename_to_crop_generic_keywords(self):
        # healthy and water_stress are generic — no specific crop mapping
        assert parse_filename_to_crop("demo_healthy.jpg") is None
        assert parse_filename_to_crop("water_stress_rack3.jpg") is None

    def test_filename_to_rack_id_direct_rack_number(self):
        layout = {"tier_3": "kai_lan", "tier_7": "baby_spinach"}
        assert filename_to_rack_id("rack_3.jpg", layout) == "tier_3"
        assert filename_to_rack_id("tier_7.png", layout) == "tier_7"

    def test_filename_to_rack_id_crop_keyword(self):
        layout = {"tier_1": "kai_lan", "tier_5": "baby_spinach", "tier_9": "arugula"}
        assert filename_to_rack_id("demo_kailan_healthy.jpg", layout) == "tier_1"
        assert filename_to_rack_id("spinach_nitrogen.jpg", layout) == "tier_5"

    def test_filename_to_rack_id_no_match(self):
        layout = {"tier_0": "kai_lan", "tier_1": "arugula"}
        assert filename_to_rack_id("random_file.jpg", layout) is None


class TestBatchDiagnosis:
    """Batch processing of multiple rack diagnoses."""

    def test_diagnose_batch_returns_all_keys(self):
        """Batch diagnose should return a result for each input rack_id."""
        images = {
            "tier_0": b"fake bytes tier 0",
            "tier_3": b"fake bytes tier 3",
            "tier_9": b"fake bytes tier 9",
        }
        results = diagnose_batch(images)

        assert set(results.keys()) == {"tier_0", "tier_3", "tier_9"}
        for result in results.values():
            assert isinstance(result, DiagnosisResult)

    def test_diagnose_batch_deterministic(self):
        """Same image bytes should produce the same diagnosis."""
        img = b"identical image bytes for testing"
        results = diagnose_batch({"tier_0": img, "tier_1": img})
        assert results["tier_0"].nutrition_status == results["tier_1"].nutrition_status

    def test_diagnose_batch_unknown_rack_defaults_to_tier_0(self):
        """Unknown rack_ids should not crash — they default to tier_0."""
        images = {"unknown_rack": b"some image data"}
        results = diagnose_batch(images)
        # Should return a result, not raise
        assert "unknown_rack" in results


class TestDemoSetLoader:
    """Demo image set covers all 10 racks."""

    def test_demo_images_exist(self):
        """All 3 demo images should exist in data/demo_images/."""
        demo_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "demo_images"
        assert (demo_dir / "demo_kailan_healthy.jpg").exists()
        assert (demo_dir / "demo_spinach_nitrogen.jpg").exists()
        assert (demo_dir / "demo_lettuce_wilt.jpg").exists()

    def test_demo_image_loadable(self):
        """Demo images should be loadable as JPEG."""
        demo_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "demo_images"
        from PIL import Image
        for filename in ["demo_kailan_healthy.jpg", "demo_spinach_nitrogen.jpg", "demo_lettuce_wilt.jpg"]:
            img = Image.open(demo_dir / filename)
            assert img.size[0] >= 100 and img.size[1] >= 100

    def test_mock_diagnose_from_image_produces_result(self):
        """mock_diagnose_from_image should produce a valid DiagnosisResult."""
        demo_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "demo_images"
        img_bytes = (demo_dir / "demo_kailan_healthy.jpg").read_bytes()
        result = mock_diagnose_from_image(img_bytes, "tier_0")

        assert isinstance(result, DiagnosisResult)
        assert result.rack_id == "tier_0"
        assert result.growth_stage in ("early", "mid", "harvest_ready")
        assert result.nutrition_status in ("normal", "nitrogen_low", "water_stress")
        assert 0.0 <= result.growth_confidence <= 1.0
        assert 0.0 <= result.nutrition_confidence <= 1.0
        assert result.is_simulated is True

    def test_diagnose_batch_with_demo_images(self):
        """Full batch diagnose using real demo image files."""
        demo_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "demo_images"
        images = {
            f"tier_{i}": (demo_dir / "demo_kailan_healthy.jpg").read_bytes()
            for i in range(10)
        }
        results = diagnose_batch(images)
        assert len(results) == 10
        assert all(isinstance(r, DiagnosisResult) for r in results.values())
