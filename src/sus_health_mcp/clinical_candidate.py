"""Strict read contract for approved hash-frozen municipalCID releases."""
import json,pathlib,hashlib,re,duckdb


def check_artifact(root):
    root=pathlib.Path(root)
    meta=json.loads((root/'clinical-metadata.json').read_text());p=root/'clinical.parquet'
    if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=meta['clinical_sha256']:
        raise ValueError('Clinical artifact integrity failed')
    return meta


def query(root,uf,year,family='RD',cid_prefix='',municipality='',limit=30):
    root=pathlib.Path(root)
    if uf not in 'AC AL AP AM BA CE ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split():
        raise ValueError('UF unavailable; DF excluded, not zero')
    meta=check_artifact(root)
    if type(year) is not int or year not in meta['years'] or family not in meta.get('approved_scopes',{}).get(str(year),('RD','PA','AM','DO')):
        raise ValueError('Only approved fixed clinical year/family scopes')
    if not re.fullmatch('[A-Z][0-9]{0,3}|',cid_prefix):
        raise ValueError('CID prefix invalid')
    if municipality and (not re.fullmatch('[0-9]{6}',municipality) or municipality.startswith('53')):
        raise ValueError('Municipality unavailable or invalid')
    if type(limit) is not int or not 1<=limit<=100:
        raise ValueError('Limit1-100')
    meta=check_artifact(root);p=root/'clinical.parquet'
    c=duckdb.connect();c.execute("SET memory_limit='384MB'");c.execute('SET threads=1')
    cur=c.execute("SELECT * FROM read_parquet(?) WHERE uf=? AND year=? AND family=? AND starts_with(cid,?) AND (?='' OR municipality=?) ORDER BY records_lower DESC,municipality,cid LIMIT ?",[str(p),uf,year,family,cid_prefix,municipality,municipality,limit+1]);rows=[dict(zip([r[0] for r in cur.description],v)) for v in cur.fetchall()];c.close()
    preview=meta.get('preview_scopes',{}).get(str(year)) if family=='DO' else None
    return {'vintage':preview,'preliminary':bool(preview),'rows':rows[:limit],'truncated':len(rows)>limit,'unit':'Source-record events, not people or prevalence','missing':'Suppressed, targeted-withheld, DF-excluded or absent; not zero and no upper bound implied','warnings':meta['warnings']+(preview['warnings'] if preview else []),'privacy':'No anonymity or sub20 secrecy guarantee. Public publisher files already expose municipality/code activity. No exact totals, residuals, quantities or new private aggregations returned.'}
