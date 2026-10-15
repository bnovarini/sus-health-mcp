"""Approved fixed annual residence billing views; no clinical or patient finding."""
import pathlib,json,hashlib,re
UF='AC AL AP AM BA CE ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split()
def check_artifact(root):
 root=pathlib.Path(root);m=json.loads((root/'metadata.json').read_text());p=root/'surface-intervals.json'
 if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=m['artifact_sha256']:raise ValueError('Deeper artifact integrity failed')
 return m
def query(root,uf,year,surface,municipality='',limit=30):
 meta=check_artifact(root)
 if uf not in UF or type(year) is not int or year not in meta['years']:raise ValueError('Unsupported UF/year; DF excluded, not zero')
 if surface not in meta['surfaces']:raise ValueError('Only three fixed reviewed residence surfaces')
 if municipality and (not re.fullmatch('[0-9]{6}',municipality) or municipality.startswith('53')):raise ValueError('Invalid municipality')
 if type(limit) is not int or not 1<=limit<=100:raise ValueError('Limit 1-100')
 a=json.loads((pathlib.Path(root)/'surface-intervals.json').read_text());rows=[r for r in a['rows'] if r['year']==year and r['surface']==surface and r['municipality'][:2]==meta['uf_codes'][uf] and (not municipality or r['municipality']==municipality)];rows.sort(key=lambda r:(-r['lower'],r['municipality'],r['label']))
 return {'rows':rows[:limit],'truncated':len(rows)>limit,'surface_definition':meta['surfaces'][surface],'warnings':meta['warnings']+meta['surfaces'][surface]['warnings'],'missing':'Suppressed, targeted-withheld, invalid geography or absent; unknown, not zero and no upper bound implied.','unit':'PA billing source-record events, not people','period':'Processing-file year; 2026 Jan-Jul partial. Not attendance-year or unique clinical episodes.','release_id':meta['release_id'],'automatic_replacement':False}
