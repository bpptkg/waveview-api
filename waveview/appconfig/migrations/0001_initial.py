# Generated by Django 4.2.16 on 2024-09-24 09:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('event', '0001_initial'),
        ('organization', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('volcano', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SeismicityConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('order', models.IntegerField(default=0, help_text='Order of the seismicity config in the list.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='event.eventtype')),
                ('volcano', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='volcano.volcano')),
            ],
            options={
                'verbose_name': 'seismicity',
                'verbose_name_plural': 'seismicity',
            },
        ),
        migrations.CreateModel(
            name='PickerConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('data', models.JSONField(blank=True, default=dict, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='organization.organization')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('volcano', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='volcano.volcano')),
            ],
            options={
                'verbose_name': 'picker',
                'verbose_name_plural': 'picker',
            },
        ),
        migrations.CreateModel(
            name='HypocenterConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('is_preferred', models.BooleanField(default=False)),
                ('data', models.JSONField(blank=True, default=dict, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('event_types', models.ManyToManyField(blank=True, to='event.eventtype')),
                ('volcano', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='volcano.volcano')),
            ],
            options={
                'verbose_name': 'hypocenter',
                'verbose_name_plural': 'hypocenter',
            },
        ),
        migrations.CreateModel(
            name='EventObserverConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Name of the registered event observer adapter class.', max_length=255)),
                ('data', models.JSONField(blank=True, default=dict, help_text='Configuration data for the event observer.', null=True)),
                ('is_enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('volcano', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='volcano.volcano')),
            ],
            options={
                'verbose_name': 'event observer',
                'verbose_name_plural': 'event observer',
            },
        ),
    ]
