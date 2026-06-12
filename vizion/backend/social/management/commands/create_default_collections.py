from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from social.models import Collection

User = get_user_model()


class Command(BaseCommand):
    help = "Create default collections for users who don't have any"

    def handle(self, *args, **options):
        created_count = 0
        users_updated = 0

        for user in User.objects.all():
            if user.collections.exists():
                continue

            users_updated += 1
            Collection.objects.get_or_create(
                user=user,
                name="Favorites",
                defaults={"icon": "❤️"}
            )
            Collection.objects.get_or_create(
                user=user,
                name="Later",
                defaults={"icon": "🔖"}
            )
            Collection.objects.get_or_create(
                user=user,
                name="Inspiration",
                defaults={"icon": "💡"}
            )
            created_count += 3

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created collections for {users_updated} users ({created_count} collections total)"
            )
        )
