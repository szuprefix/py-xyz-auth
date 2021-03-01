# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals
from xyz_util import modelutils
from rest_framework.exceptions import PermissionDenied
from django.apps.registry import apps
from django.db.models import Q
from django.db.models.base import ModelBase
from django.contrib.auth.models import User
from django.utils import translation
from django.db.models import OneToOneField
from django.db.models import OneToOneRel
from xyz_restful.helper import router
from django.contrib.contenttypes.models import ContentType

from django.conf import settings
import logging

log = logging.getLogger('django')


#
# def gen_permissions_map(permissions):
#     m = {}
#     for p in permissions:
#         app, pn = p.split('.')
#         fs = pn.split('_')
#         model = fs[-1]
#         action = '_'.join(fs[:-1])
#         am = m.setdefault(app, {})
#         mm = am.setdefault(model, {})
#         mm[action] = 1
#     return m
#
#
# def gen_default_permissions():
#     d = {}
#     for a, b, c in router.registry:
#         ps = a.split('/')
#         aname = ps[0]
#         mname = ps[1]
#         c = apps.app_configs[aname]
#         d.setdefault(ps[0], {'name': aname, 'label': c.verbose_name, 'models': []})
#         try:
#             mc = c.get_model(mname)
#         except:
#             continue
#         m = {'name': mname, 'label': mc._meta.verbose_name, 'scope': []}
#         gfk = modelutils.get_generic_foreign_key(mc._meta)
#         if gfk:
#             m['generic'] = [gfk.name, gfk.ct_field, gfk.fk_field]
#         d[aname]['models'].append(m)
#     return d


# def role_object_to_user(role_obj):
#     for f in role_obj._meta.get_fields():
#         if isinstance(f, OneToOneField) and f.related_model == User:
#             return getattr(role_obj, f.name)


def get_roles():
    return [f for f in User._meta.get_fields() if isinstance(f, OneToOneRel) and f.name.startswith('as_')]


#
# def get_user_resources():
#     pm = gen_default_permissions()
#     roles = [(r.name, r.related_model._meta.verbose_name, r.related_model) for r in get_roles()]
#     roles.append(('self', User._meta.verbose_name, User))
#     res = {}
#     for an, a in pm.iteritems():
#         for m in a['models']:
#             am = an + '.' + m['name']
#             for rn, rvn, r in roles:
#                 lks = modelutils.get_relations(r, am)
#                 if not lks:
#                     continue
#                 res[am] = dict(
#                     relation=rn,
#                     relation_verbose_name=rvn,
#                     fields=[
#                         (f.name,
#                          modelutils.get_field_verbose_name(f),
#                          f) for f in lks
#                     ]
#                 )
#     return res


USER_ROLE_MODEL_MAP = getattr(settings, 'USER_ROLE_MODEL_MAP', {})


def filter_query_set_for_user(qset, user, scope_map=USER_ROLE_MODEL_MAP, relation_lookups={}, relation_limit=None):
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
    lookup_link = None
    for r in [r.name for r in get_roles()]:
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
        scope = d2.get('scope', {})
        if scope == '@all':
            return qset
        for fn, mnl in scope.iteritems():
            # print mn, mnl, fn, r
            if isinstance(mnl, (str, unicode)):
                mnl = [mnl]
            if relation_limit and relation_limit in mnl:
                mnl = [relation_limit]
            for mn2 in mnl:
                lookup = "%s__in" % fn
                if mn2 == 'auth.user':
                    lkd = {lookup: [user.id]}
                elif mn2 == r:
                    lkd = {lookup: [role.id]}
                else:
                    m2 = apps.get_model(mn2)
                    field = m._meta.get_field(fn)
                    pqset = filter_query_set_for_user(mn2, user, scope_map=scope_map, relation_lookups=relation_lookups)
                    # print field, ids
                    if isinstance(field, GenericForeignKey):
                        lookup = "%s__in" % field.fk_field
                        ids = list(pqset.values_list('id', flat=True))
                        lkd = {field.ct_field: ContentType.objects.get_for_model(m2), lookup: ids}
                    else:
                        mrfn = 'id'
                        if field.related_model != m2:
                            f = modelutils.get_model_related_field(m2, field.related_model)
                            mrfn = f.name
                        ids = list(pqset.values_list(mrfn, flat=True))
                        lkd = {lookup: ids}
                lookup_link = Q(**lkd) if lookup_link is None else lookup_link | Q(**lkd)
    if lookup_link:
        qset = qset.filter(lookup_link)
        try:
            if [f for f in m._meta.fields if f.name == 'is_active']:
                qset = qset.filter(is_active=True)
        except:
            import traceback
            log.error('filter_query_set_for_user %s:%s error. %s', mn, lookup_link, traceback.format_exc())
        return qset.distinct()
    return qset.none()



def user_has_model_permission(model, user, action):
    from django.db.models import QuerySet
    if isinstance(model, QuerySet):
        model = model.model
    meta = model._meta
    mn = hasattr(model, 'alias') and meta.app_label + '.' + model.alias.lower() or meta.label_lower
    from . import get_user_model_permissions
    ump = get_user_model_permissions(user)
    if not ump:
        return False
    ps = ump.get(mn)
    return ps and action in ps
    # for r in [a.name for a in get_roles()]:
    #     if r not in scope_map or not hasattr(user, r):
    #         continue
    #
    #     d = scope_map.get(r)
    #     if '@all' in d:
    #         return True
    #     if mn not in d:
    #         continue
    #     d2 = d.get(mn)
    #     if '@all' in d2:
    #         return True
    #     if action in d2.get('actions', []) + d2.get('batch_actions', []):
    #         return True


