import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from .utils import create_chat_message, message_payload


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close()
            return

        self.user = user
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        is_member = await self._is_participant(user.id, self.room_id)
        if not is_member:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "presence", "user_id": user.id, "username": user.username, "online": True},
        )

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            if hasattr(self, "user"):
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {"type": "presence", "user_id": self.user.id, "username": self.user.username, "online": False},
                )

    async def receive(self, text_data):
        payload = json.loads(text_data)
        content = payload.get("content", "").strip()
        media_url = payload.get("media_url", "").strip()
        media_type = payload.get("media_type", "").strip()
        if not content and not media_url:
            return
        msg_data = await self._persist_message(self.user.id, self.room_id, content, media_url, media_type)
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", **msg_data},
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def presence(self, event):
        if event.get("user_id") != getattr(self.user, "id", None):
            await self.send(text_data=json.dumps({"type": "presence", **event}))

    @sync_to_async
    def _is_participant(self, user_id, room_id):
        from .models import ChatRoom

        return ChatRoom.objects.filter(id=room_id, participants__id=user_id).exists()

    @sync_to_async
    def _persist_message(self, user_id, room_id, content, media_url, media_type):
        from .models import ChatRoom

        room = ChatRoom.objects.get(id=room_id)
        sender = room.participants.get(id=user_id)
        msg = create_chat_message(room, sender, content=content, media_url=media_url, media_type=media_type)
        return message_payload(msg, sender)


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close()
            return
        self.user = user
        self.group_name = f"notif_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notify(self, event):
        await self.send(text_data=json.dumps(event["payload"]))
