========================
Thermal RF/APG Direction
========================

After an RF or APG event is saved, WaveView waits about two minutes and then
classifies which river axis heated first. The result is written back onto the
WaveView event and, when possible, onto the related BMA bulletin.

The classifier follows the river sets used by BPPTKG:

- Kiri: Krasak, Boyong, Sat
- Kanan: Bebeng, Putih, Lamat, Senowo

Only BMA areas in those sets are used; ``Sat_1`` and ``Sat_2`` count as Sat,
and non-river areas (Asap, Kubah_BD, Ref_Ki, Ref_Ka) are ignored. If no river
rises at least 5°C above its pre-event median, both fields are
``Tidak terdeteksi``.

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
runs only when ``Event.type.code`` or ``Event.type.name`` is ``RF``, ``APG``,
``ROCKFALL``, or ``AWANPANAS`` (case-insensitive, exact match). VEPS stores
rockfall and awan panas guguran as ``ROCKFALL`` and ``AWANPANAS``.

Autoclass changes the event type with a queryset update, which does not reach
observers. When autoclass applies ``ROCKFALL`` or ``AWANPANAS``, it queues this
observer directly, so the result arrives about 150 + 120 seconds after the event.

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

BMA stores the winning river name on the bulletin field ``arah_kubah_termal``.
The bulletin id is ``refid`` when set, otherwise the event UUID hex, the same id
the ``bma.bulletin`` observer writes. The update is:

``PATCH {BMA_URL}/api/v1/crud/bulletin/<id>/arah_kubah_termal/``

with body ``{"arah_kubah_termal": "<hasil_akhir>"}``. ``hasil_akhir`` is the river
name, such as ``Krasak``, ``Boyong``, ``Bebeng``, or ``Tidak terdeteksi``.
A JSON ``null`` clears the field. The request uses the same
``Authorization: Api-Key <BMA_API_KEY>`` header.
``Event.note`` still keeps both the river name and ``arah`` (``Kiri`` or
``Kanan``) for debugging. A failed bulletin call does not roll back the local
note. This write requires the BMA ``arah_kubah_termal`` column from
bpptkg/bma#11. Merge and deploy that change after the CHANGE COLUMN SQL,
then deploy this writer.

The thermal query is ``GET {BMA_URL}/api/v1/thermal-axis-jrg/`` with
``start`` (10 minutes before), ``end`` (2 minutes after), and
``field_types=max_temp``. BMA reads ``start``/``end`` as naive WIB
(``YYYY-MM-DD HH:MM:SS``); a ``Z`` suffix makes it return 500.
