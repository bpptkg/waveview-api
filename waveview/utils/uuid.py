import uuid


def is_valid_uuid(value: str, version: int = 4) -> bool:
    try:
        uuid.UUID(value, version=version)
        return True
    except ValueError:
        return False
