"""Private in-process ASGI contract checks, no endpoint or serving grant."""
import json
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.testclient import TestClient
from sus_health_mcp import server
from sus_health_mcp.usage import UsageLog
from sus_health_mcp.rate_limit import RateLimit


def client_app():
 inner=server.mcp.streamable_http_app()
 wrapped=RateLimit(UsageLog(inner,[t.name for t in server.mcp._tool_manager.list_tools()]))
 return Starlette(routes=[Mount('/',app=wrapped)],lifespan=inner.router.lifespan_context)


def test_http_unready_contract_and_input_bounds(tmp_path,monkeypatch):
 monkeypatch.setattr(server,'ROOT',tmp_path)
 monkeypatch.setenv('SUS_USAGE_DB',str(tmp_path/'usage.db'))
 headers={'accept':'application/json, text/event-stream'}
 with TestClient(client_app(),base_url='https://sus-health-mcp.fly.dev') as c:
  assert c.get('/healthz').status_code==503
  response=c.post('/mcp',headers=headers,json={'jsonrpc':'2.0','id':1,'method':'tools/list','params':{}})
  assert response.status_code==200
  tools=response.json()['result']['tools']
  assert len(tools)==7
  assert all(t['inputSchema']['additionalProperties'] is False for t in tools)
  def call(arguments):
   return c.post('/mcp',headers=headers,json={'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'fixed_proxy_activity','arguments':arguments}}).json()['result']
  assert call({'proxy':'a','year':2024,'uf':'RO'})['isError'] is True
  assert call({'proxy':'a','year':2024,'uf':'RO','patient_id':'x'})['isError'] is True
  assert call({'proxy':'a','year':'2024','uf':'RO'})['isError'] is True
  assert c.post('/mcp',headers=headers,content=b'x'*131073).status_code==413
  statuses=[c.get('/healthz').status_code for _ in range(41)]
  assert 429 in statuses
