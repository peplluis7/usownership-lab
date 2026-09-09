import numpy as np
import pandas as pd
import pytest
from dataclasses import replace
from ssm.model import Parameters, POLICIES, simulate, normalize, levy, update_equity, sell_vested, frontier, contribution_scores, automation, dilution, gini

@pytest.mark.parametrize('policy',list(POLICIES))
def test_policy_accounting(policy):
    df,agents=simulate(Parameters(n=40,years=8),POLICIES[policy])
    assert df.accounting_residual.abs().max()<1e-9
    assert df.goods_residual.abs().max()<1e-9
    assert df.equity_residual.abs().max()<1e-10
    assert agents.real_cash.min()>=0
    assert (df.real_gdp<=df.capacity+1e-10).all()
    assert np.allclose(df.fiscal_issuance_gdp,df.net_seigniorage_gdp+df.burn_gdp,atol=1e-9)

def test_reproducibility():
    p=Parameters(n=40,years=12)
    x,a=simulate(p);y,b=simulate(p)
    pd.testing.assert_frame_equal(x,y);pd.testing.assert_frame_equal(a,b)

def test_exact_dilution():
    q=np.full((40,3),1/40);c=[];d=np.full(3,.02)
    for _ in range(50):q,c=update_equity(q,c,d,np.full((40,3),1/40))
    assert np.allclose(q.sum(0),(1.02)**-50)
    assert np.allclose(sum(c).sum(0),1-(1.02)**-50)

def test_secondary_trade_conserves_cash_and_equity():
    p=Parameters(n=40,vesting_years=0,sell_rate=.2)
    cash=np.full(40,1.0);o=np.full((40,3),.5/40);c=[o.copy()];buyers=np.arange(40)>35
    m,q,h,value=sell_vested(cash.copy(),o.copy(),[c[0].copy()],np.ones(3),buyers,p)
    assert np.isclose(m.sum(),cash.sum())
    assert np.allclose((q+sum(h)).sum(0),1)
    assert value>0 and m.min()>=0

def test_vesting_blocks_early_sales():
    p=Parameters(n=40,vesting_years=10,sell_rate=1)
    cash=np.ones(40);o=np.full((40,3),.5/40)
    m,q,c,v=sell_vested(cash.copy(),o.copy(),[o.copy()],np.ones(3),np.arange(40)>35,p)
    assert v==0

def test_protected_balances():
    p=Parameters(n=40)
    x=np.full(40,.1/40)
    assert np.all(levy(x,1,.1,p)==0)
    assert np.allclose(levy(x,1,.1,p,False),.1*x)

def test_scoring_mass_and_exclusion():
    c=np.ones(40);aff=np.full((40,3),1/3);act=np.ones(40);act[:8]=0
    for method in ['consumption','concave','contribution']:
        s=contribution_scores(c,aff,aff,aff,act,method)
        assert np.allclose(s.sum(0),1);assert np.all(s[:8]==0)

def test_endogenous_money_demand():
    p=Parameters(n=40,years=8)
    a,_=simulate(p);b,_=simulate(replace(p,alternative_return=.1))
    assert b.money_gdp.iloc[-1]<a.money_gdp.iloc[-1]

def test_frontier_identity_and_non_monotonicity():
    f=frontier(.6,4,.03,.02,.04)
    assert np.isclose(f['gross'],f['net']+f['burn'])
    assert frontier(.6,10,.03,.02,.4)['gross']<frontier(.6,10,.03,.02,.1)['gross']

def test_zero_automation_grants_none():
    p=Parameters(n=40,years=6,automation_max=0)
    a,_=simulate(p)
    assert a.usownership_share.max()==0

def test_mvi_sunset_not_hardcoded():
    p=Parameters(n=80,years=50)
    low,_=simulate(replace(p,income_floor=.15));high,_=simulate(replace(p,income_floor=.4))
    assert low.mvi_gdp.iloc[-1]<.01 and high.mvi_gdp.iloc[-1]>.1

def test_gini_extremes():
    assert abs(gini(np.ones(40)))<1e-12
    assert np.isclose(gini(np.r_[np.zeros(39),1.0]),39/40)

@pytest.mark.parametrize('kwargs',[{'n':2},{'money_gdp':0},{'demurrage':1.1},{'excluded_fraction':1},{'dilution_threshold':1}])
def test_invalid_inputs(kwargs):
    with pytest.raises(ValueError):simulate(replace(Parameters(),**kwargs))


def test_cached_quantile_equivalence():
    # The speed optimisation relies only on positive-scalar homogeneity.
    rng=np.random.default_rng(91)
    values=np.exp(rng.normal(size=400))
    for scale in [0.15,0.4,1.0,100.0]:
        assert np.isclose(np.quantile(scale*values,.1),scale*np.quantile(values,.1),rtol=1e-14)


def test_calendar_horizon_mapping():
    p=Parameters(n=40,years=10,start_year=2027)
    d,_=simulate(p)
    assert int(d.iloc[-1].year)==10
    assert int(d.iloc[-1].calendar_year)==2037
    d50,_=simulate(replace(p,years=50))
    assert int(d50.iloc[-1].calendar_year)==2077


def test_paper_central_release_regression():
    # Frozen central medium-AI values reported by the paper. These are
    # mechanism-study regression targets, not empirical calibration targets.
    expected = {
        'B2': {'mvi_gdp': 0.190278, 'tax_gdp': 0.370401, 'usownership_share': 0.0},
        'B5': {'mvi_gdp': 0.105694, 'tax_gdp': 0.285329, 'usownership_share': 0.296692},
        'B6': {'mvi_gdp': 0.101641, 'tax_gdp': 0.271269, 'usownership_share': 0.296692},
    }
    for code, target in expected.items():
        d,_ = simulate(Parameters(n=400, years=50, start_year=2027), POLICIES[code])
        last = d.iloc[-1]
        assert int(last.calendar_year) == 2077
        for key, value in target.items():
            assert np.isclose(last[key], value, atol=7e-7)
