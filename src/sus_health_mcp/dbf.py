"""Read only selected DBF columns in bounded chunks; never load whole rows."""
import mmap,struct
import numpy as np
import pandas as pd

def chunks(path,columns,size=50000):
 with open(path,'rb') as f:
  b=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);count=struct.unpack_from('<I',b,4)[0];header,record=struct.unpack_from('<HH',b,8);off=1;fields={}
  for p in range(32,header-1,32):
   if b[p]==13:break
   name=b[p:p+11].split(b'\0')[0].decode();length=b[p+16];fields[name]=(off,length,chr(b[p+11]));off+=length
  missing=set(columns)-set(fields)
  if missing:raise ValueError('Missing source columns: '+str(missing))
  for start in range(0,count,size):
   n=min(size,count-start);data={}
   deleted=np.ndarray((n,),dtype='S1',buffer=b,offset=header+start*record,strides=(record,)).copy()
   for col in columns:
    off,length,typ=fields[col];a=np.ndarray((n,),dtype=f'S{length}',buffer=b,offset=header+start*record+off,strides=(record,)).copy()
    s=pd.Series(a).str.decode('latin1').str.strip()
    data[col]=pd.to_numeric(s.replace('',0),errors='raise') if typ in 'NF' else s
   df=pd.DataFrame(data);yield df.loc[deleted!=b'*']
  b.close()
