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
