========================
Thermal RF/APG Direction
========================

After an RF (rockfall) or APG (awan panas guguran) event is saved, WaveView
waits about two minutes, reads Merapi thermal river-axis temperatures from
BMA, and stores which river heated first.

The observer class is
``waveview.contrib.bma.thermal_direction.observer.ThermalDirectionObserver``.
Its name in the Django admin Event Observer config is ``bma.thermal_direction``.

Enable it
=========

1. Set environment variables:

   - ``BMA_URL`` — BMA host, default ``https://bma.cendana15.com``. No API key
     belongs in the repository. Put the key only in the environment.
   - ``BMA_API_KEY`` — sent as ``Authorization: Api-Key <key>``.
   - ``THERMAL_DIRECTION_DELAY`` — seconds to wait before classification.
     Default ``120``.

2. In Django admin, open Event Observer and add a row:

   - Volcano: the volcano whose events should be classified.
   - Name: ``bma.thermal_direction``.
   - Data: ``{}``.
   - Is enabled: checked.
   - Run async: unchecked. The observer only enqueues a Celery task.
   - Order: after ``bma.bulletin``, so the bulletin exists before direction is
     written.

3. Run a Celery worker that imports ``waveview.contrib.bma.thermal_direction.tasks``.
   That module is listed in ``CELERY_IMPORTS``.

What it does
============

Create schedules the task when the event type code or name is ``RF`` or
``APG`` (case-insensitive). Update schedules again while the event is still
RF or APG, so a changed origin time or a type changed onto RF/APG is
reclassified. Delete does nothing.

The task loads the event again and skips anything that is no longer RF/APG.

Classification calls ``GET {BMA_URL}/api/v1/thermal-axis-jrg/`` with:

- ``eventdate`` — event time
- ``datetime_before`` — 10 minutes before the event
- ``datetime_after`` — 2 minutes after the event
- ``rivers`` — ``Sat,Bebeng,Krasak,Putih,Boyong,Kuning,Gendol``

Query timestamps are Asia/Jakarta wall times (``YYYY-MM-DD HH:MM:SS``), the
same convention as the BMA bulletin importer. ``Event.time`` itself stays UTC.
Naive timestamps in the response are read as Asia/Jakarta. Timestamps that
carry an offset are honored.

For each river the baseline is the median temperature strictly before the
event. A spike is the first sample at or after the event that is at least
5°C above that baseline. The earliest spike wins. If two rivers spike at the
same time, the alphabetically earlier name wins.

Rivers on the left bank (``Kiri``) are Krasak, Boyong, and Sat. Rivers on the
right bank (``Kanan``) are Bebeng, Putih, Lamat, and Senowo. Kuning and Gendol
are not in either set: if one of them wins, ``hasil_akhir`` is that river name
and ``arah`` is ``Tidak terdeteksi``. No spike, or no samples before the event,
also yields ``Tidak terdeteksi``.

Where the result is stored
==========================

``Event.note`` gains one block, replaced on the next run::

    [thermal-direction]
    hasil_akhir: Krasak
    arah: Kiri
    winner: Krasak
    classified_at: 2026-09-23T02:05:00+00:00
    [/thermal-direction]

The task then tries to write the same result onto the BMA seismic bulletin.
The bulletin id is ``Event.refid``. If ``refid`` is empty, the task searches
``GET /api/v1/bulletin/`` for the closest ``eventdate`` within one minute.

WaveView's bulletin payload has no direction column. The update therefore
sends these extra fields with ``Authorization: Api-Key``:

- ``arah`` — ``Kiri``, ``Kanan``, or ``Tidak terdeteksi``
- ``hasil_akhir`` — winning river, or ``Tidak terdeteksi``
- ``arah_sumber`` — same value as ``arah``
- ``remark`` (or an existing ``keterangan``, ``catatan``, or ``note`` field)
  — ``Arah termal: ...; Hasil akhir: ...``

The first request is ``PATCH /api/v1/crud/bulletin/{id}/``. If that is rejected
as a bad method or a bad body, the task loads the bulletin and ``PUT``s it
back with those fields merged in. A missing bulletin is left alone. The event
note is kept either way. ``BMA_API_KEY`` is the only credential this package
uses. Bulletin create/update elsewhere still uses the token stored on the
``bma.bulletin`` observer, and a read-only API key can reject this write.
