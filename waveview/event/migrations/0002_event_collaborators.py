# Generated by Django 4.2.16 on 2024-10-21 06:40

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('event', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='collaborators',
            field=models.ManyToManyField(blank=True, related_name='collaborated_events', related_query_name='collaborated_event', to=settings.AUTH_USER_MODEL),
        ),
    ]
