# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from xyz_util import modelutils


class Authority(models.Model):
    class Meta:
        verbose_name_plural = verbose_name = "权力"

    user = models.OneToOneField('auth.user', related_name='xauth_authority', on_delete=models.PROTECT)
    user_name = models.CharField("姓名", max_length=64, unique=True)
    roles = modelutils.JSONField("角色", blank=True, default={})
    create_time = models.DateTimeField("创建时间", auto_now_add=True)
    modify_time = models.DateTimeField("修改时间", auto_now=True)

    def __unicode__(self):
        return self.user_name

    @property
    def active_roles(self):
        rs = {}
        for k, v in self.roles.items():
            if v.get('is_active'):
                rs[k] = v
        return rs

    def save(self, **kwargs):
        from .helper import get_user_roles
        from django.contrib.contenttypes.models import ContentType
        user = self.user
        roles = {}
        for rf in get_user_roles():
            r = getattr(user, rf.name,None)
            if not r:
                continue
            roles[rf.name] = dict(
                id=r.pk,
                name=rf.name,
                content_type_id=ContentType.objects.get_for_model(r),
                is_active=getattr(r, 'is_active', True)
            )
        self.roles = roles
        self.user_name=user.get_full_name()
        super(Authority, self).save(**kwargs)
