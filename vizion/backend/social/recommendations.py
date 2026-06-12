from heapq import heappush, heappushpop
from math import sqrt
from typing import Optional, Sequence, Tuple

from .embeddings import average_embeddings, generate_text_embedding, vector_norm
from .models import Like, Post, SavedPost


def _normalize_embedding(embedding: Sequence[float]) -> Tuple[float, ...]:
    if not embedding:
        raise ValueError("target_embedding is required")
    return tuple(float(value) for value in embedding)


def _vector_norm(embedding: Sequence[float]) -> float:
    return sqrt(sum(value * value for value in embedding))


def _cosine_similarity(target_embedding: Sequence[float], target_norm: float, candidate_embedding: Sequence[float], candidate_norm: float) -> float:
    if target_norm == 0.0 or candidate_norm == 0.0:
        return 0.0
    dot_product = sum(a * b for a, b in zip(target_embedding, candidate_embedding))
    return dot_product / (target_norm * candidate_norm)


def find_top_semantic_posts(
    target_embedding: Sequence[float],
    limit: int = 5,
    exclude_user_id: Optional[int] = None,
    exclude_post_ids: Optional[Sequence[int]] = None,
):
    if not target_embedding:
        return []

    normalized_target = _normalize_embedding(target_embedding)
    target_norm = _vector_norm(normalized_target)
    if target_norm == 0.0:
        return []

    top_matches = []
    target_size = len(normalized_target)
    excluded_ids = set(exclude_post_ids or [])

    queryset = Post.objects.filter(embedding__isnull=False, embedding_norm__gt=0).select_related("user").only(
        "id",
        "user",
        "image",
        "caption",
        "embedding",
        "embedding_norm",
        "created_at",
        "likes_count",
        "comments_count",
    ).order_by("-created_at")

    for post in queryset.iterator(chunk_size=500):
        if exclude_user_id and post.user_id == exclude_user_id:
            continue
        if post.id in excluded_ids:
            continue
        candidate_embedding = post.embedding or []
        if len(candidate_embedding) != target_size:
            continue

        candidate_norm = post.embedding_norm or _vector_norm(candidate_embedding)
        similarity = _cosine_similarity(normalized_target, target_norm, candidate_embedding, candidate_norm)
        candidate = (similarity, post.created_at, post.id, post)

        if len(top_matches) < limit:
            heappush(top_matches, candidate)
            continue

        if candidate > top_matches[0]:
            heappushpop(top_matches, candidate)

    ranked_matches = sorted(top_matches, key=lambda item: (item[0], item[1], item[2]), reverse=True)
    ranked_posts = [item[3] for item in ranked_matches]
    for post, (similarity, _, _, _) in zip(ranked_posts, ranked_matches):
        post.semantic_score = similarity
    return ranked_posts


def build_user_interest_embedding(user, limit: int = 20):
    recent_embeddings = []
    seen_post_ids = set()

    sources = (
        Like.objects.filter(user=user).select_related("post").order_by("-created_at"),
        SavedPost.objects.filter(user=user).select_related("post").order_by("-created_at"),
    )

    for source in sources:
        for item in source.iterator(chunk_size=100):
            post = item.post
            if post.id in seen_post_ids:
                continue
            seen_post_ids.add(post.id)
            embedding = post.embedding or generate_text_embedding(post.caption or "")
            if embedding and vector_norm(embedding) > 0:
                recent_embeddings.append(embedding)
            if len(recent_embeddings) >= limit:
                break
        if len(recent_embeddings) >= limit:
            break

    return average_embeddings(recent_embeddings)
