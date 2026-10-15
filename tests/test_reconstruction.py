import pytest
from sus_health_mcp.reconstruction import propagate_total,intersect_revision


def test_exact_external_total_can_reconstruct_a_suppressed_cell():
    assert propagate_total([(20,29),(0,19)],20)==[[20,20],[0,0]]


def test_external_total_narrows_all_tools_jointly():
    assert propagate_total([(20,29),(30,39)],55)==[[20,25],[30,35]]


def test_revision_combination_can_reconstruct_one_event():
    assert intersect_revision((20,29),(30,39),1)=={'old':[29,29],'new':[30,30]}


def test_inconsistent_totals_not_silently_accepted():
    with pytest.raises(ValueError):propagate_total([(20,29)],19)
    with pytest.raises(ValueError):intersect_revision((20,29),(30,39),0)
