"""
Milestone 4 (part 1) - Embedding and vector storage.

Embeds chunks with all-MiniLM-L6-v2 (sentence-transformers) and stores them
in a persistent Chroma collection along with their metadata.

The SentenceTransformer model is loaded once and reused. We pass our own
embeddings to Chroma (rather than letting Chroma embed) so the exact model
from the plan is guaranteed.
"""

from __future__ import annotations

import chromadb

from . import config
from .ingest import Chunk, load_documents

_model = None  # cached SentenceTransformer, loaded lazily


def get_model():
    """Load (and cache) the embedding model. Imported lazily so the rest of
    the system can run without sentence-transformers/torch installed."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(config.EMBEDDING_MODEL)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return a list of embedding vectors for the given texts."""
    model = get_model()
    vectors = model.encode(
        texts, convert_to_numpy=True, show_progress_bar=False
    )
    return vectors.tolist()


def _get_client() -> chromadb.ClientAPI:
    config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(config.CHROMA_DIR))


def build_index(reset: bool = True) -> int:
    """
    Load documents, embed them, and (re)build the Chroma collection.
    Returns the number of chunks indexed.
    """
    chunks: list[Chunk] = load_documents()
    client = _get_client()

    if reset:
        try:
            client.delete_collection(config.COLLECTION_NAME)
        except Exception:
            pass  # collection did not exist yet

    collection = client.get_or_create_collection(
        name=config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [c.chunk_id for c in chunks]
    documents = [c.text for c in chunks]
    metadatas = [c.metadata() for c in chunks]
    embeddings = embed_texts(documents)

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )
    return len(chunks)


def get_collection() -> chromadb.Collection:
    """Return the existing collection, or raise if the index isn't built."""
    client = _get_client()
    try:
        return client.get_collection(config.COLLECTION_NAME)
    except Exception as exc:
        raise RuntimeError(
            "Vector index not found. Run `python -m src.embed_store` "
            "(or `python app.py --rebuild`) first."
        ) from exc


if __name__ == "__main__":
    n = build_index(reset=True)
    print(f"Indexed {n} chunks into Chroma at {config.CHROMA_DIR}")
