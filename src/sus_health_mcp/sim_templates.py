"""Phase7a SIM role-margins adapter. Private candidate; import starts no listener or public route."""
import pathlib,json,hashlib,base64,re,threading,os
R=os.environ.get('SUS_SIM_TEMPLATES_DATA','data/sim-templates')
UF='AC AL AP AM BA CE ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split()
TEMPLATES={
 'sim_underlying_cid':['uf','year','exact_cid'],
 'sim_chain_role_cid':['uf','year','exact_cid','role'],
 'sim_reselection_cid':['uf','year','exact_cid','reselection_status'],
}
CIDCOL='exact_cid'
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb')as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
class SimTemplates:
 def __init__(self,root=R):
  self.root=pathlib.Path(root);self.meta=json.loads((self.root/'metadata.json').read_text());self.lock=threading.BoundedSemaphore(1)
  for tid,art in self.meta['artifacts'].items():
   p=self.root/art['filename'];assert not p.is_symlink()and digest(p)==art['sha256'],'artifactintegrity'
 def _check(self,template,uf,year,limit):
  if template not in TEMPLATES or uf not in UF or type(year)!=int or year not in range(2022,2027):raise ValueError('Unsupported fixed scope;DF/unknown excluded,notzero')
  if type(limit)!=int or not 1<=limit<=100:raise ValueError('Limit1-100')
 def page(self,template,uf,year,cid='',limit=100,cursor=''):
  import duckdb
  self._check(template,uf,year,limit)
  if cid and not re.fullmatch('[A-Z0-9]{1,8}',cid):raise ValueError('Exact source CID string only')
  spec={'template':template,'uf':uf,'year':year,'cid':cid};q=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest();art=self.meta['artifacts'][template];off=0
  if cursor:
   try:d=json.loads(base64.urlsafe_b64decode(cursor))
   except Exception:raise ValueError('Invalidcursor')
   if d.get('query')!=q or d.get('sha256')!=art['sha256']or type(d.get('offset'))!=int or d['offset']<0:raise ValueError('Cursor belongs to another scope/artifact')
   off=d['offset']
  if not self.lock.acquire(blocking=False):raise ValueError('Datasetbusy;retry')
  try:
   c=duckdb.connect();c.execute("SET memory_limit='128MB'");c.execute('SET threads=1');p=self.root/art['filename']
   cur=c.execute(f"SELECT * FROM read_parquet(?) WHERE uf=? AND year=? AND (?='' OR {CIDCOL}=?) ORDER BY ALL LIMIT ? OFFSET ?",[str(p),uf,str(year),cid,cid,limit+1,off]);rows=[dict(zip([x[0]for x in cur.description],r))for r in cur.fetchall()];c.close()
  finally:self.lock.release()
  more=len(rows)>limit;rows=rows[:limit]
  return {'rows':rows,'has_more':more,'next_cursor':base64.urlsafe_b64encode(json.dumps({'query':q,'sha256':art['sha256'],'offset':off+limit}).encode()).decode()if more else None,'query_spec':spec,'artifact_sha256':art['sha256'],'release_id':self.meta['release_id'],'status':self.meta.get('status','private_candidate_not_released'),'unit':self.meta['unit'],'time_basis':self.meta['time_basis'],'geography':self.meta['geography'],'preliminary':year>=2025,'missing':'Unknown;threshold,targetedwithholding,missingperiodorabsentcodecannotbedistinguished;withheldisneverzero','no_new_totals':True,'limits':self.meta['limits'],'warnings':self.meta['warnings']}
 def methods(self):return self.meta
