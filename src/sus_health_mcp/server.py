"""Read-only tools over fixed, privacy-reduced aggregate releases."""
import os,pathlib,json,re,threading
import duckdb
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse
mcp=FastMCP('sus-health-mcp',stateless_http=True,json_response=True,transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True,allowed_hosts=[os.getenv('SUS_ALLOWED_HOSTS','sus-health-mcp.fly.dev')],allowed_origins=['*']))
NOTE='Administrative activity, not people or prevalence. SIH/SIA are SUS-funded care. CNES includes private and public facilities. SIM covers national deaths. Municipal multi-signal patterns do not imply the same individuals, causation or misdiagnosis. Missing data is not zero. Counts are fixed intervals and small cells are omitted. No individual linkage or clinical advice.'
ROOT=pathlib.Path(os.getenv('SUS_DATA','data/release'))
_local=threading.local()
def release_metadata():
 p=ROOT/'metadata.json'
 if not p.exists():return {'status':'development_only','release_ready':False}
 return json.loads(p.read_text())

def require_ready():
 from .readiness import validate_artifacts
 validate_artifacts(release_metadata(),ROOT)

def con():
 require_ready()
 c=getattr(_local,'c',None)
 if c is None:
  c=duckdb.connect();c.execute("SET memory_limit='768MB'");c.execute("SET threads=2")
  names=['capacity']+(['signals'] if release_metadata().get('legacy_fine_lattice_approved') is True else [])
  for n in names:c.read_parquet(str(ROOT/(n+'.parquet'))).create_view(n)
  _local.c=c
 return c

def run(sql,args):
 require_ready()
 q=con().execute(sql,args);return [dict(zip([x[0] for x in q.description],r)) for r in q.fetchall()]

