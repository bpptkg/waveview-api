import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from waveview.utils.media import MediaPath


class OrganizationMember(models.Model):
    """
    Identifies relationships between organizations and users.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "Organization",
        related_name="memberships",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="organization_memberships",
        on_delete=models.CASCADE,
    )
    roles = models.ManyToManyField(
        "OrganizationRole", blank=True, related_name="organization_members"
    )
    date_added = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="invited_members",
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _("organization member")
        verbose_name_plural = _("organization members")

    def __str__(self) -> str:
        return self.user.username


class Organization(models.Model):
    """
    Organization holds various entities and resources.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    description = models.TextField(null=True, blank=True, default="")
    url = models.URLField(null=True, blank=True)
    address = models.TextField(null=True, blank=True, default="")
    avatar = models.ImageField(
        upload_to=MediaPath("organization-avatars"), null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="organizations",
        related_query_name="organization",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="OrganizationMember",
        through_fields=("organization", "user"),
    )

    class Meta:
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")

    def __str__(self) -> str:
        return self.name

    @property
    def member_count(self) -> int:
        return self.memberships.count()


class OrganizationRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "Organization",
        null=True,
        blank=False,
        related_name="organization_roles",
        related_query_name="organization_role",
        on_delete=models.CASCADE,
    )
    slug = models.SlugField(max_length=150, null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(null=True, blank=True, default="")
    permissions = ArrayField(
        models.TextField(null=False, blank=False),
        null=True,
        blank=True,
        default=list,
    )
    order = models.IntegerField(default=0, null=False, blank=False)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("organization role")
        verbose_name_plural = _("organization roles")
        unique_together = ("organization", "slug")

    def __str__(self) -> str:
        return self.name


class OrganizationSettings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(
        "Organization",
        on_delete=models.CASCADE,
        related_name="organization_settings",
        related_query_name="organization_setting",
    )
    data = models.JSONField(default=dict, help_text=_("Setting data."))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("organization settings")
        verbose_name_plural = _("organization settings")

    def __str__(self) -> str:
        return self.organization.name
