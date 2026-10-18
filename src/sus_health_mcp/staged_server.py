"""CNES registry plus separately approved fixed clinical2024 release."""
import os,pathlib,json,hashlib,re,duckdb
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse
from starlette.applications import Starlette
from starlette.routing import Mount
from .period_gates import require_period
from .rate_limit import RateLimit
from .usage import UsageLog
ROOT=pathlib.Path(os.getenv('SUS_STAGED_DATA','data/staged'))
mcp=FastMCP('sus-health-mcp',stateless_http=True,json_response=True,transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True,allowed_hosts=['sus-health-mcp.fly.dev','localhost','127.0.0.1'],allowed_origins=[]))
_conn=None

def metadata():return json.loads((ROOT/'metadata.json').read_text())

def checked():
 global _conn
 if _conn is None:
  m=metadata();p=ROOT/'capacity.parquet'
  if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=m['capacity_sha256']:raise ValueError('Registry artifact integrity failed')
  if m.get('clinical_queries_enabled') is not False:raise ValueError('Invalid staged scope')
  _conn=duckdb.connect();_conn.execute("SET memory_limit='384MB'");_conn.execute('SET threads=1');_conn.read_parquet(str(p)).create_view('capacity')
 return _conn

@mcp.tool()
def dataset_info()->dict:
 """Call first: actual serving scope, clinical2024 limitations and source gaps."""
 m=metadata();out={k:v for k,v in m.items() if k!='capacity_sha256'}
 if os.getenv('SUS_ENABLE_CLINICAL_2024')=='true':
  out.update(deployment_scope='CNES2024plusfixedclinical2024',clinical_queries_enabled=True,clinical_years=[2024],full_clinical_mcp=False)
  from .clinical_candidate import check_artifact
  cm=check_artifact(os.getenv('SUS_CLINICAL_DATA','data/clinical-candidate'))
  out['clinical_warnings']=cm['warnings']
  out['clinical_release_id']=cm['release_id']
  out['SIM_preview_scopes']=cm.get('preview_scopes',{})
  out['clinical_years']=cm['years']
  out['deployment_scope']='CNES2024plusfixedclinical'+','.join(map(str,cm['years']))
 if os.getenv('SUS_ENABLE_KNOWN_CARE')=='true':
  from .known_care_candidate import check_artifact
  km=check_artifact(os.getenv('SUS_KNOWN_CARE_DATA','data/known-care-candidate'));out['known_care_years']=km['years'];out['known_care_warnings']=km['warnings'];out['known_care_enabled']=True
 if os.getenv('SUS_ENABLE_DEEPER')=='true':
  from .deeper_candidate import check_artifact
  dm=check_artifact(os.getenv('SUS_DEEPER_DATA','data/deeper-private'));out['deeper_surfaces']=dm['surfaces'];out['deeper_years']=dm['years'];out['deeper_warnings']=dm['warnings']
 return out

@mcp.tool()
def dataset_coverage(family:str='')->dict:
 """Reviewed registry period coverage and explicit source gaps."""
 m=metadata();return {'deployment_scope':dataset_info()['deployment_scope'],'clinical_years':dataset_info().get('clinical_years',[]),'SIM_preview_scopes':dataset_info().get('SIM_preview_scopes',{}),'clinical_warnings':dataset_info().get('clinical_warnings',[]),'coverage':[r for r in m['coverage'] if not family or r['family']==family],'verified_periods':[r for r in m['publisher_periods'] if not family or r['family']==family],'clinical_status':('fixedclinicalyears'+str(dataset_info()['clinical_years'])+';otherperiodsunavailable' if dataset_info().get('clinical_queries_enabled') else m['clinical_status']),'gaps':m['gaps']}

