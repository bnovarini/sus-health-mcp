from sus_health_mcp.hit_status import describe_hits


def test_hit_not_hidden_when_cleared():
    r=describe_hits([{'geography':'test'}],release_cleared=True,evidence_complete=True)
    assert r['status']=='supported_ecological_hit' and r['hit_assessed']
    assert 'not linked symptoms' in r['uncertainty']


def test_no_hit_distinct_from_missing_evidence():
    assert describe_hits([],release_cleared=True,evidence_complete=True)['status']=='no_supported_hit'
    assert describe_hits([],release_cleared=True)['status']=='insufficient_evidence'
    assert describe_hits([{}],evidence_complete=True)['status']=='unavailable'


def test_regional_fallback_requires_independent_joint_clearance():
    from sus_health_mcp.hit_status import describe_region_activity
    assert describe_region_activity('SP',activity_present=True)['status']=='unavailable'
    assert describe_region_activity('SP',region_cleared=True)['status']=='insufficient_evidence'
    r=describe_region_activity('SP',activity_present=True,region_cleared=True,evidence_complete=True)
    assert r['status']=='recorded_regional_activity' and 'Not disclosed' in r['town_level']
    assert describe_region_activity('DF',activity_present=True,region_cleared=True,evidence_complete=True,singleton_region=True)['status']=='unavailable'
