import asyncio,json,sqlite3
from sus_health_mcp.usage import UsageLog,MAX_BODY_BYTES
from sus_health_mcp.rate_limit import RateLimit

def scope():return {'type':'http','method':'POST','path':'/mcp','headers':[(b'fly-client-ip',b'1.2.3.4'),(b'user-agent',b'secret-agent')],'client':('1.2.3.4',123)}
def test_large_body_rejected():
 out=[];called=[]
 async def app(*args):called.append(1)
 async def send(m):out.append(m)
 async def recv():return {'type':'http.request','body':b'x'*(MAX_BODY_BYTES+1),'more_body':False}
 asyncio.run(UsageLog(app,[])(scope(),recv,send))
 assert not called and out[0]['status']==413

def test_no_sensitive_query_log(tmp_path,monkeypatch):
 monkeypatch.setenv('SUS_USAGE_DB',str(tmp_path/'usage.db'));body=json.dumps({'method':'tools/call','params':{'name':'dataset_info','arguments':{'secret':'should-not-store'}}}).encode();out=[]
 async def send(m):pass
 async def recv():return {'type':'http.request','body':body,'more_body':False}
 async def app(s,r,se):out.append(await r())
 asyncio.run(UsageLog(app,['dataset_info'])(scope(),recv,send))
 assert out[0]['body']==body
 c=sqlite3.connect(tmp_path/'usage.db');r=str(c.execute('select * from usage').fetchall())
 assert 'dataset_info' in r and not any(v in r for v in ['should-not-store','1.2.3.4','secret-agent'])

def test_rate_limit():
 out=[]
 async def app(*args):pass
 async def send(m):out.append(m)
 async def recv():return {'type':'http.request','body':b'','more_body':False}
 async def go():
  app2=RateLimit(app,per_minute=1)
  await app2(scope(),recv,send);await app2(scope(),recv,send)
 asyncio.run(go());assert out[0]['status']==429
