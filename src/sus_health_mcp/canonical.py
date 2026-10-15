"""One frozen clinical activity lattice, for private release assessment only.

All clinical views must be post-processing of these cells. Suppressed cells
are absent, never zeros. This is not person anonymity or privacy certification.
Do not expose this artifact until reconciliation and reconstruction review pass.
"""
import pathlib,json,hashlib,duckdb
UF_CODES=dict(zip('11 12 13 14 15 16 17 21 22 23 24 25 26 27 28 29 31 32 33 35 41 42 43 50 51 52 53'.split(),'RO AC AM RR PA AP TO MA PI CE RN PB PE AL SE BA MG ES RJ SP PR SC RS MS MT GO DF'.split()))

def prepare(private,out,population,coverage,*,years=(2022,2023,2024),threshold=20,width=10):
 """Build candidate immutable annual municipality/CID/procedure cells.

 Coverage must include every nationwide split file for selected families/years.
 The source year is the file-processing year, not an inferred treatment year.
 Clinical quantities are rounded as well as records. Financial values omitted.
 """
 if threshold<20 or width<10:raise ValueError('Cannot weaken candidate privacy parameters')
 years=tuple(sorted(set(years)))
 if not years or any(y not in (2022,2023,2024) for y in years):raise ValueError('Only complete stable overlapping years supported')
 selected=[r for r in coverage['periods'] if r['family'] in ('RD','PA','AM','DO') and r['year'] in years]
 if not selected or any(not r['complete_for_inventory'] for r in selected):raise ValueError('Incomplete clinical source coverage')
 for family in ('RD','PA','AM','DO'):
  for year in years:
   rows=[r for r in selected if r['family']==family and r['year']==year]
   for uf in UF_CODES.values():
    months={r['file_month'] for r in rows if r['uf']==uf}
    if months != ({0} if family=='DO' else set(range(1,13))):raise ValueError('Missing nationwide annual coverage')
 pop=population['rows'];municipalities={r['municipality'] for r in pop}
 if len(municipalities)!=5570:raise ValueError('Complete verified municipality crosswalk required')
 root=pathlib.Path(out);root.mkdir(parents=True,exist_ok=True)
 if (root/'clinical.parquet').exists():raise ValueError('Frozen candidate cannot be overwritten; revisions require assessment')
 c=duckdb.connect();c.execute("SET memory_limit='768MB'");c.execute("SET threads=2")
 c.read_parquet(str(pathlib.Path(private)/'*.parquet'),union_by_name=True).create_view('private')
 c.execute('CREATE TABLE geography(municipality VARCHAR, residence_uf VARCHAR)')
 c.executemany('INSERT INTO geography VALUES (?,?)',[(m,UF_CODES[m[:2]]) for m in municipalities])
 year_sql=','.join(str(y) for y in years)
 # Countrywide grouping uses residence UF, not the processing-file UF.
 sql=f"""SELECT p.family,p.year,g.residence_uf AS uf,p.residence AS municipality,
 CASE WHEN p.cid='' THEN 'UNSPECIFIED' ELSE p.cid END AS cid,
 CASE WHEN p.procedure='' THEN 'UNSPECIFIED' ELSE p.procedure END AS procedure,
 (floor(sum(p.records)/{width})*{width})::BIGINT AS records_lower,
 (floor(sum(p.records)/{width})*{width}+{width-1})::BIGINT AS records_upper,
 (floor(sum(p.quantity)/{width})*{width})::BIGINT AS quantity_lower,
 (floor(sum(p.quantity)/{width})*{width}+{width-1})::BIGINT AS quantity_upper
 FROM private p JOIN geography g ON p.residence=g.municipality
 WHERE p.family IN ('RD','PA','AM','DO') AND p.year IN ({year_sql})
 GROUP BY p.family,p.year,g.residence_uf,p.residence,p.cid,p.procedure
 HAVING sum(p.records)>={threshold}"""
 c.execute('COPY ('+sql+') TO ? (FORMAT PARQUET)',[str(root/'clinical.parquet')])
 excluded=c.execute(f"SELECT family,year,sum(records) records FROM private WHERE family IN ('RD','PA','AM','DO') AND year IN ({year_sql}) AND residence NOT IN (SELECT municipality FROM geography) GROUP BY family,year").fetchall()
 # Private diagnostic counts: never publish excluded residuals alongside cell outputs.
 (root/'private-geography-audit.json').write_text(json.dumps(excluded))
 meta={'release_ready':False,'status':'candidate_requires_reconciliation_privacy_performance_review','grain':['family','processing_file_year','residence_municipality','cid','procedure'],'years':years,'threshold_source_records':threshold,'interval_width':width,'not_people':True,'financial_values_exposed':False,'pa_am_overlap':'never_sum','suppressed_cells':'unknown_not_zero','residence_geography':'official5570municipalitycrosswalk; invalidorunknownexcluded','revision_policy':'immutablecandidate; newhistoricalreleaseblockeduntilrevisionriskreview','source_manifest_sha256':coverage['manifest_sha256'],'clinical_sha256':hashlib.sha256((root/'clinical.parquet').read_bytes()).hexdigest()}
 (root/'metadata.json').write_text(json.dumps(meta,indent=2));c.close();return meta
