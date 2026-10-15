"""Bound HTTP workload; IPs stay only in short-lived memory, never logs."""
import time,collections,threading
class RateLimit:
 def __init__(self,app,per_minute=40):self.app=app;self.limit=per_minute;self.buckets={};self.lock=threading.Lock()
 async def __call__(self,scope,receive,send):
  if scope['type']!='http':return await self.app(scope,receive,send)
  h=dict(scope.get('headers',[]));key=h.get(b'fly-client-ip') or str(scope.get('client')).encode();now=time.monotonic()
  with self.lock:
   q=self.buckets.setdefault(key,collections.deque())
   while q and now-q[0]>60:q.popleft()
   blocked=len(q)>=self.limit
   if not blocked:q.append(now)
   if len(self.buckets)>10000:self.buckets={k:v for k,v in self.buckets.items() if v and now-v[-1]<60}
  if blocked:
   await send({'type':'http.response.start','status':429,'headers':[(b'content-type',b'application/json'),(b'retry-after',b'60')]})
   await send({'type':'http.response.body','body':b'{"error":"Rate limit exceeded"}'})
  else:await self.app(scope,receive,send)
