from dataclasses import replace
import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_comparisons import COMPARISON_POLICIES
from ssm.model import Parameters,simulate,POLICIES

@pytest.mark.parametrize('equity,levy',[('B5','B11'),('B6','B12')])
def test_cash_flow_equivalence(equity,levy):
    p=Parameters(n=80,years=35)
    a,ha=simulate(p,COMPARISON_POLICIES[equity]);b,hb=simulate(p,COMPARISON_POLICIES[levy])
    for c in ['real_gdp','inflation','median_income','mvi_gdp','tax_gdp','coverage_shortfall']:
        np.testing.assert_allclose(a[c],b[c],rtol=1e-11,atol=1e-11)
    np.testing.assert_allclose(ha.income,hb.income,rtol=1e-11,atol=1e-11)
    assert b.usownership_share.max()==0 and a.usownership_share.max()>0
    assert b.pass_through_levy_gdp.iloc[-1]>0
    assert b.gini_wealth.iloc[-1]>a.gini_wealth.iloc[-1]

@pytest.mark.parametrize('code',['B0','B2','B5','B6','B7','B10','B11','B12','B13'])
def test_comparison_accounting(code):
    d,_=simulate(Parameters(n=40,years=12),COMPARISON_POLICIES[code])
    for c in ['accounting_residual','goods_residual','equity_residual']:
        assert d[c].abs().max()<1e-10
    np.testing.assert_allclose(d.total_recorded_tax_gdp,d.tax_gdp+d.pass_through_levy_gdp,atol=1e-12)

def test_matching_rejects_share_sales():
    with pytest.raises(ValueError):
        simulate(Parameters(sell_rate=.1),COMPARISON_POLICIES['B11'])

def test_zero_redistribution_matches_legal_ownership():
    p=Parameters(n=40,years=10,dilution_cap=0)
    a,_=simulate(p,COMPARISON_POLICIES['B5']);b,_=simulate(p,COMPARISON_POLICIES['B11'])
    np.testing.assert_allclose(a.gini_wealth,b.gini_wealth,atol=1e-12)
