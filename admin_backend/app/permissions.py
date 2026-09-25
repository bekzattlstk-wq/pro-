from rest_framework.permissions import BasePermission


class IsStaffOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.method in ("GET", "POST", "HEAD", "OPTIONS") or request.user.is_staff
        )
