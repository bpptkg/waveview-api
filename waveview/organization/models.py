import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from waveview.organization.permissions import PermissionChoices
from waveview.utils.media import MediaPath


class OrganizationMember(models.Model):
    """
    Identifies relationships between organizations and users.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "Organization",
        related_name="member",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orgmember",
        on_delete=models.CASCADE,
    )
    role = models.ForeignKey(
        "Role",
        null=True,
        blank=True,
        related_name="orgmember",
        on_delete=models.SET_NULL,
    )
    email = models.EmailField(null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="inviter",
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _("organization member")
        verbose_name_plural = _("organization members")


class Organization(models.Model):
    """
    Organization holds various entities and resources.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    description = models.TextField(null=True, blank=True, default="")
    url = models.URLField(null=True, blank=True)
    address = models.TextField(null=True, blank=True, default="")
    authority_domain = models.CharField(max_length=64, null=True, blank=True)
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
        related_name="organization_memberships",
        through_fields=("organization", "user"),
    )

    class Meta:
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")

    def __str__(self) -> str:
        return self.name

    def get_authority_id(self) -> str:
        """
        Get organization authority identifier used in QuakeML URI.

        If authority_domain is not None, return its value. Otherwise, return
        slug.
        """
        if self.authority_domain is not None:
            return self.authority_domain
        return self.slug


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=250, null=False, blank=False)
    name = models.CharField(max_length=200, null=False, blank=False)
    description = models.TextField(null=True, blank=True, default="")
    permissions = ArrayField(
        models.TextField(null=False, blank=False, choices=PermissionChoices.choices),
        null=True,
        blank=True,
        default=list,
    )
    order = models.IntegerField(default=0, null=False, blank=False)
    organization = models.ForeignKey(
        "organization.Organization",
        null=True,
        blank=False,
        related_name="roles",
        related_query_name="role",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("role")
        verbose_name_plural = _("roles")
        unique_together = (("slug", "organization"),)

    def __str__(self) -> str:
        return self.name
