from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True, default="")
    profile_picture = models.URLField(blank=True, default="")
    is_private = models.BooleanField(default=False)
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)

    REQUIRED_FIELDS = ["email"]
