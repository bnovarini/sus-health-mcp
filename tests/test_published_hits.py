import pytest
from sus_health_mcp.published_hits import sanitize


def hit():return {'context':'test','year':2024,'uf':'RO','municipality':'110001','proxies':['a','b']}


def test_ratios_and_residuals_never_implicitly_published():
    assert sanitize(hit())['proxies']==['a','b']
    for k in ('private_unknown_residence_mass','ratio','baseline_upper','exact_total','patient_count'):
        with pytest.raises(ValueError):sanitize({**hit(),k:1})


def test_no_single_proxy_hit():
    with pytest.raises(ValueError):sanitize({**hit(),'proxies':['a']})


def test_invalid_or_unmatched_hit_period_fails():
 for change in [{'year':2025},{'year':'2024'},{'uf':'XX'},{'proxies':['a',2]}]:
  with pytest.raises(ValueError):sanitize({**hit(),**change})
