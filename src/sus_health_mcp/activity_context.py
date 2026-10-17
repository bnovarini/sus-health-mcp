"""Private phase5 public-reference lookup and deterministic released-cell context."""
import pathlib,json,sqlite3,hashlib,re,base64
def filehash(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
class Tariffs:
 def __init__(self,root):
  self.root=pathlib.Path(root);self.meta=json.loads((self.root/'tariff-metadata.json').read_text());self.db=self.root/self.meta['filename']
  if self.db.is_symlink()or filehash(self.db)!=self.meta['sha256']:raise ValueError('Tariff artifact integrity failed')
 def lookup(self,procedure,vintage):
  if not isinstance(procedure,str)or not re.fullmatch('[0-9]{10}',procedure):raise ValueError('Exact ten-digit procedure required')
  if not isinstance(vintage,str)or vintage not in self.meta['vintages']:raise ValueError('Explicit supported YYYYMM vintage required')
  with sqlite3.connect('file:'+str(self.db)+'?mode=ro',uri=True)as c:
   c.row_factory=sqlite3.Row;r=c.execute('SELECT *FROM procedure WHERE vintage=? AND code=?',[vintage,procedure]).fetchone()
   if not r:return {'status':'unmapped_source_code_preserved','procedure':procedure,'vintage':vintage,'rows':[],'missing':'Unknown, not zero/no payment','warnings':self.meta['limits']}
   r=dict(r);links=[dict(x)for x in c.execute('SELECT r.kind,r.target,l.name FROM relation r LEFT JOIN label l ON l.vintage=r.vintage AND l.kind=r.kind AND l.code=r.target WHERE r.vintage=? AND r.code=? ORDER BY r.kind,r.target',[vintage,procedure])];fin=c.execute("SELECT name FROM label WHERE vintage=? AND kind='financing' AND code=?",[vintage,r['financing']]).fetchone()
  return {'status':('activated_fixed_release'if self.meta.get('release_ready')else'private_candidate_not_activated'),'procedure':procedure,'name':r['name'],'vintage':vintage,'currency':'BRL','components':{k:{'source_integer':r[k+'_raw'],'centavos':r[k+'_cents'],'BRL':str(r[k+'_cents']//100)+'.'+str(r[k+'_cents']%100).zfill(2)}for k in ['sh','sa','sp']},'financing_code':r['financing'],'financing_name':fin[0]if fin else None,'dated_relations':links,'source':r['source'],'artifact_sha256':self.meta['sha256'],'warnings':self.meta['limits']}
class Context:
 def __init__(self,tariffs,provider,capacity_path,capacity_meta):
  self.tariffs=tariffs;self.provider=provider;self.capacity_path=pathlib.Path(capacity_path);self.meta=capacity_meta
  if self.capacity_path.is_symlink()or filehash(self.capacity_path)!=self.meta['capacity_sha256']:raise ValueError('Registry artifact integrity failed')
 def page(self,family,year,facility,provider_municipality,procedure,snapshot_month,registry_family,limit=100,cursor=''):
  import duckdb
  from sus_health_mcp.period_gates import require_period
  from sus_health_mcp.foundation.foundation import cursor_encode,cursor_decode
  if type(snapshot_month)!=int or not 1<=snapshot_month<=12:raise ValueError('Explicit snapshot month required')
  if registry_family not in ['ST','LT','SR','HB']:raise ValueError('One registry family required')
  if type(limit)!=int or not 1<=limit<=100:raise ValueError('Limit1-100')
  # Reuse the exact released clinical query without additional filters or raw counts.
  activity=self.provider.page('procedure',family,year,facility,provider_municipality,procedure,1,'')
  vintage=str(year)+str(snapshot_month).zfill(2);reference=self.tariffs.lookup(procedure,vintage)
  uf={'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA','22':'PI','23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA','31':'MG','32':'ES','33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS','51':'MT','52':'GO'}[provider_municipality[:2]]
  require_period(self.meta,registry_family,year,snapshot_month,uf)
  if not isinstance(cursor,str)or len(cursor)>2048:raise ValueError('Invalid registry cursor')
  spec={'family':family,'year':year,'facility':facility,'provider_municipality':provider_municipality,'procedure':procedure,'snapshot_month':snapshot_month,'registry_family':registry_family};sha=self.meta['capacity_sha256'];last=cursor_decode(cursor,sha,spec)if cursor else ['']
  if not isinstance(cursor,str)or len(cursor)>2048 or len(last)!=1 or not isinstance(last[0],str):raise ValueError('Invalid registry cursor')
  c=duckdb.connect();c.execute("SET memory_limit='128MB'");c.execute('SET threads=1')
  try:
   cur=c.execute('SELECT *FROM read_parquet(?)WHERE family=? AND uf=? AND year=? AND month=? AND facility=? AND municipality=? AND procedure>? ORDER BY procedure LIMIT ?',[str(self.capacity_path),registry_family,uf,year,snapshot_month,facility,provider_municipality,last[0],limit+1]);rows=[dict(zip([x[0]for x in cur.description],r))for r in cur.fetchall()]
  finally:c.close()
  keys=[r['procedure']for r in rows]
  if len(keys)!=len(set(keys)):raise ValueError('Nonunique registry keys; review required')
  more=len(rows)>limit;rows=rows[:limit]
  return {'status':('activated_fixed_release'if self.tariffs.meta.get('release_ready')else'private_candidate_not_activated'),'activity':activity,'reference':reference,'registry':{'rows':rows,'has_more':more,'next_cursor':cursor_encode(sha,spec,[rows[-1]['procedure']])if more else None,'artifact_sha256':sha,'release_id':self.meta['release_id'],'scope':spec,'no_rows_meaning':'No visible row for this exact snapshot/family/identity; not zero capacity or non-provision.'},'comparison':'Annual processing-file record intervals beside one explicitly requested CNES monthly snapshot. Not aligned service-date production, utilization or treatment capacity. No arithmetic ratio, tariff multiplication, mismatch score or ranking.','warnings':['All clinical rows/intervals are returned unchanged from the phase4 fixed release; no clinical filter is conditioned on registry or tariffs.','LT quantity/sus_beds are registered beds, not bed-days, occupancy or disease-specific available beds. LT code namespace is TP_LEITO:CODLEITO, not SIGTAP bed type.','ST/SR/HB quantities are registry rows, not beds, sessions, staff hours or throughput. SUS flags differ by source family.','Dated service/class relations are administrative context only; no claim that registry and billing should match or that absence means shortage.','Exact establishment/municipality must match; no fuzzy name joins or fallback to another month/location.','2026 activity Jan-Jul only. Tariff vintage and CNES snapshot may run through August but are never used to annualize activity.']}
