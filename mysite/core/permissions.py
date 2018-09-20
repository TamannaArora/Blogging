"""
permissions for all the apps
"""
from rest_framework import permissions
from django.utils.translation import ugettext as _


class PrivateTokenAccessPermission(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    message = _('You dont have permission to perform this action!')

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        if request.user.is_anonymous:
            return False

        if request.user.is_app_user:
            return False

        return True


class PublicTokenAccessPermission(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    message = _('You dont have permission to perform this action.')

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        if request.user.is_anonymous:
            return False
        return request.user.is_app_user


class PublicPrivateTokenAccessPermission(permissions.BasePermission):
    """
    Custom permission to all the users of an object to edit it.
    """
    message = _('Public Private Token Access Permission violated')

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        if request.user.is_anonymous:
            return False
        return True
