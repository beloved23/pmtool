from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from django.shortcuts import redirect


class UserPermissionsMixin(UserPassesTestMixin):
    permissions = []

    def test_func(self):
        user = self.request.user
        if user.is_anonymous:
            return False
        has_permissions = []
        if not (user.is_staff or user.is_superuser or (hasattr(user, "profile") and user.profile.is_ceo)):
            for permission in self.permissions:
                has_permissions.append(user.has_perm(permission))
            return True in has_permissions
        return True
