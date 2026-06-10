from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    ChatRoom,
    Collection,
    Comment,
    Message,
    Notification,
    Post,
    SavedPost,
    Story,
)

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "profile_picture", "avatar_url", "bio")

    def get_avatar_url(self, obj):
        return obj.profile_picture or f"https://api.dicebear.com/7.x/notionists/svg?seed={obj.username}"


class CommentSerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "user", "content", "parent", "likes_count", "created_at")


class PostSerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "user",
            "image",
            "caption",
            "created_at",
            "likes_count",
            "comments_count",
            "duration_ms",
            "is_liked",
            "is_saved",
        )
        read_only_fields = ("user", "likes_count", "comments_count", "created_at")

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()

    def get_is_saved(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return SavedPost.objects.filter(user=request.user, post=obj).exists()


class StorySerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)
    viewed = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = ("id", "user", "media_url", "created_at", "expires_at", "allow_remix", "viewed")

    def get_viewed(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.storyview_set.filter(user=request.user).exists()


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = "__all__"
        read_only_fields = ("user", "post_count", "created_at")


class SavedPostSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)

    class Meta:
        model = SavedPost
        fields = "__all__"
        read_only_fields = ("user", "auto_categorized", "ai_confidence", "created_at")


class MessageSerializer(serializers.ModelSerializer):
    sender = UserBriefSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "room", "sender", "content", "media_url", "media_type", "is_read", "created_at")


class ChatRoomSerializer(serializers.ModelSerializer):
    participants = UserBriefSerializer(many=True, read_only=True)
    other_user = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ("id", "participants", "other_user", "last_message", "last_message_at", "unread_count", "created_at")

    def get_other_user(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        other = obj.participants.exclude(id=request.user.id).first()
        return UserBriefSerializer(other).data if other else None

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if not request:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=request.user).count()


class NotificationSerializer(serializers.ModelSerializer):
    sender = UserBriefSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ("id", "sender", "notification_type", "post", "comment", "is_read", "created_at")
