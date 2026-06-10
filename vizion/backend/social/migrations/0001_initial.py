import datetime
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


def default_story_expiry():
    return django.utils.timezone.now() + datetime.timedelta(days=1)


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Post",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.URLField()),
                ("caption", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("likes_count", models.IntegerField(default=0)),
                ("comments_count", models.IntegerField(default=0)),
                ("duration_ms", models.IntegerField(default=30000)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="posts", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="ChatRoom",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_message", models.TextField(blank=True, default="")),
                ("last_message_at", models.DateTimeField(blank=True, null=True)),
                ("participants", models.ManyToManyField(related_name="chat_rooms", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Collection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50)),
                ("icon", models.CharField(default="📁", max_length=10)),
                ("embedding_cache", models.JSONField(blank=True, default=dict)),
                ("post_count", models.IntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="collections", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Comment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("likes_count", models.IntegerField(default=0)),
                ("parent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="replies", to="social.comment")),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="comments", to="social.post")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="EngagementEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_id", models.UUIDField(default=uuid.uuid4)),
                ("event_type", models.CharField(choices=[("view", "view"), ("swipe", "swipe"), ("rewind", "rewind"), ("pause", "pause")], max_length=20)),
                ("timestamp_ms", models.IntegerField()),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="engagement_events", to="social.post")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Follow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "pending"), ("accepted", "accepted"), ("rejected", "rejected")], default="pending", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("follower", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="following_relations", to=settings.AUTH_USER_MODEL)),
                ("following", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="follower_relations", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Like",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="likes", to="social.post")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField()),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("room", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="social.chatroom")),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="PostInsight",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("insight_text", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="insights", to="social.post")),
            ],
        ),
        migrations.CreateModel(
            name="Story",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("media_url", models.URLField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(default=default_story_expiry)),
                ("allow_remix", models.BooleanField(default=False)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="StoryView",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("viewed_at", models.DateTimeField(auto_now_add=True)),
                ("story", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="social.story")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("notification_type", models.CharField(max_length=50)),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("comment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="social.comment")),
                ("post", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="social.post")),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sent_notifications", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="SavedPost",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("auto_categorized", models.BooleanField(default=False)),
                ("ai_confidence", models.FloatField(default=0.0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("collection", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="social.collection")),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="social.post")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="saved_posts", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name="story",
            name="viewers",
            field=models.ManyToManyField(related_name="viewed_stories", through="social.StoryView", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(model_name="post", index=models.Index(fields=["user", "created_at"], name="social_post_user_id_2894ca_idx")),
        migrations.AddIndex(model_name="post", index=models.Index(fields=["created_at"], name="social_post_created_0edfdc_idx")),
        migrations.AddIndex(model_name="follow", index=models.Index(fields=["follower", "following", "status"], name="social_foll_followe_bf64a7_idx")),
        migrations.AddIndex(model_name="savedpost", index=models.Index(fields=["user", "collection"], name="social_save_user_id_9bc6db_idx")),
        migrations.AddIndex(model_name="engagementevent", index=models.Index(fields=["post", "event_type", "created_at"], name="social_enga_post_id_b77523_idx")),
        migrations.AddConstraint(model_name="follow", constraint=models.UniqueConstraint(fields=("follower", "following"), name="unique_follow_pair")),
        migrations.AddConstraint(model_name="like", constraint=models.UniqueConstraint(fields=("user", "post"), name="unique_user_post_like")),
        migrations.AddConstraint(model_name="savedpost", constraint=models.UniqueConstraint(fields=("user", "post"), name="unique_saved_post")),
    ]
