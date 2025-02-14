==============
Event Observer
==============

WaveView event observer is a mechanism to monitor changes with the event. It is
a way to listen to the event and take action when the event is triggered.

Several use cases for the event observer are:

- Calculating magnitude when a new event is created or updated.
- Sending event to another system like BMA or Cendana15.
- Triggering an alert when a new event is created.
- Logging event changes to a file.
- etc.

The class is defined in the ``waveview.event.observers.EventObserver``.
``EventObserver`` is a base class that needs to be inherited and implemented by
the user. After that, the observer need to be added in the
``waveview.settings.EVENT_OBSERVER_REGISTRY`` list. 

Current supported operations are:

- ``create(event_id: str, data: dict, **options)``: Triggered when a new event is created.
- ``update(event_id: str, data: dict, **options)``: Triggered when an existing event is updated.
- ``delete(event_id: str, data: dict, **options)``: Triggered when an existing event is deleted.

Each function receives the following parameters:

- ``event_id``: The event ID.

    You can use this ID to fetch the event data from the database. For example:

    .. code-block:: python

        from waveview.event.models import Event

        event = Event.objects.get(id=event_id)

- ``data``: Data passed when user register the observer in the Django admin.

    It can be any data that the user wants to pass to the observer. For example,
    if the user registers the observer with the following data:

    .. code-block:: python

        {
            "server_url": "http://localhost:8000",
            "api_key": "123456"
        }

    ``data`` will be a dictionary with the above value.
 
- ``**options``: Additional options that can be passed to the observer. 

The observer instance can be registered in the Django admin in the APP CONFIG
Event Observer section. Here is the step to register the observer:

1. Select volcano name in which the observer will be registered.

2. Fill the name with observer name attribute. If ``EventObserver.name`` is
   ``bma.sync``, the name should be ``bma.sync``.

3. Fill the data with the data that will be passed to the observer.

4. Make sure ``Is enabled`` is checked and uncheck ``Run async``. Run async is
   still in development.

5. Set the order of the observer. The observer with the lowest order will be
   executed first. For example, if the event need magnitude data, it should be
   ordered after the magnitude observer.

7. Fill the description with the text explaining what observer is doing
   (recommended).

8. Select the author of the observer (recommended).

9. Click the save button.

When the error raised in the observer, it will be logged in the Celery log file
from the storage directory. The next observer will still be executed.
