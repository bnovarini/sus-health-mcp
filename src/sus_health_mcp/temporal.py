"""Monthly billing compatibility and dated associations, never eligibility."""
import re

def billing_association(catalog, disease, competence, procedure):
    if not re.fullmatch(r'20[0-9]{2}(0[1-9]|1[0-2])',competence):
        raise ValueError('Verified source competence required, not processing-file year')
    if not re.fullmatch(r'[0-9]{10}',procedure):raise ValueError('Ten-digit procedure required')
    rows=[r for r in catalog if r['disease']==disease and r['month']==competence and r['procedure']==procedure]
    if len(rows)>1:raise ValueError('Duplicate monthly association')
    if not rows:
        return {'status':'not_verified_in_monthly_catalog','competence':competence,
                'meaning':'Not proof of no treatment, no disease, or ineligibility'}
    row=rows[0]
    if not row.get('source') or not row.get('source_sha256'):
        raise ValueError('Monthly publisher provenance missing')
    return {'status':'monthly_billing_compatibility_verified','competence':competence,
            'procedure':procedure,'procedure_name':row['name'],'compatible_cids':row['compatible_cids'],
            'source':row['source'],'meaning':'Administrative dictionary compatibility only, not verified protocol applicability, confirmed unique patients or clinical eligibility'}


def dated_protocol_association(periods, disease, competence):
    """A month overlapping a protocol transition cannot pick one protocol.

    Dates are verified effective publication dates, not order signature dates.
    Protocol associations supply context only, never patient eligibility.
    """
    import calendar
    from datetime import date
    if not re.fullmatch(r'20[0-9]{2}(0[1-9]|1[0-2])', competence):
        raise ValueError('Exact monthly competence required')
    year, month = int(competence[:4]), int(competence[4:])
    start = date(year, month, 1)
    end = date(year, month, calendar.monthrange(year, month)[1])
    matches = []
    for row in periods:
        if row['disease'] != disease:
            continue
        if not row.get('publication_source') or not row.get('effective_from'):
            raise ValueError('Verified publication provenance required')
        a = date.fromisoformat(row['effective_from'])
        b = date.fromisoformat(row['effective_until']) if row.get('effective_until') else date.max
        if row.get('verified_through'):
            b = min(b, date.fromisoformat(row['verified_through']))
        if b < a:
            raise ValueError('Invalid protocol period')
        if a <= end and b >= start:
            matches.append((row, a, b))
    matches.sort(key=lambda item:item[1])
    for previous,current in zip(matches,matches[1:]):
        if current[1]<=previous[2]:
            raise ValueError('Overlapping protocol periods require source review')
    note = 'Protocol context only; no individual diagnosis, treatment or eligibility inference'
    if not matches:
        return {'status': 'protocol_period_unverified', 'competence': competence, 'meaning': note}
    if len(matches) != 1 or matches[0][1] > start or matches[0][2] < end:
        return {'status': 'monthly_protocol_transition', 'competence': competence,
                'meaning': 'Monthly competence crosses a verified protocol boundary; no single protocol selected. ' + note}
    row = matches[0][0]
    return {'status': 'dated_protocol_association_verified', 'competence': competence,
            'order': row['order'], 'publication_source': row['publication_source'], 'meaning': note}
