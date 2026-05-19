"""RAG agent for Adopt a Kale Media AI — ChromaDB + sentence-transformers + Claude."""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Demo-mode cached answers — keyed by keywords, matched via substring
# ---------------------------------------------------------------------------
_DEMO_ANSWERS: dict[str, str] = {
    # Crops
    "crops": (
        "Adopt a Kale grows 12 varieties of leafy greens and herbs: spinach, kale, arugula, "
        "lettuce, kai lan, basil, cilantro, mint, choy sum, baby bok choy, watercress, and Swiss chard. "
        "All crops are hydroponically grown year-round with zero pesticides in our Jurong farm."
    ),
    # Water savings
    "water": (
        "Adopt a Kale uses 95% less water than conventional farming — approximately 2 litres per kg "
        "of produce vs. 20 litres for soil farming. Our closed-loop NFT system recirculates "
        "nutrient solution with a 98.2% water recycle rate, supplemented by collected rainwater."
    ),
    # Pesticides
    "pesticide": (
        "No pesticides, herbicides, or synthetic chemicals — ever. Adopt a Kale uses Integrated "
        "Pest Management (IPM) with beneficial insects (predatory mites, lacewings). "
        "Produce has zero pesticide residue and is SS 590:2018 HACCP-certified."
    ),
    # Location / farm address
    "located": (
        "Adopt a Kale is 15km from Singapore's CBD in Jurong Innovation District. "
        "Our farm spans 500 m² across 3 vertical layers, delivering to restaurants "
        "within 2 hours of harvest. Morning slots cover Jurong, Clementi, Bukit Merah, and CBD."
    ),
    # Sustainability
    "sustainab": (
        "Adopt a Kale is certified for environmental and food safety sustainability: "
        "95% less water, 98% less land, 90% fewer food miles vs. imports, "
        "zero pesticides, and HSA / SFA-approved food safety protocols."
    ),
    # Harvest
    "harvest": (
        "We harvest daily to fulfill morning delivery routes. Most crops are harvested "
        "between 5–7am, packed by 8am, and delivered to restaurants by 9–10am. "
        "This 2-hour farm-to-table model ensures maximum freshness and shelf life."
    ),
    # LED / energy
    "led": (
        "Our LED grow lights run on a tariff-optimised schedule shifting usage to off-peak "
        "hours (9pm–7am). This reduces electricity cost by 15–25% versus constant operation "
        "and aligns with Singapore's EMA peak pricing periods."
    ),
    # Revenue / profit / financials
    "revenue": (
        "Adopt a Kale's unit economics show: revenue of ~$8–12/kg produce, operating margin "
        "of 25–35% in normal tariff conditions, and payback period of ~3 years for the "
        "vertical farm infrastructure."
    ),
    # Delivery / logistics
    "deliver": (
        "Deliveries use a VRP-optimised routing system with 3 refrigerated trucks covering "
        "10–15 restaurant stops per morning route. All vehicles are electric, reducing "
        "last-mile emissions to near zero."
    ),
}

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


@dataclass
class FreshnessScore:
    """How up-to-date the knowledge base is."""

    days_since_update: int
    score: float  # 0.0–1.0, higher = fresher
    status: str  # "fresh", "stale", "critical"

    def __post_init__(self):
        if self.score >= 0.8:
            self.status = "fresh"
        elif self.score >= 0.5:
            self.status = "stale"
        else:
            self.status = "critical"


@dataclass
class RAGAnswer:
    """Answer from the RAG pipeline."""

    text: str
    sources: list[str]
    latency_ms: float
    freshness: FreshnessScore
    from_cache: bool = False  # demo-mode cache hit


# ---------------------------------------------------------------------------
# RAG Agent
# ---------------------------------------------------------------------------


