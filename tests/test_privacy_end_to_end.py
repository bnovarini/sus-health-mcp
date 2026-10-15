import hashlib,json
import pytest
from sus_health_mcp import server
from sus_health_mcp.proxy_release import reduce_proxy_events
from sus_health_mcp.published_hits import sanitize
from sus_health_mcp.fixed_candidate import prepare
from sus_health_mcp.readiness import REQUIRED_GATES


def row(p='a',**kw):
 return dict(year=2024,municipality='110001',uf='RO',proxy=p,lower=20,upper=29,**kw)


def test_boundary_every_event_count():
 for n in range(201):
  c=reduce_proxy_events([dict(source_cell='x',municipality='110001',proxies=['a'],activity=n)],{'110001':100},['a'])
  assert bool(c['rows']) == (n>=20)
  if c['rows']:
   r=c['rows'][0];assert 20<=r['lower']<=n<=r['upper'] and r['upper']-r['lower']==9


def test_record_threshold_is_not_patient_threshold():
 # All100events could be repeated care for one individual. There are no person
 # keys, so the reducer intentionally cannot make a distinct-person assertion.
 c=reduce_proxy_events([dict(source_cell='x',municipality='110001',proxies=['a'],activity=100)],{'110001':100},['a'])
 assert len(c['rows'])==1 and 'not patient anonymity' in c['claim']


def test_misleading_free_text_never_echoed():
 h=dict(context='test',year=2024,uf='RO',municipality='110001',proxies=['a','b'],meaning='Confirmed patient location',uncertainty='No uncertainty')
 r=sanitize(h)
 assert 'Confirmed' not in json.dumps(r) and 'not a patient location' in r['meaning']


@pytest.mark.parametrize('change',[{'municipality':'120001'}, {'uf':'AC'}, {'lower':19}, {'upper':20}])
def test_candidate_blocks_invalid_geography_and_intervals(tmp_path,change):
 r={**row(),**change}
 with pytest.raises(ValueError):
  prepare(tmp_path/'candidate',[r],[],source_manifest_sha256='a'*64,years=[2024],proxies=['a'],contexts=['test'])
 assert not (tmp_path/'candidate').exists()


def install_fixture(tmp_path, monkeypatch, rows, hits):
 monkeypatch.setattr(server,'ROOT',tmp_path)
 payloads={'capacity.parquet':b'fixture-only',
 'fixed-proxies.json':json.dumps({'rows':rows}).encode(),
 'ecological-hits.json':json.dumps({'rows':hits,'reviewed_scopes':['test:2024:RO']}).encode(),
 'protocol-associations.json':b'{}'}
 for n,b in payloads.items():(tmp_path/n).write_bytes(b)
 m=dict(release_ready=True,release_id='fixture-only',person_linkage=False,
 gates={g:{'status':'passed','evidence':['fixture-only']} for g in REQUIRED_GATES},
 artifacts={n:hashlib.sha256(b).hexdigest() for n,b in payloads.items()},
 approved_proxies=['a','b'],approved_hit_contexts=['test'],proxy_years=[2024])
 (tmp_path/'metadata.json').write_text(json.dumps(m))


def test_hash_valid_but_suppressed_hit_blocks_entire_runtime(tmp_path,monkeypatch):
 h=dict(context='test',year=2024,uf='RO',municipality='110001',proxies=['a','b'])
 install_fixture(tmp_path,monkeypatch,[row()],[h])
 for call in [lambda:server.ecological_hits('test',2024,'RO'),lambda:server.fixed_proxy_activity('a',2024,'RO'),lambda:server.geographic_signals('RO',2024)]:
  with pytest.raises(ValueError,match='suppressed'):call()


def test_named_hit_contains_only_visible_fixed_cells_and_safe_words(tmp_path,monkeypatch):
 h=dict(context='test',year=2024,uf='RO',municipality='110001',proxies=['a','b'],meaning='Patient location')
 install_fixture(tmp_path,monkeypatch,[row('a'),row('b')],[h])
 out=server.ecological_hits('test',2024,'RO')
 assert out['status']=='supported_ecological_hit'
 assert 'Ecological research priorities' in out['meaning']
 assert 'Patient location' not in json.dumps(out)
 assert all(server.fixed_proxy_activity(p,2024,'RO')['rows'] for p in out['hits'][0]['proxies'])
