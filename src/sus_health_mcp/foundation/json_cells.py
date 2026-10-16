"""Adapters over existing frozen JSON outputs,no new combinations."""
import pathlib,json
from .foundation import limit_check,cursor_decode,cursor_encode
UF='AC AL AP AM BA CE ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split()
class ReleasedJSON:
 def __init__(self,path,sha256,release_id,kind,scope_metadata):
  from .foundation import filehash
  self.path=pathlib.Path(path);self.sha=sha256;self.release=release_id;self.kind=kind;self.scope=scope_metadata
  if kind not in ['known_care','deeper'] or self.path.is_symlink() or filehash(self.path)!=sha256:raise ValueError('Invalid frozen JSON artifact')
 def page(self,uf,year,view='',surface='',municipality='',limit=100,cursor=''):
  import re
  limit_check(limit)
  if self.scope.get('release_id')!=self.release or self.scope.get('known_care_sha256' if self.kind=='known_care' else 'artifact_sha256')!=self.sha:raise ValueError('Scope/artifact identity mismatch')
  if uf not in UF or type(year)!=int or year not in self.scope['years']:raise ValueError('Unsupported UF/year;DF excluded')
  if municipality and (not re.fullmatch('[0-9]{6}',municipality) or municipality.startswith('53')):raise ValueError('Invalid municipality')
  if self.kind=='known_care':
   if view not in ['residence','flows'] or surface:raise ValueError('Only frozen residence/flows outputs')
   keys=['residence','category']+(['billing_provider_municipality'] if view=='flows' else []);data=json.loads(self.path.read_text())['maps' if view=='residence' else 'flows'];rows=[r for r in data if r['year']==year and r['uf']==self.scope['uf_codes'][uf] and (not municipality or r['residence']==municipality)]
  else:
   if surface not in self.scope['surfaces'] or view:raise ValueError('Only frozen deeper surfaces')
   keys=['municipality','label'];data=json.loads(self.path.read_text())['rows'];rows=[r for r in data if r['year']==year and r['surface']==surface and r['municipality'][:2]==self.scope['uf_codes'][uf] and (not municipality or r['municipality']==municipality)]
  spec={'uf':uf,'year':year,'view':view,'surface':surface,'municipality':municipality};last=cursor_decode(cursor,self.sha,spec) if cursor else ['']*len(keys)
  if len(last)!=len(keys) or any(not isinstance(x,str) for x in last):raise ValueError('Invalid cursor key')
  if len({tuple(r[k] for k in keys) for r in rows})!=len(rows):raise ValueError('Nonunique frozen keys;requires reviewed adapter')
  rows=sorted((r for r in rows if tuple(r[k] for k in keys)>tuple(last)),key=lambda r:tuple(r[k] for k in keys));more=len(rows)>limit;rows=rows[:limit]
  return {'rows':rows,'has_more':more,'next_cursor':cursor_encode(self.sha,spec,[rows[-1][k] for k in keys]) if more else None,'query_spec':spec,'release_id':self.release,'artifact_sha256':self.sha,'warnings':self.scope['warnings']+(self.scope['surfaces'][surface]['warnings'] if self.kind=='deeper' else []),'unit':'source_record_events_not_people','period':'processing_file_year;2026Jan-Julpartial','missing':'unknown_not_zero;suppressed_targeted_withheld_invalid_or_absent','no_new_aggregates':True,'bulk_access_warning':'Pagination makes bulk collection of existing released cells easier. No anonymity or sub20 secrecy guarantee;linkage and inference risks remain.'}
