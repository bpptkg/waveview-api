# Generated by Django 4.2.14 on 2024-09-16 06:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields
import uuid
import waveview.utils.media


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organization', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Volcano',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('slug', models.SlugField(max_length=200)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, default='', null=True)),
                ('elevation', models.FloatField(blank=True, null=True)),
                ('location', models.TextField(blank=True, default='', null=True)),
                ('country', django_countries.fields.CountryField(blank=True, max_length=2, null=True)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('type', models.CharField(blank=True, max_length=100, null=True)),
                ('last_eruption_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(blank=True, max_length=50, null=True)),
                ('vei', models.IntegerField(blank=True, null=True)),
                ('nearby_population', models.IntegerField(blank=True, null=True)),
                ('hazard_level', models.CharField(blank=True, max_length=50, null=True)),
                ('monitoring_status', models.CharField(blank=True, max_length=50, null=True)),
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
                ('file', models.FileField(upload_to=waveview.utils.media.MediaPath('volcano-media'), max_length=255)),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to=waveview.utils.media.MediaPath('volcano-media'), max_length=255)),
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
        migrations.CreateModel(
            name='DigitalElevationModel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to=waveview.utils.media.MediaPath('digital-elevation-models'), max_length=255)),
                ('type', models.CharField(blank=True, max_length=50, null=True)),
                ('name', models.CharField(blank=True, max_length=200, null=True)),
                ('size', models.PositiveBigIntegerField(blank=True, null=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('utm_zone', models.CharField(blank=True, max_length=10, null=True)),
                ('x_min', models.FloatField(blank=True, null=True)),
                ('x_max', models.FloatField(blank=True, null=True)),
                ('y_min', models.FloatField(blank=True, null=True)),
                ('y_max', models.FloatField(blank=True, null=True)),
                ('z_min', models.FloatField(blank=True, null=True)),
                ('z_max', models.FloatField(blank=True, null=True)),
                ('resolution', models.FloatField(blank=True, null=True)),
                ('crs', models.CharField(blank=True, max_length=50, null=True)),
                ('data_source', models.CharField(blank=True, max_length=200, null=True)),
                ('acquisition_date', models.DateField(blank=True, null=True)),
                ('processing_method', models.TextField(blank=True, null=True)),
                ('is_default', models.BooleanField(default=False)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('volcano', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='digital_elevation_models', related_query_name='digital_elevation_model', to='volcano.volcano')),
            ],
            options={
                'verbose_name': 'digital elevation model',
                'verbose_name_plural': 'digital elevation models',
            },
        ),
    ]
