"""
Milestone 4 (part 2) - Retrieval.

Embeds the user query with the same model and asks Chroma for the
top-k most similar chunks (cosine similarity). Returns lightweight
RetrievedChunk objects that carry text, metadata, and a similarity score.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config
from .embed_store import embed_texts, get_collection


@dataclass
class RetrievedChunk:
    text: str
    metadata: dict
    score: float  # cosine similarity in [0, 1]; higher is more relevant

    @property
    def citation(self) -> str:
        m = self.metadata
        return f"{m['title']} ({m['source_type']}, {m['source_file']})"


def retrieve(query: str, top_k: int | None = None) -> list[RetrievedChunk]:
    """Return the top_k chunks most relevant to query."""
    top_k = top_k or config.TOP_K
    collection = get_collection()

    query_embedding = embed_texts([query])[0]
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    docs = result["documents"][0]
    metas = result["metadatas"][0]
    dists = result["distances"][0]

    retrieved: list[RetrievedChunk] = []
    for text, meta, dist in zip(docs, metas, dists):
        # Chroma returns cosine distance; convert to similarity.
        similarity = 1.0 - float(dist)
        retrieved.append(RetrievedChunk(text=text, metadata=meta, score=similarity))
    return retrieved


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "Which professor is beginner-friendly for math?"
    print(f"Query: {q}\n")
    for i, rc in enumerate(retrieve(q), 1):
        print(f"[{i}] score={rc.score:.3f}  {rc.citation}")
        print(f"    {rc.text[:160]}...\n")
