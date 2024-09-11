# Generated by Django 4.2.14 on 2024-09-11 03:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid
import waveview.utils.media


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('volcano', '0001_initial'),
        ('inventory', '0001_initial'),
        ('organization', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Amplitude',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amplitude', models.FloatField(help_text='Measured amplitude value.')),
                ('type', models.CharField(blank=True, help_text='String that describes the type of amplitude.', max_length=50, null=True)),
                ('category', models.CharField(blank=True, choices=[('point', 'Point'), ('mean', 'Mean'), ('duration', 'Duration'), ('period', 'Period'), ('integral', 'Integral'), ('other', 'Other')], help_text='Category of the amplitude.', max_length=100, null=True)),
                ('time', models.DateTimeField(blank=True, help_text='Reference point in time or central point.', null=True)),
                ('begin', models.FloatField(blank=True, help_text='Duration of time interval before reference point in time window.', null=True)),
                ('end', models.FloatField(blank=True, help_text='Duration of time interval after reference point in time window.', null=True)),
                ('snr', models.FloatField(blank=True, help_text='Signal-to-noise ratio of the spectrogram at the location the amplitude was measured.', null=True)),
                ('unit', models.CharField(blank=True, help_text='Unit of the amplitude value.', max_length=255, null=True)),
                ('method', models.CharField(blank=True, max_length=255, null=True)),
                ('evaluation_mode', models.CharField(blank=True, choices=[('automatic', 'Automatic'), ('manual', 'Manual')], max_length=255, null=True)),
                ('is_preferred', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'amplitude',
                'verbose_name_plural': 'amplitudes',
            },
        ),
        migrations.CreateModel(
            name='Catalog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Catalog name.', max_length=200)),
                ('description', models.TextField(blank=True, default='', help_text='Catalog description.', null=True)),
                ('is_default', models.BooleanField(default=False, help_text='Whether the catalog is the default for volcano.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='catalogs', related_query_name='catalog', to=settings.AUTH_USER_MODEL)),
                ('volcano', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='catalogs', related_query_name='catalog', to='volcano.volcano')),
            ],
            options={
                'verbose_name': 'catalog',
                'verbose_name_plural': 'catalogs',
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('time', models.DateTimeField(blank=True, db_index=True, help_text='Event time.', null=True)),
                ('duration', models.FloatField(blank=True, help_text='Event duration.', null=True)),
                ('type_certainty', models.CharField(blank=True, choices=[('known', 'Known'), ('suspected', 'Suspected'), ('damaging', 'Damaging'), ('felt', 'Felt')], help_text='Event type certainty.', max_length=255, null=True)),
                ('note', models.TextField(blank=True, default='', help_text='Additional event information.', null=True)),
                ('method', models.CharField(blank=True, db_index=True, help_text='Method used to determine the event.', max_length=255, null=True)),
                ('evaluation_mode', models.CharField(blank=True, choices=[('automatic', 'Automatic'), ('manual', 'Manual')], help_text='Evaluation mode of the event.', max_length=255, null=True)),
                ('evaluation_status', models.CharField(blank=True, choices=[('preliminary', 'Preliminary'), ('confirmed', 'Confirmed'), ('reviewed', 'Reviewed'), ('final', 'Final'), ('rejected', 'Rejected')], help_text='Evaluation status of the event.', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', related_query_name='event', to=settings.AUTH_USER_MODEL)),
                ('bookmarked_by', models.ManyToManyField(blank=True, related_name='bookmarked_events', related_query_name='bookmarked_event', to=settings.AUTH_USER_MODEL)),
                ('catalog', models.ForeignKey(help_text='Catalog to which the event belongs.', on_delete=django.db.models.deletion.CASCADE, related_name='events', related_query_name='event', to='event.catalog')),
                ('station_of_first_arrival', models.ForeignKey(blank=True, help_text='Station of first arrival.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.station')),
            ],
            options={
                'verbose_name': 'Event',
                'verbose_name_plural': 'Events',
            },
        ),
        migrations.CreateModel(
            name='Magnitude',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('magnitude', models.FloatField(help_text='\n            Resulting magnitude value from combining values of type\n            StationMagnitude. If no estimations are available, this value can\n            represent the reported magnitude.\n            ')),
                ('type', models.CharField(blank=True, help_text='Describes the type of magnitude.', max_length=50, null=True)),
                ('method', models.CharField(blank=True, help_text='Identifies the method of magnitude estimation.', max_length=255, null=True)),
                ('station_count', models.IntegerField(blank=True, help_text='Number of used stations for this magnitude computation.', null=True)),
                ('azimuthal_gap', models.FloatField(blank=True, help_text='Azimuthal gap for this magnitude computation in degrees.', null=True)),
                ('evaluation_status', models.CharField(blank=True, choices=[('preliminary', 'Preliminary'), ('confirmed', 'Confirmed'), ('reviewed', 'Reviewed'), ('final', 'Final'), ('rejected', 'Rejected')], max_length=255, null=True)),
                ('is_preferred', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='magnitudes', related_query_name='magnitude', to='event.event')),
            ],
            options={
                'verbose_name': 'magnitude',
                'verbose_name_plural': 'magnitudes',
            },
        ),
        migrations.CreateModel(
            name='StationMagnitude',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('magnitude', models.FloatField(help_text='Estimated magnitude.')),
                ('type', models.CharField(blank=True, help_text='Describes the type of magnitude.', max_length=255, null=True)),
                ('method', models.CharField(blank=True, help_text='Identifies the method of magnitude estimation.', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('amplitude', models.OneToOneField(help_text='Reference to the amplitude object.', on_delete=django.db.models.deletion.CASCADE, related_name='station_magnitude', related_query_name='station_magnitude', to='event.amplitude')),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'station magnitude',
                'verbose_name_plural': 'station magnitudes',
            },
        ),
        migrations.CreateModel(
            name='StationMagnitudeContribution',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('residual', models.FloatField(blank=True, help_text='Residual of the contribution to the station magnitude.', null=True)),
                ('weight', models.FloatField(blank=True, help_text='Weight of the contribution to the station magnitude.', null=True)),
                ('magnitude', models.ForeignKey(help_text='Magnitude value of the contribution to the station magnitude.', on_delete=django.db.models.deletion.CASCADE, related_name='station_magnitude_contributions', related_query_name='station_magnitude_contribution', to='event.magnitude')),
                ('station_magnitude', models.OneToOneField(help_text='Reference to the station magnitude object.', on_delete=django.db.models.deletion.CASCADE, to='event.stationmagnitude')),
            ],
            options={
                'verbose_name': 'station magnitude contribution',
                'verbose_name_plural': 'station magnitude contributions',
            },
        ),
        migrations.CreateModel(
            name='Origin',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('time', models.DateTimeField(blank=True, db_index=True, help_text='Origin time.', null=True)),
                ('latitude', models.FloatField(blank=True, help_text='Origin latitude.', null=True)),
                ('latitude_uncertainty', models.FloatField(blank=True, help_text='Origin latitude uncertainty.', null=True)),
                ('longitude', models.FloatField(blank=True, help_text='Origin longitude.', null=True)),
                ('longitude_uncertainty', models.FloatField(blank=True, help_text='Origin longitude uncertainty.', null=True)),
                ('depth', models.FloatField(blank=True, help_text='Origin depth.', null=True)),
                ('depth_uncertainty', models.FloatField(blank=True, help_text='Origin depth uncertainty.', null=True)),
                ('method', models.CharField(blank=True, db_index=True, help_text='Method used to determine the origin.', max_length=255, null=True)),
                ('earth_model', models.CharField(blank=True, help_text='Earth model used to determine the origin.', max_length=255, null=True)),
                ('evaluation_mode', models.CharField(blank=True, choices=[('automatic', 'Automatic'), ('manual', 'Manual')], max_length=255, null=True)),
                ('evaluation_status', models.CharField(blank=True, choices=[('preliminary', 'Preliminary'), ('confirmed', 'Confirmed'), ('reviewed', 'Reviewed'), ('final', 'Final'), ('rejected', 'Rejected')], max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_preferred', models.BooleanField(default=False)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='origins', related_query_name='origin', to='event.event')),
            ],
            options={
                'verbose_name': 'origin',
                'verbose_name_plural': 'origins',
            },
        ),
        migrations.AddField(
            model_name='magnitude',
            name='station_magnitudes',
            field=models.ManyToManyField(related_name='magnitude_contributions', related_query_name='magnitude_contribution', through='event.StationMagnitudeContribution', to='event.stationmagnitude'),
        ),
        migrations.CreateModel(
            name='EventType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(db_index=True, help_text='Event type code.', max_length=50)),
                ('name', models.CharField(blank=True, help_text='Event type name.', max_length=150, null=True)),
                ('description', models.TextField(blank=True, default='', help_text='Event type description.', null=True)),
                ('color', models.CharField(blank=True, help_text='Event type default color.', max_length=32, null=True)),
                ('color_light', models.CharField(blank=True, help_text='Event type light color.', max_length=32, null=True)),
                ('color_dark', models.CharField(blank=True, help_text='Event type dark color.', max_length=32, null=True)),
                ('observation_type', models.CharField(blank=True, choices=[('explosion', 'Explosion'), ('pyroclastic_flow', 'Pyroclastic Flow'), ('rockfall', 'Rockfall'), ('tectonic', 'Tectonic'), ('volcanic_emision', 'Volcanic Emision'), ('lahar', 'Lahar'), ('sound', 'Sound')], help_text='Type of observation for the event.', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_types', related_query_name='event_type', to='organization.organization')),
            ],
            options={
                'verbose_name': 'Event type',
                'verbose_name_plural': 'Event types',
                'unique_together': {('organization', 'code')},
            },
        ),
        migrations.AddField(
            model_name='event',
            name='type',
            field=models.ForeignKey(blank=True, help_text='Event type.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='events', related_query_name='event', to='event.eventtype'),
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('media_type', models.CharField(choices=[('photo', 'Photo'), ('video', 'Video'), ('audio', 'Audio'), ('document', 'Document'), ('other', 'Other')], max_length=255)),
                ('file', models.FileField(upload_to=waveview.utils.media.MediaPath('event-attachments'))),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to=waveview.utils.media.MediaPath('event-attachments'))),
                ('name', models.CharField(max_length=255)),
                ('size', models.PositiveIntegerField()),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('event', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attachments', related_query_name='attachment', to='event.event')),
            ],
            options={
                'verbose_name': 'Attachment',
                'verbose_name_plural': 'Attachments',
            },
        ),
        migrations.AddField(
            model_name='amplitude',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='amplitudes', related_query_name='amplitude', to='event.event'),
        ),
        migrations.AddField(
            model_name='amplitude',
            name='waveform',
            field=models.ForeignKey(blank=True, help_text='Identifies the waveform stream on which the amplitude was measured.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='inventory.channel'),
        ),
    ]
