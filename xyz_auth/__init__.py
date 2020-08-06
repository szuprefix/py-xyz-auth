# -*- coding:utf-8 -*-
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

default_app_config = 'xyz_auth.apps.Config'


def load_backend(path):
    return import_string(path)()


def _get_backends(return_tuples=False):
    backends = []
    for backend_path in settings.AUTH_USER_PERMISSIONS_BACKENDS:
        backend = load_backend(backend_path)
        backends.append((backend, backend_path) if return_tuples else backend)
    if not backends:
        raise ImproperlyConfigured(
            'No AUTH USER PERMISSIONS backends have been defined. Does '
            'AUTH_USER_PERMISSIONS_BACKENDS contain anything?'
        )
    return backends


def get_backends():
    return _get_backends(return_tuples=False)


def get_user_model_permissions(user):
    for backend, backend_path in _get_backends(return_tuples=True):
        d = backend.get_permissions(user)
        if d:
            return d