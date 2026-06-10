from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import ChatRoom, Message, Notification

User = get_user_model()


def get_dm_room(user1, user2):
    rooms = ChatRoom.objects.filter(participants=user1).filter(participants=user2)
    for room in rooms:
        if room.participants.count() == 2:
            return room
    room = ChatRoom.objects.create()
    room.participants.add(user1, user2)
    return room


def avatar_url(user):
    if user.profile_picture:
        return user.profile_picture
    return f"https://api.dicebear.com/7.x/notionists/svg?seed={user.username}"


def message_payload(msg, sender):
    return {
        "id": msg.id,
        "message": msg.content,
        "media_url": msg.media_url or "",
        "media_type": msg.media_type or "",
        "sender_id": sender.id,
        "sender_username": sender.username,
        "sender_avatar": avatar_url(sender),
        "created_at": msg.created_at.isoformat(),
    }


def broadcast_chat_message(room_id, msg, sender):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        f"chat_{room_id}",
        {"type": "chat_message", **message_payload(msg, sender)},
    )


def create_chat_message(room, sender, content="", media_url="", media_type=""):
    preview = content or ("📷 Photo" if media_type == "image" else "🎬 Video" if media_type == "video" else "🎵 Audio" if media_type == "audio" else "Message")
    msg = Message.objects.create(
        room=room,
        sender=sender,
        content=content,
        media_url=media_url,
        media_type=media_type,
    )
    room.last_message = preview[:120]
    room.last_message_at = timezone.now()
    room.save(update_fields=["last_message", "last_message_at"])
    return msg


def create_notification(recipient, sender, notification_type, post=None, comment=None):
    if recipient.id == sender.id:
        return
    notif = Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        post=post,
        comment=comment,
    )
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f"notif_{recipient.id}",
            {
                "type": "notify",
                "payload": {
                    "id": notif.id,
                    "notification_type": notification_type,
                    "sender": {"id": sender.id, "username": sender.username},
                    "post": post.id if post else None,
                    "created_at": notif.created_at.isoformat(),
                },
            },
        )
    return notif
