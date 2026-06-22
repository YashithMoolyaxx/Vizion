import os
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import connection, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from users.serializers import UserSerializer

from .embeddings import refresh_post_embedding
from .feed_timeline import get_home_feed_posts
from .models import ChatRoom, Collection, Comment, EngagementEvent, Follow, Like, Message, Notification, Post, SavedPost, Story, StoryView
from .recommendations import build_user_interest_embedding, find_top_semantic_posts
from .serializers import (
    ChatRoomSerializer,
    CollectionSerializer,
    CommentSerializer,
    MessageSerializer,
    NotificationSerializer,
    PostSerializer,
    SavedPostSerializer,
    StorySerializer,
)
from .tasks import auto_categorize_saved_post, fanout_home_post, refresh_home_feed_after_follow_change, remove_creator_posts_from_feed
from .utils import broadcast_chat_message, create_chat_message, create_notification, get_dm_room

User = get_user_model()


class FeedPagination(PageNumberPagination):
    page_size = 20


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = FeedPagination

    def get_queryset(self):
        return Post.objects.select_related("user").order_by("-created_at")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

def perform_create(self, serializer):
        post = serializer.save(user=self.request.user)
        refresh_post_embedding(post)
        transaction.on_commit(lambda: fanout_home_post.delay(post.id))


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def home_feed(request):
    try:
        limit = max(1, min(int(request.query_params.get("limit", 20)), 50))
    except (TypeError, ValueError):
        limit = 20
    posts = get_home_feed_posts(request.user, limit=limit)
    serializer = PostSerializer(posts, many=True, context={"request": request})
    return Response(serializer.data)


feed = home_feed


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def semantic_feed(request):
    try:
        limit = max(1, min(int(request.query_params.get("limit", 20)), 50))
    except (TypeError, ValueError):
        limit = 20

    target_embedding = build_user_interest_embedding(request.user, limit=20)
    excluded_post_ids = set(
        Like.objects.filter(user=request.user).values_list("post_id", flat=True)
    ) | set(
        SavedPost.objects.filter(user=request.user).values_list("post_id", flat=True)
    )

    if target_embedding:
        posts = find_top_semantic_posts(
            target_embedding,
            limit=limit,
            exclude_user_id=request.user.id,
            exclude_post_ids=excluded_post_ids,
        )
    else:
        posts = list(
            Post.objects.exclude(user=request.user)
            .select_related("user")
            .order_by("-created_at")[:limit]
        )

    serializer = PostSerializer(posts, many=True, context={"request": request})
    return Response(serializer.data)


