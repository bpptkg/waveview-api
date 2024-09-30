=====
Setup
=====

Once you have installed the package, we have to setup the application in the
admin panel.

Prior to setting up the application, you need to have the following information:

- Username and password of the superuser to access the admin panel.
- Inventory files containing seismic network information in the Station XML
  format. You can copy from SeisComP if you have configured the seismic network
  in SeisComP.
- Seedlink server IP address and port number.
- Event types and picker configuration.
- Organization and volcano information.

1. Create an new organization in the Organization section. This will also create
   an inventory to store the seismic network information.

2. Create a volcano under the organization in the Volcano section. Creating a
   volcano will also create a default catalog to store the picked events.

3. In the Inventory section, create a new inventory file. Select the Station XML
   (.xml) file that contains the seismic network information and upload it.
   WaveView will parse the file and store the network information in the
   inventory automatically.

4. In the Data Sources menu, create a new data source. Select the organization
   inventory, Seedlink data source, and set the data to the following
   configuration:

    .. code-block:: json

        {
            "server_url": "192.168.10.100:18000"
        }


5. Run the Seedlink command to start the data collection process. The command
   will start the Seedlink client and connect to the Seedlink server to collect
   the seismic data. Use organization inventory ID as the argument for the
   command.

    .. code-block:: bash

        python manage.py seedlink <inventory_id>

6. Create event types in the Event Type section. Event types are used to
   categorize the picked events. You can create multiple event types and assign
   them to the picked events.

   You can see the example of the event type configuration in the
   `fixture/event-types.json` file.

   You can upload the event type configuration using the following command:

    .. code-block:: bash

        python manage.py update_eventtypes fixture/event-types.json <org_slug>

7. Create a new picker configuration for the particular organization and
   volcano. You can see the example of the picker configuration in the
   `fixture/picker-config.json` file.

   You can upload the picker configuration using the following command:

    .. code-block:: bash

        python manage.py update_picker_config fixture/picker-config.json <org_slug> <volcano_slug>
