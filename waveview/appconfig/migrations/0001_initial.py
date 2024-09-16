# Generated by Django 4.2.14 on 2024-09-16 06:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('inventory', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('volcano', '0001_initial'),
        ('event', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MagnitudeConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('method', models.CharField(max_length=255)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('data', models.JSONField(blank=True, default=dict, null=True)),
                ('is_enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('volcano', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='volcano.volcano')),
            ],
            options={
                'verbose_name': 'magnitude',
                'verbose_name_plural': 'magnitude',
            },
        ),
        migrations.CreateModel(
            name='PickerConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('data', models.JSONField(blank=True, default=dict, null=True)),
                ('is_preferred', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('volcano', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='volcano.volcano')),
            ],
            options={
                'verbose_name': 'picker',
                'verbose_name_plural': 'picker',
            },
        ),
        migrations.CreateModel(
            name='SeismogramConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('component', models.CharField(choices=[('Z', 'Vertical'), ('N', 'North'), ('E', 'East')], default='Z', max_length=32)),
                ('data', models.JSONField(blank=True, default=dict, null=True)),
                ('picker_config', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='seismogram_config', to='appconfig.pickerconfig')),
            ],
            options={
                'verbose_name': 'seismogram',
                'verbose_name_plural': 'seismogram',
            },
        ),
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
            name='HelicorderConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('color', models.CharField(blank=True, max_length=32, null=True)),
                ('color_light', models.CharField(blank=True, max_length=32, null=True)),
                ('color_dark', models.CharField(blank=True, max_length=32, null=True)),
                ('data', models.JSONField(blank=True, default=dict, null=True)),
                ('channel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.channel')),
                ('picker_config', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='helicorder_config', to='appconfig.pickerconfig')),
            ],
            options={
                'verbose_name': 'helicorder',
                'verbose_name_plural': 'helicorder',
            },
        ),
        migrations.CreateModel(
            name='StationMagnitudeConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('data', models.JSONField(blank=True, default=dict, null=True)),
                ('is_enabled', models.BooleanField(default=True)),
                ('channel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='inventory.channel')),
                ('magnitude_config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='station_magnitude_configs', to='appconfig.magnitudeconfig')),
            ],
            options={
                'verbose_name': 'station magnitude',
                'verbose_name_plural': 'station magnitude',
                'unique_together': {('magnitude_config', 'channel')},
            },
        ),
        migrations.CreateModel(
            name='SeismogramStationConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('color', models.CharField(blank=True, max_length=32, null=True)),
                ('color_light', models.CharField(blank=True, max_length=32, null=True)),
                ('color_dark', models.CharField(blank=True, max_length=32, null=True)),
                ('order', models.IntegerField(default=0)),
                ('seismogram_config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='station_configs', to='appconfig.seismogramconfig')),
                ('station', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.station')),
            ],
            options={
                'verbose_name': 'seismogram station',
                'verbose_name_plural': 'seismogram station',
                'ordering': ('order',),
                'unique_together': {('seismogram_config', 'station')},
            },
        ),
    ]
