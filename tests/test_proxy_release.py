import pytest
from sus_health_mcp.proxy_release import reduce_proxy_events, assess_elevation


def event(key, m, p, n):
    return dict(source_cell=key, municipality=m, proxies=p, activity=n)


def test_aggregate_before_suppression():
    x = reduce_proxy_events([event('a','1',['a'],15),event('b','1',['a'],15)], {'1':100}, ['a'])
    assert x['rows'][0]['lower'] == 30
    assert x['release_ready'] is False


def test_unattributed_mass_can_remove_elevation():
    pop = {'1':1000,'2':1000,'3':1000}
    base = [event(p,'1',[p],100) for p in ['a','b']]
    x = reduce_proxy_events(base,pop,['a','b'])
    assert assess_elevation(x,pop,['a','b'])['rows']
    x = reduce_proxy_events(base+[event('unknown'+p,'?', [p],1000) for p in ['a','b']],pop,['a','b'])
    assert assess_elevation(x,pop,['a','b'])['rows'] == []


def test_overlap_duplicate_and_bad_activity_block():
    for events in [[event('1','1',['a','b'],30)], [event('1','1',['a'],30)]*2, [event('1','1',['a'],1.5)]]:
        with pytest.raises(ValueError):reduce_proxy_events(events,{'1':100},['a','b'])
