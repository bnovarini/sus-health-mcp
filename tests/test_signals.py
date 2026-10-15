from sus_health_mcp.signals import rank_pockets
import pytest

def test_multisignal_not_person_count():
 p={'1':1000,'2':1000,'3':1000};r=[{'municipality':'1','signal':s,'lower':100,'upper':109} for s in ['a','b']]+[{'municipality':'2','signal':s,'lower':20,'upper':29} for s in ['a','b']]
 x=rank_pockets(r,p,['a','b'],coverage_complete=True,suppression_grain_matches_signal=True);assert len(x)==1 and x[0]['municipality']=='1'
 assert 'not the same people' in x[0]['meaning']
def test_no_single_signal_or_duplicates():
 with pytest.raises(ValueError):rank_pockets([],{},['a'])
 r=[dict(municipality='1',signal='a',lower=20,upper=29)]*2
 with pytest.raises(ValueError):rank_pockets(r,{'1':100},['a','b'])


def test_missing_coverage_blocks_ranking():
 with pytest.raises(ValueError,match='coverage'):
  rank_pockets([],{'1':100},['a','b'])

def test_suppressed_baseline_is_not_zero():
 p={str(i):1000 for i in range(100)}
 r=[{'municipality':'0','signal':s,'lower':20,'upper':29} for s in ['a','b']]
 assert rank_pockets(r,p,['a','b'],coverage_complete=True,suppression_grain_matches_signal=True)==[]


def test_finer_cell_suppression_cannot_supply_signal_bound():
 with pytest.raises(ValueError,match="Signal-grain"):
  rank_pockets([], {"120040":1000}, ["a","b"], coverage_complete=True)
