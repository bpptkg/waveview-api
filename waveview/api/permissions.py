from rest_framework import permissions
from rest_framework.request import Request


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
        self, request: Request, view: object, obj: object
    ) -> bool:
        return (
            obj.author == request.user or obj.members.filter(user=request.user).exists()
        )
