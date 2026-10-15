"""Fixed annual geographic signals. No residual totals or intersecting filters exposed.

Small-cell threshold 20; surviving counts are intervals of width 10.
No demographics or arbitrary SQL. Quantities remain activity, never people.
This is risk reduction, not a formal anonymity or differential privacy guarantee.
"""
import argparse,pathlib,duckdb,json

def build(private,out):
 c=duckdb.connect();c.execute("SET memory_limit='768MB'")
 c.read_parquet(str(pathlib.Path(private)/'*.parquet'),union_by_name=True).create_view('private')
 c.execute("COPY (SELECT family,uf,year,residence municipality,cid, floor(sum(records)/10)*10 AS records_lower, floor(sum(records)/10)*10+9 AS records_upper FROM private WHERE family IN ('RD','PA','AM','DO') AND residence ~ '[0-9]{6}' AND cid <> '' GROUP BY family,uf,year,residence,cid HAVING sum(records)>=20) TO ? (FORMAT PARQUET)",[str(pathlib.Path(out)/'signals.parquet')])
 # Registered facility metadata only. No financial/personnel identifiers.
 c.execute("COPY (SELECT family,uf,year,month,provider_municipality municipality,facility,procedure,sum(quantity) quantity,sum(approved_value) sus_beds,max(sus_flag) sus_flag FROM private WHERE family IN ('ST','LT','SR','HB') GROUP BY ALL) TO ? (FORMAT PARQUET)",[str(pathlib.Path(out)/'capacity.parquet')])
 c.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('private');p.add_argument('output');a=p.parse_args();pathlib.Path(a.output).mkdir(parents=True,exist_ok=True);build(a.private,a.output)
