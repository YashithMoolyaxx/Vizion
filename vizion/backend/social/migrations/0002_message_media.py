from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("social", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="media_url",
            field=models.URLField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="message",
            name="media_type",
            field=models.CharField(blank=True, choices=[("image", "image"), ("video", "video"), ("audio", "audio")], default="", max_length=10),
        ),
        migrations.AlterField(
            model_name="message",
            name="content",
            field=models.TextField(blank=True, default=""),
        ),
    ]
