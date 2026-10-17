"""Synthetic public-reference fixture; no clinical data or private audits."""
import pathlib,tempfile,sqlite3,json,hashlib,unittest
from sus_health_mcp.activity_context import Tariffs
class Tests(unittest.TestCase):
 def test_reference(self):
  with tempfile.TemporaryDirectory()as root:
   p=pathlib.Path(root);c=sqlite3.connect(p/'tariffs.sqlite');c.executescript('CREATE TABLE procedure(vintage TEXT,code TEXT,name TEXT,sh_raw TEXT,sa_raw TEXT,sp_raw TEXT,sh_cents INTEGER,sa_cents INTEGER,sp_cents INTEGER,financing TEXT,source TEXT);CREATE TABLE relation(vintage TEXT,code TEXT,kind TEXT,target TEXT);CREATE TABLE label(vintage TEXT,kind TEXT,code TEXT,name TEXT);');c.execute('INSERT INTO procedure VALUES(?,?,?,?,?,?,?,?,?,?,?)',['202608','0000000001','Synthetic','0000','1000','0010',0,1000,10,'06','synthetic']);c.commit();c.close();(p/'tariff-metadata.json').write_text(json.dumps({'filename':'tariffs.sqlite','sha256':hashlib.sha256((p/'tariffs.sqlite').read_bytes()).hexdigest(),'vintages':['202608'],'limits':[],'release_ready':False}));t=Tariffs(p);d=t.lookup('0000000001','202608');self.assertEqual(d['components']['sa']['BRL'],'10.00');self.assertEqual(d['components']['sp']['BRL'],'0.10');self.assertEqual(t.lookup('0000000000','202608')['status'],'unmapped_source_code_preserved')
   with self.assertRaises(ValueError):t.lookup('0000*','202608')
   with self.assertRaises(ValueError):t.lookup('0000000001','202609')
if __name__=='__main__':unittest.main()
