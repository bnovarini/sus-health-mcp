"""Complete existing-cell JSONL export and query manifest,private by default."""
import pathlib,json,os
from .foundation import filehash

def export_released(reader,path,query,methods):
 if methods.get('artifact_sha256')!=reader.sha or methods.get('release_id')!=reader.release or methods.get('query_spec')!=query:raise ValueError('Matching methods manifest required')
 if 'cursor' in query or 'limit' in query:raise ValueError('Exporter owns pagination')
 out=pathlib.Path(path);manifest_path=out.with_suffix(out.suffix+'.manifest.json');tmp=out.with_suffix(out.suffix+'.partial');mtmp=manifest_path.with_suffix(manifest_path.suffix+'.partial')
 for p in [out,manifest_path,tmp,mtmp]:
  if p.exists() or p.is_symlink():raise ValueError('Export destination already exists')
 cursor='';pages=0;visible_cells=0;installed=[]
 try:
  with open(tmp,'x',encoding='utf8') as f:
   os.chmod(tmp,0o600)
   if hasattr(reader,'iter_rows'):
    for row in reader.iter_rows(**query):
     f.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n');visible_cells+=1
    pages=None
   else:
    while True:
     d=reader.page(**query,limit=100,cursor=cursor);pages+=1
     for row in d['rows']:f.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n');visible_cells+=1
     cursor=d['next_cursor']
     if not cursor:break
  manifest={'release_id':reader.release,'artifact_sha256':reader.sha,'query_spec':query,'export_sha256':filehash(tmp),'visible_cells':visible_cells,'pages':pages,'complete_for_approved_visible_lattice':True,'complete_source_population':False,'unit':'registry_fields_not_realtime_capacity' if reader.kind=='capacity' else 'source_records_intervals_not_people','missing':'unknown_not_zero;withheld_and_absent_not_separately_diagnosable','suppression_unchanged':True,'no_new_aggregates':True,'format':'jsonl','methods':methods,'audience':'private_owner_only;publication_requires_review'}
  with open(mtmp,'x',encoding='utf8') as f:
   os.chmod(mtmp,0o600);json.dump(manifest,f,indent=2)
  # Exclusive links fail rather than replace a destination created during export.
  os.link(tmp,out);installed.append(out);os.link(mtmp,manifest_path);installed.append(manifest_path)
  return manifest
 except Exception:
  for p in installed:p.unlink(missing_ok=True)
  raise
 finally:
  tmp.unlink(missing_ok=True);mtmp.unlink(missing_ok=True)
