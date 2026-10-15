"""Receipt-based coverage. Missing inventory files do not establish zero activity."""
import json,pathlib,collections,hashlib

def coverage(manifest,receipts):
 groups=collections.defaultdict(lambda:{'expected':[],'received':[],'missing':[]})
 expected_names=set()
 for entry in manifest:
  name=entry['name']
  if name in expected_names:raise ValueError('Duplicate manifest filename: '+name)
  expected_names.add(name);key=(entry['prefix'],entry['uf'],entry['year'],entry.get('month') or 0)
  g=groups[key];g['expected'].append(name);r=receipts.get(name)
  if r:
   if any(r.get(k)!=entry.get(k) for k in ['name','size','url']):raise ValueError('Receipt/source mismatch: '+name)
   if not r.get('sha256') or len(r['sha256'])!=64:raise ValueError('Missing checksum: '+name)
   g['received'].append(name)
  else:g['missing'].append(name)
 return [{'family':k[0],'uf':k[1],'year':k[2],'file_month':k[3],'expected_parts':len(g['expected']),'received_parts':len(g['received']),'complete_for_inventory':not g['missing'],'missing_files':g['missing']} for k,g in sorted(groups.items())]

def build(manifest_path,receipt_path,out):
 mpath=pathlib.Path(manifest_path);manifest=json.loads(mpath.read_text());receipts={}
 for p in pathlib.Path(receipt_path).glob('*.json'):
  r=json.loads(p.read_text())
  if r.get('name') and r.get('sha256'):receipts[r['name']]=r
 rows=coverage(manifest,receipts)
 result={'status':'private_build_coverage_not_release_certification','manifest_sha256':hashlib.sha256(mpath.read_bytes()).hexdigest(),'expected_files':len(manifest),'received_files':sum(r['received_parts'] for r in rows),'periods':rows,'notes':['Complete means all parts in this manifest have verified receipts, not that the publisher has finalized the period.','Periods absent from the publisher inventory are not zero.','SIH/SIA file month is processing-file month, not proven service month.','2026 partial publication must not be compared as a full year.']}
 pathlib.Path(out).write_text(json.dumps(result,indent=2));return result
