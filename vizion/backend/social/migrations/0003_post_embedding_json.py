from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("social", "0002_message_media"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="embedding",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="post",
            name="embedding_norm",
            field=models.FloatField(default=0.0),
        ),
    ]