EXT_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/mp4": ".m4a",
    "audio/aac": ".aac",
}


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def upload_media(request):
    file = request.FILES.get("file")
    if not file:
        return Response({"detail": "file required"}, status=400)
    ext = os.path.splitext(file.name)[1].lower()
    if not ext:
        ext = EXT_BY_MIME.get(file.content_type, "")
    allowed = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif", ".mp4", ".webm", ".mov", ".mp3", ".wav", ".ogg", ".m4a", ".aac"}
    if ext not in allowed:
        return Response({"detail": f"unsupported file type ({ext or file.content_type})"}, status=400)
    name = f"uploads/{uuid.uuid4().hex}{ext}"
    path = default_storage.save(name, file)
    media_path = settings.MEDIA_URL + path
    url = request.build_absolute_uri(media_path)
    return Response({"url": url, "path": media_path})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related("user"), id=post_id)
    return Response(PostSerializer(post, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def list_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post, parent__isnull=True).select_related("user").order_by("-created_at")
    return Response(CommentSerializer(comments, many=True).data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def save_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    saved_post = SavedPost.objects.filter(user=request.user, post=post).first()
    
    if saved_post:
        # Unsave
        saved_post.delete()
        return Response({"is_saved": False}, status=status.HTTP_200_OK)
    else:
        # Save
        saved_post = SavedPost.objects.create(user=request.user, post=post)
        transaction.on_commit(lambda: auto_categorize_saved_post.delay(request.user.id, post.id, post.caption))
        return Response(SavedPostSerializer(saved_post, context={"request": request}).data, status=status.HTTP_201_CREATED)


class CollectionListView(generics.ListAPIView):
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user).order_by("-post_count", "name")


class CollectionPostsView(generics.ListAPIView):
    serializer_class = SavedPostSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = FeedPagination

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def get_queryset(self):
        return SavedPost.objects.filter(
            user=self.request.user, collection_id=self.kwargs["collection_id"]
        ).select_related("post", "post__user", "collection")


@api_view(["PUT"])
@permission_classes([permissions.IsAuthenticated])
def move_saved_post(request, saved_id):
    saved = get_object_or_404(SavedPost, id=saved_id, user=request.user)
    collection = get_object_or_404(Collection, id=request.data.get("collection_id"), user=request.user)
    old_collection = saved.collection
    saved.collection = collection
    saved.save(update_fields=["collection"])
    collection.post_count = SavedPost.objects.filter(collection=collection).count()
    collection.save(update_fields=["post_count"])
    if old_collection:
        old_collection.post_count = SavedPost.objects.filter(collection=old_collection).count()
        old_collection.save(update_fields=["post_count"])
    return Response(SavedPostSerializer(saved, context={"request": request}).data)

#post
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def batch_events(request):
    events = request.data.get("events", [])
    objs = []
    for event in events:
        objs.append(
            EngagementEvent(
                post_id=event["post_id"],
                user_id=request.user.id,
                session_id=event["session_id"],
                event_type=event["event_type"],
                timestamp_ms=event["timestamp_ms"],
                metadata=event.get("metadata", {}),
            )
        )
    if objs:
        EngagementEvent.objects.bulk_create(objs)
    post_ids = set(e["post_id"] for e in events) if events else set()
    for pid in post_ids:
        cache.delete(f"heatmap:{pid}")
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_heatmap(request, post_id):
    cache_key = f"heatmap:{post_id}"
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)
    post = get_object_or_404(Post, id=post_id)
    duration_ms = post.duration_ms or 30000
    bucket_size = max(1, duration_ms // 20)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                FLOOR(timestamp_ms / %s) as bucket,
                MIN(FLOOR(timestamp_ms / %s) * %s) as start_ms,
                MAX(FLOOR(timestamp_ms / %s) * %s + %s) as end_ms,
                COUNT(DISTINCT user_id) as viewers
            FROM social_engagementevent
            WHERE post_id = %s AND event_type = 'view'
            GROUP BY bucket
            ORDER BY bucket
            """,
            [bucket_size, bucket_size, bucket_size, bucket_size, bucket_size, bucket_size, post_id],
        )
        results = cursor.fetchall()

    heatmap = []
    total = 0
    for i, row in enumerate(results):
        bucket, start, end, viewers = row
        if i == 0:
            total = viewers
        retention = round(100 * viewers / total, 1) if total > 0 and i > 0 else 100.0
        heatmap.append(
            {
                "bucket": bucket + 1,
                "start_ms": int(start),
                "end_ms": int(end),
                "viewers": viewers,
                "retention": retention,
            }
        )
    response_data = {"heatmap": heatmap, "total_viewers": total}
    cache.set(cache_key, response_data, 300)
    return Response(response_data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if created:
        post.likes_count += 1
        post.save(update_fields=["likes_count"])
        create_notification(post.user, request.user, "like", post=post)
        return Response({"liked": True, "likes_count": post.likes_count})
    like.delete()
    post.likes_count = max(0, post.likes_count - 1)
    post.save(update_fields=["likes_count"])
    return Response({"liked": False, "likes_count": post.likes_count})


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    content = request.data.get("content", "").strip()
    if not content:
        return Response({"detail": "content required"}, status=400)
    parent_id = request.data.get("parent_id")
    parent = Comment.objects.filter(id=parent_id, post=post).first() if parent_id else None
    comment = Comment.objects.create(user=request.user, post=post, parent=parent, content=content)
    post.comments_count += 1
    post.save(update_fields=["comments_count"])
    create_notification(post.user, request.user, "comment", post=post, comment=comment)
    return Response(CommentSerializer(comment).data, status=201)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def follow_user(request, user_id):
    if user_id == request.user.id:
        return Response({"detail": "cannot follow yourself"}, status=400)
    target = get_object_or_404(User, id=user_id)
    follow = Follow.objects.filter(follower=request.user, following=target).first()

    if follow and follow.status == "accepted":
        follow.delete()
        target.followers_count = max(0, target.followers_count - 1)
        request.user.following_count = max(0, request.user.following_count - 1)
        target.save(update_fields=["followers_count"])
        request.user.save(update_fields=["following_count"])
        transaction.on_commit(lambda: remove_creator_posts_from_feed.delay(request.user.id, target.id))
        transaction.on_commit(lambda: refresh_home_feed_after_follow_change.delay(request.user.id))
        return Response({"following": False, "status": None})

    if follow and follow.status == "pending":
        follow.delete()
        return Response({"following": False, "status": None})

    if follow and follow.status == "rejected":
        follow.delete()

    status_value = "pending" if target.is_private else "accepted"
    follow = Follow.objects.create(follower=request.user, following=target, status=status_value)

    if status_value == "accepted":
        target.followers_count += 1
        request.user.following_count += 1
        target.save(update_fields=["followers_count"])
        request.user.save(update_fields=["following_count"])
        create_notification(target, request.user, "follow")
        transaction.on_commit(lambda: refresh_home_feed_after_follow_change.delay(request.user.id))

    return Response({"following": status_value == "accepted", "status": status_value, "id": follow.id})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(follower=request.user, following=user).first()
    is_following = bool(follow and follow.status == "accepted")
    posts_count = Post.objects.filter(user=user).count()
    data = UserSerializer(user).data
    data.update(
        {
            "is_following": is_following,
            "follow_status": follow.status if follow else None,
            "posts_count": posts_count,
            "is_me": user.id == request.user.id,
        }
    )
    if not data.get("avatar_url"):
        data["avatar_url"] = user.profile_picture or f"https://api.dicebear.com/7.x/notionists/svg?seed={user.username}"
    return Response(data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def user_posts(request, username):
    user = get_object_or_404(User, username=username)
    queryset = Post.objects.filter(user=user).select_related("user").order_by("-created_at")
    paginator = FeedPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = PostSerializer(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def search_users(request):
    q = request.query_params.get("q", "").strip()
    if not q:
        return Response([])
    users = User.objects.filter(Q(username__icontains=q) | Q(bio__icontains=q))[:20]
    return Response(UserSerializer(users, many=True).data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def stories_feed(request):
    following_ids = Follow.objects.filter(follower=request.user, status="accepted").values_list("following_id", flat=True)
    user_ids = list(following_ids) + [request.user.id]
    stories = (
        Story.objects.filter(user_id__in=user_ids, expires_at__gt=timezone.now())
        .select_related("user")
        .order_by("-created_at")
    )
    return Response(StorySerializer(stories, many=True, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_story(request):
    media_url = request.data.get("media_url")
    if not media_url:
        return Response({"detail": "media_url required"}, status=400)
    story = Story.objects.create(user=request.user, media_url=media_url, allow_remix=bool(request.data.get("allow_remix")))
    return Response(StorySerializer(story, context={"request": request}).data, status=201)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def view_story(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    StoryView.objects.get_or_create(user=request.user, story=story)
    return Response({"viewed": True})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def list_chat_rooms(request):
    rooms = ChatRoom.objects.filter(participants=request.user).prefetch_related("participants").order_by("-last_message_at", "-created_at")
    return Response(ChatRoomSerializer(rooms, many=True, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def get_or_create_dm(request):
    user_id = request.data.get("user_id")
    other = get_object_or_404(User, id=user_id)
    room = get_dm_room(request.user, other)
    return Response(ChatRoomSerializer(room, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def get_chat_room(request, room_id):
    room = get_object_or_404(ChatRoom.objects.prefetch_related("participants"), id=room_id, participants=request.user)
    return Response(ChatRoomSerializer(room, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def mark_room_read(request, room_id):
    get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    Message.objects.filter(room_id=room_id, is_read=False).exclude(sender=request.user).update(is_read=True)
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def list_messages(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    messages = room.messages.select_related("sender").order_by("created_at")
    paginator = FeedPagination()
    page = paginator.paginate_queryset(messages, request)
    if page is not None:
        return paginator.get_paginated_response(MessageSerializer(page, many=True).data)
    return Response(MessageSerializer(messages, many=True).data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def send_message(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    content = request.data.get("content", "").strip()
    media_url = request.data.get("media_url", "").strip()
    media_type = request.data.get("media_type", "").strip()
    if not content and not media_url:
        return Response({"detail": "content or media required"}, status=400)
    msg = create_chat_message(room, request.user, content=content, media_url=media_url, media_type=media_type)
    broadcast_chat_message(room_id, msg, request.user)
    other = room.participants.exclude(id=request.user.id).first()
    if other:
        create_notification(other, request.user, "message")
    return Response(MessageSerializer(msg).data, status=201)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def list_notifications(request):
    notifs = Notification.objects.filter(recipient=request.user).select_related("sender").order_by("-created_at")[:50]
    return Response(NotificationSerializer(notifs, many=True).data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def mark_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return Response({"status": "ok"})
