import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def default_story_expiry():
    return timezone.now() + timedelta(days=1)


class Post(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    image = models.URLField()
    caption = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    duration_ms = models.IntegerField(default=30000)

    class Meta:
        indexes = [models.Index(fields=["user", "created_at"]), models.Index(fields=["created_at"])]


class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="unique_user_post_like")]


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    likes_count = models.IntegerField(default=0)


class Follow(models.Model):
    STATUS_CHOICES = [("pending", "pending"), ("accepted", "accepted"), ("rejected", "rejected")]
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following_relations")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="follower_relations")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["follower", "following"], name="unique_follow_pair")]
        indexes = [models.Index(fields=["follower", "following", "status"])]


class Story(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    media_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_story_expiry)
    allow_remix = models.BooleanField(default=False)
    viewers = models.ManyToManyField(settings.AUTH_USER_MODEL, through="StoryView", related_name="viewed_stories")


class StoryView(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)


class Collection(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="collections")
    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=10, default="📁")
    embedding_cache = models.JSONField(default=dict, blank=True)
    post_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class SavedPost(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_posts")
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, blank=True)
    auto_categorized = models.BooleanField(default=False)
    ai_confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "collection"])]
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="unique_saved_post")]


class EngagementEvent(models.Model):
    EVENT_CHOICES = [("view", "view"), ("swipe", "swipe"), ("rewind", "rewind"), ("pause", "pause")]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="engagement_events")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session_id = models.UUIDField(default=uuid.uuid4)
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    timestamp_ms = models.IntegerField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["post", "event_type", "created_at"])]


class ChatRoom(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="chat_rooms")
    created_at = models.DateTimeField(auto_now_add=True)
    last_message = models.TextField(blank=True, default="")
    last_message_at = models.DateTimeField(null=True, blank=True)


class Message(models.Model):
    MEDIA_TYPES = [("image", "image"), ("video", "video"), ("audio", "audio")]
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(blank=True, default="")
    media_url = models.URLField(blank=True, default="")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, blank=True, default="")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_notifications")
    notification_type = models.CharField(max_length=50)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class PostInsight(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="insights")
    insight_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