def checked_uf(uf):
 if uf not in set('AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split()):raise ValueError('UF must be two uppercase letters')
 return uf

def wrap(rows,**meta):return {'rows':rows,'notes':NOTE,'sources':['https://datasus.saude.gov.br/transferencia-de-arquivos/','https://dadosabertos.saude.gov.br/dataset/sim'],**meta}

@mcp.tool()
def dataset_info()->dict:
 """Call first: coverage, vintage, units, privacy release and audit status."""
 p=ROOT/'metadata.json'
 return {**release_metadata(),'notes':NOTE,'privacy':{'threshold':20,'count_interval_width':10,'no_demographics':True,'fixed_annual_cid_tables_only':True,'no_arbitrary_sql':True}}

@mcp.tool()
def geographic_signals(uf:str,year:int,family:str='RD',cid_prefix:str='',limit:int=30)->dict:
 """Fixed annual municipal diagnosis activity intervals, not patients. Small cells omitted."""
 require_ready()
 if release_metadata().get('legacy_fine_lattice_approved') is not True:raise ValueError('Fine CID lattice is not release-approved; use reviewed fixed proxies')
 if family not in ['RD','PA','AM','DO']:raise ValueError('family must be RD, PA, AM or DO')
 if not re.fullmatch('[A-Z][0-9]{0,3}|',cid_prefix):raise ValueError('CID prefix format invalid')
 rows=run('SELECT * FROM signals WHERE uf=? AND year=? AND family=? AND starts_with(cid,?) ORDER BY records_lower DESC LIMIT ?',[checked_uf(uf),year,family,cid_prefix,max(1,min(limit,100))])
 return wrap(rows,truncated=len(rows)>=max(1,min(limit,100)),unit='source-record activity intervals; not unique patients',geography='residence municipality',period='annual',missing_small_cells='suppressed, not zero')

@mcp.tool()
def facility_capacity(uf:str,year:int,month:int,municipality:str='',limit:int=30,family:str='LT')->dict:
 """Registered capacity by facility; inpatient/complementary bed types remain separate."""
 if not 1<=month<=12:raise ValueError('month must be 1-12')
 if municipality and not re.fullmatch('[0-9]{6}',municipality):raise ValueError('six digit municipality code required')
 require_ready()
 if family not in ('ST','LT','SR','HB'):raise ValueError('Invalid capacity family')
 from .period_gates import require_period
 require_period(release_metadata(),family,year,month,checked_uf(uf))
 rows=run('SELECT * FROM capacity WHERE family=? AND uf=? AND year=? AND month=? AND (?=\'\' OR municipality=?) ORDER BY facility,family LIMIT ?',[family,checked_uf(uf),year,month,municipality,municipality,max(1,min(limit,100))])
 return wrap(rows,truncated=len(rows)>=max(1,min(limit,100)),geography='provider municipality',bed_note='LT procedure is TP_LEITO:CODLEITO; type 3 is complementary, excluded from inpatient totals')

@mcp.tool()
def dataset_coverage(family:str='',year:int=0)->dict:
 """Inventory and publisher gates, never treat unpublished months as zero."""
 if family and family not in ('RD','PA','AM','DO','ST','LT','SR','HB'):raise ValueError('Invalid family')
 meta=release_metadata()
 periods=[r for r in meta.get('coverage',[]) if (not family or r['family']==family) and (not year or r['year']==year)]
 return {'release_ready':meta.get('release_ready',False),'periods':periods,'missing':'Absent periods are unavailable, not zero','period_semantics':'Processing-file periods;2026partial and2025preliminarymortality are not stable matched annual comparisons'}

@mcp.tool()
def fixed_proxy_activity(proxy:str,year:int,uf:str,municipality:str='',limit:int=30)->dict:
 """Reviewed fixed ecological proxy cells. No flexible CID/procedure intersections."""
 require_ready()
 meta=release_metadata()
 if proxy not in meta.get('approved_proxies',[]):raise ValueError('Proxy not release-approved')
 if year not in meta.get('proxy_years',[]):raise ValueError('Period not approved for this proxy release')
 if municipality and not re.fullmatch('[0-9]{6}',municipality):raise ValueError('Six-digit municipality required')
 checked_uf(uf)
 artifact=ROOT/'fixed-proxies.json'
 if not artifact.exists():raise ValueError('Fixed proxy artifact unavailable')
 from .fixed_views import activity
 out=activity(json.loads(artifact.read_text())['rows'],proxy,[year],municipality,uf)
 cap=max(1,min(limit,100));out['truncated']=len(out['rows'])>cap;out['rows']=out['rows'][:cap]
 return wrap(out.pop('rows'),**out)

@mcp.tool()
def ecological_hits(context:str,year:int,uf:str,limit:int=30)->dict:
 """Pre-reviewed fixed multi-signal ecological hits, not patient case finding."""
 require_ready();meta=release_metadata();checked_uf(uf)
 if context not in meta.get('approved_hit_contexts',[]):raise ValueError('Context not release-approved')
 if year not in meta.get('proxy_years',[]):raise ValueError('Period not approved for ecological comparison')
 artifact=ROOT/'ecological-hits.json'
 if not artifact.exists():raise ValueError('Reviewed hit artifact unavailable')
 data=json.loads(artifact.read_text())
 key=f'{context}:{year}:{uf}'
 if key not in data.get('reviewed_scopes',[]):raise ValueError('Requested hit scope not jointly reviewed')
 from .published_hits import sanitize
 rows=[sanitize(r) for r in data['rows'] if r['context']==context and r['year']==year and r['uf']==uf]
 from .hit_status import describe_hits
 cap=max(1,min(limit,100));out=describe_hits(rows[:cap],release_cleared=True,evidence_complete=True)
 out['truncated']=len(rows)>cap
 out['comparison_scope']=meta.get('comparison_scope','Reviewed fixed scope; not national prevalence')
 return out

@mcp.tool()
def protocol_billing_association(disease:str,competence:str,procedure:str)->dict:
 """Dated protocol/billing association only; never diagnosis or patient eligibility."""
 require_ready();meta=release_metadata()
 if disease not in meta.get('approved_protocol_contexts',[]):raise ValueError('Protocol context not reviewed')
 path=ROOT/'protocol-associations.json'
 if not path.exists():raise ValueError('Reviewed protocol catalog unavailable')
 from .temporal import billing_association,dated_protocol_association
 data=json.loads(path.read_text())
 result=billing_association(data['monthly_billing'],disease,competence,procedure)
 result['protocol_context']=dated_protocol_association(data.get('protocol_periods',[]),disease,competence)
 return result

@mcp.custom_route('/healthz',methods=['GET'])
async def health(request):
 p=ROOT/'metadata.json'
 ready=False
 if p.exists():
  try:
   meta=json.loads(p.read_text());from .readiness import validate_artifacts
   ready=validate_artifacts(meta,ROOT)
  except (ValueError,OSError):pass
 return JSONResponse({'ok':ready,'release_ready':ready},status_code=200 if ready else 503)

def http_app():
 from .usage import UsageLog
 from .rate_limit import RateLimit
 return RateLimit(UsageLog(mcp.streamable_http_app(), ['dataset_info','dataset_coverage','fixed_proxy_activity','ecological_hits','protocol_billing_association','geographic_signals','facility_capacity']))

# FastMCP's generated Pydantic argument models default to ignoring extra fields.
# Forbid them explicitly and publish the same strict schema used at execution.
for _tool in mcp._tool_manager.list_tools():
 _model=_tool.fn_metadata.arg_model
 _model.model_config={**_model.model_config,'extra':'forbid','strict':True}
 _model.model_rebuild(force=True)
 _tool.parameters=_model.model_json_schema()
