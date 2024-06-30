from django.db import models


class PermissionChoices(models.TextChoices):
    """
    Permission choices for organization roles.
    """

    VIEW = "view", "View"
    EDIT = "edit", "Edit"
    DELETE = "delete", "Delete"
    CREATE = "create", "Create"
    MANAGE = "manage", "Manage"
    ASSIGN = "assign", "Assign"
    INVITE = "invite", "Invite"
    EXPORT = "export", "Export"
    IMPORT = "import", "Import"
    PUBLISH = "publish", "Publish"
    UNPUBLISH = "unpublish", "Unpublish"
    ARCHIVE = "archive", "Archive"
    RESTORE = "restore", "Restore"
    APPROVE = "approve", "Approve"
    REJECT = "reject", "Reject"
    SUBMIT = "submit", "Submit"
    CANCEL = "cancel", "Cancel"
    REQUEST = "request", "Request"
    REVIEW = "review", "Review"
    COMMENT = "comment", "Comment"
    TAG = "tag", "Tag"
