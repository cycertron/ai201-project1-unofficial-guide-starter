"""
Evaluation harness - runs the 5 questions from the planning document and
checks whether the EXPECTED source file(s) appear in the retrieved chunks.

This is a retrieval-quality check (does the system surface the right
evidence?), which is the part you can score objectively without a human
reading every answer. It runs against whatever LLM_BACKEND is configured,
including "offline".

Usage:
    python evaluate.py
"""

from __future__ import annotations

from src.embed_store import build_index, get_collection
from src.pipeline import answer_question

# (question, set of acceptable source files - hit if ANY appears in top-k)
EVAL_SET = [
    (
        "What do students say about Professor Carol Ligarski's workload and difficulty?",
        {"rmp_professor_a.txt"},
    ),
    (
        "Which professor in the documents seems most beginner-friendly for math?",
        {"rmp_professor_b.txt"},
    ),
    (
        "What do students say about class sizes and professor accessibility at Springfield College?",
        {"unigo_academics.txt", "niche_academics_reviews.txt"},
    ),
    (
        "Before choosing a class that seems easy, what should a student check first?",
        {"reddit_easy_classes.txt", "campus_classes_article.txt"},
    ),
    (
        "How should a beginner CS student prepare for programming exams?",
        {"discord_course_advice.txt", "course_advice.txt", "reddit_cs_professors.txt"},
    ),
]


def _ensure_index() -> None:
    try:
        get_collection()
    except Exception:
        print("Index not found - building it now...")
        n = build_index(reset=True)
        print(f"Indexed {n} chunks.\n")


def run() -> None:
    _ensure_index()
    passed = 0

    for i, (question, expected) in enumerate(EVAL_SET, 1):
        result = answer_question(question)
        retrieved_files = set(result.sources)
        hit = bool(expected & retrieved_files)
        passed += hit

        print("=" * 70)
        print(f"Q{i}: {question}")
        print(f"Expected any of : {sorted(expected)}")
        print(f"Retrieved files : {result.sources}")
        print(f"Result          : {'PASS' if hit else 'FAIL'}")
        print("-" * 70)
        print(result.answer)
        print()

    print("=" * 70)
    print(f"Retrieval score: {passed}/{len(EVAL_SET)} questions hit an expected source.")


if __name__ == "__main__":
    run()
