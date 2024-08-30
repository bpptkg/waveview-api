from uuid import UUID


def user_channel(pk: UUID | str) -> str:
    return f"user.{str(pk)}"


def organization_channel(pk: UUID | str) -> str:
    return f"organization.{str(pk)}"
