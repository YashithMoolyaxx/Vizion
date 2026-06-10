from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from social.models import Follow, Post

User = get_user_model()

DEMO_USERS = [
    {
        "username": "alex_creator",
        "email": "alex@vizion.demo",
        "bio": "Travel & food creator · documenting journeys",
        "profile_picture": "https://api.dicebear.com/7.x/notionists/svg?seed=alex_creator",
    },
    {
        "username": "maya_fitness",
        "email": "maya@vizion.demo",
        "bio": "Personal trainer · daily workout motivation",
        "profile_picture": "https://api.dicebear.com/7.x/notionists/svg?seed=maya_fitness",
    },
    {
        "username": "dev_jordan",
        "email": "jordan@vizion.demo",
        "bio": "Full-stack dev · building in public",
        "profile_picture": "https://api.dicebear.com/7.x/notionists/svg?seed=dev_jordan",
    },
    {
        "username": "luna_style",
        "email": "luna@vizion.demo",
        "bio": "Fashion & lifestyle · monochrome aesthetic",
        "profile_picture": "https://api.dicebear.com/7.x/notionists/svg?seed=luna_style",
    },
    {
        "username": "chef_omar",
        "email": "omar@vizion.demo",
        "bio": "Home chef · recipes & plating",
        "profile_picture": "https://api.dicebear.com/7.x/notionists/svg?seed=chef_omar",
    },
]

DEMO_POSTS = [
    ("alex_creator", "Sunset dinner by the beach #travel #food", "https://picsum.photos/seed/vizion-travel-1/900/900"),
    ("alex_creator", "Weekend pasta night #recipe #cooking", "https://picsum.photos/seed/vizion-food-2/900/900"),
    ("maya_fitness", "Morning workout complete #fitness #gym", "https://picsum.photos/seed/vizion-gym-1/900/900"),
    ("maya_fitness", "Yoga flow for beginners #wellness", "https://picsum.photos/seed/vizion-yoga-2/900/900"),
    ("dev_jordan", "Built with Django + React #tech #coding", "https://picsum.photos/seed/vizion-tech-1/900/900"),
    ("dev_jordan", "System design notes #developer #software", "https://picsum.photos/seed/vizion-code-2/900/900"),
    ("luna_style", "Monochrome outfit of the day #fashion #style", "https://picsum.photos/seed/vizion-fashion-1/900/900"),
    ("luna_style", "Minimal desk setup #aesthetic", "https://picsum.photos/seed/vizion-desk-2/900/900"),
    ("chef_omar", "Homemade ramen bowl #food #recipe", "https://picsum.photos/seed/vizion-ramen-1/900/900"),
    ("chef_omar", "Plating techniques 101 #cooking", "https://picsum.photos/seed/vizion-plate-2/900/900"),
]


class Command(BaseCommand):
    help = "Seed demo users and posts for Vizion"

    def handle(self, *args, **options):
        users = {}
        for data in DEMO_USERS:
            user, created = User.objects.update_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "bio": data["bio"],
                    "profile_picture": data["profile_picture"],
                },
            )
            if created:
                user.set_password("demo1234")
                user.save()
                self.stdout.write(f"Created user: {user.username}")
            users[user.username] = user

        for username, caption, image in DEMO_POSTS:
            user = users[username]
            if not Post.objects.filter(user=user, caption=caption).exists():
                Post.objects.create(user=user, caption=caption, image=image)
                self.stdout.write(f"Created post for {username}")

        # Cross-follow demo accounts so Following feed works
        names = list(users.keys())
        for i, uname in enumerate(names):
            follower = users[uname]
            for other_name in names:
                if other_name == uname:
                    continue
                Follow.objects.get_or_create(
                    follower=follower,
                    following=users[other_name],
                    defaults={"status": "accepted"},
                )

        self.stdout.write(self.style.SUCCESS("Demo seeded. Login: alex_creator / demo1234"))
