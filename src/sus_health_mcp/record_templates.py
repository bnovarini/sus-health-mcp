"""Fixed phase6 RD record-template adapter. Private candidate; import starts no listener or public route."""
import pathlib,json,hashlib,base64,re,threading,os
R=os.environ.get('SUS_RECORD_TEMPLATES_DATA','data/record-templates')
UF='AC AL AP AM BA CE ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split()
TEMPLATES={
 'rd_principal_age':['uf','year','cid','age_band'],
 'rd_principal_sex':['uf','year','cid','recorded_sex'],
 'rd_recorded_outcome':['uf','year','cid','aih_type','morte_category'],
 'rd_recorded_stay':['uf','year','cid','aih_type','stay_bin'],
}
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb')as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
class RecordTemplates:
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
  cols=TEMPLATES[template];key='|'.join(cols)
  spec={'template':template,'uf':uf,'year':year,'cid':cid};q=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest();art=self.meta['artifacts'][template];off=0
  if cursor:
   try:d=json.loads(base64.urlsafe_b64decode(cursor))
   except Exception:raise ValueError('Invalidcursor')
   if d.get('query')!=q or d.get('sha256')!=art['sha256']or type(d.get('offset'))!=int or d['offset']<0:raise ValueError('Cursor belongs to another scope/artifact')
   off=d['offset']
  if not self.lock.acquire(blocking=False):raise ValueError('Datasetbusy;retry')
  try:
   c=duckdb.connect();c.execute("SET memory_limit='128MB'");c.execute('SET threads=1');p=self.root/art['filename']
   cur=c.execute("SELECT * FROM read_parquet(?) WHERE uf=? AND year=? AND (?='' OR cid=?) ORDER BY ALL LIMIT ? OFFSET ?",[str(p),uf,year,cid,cid,limit+1,off]);rows=[dict(zip([x[0]for x in cur.description],r))for r in cur.fetchall()];c.close()
  finally:self.lock.release()
  more=len(rows)>limit;rows=rows[:limit]
  return {'rows':rows,'has_more':more,'next_cursor':base64.urlsafe_b64encode(json.dumps({'query':q,'sha256':art['sha256'],'offset':off+limit}).encode()).decode()if more else None,'query_spec':spec,'artifact_sha256':art['sha256'],'release_id':self.meta['release_id'],'status':'private_candidate_not_released','unit':self.meta['unit'],'time_basis':'Processingfileyear;2026Jan-Julpartial,notnecessarilyattendancedate','geography':self.meta['geography'],'missing':'Unknown;threshold,targetedwithholding,missingperiodorabsentcodecannotbedistinguished;withheldisneverzero','no_new_totals':True,'limits':self.meta['limits'],'warnings':self.meta['warnings']}
 def comparison(self,template,uf,year,cid_a,cid_b):
  import duckdb
  self._check(template,uf,year,100)
  for cid in (cid_a,cid_b):
   if not re.fullmatch('[A-Z0-9]{1,8}',cid):raise ValueError('Exact source CID string only')
  if cid_a==cid_b:raise ValueError('Two distinct exact CIDs required')
  cols=TEMPLATES[template];strata=[c for c in cols if c not in ('uf','year','cid')];art=self.meta['artifacts'][template]
  if not self.lock.acquire(blocking=False):raise ValueError('Datasetbusy;retry')
  try:
   c=duckdb.connect();c.execute("SET memory_limit='128MB'");c.execute('SET threads=1');p=self.root/art['filename']
   cur=c.execute("SELECT * FROM read_parquet(?) WHERE uf=? AND year=? AND cid IN (?,?) ORDER BY ALL",[str(p),uf,year,cid_a,cid_b]);rows=[dict(zip([x[0]for x in cur.description],r))for r in cur.fetchall()];c.close()
  finally:self.lock.release()
  bykey={}
  for r in rows:
   k=tuple(str(r[s]) for s in strata);bykey.setdefault(k,{})[r['cid']]=[r['records_lower'],r['records_upper']]
  out=[]
  for k,v in bykey.items():
   row=dict(zip(strata,k));row['a']=v.get(cid_a);row['b']=v.get(cid_b);out.append(row)
  return {'template':template,'uf':uf,'year':year,'cid_a':cid_a,'cid_b':cid_b,'strata':strata,'rows':out,'a_null_or_b_null':'Absentcellisunknown(threshold,withholdingorabsentcode),neverzero','release_id':self.meta['release_id'],'status':'private_candidate_not_released','unit':self.meta['unit'],'limits':self.meta['comparison_limits'],'no_statistics':'Descriptiverecordintervalsonly;nop-values,oddsratios,risk,qualityrankingorcausalreading;ratiosonlyfromthesedisplayedintervals'}
 def methods(self):return self.meta
