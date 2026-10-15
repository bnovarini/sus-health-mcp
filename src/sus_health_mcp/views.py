"""Post-processing only: never read private clinical cubes.

Intervals describe visible activity. Missing cells remain unknown, so a sum of
visible cells is not a bound on the entire unsuppressed administrative total.
"""
import collections,re
from .canonical import UF_CODES
UNITS={'RD':'approved hospital admissions; not people','PA':'approved outpatient quantity; units differ by procedure','AM':'medication APAC source records; not patients or doses','DO':'death-certificate events; national mortality, not SUS-only'}

def visible_activity(rows,*,family,years,uf='',municipality='',cid_prefix='',procedure='',by='year'):
 if family not in UNITS:raise ValueError('Unsupported family')
 if by not in ('year','municipality','cid','procedure'):raise ValueError('Unsupported grouping')
 if uf and uf not in UF_CODES.values():raise ValueError('Invalid UF')
 if municipality and not re.fullmatch('[0-9]{6}',municipality):raise ValueError('Invalid municipality')
 if cid_prefix and not re.fullmatch('[A-Z][0-9]{0,3}',cid_prefix):raise ValueError('Invalid CID prefix')
 if procedure and not re.fullmatch('[0-9]{10}',procedure):raise ValueError('Ten-digit procedure required')
 if family=='DO' and procedure:raise ValueError('Mortality has no procedure codes')
 groups=collections.defaultdict(lambda:[0,0,0]);seen=set()
 for r in rows:
  if r['family']!=family or r['year'] not in years:continue
  if uf and r['uf']!=uf:continue
  if municipality and r['municipality']!=municipality:continue
  if cid_prefix and not r['cid'].startswith(cid_prefix):continue
  if procedure and r['procedure']!=procedure:continue
  key=tuple(r[k] for k in ['family','year','municipality','cid','procedure'])
  if key in seen:raise ValueError('Duplicate canonical cell')
  seen.add(key)
  measure='quantity' if family in ('RD','PA') else 'records'
  low,high=r[measure+'_lower'],r[measure+'_upper']
  if low<0 or high<low:raise ValueError('Invalid canonical interval')
  g=groups[r[by]];g[0]+=low;g[1]+=high;g[2]+=1
 return {'rows':[{by:k,'visible_lower':v[0],'visible_upper':v[1],'visible_cells':v[2]} for k,v in sorted(groups.items())],
         'family':family,'unit':UNITS[family],'missing':'suppressed, unknown or unavailable; never zero',
         'scope':'sum of published visible cell intervals only; not the complete underlying total',
         'geography':'residence municipality','period':'processing-file year; not treatment/admission year',
         'overlap':'PA includes AM-related production; never sum PA and AM'}
