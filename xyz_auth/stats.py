# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals
from xyz_util import statutils

def stats_login(qset=None, measures=None, period=None):
    from django_szuprefix.common.models import Event
    qset = qset if qset is not None else Event.objects.filter(name__startswith='login')
    qset = statutils.using_stats_db(qset)
    dstat = statutils.DateStat(qset, 'create_time')
    gm = {'login.wechat.mp.qrcode': '微信扫码', 'login.wechat.mp': '微信', 'login.mobile': '手机号', 'login': '普通',
         'login.temptoken': '临时密码'}
    funcs = {
        'today': lambda: dstat.stat("今天", count_field="object_id", distinct=True, only_first=True),
        'yesterday': lambda: dstat.stat("昨天", count_field="object_id", distinct=True, only_first=True),
        'all': lambda: qset.values("object_id").distinct().count(),
        'count': lambda: dstat.get_period_query_set(period).count(),
        'daily': lambda: dstat.stat(period, count_field='object_id', distinct=True),
        'type': lambda: statutils.count_by(
            dstat.get_period_query_set(period),
            'name',
            count_field='object_id',
            distinct=True, sort="-", group_map=gm)
    }
    return dict([(m, funcs[m]()) for m in measures])