class RAGAgent:
    """RAG chatbot backed by ChromaDB + sentence-transformers + Claude API."""

    def __init__(
        self,
        knowledge_dir: Path | str | None = None,
        persist_dir: Path | str | None = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "greenloop_kb",
        n_retrieval: int = 5,
        llm_max_tokens: int = 512,
    ):
        if knowledge_dir is None:
            from greenloop.data.loader import DATA_DIR

            knowledge_dir = DATA_DIR / "rag_knowledge"

        self.knowledge_dir = Path(knowledge_dir)
        self.persist_dir = Path(persist_dir) if persist_dir else None
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.n_retrieval = n_retrieval
        self.llm_max_tokens = llm_max_tokens

        self._embedder: "EmbeddingFunction" | None = None
        self._chroma_client: "PersistentClient | HTTPClient" | None = None
        self._collection: "Collection" | None = None
        self._is_demo: bool = False
        self._indexed: bool = False

    # ── Public API ────────────────────────────────────────────────────────

    def is_ready(self) -> bool:
        """True if ChromaDB collection is loaded and ready for queries."""
        return self._indexed and self._collection is not None

    def ensure_indexed(self) -> None:
        """Load/reload documents from knowledge_dir into ChromaDB."""
        if self._indexed:
            return

        t0 = time.monotonic()
        self._init_embedder()
        self._init_chroma()
        self._load_documents()
        self._indexed = True
        logger.info(
            "rag.indexed",
            extra={
                "duration_ms": round((time.monotonic() - t0) * 1000, 1),
                "n_docs": len(self._chroma_docs()),
                "persist_dir": str(self.persist_dir),
            },
        )

    def ask(
        self,
        question: str,
        *,
        include_freshness: bool = True,
    ) -> RAGAnswer:
        """Answer a question using RAG.

        Latency target: <500ms end-to-end.
        Falls back to demo-mode cache if LLM API key is not configured.
        """
        t0 = time.monotonic()

        # Check demo mode
        if self._is_demo_mode():
            return self._demo_answer(question, t0)

        # Ensure index
        self.ensure_indexed()

        # Retrieve context
        context_chunks = self._retrieve(question)
        context_text = "\n\n".join(
            f"[Source: {c['source']}]\n{c['text']}" for c in context_chunks
        )

        # Build prompt
        system_prompt = (
            "You are a helpful assistant for Adopt a Kale Farm — a hydroponic vertical farm in Singapore. "
            "Answer questions using ONLY the provided context. "
            "If the answer is not in the context, say you don't know. "
            "Be concise, factual, and mention specific numbers when available."
        )
        user_prompt = f"Context:\n{context_text}\n\nQuestion: {question}"

        # Call LLM
        try:
            from greenloop.utils.llm import chat

            answer_text = chat(
                [{"role": "system", "content": system_prompt},
                 {"role": "user", "content": user_prompt}],
                max_tokens=self.llm_max_tokens,
            )
        except Exception as exc:
            logger.warning("rag.llm_fallback", extra={"error": str(exc)})
            # Fall back to demo-mode cache on LLM failure (auth error, network, etc.)
            return self._demo_answer(question, t0)

        sources = list({c["source"] for c in context_chunks})
        latency_ms = round((time.monotonic() - t0) * 1000, 1)

        return RAGAnswer(
            text=answer_text,
            sources=sources,
            latency_ms=latency_ms,
            freshness=self._compute_freshness(),
            from_cache=False,
        )

    def get_freshness(self) -> FreshnessScore:
        """Return current knowledge base freshness score."""
        return self._compute_freshness()

    # ── Internals ─────────────────────────────────────────────────────────

    def _init_embedder(self) -> None:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

        self._embedder = SentenceTransformerEmbeddingFunction(model_name=self.embedding_model)

    def _init_chroma(self) -> None:
        from chromadb import PersistentClient

        if self.persist_dir:
            self._chroma_client = PersistentClient(path=str(self.persist_dir))
        else:
            self._chroma_client = PersistentClient()  # in-memory

        self._collection = self._chroma_client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._embedder,
            metadata={"description": "Adopt a Kale Farm knowledge base"},
        )

    def _load_documents(self) -> None:
        """Load all .md files from knowledge_dir into ChromaDB."""
        docs = []
        ids = []
        for md_file in sorted(self.knowledge_dir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            source_name = md_file.name
            # Split into paragraphs (simple heuristic: double newline = chunk)
            chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
            for i, chunk in enumerate(chunks):
                docs.append(chunk)
                ids.append(f"{source_name}::{i}")

        if not docs:
            logger.warning("rag.no_docs_found", extra={"knowledge_dir": str(self.knowledge_dir)})
            return

        self._collection.add(documents=docs, ids=ids)

    def _chroma_docs(self) -> list[dict]:
        """Return all docs currently in the collection."""
        result = self._collection.get()
        return [
            {"id": rid, "text": doc, "source": rid.split("::")[0]}
            for rid, doc in zip(result["ids"], result["documents"])
        ]

    def _retrieve(self, query: str) -> list[dict]:
        """Retrieve top-k chunks for query."""
        results = self._collection.query(
            query_texts=[query],
            n_results=self.n_retrieval,
            include=["documents"],
        )
        chunks = []
        for rid, doc in zip(results["ids"][0], results["documents"][0]):
            chunks.append({"id": rid, "text": doc, "source": rid.split("::")[0]})
        return chunks

    def _is_demo_mode(self) -> bool:
        """Check if LLM is unavailable (no API key)."""
        try:
            from greenloop.llm.client import llm_is_configured

            configured = llm_is_configured()
            self._is_demo = not configured
            return not configured
        except Exception:
            self._is_demo = True
            return True

    def _demo_answer(self, question: str, t0: float) -> RAGAnswer:
        """Return a cached answer for demo/no-API-key mode."""
        q_lower = question.lower()
        answer_text = None
        for key, answer in _DEMO_ANSWERS.items():
            if key in q_lower:
                answer_text = answer
                break

        if answer_text is None:
            answer_text = (
                "I'm in demo mode (no LLM API key configured). I can answer questions about: "
                "crops & varieties · water savings · pesticides · location & delivery areas · "
                "sustainability certifications · harvest schedule · LED energy schedule · "
                "unit economics & revenue. "
                "Configure OPENAI_API_KEY (or ANTHROPIC_API_KEY) in .env to unlock full RAG responses."
            )

        return RAGAnswer(
            text=answer_text,
            sources=["demo_cache"],
            latency_ms=round((time.monotonic() - t0) * 1000, 1),
            freshness=self._compute_freshness(),
            from_cache=True,
        )

    def _compute_freshness(self) -> FreshnessScore:
        """Compute freshness score based on knowledge base modification time."""
        if not self.knowledge_dir.exists():
            return FreshnessScore(days_since_update=999, score=0.0, status="critical")

        md_files = list(self.knowledge_dir.glob("*.md"))
        if not md_files:
            return FreshnessScore(days_since_update=999, score=0.0, status="critical")

        latest_mtime = max(f.stat().st_mtime for f in md_files)
        latest_date = datetime.fromtimestamp(latest_mtime)
        today = datetime.now()
        days_since = (today - latest_date).days

        # Score: 1.0 if updated today, decays linearly to 0.0 after 30 days
        score = max(0.0, 1.0 - (days_since / 30))
        return FreshnessScore(days_since_update=days_since, score=round(score, 3), status="fresh")
