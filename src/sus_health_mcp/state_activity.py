"""Private phase2 candidate only. Import starts no listener or public route."""
import pathlib,json,hashlib,base64,re,threading
R=pathlib.Path(__import__('os').environ.get('SUS_STATE_DATA','/app/data/state'))
UF='AC AL AP AM BA CE ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split()
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb')as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
class StateCandidate:
 def __init__(self,root=R):
  self.root=pathlib.Path(root);self.meta=json.loads((self.root/'phase2-metadata.json').read_text());self.lock=threading.BoundedSemaphore(1)
  for kind in ['cid','procedure']:
   p=self.root/self.meta['artifacts'][kind]['filename'];assert not p.is_symlink()and digest(p)==self.meta['artifacts'][kind]['sha256'],'artifactintegrity'
 def page(self,kind,uf,year,family,code='',limit=100,cursor=''):
  import duckdb
  if kind not in ['cid','procedure']or uf not in UF or type(year)!=int or year not in range(2022,2027)or family not in ['RD','PA','AM']:raise ValueError('Unsupported fixed scope;DF/unknown excluded,notzero')
  if type(limit)!=int or not 1<=limit<=100:raise ValueError('Limit1-100')
  if code and not re.fullmatch('[A-Z0-9]{1,10}',code):raise ValueError('Exact sourcecode only')
  spec={'kind':kind,'uf':uf,'year':year,'family':family,'code':code};q=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest();art=self.meta['artifacts'][kind];last=''
  if cursor:
   try:d=json.loads(base64.urlsafe_b64decode(cursor))
   except Exception:raise ValueError('Invalidcursor')
   if d.get('query')!=q or d.get('sha256')!=art['sha256']or not isinstance(d.get('last'),str):raise ValueError('Cursor belongs to another scope/artifact')
   last=d['last']
  if not self.lock.acquire(blocking=False):raise ValueError('Datasetbusy;retry')
  try:
   c=duckdb.connect();c.execute("SET memory_limit='128MB'");c.execute('SET threads=1');p=self.root/art['filename'];args=[str(p),uf,year,family,code,code,last,limit+1];cur=c.execute('SELECT * FROM read_parquet(?) WHERE uf=? AND year=? AND family=? AND(?=\'\' OR '+kind+'=?)AND '+kind+'>? ORDER BY '+kind+' LIMIT ?',args);rows=[dict(zip([x[0]for x in cur.description],r))for r in cur.fetchall()];c.close()
  finally:self.lock.release()
  more=len(rows)>limit;rows=rows[:limit]
  return {'rows':rows,'has_more':more,'next_cursor':base64.urlsafe_b64encode(json.dumps({'query':q,'sha256':art['sha256'],'last':rows[-1][kind]}).encode()).decode()if more else None,'query_spec':spec,'artifact_sha256':art['sha256'],'release_id':self.meta['release_id'],'status':'fixed_state_release','unit':self.meta['units'][family],'time_basis':'Processingfileyear;2026Jan-Julpartial,notnecessarilyattendancedate','geography':'ResidenceUF;exactfrozen2024municipalitymembership;DFandunknownexcluded,notzero','missing':'Unknown;threshold,targetedwithholding,invalidgeography,missingperiodorabsentcodecannotbedistinguished','no_new_totals':True,'warnings':self.meta['warnings']}
 def methods(self):return self.meta
