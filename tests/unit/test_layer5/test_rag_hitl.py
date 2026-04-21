"""Tests for RAG HITL module (feedback logging, query logging, tone control)."""

import csv
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from greenloop.rag.hitl import (
    Tone,
    TONE_LABELS,
    FeedbackRecord,
    QueryRecord,
    get_feedback_summary,
    get_system_prompt,
    get_top_questions,
    log_feedback,
    log_query,
)


class TestTone:
    def test_tone_labels_has_three_entries(self):
        assert len(TONE_LABELS) == 3

    def test_tone_labels_values(self):
        assert TONE_LABELS[Tone.SALES] == "Sales"
        assert TONE_LABELS[Tone.NEUTRAL] == "Neutral"
        assert TONE_LABELS[Tone.TECHNICAL] == "Technical"


class TestGetSystemPrompt:
    def test_sales_tone_adds_sales_modifier(self):
        prompt = get_system_prompt(
            Tone.SALES,
            "You are a helpful assistant.",
        )
        assert "sales" in prompt.lower() or "ROI" in prompt

    def test_neutral_tone_adds_neutral_modifier(self):
        prompt = get_system_prompt(
            Tone.NEUTRAL,
            "You are a helpful assistant.",
        )
        assert "neutral" in prompt.lower()

    def test_technical_tone_adds_technical_modifier(self):
        prompt = get_system_prompt(
            Tone.TECHNICAL,
            "You are a helpful assistant.",
        )
        assert "technical" in prompt.lower() or "SOP" in prompt


class TestFeedbackRecord:
    def test_feedback_record_fields(self):
        record = FeedbackRecord(
            timestamp="2025-10-15T10:00:00",
            question="What crops do you grow?",
            answer="We grow leafy greens.",
            tone="neutral",
            rating="good",
            session_id="abc123",
        )
        assert record.rating == "good"
        assert record.tone == "neutral"


class TestQueryRecord:
    def test_query_record_fields(self):
        record = QueryRecord(
            timestamp="2025-10-15T10:00:00",
            question="Where are you located?",
            answer="Jurong, Singapore",
            tone="sales",
            sources="location.md",
            latency_ms=150.0,
            from_cache=False,
            session_id="abc123",
        )
        assert record.latency_ms == 150.0
        assert record.from_cache is False


class TestLogFeedback:
    def test_log_feedback_creates_file(self, tmp_path, monkeypatch):
        # Redirect data path
        monkeypatch.setattr(
            "greenloop.rag.hitl._FEEDBACK_PATH",
            tmp_path / "rag_feedback.csv",
        )
        record = FeedbackRecord(
            timestamp="2025-10-15T10:00:00",
            question="test question",
            answer="test answer",
            tone="neutral",
            rating="good",
            session_id="sess1",
        )
        log_feedback(record)

        path = tmp_path / "rag_feedback.csv"
        assert path.exists()
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["rating"] == "good"
        assert rows[0]["question"] == "test question"

    def test_log_feedback_append_multiple(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "greenloop.rag.hitl._FEEDBACK_PATH",
            tmp_path / "rag_feedback.csv",
        )
        for i in range(3):
            log_feedback(FeedbackRecord(
                timestamp=datetime.now().isoformat(),
                question=f"q{i}",
                answer=f"a{i}",
                tone="neutral",
                rating="good" if i % 2 == 0 else "needs_refinement",
                session_id=f"sess{i}",
            ))
        path = tmp_path / "rag_feedback.csv"
        with path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 3


class TestLogQuery:
    def test_log_query_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "greenloop.rag.hitl._QUERY_PATH",
            tmp_path / "rag_queries.csv",
        )
        record = QueryRecord(
            timestamp="2025-10-15T10:00:00",
            question="What is your water savings?",
            answer="95% less water.",
            tone="neutral",
            sources="water.md",
            latency_ms=120.5,
            from_cache=True,
            session_id="sess1",
        )
        log_query(record)

        path = tmp_path / "rag_queries.csv"
        assert path.exists()
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["from_cache"] == "True"
        assert rows[0]["latency_ms"] == "120.5"


class TestGetTopQuestions:
    def test_empty_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "greenloop.rag.hitl._QUERY_PATH",
            tmp_path / "rag_queries.csv",
        )
        result = get_top_questions(10)
        assert result == []

    def test_top_questions_counted_correctly(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "greenloop.rag.hitl._QUERY_PATH",
            tmp_path / "rag_queries.csv",
        )
        # Write some query records
        path = tmp_path / "rag_queries.csv"
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=["timestamp", "question", "answer", "tone",
                            "sources", "latency_ms", "from_cache", "session_id"],
            )
            writer.writeheader()
            for _ in range(3):
                writer.writerow({
                    "timestamp": datetime.now().isoformat(),
                    "question": "what crops do you grow",
                    "answer": "leafy greens",
                    "tone": "neutral",
                    "sources": "",
                    "latency_ms": "100",
                    "from_cache": "False",
                    "session_id": "s1",
                })
            for _ in range(2):
                writer.writerow({
                    "timestamp": datetime.now().isoformat(),
                    "question": "where are you located",
                    "answer": "Jurong",
                    "tone": "sales",
                    "sources": "",
                    "latency_ms": "100",
                    "from_cache": "False",
                    "session_id": "s1",
                })

        result = get_top_questions(5)
        questions = {q for q, _ in result}
        assert ("what crops do you grow", 3) in result
        assert ("where are you located", 2) in result


class TestGetFeedbackSummary:
    def test_empty_file_returns_zeros(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "greenloop.rag.hitl._FEEDBACK_PATH",
            tmp_path / "rag_feedback.csv",
        )
        result = get_feedback_summary()
        assert result["good"] == 0
        assert result["needs_refinement"] == 0

    def test_summary_counts_correctly(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "greenloop.rag.hitl._FEEDBACK_PATH",
            tmp_path / "rag_feedback.csv",
        )
        path = tmp_path / "rag_feedback.csv"
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=["timestamp", "question", "answer", "tone", "rating", "session_id"],
            )
            writer.writeheader()
            for _ in range(4):
                writer.writerow({
                    "timestamp": datetime.now().isoformat(),
                    "question": "q",
                    "answer": "a",
                    "tone": "neutral",
                    "rating": "good",
                    "session_id": "s1",
                })
            for _ in range(2):
                writer.writerow({
                    "timestamp": datetime.now().isoformat(),
                    "question": "q",
                    "answer": "a",
                    "tone": "neutral",
                    "rating": "needs_refinement",
                    "session_id": "s1",
                })

        result = get_feedback_summary()
        assert result["good"] == 4
        assert result["needs_refinement"] == 2
