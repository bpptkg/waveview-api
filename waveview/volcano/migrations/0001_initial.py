# Generated by Django 4.2.14 on 2024-08-12 08:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields
import uuid
import waveview.utils.media


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Volcano',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, default='', null=True)),
                ('elevation', models.IntegerField(blank=True, null=True)),
                ('location', models.TextField(blank=True, default='', null=True)),
                ('country', django_countries.fields.CountryField(blank=True, max_length=2, null=True)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_default', models.BooleanField(default=False)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='volcanoes', related_query_name='volcano', to='organization.organization')),
            ],
            options={
                'verbose_name': 'volcano',
                'verbose_name_plural': 'volcanoes',
            },
        ),
        migrations.CreateModel(
            name='VolcanoMedia',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to=waveview.utils.media.MediaPath('volcano-media'))),
                ('name', models.CharField(blank=True, max_length=200, null=True)),
                ('size', models.PositiveBigIntegerField()),
                ('media_type', models.CharField(choices=[('photo', 'Photo'), ('video', 'Video'), ('audio', 'Audio'), ('document', 'Document'), ('other', 'Other')], max_length=50)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('volcano', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media', related_query_name='media', to='volcano.volcano')),
            ],
            options={
                'verbose_name': 'volcano media',
                'verbose_name_plural': 'volcano media',
            },
        ),
    ]
