====================
Picker Configuration
====================

Picker configuration is used to configure which stream to display in helicorder
and seismogram view, and to configure set of filters and related parameters for
the picker algorithm.

Picker configuration is stored in the database for particular volcano. In the
admin panel, you can create picker configuration in the APP CONFIG -> Picker
section.

Picker configuration type is defined in the
``waveview.appconfig.models.picker.PickerConfigData``. A user can also override
the picker configuration as its type is defined in the
``waveview.appconfig.models.picker.UserPickerConfigData``. For example, a user
can select which helicorder channel to display in the helicorder view, select
list of seismogram channels to display in the seismogram view, window size, and
more.

As configuration can be complex if it created manually, WaveView provides a
handy command to import the configuration from JSON data. You can see example of
the JSON data in the ``fixtures/picker-config.json``. It is more easier to write
channel ID using station and channel code and WaveView will translate it to the
actual channel UUID.

To import the configuration, you can run the following command:

.. code-block:: bash

    python manage.py update_picker_config <path-to-file> <org-slug> <volcano-slug>
