import pytest
from sus_health_mcp.period_gates import require_period


def test_unverified_period_not_zero():
 m={'publisher_periods':[{'family':'SR','year':2024,'month':7,'uf':'all27','status':'passed','evidence':['fixture']} ]}
 assert require_period(m,'SR',2024,7,'AP')
 with pytest.raises(ValueError):require_period(m,'SR',2024,8,'AP')
 with pytest.raises(ValueError):require_period(m,'LT',2024,7,'AP')


def test_one_month_cannot_clear_annual_or_one_uf_national():
 m={'publisher_periods':[{'family':'PA','year':2024,'month':1,'uf':'AC','status':'passed','evidence':['fixture']}]}
 with pytest.raises(ValueError):require_period(m,'PA',2024,None,'AC')
 with pytest.raises(ValueError):require_period(m,'PA',2024,1,None)
 assert require_period(m,'PA',2024,1,'AC')
