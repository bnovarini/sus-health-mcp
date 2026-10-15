"""Ecological multi-signal ranking, never prevalence or person-level overlap.

Comparisons use each cell's lower bound against a conservative geographic
baseline upper bound. Omitted cells may be suppressed or missing, never zero.
The caller must certify complete source coverage, fixed signal definitions,
complete geography, and a matching sourced population vintage before calling.
"""

def rank_pockets(rows,population,signal_names,minimum_signals=2,*,coverage_complete=False,suppression_threshold=20,suppression_grain_matches_signal=False):
 if not coverage_complete:raise ValueError('Complete geographic source coverage must be verified before ranking')
 if not suppression_grain_matches_signal:raise ValueError('Signal-grain suppression bound must be verified; finer omitted cells can exceed the threshold')
 if len(set(signal_names))!=len(signal_names) or len(signal_names)<minimum_signals:raise ValueError('At least two distinct documented proxies required')
 if not population or any(p<=0 for p in population.values()):raise ValueError('Complete positive population denominators required')
 by={};totals={s:0 for s in signal_names}
 for r in rows:
  s=r['signal'];m=r['municipality']
  if s not in totals:continue
  if m not in population:raise ValueError('Signal municipality missing from population crosswalk')
  if (m,s) in by:raise ValueError('Duplicate signal row; aggregate explicitly before ranking')
  if not suppression_threshold<=r['lower']<=r['upper']:raise ValueError('Invalid released interval')
  by[m,s]=r
 total_pop=sum(population.values())
 # Even with complete sources an omitted cell can contain 0..threshold-1
 # events. Include that uncertainty rather than treating omissions as zero.
 baseline_upper={s:sum(by[m,s]['upper'] if (m,s) in by else suppression_threshold-1 for m in population)/total_pop for s in signal_names}
 results=[]
 for m,pop in population.items():
  elevated=[]
  for s in signal_names:
   r=by.get((m,s))
   if not r or baseline_upper[s]<=0:continue
   ratio=(r['lower']/pop)/baseline_upper[s]
   if ratio>=1.5:elevated.append({'signal':s,'activity_interval':[r['lower'],r['upper']],'relative_activity_lower':round(ratio,3),'baseline_rate_upper':baseline_upper[s]})
  if len(elevated)>=minimum_signals:
   results.append({'municipality':m,'population':pop,'elevated_signals':elevated,'rank_statistic':min(x['relative_activity_lower'] for x in elevated),'meaning':'multiple aggregate activity proxies elevated in the same geography, not the same people','baseline':'conservative upper bound including suppressed-cell uncertainty; complete source coverage required'})
 return sorted(results,key=lambda r:(-len(r['elevated_signals']),-r['rank_statistic'],r['municipality']))
