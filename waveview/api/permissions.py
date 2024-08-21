from django.utils import timezone
from rest_framework import permissions
from rest_framework.request import Request

from waveview.organization.models import Organization


class NoPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: object) -> bool:
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(
        self, request: Request, view: object, obj: object
    ) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request: Request, view: object) -> bool:
        return request.user.is_superuser


class IsOrganizationMember(permissions.BasePermission):
    def has_object_permission(
        self, request: Request, view: object, obj: Organization
    ) -> bool:
        is_author = obj.author == request.user
        is_member = obj.members.filter(id=request.user.id).exists()
        has_expired = obj.memberships.filter(
            user=request.user, expiration_date__lt=timezone.now()
        ).exists()
        return is_author or (is_member and not has_expired)
