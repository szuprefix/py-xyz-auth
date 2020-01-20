# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals

from rest_framework.filters import BaseFilterBackend


class UserResourceFilter(BaseFilterBackend):

    def gen_relation_lookup_from_request(self, request):
        from django.apps.registry import apps
        pms = request.query_params
        d = {}
        for k, v in pms.iteritems():
            ps = k.split('.')
            if len(ps) != 3:
                continue
            mn = '.'.join(ps[:2])
            try:
                m = apps.get_model(mn)
                fn = ps[2]
                m._meta.get_field(fn)
                d.setdefault(mn, {})[fn] = v
            except:
                pass
        return d

    def filter_queryset(self, request, queryset, view):
        from .helper import filter_query_set_for_user
        user = request.user
        rld = self.gen_relation_lookup_from_request(request)
        return filter_query_set_for_user(queryset, user, relation_lookups=rld)
