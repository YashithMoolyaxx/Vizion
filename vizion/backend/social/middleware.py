from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@database_sync_to_async
def _get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            query = parse_qs(scope.get("query_string", b"").decode())
            token = query.get("token", [None])[0]
            if token:
                try:
                    access = AccessToken(token)
                    scope["user"] = await _get_user(access["user_id"])
                except (InvalidToken, TokenError, KeyError):
                    scope["user"] = AnonymousUser()
            elif scope.get("user") is None:
                scope["user"] = AnonymousUser()
        return await super().__call__(scope, receive, send)
