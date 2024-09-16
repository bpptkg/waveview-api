# Generated by Django 4.2.14 on 2024-09-16 06:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
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
            name='Inventory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, default='', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='inventory', to='organization.organization')),
            ],
            options={
                'verbose_name': 'inventory',
                'verbose_name_plural': 'inventories',
            },
        ),
        migrations.CreateModel(
            name='Network',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(help_text='Network code, e.g. "VG"', max_length=64)),
                ('alternate_code', models.CharField(blank=True, help_text='A code used for display or association.', max_length=64, null=True)),
                ('start_date', models.DateTimeField(blank=True, help_text='Start date of network.', null=True)),
                ('end_date', models.DateTimeField(blank=True, help_text='End date of network.', null=True)),
                ('historical_code', models.CharField(blank=True, help_text='A previously used code if different from the current code.', max_length=64, null=True)),
                ('description', models.TextField(blank=True, default='', help_text='Network description.', null=True)),
                ('region', models.CharField(blank=True, help_text='Region of network.', max_length=255, null=True)),
                ('restricted_status', models.CharField(choices=[('open', 'Open'), ('close', 'Close'), ('partial', 'Partial')], default='open', help_text='Restricted status of network.', max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('inventory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='networks', related_query_name='network', to='inventory.inventory')),
            ],
            options={
                'verbose_name': 'network',
                'verbose_name_plural': 'networks',
            },
        ),
        migrations.CreateModel(
            name='Station',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(help_text='Station code.', max_length=64)),
                ('alternate_code', models.CharField(blank=True, help_text='Alternate code used for display or association.', max_length=64, null=True)),
                ('start_date', models.DateTimeField(blank=True, help_text='Start date of station.', null=True)),
                ('end_date', models.DateTimeField(blank=True, help_text='End date of station.', null=True)),
                ('historical_code', models.CharField(blank=True, help_text='Historical code of station.', max_length=64, null=True)),
                ('latitude', models.FloatField(blank=True, help_text='Station latitude, in degrees.', null=True)),
                ('longitude', models.FloatField(blank=True, help_text='Station longitude, in degrees.', null=True)),
                ('elevation', models.FloatField(blank=True, help_text='Station elevation, in meters.', null=True)),
                ('restricted_status', models.CharField(choices=[('open', 'Open'), ('close', 'Close'), ('partial', 'Partial')], default='open', help_text='Restricted status of station.', max_length=32)),
                ('description', models.TextField(blank=True, default='', help_text='Station description.', null=True)),
                ('place', models.CharField(blank=True, help_text='Place where the station is located.', max_length=255, null=True)),
                ('country', models.CharField(blank=True, help_text='Country where the station is located.', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('network', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stations', related_query_name='station', to='inventory.network')),
            ],
            options={
                'verbose_name': 'station',
                'verbose_name_plural': 'stations',
            },
        ),
        migrations.CreateModel(
            name='InventoryFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(blank=True, max_length=50, null=True)),
                ('file', models.FileField(upload_to=waveview.utils.media.MediaPath('inventories/'))),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('inventory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', related_query_name='file', to='inventory.inventory')),
            ],
            options={
                'verbose_name': 'inventory file',
                'verbose_name_plural': 'inventory files',
            },
        ),
        migrations.CreateModel(
            name='DataSource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('source', models.CharField(choices=[('seedlink', 'Seedlink'), ('scream', 'Scream'), ('arclink', 'Arclink'), ('fdsnws', 'FDSN Web Service'), ('earthworm', 'Earthworm'), ('winston', 'Winston Wave Server'), ('file', 'File')], max_length=50)),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('data', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('inventory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_sources', related_query_name='data_source', to='inventory.inventory')),
            ],
            options={
                'verbose_name': 'Data Source',
                'verbose_name_plural': 'Data Sources',
            },
        ),
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(help_text='Channel code.', max_length=64)),
                ('alternate_code', models.CharField(blank=True, help_text='Alternate code used for display or association.', max_length=64, null=True)),
                ('start_date', models.DateTimeField(blank=True, help_text='Start date of channel.', null=True)),
                ('end_date', models.DateTimeField(blank=True, help_text='End date of channel.', null=True)),
                ('historical_code', models.CharField(blank=True, help_text='Historical code of channel.', max_length=64, null=True)),
                ('location_code', models.CharField(help_text='Location code of channel.', max_length=64)),
                ('latitude', models.FloatField(help_text='\n            Latitude of this channel’s sensor, in degrees. Often the same as the\n            station latitude, but when different the channel latitude is the true\n            location of the sensor.\n            ')),
                ('longitude', models.FloatField(help_text='\n            Longitude of this channel’s sensor, in degrees. Often the same as the\n            station longitude, but when different the channel longitude is the true\n            location of the sensor.\n            ')),
                ('elevation', models.FloatField(help_text='Elevation of the sensor, in meters.')),
                ('depth', models.FloatField(help_text='The depth of the sensor relative to the local ground surface level, in meters.')),
                ('restricted_status', models.CharField(choices=[('open', 'Open'), ('close', 'Close'), ('partial', 'Partial')], default='open', help_text='Restricted status of channel.', max_length=32)),
                ('description', models.TextField(blank=True, default='', help_text='Channel description.', null=True)),
                ('azimuth', models.FloatField(blank=True, help_text='Azimuth of the component in degrees clockwise from geographic (true) north.', null=True)),
                ('dip', models.FloatField(blank=True, help_text='\n            Dip of the component in degrees, positive is down from horizontal.\n            For horizontal dip=0, for vertical upwards dip=-90 and for vertical\n            downwards dip=+90.\n            ', null=True)),
                ('water_level', models.FloatField(blank=True, help_text='\n            Elevation of the water surface in meters for underwater sites, where\n            0 is mean sea level. If you put an OBS on a lake bottom, where the\n            lake surface is at elevation=1200 meters, then you should set\n            WaterLevel=1200. An OBS in the ocean would have WaterLevel=0.\n            ', null=True)),
                ('sample_rate', models.FloatField(blank=True, help_text='Sample rate in samples per second.', null=True)),
                ('sample_rate_ratio_number_samples', models.IntegerField(blank=True, help_text='Integer number of samples that span a number of seconds.', null=True)),
                ('sample_rate_ratio_number_seconds', models.FloatField(blank=True, help_text='Integer number of seconds that span a number of samples.', null=True)),
                ('clock_drift', models.FloatField(blank=True, help_text='\n            A tolerance value, measured in seconds per sample, used as a\n            threshold for time error detection in data from the channel.\n            ', null=True)),
                ('calibration_units', models.CharField(blank=True, help_text='\n            Symbol or name of units, e.g. "m/s", "V", "Pa", "C".\n            ', max_length=64, null=True)),
                ('calibration_units_description', models.CharField(blank=True, help_text='\n            Description of units, e.g. "Velocity in meters per second", "Volts",\n            "Pascals", "Degrees Celsius".\n            ', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='channels', related_query_name='channel', to='inventory.station')),
            ],
            options={
                'verbose_name': 'channel',
                'verbose_name_plural': 'channels',
            },
        ),
    ]
