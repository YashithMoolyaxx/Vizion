from django.contrib import admin

from .models import (
    ChatRoom,
    Collection,
    Comment,
    EngagementEvent,
    Follow,
    Like,
    Message,
    Notification,
    Post,
    PostInsight,
    SavedPost,
    Story,
    StoryView,
)

admin.site.register(Post)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Follow)
admin.site.register(Story)
admin.site.register(StoryView)
admin.site.register(Collection)
admin.site.register(SavedPost)
admin.site.register(EngagementEvent)
admin.site.register(ChatRoom)
admin.site.register(Message)
admin.site.register(Notification)
admin.site.register(PostInsight)
