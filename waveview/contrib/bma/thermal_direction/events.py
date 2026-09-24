RF_APG_CODES = frozenset({"rf", "apg"})


def is_rf_or_apg(event) -> bool:
    """True when the event type code or name is RF or APG, ignoring case."""
    event_type = getattr(event, "type", None)
    if event_type is None:
        return False
    code = (getattr(event_type, "code", None) or "").strip().casefold()
    name = (getattr(event_type, "name", None) or "").strip().casefold()
    return code in RF_APG_CODES or name in RF_APG_CODES
