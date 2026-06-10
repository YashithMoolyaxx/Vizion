import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

from social.consumers import ChatConsumer, NotificationConsumer
from social.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddleware(
            AuthMiddlewareStack(
                URLRouter(
                    [
                        path("ws/chat/<int:room_id>/", ChatConsumer.as_asgi()),
                        path("ws/notifications/", NotificationConsumer.as_asgi()),
                    ]
                )
            )
        ),
    }
)
