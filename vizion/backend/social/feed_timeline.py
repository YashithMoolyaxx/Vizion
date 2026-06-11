from __future__ import annotations

from datetime import timedelta
from functools import lru_cache
from typing import Iterable

import redis
from django.conf import settings
from django.utils import timezone

from .models import Follow, Post


@lru_cache(maxsize=1)
def get_feed_client():
    return redis.Redis.from_url(settings.REDIS_FEED_URL, decode_responses=True)


def feed_key(user_id: int) -> str:
    return f"feed:home:{user_id}"


def active_key(user_id: int) -> str:
    return f"feed:active:{user_id}"


def feed_index_key() -> str:
    return "feed:home:index"


def celebrity_threshold() -> int:
    return int(getattr(settings, "REDIS_FEED_CELEBRITY_THRESHOLD", 5000))


def active_ttl() -> int:
    return int(getattr(settings, "REDIS_FEED_ACTIVE_TTL", 60 * 60 * 24 * 7))


def lookback_days() -> int:
    return int(getattr(settings, "REDIS_FEED_LOOKBACK_DAYS", 7))


def cache_limit() -> int:
    return int(getattr(settings, "REDIS_FEED_CACHE_LIMIT", 1000))


def celebrity_lookup_limit() -> int:
    return int(getattr(settings, "REDIS_FEED_CELEBRITY_LOOKUP_LIMIT", 200))


def touch_feed_activity(user_id: int) -> None:
    client = get_feed_client()
    client.set(active_key(user_id), "1", ex=active_ttl())
    client.expire(feed_key(user_id), active_ttl())
    client.sadd(feed_index_key(), str(user_id))


def _store_posts(user_id: int, posts: Iterable[Post]) -> None:
    client = get_feed_client()
    mapping = {}
    for post in posts:
        if not post.created_at:
            continue
        mapping[str(post.id)] = float(post.created_at.timestamp())
    if not mapping:
        return
    pipe = client.pipeline(transaction=False)
    pipe.zadd(feed_key(user_id), mapping)
    pipe.sadd(feed_index_key(), str(user_id))
    pipe.execute()


def rebuild_home_feed_cache(user_id: int) -> None:
    client = get_feed_client()
    key = feed_key(user_id)
    client.delete(key)

    cutoff = timezone.now() - timedelta(days=lookback_days())
    regular_following_ids = list(
        Follow.objects.filter(
            follower_id=user_id,
            status="accepted",
            following__followers_count__lt=celebrity_threshold(),
        ).values_list("following_id", flat=True)
    )
    regular_following_ids.append(user_id)

    recent_posts = (
        Post.objects.filter(user_id__in=regular_following_ids, created_at__gte=cutoff)
        .only("id", "created_at")
        .order_by("-created_at")[: cache_limit()]
    )
    _store_posts(user_id, recent_posts)
    touch_feed_activity(user_id)


def _get_cached_post_items(user_id: int) -> list[tuple[int, float]]:
    client = get_feed_client()
    cached = client.zrevrange(feed_key(user_id), 0, cache_limit() - 1, withscores=True)
    return [(int(post_id), float(score)) for post_id, score in cached]


def _merge_post_ids(cached_items: list[tuple[int, float]], celebrity_posts: Iterable[Post]) -> list[int]:
    merged: dict[int, float] = {}
    for post_id, score in cached_items:
        merged[post_id] = max(merged.get(post_id, 0.0), score)
    for post in celebrity_posts:
        if not post.created_at:
            continue
        merged[post.id] = max(merged.get(post.id, 0.0), float(post.created_at.timestamp()))
    ordered = sorted(merged.items(), key=lambda item: (item[1], item[0]), reverse=True)
    return [post_id for post_id, _ in ordered]


def get_home_feed_posts(user, limit: int = 20) -> list[Post]:
    client = get_feed_client()
    key = feed_key(user.id)
    if not client.exists(active_key(user.id)) or not client.exists(key):
        rebuild_home_feed_cache(user.id)

    cached_items = _get_cached_post_items(user.id)
    celebrity_following_ids = list(
        Follow.objects.filter(
            follower=user,
            status="accepted",
            following__followers_count__gte=celebrity_threshold(),
        ).values_list("following_id", flat=True)
    )
    cutoff = timezone.now() - timedelta(days=lookback_days())
    celebrity_posts = (
        Post.objects.filter(user_id__in=celebrity_following_ids, created_at__gte=cutoff)
        .select_related("user")
        .only("id", "user", "image", "caption", "created_at", "likes_count", "comments_count", "duration_ms")
        .order_by("-created_at")[: celebrity_lookup_limit()]
    )

    ordered_ids = _merge_post_ids(cached_items, celebrity_posts)
    if not ordered_ids:
        return []

    selected_ids = ordered_ids[: max(limit, 1)]
    posts_by_id = Post.objects.filter(id__in=selected_ids).select_related("user")
    lookup = {post.id: post for post in posts_by_id}
    ordered_posts = [lookup[post_id] for post_id in selected_ids if post_id in lookup]
    touch_feed_activity(user.id)
    return ordered_posts


def fanout_post_to_home_feeds(post: Post) -> None:
    client = get_feed_client()
    author_key = feed_key(post.user_id)
    author_score = float(post.created_at.timestamp())
    pipe = client.pipeline(transaction=False)
    pipe.set(active_key(post.user_id), "1", ex=active_ttl())
    pipe.zadd(author_key, {str(post.id): author_score})
    pipe.expire(author_key, active_ttl())
    pipe.sadd(feed_index_key(), str(post.user_id))
    pipe.execute()

    if post.user.followers_count >= celebrity_threshold():
        return

    follower_ids = list(
        Follow.objects.filter(following_id=post.user_id, status="accepted").values_list("follower_id", flat=True)
    )
    if not follower_ids:
        return

    active_lookup = client.mget([active_key(follower_id) for follower_id in follower_ids])
    pipe = client.pipeline(transaction=False)
    for follower_id, marker in zip(follower_ids, active_lookup):
        if not marker:
            continue
        pipe.zadd(feed_key(follower_id), {str(post.id): author_score})
        pipe.sadd(feed_index_key(), str(follower_id))
    pipe.execute()


def rebuild_following_cache_after_relationship_change(user_id: int) -> None:
    rebuild_home_feed_cache(user_id)


def remove_creator_from_home_feed(follower_id: int, creator_id: int) -> None:
    client = get_feed_client()
    cutoff = timezone.now() - timezone.timedelta(days=lookback_days())
    post_ids = list(
        Post.objects.filter(user_id=creator_id, created_at__gte=cutoff).values_list("id", flat=True)
    )
    if not post_ids:
        return
    client.zrem(feed_key(follower_id), *[str(post_id) for post_id in post_ids])
