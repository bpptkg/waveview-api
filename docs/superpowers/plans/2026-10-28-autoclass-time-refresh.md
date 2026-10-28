# Autoclass Time Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-run autoclass when an eligible native VEPS event is created or its event time changes, without replacing a manually selected event type.

**Architecture:** Extend the existing durable event job in `waveview.contrib.autoclass.task` with separate classification and type-application gates. Reapply a detector prediction only to AUTO or a still autoclass-owned type. Call the queue from the existing event serializer on creation and only when the event time changes. Reuse the JSON field, celery task, model, and display paths.

**Tech Stack:** Django REST Framework, Celery, PostgreSQL, pytest.

**Spec:** `docs/superpowers/specs/2026-10-28-autoclass-time-refresh-design.md`

## Global Constraints

- Limit work to the configured Merapi pilot catalog; the allowlist remains the activation gate.
- Exclude imported events with `refid`.
- Apply detector type predictions only while the event remains automatic and preliminary and its type is AUTO or still matches its previous autoclass-applied type.
- Never replace type or validation fields for manual VEPS events.
- Requeue only when event time changes; edits to other fields do not trigger inference.
- Respect the existing 150-second waveform wait and model revision.
- Add no database migration or dependency.

## Review Focus

- A manual VEPS event created with a non-AUTO type receives prediction metadata and retains its selected type — test in Task 1.
- A type-only operator edit during a running prediction is preserved — test in Task 1.
- Editing a manual event time after success requeues the new time and leaves its type/status unchanged — test in Task 1.
- A late response from an older time cannot replace the new queued result — test in Task 1.
- Changing only the note or event type does not requeue inference — test in Task 1.
- Detector AUTO classification still updates type, while imported and non-pilot events remain excluded — existing tests plus Task 1 regression check.

## Files and responsibilities

- `waveview/contrib/autoclass/task.py`: define classification eligibility separately from AUTO type-application eligibility; reset and queue work for changed event times.
- `waveview/event/serializers/event.py`: enqueue after event creation and requeue after an event-time change.
- `tests/autoclass/test_pipeline.py`: cover manual classification, time refresh, non-time edits, stale in-flight results, and automatic-event regression.
- `docs/guides/autoclass.rst`: document native manual events and time-change behavior.

---

### Task 1: Queue and safely refresh VEPS autoclass predictions

**Files:**
- Modify: `waveview/contrib/autoclass/task.py`
- Modify: `waveview/event/serializers/event.py`
- Test: `tests/autoclass/test_pipeline.py`
- Modify: `docs/guides/autoclass.rst`

**Interfaces:**
- Reuse `enqueue_event(event: Event) -> None` from serializer create/update paths.
- Keep classification and type-application gates separate. Add a classification gate for detector refreshes and native manual VEPS events; apply type only to AUTO events or to the prior autoclass-applied type, and never map manual VEPS results back to `Event.type`.

- [x] **Step 1: Write failing tests** for manual VEPS prediction without type mutation; event creation enqueue; successful prediction requeue after time edit; type-only edit preservation; non-time edit not requeueing; and stale in-flight result rejection after a new time is enqueued.
- [x] **Step 2: Run the focused tests** and confirm failures are caused by missing manual/time-change behavior.
- [x] **Step 3: Implement the classification predicate and time-aware enqueue reset** in `task.py`; preserve the manual validation snapshot, clear stale attempt identity, reset attempts/result for the new timestamp, and keep the existing 150-second wait.
- [x] **Step 4: Enqueue event creation and time changes** in `EventPayloadSerializer`; leave other edits on the existing path without a new prediction.
- [x] **Step 5: Update `docs/guides/autoclass.rst`** with the manual-event and event-time rules.
- [x] **Step 6: Run focused tests** and then all `tests/autoclass` tests; verify the existing AUTO mapping tests still pass.
- [x] **Step 7: Commit** as `feat: refresh autoclass when event time changes`.

Run: `SECRET_KEY=test DATABASE_NAME=waveview_test DATABASE_USER=postgres DATABASE_PASSWORD=test DATABASE_HOST=127.0.0.1 DATABASE_PORT=16440 poetry run pytest -q tests/autoclass/test_pipeline.py`
Expected: focused tests pass.

Run: `SECRET_KEY=test DATABASE_NAME=waveview_test DATABASE_USER=postgres DATABASE_PASSWORD=test DATABASE_HOST=127.0.0.1 DATABASE_PORT=16440 poetry run pytest -q tests/autoclass`
Expected: autoclass test suite passes.
