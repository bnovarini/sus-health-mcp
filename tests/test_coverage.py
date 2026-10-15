import pytest
from sus_health_mcp.coverage import coverage

def entry(name):return {'name':name,'size':12,'url':'ftp://source/'+name,'prefix':'PA','uf':'MG','year':2024,'month':1}
def receipt(e):return {**e,'sha256':'a'*64}
def test_split_part_required():
 a,b=entry('PAMG2401a.dbc'),entry('PAMG2401b.dbc');rows=coverage([a,b],{a['name']:receipt(a)})
 assert len(rows)==1 and not rows[0]['complete_for_inventory'] and rows[0]['missing_files']==[b['name']]
 rows=coverage([a,b],{a['name']:receipt(a),b['name']:receipt(b)})
 assert rows[0]['complete_for_inventory']
def test_mismatched_receipt_rejected():
 a=entry('x.dbc');r=receipt(a);r['size']=13
 with pytest.raises(ValueError,match='mismatch'):coverage([a],{a['name']:r})
def test_duplicate_manifest_rejected():
 a=entry('x.dbc')
 with pytest.raises(ValueError,match='Duplicate'):coverage([a,a],{})
