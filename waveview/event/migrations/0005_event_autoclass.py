from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('event', '0004_alter_amplitude_method')]
    operations = [migrations.AddField(model_name='event', name='autoclass',
                                     field=models.JSONField(null=True, blank=True, editable=False))]
