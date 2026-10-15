import asyncio,json,pytest,duckdb
from sus_health_mcp import server
from pydantic import ValidationError

def test_generated_schema_forbids_extras():
 for tool in server.mcp._tool_manager.list_tools():
  assert tool.parameters['additionalProperties'] is False
 t=server.mcp._tool_manager.get_tool('geographic_signals')
 with pytest.raises(ValidationError):t.fn_metadata.arg_model.model_validate({'uf':'AC','year':2024,'patient_id':'x'})
 with pytest.raises(ValidationError):t.fn_metadata.arg_model.model_validate({'uf':'AC','year':'2024'})

def test_unready_release_blocks_data(tmp_path,monkeypatch):
 monkeypatch.setattr(server,'ROOT',tmp_path)
 with pytest.raises(ValueError,match='not ready'):server.geographic_signals('AC',2024)
 assert asyncio.run(server.health(None)).status_code==503
 (tmp_path/'metadata.json').write_text(json.dumps({'release_ready':False}))
 with pytest.raises(ValueError):server.facility_capacity('AC',2024,1)

def test_invalid_filters():
 with pytest.raises(ValueError):server.geographic_signals('XX',2024)
 with pytest.raises(ValueError):server.geographic_signals('AC',2024,cid_prefix="E75' OR 1=1")
 with pytest.raises(ValueError):server.facility_capacity('AC',2024,13)


def test_readiness_boolean_alone_cannot_unlock_tools(tmp_path,monkeypatch):
 monkeypatch.setattr(server,'ROOT',tmp_path)
 (tmp_path/'metadata.json').write_text(json.dumps({'release_ready':True}))
 with pytest.raises(ValueError,match='gates'):server.fixed_proxy_activity('test',2024,'AC')
 assert asyncio.run(server.health(None)).status_code==503


def test_new_hit_tool_fails_closed(tmp_path,monkeypatch):
 monkeypatch.setattr(server,'ROOT',tmp_path)
 with pytest.raises(ValueError,match='not ready'):server.ecological_hits('gaucher',2024,'AC')


def test_protocol_tool_cannot_publish_development_catalog(tmp_path,monkeypatch):
 monkeypatch.setattr(server,'ROOT',tmp_path)
 with pytest.raises(ValueError,match='not ready'):server.protocol_billing_association('gaucher','202401','0604240023')


def test_frozen_fixture_end_to_end_hit_and_protocol(tmp_path,monkeypatch):
 import hashlib
 from sus_health_mcp.readiness import REQUIRED_GATES
 monkeypatch.setattr(server,'ROOT',tmp_path)
 h={'context':'fixture','year':2024,'uf':'RO','municipality':'110001','proxies':['a','b']}
 payloads={'capacity.parquet':b'fixture-not-capacity',
  'fixed-proxies.json':json.dumps({'rows':[{'year':2024,'uf':'RO','municipality':'110001','proxy':p,'lower':20,'upper':29} for p in ['a','b']]}).encode(),
  'ecological-hits.json':json.dumps({'rows':[h],'reviewed_scopes':['fixture:2024:RO']}).encode(),
  'protocol-associations.json':json.dumps({'monthly_billing':[{'disease':'fixture','month':'202401','procedure':'0604240023','name':'fixture','compatible_cids':['E752'],'source':'fixture','source_sha256':'a'*64}],'protocol_periods':[]}).encode()}
 for n,b in payloads.items():(tmp_path/n).write_bytes(b)
 m={'release_ready':True,'release_id':'fixture-only','person_linkage':False,
 'gates':{g:{'status':'passed','evidence':['fixture-only']} for g in REQUIRED_GATES},
 'artifacts':{n:hashlib.sha256(b).hexdigest() for n,b in payloads.items()},
 'approved_proxies':['a','b'],'proxy_years':[2024], 'approved_hit_contexts':['fixture'],'approved_protocol_contexts':['fixture']}
 (tmp_path/'metadata.json').write_text(json.dumps(m))
 assert server.ecological_hits('fixture',2024,'RO')['status']=='supported_ecological_hit'
 assert len(server.fixed_proxy_activity('a',2024,'RO')['rows'])==1
 r=server.protocol_billing_association('fixture','202401','0604240023')
 assert r['status']=='monthly_billing_compatibility_verified'
 assert r['protocol_context']['status']=='protocol_period_unverified'
 with pytest.raises(ValueError):server.ecological_hits('fixture',2024,'AC')
 (tmp_path/'ecological-hits.json').write_text('{}')
 with pytest.raises(ValueError,match='checksum'):server.ecological_hits('fixture',2024,'RO')
 assert asyncio.run(server.health(None)).status_code==503