@mcp.tool()
def facility_capacity(uf:str,year:int,month:int,municipality:str='',family:str='LT',limit:int=30)->dict:
 """Fixed CNES2022-26 partial registered beds, facility types, services, authorizations. Not real-time availability."""
 if uf not in 'AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split():raise ValueError('UF invalid')
 if family not in ('ST','LT','SR','HB') or not 1<=month<=12 or year not in metadata().get('registry_years',[2024]):raise ValueError('Only reviewed fixed CNES periods')
 if municipality and not re.fullmatch('[0-9]{6}',municipality):raise ValueError('Six-digit municipality required')
 if not 1<=limit<=100:raise ValueError('Limit1-100')
 require_period(metadata(),family,year,month,uf)
 c=checked();cur=c.execute("SELECT * FROM capacity WHERE uf=? AND year=? AND month=? AND family=? AND (?='' OR municipality=?) ORDER BY facility,procedure LIMIT ?",[uf,year,month,family,municipality,municipality,limit+1]);rows=[dict(zip([r[0] for r in cur.description],v)) for v in cur.fetchall()]
 return {'rows':rows[:limit],'truncated':len(rows)>limit,'registry_warnings':metadata().get('registry_warnings',[]),'registry_release_id':metadata()['release_id'],'partial_year':year in (int(y) for y in metadata().get('registry_partial_years',{})),'notes':'Registered capacity, not occupancy or appointments. LTprocedure=TP_LEITO:CODLEITO;type3=complementary,notinpatient. ST/SR/HBquantity=registryrows,notbedcounts. sus_flagregistrationsemanticsdifferbyfamily. No clinical activity or individual records.'}

# Explicit opt-in for a separately approved, hash-frozen clinical candidate.
if os.getenv('SUS_ENABLE_CLINICAL_2024') == 'true':
 @mcp.tool()
 def geographic_signals(uf:str,year:int,family:str='RD',cid_prefix:str='',municipality:str='',limit:int=30)->dict:
  """Fixed2024municipalCIDrecordintervals. DF and targeted groups withheld; not people."""
  from .clinical_candidate import query
  return query(os.getenv('SUS_CLINICAL_DATA','data/clinical-candidate'),uf,year,family,cid_prefix,municipality,limit)

# Separate, explicit activation gate. Private candidates are not packaged by default.
if os.getenv('SUS_ENABLE_KNOWN_CARE') == 'true':
 @mcp.tool()
 def known_care_activity(uf:str,year:int,view:str='residence',municipality:str='',limit:int=30)->dict:
  """Fixed E851 billing records and residence-to-billingmunicipality flows; not people/hospitals."""
  from .known_care_candidate import query
  return query(os.getenv('SUS_KNOWN_CARE_DATA','data/known-care-candidate'),uf,year,view,municipality,limit)

if os.getenv('SUS_ENABLE_DEEPER')=='true':
 @mcp.tool()
 def rare_disease_billing(uf:str,year:int,surface:str,municipality:str='',limit:int=30)->dict:
  """Three fixed annual residence billing views: related E85, tafamidis61mg, nonspecific workup. Not patients or diagnosis."""
  from .deeper_candidate import query
  return query(os.getenv('SUS_DEEPER_DATA','data/deeper-private'),uf,year,surface,municipality,limit)

@mcp.custom_route('/healthz',methods=['GET'])
async def health(request):
 try:
  checked()
  enabled=os.getenv('SUS_ENABLE_CLINICAL_2024')=='true'
  if enabled:
   from .clinical_candidate import check_artifact
   check_artifact(os.getenv('SUS_CLINICAL_DATA','data/clinical-candidate'))
  if os.getenv('SUS_ENABLE_KNOWN_CARE')=='true':
   from .known_care_candidate import check_artifact as check_known_care
   check_known_care(os.getenv('SUS_KNOWN_CARE_DATA','data/known-care-candidate'))
  if os.getenv('SUS_ENABLE_DEEPER')=='true':
   from .deeper_candidate import check_artifact as check_deeper
   check_deeper(os.getenv('SUS_DEEPER_DATA','data/deeper-private'))
  return JSONResponse({'ok':True,'stage':'registry_clinical_fixed_years_knowncare' if enabled else 'registry_only','full_clinical_mcp':False,'clinical2024_enabled':enabled,'clinical_years':check_artifact(os.getenv('SUS_CLINICAL_DATA','data/clinical-candidate'))['years'] if enabled else []})
 except Exception:return JSONResponse({'ok':False},status_code=503)

