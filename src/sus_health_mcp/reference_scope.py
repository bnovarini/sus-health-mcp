"""Explicit excluded-region reference, not a private withheld-mass estimate."""
from .signals import rank_pockets


def excluding_df(rows, population, proxies):
    """Both numerator and reference exclude DF; no nationwide interpretation.

    Input rows are fixed public intervals. Caller still verifies source coverage,
    population vintage, definitions, final-grain suppression and unknown mass.
    """
    pop = {m:n for m,n in population.items() if not m.startswith('53')}
    kept = [r for r in rows if not r['municipality'].startswith('53')]
    if any(r['municipality'] not in pop for r in kept):
        raise ValueError('Row outside reviewed reference geography')
    hits = rank_pockets(kept,pop,proxies,coverage_complete=True,
                       suppression_grain_matches_signal=True)
    return {'comparison_scope':'Brazil excluding DF, not a national estimate',
            'rows':kept,'population':pop,'hits':hits,
            'withheld':'DF not assessed; never infer absence or state presence'}
