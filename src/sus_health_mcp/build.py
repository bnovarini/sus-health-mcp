"""Sequential manifest-driven ingestion. Raw identifiers never reach serving tables."""
from __future__ import annotations
import argparse,collections,csv,hashlib,json,pathlib,re,subprocess,time
import duckdb,dbfread,pyreaddbc
FAMILIES={'RD':('SIHSUS/200801_/Dados','sih'), 'PA':('SIASUS/200801_/Dados','sia'), 'AM':('SIASUS/200801_/Dados','medication'), 'DO':('SIM/CID10/DORES','mortality'), **{p:(f'CNES/200508_/Dados/{p}','capacity') for p in ['ST','LT','SR','HB']}}
BASE='ftp://ftp.datasus.gov.br/dissemin/publicos/'
UFS=set('AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split())

def inventory(prefix,start=2022,end=2026):
 directory,system=FAMILIES[prefix]
 r=subprocess.run(['curl','--fail','--max-time','60','--silent','--show-error',BASE+directory+'/'],capture_output=True,check=True,text=True)
 out=[]
 for line in r.stdout.splitlines():
  m=re.search(r'(\d+)\s+('+prefix+r'([A-Z]{2})(\d{4})([a-z]*)\.dbc)$',line,re.I)
  if not m or m[3] not in UFS:continue
  n,uf,code,part=m[2],m[3],m[4],m[5];year=int(code) if prefix=='DO' else 2000+int(code[:2]);month=None if prefix=='DO' else int(code[2:])
  if start<=year<=end:out.append(dict(system=system,prefix=prefix,uf=uf,year=year,month=month,part=part,name=n,size=int(m[1]),url=BASE+directory+'/'+n))
 return sorted(out,key=lambda x:(x['year'],x['month'] or 0,x['uf'],x['part']))

def download(entry,work):
 p=work/entry['name']
 for attempt in range(3):
  if p.exists() and p.stat().st_size==entry['size']:break
  res=subprocess.run(['curl','--fail','-C','-','--connect-timeout','20','--max-time','600','--silent','--show-error',entry['url'],'-o',str(p)])
  if res.returncode==0 and p.stat().st_size==entry['size']:break
  time.sleep(5)
 if not p.exists() or p.stat().st_size!=entry['size']:raise RuntimeError('Incomplete download: '+entry['name'])
 digest=hashlib.sha256(p.read_bytes()).hexdigest()
 return p,digest

def numeric(x):
 try:return float(x or 0)
 except (ValueError,TypeError):raise ValueError('Invalid numeric field')

def competence(entry,r):
 p=entry['prefix']
 if p=='RD':value=str(r['ANO_CMPT'])+str(r['MES_CMPT']).zfill(2)
 elif p=='PA':value=str(r['PA_CMP'])
 elif p=='AM':value=str(r['AP_CMP'])
 else:return ''
 if not re.fullmatch(r'20[0-9]{2}(0[1-9]|1[0-2])',value):raise ValueError('Invalid source competence: '+value)
 return value

def rows_for(entry,records):
 """Outputs coarse private per-file aggregates; all omitted source fields discarded."""
 groups=collections.defaultdict(lambda:[0,0.,0.,0,0]);p=entry['prefix'];year=entry['year']
 for r in records:
  if p=='RD':
   key=(str(r['MUNIC_RES']),str(r['MUNIC_MOV']),str(r['CNES']),str(r['DIAG_PRINC']),str(r['PROC_REA']),competence(entry,r))
   v=groups[key];v[0]+=1;v[1]+=numeric(r['IDENT']=='1');v[2]+=numeric(r['VAL_TOT']);v[3]+=int(r['MORTE']==1)
  elif p=='PA':
   key=(str(r['PA_MUNPCN']),str(r['PA_UFMUN']),str(r['PA_CODUNI']),str(r['PA_CIDPRI']),str(r['PA_PROC_ID']),competence(entry,r))
   v=groups[key];v[0]+=1;v[1]+=numeric(r['PA_QTDAPR']);v[2]+=numeric(r['PA_VALAPR'])
  elif p=='AM':
   key=(str(r['AP_MUNPCN']),str(r['AP_UFMUN']),str(r['AP_CODUNI']),str(r['AP_CIDPRI']),str(r['AP_PRIPAL']),competence(entry,r))
   v=groups[key];v[0]+=1;v[1]+=1;v[2]+=numeric(r['AP_VL_AP'])
  elif p=='DO':
   if str(r['TIPOBITO'])!='2':continue
   key=(str(r['CODMUNRES']),str(r['CODMUNOCOR']),'',str(r['CAUSABAS']),'','')
   v=groups[key];v[0]+=1;v[1]+=1
  elif p=='LT':
   key=(str(r['CODUFMUN']),str(r['CODUFMUN']),str(r['CNES']),'',str(r['TP_LEITO'])+':'+str(r['CODLEITO']),'')
   v=groups[key];v[0]+=1;v[1]+=numeric(r['QT_EXIST']);v[2]+=numeric(r['QT_SUS']);v[3]+=int(numeric(r['QT_NSUS']))
  elif p=='ST':
   key=(str(r['CODUFMUN']),str(r['CODUFMUN']),str(r['CNES']),'',str(r['TP_UNID']),'')
   v=groups[key];v[0]+=1;v[1]+=1;v[4]=int(str(r.get('VINC_SUS',''))=='1')
  elif p=='SR':
   key=(str(r['CODUFMUN']),str(r['CODUFMUN']),str(r['CNES']),'',str(r['SERV_ESP'])+':'+str(r['CLASS_SR']),'')
   v=groups[key];v[0]+=1;v[1]+=1;v[4]=int(str(r['AMB_SUS'])=='1' or str(r['HOSP_SUS'])=='1')
  elif p=='HB':
   key=(str(r['CODUFMUN']),str(r['CODUFMUN']),str(r['CNES']),'',str(r['SGRUPHAB']),'')
   v=groups[key];v[0]+=1;v[1]+=1;v[4]=int(str(r['VINC_SUS'])=='1')
  else:raise ValueError('Unverified mapping: '+p)
 for k,v in groups.items():yield [entry['system'],p,entry['uf'],year,entry['month'] or 0,*k[:5],*v,entry['name'],k[5]]

HEADER=['system','family','uf','year','month','residence','provider_municipality','facility','cid','procedure','records','quantity','value','deaths_or_non_sus','sus_flag','source_file','competence']
SELECTED={
'RD':['ANO_CMPT','MES_CMPT','MUNIC_RES','MUNIC_MOV','CNES','DIAG_PRINC','PROC_REA','IDENT','VAL_TOT','MORTE'],
'PA':['PA_CMP','PA_MUNPCN','PA_UFMUN','PA_CODUNI','PA_CIDPRI','PA_PROC_ID','PA_QTDAPR','PA_VALAPR'],
'AM':['AP_CMP','AP_MUNPCN','AP_UFMUN','AP_CODUNI','AP_CIDPRI','AP_PRIPAL','AP_VL_AP'],
'DO':['CODMUNRES','CODMUNOCOR','CAUSABAS','TIPOBITO'],
'LT':['CODUFMUN','CNES','TP_LEITO','CODLEITO','QT_EXIST','QT_SUS','QT_NSUS'],
'ST':['CODUFMUN','CNES','TP_UNID','VINC_SUS'],
'SR':['CODUFMUN','CNES','SERV_ESP','CLASS_SR','AMB_SUS','HOSP_SUS'],
'HB':['CODUFMUN','CNES','SGRUPHAB','NULEITOS','VINC_SUS']}

def ingest(entry,root):
 from .dbf import chunks
 work=root/'work';private=root/'private';work.mkdir(parents=True,exist_ok=True);private.mkdir(parents=True,exist_ok=True)
 out=private/(entry['name']+'.parquet');receipt=private/(entry['name']+'.json')
 if out.exists() and receipt.exists():return json.loads(receipt.read_text())
 p,digest=download(entry,work);dbf=p.with_suffix('.dbf');pyreaddbc.dbc2dbf(str(p),str(dbf))
 c=duckdb.connect(str(work/'scratch.duckdb'));c.execute("SET memory_limit='768MB'");c.execute("SET threads=1");c.execute("SET temp_directory='"+str(work/'tmp')+"'")
 c.execute('DROP TABLE IF EXISTS cube');source_count=0
 import pandas as pd
 for df in chunks(dbf,SELECTED[entry['prefix']]):
  source_count+=len(df)
  if entry['prefix']=='PA':
   from .pa_fast import aggregate
   part=aggregate(entry,df)
  else:part=pd.DataFrame(rows_for(entry,df.to_dict('records')),columns=HEADER)
  if len(part)==0:continue
  c.register('part',part)
  if c.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='cube'").fetchone()[0]==0:c.execute('CREATE TABLE cube AS SELECT * FROM part')
  else:c.execute('INSERT INTO cube SELECT * FROM part')
 groupcols=HEADER[:10]+['source_file','competence']
 if source_count:
  sql='SELECT '+','.join(groupcols)+',sum(records)::BIGINT records,sum(quantity)::DOUBLE quantity,sum(value)::DOUBLE approved_value,sum(deaths_or_non_sus)::BIGINT deaths_or_non_sus,max(sus_flag)::INTEGER sus_flag FROM cube GROUP BY '+','.join(groupcols)
  c.execute("COPY ("+sql+") TO ? (FORMAT PARQUET)",[str(out)])
 result={**entry,'sha256':digest,'source_record_count':source_count,'decoded_bytes':dbf.stat().st_size,'cube_bytes':out.stat().st_size if out.exists() else 0,'schema_version':2,'fetched_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())};receipt.write_text(json.dumps(result,indent=2));c.close()
 for x in [p,dbf,work/'scratch.duckdb']:
  if x.exists():x.unlink()
 print(json.dumps(result),flush=True);return result

def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default='data');a.add_argument('--manifest');a.add_argument('--inventory',action='store_true');a.add_argument('--families',default='RD,PA,AM,DO,ST,LT');a.add_argument('--uf');a.add_argument('--start',type=int,default=2022);a.add_argument('--end',type=int,default=2026);x=a.parse_args();root=pathlib.Path(x.root);root.mkdir(parents=True,exist_ok=True)
 entries=json.loads(pathlib.Path(x.manifest).read_text()) if x.manifest else [e for p in x.families.split(',') for e in inventory(p,x.start,x.end)]
 if x.uf:entries=[e for e in entries if e['uf']==x.uf]
 (root/'manifest.json').write_text(json.dumps(entries,indent=2))
 if x.inventory:print('files',len(entries),'bytes',sum(e['size'] for e in entries));return
 for entry in entries:ingest(entry,root)
if __name__=='__main__':main()
