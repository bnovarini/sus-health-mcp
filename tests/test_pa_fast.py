import pandas as pd,numpy as np,pytest
from sus_health_mcp.pa_fast import aggregate
from sus_health_mcp.build import rows_for,HEADER

def test_fast_bitwise_equivalence():
 e={'prefix':'PA','system':'sia','uf':'SP','year':2024,'month':1,'name':'fixture.dbc'}
 rng=np.random.default_rng(5);rows=[]
 for i in range(5000):
  rows.append(dict(PA_CMP='202312' if i%7 else '202401',PA_MUNPCN='355030',PA_UFMUN='355030',PA_CODUNI=str(i%3),PA_CIDPRI='E752' if i%2 else '',PA_PROC_ID=str(i%4),PA_QTDAPR=int(rng.integers(0,20)),PA_VALAPR=int(rng.integers(0,100000))/100))
 df=pd.DataFrame(rows);old=pd.DataFrame(rows_for(e,rows),columns=HEADER);new=aggregate(e,df)
 key=['residence','provider_municipality','facility','cid','procedure','competence'];old=old.sort_values(key).reset_index(drop=True);new=new.sort_values(key).reset_index(drop=True)
 assert old[key].equals(new[key]);assert np.array_equal(old[['records','quantity','value']].to_numpy(),new[['records','quantity','value']].to_numpy())

def test_fast_invalid_competence():
 e={'prefix':'PA','system':'sia','uf':'SP','year':2024,'month':1,'name':'fixture.dbc'}
 r=dict(PA_CMP='202413',PA_MUNPCN='355030',PA_UFMUN='355030',PA_CODUNI='1',PA_CIDPRI='',PA_PROC_ID='1',PA_QTDAPR=0,PA_VALAPR=0)
 with pytest.raises(ValueError):aggregate(e,pd.DataFrame([r]))
