==============
Event Observer
==============

WaveView event observer is a mechanism to monitor changes with the event.
It is a way to listen to the event and take action when the event is triggered.
Current supported operations are:

- ``create``: Triggered when a new event is created.
- ``update``: Triggered when an existing event is updated.
- ``delete``: Triggered when an existing event is deleted.

The class is defined in the ``waveview.event.observers`` module.
``EventObserver`` is a base class that needs to be inherited and implemented by
the user. After that, the observer can be registered in the
``waveview.settings.EVENT_OBSERVER_REGISTRY`` list.

Several use cases for the event observer are:

- Calculating magnitude when a new event is created or updated.
- Sending event to another system like BMA or Cendana15.
- Triggering an alert when a new event is created.
- Logging event changes to a file.
- etc.
