"""Private aggregate analysis helpers, not a public serving surface."""
from collections import defaultdict

NOTE = ('Source records, not people or prevalence. Residence and billing-provider '
        'views are not additive. Workup is nonspecific. PA/AM overlap is unknown; '
        'no person linkage or clinical eligibility claim.')


def classify(cid, procedure):
    """Fixed disjoint known-care categories. Drug association needs dated catalog."""
    if procedure == '0604540060' and cid == 'E851':
        return 'e851_tafamidis20_billing'
    if cid == 'E851':
        return 'e851_other_billing'
    if procedure == '0604540086':
        return 'tafamidis61_cardiac_context'
    if cid.startswith('E85'):
        return 'other_amyloidosis_billing'
    return None


def workup(procedure):
    return {'0211050083': 'electroneuromyography_nonspecific',
            '0201010291': 'nerve_biopsy_nonspecific'}.get(procedure)


def interval(n):
    if type(n) is not int or n < 0:
        raise ValueError('Nonnegative integer records required')
    return None if n < 20 else {'lower': n // 10 * 10, 'upper': n // 10 * 10 + 9}


def annual_view(rows, geography):
    """One fixed marginal at a time; no arbitrary cross-tab or small-cell return."""
    if geography not in ('residence', 'provider_municipality'):
        raise ValueError('Unsupported geography')
    counts = defaultdict(int)
    for r in rows:
        if str(r['residence']).startswith('53'):
            continue
        label = classify(r['cid'], r['procedure'])
        if label:
            n = r['records']
            interval(n)  # validation, not per-input suppression
            counts[r['year'], r[geography], label] += n
    return {'private_only': True, 'release_ready': False, 'notes': NOTE,
            'geography': geography,
            'rows': [dict(year=y, municipality=m, category=k, **v)
                     for (y, m, k), n in sorted(counts.items())
                     if (v := interval(n)) is not None]}


def cross_source_comparison(pa, am, rd):
    """Do not invent a unique-person union or sum overlapping PA/AM records."""
    return {'private_only': True, 'release_ready': False,
            'pa': pa, 'am': am, 'rd': rd,
            'combined_total': None, 'linkage': 'none',
            'notes': NOTE, 'source_gates': 'RD diagnosis and AM publisher checks unresolved'}


def dated_procedure(catalog, month, procedure):
    if len(month) != 6 or not month.isdigit() or not 1 <= int(month[4:]) <= 12:
        raise ValueError('YYYYMM required')
    matches = [r for r in catalog if r['month'] == month]
    if len(matches) != 1 or not matches[0].get('sha256'):
        return {'status': 'unverified_in_month', 'clinical_specificity': 'not established'}
    row = next((r for r in matches[0]['rows'] if r['CO_PROCEDIMENTO'] == procedure), None)
    return {'status': 'dated_name_verified' if row else 'unverified_in_month',
            'name': row['NO_PROCEDIMENTO'] if row else None,
            'source': matches[0]['source'],
            'clinical_specificity': 'not established by billing dictionary'}
