"""
Milestone 5 - Simple command-line interface for the Unofficial Guide RAG.

Usage:
    python app.py --rebuild          # (re)build the vector index from data/
    python app.py "your question"    # ask a single question
    python app.py                    # interactive mode (ask repeatedly)
"""

from __future__ import annotations

import argparse
import sys

from src import config
from src.embed_store import build_index
from src.pipeline import answer_question


def _print_result(result) -> None:
    print("\n" + "=" * 70)
    print(f"Q: {result.question}")
    print("-" * 70)
    print(result.answer)
    print("-" * 70)
    print("Retrieved chunks (top-{}):".format(config.TOP_K))
    for i, rc in enumerate(result.chunks, 1):
        print(f"  [{i}] score={rc.score:.3f}  {rc.citation}")
    print("Sources: " + ", ".join(result.sources))
    print("=" * 70 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Unofficial Guide RAG")
    parser.add_argument("question", nargs="*", help="question to ask")
    parser.add_argument(
        "--rebuild", action="store_true", help="rebuild the vector index"
    )
    parser.add_argument(
        "--top-k", type=int, default=config.TOP_K, help="chunks to retrieve"
    )
    args = parser.parse_args()

    if args.rebuild:
        n = build_index(reset=True)
        print(f"Indexed {n} chunks into {config.CHROMA_DIR}")
        if not args.question:
            return

    if args.question:
        result = answer_question(" ".join(args.question), top_k=args.top_k)
        _print_result(result)
        return

    # Interactive mode
    print("Unofficial Guide RAG. Type a question, or 'quit' to exit.")
    print(f"(LLM backend: {config.LLM_BACKEND})")
    while True:
        try:
            q = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if q.lower() in {"quit", "exit", "q", ""}:
            break
        _print_result(answer_question(q, top_k=args.top_k))


if __name__ == "__main__":
    sys.exit(main())
