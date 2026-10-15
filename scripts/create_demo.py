"""Create one fictional CNES row for a local setup smoke test. No real health data."""
import hashlib, json
from pathlib import Path
import duckdb
root = Path('data/demo')
root.mkdir(parents=True, exist_ok=True)
p = root / 'capacity.parquet'
c = duckdb.connect()
c.execute("CREATE TABLE demo AS SELECT 'LT' AS family, 'SP' AS uf, 2024 AS year, 1 AS month, '350000' AS municipality, 'DEMO' AS facility, '1:01' AS procedure, 10 AS quantity, 8 AS sus_beds, 1 AS sus_flag")
c.execute('COPY demo TO ? (FORMAT PARQUET)', [str(p)])
c.close()
meta = {
    'release_id': 'synthetic-demo-not-real-data',
    'deployment_scope': 'synthetic-registry-demo',
    'clinical_queries_enabled': False,
    'person_linkage': False,
    'capacity_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
    'registry_years': [2024], 'registry_partial_years': {},
    'registry_warnings': ['Fictional setup fixture. Not DATASUS data.'],
    'coverage': [], 'gaps': [], 'clinical_status': 'disabled',
    'publisher_periods': [{'family': 'LT', 'year': 2024, 'month': 1,
                           'uf': 'SP', 'status': 'passed',
                           'evidence': ['synthetic fixture, not publisher verification']}],
}
(root / 'metadata.json').write_text(json.dumps(meta, indent=2))
print('Synthetic fixture created in data/demo. Not real healthcare data.')