# Phase1 additions share one work slot with the six existing tools.
from .foundation.candidate_api import FoundationAPI
from .foundation.mcp_foundation_candidate import register as register_foundation
import functools
_foundation_root=os.getenv('SUS_FOUNDATION_DATA','/app/data/foundation')
_data_root=os.getenv('SUS_DATA_ROOT','/app/data');_foundation_api=FoundationAPI(_foundation_root,_data_root,str(pathlib.Path(_foundation_root)/'serving-coverage-scientific.json'))
for _tool in mcp._tool_manager.list_tools():
 _original=_tool.fn
 def _guarded(original):
  @functools.wraps(original)
  def call(*args,**kwargs):
   with _foundation_api.work_slot():return original(*args,**kwargs)
  return call
 _tool.fn=_guarded(_original)
register_foundation(mcp,_foundation_api)

# Fixed phase 2 tables share the existing process-wide dataset work slot.
from .state_activity import StateCandidate
_state_api=StateCandidate()
@mcp.tool()
def state_activity_page(kind:str,uf:str,year:int,family:str,code:str='',limit:int=100,cursor:str='')->dict:
 """Separate fixed annual residence-UF CID or procedure record intervals. Not patients, prevalence, approved quantities or doses. DF/unknown excluded, not zero;2026Jan-Julpartial. No CID/procedure joint filter."""
 with _foundation_api.work_slot():return _state_api.page(kind,uf,year,family,code,limit,cursor)
@mcp.tool()
def state_activity_methods()->dict:
 """Read first: source gaps, CID placeholders, record units, dated references and disclosure-test limits for fixed state activity."""
 return _state_api.methods()

from .annual_series import Series
_series_api=Series(state_api=_state_api)
@mcp.tool()
def annual_activity_series(kind:str,uf:str,family:str,code:str,years:list[int]=[2022,2023,2024,2025])->dict:
 """Exact-code annual source-record intervals with population context. Not patient rates or prevalence.2026partial has no annual rate. No sums, groups or automatic trend labels."""
 with _foundation_api.work_slot():return _series_api.series(kind,uf,family,code,years)
@mcp.tool()
def annual_series_methods()->dict:
 """Read first: population vintage, coverage gaps, rate rounding, record units and longitudinal limits."""
 return _series_api.methods()

# Provider additions are gated; no artifact or surface activates by import alone.
if os.getenv('SUS_ENABLE_PROVIDER')=='true':
 from .provider_activity import ProviderCandidate
 _provider_api=ProviderCandidate()
 @mcp.tool()
 def provider_activity_page(kind:str,family:str,year:int,facility:str,provider_municipality:str,code:str='',limit:int=100,cursor:str='')->dict:
  """Separate fixed annual provider CID, procedure or residence-UF record intervals. Exact source establishment and provider municipality required. No joint filters, totals, people or historical hospital identity. DF/unknown omitted, not zero."""
  with _foundation_api.work_slot():return _provider_api.page(kind,family,year,facility,provider_municipality,code,limit,cursor)
 @mcp.tool()
 def provider_activity_methods()->dict:
  """Read first: fixed provider scope, source coverage, record units, identity/catchment limits and disclosure-test caveats."""
  return _provider_api.methods()

# Private opt-in preparation; not configured on the live service.
if os.getenv('SUS_ENABLE_CONTEXT')=='true':
 from .activity_context import Tariffs,Context
 _tariff_api=Tariffs(os.getenv('SUS_TARIFF_DATA','data/tariffs'))
 _context_api=Context(_tariff_api,_provider_api,ROOT/'capacity.parquet',metadata())
 @mcp.tool()
 def reimbursement_reference(procedure:str,vintage:str)->dict:
  """Dated SIGTAP SH/SA/SP national reference components. Explicit YYYYMM. Not actual payments, cost, private prices or billing eligibility."""
  return _tariff_api.lookup(procedure,vintage)
 @mcp.tool()
 def provider_activity_context(family:str,year:int,facility:str,provider_municipality:str,procedure:str,snapshot_month:int,registry_family:str,limit:int=100,cursor:str='')->dict:
  """Unchanged annual provider-procedure record interval beside one explicitly chosen CNES monthly registry family and SIGTAP vintage. No utilization, shortage, ranking, payment estimate or clinical cross-filter."""
  with _foundation_api.work_slot():return _context_api.page(family,year,facility,provider_municipality,procedure,snapshot_month,registry_family,limit,cursor)

