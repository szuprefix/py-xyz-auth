# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals

from rest_framework.filters import BaseFilterBackend
from django.apps.registry import apps


class UserResourceFilter(BaseFilterBackend):

    def gen_relation_lookup_from_request(self, request):
        pms = request.query_params
        d = {}
        for k, v in pms.items():
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
        if 'pk' in view.kwargs:
            return queryset
        from .helper import filter_query_set_for_user
        user = request.user
        rld = self.gen_relation_lookup_from_request(request)
        from .helper import get_relation_limit
        relation_limit = get_relation_limit(request, queryset)
        qset = filter_query_set_for_user(
            queryset,
            user,
            relation_lookups=rld,
            relation_limit=relation_limit,
            role_name=request.query_params.get('role_name_for_filter')
        )
        # if mn:
        #     model = apps.get_model(mn)
        #     from xyz_util.modelutils import get_generic_foreign_key, distinct
        #     from django.contrib.contenttypes.models import ContentType
        #     sqset = filter_query_set_for_user(model.objects.all(), user, relation_lookups=rld, relation_limit=queryset.model._meta.label_lower)
        #     gfk = get_generic_foreign_key(model._meta)
        #     d = {gfk.ct_field: ContentType.objects.get_for_model(queryset.model)}
        #     sqset.filter(**d)
        #     qset = qset.filter(id__in=list(distinct(sqset, gfk.fk_field)))
        return qset
