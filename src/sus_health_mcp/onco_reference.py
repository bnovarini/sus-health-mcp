"""Phase7c oncology reference: DATASUS PAINEL-Oncologia published aggregates. Fixed views only; import starts no listener or public route."""
import pathlib,json,hashlib,base64,csv,threading,os
R=os.environ.get('SUS_ONCO_REF_DATA','data/oncology-reference')
VIEWS=['diag_agr_x_ano','diag_det_x_ano','uf_res_x_ano','tempo_trat_x_ano','modalidade_x_ano','estadiamento_x_ano']
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
class OncoReference:
 def __init__(self,root=R):
  self.root=pathlib.Path(root);self.meta=json.loads((self.root/'manifest.json').read_text());self.lock=threading.BoundedSemaphore(1)
  self.tables={}
  for v in VIEWS:
   p=self.root/(v+'.csv');assert not p.is_symlink() and digest(p)==self.meta['files'][v+'.csv']['sha256'],'artifactintegrity'
   rows=list(csv.reader(open(p,encoding='iso-8859-1'),delimiter=';',quotechar='"'))
   header=rows[0];data=[]
   for r in rows[1:]:
    if len(r)!=len(header) or not r[0]:continue
    data.append({'category':r[0],'counts_by_year':{header[i]:int(r[i]) for i in range(1,len(header))}})
   self.tables[v]={'rows':data,'sha256':self.meta['files'][v+'.csv']['sha256']}
 def page(self,view,limit=100,cursor=''):
  if view not in VIEWS:raise ValueError('Unsupported fixed view')
  if type(limit)!=int or not 1<=limit<=100:raise ValueError('Limit1-100')
  t=self.tables[view];off=0
  if cursor:
   try:d=json.loads(base64.urlsafe_b64decode(cursor))
   except Exception:raise ValueError('Invalidcursor')
   if d.get('view')!=view or d.get('sha256')!=t['sha256'] or type(d.get('offset'))!=int or d['offset']<0:raise ValueError('Cursor belongs to another scope/artifact')
   off=d['offset']
  if not self.lock.acquire(blocking=False):raise ValueError('Datasetbusy;retry')
  try:rows=t['rows'][off:off+limit+1]
  finally:self.lock.release()
  more=len(rows)>limit;rows=rows[:limit]
  return {'rows':rows,'has_more':more,'next_cursor':base64.urlsafe_b64encode(json.dumps({'view':view,'sha256':t['sha256'],'offset':off+limit}).encode()).decode() if more else None,'view':view,'view_description':self.meta['views'][view],'artifact_sha256':t['sha256'],'status':self.meta.get('status','private_candidate_not_released'),'source':self.meta['source'],'panel_data_updated':self.meta['panel_data_updated'],'column':self.meta['column'],'measure':self.meta['measure'],'citation':'DATASUS TabNet PAINEL-Oncologia published aggregates; exact counts as published by DATASUS; 2026 partial year-to-date','release_id':self.meta['package']}
 def methods(self):return self.meta
