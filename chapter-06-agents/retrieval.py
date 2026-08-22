"""Embeddings and local cosine retrieval for the Chapter 5 corpus."""

import math
from dataclasses import dataclass

from openai import OpenAI, OpenAIError

from config import (
    EMBEDDING_MODEL,
    MAX_EVIDENCE_CHARS,
    MAX_RETRIEVED_CHUNKS,
    MIN_RETRIEVAL_SCORE,
)
from corpus import RubricChunk


class RetrievalError(Exception):
    """Raised when an embedding or retrieval operation cannot complete."""


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: RubricChunk
    score: float


@dataclass(frozen=True)
class EmbeddedCorpus:
    """A corpus and its cached vectors, kept together to avoid mismatches."""

    chunks: list[RubricChunk]
    embeddings: list[list[float]]


def embed_texts(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Embed a batch of non-empty strings with one configured model."""
    if not texts or any(not text.strip() for text in texts):
        raise RetrievalError("Embedding input must contain non-empty text.")
    try:
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    except OpenAIError as exc:
        raise RetrievalError("The rubric search failed. Please try again shortly.") from exc
    return [item.embedding for item in response.data]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity without adding a numerical dependency."""
    if len(left) != len(right) or not left:
        raise RetrievalError("Embedding vectors must be non-empty and the same length.")
    denominator = math.sqrt(sum(x * x for x in left)) * math.sqrt(sum(x * x for x in right))
    if denominator == 0:
        raise RetrievalError("Embedding vectors must not be zero vectors.")
    return sum(x * y for x, y in zip(left, right)) / denominator


def build_index(client: OpenAI, corpus: list[RubricChunk]) -> EmbeddedCorpus:
    """Embed curated chunks once for the life of the running app process."""
    if not corpus:
        raise RetrievalError("The rubric corpus is empty.")
    texts = [f"{chunk.role_family}\n{chunk.title}\n{chunk.text}" for chunk in corpus]
    return EmbeddedCorpus(chunks=corpus, embeddings=embed_texts(client, texts))


def rank_matches(
    query_embedding: list[float], index: EmbeddedCorpus, limit: int = MAX_RETRIEVED_CHUNKS
) -> list[RetrievedChunk]:
    """Rank an already-embedded query and enforce the calibrated fallback."""
    if not index.chunks or len(index.chunks) != len(index.embeddings):
        raise RetrievalError("The rubric index is empty or incomplete.")
    matches = [
        RetrievedChunk(chunk=chunk, score=cosine_similarity(query_embedding, vector))
        for chunk, vector in zip(index.chunks, index.embeddings)
    ]
    results = sorted(matches, key=lambda match: match.score, reverse=True)[:limit]
    if not results or results[0].score < MIN_RETRIEVAL_SCORE:
        raise RetrievalError(
            "I do not have a reliable curated rubric for that role yet. "
            "Try a supported role or use a more specific target role."
        )
    return results


def retrieve_rubrics(
    client: OpenAI,
    target_role: str,
    index: EmbeddedCorpus,
    limit: int = MAX_RETRIEVED_CHUNKS,
) -> list[RetrievedChunk]:
    """Return the most relevant rubric chunks for a target role."""
    if not target_role.strip():
        raise RetrievalError("Choose a target role before searching the rubric corpus.")
    query = f"Role-specific resume evaluation criteria for: {target_role.strip()}"
    query_embedding = embed_texts(client, [query])[0]
    return rank_matches(query_embedding, index, limit)


def format_evidence(matches: list[RetrievedChunk]) -> str:
    """Build a bounded, labeled evidence pack for the generation prompt."""
    parts = []
    total = 0
    for match in matches:
        block = (
            f"[RUBRIC {match.chunk.chunk_id}: {match.chunk.title}]\n"
            f"{match.chunk.text.strip()}"
        )
        if total + len(block) > MAX_EVIDENCE_CHARS:
            break
        parts.append(block)
        total += len(block)
    if not parts:
        raise RetrievalError("The retrieved evidence was empty after applying the size limit.")
    return "\n\n".join(parts)
