"""Synthetic only: no real healthcare cells or private review material."""
import hashlib,json,pathlib,tempfile,unittest
import duckdb
from sus_health_mcp.state_activity import StateCandidate
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=pathlib.Path(self.tmp.name);art={}
  for kind in ['cid','procedure']:
   p=self.root/(kind+'.parquet');c=duckdb.connect();c.execute('CREATE TABLE cells(uf VARCHAR,year INTEGER,family VARCHAR,'+kind+' VARCHAR,records_lower BIGINT,records_upper BIGINT)');c.executemany('INSERT INTO cells VALUES(?,?,?,?,?,?)',[('SP',2025,'PA',x,20+i*10,29+i*10)for i,x in enumerate(['A00','B00','C00'])]);c.execute('COPY cells TO ?(FORMAT PARQUET)',[str(p)]);c.close();art[kind]={'filename':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  (self.root/'phase2-metadata.json').write_text(json.dumps({'artifacts':art,'release_id':'synthetic-test','units':{'PA':'synthetic source records'},'warnings':['Synthetic only']}));self.api=StateCandidate(self.root)
 def test_page(self):
  a=self.api.page('cid','SP',2025,'PA',limit=2);self.assertEqual(len(a['rows']),2);b=self.api.page('cid','SP',2025,'PA',limit=2,cursor=a['next_cursor']);self.assertEqual([r['cid']for r in b['rows']],['C00']);self.assertTrue(all(type(r['records_lower'])is int for r in a['rows']))
 def test_cursor(self):
  a=self.api.page('cid','SP',2025,'PA',limit=1)
  with self.assertRaises(ValueError):self.api.page('cid','RJ',2025,'PA',cursor=a['next_cursor'])
  with self.assertRaises(ValueError):self.api.page('procedure','SP',2025,'PA',cursor=a['next_cursor'])
 def test_scope(self):
  for k,u,y,f in [('joint','SP',2025,'PA'),('cid','DF',2025,'PA'),('cid','SP',2027,'PA'),('cid','SP',True,'PA'),('cid','SP',2025,'DO')]:
   with self.assertRaises(ValueError):self.api.page(k,u,y,f)
 def test_limit(self):
  for v in [0,101,True,'2']:
   with self.assertRaises(ValueError):self.api.page('cid','SP',2025,'PA',limit=v)
 def test_exact_and_unknown(self):
  a=self.api.page('cid','SP',2025,'PA',code='A00');self.assertEqual([r['cid']for r in a['rows']],['A00']);a=self.api.page('cid','SP',2025,'PA',code='A01');self.assertFalse(a['rows']);self.assertIn('Unknown',a['missing'])
 def test_integrity(self):
  (self.root/'cid.parquet').write_bytes(b'changed')
  with self.assertRaises(AssertionError):StateCandidate(self.root)
 def test_busy(self):
  self.api.lock.acquire()
  try:
   with self.assertRaises(ValueError):self.api.page('cid','SP',2025,'PA')
  finally:self.api.lock.release()
  self.assertTrue(self.api.page('cid','SP',2025,'PA')['rows'])
if __name__=='__main__':unittest.main()
