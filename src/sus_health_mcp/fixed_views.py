"""Post-processing of reviewed final-grain releases, never raw clinical cubes."""

def activity(rows, proxy, years, municipality='', uf=''):
    selected=[];seen=set()
    for row in rows:
        key=(row['year'],row['municipality'],row['proxy'])
        if key in seen:raise ValueError('Duplicate final-grain cell')
        seen.add(key)
        if row['proxy']!=proxy or row['year'] not in years:continue
        if municipality and row['municipality']!=municipality:continue
        if uf and row['uf']!=uf:continue
        if type(row['lower']) is not int or type(row['upper']) is not int or row['lower']<20 or row['lower']%10 or row['upper']!=row['lower']+9:raise ValueError('Invalid fixed-width final-grain interval')
        selected.append({k:row[k] for k in ['year','municipality','uf','proxy','lower','upper']})
    return {'rows':sorted(selected,key=lambda r:(r['year'],r['municipality'])),'missing':'suppressed, unknown or unavailable; never zero','unit':'source-record events, not people, doses or prevalence','scope':'fixed final-grain published cells only','meaning':'ecological association only, not the same individuals or evidence of misdiagnosis'}
