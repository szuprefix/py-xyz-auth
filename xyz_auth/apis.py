# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from . import serializers, signals, stats
from rest_framework import viewsets, decorators, response, status, permissions
from xyz_restful.helper import register_urlpatterns
from xyz_restful.decorators import register
from django.contrib.auth import login as auth_login
from rest_framework.serializers import Serializer
from .authentications import USING_JWTA, add_token_for_user


@register(base_name='user')
class UserViewSet(viewsets.GenericViewSet):
    serializer_class = serializers.UserSerializer

    def get_object(self):
        return self.request.user

    @decorators.list_route(['post'], authentication_classes=[], permission_classes=[])
    def login(self, request, *args, **kwargs):
        serializer = serializers.LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.user
            auth_login(request, user)
            data = self.get_serializer(serializer.user).data
            add_token_for_user(data, user)
            return response.Response(data)
        return response.Response(serializer.errors, status=400)

    @decorators.list_route(['get'], permission_classes=[permissions.IsAuthenticated])
    def current(self, request):
        srs = signals.to_get_user_profile.send(sender=self, user=request.user, request=request)
        srs = [rs[1] for rs in srs if isinstance(rs[1], Serializer)]
        data = self.get_serializer(request.user, context={'request': request}).data
        for rs in srs:
            opt = rs.Meta.model._meta
            n = "as_%s_%s" % (opt.app_label, opt.model_name)
            data[n] = rs.data
        return response.Response(data)

    @decorators.list_route(['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        serializer = serializers.PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return response.Response({})
        return response.Response(serializer.errors, status=400)

    @decorators.list_route(['post', 'get'], authentication_classes=[], permission_classes=[])
    def logout(self, request):
        from django.contrib.auth import logout
        logout(request)
        return response.Response('退出成功', status=status.HTTP_200_OK)

    @decorators.list_route(['get'], permission_classes=[permissions.IsAuthenticated])
    def stat(self, request):
        pms = request.query_params
        ms = pms.getlist('measures', ['all'])
        return response.Response(stats.stats_login(None, ms, pms.get('period', '近7天')))



if USING_JWTA:
    from rest_framework_simplejwt.views import token_obtain_pair, token_refresh
    from django.conf.urls import url

    urlpatterns = [
        url(r'^token/$', token_obtain_pair, name='token_obtain_pair'),
        url(r'^token/refresh/$', token_refresh, name='token_refresh')
    ]
    register_urlpatterns('auth', urlpatterns)
