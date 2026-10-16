"""Synthetic population and activity only; no publisher workbook or clinical data."""
import pathlib,json,hashlib,tempfile,unittest
from decimal import Decimal
from sus_health_mcp.annual_series import Series,rate_bounds
class Reader:
 def page(self,kind,uf,year,family,code,limit):
  if kind not in ['cid','procedure']or uf not in ['SP','RJ']or family not in ['RD','PA','AM']:raise ValueError('scope')
  rows=[]if code=='A01'else [{'uf':uf,'year':year,'family':family,kind:code,'records_lower':20,'records_upper':29}]
  return {'rows':rows,'has_more':False,'warnings':['Synthetic only']}
 def methods(self):return {'warnings':['Synthetic only']}
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=pathlib.Path(self.tmp.name)
  p={'source_url':'https://example.invalid/synthetic','source_sha256':'synthetic','vintage':'synthetic','reference_date':'July1','unit':'synthetic residents','rows':[{'uf':u,'year':y,'population':100003}for u in ['SP','RJ']for y in range(2022,2027)]};c=[{'family':f,'year':y,'processing_months':list(range(1,8 if y==2026 else 13)),'missing_billing_uf_months':[{'uf':'RJ','month':1}]if f=='AM'else []}for f in ['RD','PA','AM']for y in range(2022,2027)]
  for n,d in [('population-context.json',p),('source-period-coverage.json',c)]:
   (self.root/n).write_text(json.dumps(d))
  manifest={'context_hashes':{n:hashlib.sha256((self.root/n).read_bytes()).hexdigest()for n in ['population-context.json','source-period-coverage.json']}};(self.root/'phase3-manifest.json').write_text(json.dumps(manifest));self.api=Series(context_root=self.root,state_api=Reader())
 def test_rounding(self):
  for pop in [1,1000,100003,99999999]:
   d=rate_bounds(20,29,pop);self.assertLessEqual(Decimal(d['lower']),Decimal(20)*100000/pop);self.assertGreaterEqual(Decimal(d['upper']),Decimal(29)*100000/pop)
 def test_partial(self):
  d=self.api.series('cid','SP','PA','A00',[2025,2026]);self.assertFalse(d['same_processing_window']);self.assertIsNone(d['points'][1]['record_rate_interval']);self.assertIsNotNone(d['points'][0]['record_rate_interval'])
 def test_bounds(self):
  d=self.api.series('cid','SP','PA','A00',[2025]);self.assertEqual(d['points'][0]['records']['records_lower'],20);self.assertFalse(d['automatic_trend_classification']);self.assertTrue(d['no_year_sums_or_code_pools'])
 def test_missing(self):
  d=self.api.series('cid','SP','PA','A01',[2025]);self.assertIsNone(d['points'][0]['records']);self.assertIsNone(d['points'][0]['record_rate_interval']);self.assertIn('Unknown',d['points'][0]['missing_status'])
 def test_gaps(self):
  d=self.api.series('procedure','SP','AM','A00',[2025]);self.assertFalse(d['all_expected_billing_file_slots_present']);self.assertTrue(d['points'][0]['flags'])
 def test_placeholder(self):self.assertIsNone(self.api.series('cid','SP','PA','0000',[2025])['points'][0]['record_rate_interval'])
 def test_scope(self):
  for years in [[True],[2027],[2025,2025],[]]:
   with self.assertRaises(ValueError):self.api.series('cid','SP','PA','A00',years)
  for code in ['','Z73*','A00 OR1=1']:
   with self.assertRaises(ValueError):self.api.series('cid','SP','PA',code,[2025])
 def test_integrity(self):
  (self.root/'population-context.json').write_text('{}')
  with self.assertRaises(ValueError):Series(context_root=self.root,state_api=Reader())
if __name__=='__main__':unittest.main()
