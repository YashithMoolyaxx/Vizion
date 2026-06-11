from django.core.management.base import BaseCommand

from social.embeddings import refresh_post_embedding
from social.models import Post


class Command(BaseCommand):
    help = "Backfill and rebuild semantic embeddings for all posts."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=100, help="Number of posts to process per batch")

    def handle(self, *args, **options):
        batch_size = max(1, options["batch_size"])
        processed = 0
        updated = 0

        queryset = Post.objects.select_related("user").order_by("id")
        for post in queryset.iterator(chunk_size=batch_size):
            refresh_post_embedding(post)
            processed += 1
            updated += 1
            if updated % batch_size == 0:
                self.stdout.write(f"Updated {updated} posts...")

        self.stdout.write(self.style.SUCCESS(f"Rebuilt embeddings for {processed} posts."))
