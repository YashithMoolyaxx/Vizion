import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        user = request.user
        for field in ("bio", "profile_picture", "is_private"):
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
        return Response(UserSerializer(user).data)


class AvatarUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            url = request.data.get("profile_picture")
            if not url:
                return Response({"detail": "file or profile_picture url required"}, status=400)
            request.user.profile_picture = url
            request.user.save(update_fields=["profile_picture"])
            return Response(UserSerializer(request.user).data)

        ext = os.path.splitext(file.name)[1].lower()
        name = f"avatars/{uuid.uuid4().hex}{ext}"
        path = default_storage.save(name, file)
        url = request.build_absolute_uri(settings.MEDIA_URL + path)
        request.user.profile_picture = url
        request.user.save(update_fields=["profile_picture"])
        return Response(UserSerializer(request.user).data)
