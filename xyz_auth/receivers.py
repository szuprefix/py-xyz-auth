# -*- coding:utf-8 -*-
from django.dispatch import receiver
from .signals import to_bind_user, to_change_user_name
from django.db.models.signals import post_save

@receiver(to_bind_user)
def bind_user(sender, **kwargs):
    old_user = kwargs['old_user']
    new_user = kwargs['new_user']
    if hasattr(old_user, "as_wechat_user"):
        wuser = old_user.as_wechat_user
        wuser.user = new_user
        wuser.save()

def change_user_name(sender, **kwargs):
    created = kwargs['created']
    user = kwargs['user']
