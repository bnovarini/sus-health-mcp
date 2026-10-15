"""Fail-closed release gate validation independent of a loose readiness boolean."""
REQUIRED_GATES=('source_inventory','publisher_reconciliation','clinical_definitions','temporal_semantics','privacy_joint_outputs','privacy_revisions','residence_coverage','performance','tool_contracts')

def validate(metadata):
    if metadata.get('release_ready') is not True:
        raise ValueError('Verified serving release is not ready')
    gates=metadata.get('gates',{})
    if not isinstance(gates,dict):raise ValueError('Invalid serving gate record')
    missing=[key for key in REQUIRED_GATES if not isinstance(gates.get(key),dict) or gates[key].get('status')!='passed' or not gates[key].get('evidence')]
    if missing:raise ValueError('Serving gates not verified: '+', '.join(missing))
    if not metadata.get('release_id') or not metadata.get('artifacts'):
        raise ValueError('Frozen release identity and artifacts required')
    if metadata.get('person_linkage') is not False:
        raise ValueError('No-person-linkage scope required')
    return True


def validate_artifacts(metadata, root):
    """Check frozen bytes before use. Gate records alone cannot assert integrity."""
    import hashlib
    import pathlib
    import re
    validate(metadata)
    root = pathlib.Path(root).resolve()
    artifacts = metadata['artifacts']
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError('Artifact digest manifest required')
    known = {'signals.parquet', 'capacity.parquet', 'fixed-proxies.json',
             'ecological-hits.json', 'protocol-associations.json'}
    if set(artifacts) - known:
        raise ValueError('Unreviewed release artifact')
    required = {'capacity.parquet', 'fixed-proxies.json', 'ecological-hits.json', 'protocol-associations.json'}
    if metadata.get('legacy_fine_lattice_approved') is True:
        required.add('signals.parquet')
    if not required.issubset(artifacts):
        raise ValueError('Tool contract artifacts missing')
    for name, sha in artifacts.items():
        p = root / name
        if not isinstance(sha, str) or not re.fullmatch('[a-f0-9]{64}', sha):
            raise ValueError('Invalid artifact digest')
        if p.is_symlink() or not p.is_file() or p.resolve().parent != root:
            raise ValueError('Missing or unsafe release artifact')
        h = hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda: f.read(1048576), b''):
                h.update(b)
        if h.hexdigest() != sha:
            raise ValueError('Frozen artifact checksum mismatch')
    # Checksums prove frozen bytes, not safe contents. Validate all clinical
    # artifacts jointly even when the requested tool is only one filtered view.
    import json
    from .fixed_disclosure import validate_joint
    proxy_data = json.loads((root / 'fixed-proxies.json').read_text())
    hit_data = json.loads((root / 'ecological-hits.json').read_text())
    validate_joint(proxy_data['rows'], hit_data['rows'], hit_data.get('reviewed_scopes', []),
                   years=metadata.get('proxy_years', []),
                   proxies=metadata.get('approved_proxies', []),
                   contexts=metadata.get('approved_hit_contexts', []))
    if any(c.endswith('_excluding_df') for c in metadata.get('approved_hit_contexts', [])):
        if metadata.get('comparison_scope') != 'Brazil excluding DF, not a national estimate':
            raise ValueError('Explicit DF-excluded comparison scope required')
        if any(r['uf']=='DF' for r in proxy_data['rows']) or any(r['uf']=='DF' for r in hit_data['rows']) or any(s.endswith(':DF') for s in hit_data.get('reviewed_scopes', [])):
            raise ValueError('DF present in excluded comparison bundle')
    return True
