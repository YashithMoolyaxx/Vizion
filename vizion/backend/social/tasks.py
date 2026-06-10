from datetime import timedelta

from celery import shared_task
from django.db import connection
from django.utils import timezone

from .models import Collection, EngagementEvent, Post, PostInsight, SavedPost, Story


def get_icon_for_category(category):
    icons = {
        "Recipes": "🍳",
        "Travel": "✈️",
        "Memes": "😂",
        "Fashion": "👗",
        "Quotes": "💬",
        "Fitness": "💪",
        "Tech": "💻",
    }
    return icons.get(category, "📁")


@shared_task
def auto_categorize_saved_post(user_id, post_id, caption_text):
    categories = {
        "Recipes": ["recipe", "food", "cooking", "pasta", "dinner", "lunch", "breakfast"],
        "Travel": ["travel", "trip", "vacation", "beach", "mountain", "hotel", "flight"],
        "Memes": ["meme", "funny", "lol", "hilarious", "joke", "comedy"],
        "Fashion": ["outfit", "dress", "shoes", "fashion", "style", "clothing"],
        "Quotes": ["quote", "motivation", "inspiring", "success", "life", "wisdom"],
        "Fitness": ["workout", "gym", "fitness", "exercise", "yoga", "running"],
        "Tech": ["coding", "programming", "developer", "tech", "software", "ai"],
    }
    caption_lower = caption_text.lower() if caption_text else ""
    matched_category = None
    highest_score = 0
    for category, keywords in categories.items():
        score = sum(1 for keyword in keywords if keyword in caption_lower)
        if score > highest_score and score > 0:
            highest_score = score
            matched_category = category

    if matched_category:
        collection, _ = Collection.objects.get_or_create(
            user_id=user_id, name=matched_category, defaults={"icon": get_icon_for_category(matched_category)}
        )
        confidence = min(0.7 + (highest_score * 0.05), 0.95)
    else:
        collection, _ = Collection.objects.get_or_create(user_id=user_id, name="Unsorted", defaults={"icon": "📁"})
        confidence = 0.3

    SavedPost.objects.filter(user_id=user_id, post_id=post_id).update(
        collection=collection, auto_categorized=True, ai_confidence=confidence
    )
    collection.post_count = SavedPost.objects.filter(collection=collection).count()
    collection.save(update_fields=["post_count"])


@shared_task
def generate_post_insights():
    recent_posts = Post.objects.filter(created_at__gte=timezone.now() - timedelta(hours=24))
    for post in recent_posts:
        total_views = EngagementEvent.objects.filter(post=post, event_type="view").values("user_id").distinct().count()
        if total_views < 100:
            continue
        duration = post.duration_ms or 30000
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT FLOOR(timestamp_ms / %s) as bucket, COUNT(DISTINCT user_id) as viewers
                FROM social_engagementevent
                WHERE post_id = %s AND event_type = 'view'
                GROUP BY bucket
                ORDER BY viewers ASC LIMIT 1
                """,
                [max(1, duration // 20), post.id],
            )
            worst = cursor.fetchone()
        if worst:
            insight = f"⚠️ Bucket {worst[0] + 1} lost viewers. Consider adding a hook here."
            PostInsight.objects.create(post=post, insight_text=insight)


@shared_task
def cleanup_expired_stories():
    Story.objects.filter(expires_at__lte=timezone.now()).delete()
