import pytest
from sus_health_mcp.readiness import validate,REQUIRED_GATES


def complete():
    return {'release_ready':True,'release_id':'test-only','artifacts':['test-only'], 'person_linkage':False,'gates':{g:{'status':'passed','evidence':['test-only']} for g in REQUIRED_GATES}}


def test_boolean_alone_cannot_enable_serving():
    with pytest.raises(ValueError):validate({'release_ready':True})


def test_each_gate_and_evidence_required():
    for g in REQUIRED_GATES:
        m=complete();m['gates'][g]['status']='pending'
        with pytest.raises(ValueError):validate(m)
        m=complete();m['gates'][g]['evidence']=[]
        with pytest.raises(ValueError):validate(m)
    assert validate(complete()) is True


def test_no_linkage_flag_required():
    m=complete();m['person_linkage']=True
    with pytest.raises(ValueError):validate(m)


def test_artifact_hashes_paths_and_tool_coverage(tmp_path):
 import hashlib
 from sus_health_mcp.readiness import validate_artifacts
 m=complete()
 names=['capacity.parquet','fixed-proxies.json','ecological-hits.json','protocol-associations.json']
 m['artifacts']={}
 for n in names:
  b = b'{"rows":[]}' if n.endswith('.json') else b'test-only'
  (tmp_path/n).write_bytes(b)
  m['artifacts'][n]=hashlib.sha256(b).hexdigest()
 assert validate_artifacts(m,tmp_path)
 (tmp_path/names[0]).write_bytes(b'changed')
 with pytest.raises(ValueError,match='checksum'):validate_artifacts(m,tmp_path)
 (tmp_path/names[0]).write_bytes(b'test-only')
 m['artifacts']['../outside']='a'*64
 with pytest.raises(ValueError,match='Unreviewed'):validate_artifacts(m,tmp_path)
 del m['artifacts']['../outside']; del m['artifacts']['ecological-hits.json']
 with pytest.raises(ValueError,match='missing'):validate_artifacts(m,tmp_path)
