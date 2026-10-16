"""Synthetic tests only. No publisher files or clinical data shipped in git."""
import hashlib,json,pathlib,tempfile,unittest,threading
from sus_health_mcp.foundation.foundation import ReleasedCells,cursor_encode,cursor_decode,limit_check,norm,filehash
from sus_health_mcp.foundation.exporter import export_released
from sus_health_mcp.foundation.json_cells import ReleasedJSON
from sus_health_mcp.foundation.mcp_foundation_candidate import ClinicalQuery,register
class FoundationTests(unittest.TestCase):
 def test_cursor_query_release_binding(self):
  t=cursor_encode('r',{'a':1},['x']);self.assertEqual(cursor_decode(t,'r',{'a':1}),['x'])
  for r,q in [('bad',{'a':1}),('r',{'a':2})]:
   with self.assertRaises(ValueError):cursor_decode(t,r,q)
  with self.assertRaises(ValueError):cursor_decode('garbage','r',{})
 def test_limits_and_unicode(self):
  for v in [0,101,True,'10']:
   with self.assertRaises(ValueError):limit_check(v)
  self.assertEqual(norm('Petrópolis'),'petropolis')
 def test_page_complete_and_export_exclusive(self):
  import duckdb
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp)/'synthetic.parquet';c=duckdb.connect();c.execute("COPY (SELECT 'RD' AS family,'RJ' AS uf,2025 AS year,printf('%06d',i) AS municipality,'Z730' AS cid,20 records_lower,29 records_upper FROM range(1,254)t(i)) TO ? (FORMAT PARQUET)",[str(p)]);c.close();h=filehash(p);r=ReleasedCells(p,h,'fictional','clinical',{'release_id':'fictional','clinical_sha256':h,'approved_scopes':{'2025':['RD']}});q={'uf':'RJ','year':2025,'family':'RD'};rows=[];cursor=''
   while True:
    d=r.page(**q,limit=100,cursor=cursor);rows+=d['rows'];cursor=d['next_cursor']
    if not cursor:break
   self.assertEqual(len(rows),253);self.assertEqual(len({x['municipality']for x in rows}),253);self.assertIn('bulk',d['bulk_access_warning'])
   out=pathlib.Path(tmp)/'out.jsonl';m={'release_id':'fictional','artifact_sha256':h,'query_spec':q};e=export_released(r,out,q,m);self.assertEqual(e['visible_cells'],253);self.assertEqual(out.stat().st_mode&0o777,0o600)
   with self.assertRaises(ValueError):export_released(r,out,q,m)
   with self.assertRaises(ValueError):r.page('DF',2025,'RD')
   with self.assertRaises(ValueError):ReleasedCells(p,'bad','fictional','clinical')
 def test_duplicate_keys_fail_closed(self):
  import duckdb
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp)/'p.parquet';c=duckdb.connect();c.execute("COPY (SELECT 'RD' AS family,'RJ' AS uf,2025 AS year,'330390' AS municipality,'Z730' AS cid,20 records_lower,29 records_upper FROM range(2)) TO ? (FORMAT PARQUET)",[str(p)]);c.close();h=filehash(p);r=ReleasedCells(p,h,'r','clinical',{'release_id':'r','clinical_sha256':h,'approved_scopes':{'2025':['RD']}})
   with self.assertRaises(ValueError):r.page('RJ',2025,'RD')
 def test_json_pages_preserve_existing_cells(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp)/'known.json';p.write_text(json.dumps({'maps':[{'year':2025,'uf':'35','residence':'350950','category':str(i),'lower':20,'upper':29}for i in range(5)]}));h=filehash(p);r=ReleasedJSON(p,h,'r','known_care',{'release_id':'r','known_care_sha256':h,'years':[2025],'uf_codes':{'SP':'35'},'warnings':[]});a=r.page('SP',2025,view='residence',limit=2);b=r.page('SP',2025,view='residence',limit=2,cursor=a['next_cursor']);self.assertEqual(len(a['rows']),2);self.assertFalse({x['category']for x in a['rows']}&{x['category']for x in b['rows']})
 def test_strict_discriminated_query(self):
  for q in [{'kind':'clinical','uf':'RJ','year':'2025','family':'PA'},{'kind':'clinical','uf':'RJ','year':2025,'family':'PA','procedure':'123'}]:
   with self.assertRaises(Exception):ClinicalQuery(**q)
 def test_registration_five_tools_no_listener(self):
  class Dummy:
   def __init__(self):self.tools={}
   def tool(self):
    def wrap(f):self.tools[f.__name__]=f;return f
    return wrap
  d=Dummy();register(d,object());self.assertEqual(len(d.tools),5)
