import hashlib
import json
import math
import os
import re
from typing import Iterable, Sequence
from urllib import error, request

EMBEDDING_DIMENSIONS = int(os.getenv("SEMANTIC_EMBEDDING_DIMENSIONS", "1536"))
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_EMBEDDING_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

TOKEN_RE = re.compile(r"[a-z0-9']+")
URL_RE = re.compile(r"https?://\S+")

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "have",
    "has",
    "he",
    "her",
    "his",
    "i",
    "in",
    "is",
    "it",
    "its",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "she",
    "so",
    "that",
    "the",
    "their",
    "them",
    "this",
    "to",
    "us",
    "we",
    "with",
    "you",
    "your",
}

CONCEPT_ALIASES = {
    "code": ("coding", "programming", "software", "developer", "tech"),
    "coding": ("programming", "software", "developer", "tech"),
    "developer": ("coding", "programming", "software", "tech"),
    "fitness": ("workout", "gym", "exercise", "health"),
    "food": ("recipe", "cooking", "meal", "dinner", "lunch"),
    "travel": ("trip", "vacation", "journey", "adventure"),
    "music": ("song", "audio", "playlist", "beat"),
    "photo": ("image", "picture", "camera", "visual"),
    "video": ("clip", "reel", "movie", "media"),
    "fashion": ("style", "outfit", "clothes", "wear"),
    "business": ("startup", "marketing", "founder", "entrepreneur"),
    "ai": ("artificial", "intelligence", "ml", "machine", "learning"),
    "art": ("design", "creative", "illustration", "drawing"),
}


def _normalize_text(text: str) -> str:
    cleaned = URL_RE.sub(" ", text or "")
    return re.sub(r"\s+", " ", cleaned.lower()).strip()


def _normalize_token(token: str) -> str:
    token = token.lstrip("#")
    if len(token) > 4 and token.endswith("ing"):
        token = token[:-3]
    elif len(token) > 3 and token.endswith("ed"):
        token = token[:-2]
    elif len(token) > 3 and token.endswith("s"):
        token = token[:-1]
    return token


def _tokenize(text: str) -> list[str]:
    tokens = []
    for raw_token in TOKEN_RE.findall(_normalize_text(text)):
        token = _normalize_token(raw_token)
        if token and token not in STOPWORDS:
            tokens.append(token)
    return tokens


def _feature_stream(text: str) -> list[tuple[str, float]]:
    tokens = _tokenize(text)
    features: list[tuple[str, float]] = []

    for token in tokens:
        features.append((f"tok:{token}", 1.0))
        for alias in CONCEPT_ALIASES.get(token, ()):
            features.append((f"alias:{alias}", 0.75))
        if len(token) > 3:
            features.append((f"suffix:{token[-3:]}", 0.25))

    for left, right in zip(tokens, tokens[1:]):
        features.append((f"bigram:{left}_{right}", 1.25))

    return features


def _hash_feature(feature: str) -> tuple[int, float]:
    digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=16).digest()
    index = int.from_bytes(digest[:8], "big") % EMBEDDING_DIMENSIONS
    sign = 1.0 if digest[8] % 2 == 0 else -1.0
    magnitude = 1.0 + (digest[9] / 255.0) * 0.5
    return index, sign * magnitude


def _normalize_vector(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if not norm:
        return [0.0 for _ in vector]
    return [value / norm for value in vector]


def local_text_embedding(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    for feature, weight in _feature_stream(text):
        index, contribution = _hash_feature(feature)
        vector[index] += contribution * weight
    return _normalize_vector(vector)


def generate_text_embedding(text: str) -> list[float]:
    normalized_text = text or ""
    if not normalized_text.strip():
        return [0.0] * EMBEDDING_DIMENSIONS

    if OPENAI_EMBEDDING_API_KEY:
        try:
            payload = json.dumps({"model": OPENAI_EMBEDDING_MODEL, "input": normalized_text}).encode("utf-8")
            req = request.Request(
                "https://api.openai.com/v1/embeddings",
                data=payload,
                headers={
                    "Authorization": f"Bearer {OPENAI_EMBEDDING_API_KEY}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
            embedding = data["data"][0]["embedding"]
            if len(embedding) == EMBEDDING_DIMENSIONS:
                return [float(value) for value in embedding]
        except (KeyError, IndexError, ValueError, error.URLError, TimeoutError, json.JSONDecodeError):
            pass

    return local_text_embedding(normalized_text)


def vector_norm(embedding: Sequence[float]) -> float:
    return math.sqrt(sum(float(value) * float(value) for value in embedding))


def average_embeddings(embeddings: Iterable[Sequence[float]]) -> list[float] | None:
    vectors = [list(map(float, embedding)) for embedding in embeddings if embedding]
    if not vectors:
        return None

    dimensions = len(vectors[0])
    averaged = [0.0] * dimensions
    for vector in vectors:
        if len(vector) != dimensions:
            continue
        for index, value in enumerate(vector):
            averaged[index] += value

    return _normalize_vector(averaged)


def build_post_embedding_text(post) -> str:
    caption = getattr(post, "caption", "") or ""
    return caption.strip()


def refresh_post_embedding(post) -> list[float]:
    embedding = generate_text_embedding(build_post_embedding_text(post))
    post.embedding = embedding
    post.embedding_norm = vector_norm(embedding)
    post.save(update_fields=["embedding", "embedding_norm"])
    return embedding
