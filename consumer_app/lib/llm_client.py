"""RAG client — connects consumer chat to RAGAgent with ZAI LLM."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env so LLM_PROVIDER and ZAI_API_KEY are available
_dotenv = Path(__file__).parent.parent.parent / ".env"
if _dotenv.exists():
    load_dotenv(_dotenv)

# Ensure src/ is on sys.path for greenloop editable install
_src_dir = Path(__file__).parent.parent.parent / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))


class RAGClient:
    """Wrapper around RAGAgent that uses ZAI LLM.

    Falls back to keyword-matched mock responses when LLM is unavailable.
    """

    def __init__(self):
        from greenloop.rag.agent import RAGAgent

        data_dir = Path(__file__).parent.parent.parent / "data"
        self._agent = RAGAgent(
            knowledge_dir=data_dir / "rag_knowledge",
            persist_dir=str(data_dir / "chroma_db"),
            embedding_model="all-MiniLM-L6-v2",
            collection_name="greenloop_kb",
            n_retrieval=5,
            llm_max_tokens=512,
        )
        self._agent.ensure_indexed()
        self._provider = os.environ.get("LLM_PROVIDER", "zai")

    def ask(self, question: str) -> dict:
        """Ask a question. Returns dict with text, citations, recipes, from_cache."""
        try:
            # Try real RAG + LLM path
            answer = self._agent.ask(question, include_freshness=False)
            return {
                "text": answer.text,
                "citations": [{"source": s, "snippet": s} for s in answer.sources],
                "recipes": None,
                "from_cache": answer.from_cache,
            }
        except Exception as exc:
            logger.warning("rag.llm_fallback: %s", str(exc))
            # Fall back to mock
            from consumer_app.lib.mock_data import mock_response
            return mock_response(question)
