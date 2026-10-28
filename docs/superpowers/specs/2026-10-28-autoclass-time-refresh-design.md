# Autoclass for Manual VEPS Events and Time Changes

## Intent

Run autoclass for native VEPS events created manually and refresh its result when an eligible event's time changes. This keeps the prediction aligned with the waveform window while preserving the operator's event type.

## Goals and non-goals

- Queue predictions for native VEPS events in the configured Merapi pilot catalog, including manually created, confirmed events.
- Requeue on event-time edits, including after manual validation, and ignore any older in-flight result.
- Keep a manual event's selected type unchanged; store and show autoclass as a prediction only.
- Preserve the existing automatic-event behavior: apply a result only while the event remains AUTO, automatic, and preliminary.
- Do not classify imported BMA events, change the model, or alter thermal classification and BMA publication rules.

## Approaches

1. **Reprocess on every eligible time change (selected):** enqueue native VEPS manual events at creation and reset/requeue work when an eligible event's time changes. The new prediction is stored after the existing 150-second waveform wait; manual event types are never replaced. This handles corrected timestamps and avoids stale predictions.
2. **Run once at creation:** predict manual events once and mark the prediction stale after a time edit. This avoids repeat model calls but does not meet the request to update the prediction.

## Constraints and implementation calls

- Reuse the existing `Event.autoclass` state, Celery task, model revision, and catalog allowlist; no schema or model change is planned.
- Scope manual predictions to native VEPS events (`method=veps`, no imported `refid`) in the configured pilot catalog. Detector-created events keep their current eligibility.
- A changed event time invalidates any prior prediction/work, resets retry state, and schedules a fresh prediction for the new time. This also applies after manual validation; late responses for the old time must not apply.
- Manual event type and validation fields are preserved regardless of autoclass result. Autoclass metadata remains a prediction and continues through existing event display and notification paths.
- Reuse the existing post-validation BMA synchronization behavior; this change does not add a new BMA write path.

## Validation

Add backend tests for manual creation enqueueing without type mutation, time edits requeueing, stale in-flight results being ignored, and detector AUTO events retaining their existing type-application behavior. Run the focused autoclass tests and the repository's relevant checks.
