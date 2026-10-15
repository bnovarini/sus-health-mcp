"""Validate the complete fixed release together before any clinical tool serves it.

Necessary record-cell checks only. Does not certify patient anonymity, external
constraint safety or clinical validity. Gate review remains independent.
"""
import re
from .fixed_views import activity
from .published_hits import sanitize

UF_CODES = dict(zip('11 12 13 14 15 16 17 21 22 23 24 25 26 27 28 29 31 32 33 35 41 42 43 50 51 52 53'.split(),
                    'RO AC AM RR PA AP TO MA PI CE RN PB PE AL SE BA MG ES RJ SP PR SC RS MS MT GO DF'.split()))
# IBGE: 41 PR, 42 SC, 43 RS.
UF_CODES.update({'41': 'PR', '42': 'SC', '43': 'RS'})


def validate_joint(proxy_rows, hit_rows, reviewed_scopes, *, years, proxies, contexts):
    rows = list(proxy_rows)
    for row in rows:
        if set(row) != {'year', 'municipality', 'uf', 'proxy', 'lower', 'upper'}:
            raise ValueError('Extra fields in final-grain activity')
        m = row['municipality']
        if not isinstance(m, str) or not re.fullmatch('[0-9]{6}', m) or UF_CODES.get(m[:2]) != row['uf']:
            raise ValueError('Invalid or mismatched residence geography')
        if type(row['year']) is not int or row['year'] not in years or row['proxy'] not in proxies:
            raise ValueError('Unreviewed candidate scope')
    for proxy in proxies:
        activity(rows, proxy, years)
    for scope in reviewed_scopes:
        parts = scope.split(':')
        if len(parts) != 3 or parts[0] not in contexts or not parts[1].isdigit() or int(parts[1]) not in years or parts[2] not in UF_CODES.values():
            raise ValueError('Unreviewed hit scope')
    visible = {(r['year'], r['municipality'], r['uf'], r['proxy']) for r in rows}
    hit_keys = set()
    hit_rows = list(hit_rows)
    keys = [(r.get('context'),r.get('year'),r.get('uf'),r.get('municipality')) for r in hit_rows]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate fixed hit')
    for raw in hit_rows:
        row = sanitize(raw)
        key = (row['context'], row['year'], row['uf'], row['municipality'])
        if key in hit_keys:
            raise ValueError('Duplicate fixed hit')
        hit_keys.add(key)
        if row['year'] not in years or row['context'] not in contexts or not set(row['proxies']) <= set(proxies):
            raise ValueError('Unreviewed hit definition')
        if any((row['year'], row['municipality'], row['uf'], proxy) not in visible for proxy in row['proxies']):
            raise ValueError('Hit references a suppressed, absent or mismatched proxy cell')
        if f"{row['context']}:{row['year']}:{row['uf']}" not in reviewed_scopes:
            raise ValueError('Hit scope lacks joint review')
    return True
