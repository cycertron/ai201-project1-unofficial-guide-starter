"""
Central configuration for the Unofficial Guide RAG system.

Every tunable parameter lives here so the rest of the code stays readable
and the design choices from the planning document are easy to find and change.
"""

from pathlib import Path

# --- Paths -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"            # source .txt files live here
CHROMA_DIR = PROJECT_ROOT / "chroma_store"  # persistent vector DB
COLLECTION_NAME = "unofficial_guide"

# --- Chunking (see "Chunking Strategy" in the plan) --------------------------
# Chunk first by natural units (review / post / message / paragraph).
# Only fall back to fixed-size splitting when a unit is longer than CHUNK_SIZE.
CHUNK_SIZE = 1000          # max characters per chunk (~250 tokens)
CHUNK_MIN_SIZE = 700       # target floor for a split chunk (~150 tokens)
CHUNK_OVERLAP = 125        # characters of overlap when splitting a long unit

# --- Retrieval (see "Retrieval Approach") ------------------------------------
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # lightweight sentence-transformers model
TOP_K = 4                              # chunks retrieved per query

# --- Generation backend ------------------------------------------------------
# Options: "groq", "openai", "anthropic", or "offline".
# "offline" needs no API key: it returns an extractive, cited answer built
# straight from the retrieved chunks, so retrieval is testable on its own.
LLM_BACKEND = "groq"
OPENAI_MODEL = "gpt-4o-mini"
ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"

# Groq is OpenAI-API-compatible (uses the openai client + a Groq base URL).
# Set your key with:  export GROQ_API_KEY="gsk_..."
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# --- Source-type labels for metadata -----------------------------------------
# Maps a filename substring to a human-readable source type. Used during
# ingestion so every chunk carries honest provenance for citations.
SOURCE_TYPE_RULES = {
    "rmp_": "Rate My Professors review",
    "reddit_": "Reddit thread",
    "niche_": "Niche college review",
    "unigo_": "Unigo college review",
    "course_advice": "Student course advice",
    "discord_": "Discord advice",
    "campus_": "Campus newspaper article",
}
