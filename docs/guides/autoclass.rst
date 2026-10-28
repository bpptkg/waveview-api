Autoclass pilot integration
===========================

The integration is disabled by default. Keep ``AUTOCLASS_CATALOG_IDS`` empty
until staging verification and the operational pilot have been approved.
No TensorFlow dependency is added to WaveView API.

Data and workflow
-----------------

Native Merapi AUTO events created by STE/LTE or SINOAS, and manually created
VEPS events in an allowed catalog, receive durable work metadata in the nullable
``Event.autoclass`` JSON field. Celery calls the private autoclass API after
event time +150 seconds. A valid result fills the type only while a detector
event is still automatic/preliminary and its input time and model revision
match. Manual VEPS events keep the operator-selected type; autoclass is stored
as a prediction only. Changing the event time queues a fresh prediction for the
new time and ignores any late result for the previous time. Editing other fields
does not queue another prediction. Manual decisions always take precedence.
The latest manual decision records its actor, UTC time, type and status in
``autoclass.validation`` without replacing the detector author.

DG, RF and APG map to GASBURST, ROCKFALL and AWANPANAS. APRF is an additional
model label, not an EventType or a new probability. A seismic validation may
omit visual observation; existing observations are preserved. Explicit visual
payloads still use the existing validation rules.

Only a manual confirmed/reviewed/final/rejected decision schedules BMA publication.
Sync uses the native UUID hex, existing CRUD authentication and the upstream
narrow autoclass PATCH. Sync failures have their own bounded retries and never
repeat a successful inference. Import and cleanup preserve pilot native events.

Configuration and activation
----------------------------

1. Deploy migration ``event.0005_event_autoclass`` before using the JSON field.
2. Run the autoclass repository's authenticated ``serve`` mode on the private
   Docker network. Its VEPS Compose override replaces cron and publishes no host
   port. The wheel/model are version 0.3.1 / ``model_merapi_v6ga_m1348``.
3. Configure the backend environment, leaving the allowlist empty::

       AUTOCLASS_CATALOG_IDS=
       AUTOCLASS_URL=http://autoclass:8765
       AUTOCLASS_TOKEN=<same secret as AUTOCLASS_API_TOKEN>
       AUTOCLASS_REVISION=merapi-v6ga-m1348-0.3.1

4. Configure an enabled ``bma.bulletin`` observer for the volcano. Its
   ``server_url`` must match ``BMA_URL``. Its CRUD token and ``BMA_API_KEY`` for
   narrow PATCH remain separate credentials. Verify BMA's existing autoclass
   column and PATCH migration before enabling a writer.
5. Restart Celery worker and beat using the deployment procedure. Stop legacy
   autoclass cron for the same pilot events. After staging approval, explicitly
   allow the pilot catalog UUID. Change ``AUTOCLASS_REVISION`` whenever the
   model/configuration changes; old queued inputs become stale.

Model cutover
-------------

The backend accepts only the pinned model/version, so a mismatched service
response fails the job permanently. Change the model with inference disabled:

1. Empty ``AUTOCLASS_CATALOG_IDS`` and restart Celery worker and beat.
2. Deploy the new autoclass service and wait until its API health check passes.
3. Deploy the backend with the matching validator and ``AUTOCLASS_REVISION``,
   then restart worker and beat.
4. Only then restore the allowlist and restart worker and beat again.

Events detected while the allowlist is empty are never classified later. They
remain available for manual validation.

Thermal classification remains disabled pending agreement on river mappings and
the live thermal contract. Enabling this integration does not enable new
detectors or external alert observers.

Recovery and rollback
---------------------

Beat republishes due pending/retrying work and expired 600-second running leases
every minute, at most 200 inference and 200 sync jobs per pass. Retries use
30/120/300 seconds. Check ``autoclass.state/error`` and ``autoclass.sync.state/error``
independently. Failed work stays available for manual validation.

An authorized operator may call ``recover_events()`` from
``waveview.contrib.autoclass.task`` in Django shell. For exhausted inference,
correct the cause and use a transaction to verify eligibility, clear only failed
metadata with no successful result, and call ``enqueue_event(event)``. Record the
operator and reason in the operational log. Never clear a successful prediction
or a manual decision to force reprocessing.

For rollback, empty the allowlist and restart workers/beat. Retain the JSON column,
original predictions and manual decisions. Do not bulk-reset types or reverse the
migration and lose results. The outbound ordering uses PostgreSQL advisory locks.

Local verification
------------------

Use a dedicated PostgreSQL/Timescale test database and explicit test environment::

    AUTOCLASS_CHECKOUT=/path/to/autoclass .venv/bin/python -m pytest -q
    .venv/bin/python manage.py makemigrations --check --dry-run

The cross-repository test uses the real private HTTP transport with a deterministic
predictor fixture and local BMA stub. It does not establish model accuracy, FDSN
availability, production migrations or two-operator browser behavior. Those remain
staging gates before activation.
