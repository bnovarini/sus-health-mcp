"""PA-only acceleration preserving ordered addition for every source cell."""
import numpy as np,pandas as pd
from .build import HEADER

def aggregate(entry,df):
 keys=['residence','provider_municipality','facility','cid','procedure','competence']
 new=df.rename(columns={'PA_CMP':'competence','PA_MUNPCN':'residence','PA_UFMUN':'provider_municipality','PA_CODUNI':'facility','PA_CIDPRI':'cid','PA_PROC_ID':'procedure','PA_QTDAPR':'quantity','PA_VALAPR':'value'}).copy()
 for k in keys:new[k]=new[k].astype(str)
 if not new['competence'].str.fullmatch(r'20[0-9]{2}(0[1-9]|1[0-2])').all():raise ValueError('Invalid source competence')
 codes,_=pd.factorize(pd.MultiIndex.from_frame(new[keys]),sort=False)
 first=np.flatnonzero(~pd.Series(codes).duplicated().to_numpy());out=new.iloc[first][keys].reset_index(drop=True)
 out['records']=np.bincount(codes);out['quantity']=np.bincount(codes,weights=new['quantity'].to_numpy(dtype=float));out['value']=np.bincount(codes,weights=new['value'].to_numpy(dtype=float))
 out['system']=entry['system'];out['family']='PA';out['uf']=entry['uf'];out['year']=entry['year'];out['month']=entry['month'];out['deaths_or_non_sus']=0;out['sus_flag']=0;out['source_file']=entry['name']
 return out[HEADER]
