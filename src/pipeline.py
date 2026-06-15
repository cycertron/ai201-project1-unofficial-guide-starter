"""
End-to-end RAG pipeline: retrieve -> generate -> return answer + citations.

This is the single entry point the CLI and the evaluation harness both call.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config
from .generate import generate_answer
from .retrieve import RetrievedChunk, retrieve


@dataclass
class RagResult:
    question: str
    answer: str
    chunks: list[RetrievedChunk]

    @property
    def sources(self) -> list[str]:
        """Unique source files that supported the answer, in rank order."""
        seen: list[str] = []
        for rc in self.chunks:
            f = rc.metadata["source_file"]
            if f not in seen:
                seen.append(f)
        return seen


def answer_question(question: str, top_k: int | None = None) -> RagResult:
    chunks = retrieve(question, top_k=top_k or config.TOP_K)
    answer = generate_answer(question, chunks)
    return RagResult(question=question, answer=answer, chunks=chunks)
