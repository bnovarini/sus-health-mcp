"""Private assessment of one final municipality/proxy grain, never public by default.

No person-level privacy claim. Missing residence mass is unknown and raises the
reference upper bound. This module cannot grant source or publication readiness.
"""
from collections import defaultdict
from fractions import Fraction


def reduce_proxy_events(events, population, proxies, *, threshold=20, width=10):
    if threshold < 20 or width < 10:
        raise ValueError('Cannot weaken assessment parameters')
    if not population or any(type(v) is not int or v <= 0 for v in population.values()):
        raise ValueError('Positive integer population required')
    if not proxies or len(proxies) != len(set(proxies)):
        raise ValueError('Distinct fixed proxies required')
    counts = defaultdict(int)
    unknown = defaultdict(int)
    seen = set()
    for event in events:
        key = event['source_cell']
        if key in seen:
            raise ValueError('Duplicate source cell')
        seen.add(key)
        memberships = event['proxies']
        if len(memberships) > 1:
            raise ValueError('Overlapping proxies are not allowed')
        if not memberships:
            continue
        proxy = memberships[0]
        if proxy not in proxies:
            raise ValueError('Unknown proxy')
        n = event['activity']
        if type(n) is not int or n < 0:
            raise ValueError('Nonnegative integer event activity required')
        municipality = event['municipality']
        if municipality not in population:
            unknown[proxy] += n
        else:
            counts[municipality, proxy] += n
    rows = []
    for (municipality, proxy), n in sorted(counts.items()):
        if n >= threshold:
            low = n // width * width
            rows.append({'municipality': municipality, 'proxy': proxy, 'lower': low, 'upper': low + width - 1})
    return {'release_ready': False, 'rows': rows, 'private_unknown_residence_mass': dict(unknown),
            'threshold': threshold, 'width': width, 'grain': ['municipality', 'fixed_proxy'],
            'claim': 'event-level risk reduction only; not patient anonymity or privacy certification'}


def assess_elevation(candidate, population, proxies, *, minimum_proxies=2):
    """Private diagnostic only. This output must not be used to enable serving."""
    if minimum_proxies < 2 or minimum_proxies > len(proxies):
        raise ValueError('At least two fixed proxies required')
    by = {}
    for row in candidate['rows']:
        key = row['municipality'], row['proxy']
        if key in by or key[0] not in population or key[1] not in proxies:
            raise ValueError('Invalid or duplicate final-grain row')
        if row['lower'] < candidate['threshold'] or row['upper'] < row['lower']:
            raise ValueError('Invalid final-grain interval')
        by[key] = row
    total_population = sum(population.values())
    upper_totals = {proxy: sum(by[m, proxy]['upper'] if (m, proxy) in by else candidate['threshold'] - 1
                              for m in population) + candidate['private_unknown_residence_mass'].get(proxy, 0)
                    for proxy in proxies}
    result = []
    for municipality, pop in population.items():
        ratios = []
        for proxy in proxies:
            row = by.get((municipality, proxy))
            if row and upper_totals[proxy]:
                ratio = Fraction(row['lower'] * total_population, pop * upper_totals[proxy])
                if ratio >= Fraction(3, 2):
                    ratios.append((proxy, float(ratio)))
        if len(ratios) >= minimum_proxies:
            result.append({'municipality': municipality, 'elevated_proxies': ratios})
    return {'release_ready': False, 'private_assessment_only': True, 'rows': result,
            'meaning': 'aggregate proxy co-location, never the same people'}
