"""
Milestone 5 - Generation.

Builds a grounded prompt from the retrieved chunks and sends it to the
configured LLM backend. The system prompt forces the model to:
  - answer ONLY from the retrieved context,
  - cite the source files it used,
  - use hedged language ("the available reviews suggest..."),
  - say it doesn't know when the context is insufficient.

Backends: "openai", "anthropic", or "offline" (no API key required).
The offline backend returns an extractive, fully-cited answer so the whole
pipeline is testable without any external service.
"""

from __future__ import annotations

import os
import textwrap

from . import config
from .retrieve import RetrievedChunk

SYSTEM_PROMPT = textwrap.dedent(
    """\
    You are the Unofficial Course & Professor Guide for Springfield College.
    You answer student questions using ONLY the provided student-generated
    sources (Rate My Professors reviews, Reddit threads, college review sites,
    and student advice forums).

    Rules:
    1. Use ONLY the information in the CONTEXT below. Do not use outside
       knowledge and do not invent professors, courses, or facts.
    2. These are subjective student opinions. Use careful, hedged wording such
       as "students in the collected sources suggest" or "the available
       reviews indicate". Never state opinions as absolute fact.
    3. Cite the source file(s) you used, e.g. (rmp_professor_b.txt).
    4. If the context does not contain enough information to answer, say so
       plainly: "The available sources do not contain enough information to
       answer this." Do not guess.
    """
)


def build_context_block(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks into a numbered, citable context block."""
    lines = []
    for i, rc in enumerate(chunks, 1):
        m = rc.metadata
        lines.append(
            f"[Source {i}] {m['title']} — {m['source_type']} "
            f"(file: {m['source_file']})\n{rc.text}"
        )
    return "\n\n".join(lines)


def build_user_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    return (
        f"CONTEXT:\n{build_context_block(chunks)}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer using only the context above, with citations."
    )


# --- Backends ----------------------------------------------------------------
def _chat_openai_compatible(api_key: str, base_url, model: str,
                            system: str, user: str) -> str:
    """Shared helper for any OpenAI-compatible chat API (OpenAI, Groq)."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


def _generate_openai(system: str, user: str) -> str:
    return _chat_openai_compatible(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=None,
        model=config.OPENAI_MODEL,
        system=system,
        user=user,
    )


def _generate_groq(system: str, user: str) -> str:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY not set. Run: export GROQ_API_KEY=\"gsk_...\""
        )
    return _chat_openai_compatible(
        api_key=key,
        base_url=config.GROQ_BASE_URL,
        model=config.GROQ_MODEL,
        system=system,
        user=user,
    )


def _generate_anthropic(system: str, user: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=600,
        temperature=0.2,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text.strip()


def _generate_offline(question: str, chunks: list[RetrievedChunk]) -> str:
    """
    No-LLM fallback: stitch the retrieved evidence into a hedged, cited
    answer. Lets you verify retrieval without paying for or configuring an LLM.
    """
    if not chunks:
        return "The available sources do not contain enough information to answer this."

    files = sorted({rc.metadata["source_file"] for rc in chunks})
    lines = [
        "Based only on the retrieved student sources, the available reviews "
        "indicate the following (this is an extractive, no-LLM answer):\n"
    ]
    for i, rc in enumerate(chunks, 1):
        snippet = " ".join(rc.text.split())
        if len(snippet) > 280:
            snippet = snippet[:280].rsplit(" ", 1)[0] + "..."
        lines.append(f"  {i}. {snippet} ({rc.metadata['source_file']})")
    lines.append("\nSources: " + ", ".join(files))
    return "\n".join(lines)


def generate_answer(question: str, chunks: list[RetrievedChunk]) -> str:
    """Generate a grounded answer using the configured backend."""
    backend = config.LLM_BACKEND.lower()

    if backend == "offline":
        return _generate_offline(question, chunks)

    user = build_user_prompt(question, chunks)
    if backend == "groq":
        return _generate_groq(SYSTEM_PROMPT, user)
    if backend == "openai":
        return _generate_openai(SYSTEM_PROMPT, user)
    if backend == "anthropic":
        return _generate_anthropic(SYSTEM_PROMPT, user)

    raise ValueError(f"Unknown LLM_BACKEND: {config.LLM_BACKEND!r}")
