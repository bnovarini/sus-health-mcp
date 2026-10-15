import json,pytest
from sus_health_mcp.fixed_candidate import prepare
from sus_health_mcp.readiness import validate


def row():
 return {'year':2024,'municipality':'110001','uf':'RO','proxy':'a','lower':20,'upper':29}


def args():
 return {'source_manifest_sha256':'a'*64,'years':[2024],'proxies':['a','b'],'contexts':['test']}


def test_candidate_never_grants_readiness_or_overwrites(tmp_path):
 out=tmp_path/'candidate';m=prepare(out,[row()],[],**args())
 assert m['release_ready'] is False and len(m['artifacts'])==2
 with pytest.raises(ValueError):validate(m)
 with pytest.raises(ValueError,match='overwritten'):prepare(out,[row()],[],**args())
 assert json.loads((out/'fixed-proxies.json').read_text())['rows']==[row()]


def test_extra_fields_and_unreviewed_grain_fail(tmp_path):
 for r in [{**row(),'exact_total':21},{**row(),'upper':20},{**row(),'year':2025}]:
  with pytest.raises(ValueError):prepare(tmp_path/'candidate',[r],[],**args())
 assert not (tmp_path/'candidate').exists()


def test_duplicate_hits_and_extra_review_scope_fail(tmp_path):
 h={'context':'test','year':2024,'uf':'RO','municipality':'110001','proxies':['a','b']}
 with pytest.raises(ValueError,match='Duplicate'):prepare(tmp_path/'candidate',[row()],[h,h],**args())
 with pytest.raises(ValueError,match='scope'):prepare(tmp_path/'candidate',[row(),{**row(),'proxy':'b'}],[h],reviewed_scopes=['test:2025:RO'],**args())
 assert not (tmp_path/'candidate').exists()


def test_hits_cannot_expose_suppressed_cells_or_unreviewed_scope(tmp_path):
 h={'context':'test','year':2024,'uf':'RO','municipality':'110001','proxies':['a','b']}
 with pytest.raises(ValueError,match='suppressed'):prepare(tmp_path/'candidate',[row()],[h],reviewed_scopes=['test:2024:RO'],**args())
 rows=[row(),{**row(),'proxy':'b'}]
 with pytest.raises(ValueError,match='joint review'):prepare(tmp_path/'candidate',rows,[h],**args())
 assert not (tmp_path/'candidate').exists()
 m=prepare(tmp_path/'candidate',rows,[h],reviewed_scopes=['test:2024:RO'],**args())
 assert m['release_ready'] is False
