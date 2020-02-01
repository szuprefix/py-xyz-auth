# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals
from django.conf import settings
from xyz_util import modelutils
from rest_framework.exceptions import PermissionDenied
from django.apps.registry import apps
from django.db.models import Q
from django.db.models.base import ModelBase


def gen_permissions_map(permissions):
    m = {}
    for p in permissions:
        app, pn = p.split('.')
        fs = pn.split('_')
        model = fs[-1]
        action = '_'.join(fs[:-1])
        am = m.setdefault(app, {})
        mm = am.setdefault(model, {})
        mm[action] = 1
    return m


def gen_default_permissions():
    from django_szuprefix.api.helper import router
    from django.apps.registry import apps
    from django_szuprefix.utils import modelutils
    d = {}
    for a, b, c in router.registry:
        ps = a.split('/')
        aname = ps[0]
        mname = ps[1]
        c = apps.app_configs[aname]
        d.setdefault(ps[0], {'name': aname, 'label': c.verbose_name, 'models': []})
        try:
            mc = c.get_model(mname)
        except:
            continue
        m = {'name': mname, 'label': mc._meta.verbose_name, 'scope': []}
        gfk = modelutils.get_generic_foreign_key(mc._meta)
        if gfk:
            m['generic'] = [gfk.name, gfk.ct_field, gfk.fk_field]
        d[aname]['models'].append(m)
    return d


def role_object_to_user(role_obj):
    from django.contrib.auth.models import User
    from django.db.models import OneToOneField

    for f in role_obj._meta.get_fields():
        if isinstance(f, OneToOneField) and f.related_model == User:
            return getattr(role_obj, f.name)


def get_user_roles():
    from django.contrib.auth.models import User
    from django.db.models import OneToOneRel

    return [f for f in User._meta.get_fields() if isinstance(f, OneToOneRel) and f.name.startswith('as_')]


def get_user_resources():
    from django_szuprefix.utils import modelutils
    from django.contrib.auth.models import User
    pm = gen_default_permissions()
    roles = [(r.name, r.related_model._meta.verbose_name, r.related_model) for r in get_user_roles()]
    roles.append(('self', User._meta.verbose_name, User))
    for an, a in pm.iteritems():
        for m in a['models']:
            am = a['name'] + '.' + m['name']
            for rn, rvn, r in roles:
                lks = modelutils.get_model_links(r, am)
                if not lks:
                    continue
                print am, rn, rvn, [f.name for f in lks]


USER_ROLE_MODEL_MAP = getattr(settings, 'USER_ROLE_MODEL_MAP', {})


def filter_query_set_for_user(qset, user, scope_map=USER_ROLE_MODEL_MAP, relation_lookups={}):
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.contrib.contenttypes.models import ContentType
    if isinstance(qset, (str, unicode)):
        qset = apps.get_model(qset)
    if type(qset) == ModelBase:
        qset = qset.objects.all()
    m = qset.model
    mn = m._meta.label_lower
    rld = relation_lookups.get(mn)
    # print rld, relation_lookups
    if rld:
        qset = qset.filter(**rld)
    if user.is_superuser:
        return qset
    lookup_link = None
    for r in [r.name for r in get_user_roles()]:
        if r not in scope_map or not hasattr(user, r):
            continue

        role = getattr(user, r)
        if hasattr(role, 'is_active') and role.is_active == False:
            raise PermissionDenied('当前%s帐号已被禁用' % role._meta.verbose_name)

        d = scope_map.get(r)
        if '@all' in d:
            return qset
        if mn not in d:
            continue
        d2 = d.get(mn)
        if '@all' in d2:
            return qset
        for fn, mnl in d2.get('scope', {}).iteritems():
            # print mn, mnl, fn, r
            if isinstance(mnl, (str, unicode)):
                mnl = [mnl]
            for mn2 in mnl:
                lookup = "%s__in" % fn
                if mn2 == 'auth.user':
                    lkd = {lookup: [user.id]}
                elif mn2 == r:
                    lkd = {lookup: [role.id]}
                else:
                    m2 = apps.get_model(mn2)
                    field = m._meta.get_field(fn)
                    ids = filter_query_set_for_user(mn2, user, scope_map=scope_map, relation_lookups=relation_lookups)
                    # print field, ids
                    if isinstance(field, GenericForeignKey):
                        lookup = "%s__in" % field.fk_field
                        lkd = {field.ct_field: ContentType.objects.get_for_model(m2), lookup: ids}
                    else:
                        if field.related_model != m2:
                            f = modelutils.get_model_related_field(m2, field.related_model)
                            ids = ids.values_list(f.name, flat=True)
                        lkd = {lookup: ids}
                lookup_link = Q(**lkd) if lookup_link is None else lookup_link | Q(**lkd)
    if lookup_link:
        qset = qset.filter(lookup_link)
        try:
            m._meta.get_field('is_active')
            qset = qset.filter(is_active=True)
        except:
            pass
        return qset.distinct()
    return qset.none()


def user_has_model_permission(model, user, action, scope_map=USER_ROLE_MODEL_MAP):
    from django.db.models import QuerySet
    if isinstance(model, QuerySet):
        model = model.model
    mn = model._meta.label_lower
    for r in [a.name for a in get_user_roles()]:
        if r not in scope_map or not hasattr(user, r):
            continue

        d = scope_map.get(r)
        if '@all' in d:
            return True
        if mn not in d:
            continue
        d2 = d.get(mn)
        if '@all' in d2:
            return True
        if action in d2.get('actions', []) + d2.get('batch_actions', []):
            return True


def get_user_model_permissions(user, scope_map=USER_ROLE_MODEL_MAP):
    from xyz_restful.helper import get_model_actions
    res = {}
    mds = get_model_actions()
    if user.is_superuser:
        return mds
    for r in [a.name for a in get_user_roles()]:
        if r not in scope_map or not hasattr(user, r):
            continue
        d = scope_map.get(r)
        if '@all' in d:
            return mds
        for mn, conf in d.iteritems():
            res.setdefault(mn, set())
            if '@all' in conf:
                res[mn] = mds[mn]
            else:
                acs = conf.get('actions', []) + ['batch_%s' % b for b in conf.get('batch_actions', [])]
                res[mn].update(acs)
    return res
