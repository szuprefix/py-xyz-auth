# -*- coding:utf-8 -*-
from django.contrib.auth.backends import ModelBackend


class TempTokenBackend(ModelBackend):
    """
    Custom auth backend that uses an worker mobile and password
    """

    def authenticate(self, request, username, password):
        from django.core.signing import TimestampSigner
        signer = TimestampSigner(salt=username)
        try:
            uid = signer.unsign(password, max_age=300)
        except Exception as e:
            return
        from django.contrib.auth import models
        user = models.User.objects.filter(username=username, id=uid).first()
        if user:
            setattr(user, 'login_type', 'temptoken')
        return user


class RolePermissionBackend(object):
    def get_permissions(self, user):
        from .helper import get_user_model_permissions
        return get_user_model_permissions(user)
