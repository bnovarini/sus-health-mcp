"""Synthetic reader checks; no clinical artifacts or private audit data."""
import tempfile,pathlib,json,hashlib,unittest
import duckdb
from sus_health_mcp.provider_activity import ProviderCandidate,WORK
class ProviderTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.r=pathlib.Path(self.tmp.name);(self.r/'candidate').mkdir();c=duckdb.connect();parts={}
  for kind,col in [('cid','cid'),('procedure','procedure'),('catchment','residence_uf_code')]:
   p=self.r/'candidate'/(kind+'.parquet');rows=[('0000001','330390','33'if kind=='catchment'else code,20,29)for code in(['A001']if kind=='catchment'else['A001','A002'])];c.execute('CREATE OR REPLACE TABLE x(facility VARCHAR,provider_municipality VARCHAR,'+col+' VARCHAR,records_lower BIGINT,records_upper BIGINT)');c.executemany('INSERT INTO x VALUES(?,?,?,?,?)',rows);c.execute('COPY x TO ?(FORMAT PARQUET)',[str(p)]);parts[kind]={'filename':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  c.close();(self.r/'candidate-metadata.json').write_text(json.dumps({'partitions':{'RD2025':parts},'provider_municipality_codes':['330390'],'residence_uf_codes':['33'],'release_id':'synthetic','units':{'RD':'records'},'warnings':[],'private_only':True,'release_ready':False}));self.api=ProviderCandidate(self.r)
 def tearDown(self):self.tmp.cleanup()
 def test_pages(self):
  a=self.api.page('cid','RD',2025,'0000001','330390',limit=1);self.assertTrue(a['has_more']);b=self.api.page('cid','RD',2025,'0000001','330390',limit=1,cursor=a['next_cursor']);self.assertEqual(b['rows'][0]['cid'],'A002')
  with self.assertRaises(ValueError):self.api.page('procedure','RD',2025,'0000001','330390',cursor=a['next_cursor'])
 def test_inputs_and_slot(self):
  with self.assertRaises(ValueError):self.api.page('cid','RD',True,'0000001','330390')
  with self.assertRaises(ValueError):self.api.page('cid','RD',2025,'0000001','330390',code='A*')
  WORK.acquire()
  try:
   with self.assertRaises(ValueError):self.api.page('cid','RD',2025,'0000001','330390')
  finally:WORK.release()
if __name__=='__main__':unittest.main()
