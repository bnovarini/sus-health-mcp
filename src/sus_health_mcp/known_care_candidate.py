"""Fixed reviewed E851 billing activity and flows, never people."""
import json,pathlib,hashlib,re
UF='AC AL AP AM BA CE ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split()
def check_artifact(root):
 root=pathlib.Path(root);m=json.loads((root/'known-care-metadata.json').read_text());p=root/'known-care.json'
 if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=m['known_care_sha256']:raise ValueError('Knowncareartifactintegrityfailed')
 return m
def query(root,uf,year,view='residence',municipality='',limit=30):
 m=check_artifact(root)
 if uf not in UF or type(year) is not int or year not in m['years']:raise ValueError('UnsupportedUF/year;DFexcluded')
 if view not in ('residence','flows'):raise ValueError('Onlyfixedresidenceorflowsviews')
 if municipality and (not re.fullmatch('[0-9]{6}',municipality) or municipality.startswith('53')):raise ValueError('Invalidmunicipality')
 if type(limit) is not int or not 1<=limit<=100:raise ValueError('Limit1-100')
 a=json.loads((pathlib.Path(root)/'known-care.json').read_text());rows=[r for r in a['maps' if view=='residence' else 'flows'] if r['year']==year and r['uf']==m['uf_codes'][uf] and (not municipality or r['residence']==municipality)];rows.sort(key=lambda r:(-r['records_lower'],r['residence'],r['category'],r.get('billing_provider_municipality','')))
 return {'rows':rows[:limit],'truncated':len(rows)>limit,'warnings':m['warnings'],'missing':'Suppressed,targetedwithheld,invalidgeographyorabsent;notzero,noupperbound','unit':'Sourcebillingrecords,notpeople','provider_geography':'Billingprovidermunicipality,notconfirmedclinicalhospital','period':'Processingfileyear;2026Jan-Julpartial','release_id':m['release_id']}
