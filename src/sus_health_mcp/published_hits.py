"""Allowlisted ecological hit fields; no private ratios, exact totals or residuals."""
import re

def sanitize(row):
    allowed={'context','year','uf','municipality','proxies','meaning','uncertainty'}
    if set(row)-allowed:raise ValueError('Unreviewed hit fields; private statistics cannot be exposed')
    if not re.fullmatch(r'[0-9]{6}',row.get('municipality','')):raise ValueError('Invalid geography')
    if type(row.get('year')) is not int or not 2022<=row['year']<=2024:raise ValueError('Stable matched year required')
    if row.get('uf') not in set('AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split()):raise ValueError('Invalid UF')
    if not isinstance(row.get('context'),str) or not row['context']:raise ValueError('Context required')
    proxies=row.get('proxies',[])
    if not isinstance(proxies,list) or any(not isinstance(p,str) or not p for p in proxies) or len(proxies)<2 or len(proxies)!=len(set(proxies)):raise ValueError('Distinct multi-proxy hit required')
    # Never echo free-text artifact wording as patient-location inference.
    return {**{k:row[k] for k in ('context','year','uf','municipality','proxies')},
            'meaning':'Ecological research priority from aggregate source-record activity; not a patient location',
            'uncertainty':'Not unique people, linked symptoms, diagnosis, prevalence or calibrated diagnostic probability'}
