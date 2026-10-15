import pytest
from sus_health_mcp.fixed_views import activity


def test_final_grain_only_and_unknown_missing():
 r={'year':2024,'municipality':'110001','uf':'RO','proxy':'a','lower':20,'upper':29}
 out=activity([r],'a',[2024]);assert len(out['rows'])==1 and 'never zero' in out['missing']
 assert activity([r],'a',[2023])['rows']==[]
 with pytest.raises(ValueError):activity([r,r],'a',[2024])
 with pytest.raises(ValueError):activity([{**r,'lower':19}],'a',[2024])


def test_fixed_intervals_cannot_be_arbitrarily_narrowed():
 r={'year':2024,'municipality':'110001','uf':'RO','proxy':'a','lower':20,'upper':29}
 for change in [{'upper':20},{'lower':21,'upper':30},{'lower':20.0},{'upper':100}]:
  with pytest.raises(ValueError):activity([{**r,**change}],'a',[2024])