def extract_actions(d, mds):
    res = {}
    for mn, conf in d.iteritems():
        res.setdefault(mn, set())
        if '@all' in conf:
            res[mn] = mds[mn]
        else:
            acs = conf.get('actions', []) + ['batch_%s' % b for b in conf.get('batch_actions', [])]
            res[mn].update(acs)
    return res


def get_user_model_permissions(user, scope_map=USER_ROLE_MODEL_MAP):
    from xyz_restful.helper import get_model_actions
    res = {}
    mds = get_model_actions()
    for r in [a.name for a in get_roles()]:
        if r not in scope_map or not hasattr(user, r):
            continue
        d = scope_map.get(r)
        if '@all' in d:
            return mds
        res.update(extract_actions(d, mds))
    return res


def find_user_ids_by_tag(tag):
    translation.activate(settings.LANGUAGE_CODE)
    ps = tag.split(':')
    lookup_values = ps[-1]
    mvn = '用户'
    fvn = '名称'
    if len(ps) == 2:
        ps2 = ps[0].split('.')
        mvn = ps2[0]
        if len(ps2) == 2:
            fvn = ps2[1]
    if mvn == '用户' and fvn == 'id':
        return [int(a) for a in lookup_values.split(',')]
    ms = modelutils.get_model_verbose_name_map().get(mvn)
    model = ms and ms[0]
    if not model:
        return []
    mfvm = modelutils.get_model_field_verbose_name_map(model)
    field = mfvm.get(fvn)
    if not field:
        field = model._meta.get_field('first_name' if mvn == '用户' else 'name')
    qset = model.objects.all()
    if lookup_values != '*':
        lookup = {}
        lookup_name = '%s__name__in' % field.name if field.is_relation else '%s__in' % field.name
        lookup[lookup_name] = lookup_values.split(',')
        qset = qset.filter(**lookup)
    for role in get_roles():
        rmodel = role.related_model
        if model == rmodel:
            return qset.values_list('user_id', flat=True)
        if mvn == '用户':
            return qset.values_list('id', flat=True)
        r = modelutils.get_relations(rmodel, model)
        if r:
            f = r[0]
            lookup = {}
            lookup['%s__in' % f.name] = list(qset.values_list('id', flat=True))
            return rmodel.objects.filter(**lookup).values_list('user_id', flat=True)
    return qset.values_list('user_id', flat=True)


def get_all_app_models():
    r = {}
    for app in apps.get_app_configs():
        model_names = app.models.keys()
        if not model_names:
            continue
        m = r[app.label] = {}
        for model_name in model_names:
            m[model_name] = dict(full={}, part={})
    return r

def gen_appmodel_scope_map(scope_map=USER_ROLE_MODEL_MAP):
    r = get_all_app_models()
    for role_name, pm in scope_map.iteritems():
        for appmodel, setting in pm.iteritems():
            if appmodel == '@all':
                for an, app in r.iteritems():
                    for mn, model in app.iteritems():
                        model['full'][role_name] = True
                continue
            app_label, model_name = appmodel.split('.')
            am = r.setdefault(app_label, {})
            mm = am.setdefault(model_name, {})
            scope = setting.get('scope', {})
            if scope == '@all':
                mm['full'][role_name] = True
            else:
                mm['part'][role_name] = scope
    return r



def model_in_user_scope(model, user, appmodel_scope_map=None):
    asm = appmodel_scope_map
    if not asm:
        asm = gen_appmodel_scope_map()
    an, mn=model._meta.app_label, model._meta.model_name
    sm = asm[an][mn]
    for role, scope in sm['full'].iteritems():
        if scope and hasattr(user, role):
            return True
    for role, scope in sm['part'].iteritems():
        if scope and hasattr(user, role):
            for field_name, relations in scope.iteritems():
                if isinstance(relations, (str, unicode)):
                    relations=[relations]
                field = model._meta.get_field(field_name)
                if field.is_relation:
                    if field.many_to_one or field.one_to_one:
                        rel_model = getattr(model, field_name)
                        if not rel_model:
                            continue
                        meta = rel_model._meta
                        app_model = '%s.%s' % (meta.app_label, meta.model_name)

                        if app_model == 'auth.user':
                            if getattr(model, '%s_id' % field_name) == user.id:
                                return True
                        elif role in relations:
                            if rel_model.id == getattr(user, role).id:
                                return True
                        elif app_model in relations:
                            b = model_in_user_scope(rel_model, user, asm)
                            if b:
                                return True
                    else:
                        rel_qset = getattr(model, field_name)
                        meta = rel_qset.model._meta
                        app_model = '%s.%s' % (meta.app_label, meta.model_name)
                        if app_model == 'auth.user':
                            if rel_qset.filter(id= user.id).exists():
                                return True
                        if role in relations:
                            if rel_qset.filter(id= getattr(user, role).id).exists():
                                return True
                        elif app_model in relations:
                            b = filter_query_set_for_user(rel_qset, user).exists()
                            if b:
                                return True
    return False


def get_relation_limit(request, queryset):
    gfk = modelutils.get_generic_foreign_key(queryset.model._meta)
    if not gfk:
        return
    pms = request.query_params
    ctid = pms.get(gfk.ct_field)
    if not ctid:
        return
    ct = ContentType.objects.get_for_id(ctid)
    return '%s.%s' % (ct.app_label, ct.model)

