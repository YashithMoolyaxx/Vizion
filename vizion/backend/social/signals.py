from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Collection

User = get_user_model()


@receiver(post_save, sender=User)
def create_default_collections(sender, instance, created, **kwargs):
    """Create default collections when a new user is created."""
    if created:
        Collection.objects.get_or_create(
            user=instance,
            name="Favorites",
            defaults={"icon": "❤️"}
        )
        Collection.objects.get_or_create(
            user=instance,
            name="Later",
            defaults={"icon": "🔖"}
        )
        Collection.objects.get_or_create(
            user=instance,
            name="Inspiration",
            defaults={"icon": "💡"}
        )
