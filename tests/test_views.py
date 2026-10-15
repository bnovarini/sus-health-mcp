import pytest
from sus_health_mcp.views import visible_activity

def row(**kw):
 return dict(family='RD',year=2024,uf='AC',municipality='120040',cid='E752',procedure='0604240023',records_lower=20,records_upper=29,quantity_lower=10,quantity_upper=19,**kw)

def test_admissions_are_not_aih_records():
 x=visible_activity([row()],family='RD',years=[2024]);assert x['rows'][0]['visible_lower']==10
 assert 'not people' in x['unit']

def test_all_views_use_same_cells():
 rows=[row(),{**row(),'procedure':'0604240031','quantity_lower':20,'quantity_upper':29}]
 total=visible_activity(rows,family='RD',years=[2024])
 detail=visible_activity(rows,family='RD',years=[2024],by='procedure')
 assert total['rows'][0]['visible_lower']==sum(x['visible_lower'] for x in detail['rows'])
 assert total['rows'][0]['visible_upper']==sum(x['visible_upper'] for x in detail['rows'])

def test_missing_is_not_zero_and_duplicate_blocks():
 assert visible_activity([],family='DO',years=[2024])['rows']==[]
 with pytest.raises(ValueError,match='Duplicate'):
  visible_activity([row(),row()],family='RD',years=[2024])
 with pytest.raises(ValueError):visible_activity([],family='DO',years=[2024],procedure='0604240023')
 with pytest.raises(ValueError):visible_activity([],family='RD',years=[2024],cid_prefix="E75' OR 1=1")
