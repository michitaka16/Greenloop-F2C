"""RAG HITL — feedback logging, query logging, and tone control.

Wires into the dashboard Media AI chatbot panel to:
1. Log user feedback (good / needs refinement) to a CSV file.
2. Log every query + answer to a CSV file.
3. Apply tone pre-selection (Sales / Neutral / Technical) as a system-prompt modifier.
"""

from __future__ import annotations

import csv
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class Tone(Enum):
    """Response tone for the RAG chatbot."""

    SALES = "sales"
    NEUTRAL = "neutral"
    TECHNICAL = "technical"


TONE_LABELS = {
    Tone.SALES: "Sales",
    Tone.NEUTRAL: "Neutral",
    Tone.TECHNICAL: "Technical",
}


@dataclass
class FeedbackRecord:
    """One feedback event from the chatbot UI."""

    timestamp: str
    question: str
    answer: str
    tone: str
    rating: str  # "good" | "needs_refinement"
    session_id: str


@dataclass
class QueryRecord:
    """One query logged to CSV."""

    timestamp: str
    question: str
    answer: str
    tone: str
    sources: str
    latency_ms: float
    from_cache: bool
    session_id: str


# ---------------------------------------------------------------------------
# Tone system prompts
# ---------------------------------------------------------------------------

TONE_MODIFIERS = {
    Tone.SALES: (
        "You are a enthusiastic GreenLoop sales advisor. Highlight ROI, freshness, "
        "and sustainability benefits. Use concrete numbers where available. "
        "End with an invitation to schedule a farm tour."
    ),
    Tone.NEUTRAL: (
        "You are a helpful and neutral assistant for GreenLoop Farm. "
        "Answer questions factually and concisely."
    ),
    Tone.TECHNICAL: (
        "You are a technical expert for GreenLoop Farm operations. "
        "Use precise agricultural and engineering terminology. "
        "Reference specific metrics, SOPs, and compliance standards where relevant."
    ),
}


def get_system_prompt(tone: Tone, base_prompt: str) -> str:
    """Combine tone modifier with the base RAG system prompt."""
    modifier = TONE_MODIFIERS.get(tone, TONE_MODIFIERS[Tone.NEUTRAL])
    return f"{modifier}\n\n{base_prompt}"


# ---------------------------------------------------------------------------
# Feedback logger
# ---------------------------------------------------------------------------

_FEEDBACK_LOCK = threading.Lock()
_FEEDBACK_PATH = Path("data/rag_feedback.csv")
_FEEDBACK_COLUMNS = ["timestamp", "question", "answer", "tone", "rating", "session_id"]


def log_feedback(record: FeedbackRecord) -> None:
    """Append one feedback record to rag_feedback.csv (thread-safe)."""
    path = _FEEDBACK_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    is_new = not path.exists()

    with _FEEDBACK_LOCK:
        with path.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=_FEEDBACK_COLUMNS)
            if is_new:
                writer.writeheader()
            writer.writerow({
                "timestamp": record.timestamp,
                "question": record.question,
                "answer": record.answer,
                "tone": record.tone,
                "rating": record.rating,
                "session_id": record.session_id,
            })

    logger.info("rag.feedback_logged", extra={"rating": record.rating})


# ---------------------------------------------------------------------------
# Query logger
# ---------------------------------------------------------------------------

_QUERY_LOCK = threading.Lock()
_QUERY_PATH = Path("data/rag_queries.csv")
_QUERY_COLUMNS = ["timestamp", "question", "answer", "tone", "sources",
                  "latency_ms", "from_cache", "session_id"]


def log_query(record: QueryRecord) -> None:
    """Append one query record to rag_queries.csv (thread-safe)."""
    path = _QUERY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    is_new = not path.exists()

    with _QUERY_LOCK:
        with path.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=_QUERY_COLUMNS)
            if is_new:
                writer.writeheader()
            writer.writerow({
                "timestamp": record.timestamp,
                "question": record.question,
                "answer": record.answer,
                "tone": record.tone,
                "sources": record.sources,
                "latency_ms": record.latency_ms,
                "from_cache": record.from_cache,
                "session_id": record.session_id,
            })

    logger.info("rag.query_logged", extra={"latency_ms": record.latency_ms})


# ---------------------------------------------------------------------------
# Top-10 analytics
# ---------------------------------------------------------------------------


def get_top_questions(n: int = 10) -> list[tuple[str, int]]:
    """Return top-n questions by frequency from rag_queries.csv.

    Returns
    -------
    list of (question, count) tuples, descending by count.
    """
    path = _QUERY_PATH
    if not path.exists():
        return []

    counts: dict[str, int] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            q = row.get("question", "").strip().lower()
            if q:
                counts[q] = counts.get(q, 0) + 1

    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]


def get_feedback_summary() -> dict[str, int]:
    """Return counts of each rating from rag_feedback.csv."""
    path = _FEEDBACK_PATH
    if not path.exists():
        return {"good": 0, "needs_refinement": 0}

    counts: dict[str, int] = {"good": 0, "needs_refinement": 0}
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rating = row.get("rating", "").strip().lower()
            if rating in counts:
                counts[rating] += 1
    return counts
