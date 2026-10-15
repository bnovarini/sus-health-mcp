import pathlib
from sus_health_mcp.build import rows_for,HEADER

def entry(p):return dict(prefix=p,system=p,uf='AC',year=2024,month=1,name='source.dbc')
def test_units():
 rows=list(rows_for(entry('RD'),[dict(ANO_CMPT='2024',MES_CMPT='01',MUNIC_RES='120040',MUNIC_MOV='120040',CNES='1',DIAG_PRINC='E752',PROC_REA='1',IDENT='5',VAL_TOT=10,MORTE=0)]))
 assert rows[0][10]==1
 assert rows[0][11]==0 # prolongation is an AIH, not a new admission
 assert rows[0][9]=='1'
 assert rows[0][8]=='E752'
def test_no_identifier_columns():
 assert not {'CPF','CNS','date_of_birth','NASC','CEP','AP_AUTORIZ'} & set(HEADER)
def test_approval_quantity_not_line_count():
 rows=list(rows_for(entry('PA'),[dict(PA_CMP="202401",PA_MUNPCN='120040',PA_UFMUN='120040',PA_CODUNI='1',PA_CIDPRI='',PA_PROC_ID='1',PA_QTDAPR=25,PA_VALAPR=8)]))
 assert rows[0][10]==1 and rows[0][11]==25


def test_source_competence_preserved():
 rows=list(rows_for(entry('PA'),[dict(PA_CMP='202312',PA_MUNPCN='120040',PA_UFMUN='120040',PA_CODUNI='1',PA_CIDPRI='',PA_PROC_ID='1',PA_QTDAPR=25,PA_VALAPR=8)]))
 assert rows[0][-1]=='202312' and rows[0][4]==1

def test_invalid_competence_rejected():
 import pytest
 from sus_health_mcp.build import competence
 with pytest.raises(ValueError):competence(entry('PA'),{'PA_CMP':'202413'})

def test_medication_records_not_doses():
 rows=list(rows_for(entry('AM'),[dict(AP_CMP='202401',AP_MUNPCN='120040',AP_UFMUN='120040',AP_CODUNI='1',AP_CIDPRI='E752',AP_PRIPAL='0604240023',AP_VL_AP=100)]))
 assert rows[0][10:12]==[1,1.0]