# Phase6 record templates: private opt-in; not configured on the live service.
if os.getenv('SUS_ENABLE_RECORD_TEMPLATES')=='true':
 from .record_templates import RecordTemplates
 _templates_api=RecordTemplates()
 @mcp.tool()
 def record_template_page(template:str,uf:str,year:int,cid:str='',limit:int=100,cursor:str='')->dict:
  """Private candidate: fixed RD record-template intervals by exact principal CID, residence UF and processing year. Not people, admissions, prevalence or outcomes."""
  with _foundation_api.work_slot():return _templates_api.page(template,uf,year,cid,limit,cursor)
 @mcp.tool()
 def record_template_comparison(template:str,uf:str,year:int,cid_a:str,cid_b:str)->dict:
  """Private candidate: exactly two exact CIDs side by side within one frozen template. Descriptive record intervals only."""
  with _foundation_api.work_slot():return _templates_api.comparison(template,uf,year,cid_a,cid_b)
 @mcp.tool()
 def record_template_methods()->dict:
  """Read first: scope, encodings, withholds, dictionary coverage and limits for the private record templates."""
  return _templates_api.methods()

# Phase7a SIM role margins: private opt-in; not configured on the live service.
if os.getenv('SUS_ENABLE_SIM_TEMPLATES')=='true':
 from .sim_templates import SimTemplates
 _sim_api=SimTemplates()
 @mcp.tool()
 def sim_template_page(template:str,uf:str,year:int,cid:str='',limit:int=100,cursor:str='')->dict:
  """Private candidate: SIM death-certificate role margins by exact CID, residence UF and death year. Certificates, not people; 2025/2026 preliminary; no rates or trends."""
  with _foundation_api.work_slot():return _sim_api.page(template,uf,year,cid,limit,cursor)
 @mcp.tool()
 def sim_template_methods()->dict:
  """Read first: scope, packed-field encodings, withholds, dictionary coverage and limits for the private SIM role margins."""
  return _sim_api.methods()

# Phase7c oncology reference: opt-in published-aggregate views; not configured before approval.
if os.getenv('SUS_ENABLE_ONCO_REF')=='true':
 from .onco_reference import OncoReference
 _onco_api=OncoReference()
 @mcp.tool()
 def oncology_reference_page(view:str,limit:int=100,cursor:str='')->dict:
  """DATASUS PAINEL-Oncologia published national aggregates, six fixed views by diagnosis year 2013-2026. Exact counts as published; 2026 partial; not rates or trends."""
  with _foundation_api.work_slot():return _onco_api.page(view,limit,cursor)
 @mcp.tool()
 def oncology_reference_methods()->dict:
  """Read first: sources, panel update date, view definitions and citation for the oncology reference."""
  return _onco_api.methods()

for t in mcp._tool_manager.list_tools():
 t.fn_metadata.arg_model.model_config={**t.fn_metadata.arg_model.model_config,'extra':'forbid','strict':True};t.fn_metadata.arg_model.model_rebuild(force=True);t.parameters=t.fn_metadata.arg_model.model_json_schema()

def http_app():
 inner=mcp.streamable_http_app();return Starlette(routes=[Mount('/',app=RateLimit(UsageLog(inner,[t.name for t in mcp._tool_manager.list_tools()])))],lifespan=inner.router.lifespan_context)

def main():
 import uvicorn
 uvicorn.run(http_app(),host='0.0.0.0',port=8080,access_log=False)
if __name__=='__main__':main()
