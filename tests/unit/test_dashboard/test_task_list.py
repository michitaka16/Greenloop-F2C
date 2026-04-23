"""Tests for greenloop.dashboard.components.task_list."""

from __future__ import annotations

from greenloop.dashboard.components.task_list import (
    _build_priority_tasks,
    _build_routine_tasks,
    _harvest_time_for_tier,
    _priority_label,
    _greeting,
)


class TestPriorityTasksFromDiagnoses:
    """test_priority_tasks_from_diagnoses"""

    def test_nitrogen_low_returns_priority_task(self):
        plan = {
            "rack_layout": {"tier_3": "baby_spinach"},
            "cv_diagnosis_summary": {
                "details": {
                    "tier_3": {
                        "nutrition_status": "nitrogen_low",
                        "growth_stage": "mid",
                    }
                }
            },
        }
        tasks = _build_priority_tasks(plan)
        assert len(tasks) == 1
        assert tasks[0]["action"] == "Add nitrogen"
        assert tasks[0]["rack"] == "Rack 3"
        assert tasks[0]["crop"] == "Baby Spinach"

    def test_water_stress_returns_priority_task(self):
        plan = {
            "rack_layout": {"tier_4": "arugula"},
            "cv_diagnosis_summary": {
                "details": {
                    "tier_4": {
                        "nutrition_status": "water_stress",
                        "growth_stage": "harvest_ready",
                    }
                }
            },
        }
        tasks = _build_priority_tasks(plan)
        assert len(tasks) == 1
        assert tasks[0]["action"] == "Increase irrigation"
        assert tasks[0]["rack"] == "Rack 4"

    def test_normal_nutrition_returns_no_priority_task(self):
        plan = {
            "rack_layout": {"tier_0": "kai_lan"},
            "cv_diagnosis_summary": {
                "details": {
                    "tier_0": {
                        "nutrition_status": "normal",
                        "growth_stage": "harvest_ready",
                    }
                }
            },
        }
        tasks = _build_priority_tasks(plan)
        assert tasks == []

    def test_multiple_problem_racks_returns_all_tasks(self):
        plan = {
            "rack_layout": {
                "tier_3": "baby_spinach",
                "tier_6": "lettuce_mambo",
            },
            "cv_diagnosis_summary": {
                "details": {
                    "tier_3": {"nutrition_status": "nitrogen_low", "growth_stage": "mid"},
                    "tier_6": {"nutrition_status": "water_stress", "growth_stage": "early"},
                }
            },
        }
        tasks = _build_priority_tasks(plan)
        assert len(tasks) == 2
        actions = {t["action"] for t in tasks}
        assert "Add nitrogen" in actions
        assert "Increase irrigation" in actions


class TestRoutineTasksFromMilpPlan:
    """test_routine_tasks_from_milp_plan"""

    def test_harvest_ready_rack_generates_harvest_task(self):
        plan = {
            "rack_layout": {"tier_0": "kai_lan"},
            "cv_diagnosis_summary": {
                "details": {
                    "tier_0": {
                        "nutrition_status": "normal",
                        "growth_stage": "harvest_ready",
                    }
                }
            },
            "led_schedule": {},
            "staff_shifts": [],
        }
        tasks = _build_routine_tasks(plan)
        harvest_tasks = [t for t in tasks if "Harvest" in t["action"]]
        assert len(harvest_tasks) == 1
        assert harvest_tasks[0]["time"] == "07:00"
        assert "Rack 0" in harvest_tasks[0]["action"]
        assert "Kai Lan" in harvest_tasks[0]["detail"]

    def test_morning_staff_generates_dispatch_task(self):
        plan = {
            "rack_layout": {},
            "cv_diagnosis_summary": {"details": {}},
            "led_schedule": {},
            "staff_shifts": [
                {"shift": "morning", "staff_count": 3, "hours": ["06:00", "14:00"]},
                {"shift": "afternoon", "staff_count": 2, "hours": ["14:00", "22:00"]},
            ],
        }
        tasks = _build_routine_tasks(plan)
        dispatch_tasks = [t for t in tasks if "Dispatch" in t["action"]]
        assert len(dispatch_tasks) == 1
        assert dispatch_tasks[0]["time"] == "10:00"

    def test_led_schedule_turning_off_at_peak_extracts_correct_hour(self):
        # tier_0 LEDs off from 17:00 onwards (17 is in PEAK_HOURS)
        led_schedule = {
            "tier_0": [1] * 17 + [0] * 7,
            "tier_1": [1] * 16 + [0] * 8,
        }
        plan = {
            "rack_layout": {},
            "cv_diagnosis_summary": {"details": {}},
            "led_schedule": led_schedule,
            "staff_shifts": [],
        }
        tasks = _build_routine_tasks(plan)
        led_tasks = [t for t in tasks if "LED" in t["action"]]
        assert len(led_tasks) == 1
        # Earliest off-hour in peak window is 17:00
        assert led_tasks[0]["time"] == "17:00"
        assert "peak tariff" in led_tasks[0]["detail"].lower()

    def test_review_tomorrow_task_is_always_present(self):
        plan = {
            "rack_layout": {},
            "cv_diagnosis_summary": {"details": {}},
            "led_schedule": {},
            "staff_shifts": [],
        }
        tasks = _build_routine_tasks(plan)
        review_tasks = [t for t in tasks if "Review tomorrow" in t["action"]]
        assert len(review_tasks) == 1
        assert review_tasks[0]["time"] == "18:00"


class TestEmptyStateWhenNoDiagnoses:
    """test_empty_state_when_no_diagnoses"""

    def test_empty_cv_details_returns_no_priority_tasks(self):
        plan = {
            "rack_layout": {"tier_0": "kai_lan"},
            "cv_diagnosis_summary": {"details": {}},
        }
        tasks = _build_priority_tasks(plan)
        assert tasks == []

    def test_empty_plan_returns_empty_routine(self):
        plan = {
            "rack_layout": {},
            "cv_diagnosis_summary": {"details": {}},
            "led_schedule": {},
            "staff_shifts": [],
        }
        tasks = _build_routine_tasks(plan)
        # Only the review task is always present
        review_tasks = [t for t in tasks if "Review tomorrow" in t["action"]]
        assert len(review_tasks) == 1
        harvest_tasks = [t for t in tasks if "Harvest" in t["action"]]
        assert harvest_tasks == []


class TestHelperFunctions:
    """Unit tests for helper functions."""

    def test_priority_label_nitrogen_low(self):
        assert _priority_label("nitrogen_low") == "Add nitrogen"

    def test_priority_label_water_stress(self):
        assert _priority_label("water_stress") == "Increase irrigation"

    def test_priority_label_unknown(self):
        assert _priority_label("unknown_condition") == "Check crop"

    def test_harvest_time_for_tier_finds_first_off(self):
        schedule = [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        assert _harvest_time_for_tier({"tier_0": schedule}, "tier_0") == 7

    def test_harvest_time_for_tier_ignores_early_off(self):
        # First 5 hours off (simulating night), first real off is at 17
        schedule = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
        assert _harvest_time_for_tier({"tier_0": schedule}, "tier_0") == 17

    def test_harvest_time_for_tier_never_off(self):
        schedule = [1] * 24
        assert _harvest_time_for_tier({"tier_0": schedule}, "tier_0") is None

    def test_greeting_is_not_empty(self):
        greeting = _greeting()
        assert greeting != ""
        assert greeting in ("Good morning!", "Good afternoon!", "Good evening!")
