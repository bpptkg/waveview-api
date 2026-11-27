# Copy autohypo locations onto verified VEPS events

## Intent

Read `bulletin.autohypo` from BMA and store it as an `Origin` on the matching verified VEPS event. The event table and summary show that location when the event has no preferred origin yet. An origin an operator already marked preferred stays preferred.

## Goals and non-goals

- Add a management command in waveview-api that only reads BMA. It creates or updates one `Origin` with `method="nlloc"` per matched event.
- Match a bulletin row to a native VEPS event by parsing `eventid` as the event UUID. Limit the write to the volcano's default catalog and to events whose `evaluation_mode` is `manual` and whose `evaluation_status` is `confirmed`, `reviewed`, or `final`.
- Set `is_preferred` only when the event has no other preferred origin. Leave an existing preferred origin preferred. Leave an `nlloc` origin preferred once it already is.
- Copy `lat`, `lon`, and `z` unchanged. `z` and `Origin.depth` are both kilometers, positive down, negative above MSL.
- Do not change autohypo, the bulletin observer, bulletin upsert, the hypocenter map, or the event UI.
- Do not create events, write `refid`, copy quality fields (`rmsp`, `stde`, and the rest), or widen autohypo's two-hour lookback. A verified event whose bulletin row never received `autohypo` stays without an `nlloc` origin.

## Approaches

1. **Separate `nlloc` origin, preferred only when none exists (selected).** The location columns fill in for events that had no location. A later cron run does not take preferred away from an operator origin. The hypocenter map draws two points when both origins exist, because that endpoint lists every origin.
2. **Never-preferred `nlloc` origin.** The trace stays visible on the location tab, and the event table stays empty until someone marks it preferred.
3. **Fill an empty existing origin in place.** One map point, and no separate record that the numbers came from NLLoc.

## Data flow

Cron invokes `sync_autohypo_origins` with `--org`, `--volcano`, and `--hours`. The command loads `GET /api/v1/bulletin/` through `BulletinImporter`, using `settings.BMA_URL` and `settings.BMA_API_KEY`, with `nolimit=true`. A body shaped `{data: [...]}` is unwrapped. An empty list is success.

Window rules match `sync_bma_events` except there is no historical floor: `--end` defaults to now, `--hours` sets the start to that many hours before the end, and otherwise `--start` defaults to one day before the end. Datetimes are timezone-aware. `BulletinImporter` converts the query to Asia/Jakarta.

For each bulletin row:

1. Skip unless `eventtype` is `VTA` or `VTB`, compared case-insensitively.
2. Skip unless `autohypo` is an object with finite numeric `lat`, `lon`, and `z`.
3. Skip unless `eventid` parses as a UUID. A 32-character hex id is valid. WebObs ids are skipped. Do not look up `refid`.
4. Load `Event` in the volcano's default catalog with that primary key. Skip when it is missing. Do not create an event.
5. Skip unless `evaluation_mode` is `manual` and `evaluation_status` is `confirmed`, `reviewed`, or `final`.

The write is one transaction per event:

- Update one existing `Origin` with `method="nlloc"` on that event. When several exist, update the preferred one among them, otherwise the oldest. When none exists, create one. Do not insert another row, and do not delete extras.
- Set `latitude`, `longitude`, and `depth` from `lat`, `lon`, and `z`. Set `time` to the event time. Set `evaluation_mode` to `automatic` and `evaluation_status` to `preliminary`. On create, leave `author` and `earth_model` empty. On update, leave `author` and `earth_model` as they are.
- Set `is_preferred` when no other origin on the event is preferred. Do not clear `is_preferred` on the `nlloc` row, and do not clear it on any other origin.

Saving an `Origin` does not call `notify_event_observer`. This command must not call it either. A later `sync_bma_events` run will publish the preferred origin's latitude, longitude, and depth into the ordinary bulletin columns. The `autohypo` JSON column stays, because bulletin upsert does not update it. That publish happens only when `nlloc` is the preferred origin.

`--dry-run` logs the event id, coordinates, and whether the origin would be preferred. It does not write.

## Failures

A bad row is logged and skipped. The rest of the batch continues. Skips are: non-UUID `eventid`, unknown event, status outside the verified set, bulletin type other than VTA/VTB, and an `autohypo` object without finite `lat`, `lon`, and `z`.

A missing organization, volcano, or default catalog writes to stderr and stops, as `sync_bma_events` does. An HTTP or network failure from the bulletin request propagates, so cron sees a failed run and that run writes no origins.

## Validation

Backend tests with a mocked bulletin response, and no live BMA call:

- A verified event with no origin gets one preferred `nlloc` origin, and a negative `z` stays negative.
- An event that already has another preferred origin gets a non-preferred `nlloc` origin, and the existing preferred flag stays.
- A second run updates coordinates and does not add a row.
- When two `nlloc` origins already exist and one is preferred, that preferred row is updated and the count stays two. When neither is preferred, the oldest is updated.
- Automatic/preliminary events, rejected events, non-UUID ids, unknown ids, types other than VTA/VTB, and incomplete `autohypo` objects are skipped.
- `--dry-run` writes nothing.
- A failed HTTP fetch writes nothing.

## Files

- `waveview/contrib/bma/bulletin/autohypo.py` holds the fetch unwrapping and the per-event write.
- `waveview/event/management/commands/sync_autohypo_origins.py` is the thin command.
- Tests live next to the existing bulletin tests.
