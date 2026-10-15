"""Honest ecological hit status for a cleared, fixed-grain result only."""

def describe_hits(rows, *, release_cleared=False, evidence_complete=False):
    if not release_cleared:
        return {'status':'unavailable','hit_assessed':False,'reason':'Joint source and disclosure review has not cleared this result','missing':'Unknown, not zero'}
    if not evidence_complete:
        return {'status':'insufficient_evidence','hit_assessed':False,'reason':'Coverage or comparison evidence is incomplete','missing':'Unknown, not zero'}
    return {'status':'supported_ecological_hit' if rows else 'no_supported_hit',
            'hit_assessed':True,'hits':rows,
            'meaning':'Ecological research priorities: multiple fixed aggregate source-record proxies co-elevated in the same geography; not patient locations',
            'uncertainty':'Exploratory association with many competing causes; not linked symptoms in one person, diagnosis, prevalence or evidence of misdiagnosis',
            'negative_result':'No supported hit is not proof of no disease or unmet need'}


def describe_region_activity(region, *, activity_present=None, region_cleared=False,
                             evidence_complete=False, singleton_region=False):
    """A pre-reviewed coarse existence result, never a hidden-cell residual."""
    if singleton_region or not region_cleared:
        return {'status':'unavailable','activity_assessed':False,
                'reason':'This broader geography has not passed joint disclosure review',
                'missing':'Unknown, not zero'}
    if not evidence_complete or type(activity_present) is not bool:
        return {'status':'insufficient_evidence','activity_assessed':False,
                'reason':'Broader-region activity evidence is incomplete','missing':'Unknown, not zero'}
    return {'status':'recorded_regional_activity' if activity_present else 'no_recorded_regional_activity',
            'region':region,'activity_assessed':True,
            'town_level':'Not disclosed; no town presence or absence may be inferred from this response',
            'meaning':'Recorded disease-associated administrative care, not confirmed unique patients or a clinical cluster',
            'negative_result':'No recorded activity does not establish no disease or unmet need',
            'counts':'No exact hidden residual or patient count is supplied'}
