"""An explicitly closed, discrete-time monetary/ownership transition laboratory.

Not an estimated DSGE model. Every stock and flow is recorded. Payment accounts
are sovereign money, firms retain earnings to invest, and there is no bank
credit, government debt, external sector, or endogenous asset valuation.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from typing import Literal
import numpy as np
import pandas as pd
from scipy.optimize import brentq

@dataclass(frozen=True)
class Parameters:
    n: int = 400
    years: int = 50
    start_year: int = 2027
    seed: int = 240712
    midpoint: float = 20.0
    speed: float = 0.14
    automation_max: float = 0.90
    ai_gain: float = 0.90
    trend_tfp: float = 0.01
    capital_elasticity: float = 0.40
    depreciation: float = 0.06
    capital_output: float = 3.0
    investment_base: float = 0.22
    investment_ai: float = 0.025
    dilution_investment_penalty: float = 0.60
    dilution_cap: float = 0.02
    dilution_threshold: float = 0.25
    money_gdp: float = 0.60
    liquidity_elasticity: float = 4.0
    liquidity_heterogeneity: float = 0.30
    expected_inflation_adjustment: float = 0.30
    alternative_return: float = 0.02
    reference_alternative_return: float = 0.02
    fixed_money_growth: float = 0.04
    forecast_bias: float = 0.0
    numerical_inflation_limit: float = 100.0
    numerical_price_limit: float = 1e15
    inflation_target: float = 0.02
    controller_gain: float = 0.25
    min_money_growth: float = -0.15
    max_money_growth: float = 0.20
    max_deflation: float = 0.02
    government_share: float = 0.22
    income_floor: float = 0.25
    floor_quantile: float = 0.10
    floor_indexation: float = 1.0
    fixed_tax: float = 0.30
    max_tax: float = 0.85
    demurrage: float = 0.04
    max_demurrage: float = 0.15
    demurrage_feedback: float = 0.30
    protected_balance: float = 0.12
    upper_bracket: float = 1.0
    excluded_fraction: float = 0.0
    sell_rate: float = 0.0
    vesting_years: int = 10
    transfer_retained_core: float = 0.20
    resource_cap: float = 1.30
    resource_growth: float = 0.035
    resource_intensity: float = 0.15
    shock_year: int = 0
    shock_size: float = 0.0
    bot_share: float = 0.0
    money_preference_shock_year: int = 0
    money_preference_shock: float = 0.0

@dataclass(frozen=True)
class Policy:
    name: str
    transfers: Literal['none','targeted','universal'] = 'universal'
    usownership: bool = False
    scoring: str = 'contribution'
    monetary: Literal['adaptive','fixed','fiscal'] = 'adaptive'
    demurrage: bool = False
    progressive: bool = True
    tax_override: float | None = None
    wage_tax_multiplier: float = 1.0
    capital_tax_multiplier: float = 1.0
    # Matching uses a shadow entitlement register, not issued legal equity.
    payout_mode: Literal['equity', 'matched_levy'] = 'equity'

POLICIES = {
    'B0': Policy('B0: targeted tax-transfer comparator', transfers='targeted'),
    'B1': Policy('B1: no household transfer', transfers='none'),
    'B2': Policy('B2: universal transfer + residual tax'),
    'B3': Policy('B3: fiscal-dominant monetary transfer', monetary='fiscal'),
    'B4': Policy('B4: fiscal dominance + burn', monetary='fiscal', demurrage=True),
    'B5': Policy('B5: usownership + residual tax', usownership=True),
    'B6': Policy('B6: SSM hybrid', usownership=True, demurrage=True),
    'B7': Policy('B7: equal citizen-equity comparator', usownership=True, scoring='equal'),
    'B8': Policy('B8: fixed money growth + usownership', usownership=True, demurrage=True, monetary='fixed'),
    'B9': Policy('B9: no-tax SSM stress', usownership=True, demurrage=True, monetary='fiscal', tax_override=0.0),
}
AI_SCENARIOS = {
    'slow': dict(midpoint=40.0, speed=0.08, automation_max=0.65, ai_gain=0.35),
    'medium': dict(midpoint=20.0, speed=0.14, automation_max=0.90, ai_gain=0.90),
    'fast': dict(midpoint=10.0, speed=0.30, automation_max=0.98, ai_gain=1.60),
}

def gini(x: np.ndarray) -> float:
    """Equal-agent-weight Gini; nonnegative levels required."""
    x = np.sort(np.asarray(x, float))
    if np.min(x) < -1e-10:
        raise ValueError('Gini is defined here only for nonnegative observations.')
    total = x.sum()
    return float(2 * np.dot(np.arange(1, len(x)+1), x) / (len(x)*total) - (len(x)+1)/len(x)) if total > 0 else 0.0

def normalize(x: np.ndarray, axis: int = 0) -> np.ndarray:
    d = x.sum(axis=axis, keepdims=True)
    if np.any(d <= 0):
        raise ValueError('A contribution or ownership column has zero mass.')
    return x/d

def automation(t: int, p: Parameters) -> np.ndarray:
    l0 = 1/(1+np.exp(p.speed*p.midpoint))
    lt = 1/(1+np.exp(-p.speed*(t-p.midpoint)))
    a = p.automation_max*(lt-l0)/(1-l0)
    return np.clip(a*np.array([1.0, 0.9, 0.8]), 0, 0.999)

def dilution(a: np.ndarray, p: Parameters) -> np.ndarray:
    return p.dilution_cap*np.maximum((a-p.dilution_threshold)/(1-p.dilution_threshold),0)

def levy(cash: np.ndarray, nominal_reference: float, rate: float,
         p: Parameters, progressive: bool = True) -> np.ndarray:
    if not progressive:
        return rate*cash
    z = nominal_reference/p.n
    lower = np.maximum(cash-p.protected_balance*z,0)
    upper = np.maximum(cash-p.upper_bracket*z,0)
    # Marginal rate = rate/2 above the exemption, rate above upper bracket.
    return 0.5*rate*(lower+upper)

def update_equity(ordinary: np.ndarray, cohorts: list[np.ndarray],
                  delta: np.ndarray, scores: np.ndarray) -> tuple[np.ndarray,list[np.ndarray]]:
    scale = 1+delta
    ordinary = ordinary/scale
    cohorts = [c/scale for c in cohorts]
    cohorts.append(scores*delta/scale)
    return ordinary, cohorts

def contribution_scores(consumption: np.ndarray, affinity: np.ndarray,
                        engagement: np.ndarray, creation: np.ndarray,
                        active: np.ndarray, scoring: str, bot_share: float = 0) -> np.ndarray:
    n, j = affinity.shape
    if scoring == 'equal':
        return np.full((n,j),1/n)
    usage = np.maximum(consumption[:,None]*affinity,0)
    usage /= np.maximum(np.median(usage,axis=0,keepdims=True),1e-15)
    if scoring == 'consumption':
        raw = usage
    elif scoring == 'concave':
        raw = np.sqrt(usage)
    elif scoring == 'contribution':
        # Explicit normative weights, not estimates of marginal economic value.
        raw = 0.35*np.sqrt(np.minimum(usage,25))+0.25*engagement+0.40*creation
    else:
        raise ValueError(f'Unknown scoring rule {scoring}')
    raw *= active[:,None]
    s = normalize(raw)
    if bot_share > 0:
        # One synthetic attacker is counted once in the identity set but captures
        # a specified share of score mass. This tests measurement failure.
        s = (1-bot_share)*s
        s[-1,:] += bot_share
    return s

def sell_vested(cash: np.ndarray, ordinary: np.ndarray, cohorts: list[np.ndarray],
                prices: np.ndarray, buyers: np.ndarray, p: Parameters) -> tuple[np.ndarray,np.ndarray,list[np.ndarray],float]:
    """Cash-settled secondary sales; no money or aggregate equity is destroyed."""
    eligible = len(cohorts)-p.vesting_years
    if p.sell_rate <= 0 or eligible <= 0:
        return cash, ordinary, cohorts, 0.0
    sellers = ~buyers
    eligible_holdings = sum(cohorts[:eligible],np.zeros_like(ordinary))
    offer = eligible_holdings*p.sell_rate*(1-p.transfer_retained_core)*sellers[:,None]
    value = offer @ prices
    budget = 0.5*cash*buyers
    total = min(float(value.sum()),float(budget.sum()))
    if total <= 0:
        return cash, ordinary, cohorts, 0.0
    ratio = total/value.sum()
    sold = offer*ratio
    buyweights = budget/budget.sum()
    cash = cash + sold@prices - total*buyweights
    ordinary = ordinary + buyweights[:,None]*sold.sum(axis=0)[None,:]
    for k in range(eligible):
        cohorts[k] = cohorts[k]*(1-p.sell_rate*(1-p.transfer_retained_core)*sellers[:,None]*ratio)
    return cash,ordinary,cohorts,total

def simulate(p: Parameters = Parameters(), policy: Policy = POLICIES['B6']) -> tuple[pd.DataFrame,pd.DataFrame]:
    if p.n < 20 or p.years < 1 or not 0 <= p.excluded_fraction < 1:
        raise ValueError('Invalid population, horizon or excluded fraction.')
    if not (0 <= p.demurrage <= p.max_demurrage < 1 and 0 <= p.max_tax < 1):
        raise ValueError('Levy and tax rates must lie in [0,1).')
    if p.money_gdp <= 0 or p.liquidity_elasticity < 0 or not 0 <= p.bot_share < 1:
        raise ValueError('Invalid liquidity or attack parameters.')
    if not (0 <= p.dilution_threshold < 1 and p.dilution_cap >= 0):
        raise ValueError('Invalid dilution parameters.')
    if not 0 <= p.money_preference_shock < 1 or not 0 <= p.shock_size < 1:
        raise ValueError('Shock proportions must be in [0,1).')
    if policy.wage_tax_multiplier < 0 or policy.capital_tax_multiplier < 0:
        raise ValueError('Tax multipliers cannot be negative.')
    if policy.payout_mode == 'matched_levy' and (not policy.usownership or p.sell_rate > 0):
        raise ValueError('Matched-payout experiment requires shadow grants and no secondary sales.')
    rng = np.random.default_rng(p.seed)
    n = p.n
    weights = np.array([0.35,0.35,0.30])
    latent = rng.normal(size=n)
    labour0 = normalize(np.exp(0.6*latent[:,None]+0.25*rng.normal(size=(n,3))))
    wealth = np.exp(1.8*(0.45*latent+np.sqrt(1-0.45**2)*rng.normal(size=n)))
    ordinary = normalize(wealth[:,None]*np.exp(0.2*rng.normal(size=(n,3))))
    initial_ordinary = ordinary.copy()
    cohorts: list[np.ndarray] = []
    affinity = rng.dirichlet([2,2,2],size=n)
    engagement = np.clip(np.exp(0.25*latent[:,None]+0.45*rng.normal(size=(n,3))),0,3)
    creation = np.clip(np.exp(0.2*latent[:,None]+0.7*rng.normal(size=(n,3))),0,5)
    active = np.ones(n)
    excluded = np.argsort(labour0.mean(axis=1))[:int(p.excluded_fraction*n)]
    active[excluded] = 0
    buyers = wealth >= np.quantile(wealth,0.90)
    exposure = rng.uniform(0.25,0.95,size=(n,3))
    base_liq = np.exp(p.liquidity_heterogeneity*latent)
    base_liq /= base_liq.mean()
    cash = p.money_gdp*(0.5/n+0.5*normalize(wealth))
    K = p.capital_output*weights
    K0 = K.copy()
    P = Yprev = 1.0
    inflation_prev = expected = p.inflation_target
    old_kappa = p.money_gdp/(1-p.investment_base-p.government_share)*base_liq
    consumption_prev = np.full(n,(1-p.investment_base-p.government_share)/n)
    records = []
    cumulative_legacy_dividend = 0.0
    terminal_agents = None
    status = 'ok'
    for t in range(1,p.years+1):
        M0 = float(cash.sum()); P0 = P
        a = automation(t,p); abar = float(weights@a)
        delta = dilution(a,p) if policy.usownership else np.zeros(3)
        scores = contribution_scores(consumption_prev,affinity,engagement,creation,active,policy.scoring,p.bot_share)
        ordinary,cohorts = update_equity(ordinary,cohorts,delta,scores)
        cash,ordinary,cohorts,traded = sell_vested(cash,ordinary,cohorts,P0*K,buyers,p)
        U = sum(cohorts,np.zeros_like(ordinary)); ownership = ordinary+U
        assert np.max(np.abs(ownership.sum(axis=0)-1)) < 1e-10
        lambdas = 0.10+(0.58-0.10)*(1-a)
        invest = np.clip(p.investment_base+p.investment_ai*a-p.dilution_investment_penalty*delta,0.04,0.40)
        invest = np.minimum(invest,1-lambdas-0.02)
        nu = float(weights@invest)
        dividend_rate = 1-lambdas-invest
        L = normalize(labour0*(1-a[None,:]*exposure))
        wage_share = L@(weights*lambdas)
        use_share = U@(weights*dividend_rate)
        ordinary_share = ordinary@(weights*dividend_rate)
        income_share = wage_share+use_share+ordinary_share
        assert abs(income_share.sum()-(1-nu)) < 1e-10
        z = (1+p.trend_tfp)**t*np.exp(p.ai_gain*a)
        raw_capacity = float(np.sum(weights*z*(K/K0)**p.capital_elasticity))
        resource_capacity = p.resource_cap*(1+p.resource_growth)**t/(1+p.resource_intensity*abar)
        yhat = min(raw_capacity,resource_capacity)
        shock = 1.0
        if p.shock_year > 0 and p.shock_year <= t < p.shock_year+3:
            shock -= p.shock_size*(1-(t-p.shock_year)/3)
        capacity = yhat*shock
        yforecast = yhat*(1+p.forecast_bias)
        Nhat = P0*yforecast
        G = p.government_share*Nhat
        drate = 0.0
        if policy.demurrage:
            drate = min(p.max_demurrage,p.demurrage+p.demurrage_feedback*max(inflation_prev-p.inflation_target,0))
        burn_i = levy(cash,Nhat,drate,p,policy.progressive)
        cash_after = cash-burn_i; B = float(burn_i.sum())
        effective_d = B/M0
        # Opportunity-cost response is a behavioural assumption. Base kappa is
        # normalised at the target inflation and zero levy, not fit to data.
        kappa = p.money_gdp/(1-p.investment_base-p.government_share)*base_liq
        kappa *= np.exp(np.clip(-p.liquidity_elasticity*(expected-p.inflation_target+effective_d+p.alternative_return-p.reference_alternative_return),-18,8))
        if p.money_preference_shock_year and t >= p.money_preference_shock_year:
            kappa *= 1-p.money_preference_shock
        alpha = 1/(1+kappa)
        desired_mu = ((1+p.inflation_target)*(yforecast/Yprev)*(kappa.mean()/old_kappa.mean())-1
                      +p.controller_gain*(p.inflation_target-inflation_prev))
        desired_mu = float(np.clip(desired_mu,p.min_money_growth,p.max_money_growth))
        if policy.monetary == 'fixed':
            desired_mu = p.fixed_money_growth
        target_M = M0*(1+desired_mu)
        floor_reference = P0*yforecast**p.floor_indexation*p.income_floor/n
        # Quantiles commute with a nonnegative scalar. Cache the pre-tax
        # income quantile outside the fiscal root solve; this changes no rule.
        income_quantile = float(np.quantile(income_share,p.floor_quantile))*Nhat
        def evaluate(tax_rate: float):
            if policy.wage_tax_multiplier == policy.capital_tax_multiplier == 1.0:
                net_share = (1-tax_rate)*income_share
                net_quantile = (1-tax_rate)*income_quantile
            else:
                tw = min(tax_rate*policy.wage_tax_multiplier, 0.95)
                tk = min(tax_rate*policy.capital_tax_multiplier, 0.95)
                net_share = (1-tw)*wage_share + (1-tk)*(ordinary_share+use_share)
                net_quantile = float(np.quantile(net_share,p.floor_quantile))*Nhat
            predicted = net_share*Nhat
            if policy.transfers == 'none':
                transfers = np.zeros(n)
            elif policy.transfers == 'targeted':
                transfers = np.maximum(floor_reference-predicted,0)
            else:
                b = max(0.0,floor_reference-net_quantile)
                transfers = np.full(n,b)
            A = float(np.dot(alpha,net_share))
            denominator = 1-nu-A
            if denominator <= 1e-14:
                raise FloatingPointError('Nominal expenditure denominator collapsed.')
            N = (float(np.dot(alpha,cash_after+transfers))+G)/denominator
            tax_i = (income_share-net_share)*N
            disposable = income_share*N+transfers-tax_i
            C = alpha*(cash_after+disposable)
            money_end = cash_after+disposable-C
            return N,transfers,tax_i,disposable,C,money_end
        fiscal_bound = False
        if policy.monetary == 'fiscal':
            tau = p.fixed_tax if policy.tax_override is None else policy.tax_override
        else:
            def f(tax_rate):
                return float(evaluate(tax_rate)[-1].sum())-target_M
            flo,fhi = f(0.0),f(p.max_tax)
            if flo*fhi <= 0:
                tau = float(brentq(f,0,p.max_tax,xtol=1e-13))
            else:
                tau = 0.0 if abs(flo) < abs(fhi) else p.max_tax
                fiscal_bound = True
        N,transfers,tax_i,disposable,C,cash = evaluate(tau)
        # Sticky downward prices; excess nominal demand is met by prices rather
        # than output above capacity. This is a closure, not a Phillips estimate.
        P = max(N/capacity,P0*(1-p.max_deflation))
        Y = N/P; pi = P/P0-1
        J = nu*N
        T = float(tax_i.sum()); H = float(transfers.sum())
        F = G+H-T  # fiscal issuance net of ordinary tax receipts, before demurrage
        M1 = float(cash.sum())
        residual = M1-M0-(F-B)
        goods_residual = N-float(C.sum())-J-G
        Knew = (1-p.depreciation)*K+weights*invest*Y
        # Exact payout equivalence: legal owners keep all shares in the levy
        # comparator; gross dividend tax and participant rebate offset. The
        # shadow register is used only to match the equity policy's cash flows.
        matched = policy.payout_mode == 'matched_levy'
        legal_ownership = initial_ordinary if matched else ownership
        legal_U = np.zeros_like(U) if matched else U
        gross_pass_through = float(use_share.sum()*N) if matched else 0.0
        wealth_end = cash/P+legal_ownership@Knew
        eqwealth = legal_ownership@Knew
        legacy_div = float(ordinary_share.sum()*Y)
        cumulative_legacy_dividend += legacy_div/(1.03**t)
        top10 = np.argsort(wealth_end)[-max(1,n//10):]
        top1 = np.argsort(wealth_end)[-max(1,n//100):]
        c_real = C/P
        floor_real = p.income_floor*yhat**p.floor_indexation/n
        required_gap = float(np.maximum(floor_real-(disposable/P-burn_i/P),0).sum())
        records.append(dict(year=t,calendar_year=p.start_year+t,automation=abar,real_gdp=Y,capacity=capacity,raw_capacity=raw_capacity,
            nominal_gdp=N,price_level=P,inflation=pi,labour_share=float(weights@lambdas),
            labour_demand_proxy=float(np.mean(1-a[None,:]*exposure))*Y/capacity,
            investment_share=nu,capital_stock=float(Knew.sum()),
            usownership_share=float(weights@legal_U.sum(axis=0)),
            shadow_participation_share=float(weights@U.sum(axis=0)),
            participant_income_gdp=float(use_share.sum()),pass_through_levy_gdp=gross_pass_through/N,
            total_recorded_tax_gdp=(T+gross_pass_through)/N,
            use_dividend_gdp=0.0 if matched else float(use_share.sum()),median_use_dividend=float(np.median(use_share)*N/P*n),
            mvi_gdp=H/N,mvi_real_resident_equivalent=H/P,
            fiscal_issuance_gdp=F/N,net_seigniorage_gdp=(M1-M0)/N,burn_gdp=B/N,
            money_growth=M1/M0-1,money_gdp=M1/N,velocity=N/M1,
            demurrage_rate=drate,effective_demurrage=effective_d,tax_rate=tau,tax_gdp=T/N,
            public_expenditure_gdp=(G+H)/N,government_consumption_gdp=G/N,
            gini_income=gini(disposable),gini_wealth=gini(wealth_end),top10_wealth=float(wealth_end[top10].sum()/wealth_end.sum()),
            top1_wealth=float(wealth_end[top1].sum()/wealth_end.sum()),median_income=float(np.median(disposable)/P*n),
            p10_income=float(np.quantile(disposable/P,p.floor_quantile)*n),
            mean_log_consumption=float(np.log(np.maximum(c_real*n,1e-14)).mean()),
            median_consumption=float(np.median(c_real)*n),coverage_shortfall=required_gap/Y,
            secondary_sales_gdp=traded/N,legacy_capital_share=1.0 if matched else float(weights@ordinary.sum(axis=0)),
            ordinary_discounted_dividends=cumulative_legacy_dividend,resource_pressure_proxy=raw_capacity/capacity,
            output_gap=Y/capacity-1,accounting_residual=residual/N,goods_residual=goods_residual/N,
            equity_residual=float(np.max(np.abs(ownership.sum(axis=0)-1))),
            controller_at_bound=float(fiscal_bound),policy=policy.name))
        terminal_agents = pd.DataFrame(dict(agent=np.arange(n),real_cash=cash/P,
            real_equity=eqwealth,income=disposable/P,use_dividend=use_share*Y,consumption=c_real,
            active=active,initial_capital=initial_ordinary@K0,final_use_equity=legal_U@Knew))
        if not np.isfinite(P) or P > p.numerical_price_limit or pi > p.numerical_inflation_limit:
            status = 'nominal_collapse'
            break
        if np.min(cash) < -1e-10 or abs(residual/N)>1e-9 or abs(goods_residual/N)>1e-9:
            raise AssertionError('Stock-flow consistency failure')
        expected = (1-p.expected_inflation_adjustment)*expected+p.expected_inflation_adjustment*pi
        consumption_prev = C
        Yprev = Y; inflation_prev = pi; old_kappa = kappa
        K = Knew
    out = pd.DataFrame(records)
    out['status'] = status
    return out,terminal_agents


def frontier(k0: float, elasticity: float, growth: float, inflation: float,
             demurrage: float) -> dict[str,float]:
    """Exact discrete annual balance-sheet capacity at a constant money/GDP ratio.

k0 is demand at zero inflation and zero demurrage. This analytical model is
separate from the heterogeneous simulation's consumption-liquidity closure.
"""
    k = k0*np.exp(-elasticity*(inflation+demurrage))
    nominal_growth = (1+growth)*(1+inflation)-1
    net = k*nominal_growth/(1+nominal_growth)
    burn = k*demurrage/(1+nominal_growth)
    return dict(k=k,net=net,burn=burn,gross=net+burn)
