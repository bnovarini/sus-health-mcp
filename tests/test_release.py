import duckdb,pathlib
from sus_health_mcp.release import build

def test_fixed_suppression(tmp_path):
 private=tmp_path/'private';private.mkdir();out=tmp_path/'release';out.mkdir();c=duckdb.connect()
 c.execute("CREATE TABLE t AS SELECT 'DO' AS family,'AC' AS uf,2024 AS year,0 AS month,'120040' AS residence,'120040' AS provider_municipality,'' AS facility,'E752' AS cid,'' AS procedure,19 AS records,19 AS quantity,0 AS approved_value,0 AS deaths_or_non_sus,0 AS sus_flag,'f.dbc' AS source_file")
 c.execute("COPY t TO '"+str(private/'a.parquet')+"' (FORMAT PARQUET)");build(private,out)
 assert c.read_parquet(str(out/'signals.parquet')).count('*').fetchone()[0]==0
 c.execute('UPDATE t SET records=27');c.execute("COPY t TO '"+str(private/'a.parquet')+"' (FORMAT PARQUET)");build(private,out)
 row=c.read_parquet(str(out/'signals.parquet')).fetchone();assert row[-2:]==(20.0,29.0)
