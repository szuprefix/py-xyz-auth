# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from . import serializers, signals, stats
from rest_framework import viewsets, decorators, response, status, permissions
from xyz_restful.helper import register_urlpatterns
from xyz_restful.decorators import register
from django.contrib.auth import login as auth_login, models
from rest_framework.serializers import Serializer, ListSerializer
from .authentications import USING_JWTA, add_token_for_user


@register(basename='user')
class UserViewSet(viewsets.GenericViewSet):
    serializer_class = serializers.UserSerializer
    queryset = models.User.objects.none()

    def get_object(self):
        return self.request.user

    @decorators.action(['post'], detail=False, authentication_classes=[], permission_classes=[])
    def login(self, request, *args, **kwargs):
        serializer = serializers.LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.user
            auth_login(request, user)
            data = self.get_serializer(serializer.user).data
            add_token_for_user(data, user)
            return response.Response(data)
        return response.Response(serializer.errors, status=400)

    @decorators.action(['get'], detail=False, permission_classes=[permissions.IsAuthenticated])
    def current(self, request):
        srs = signals.to_get_user_profile.send(sender=self, user=request.user, request=request)
        srs = [rs[1] for rs in srs]
        data = self.get_serializer(request.user, context={'request': request}).data
        for rs in srs:
            if not isinstance(rs, (list, tuple)):
                rs = [rs]
            for s in rs:
                if isinstance(s, (Serializer, ListSerializer)):
                    opt = s.child.Meta.model._meta if hasattr(s, 'child') else s.Meta.model._meta
                    n = "as_%s_%s" % (opt.app_label, opt.model_name)
                    data[n] = s.data
        return response.Response(data)

    @decorators.action(['post'], detail=False, permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        serializer = serializers.PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return response.Response({})
        return response.Response(serializer.errors, status=400)

    @decorators.action(['post', 'get'], detail=False, authentication_classes=[], permission_classes=[])
    def logout(self, request):
        from django.contrib.auth import logout
        logout(request)
        return response.Response('退出成功', status=status.HTTP_200_OK)

    @decorators.action(['get'], detail=False, permission_classes=[permissions.IsAuthenticated])
    def stat(self, request):
        pms = request.query_params
        ms = pms.getlist('measures', ['all'])
        return response.Response(stats.stats_login(None, ms, pms.get('period', '近7天')))

    @decorators.action(['patch'], detail=False)
    def change_user_name(self, request):
        ds = request.data
        uid = ds['user_id']
        name = ds['name']
        from .helper import change_user_names
        rns = change_user_names(uid, name)
        return response.Response(dict(detail='ok', roles=rns))



if USING_JWTA:
    from rest_framework_simplejwt.views import token_obtain_pair, token_refresh
    from django.conf.urls import url

    urlpatterns = [
        url(r'^token/$', token_obtain_pair, name='token_obtain_pair'),
        url(r'^token/refresh/$', token_refresh, name='token_refresh')
    ]
    register_urlpatterns('auth', urlpatterns)
