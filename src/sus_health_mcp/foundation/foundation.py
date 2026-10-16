"""Reference layer: reference lookup and released-cell pagination.
No network writes or new aggregates.
"""
import base64,hashlib,json,pathlib,sqlite3,unicodedata,re
KINDS={'cid','procedure','service','service_class','authorization','bed_detail','facility','municipality','facility_type','cnes_bed_type','cnes_bed_specialty'}
def norm(x):return ''.join(c for c in unicodedata.normalize('NFKD',x.casefold()) if not unicodedata.combining(c))
def filehash(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def fingerprint(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def cursor_encode(release,filters,last):return base64.urlsafe_b64encode(json.dumps({'release':release,'query':fingerprint(filters),'last':last},separators=(',',':')).encode()).decode()
def cursor_decode(token,release,filters):
 try:d=json.loads(base64.urlsafe_b64decode(token.encode()))
 except Exception:raise ValueError('Invalid cursor')
 if d.get('release')!=release or d.get('query')!=fingerprint(filters):raise ValueError('Cursor belongs to another release or query')
 if not isinstance(d.get('last'),list):raise ValueError('Invalid cursor key')
 return d['last']
def limit_check(limit):
 if type(limit)!=int or not 1<=limit<=100:raise ValueError('Limit1-100')
class References:
 def __init__(self,root):
  self.root=pathlib.Path(root);self.meta=json.loads((self.root/'reference-metadata.json').read_text());self.db=self.root/self.meta.get('filename','reference.sqlite')
  if self.db.is_symlink() or filehash(self.db)!=self.meta['sha256']:raise ValueError('Reference integrity mismatch')
 def lookup(self,kind,query='',vintage='',municipality='',limit=30,cursor=''):
  limit_check(limit)
  if kind not in KINDS:raise ValueError('Unknown reference kind')
  if len(query)>160:raise ValueError('Query too long')
  if municipality and (kind!='facility' or not re.fullmatch('[0-9]{6}',municipality)):raise ValueError('Municipality filter only for facility names')
  if not vintage:vintage='retrieved20261016' if kind in ['facility','municipality','facility_type','cnes_bed_type','cnes_bed_specialty'] else '202608'
  with sqlite3.connect('file:'+str(self.db)+'?mode=ro',uri=True) as check:
   if not check.execute('SELECT 1 FROM reference WHERE kind=? AND vintage=? LIMIT 1',[kind,vintage]).fetchone():raise ValueError('Reference kind/vintage unavailable;not evidence of code absence')
  filters={'kind':kind,'query':norm(query),'vintage':vintage,'municipality':municipality};last=cursor_decode(cursor,self.meta['sha256'],filters) if cursor else ['']
  if len(last)!=1 or not isinstance(last[0],str):raise ValueError('Invalid cursor key')
  where='kind=? AND vintage=? AND (instr(normalized,?)>0 OR instr(code,?)>0) AND code>?';params=[kind,vintage,norm(query),query.upper().replace('.',''),last[0]]
  if kind in ['service','service_class'] and query:
   target="substr(link.to_code,1,3)=reference.code" if kind=='service' else "link.to_code=reference.code"
   where='kind=? AND vintage=? AND (instr(normalized,?)>0 OR instr(code,?)>0 OR EXISTS(SELECT 1 FROM relation link JOIN reference proc ON proc.kind=\'procedure\' AND proc.code=link.from_code AND proc.vintage=link.vintage WHERE link.vintage=reference.vintage AND '+target+' AND instr(proc.normalized,?)>0)) AND code>?'
   params=[kind,vintage,norm(query),query.upper().replace('.',''),norm(query),last[0]]
  if municipality:where+=' AND json_extract(details,\'$.municipality\')=?';params.append(municipality)
  c=sqlite3.connect('file:'+str(self.db)+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;rows=[dict(r) for r in c.execute('SELECT code,name,vintage,source,details FROM reference WHERE '+where+' ORDER BY code LIMIT ?',params+[limit+1])];c.close();more=len(rows)>limit;rows=rows[:limit]
  for r in rows:
   r['details']=json.loads(r['details'])
   r['match_interpretation']='Direct label/code match or dated SIGTAP procedure-to-service relationship;not proof that a facility performs the procedure.'
  return {'rows':rows,'has_more':more,'next_cursor':cursor_encode(self.meta['sha256'],filters,[rows[-1]['code']]) if more else None,'reference_sha256':self.meta['sha256'],'reference_vintage':vintage,'caveats':self.meta['limitations'],'meaning':'Lookup labels and dated definitions,not clinical eligibility,clinical evidence or provider availability.'}

def resolve_code(root,kind,code,vintage='202608'):
 """Resolve exact code only. An auxiliary label never proves monthly validity."""
 r=References(root)
 if kind not in KINDS:raise ValueError('Unknown reference kind')
 clean=code.upper().replace('.','') if kind=='cid' else code
 with sqlite3.connect('file:'+str(r.db)+'?mode=ro',uri=True) as c:
  c.row_factory=sqlite3.Row
  rows=[dict(x) for x in c.execute('SELECT code,name,vintage,source,details FROM reference WHERE kind=? AND code=? AND vintage=?',[kind,clean,vintage])]
  status='dated_reference_match'
  if not rows and kind=='cid':
   rows=[dict(x) for x in c.execute("SELECT code,name,vintage,source,details FROM reference WHERE kind='cid' AND code=? AND vintage='aux_retrieved20261016'",[clean])];status='auxiliary_label_only_not_dated_validity'
 for row in rows:row['details']=json.loads(row['details'])
 return {'source_code':code,'lookup_code':clean,'status':status if rows else 'unmapped_source_code_preserved','rows':rows,'requested_vintage':vintage,'reference_sha256':r.meta['sha256'],'warning':'Never drop,correct or recode an input record because its dictionary label is missing. Placeholders are not clinical diagnoses.'}

class ReleasedCells:
 """Pages only the frozen already-served lattice. Not a general SQL interface."""
 def __init__(self,path,sha256,release_id,kind,scope_metadata=None):
  self.path=pathlib.Path(path);self.sha=sha256;self.release=release_id;self.kind=kind;self.scope=scope_metadata;self._checked_queries=set()
  if kind not in ['clinical','capacity']:raise ValueError('Unknown lattice')
  if self.path.is_symlink() or filehash(self.path)!=sha256:raise ValueError('Released artifact hash mismatch')
 def page(self,uf,year,family,month=0,municipality='',cid_prefix='',limit=100,cursor='',registry_code_prefix=''):
  import duckdb
  limit_check(limit)
  if self.scope is None:raise ValueError('Reviewed source-scope metadata is required')
  if self.scope.get('release_id')!=self.release or self.scope.get('clinical_sha256' if self.kind=='clinical' else 'capacity_sha256')!=self.sha:raise ValueError('Scope/artifact identity mismatch')
  if not re.fullmatch('[0-9]{1,4}(:[0-9]{0,3})?|',registry_code_prefix):raise ValueError('Invalid registry code prefix')
  if registry_code_prefix and self.kind!='capacity':raise ValueError('Registry code filter only for public registry cells')
  if self.kind=='clinical':
   if family not in self.scope.get('approved_scopes',{}).get(str(year),[]):raise ValueError('Clinical year/family unavailable')
  else:
   from sus_health_mcp.period_gates import require_period
   require_period(self.scope,family,year,month,uf)
  if uf not in 'AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split() or type(year)!=int:raise ValueError('UF/year invalid')
  if municipality and not re.fullmatch('[0-9]{6}',municipality):raise ValueError('Invalid municipality')
  if not re.fullmatch('[A-Z][0-9]{0,3}|',cid_prefix):raise ValueError('CID prefix invalid')
  if self.kind=='clinical':
   if uf=='DF' or municipality.startswith('53') or family not in ['RD','PA','AM','DO'] or month:raise ValueError('Unsupported clinical scope')
   keys=['municipality','cid'];cols='family,uf,year,municipality,cid,records_lower,records_upper'
  else:
   if family not in ['ST','LT','SR','HB'] or type(month)!=int or not 1<=month<=12 or cid_prefix:raise ValueError('Unsupported capacity scope')
   keys=['facility','procedure','municipality'];cols='family,uf,year,month,municipality,facility,procedure,quantity,sus_beds,sus_flag'
  spec={'kind':self.kind,'uf':uf,'year':year,'family':family,'month':month,'municipality':municipality,'cid_prefix':cid_prefix,'registry_code_prefix':registry_code_prefix}
  last=cursor_decode(cursor,self.sha,spec) if cursor else ['']*len(keys)
  if len(last)!=len(keys) or any(not isinstance(x,str) for x in last):raise ValueError('Invalid cursor key')
  where='uf=? AND year=? AND family=?';p=[str(self.path),uf,year,family]
  if self.kind=='capacity':where+=' AND month=?';p.append(month)
  if municipality:where+=' AND municipality=?';p.append(municipality)
  if cid_prefix:where+=' AND starts_with(cid,?)';p.append(cid_prefix)
  if registry_code_prefix:where+=' AND starts_with(procedure,?)';p.append(registry_code_prefix)
  validation_where=where;validation_params=list(p)
  where+=' AND ('+','.join(keys)+')>('+','.join('?' for _ in keys)+')';p+=last
  c=duckdb.connect();c.execute("SET memory_limit='192MB'");c.execute('SET threads=1');
  if fingerprint(spec) not in self._checked_queries and c.execute('SELECT count(*) FROM (SELECT '+','.join(keys)+',count(*) n FROM read_parquet(?) WHERE '+validation_where+' GROUP BY ALL HAVING n>1)',validation_params).fetchone()[0]:
   c.close();raise ValueError('Nonunique frozen keys;requires reviewed adapter')
  self._checked_queries.add(fingerprint(spec))
  cur=c.execute('SELECT '+cols+' FROM read_parquet(?) WHERE '+where+' ORDER BY '+','.join(keys)+' LIMIT ?',p+[limit+1]);rows=[dict(zip([d[0] for d in cur.description],r)) for r in cur.fetchall()];c.close();more=len(rows)>limit;rows=rows[:limit]
  return {'rows':rows,'has_more':more,'next_cursor':cursor_encode(self.sha,spec,[rows[-1][k] for k in keys]) if more else None,'release_id':self.release,'artifact_sha256':self.sha,'query_spec':spec,'grain':'existing_released_cells_only','missing_status':'not_distinguishable:suppressed,targeted_withheld,DF_excluded,invalid_geography,source_absent_or_unavailable','no_new_totals':True,'bulk_access_warning':'Pagination makes bulk collection of existing released cells easier. No anonymity or sub20 secrecy guarantee. Public source files and other releases can enable linkage or inference;targeted withholding does not eliminate residual risk.','warnings':self.scope.get('warnings',self.scope.get('registry_warnings',[]))+self.scope.get('preview_scopes',{}).get(str(year),{}).get('warnings',[]) if family=='DO' else self.scope.get('warnings',self.scope.get('registry_warnings',[])),'preview_vintage':self.scope.get('preview_scopes',{}).get(str(year)) if family=='DO' else None,'status':'phase1_active_existing_frozen_cells'}

 def iter_rows(self,**query):
  """One sorted streaming query for exports;never repeatedly rescan every page."""
  import duckdb
  self.page(**query,limit=1)
  where='uf=? AND year=? AND family=?';params=[str(self.path),query['uf'],query['year'],query['family']]
  if self.kind=='capacity':where+=' AND month=?';params.append(query['month'])
  if query.get('municipality'):where+=' AND municipality=?';params.append(query['municipality'])
  if query.get('cid_prefix'):where+=' AND starts_with(cid,?)';params.append(query['cid_prefix'])
  if query.get('registry_code_prefix'):where+=' AND starts_with(procedure,?)';params.append(query['registry_code_prefix'])
  keys=['municipality','cid'] if self.kind=='clinical' else ['facility','procedure','municipality']
  cols='family,uf,year,municipality,cid,records_lower,records_upper' if self.kind=='clinical' else 'family,uf,year,month,municipality,facility,procedure,quantity,sus_beds,sus_flag'
  c=duckdb.connect();c.execute("SET memory_limit='192MB'");c.execute('SET threads=1');c.execute('SET preserve_insertion_order=false');last=None
  try:
   cur=c.execute('SELECT '+cols+' FROM read_parquet(?) WHERE '+where+' ORDER BY '+','.join(keys),params);names=[x[0] for x in cur.description]
   while True:
    batch=cur.fetchmany(1000)
    if not batch:break
    for values in batch:
     row=dict(zip(names,values));key=tuple(row[k] for k in keys)
     if key==last:raise ValueError('Nonunique frozen keys;export stopped')
     last=key;yield row
  finally:c.close()
