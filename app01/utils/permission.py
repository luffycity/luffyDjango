from rest_framework.permissions import BasePermission


class LuffyPermission(BasePermission):
    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        if request.user:
            return True
        return False