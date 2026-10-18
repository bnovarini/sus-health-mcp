"""Fixed annual series composition of already-frozen intervals. No listener or mutation."""
import pathlib,json,hashlib,re
from decimal import Decimal,ROUND_FLOOR,ROUND_CEILING
R=pathlib.Path(__import__('os').environ.get('SUS_SERIES_DATA','/app/data/series'))
from .state_activity import StateCandidate
def rate_bounds(lo,hi,pop):
 if not all(type(x)is int for x in [lo,hi,pop])or lo<0 or hi<lo or pop<=0:raise ValueError('Invalid interval/population')
 scale=Decimal(100000)/Decimal(pop);unit=Decimal('.001')
 return {'lower':str((Decimal(lo)*scale).quantize(unit,rounding=ROUND_FLOOR)),'upper':str((Decimal(hi)*scale).quantize(unit,rounding=ROUND_CEILING)),'unit':'Administrative source records per100,000 total residents;not people,incidence,prevalence or SUS utilization probability','rounding':'Outward to0.001;original record interval retained'}
class Series:
 def __init__(self,state_root='/app/data/state',context_root=R,state_api=None):
  self.state=state_api if state_api is not None else StateCandidate(state_root);self.root=pathlib.Path(context_root);manifest=json.loads((self.root/'phase3-manifest.json').read_text())
  for name,digest in manifest['context_hashes'].items():
   if hashlib.sha256((self.root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Context integrity')
  self.population=json.loads((self.root/'population-context.json').read_text());self.coverage={(x['family'],x['year']):x for x in json.loads((self.root/'source-period-coverage.json').read_text())}
 def series(self,kind,uf,family,code,years=(2022,2023,2024,2025)):
  if not isinstance(code,str)or not re.fullmatch('[A-Z0-9]{1,10}',code):raise ValueError('One exact source code required')
  if not isinstance(years,(tuple,list))or not 1<=len(years)<=5 or len(set(years))!=len(years)or any(type(y)is not int or y not in range(2022,2027)for y in years):raise ValueError('One to five distinct fixed years')
  out=[]
  for year in sorted(years):
   page=self.state.page(kind,uf,year,family,code=code,limit=1);assert not page['has_more'];rows=page['rows'];cover=self.coverage[(family,year)];pop=next(x for x in self.population['rows']if x['uf']==uf and x['year']==year);flags=[]
   if year==2026:flags.append('PartialJanuary-Julyprocessingfiles,notcomparabletofullyear;noannualizationorannualrecordrate')
   if cover['missing_billing_uf_months']:flags.append('Missingbilling-UF/monthfilescanbiasallresidenceUFs;absenceisunknown')
   if family in ['PA','AM']and year>=2025:flags.append('SIA2025codingnoticequalifiesascertainment;breaksarenotmeasuredorcorrected')
   if family=='AM':flags.append('APACrecordfrequency,notmedicationdoses,prescriptionsordispensing')
   placeholder=kind=='cid'and (code in ['0000','1111']or not re.fullmatch('[A-Z][0-9]{2}[0-9X]?',code))
   if placeholder:flags.append('PlaceholderorunvalidatedCIDformat;notadiagnosis;populationratewithheld')
   rate=None
   if rows and year!=2026 and not placeholder:rate=rate_bounds(rows[0]['records_lower'],rows[0]['records_upper'],pop['population'])
   out.append({'year':year,'records':rows[0]if rows else None,'missing_status':None if rows else 'Unknown,notzero;cannotdistinguishsuppression/missing/absentcode','population_context':{'population':pop['population'],'reference_date':str(year)+'-07-01','vintage':self.population['vintage'],'unit':self.population['unit']},'record_rate_interval':rate,'coverage':cover,'flags':flags,'existing_warnings':page['warnings']})
  return {'status':'fixed_annual_series','query':{'kind':kind,'uf':uf,'family':family,'exact_source_code':code,'years':sorted(years)},'points':out,'same_processing_window':len({tuple(x['coverage']['processing_months'])for x in out})==1,'all_expected_billing_file_slots_present':all(not x['coverage']['missing_billing_uf_months']for x in out),'automatic_trend_classification':False,'no_year_sums_or_code_pools':True,'interpretation':'Separateannualsource-recordcohorts,notpatientfollow-upordiseasetrends;noexactdeltas/cumulativecounts/interpolation/annualization','population_source':self.population['source_url'],'population_source_sha256':self.population['source_sha256'],'geography_limit':'PopulationprojectionusesitsownUFvintage;frozen2024clinicalmunicipalitymembershipunchanged. Boundarychangescanlimitcomparison.'}

 def methods(self):
  return {'status':'fixed_annual_series','population_source':self.population['source_url'],'population_source_sha256':self.population['source_sha256'],'population_vintage':self.population['vintage'],'population_reference_date':self.population['reference_date'],'population_unit':self.population['unit'],'source_period_coverage':list(self.coverage.values()),'warnings':self.state.methods()['warnings'],'rate_method':'Visible integer record bounds transformed with the same public denominator; outward-rounded to0.001per100,000. Count bounds retained. No annual rate for2026 or placeholder CID. No rates for missing cells.','limits':'Administrative source records per total resident, not people, incidence, prevalence or SUS utilization probability. Separate annual cohorts, not patient trajectories. No totals, deltas, code pools, automatic trend labels or annualization. Full slot coverage is not clinical ascertainment or independent publisher reconciliation.','geography':'Population projection UF vintage and frozen2024 clinical municipality membership differ; no silent remapping.','population_2022':'Reconstructed demographic estimate, not raw census enumeration','population_2023_onward':'Projection from the stated revision, not a claim of latest annual estimate'}
