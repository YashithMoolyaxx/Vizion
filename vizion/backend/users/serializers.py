from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


def default_avatar(username):
    return f"https://api.dicebear.com/7.x/notionists/svg?seed={username}"


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "bio",
            "profile_picture",
            "avatar_url",
            "is_private",
            "followers_count",
            "following_count",
        )

    def get_avatar_url(self, obj):
        return obj.profile_picture or default_avatar(obj.username)
