# -*- coding:utf-8 -*-
from rest_framework.authentication import SessionAuthentication as OrgSessionAuthentication
from django.utils.six import text_type

__author__ = 'denishuang'

from rest_framework.settings import api_settings

DACS = api_settings.user_settings.get('DEFAULT_AUTHENTICATION_CLASSES')
USING_JWTA = 'rest_framework_simplejwt.authentication.JWTAuthentication' in DACS


class SessionAuthentication(OrgSessionAuthentication):
    def authenticate_header(self, request):
        return '/accounts/login/'


def add_token_for_user(d, user):
    if USING_JWTA:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        d['token'] = {'refresh': text_type(refresh), 'access': text_type(refresh.access_token)}
