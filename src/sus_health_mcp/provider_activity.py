"""Private fixed provider margins candidate. Import opens no listener."""
import pathlib,json,hashlib,re,threading,base64,os
R=pathlib.Path(os.getenv('SUS_PROVIDER_DATA','data/provider'));WORK=threading.BoundedSemaphore(1)
class ProviderCandidate:
 def __init__(self,root=R):
  self.root=pathlib.Path(root);self.meta=json.loads((self.root/'candidate-metadata.json').read_text())
  for outputs in self.meta['partitions'].values():
   for a in outputs.values():
    p=self.root/'candidate'/a['filename'];assert not p.is_symlink()and hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256']
 def methods(self):return self.meta
 def page(self,kind,family,year,facility,provider_municipality,code='',limit=100,cursor=''):
  import duckdb
  if kind not in ['cid','procedure','catchment']or family not in ['RD','PA','AM']or type(year)!=int or year not in range(2022,2027):raise ValueError('Unsupported fixed provider scope')
  if not isinstance(facility,str)or not re.fullmatch('[0-9]{7}',facility):raise ValueError('Exact7digit sourcefacility required')
  if not isinstance(provider_municipality,str)or provider_municipality not in self.meta['provider_municipality_codes']:raise ValueError('Exact nonDF frozen2024provider municipality required')
  pattern='[0-9]{2}'if kind=='catchment'else'[A-Z0-9]{1,10}'
  if not isinstance(code,str)or(code and not re.fullmatch(pattern,code)):raise ValueError('Exactcode only')
  if kind=='catchment'and code and code not in self.meta['residence_uf_codes']:raise ValueError('Unknown/DFresidence isnotzero')
  if type(limit)!=int or not 1<=limit<=100:raise ValueError('Limit1-100')
  a=self.meta['partitions'][family+str(year)][kind];col={'cid':'cid','procedure':'procedure','catchment':'residence_uf_code'}[kind];spec={'kind':kind,'family':family,'year':year,'facility':facility,'provider_municipality':provider_municipality,'code':code};q=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest();last=''
  if not isinstance(cursor,str)or len(cursor)>2048:raise ValueError('Invalid cursor')
  if cursor:
   try:d=json.loads(base64.urlsafe_b64decode(cursor))
   except Exception:raise ValueError('Invalidcursor')
   if d.get('query')!=q or d.get('sha256')!=a['sha256']or not isinstance(d.get('last'),str):raise ValueError('Cursorbelongs toanother scope/artifact')
   last=d['last']
  if not WORK.acquire(blocking=False):raise ValueError('Datasetbusy;retry')
  try:
   c=duckdb.connect();c.execute("SET memory_limit='128MB'");c.execute('SET threads=1');cur=c.execute('SELECT *FROM read_parquet(?)WHERE facility=? AND provider_municipality=? AND(?=\'\'OR '+col+'=?)AND '+col+'>?ORDER BY '+col+' LIMIT ?',[str(self.root/'candidate'/a['filename']),facility,provider_municipality,code,code,last,limit+1]);rows=[dict(zip([x[0]for x in cur.description],r))for r in cur.fetchall()];c.close()
  finally:WORK.release()
  more=len(rows)>limit;rows=rows[:limit];return {'rows':rows,'has_more':more,'next_cursor':base64.urlsafe_b64encode(json.dumps({'query':q,'sha256':a['sha256'],'last':rows[-1][col]}).encode()).decode()if more else None,'query_spec':spec,'release_id':self.meta['release_id'],'artifact_sha256':a['sha256'],'status':('activated_fixed_release' if self.meta.get('release_ready') and not self.meta.get('private_only') else 'private_candidate_not_activated'),'unit':self.meta['units'][family],'time_basis':'Processingfileyear;2026Jan-Julpartial','provider_identity':'Sourcebillingestablishmentcode+sourceprovidermunicipality,notprovenhistoricalhospital/legalidentity. Currentnamelookupdoesnotprovepastname.','catchment':'Separate provider-to-residence-UF billing-record margin. UF is the two-digit Brazilian state code, not an abbreviation. Not people, referral pathways, geographic markets or patient journeys. No CID/procedure intersections.','missing':'Unknown;omittedcodesarenotzero andcannotdistinguishabsent/suppressed/withheld/unavailable. Noexacttotals.','warnings':self.meta['warnings']}
