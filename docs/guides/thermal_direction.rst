========================
Thermal RF/APG Direction
========================

After an RF or APG event is saved, WaveView waits about two minutes and then
classifies which river axis heated first. The result is written back onto the
WaveView event and, when possible, onto the related BMA bulletin.

The classifier follows the river sets used by BPPTKG:

- Kiri: Krasak, Boyong, Sat
- Kanan: Bebeng, Putih, Lamat, Senowo

Rivers outside those sets, including Kuning and Gendol, keep their river name
in ``hasil_akhir`` and use ``Tidak terdeteksi`` for ``arah``. If no river rises
at least 5°C above its pre-event median, both fields are ``Tidak terdeteksi``.

Enable the observer
===================

1. Set ``BMA_URL`` and ``BMA_API_KEY`` in the environment. The thermal request
   sends ``Authorization: Api-Key <BMA_API_KEY>``. Do not put the key in code.
2. Optional: ``THERMAL_DIRECTION_DELAY`` is the Celery countdown in seconds.
   The default is ``120``. An Event Observer Config ``data`` object may set
   ``delay`` to override that value for one volcano.
3. In Django admin, open App Config → Event Observer and add:

   - Name: ``bma.thermal_direction``
   - Is enabled: checked
   - Order: after the bulletin observer if the bulletin should exist first
   - Data: ``{}`` or ``{"delay": 120}``

The class must stay in ``EVENT_OBSERVER_REGISTRY``. Delete events are ignored.
Create and update both queue
``waveview.contrib.bma.thermal_direction.classify_thermal_direction``. The task
runs only when ``Event.type.code`` or ``Event.type.name`` is ``RF`` or ``APG``
(case-insensitive, exact match).

What gets stored
================

``Event.note`` gains one block. A later run replaces that block and leaves the
rest of the note alone::

    [thermal-direction]
    hasil_akhir: Krasak
    arah: Kiri
    winner: Krasak
    classified_at: 2026-09-23T10:02:00+00:00
    [/thermal-direction]

The same ``hasil_akhir``, ``arah``, and ``arah_sumber`` values are sent to the
BMA bulletin. ``refid`` is the bulletin id. When ``refid`` is empty, the task
looks up ``/api/v1/bulletin/`` around the event time. The update is a PATCH of
those fields on ``/api/v1/crud/bulletin/<id>/``, using the same API key. If the
fetched bulletin already has ``attributes`` or ``remark`` / ``note`` /
``catatan``, those are updated as well. A failed bulletin call does not roll
back the local note.

The thermal query is ``GET {BMA_URL}/api/v1/thermal-axis-jrg/`` with
``eventdate``, ``datetime_before`` (10 minutes before), ``datetime_after``
(2 minutes after), and the river names Sat, Bebeng, Krasak, Putih, Boyong,
Kuning, and Gendol. Times are UTC.
