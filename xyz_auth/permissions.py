# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from rest_framework.permissions import DjangoModelPermissions

__author__ = 'denishuang'


class RoleResPermissions(DjangoModelPermissions):
    def has_permission(self, request, view):
        if super(RoleResPermissions, self).has_permission(request, view):
            return True
        from .helper import user_has_model_permission
        return user_has_model_permission(self._queryset(view), request.user, view.action)
