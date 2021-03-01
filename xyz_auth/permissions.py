# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from rest_framework.permissions import DjangoModelPermissions

__author__ = 'denishuang'


class RoleResPermissions(DjangoModelPermissions):
    def has_permission(self, request, view):
        if super(RoleResPermissions, self).has_permission(request, view):
            return True
        if view.action == 'metadata':
            return True
        from .helper import user_has_model_permission
        return user_has_model_permission(self._queryset(view), request.user, view.action)

    def has_object_permission(self, request, view, obj):
        from .helper import model_in_user_scope
        if not model_in_user_scope(obj, request.user):
            return False
        return super(RoleResPermissions, self).has_object_permission(request, view, obj)
