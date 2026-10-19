"""RD co-diagnosis pair intervals. Approved private release 2026-10-19; import starts no listener."""
import pathlib,json,hashlib,base64,re,threading,os
R=os.environ.get('SUS_CODIAGNOSIS_DATA','/app/data/codiagnosis')
UF='AC AL AP AM BA CE ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split()
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb')as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
class Codiagnosis:
 def __init__(self,root=R):
  self.root=pathlib.Path(root);self.meta=json.loads((self.root/'metadata.json').read_text());self.lock=threading.BoundedSemaphore(1)
  for aid,art in self.meta['artifacts'].items():
   p=self.root/art['filename'];assert not p.is_symlink()and digest(p)==art['sha256'],'artifactintegrity'
  self.cov=json.loads((self.root/self.meta['artifacts']['coverage']['filename']).read_text())
 def _cid(self,cid):
  if type(cid)!=str or not re.fullmatch('[A-Z0-9]{1,8}',cid):raise ValueError('Exact source CID string only')
 def pairs(self,cid,uf='',year=0,limit=100,cursor=''):
  import duckdb
  self._cid(cid)
  if uf and uf not in UF:raise ValueError('UF invalid;DF/unknown excluded,notzero')
  if type(year)!=int or year not in (0,2022,2023,2024,2025,2026):raise ValueError('Year2022-2026or0forall')
  if type(limit)!=int or not 1<=limit<=100:raise ValueError('Limit1-100')
  spec={'cid':cid,'uf':uf,'year':year};q=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest();art=self.meta['artifacts']['codiagnosis'];off=0
  if cursor:
   try:d=json.loads(base64.urlsafe_b64decode(cursor))
   except Exception:raise ValueError('Invalidcursor')
   if d.get('query')!=q or d.get('sha256')!=art['sha256']or type(d.get('offset'))!=int or d['offset']<0:raise ValueError('Cursor belongs to another scope/artifact')
   off=d['offset']
  if not self.lock.acquire(blocking=False):raise ValueError('Datasetbusy;retry')
  try:
   c=duckdb.connect();c.execute("SET memory_limit='128MB'");c.execute('SET threads=1');p=self.root/art['filename']
   cur=c.execute("SELECT * FROM read_parquet(?) WHERE (principal=? OR secondary=?) AND (?='' OR uf=?) AND (?=0 OR year=?) ORDER BY ALL LIMIT ? OFFSET ?",[str(p),cid,cid,uf,uf,year,year,limit+1,off]);rows=[dict(zip([x[0]for x in cur.description],r))for r in cur.fetchall()];c.close()
  finally:self.lock.release()
  more=len(rows)>limit;rows=rows[:limit]
  return {'rows':rows,'has_more':more,'next_cursor':base64.urlsafe_b64encode(json.dumps({'query':q,'sha256':art['sha256'],'offset':off+limit}).encode()).decode()if more else None,'query_spec':spec,'artifact_sha256':art['sha256'],'release_id':self.meta['release_id'],'unit':self.meta['unit'],'pair_semantics':self.meta['pair_semantics'],'time_basis':'Processingfileyear;2026Jan-Julpartial','geography':self.meta['geography'],'missing':'Withheldcellsareabsent;absentisunknown(threshold,withholdingorabsentpair),neverzero','limits':self.meta['limits']}
 def coverage(self,cid=''):
  out={'release_id':self.meta['release_id'],'unit':self.meta['unit'],'pair_eligible_share':self.meta['pair_eligible_share'],'record_selection':self.meta['record_selection'],'disclosure':self.meta['disclosure'],'totals':self.meta['totals'],'years':self.meta['years'],'geography':self.meta['geography']}
  if cid:
   self._cid(cid);d=self.cov.get(cid)
   out['cid']=cid;out['cid_coverage']=d if d else 'No served cells and no withheld-cell aggregate for this exact CID; absent is unknown, never zero'
  return out
 def methods(self):return self.meta
