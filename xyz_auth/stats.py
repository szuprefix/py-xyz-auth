# -*- coding:utf-8 -*- 
# author = 'denishuang'
from __future__ import unicode_literals
from xyz_util import statutils


def stats_login(qset=None, measures=None, period=None):
    from xyz_common.models import Event
    qset = qset if qset is not None else Event.objects.filter(name__startswith='login')
    qset = statutils.using_stats_db(qset)
    dstat = statutils.DateStat(qset, 'create_time')
    gm = {'login.wechat.mp.qrcode': u'电脑扫码', 'login.wechat.mp': u'微信公号', 'login.mobile': u'手机号', 'login': u'帐号密码',
          'login.temptoken': u'临时密码'}
    funcs = {
        'today': lambda: dstat.stat("今天", count_field="owner_id", distinct=True, only_first=True),
        'yesterday': lambda: dstat.stat("昨天", count_field="owner_id", distinct=True, only_first=True),
        'all': lambda: qset.values("owner_id").distinct().count(),
        'count': lambda: dstat.get_period_query_set(period).count(),
        'daily': lambda: dstat.stat(period, count_field='owner_id', distinct=True),
        'type': lambda: statutils.count_by(
            dstat.get_period_query_set(period),
            'name',
            count_field='owner_id',
            distinct=True, sort="-", group_map=gm)
    }
    return dict([(m, funcs[m]()) for m in measures])
