"""
Milestone 3 - Ingestion and chunking.

load_documents() reads every .txt file from data/ and attaches metadata.
chunk_text() splits a document by natural units first (reviews, posts,
messages, paragraphs) and only falls back to fixed-size character splitting
when a single unit is too long.

Every chunk keeps: file path, document title, source type, and chunk id,
so the answer can always be cited (see "Anticipated Challenges" #2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import config


@dataclass
class Chunk:
    """One retrievable unit of text plus the metadata needed to cite it."""
    text: str
    source_file: str      # e.g. "rmp_professor_a.txt"
    source_path: str      # full path on disk
    title: str            # human-readable document title
    source_type: str      # e.g. "Rate My Professors review"
    chunk_id: str         # e.g. "rmp_professor_a.txt::3"

    def metadata(self) -> dict:
        return {
            "source_file": self.source_file,
            "source_path": self.source_path,
            "title": self.title,
            "source_type": self.source_type,
            "chunk_id": self.chunk_id,
        }


def _source_type_for(filename: str) -> str:
    """Map a filename to a readable source type using config rules."""
    lower = filename.lower()
    for needle, label in config.SOURCE_TYPE_RULES.items():
        if needle in lower:
            return label
    return "Student-generated source"


def _title_for(filename: str, first_lines: str) -> str:
    """
    Derive a title. Prefer a 'Source:'/'Professor:'/'Thread:' header line
    if the document has one; otherwise fall back to a tidied filename.
    """
    for line in first_lines.splitlines():
        line = line.strip()
        for prefix in ("Thread:", "Professor:", "Source:"):
            if line.startswith(prefix):
                return line[len(prefix):].strip().strip('"')
    return filename.replace("_", " ").replace(".txt", "").title()


def _split_natural_units(text: str) -> list[str]:
    """
    Split a document into natural units.

    Primary separator is a '---' divider (used between reviews/posts).
    If there are no dividers, fall back to blank-line paragraph breaks.
    """
    if "---" in text:
        parts = re.split(r"\n-{3,}\n", text)
    else:
        parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def _split_long_unit(unit: str) -> list[str]:
    """
    Fixed-size character splitting with overlap, used only when a single
    natural unit exceeds CHUNK_SIZE. Tries to break on whitespace so words
    are not cut in half.
    """
    size = config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP
    pieces: list[str] = []
    start = 0
    n = len(unit)

    while start < n:
        end = min(start + size, n)
        if end < n:
            # back up to the last space to avoid splitting a word
            space = unit.rfind(" ", start + config.CHUNK_MIN_SIZE, end)
            if space != -1:
                end = space
        pieces.append(unit[start:end].strip())
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return [p for p in pieces if p]


def chunk_text(text: str) -> list[str]:
    """
    Chunk a document: natural units first, then split any oversized unit.
    Returns a list of chunk strings (metadata is attached by the caller).
    """
    chunks: list[str] = []
    for unit in _split_natural_units(text):
        if len(unit) <= config.CHUNK_SIZE:
            chunks.append(unit)
        else:
            chunks.extend(_split_long_unit(unit))
    return chunks


def load_documents(data_dir: Path | None = None) -> list[Chunk]:
    """
    Read every .txt file in data_dir, chunk it, and return a flat list of
    Chunk objects with full metadata. Header lines like 'Source:' are kept
    inside the text so the model sees the provenance too.
    """
    data_dir = Path(data_dir) if data_dir else config.DATA_DIR
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    files = sorted(data_dir.glob("*.txt"))
    if not files:
        raise FileNotFoundError(
            f"No .txt files found in {data_dir}. Add your sources there."
        )

    all_chunks: list[Chunk] = []
    for path in files:
        raw = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not raw:
            continue
        source_type = _source_type_for(path.name)
        title = _title_for(path.name, raw[:400])

        for i, piece in enumerate(chunk_text(raw)):
            all_chunks.append(
                Chunk(
                    text=piece,
                    source_file=path.name,
                    source_path=str(path),
                    title=title,
                    source_type=source_type,
                    chunk_id=f"{path.name}::{i}",
                )
            )
    return all_chunks


if __name__ == "__main__":
    chunks = load_documents()
    print(f"Loaded {len(chunks)} chunks from {config.DATA_DIR}")
    by_file: dict[str, int] = {}
    for c in chunks:
        by_file[c.source_file] = by_file.get(c.source_file, 0) + 1
    for fname, count in sorted(by_file.items()):
        print(f"  {fname:35s} {count:3d} chunks")
