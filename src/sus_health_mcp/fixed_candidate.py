"""Private frozen final-grain candidate, never a publication grant.

This replaces the unsafe flexible CID/procedure release route for assessment.
Clinical rows contain only one activity measure. No patient privacy claim.
"""
import hashlib
import json
import pathlib
import re
from .fixed_views import activity
from .published_hits import sanitize


def prepare(output, proxy_rows, hit_rows, *, source_manifest_sha256, years, proxies,
            contexts, reviewed_scopes=(), comparison_scope=None):
    if not isinstance(source_manifest_sha256, str) or not re.fullmatch("[a-f0-9]{64}", source_manifest_sha256):
        raise ValueError('Source manifest digest required')
    years = sorted(set(years))
    proxies = sorted(set(proxies))
    contexts = sorted(set(contexts))
    if not years or any(type(y) is not int or y not in (2022, 2023, 2024) for y in years):
        raise ValueError('Stable matched candidate years required')
    if not proxies or not contexts:
        raise ValueError('Fixed reviewed definitions required')
    rows = list(proxy_rows)
    hits = [sanitize(row) for row in hit_rows]
    from .fixed_disclosure import validate_joint
    validate_joint(rows, hits, reviewed_scopes, years=years, proxies=proxies, contexts=contexts)
    if any(c.endswith('_excluding_df') for c in contexts):
        if comparison_scope != 'Brazil excluding DF, not a national estimate':
            raise ValueError('Explicit DF-excluded comparison scope required')
        if any(r['uf']=='DF' for r in rows) or any(r['uf']=='DF' for r in hits) or any(scope.endswith(':DF') for scope in reviewed_scopes):
            raise ValueError('DF must be absent from the excluded comparison bundle')
    root = pathlib.Path(output)
    if root.exists():
        raise ValueError('Frozen candidate cannot be overwritten')
    root.mkdir(parents=True)
    artifacts = {}
    for name, data in [('fixed-proxies.json', {'rows': rows}),
                       ('ecological-hits.json', {'rows': hits, 'reviewed_scopes': list(reviewed_scopes)})]:
        content = (json.dumps(data, sort_keys=True, separators=(',', ':')) + '\n').encode()
        (root / name).write_bytes(content)
        artifacts[name] = hashlib.sha256(content).hexdigest()
    meta = {'release_ready': False, 'status': 'private_candidate_not_approved',
            'person_linkage': False, 'legacy_fine_lattice_approved': False,
            'approved_proxies': proxies, 'approved_hit_contexts': contexts,
            'proxy_years': years, 'source_manifest_sha256': source_manifest_sha256,
            'artifacts': artifacts, 'gates': {},
            'comparison_scope': comparison_scope,
            'meaning': 'Ecological event activity only, not clinical cases or patient anonymity'}
    (root / 'metadata.json').write_text(json.dumps(meta, indent=2) + '\n')
    return meta
