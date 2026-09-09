#!/usr/bin/env python3
"""Matched-institution counterfactuals and analytic incidence calculations.

Run from the repository root. No external data or network connection required.
These are conditional experiments, not estimates or optimized tax schedules.
"""
from pathlib import Path
import sys, json
from dataclasses import replace, asdict
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from ssm.model import Parameters, Policy, POLICIES, AI_SCENARIOS, simulate

COMPARISON_POLICIES = {
    'B0': POLICIES['B0'], 'B2': POLICIES['B2'], 'B5': POLICIES['B5'],
    'B6': POLICIES['B6'], 'B7': POLICIES['B7'],
    'B10': Policy('B10: capital-tilted tax and universal transfer',
                 wage_tax_multiplier=0.6, capital_tax_multiplier=1.4),
    'B11': replace(POLICIES['B5'], name='B11: matched dividend levy',payout_mode='matched_levy'),
    'B12': replace(POLICIES['B6'], name='B12: matched levy and monetary hybrid',payout_mode='matched_levy'),
    'B13': replace(POLICIES['B6'],name='B13: usownership and targeted income protection', transfers='targeted'),
}

def write_table(df: pd.DataFrame, path: Path, columns: list[str], headers: list[str], formats: dict):
    lines=['\\begin{tabular}{@{}'+'l'+'r'*(len(columns)-1)+'@{}}','\\toprule', ' & '.join(headers)+' \\\\', '\\midrule']
    for _,r in df.iterrows():
        cells=[formats.get(c,str)(r[c]) for c in columns]
        lines.append(' & '.join(cells)+' \\\\')
    lines+=['\\bottomrule','\\end{tabular}']
    path.write_text('\n'.join(lines)+'\n')

def main():
    out=ROOT/'results/tables'; out.mkdir(exist_ok=True)
    frames=[];summary=[]; agents=[]; checks=[]
    for scenario,settings in AI_SCENARIOS.items():
        cache={}
        for code,policy in COMPARISON_POLICIES.items():
            print(f'Comparison {scenario}: {code}', flush=True)
            df,a=simulate(replace(Parameters(),years=50,**settings),policy)
            df['scenario']=scenario;df['code']=code
            frames.append(df);cache[code]=df
            a['scenario']=scenario;a['code']=code;agents.append(a)
            r=df.iloc[-1].to_dict()
            r.update(max_inflation=df.inflation.max(), cumulative_mvi_real=df.mvi_real_resident_equivalent.sum(),
                     consumption_score=np.sum(df.mean_log_consumption/(1.03**df.year)),
                     min_p10=df.p10_income.min(),max_coverage_gap=df.coverage_shortfall.max())
            summary.append(r)
        for left,right in [('B5','B11'),('B6','B12')]:
            for col in ['real_gdp','inflation','mvi_gdp','tax_gdp','median_income','p10_income','mean_log_consumption','money_gdp']:
                err=float(np.max(np.abs(cache[left][col]-cache[right][col])))
                checks.append(dict(scenario=scenario,equity=left,levy=right,metric=col,max_absolute_error=err))
                if err>1e-10: raise AssertionError(f'Matched payout failed: {left}/{right} {col} {err}')
    paths=pd.concat(frames,ignore_index=True);s=pd.DataFrame(summary)
    paths.to_csv(out/'policy_comparison_paths.csv',index=False)
    pd.concat(agents,ignore_index=True).to_csv(out/'policy_comparison_agents.csv',index=False)
    s.to_csv(out/'policy_comparison_summary.csv',index=False)
    pd.DataFrame(checks).to_csv(out/'matched_equivalence_checks.csv',index=False)
    # Fair benchmark sensitivity, one-at-a-time. Same primitives within each set.
    robustness=[]
    designs={'central':{},'high_investment_penalty':{'dilution_investment_penalty':3.0},
             'no_investment_penalty':{'dilution_investment_penalty':0.0},
             'excluded_20pct':{'excluded_fraction':0.2},'fast_dilution':{'dilution_cap':0.04},
             'slow_dilution':{'dilution_cap':0.005},'tight_public_budget':{'government_share':0.07},
             'larger_public_budget':{'government_share':0.30},'fixed_real_floor':{'floor_indexation':0.0},
             'high_liquidity_elasticity':{'liquidity_elasticity':10.0},
             'score_capture_20pct':{'bot_share':0.20},'resource_bottleneck':{'resource_growth':0.012}}
    for name,changes in designs.items():
        print(f'Comparative robustness: {name}', flush=True)
        for code in ['B0','B2','B5','B6','B10','B13']:
            df,_=simulate(replace(Parameters(),**changes),COMPARISON_POLICIES[code])
            r=df.iloc[-1].to_dict();r.update(experiment=name,code=code,max_inflation=df.inflation.max())
            robustness.append(r)
    pd.DataFrame(robustness).to_csv(out/'policy_comparison_robustness.csv',index=False)
    # Share issuance uses delta relative to pre-issue stock; no unrelated capital raises.
    incidence=[]
    for delta in [0.005,0.01,0.02]:
        for T in [10,25,50]:
            user=1-(1+delta)**(-T)
            incidence.append(dict(annual_issuance=delta,year=T,user_share=user,
                required_total_value_growth_for_legacy_wealth=1/(1-user)-1,
                # Exact annual end-period dividends, r > g, perpetual constant issuance.
                legacy_pv_loss=1-((1.08-1.03)/(1.08*(1+delta)-1.03))))
    inc=pd.DataFrame(incidence);inc.to_csv(out/'ownership_incidence.csv',index=False)
    # Cash vs equity present-value comparison with identical beneficiaries and discounting.
    # Per-period cash levy fraction U(t) exactly replicates the granted share's dividends.
    cf=[]
    for delta in [0.005,0.01,0.02]:
        for t in range(1,51):
            u=1-(1+delta)**-t;profit=100*(1.03)**t
            cf.append(dict(delta=delta,year=t,distributable_profit=profit,user_share=u,
                           user_dividend=u*profit,matched_levy_transfer=u*profit,
                           old_owners_dividend=(1-u)*profit))
    pd.DataFrame(cf).to_csv(out/'matched_cashflow_arithmetic.csv',index=False)
    med=s[s.scenario=='medium'].copy()
    write_table(med,ROOT/'paper/tables/policy_comparison.tex',
        ['code','real_gdp','mvi_gdp','tax_gdp','participant_income_gdp','gini_wealth'],
        ['Policy','$Y_{50}$','MVI/GDP','Tax/GDP','Participant/GDP','Book Gini'],
        {'real_gdp':lambda x:f'{x:.2f}','mvi_gdp':lambda x:f'{100*x:.2f}',
         'tax_gdp':lambda x:f'{100*x:.2f}','participant_income_gdp':lambda x:f'{100*x:.2f}',
         'gini_wealth':lambda x:f'{x:.3f}'})
    write_table(inc,ROOT/'paper/tables/ownership_incidence.tex',
        ['annual_issuance','year','user_share','required_total_value_growth_for_legacy_wealth','legacy_pv_loss'],
        ['Issuance (\\%)','Years','User share (\\%)','Value offset (\\%)','PV loss (\\%)'],
        {'annual_issuance':lambda x:f'{100*x:.1f}','year':lambda x:f'{x:.0f}',
         'user_share':lambda x:f'{100*x:.1f}', 'required_total_value_growth_for_legacy_wealth':lambda x:f'{100*x:.1f}',
         'legacy_pv_loss':lambda x:f'{100*x:.1f}'})
    figs=ROOT/'paper/figures'
    for metric,filename,label in [('mvi_gdp','comparative_transfer','MVI / GDP (%)'),
                                  ('gini_wealth','comparative_ownership','Book-value wealth Gini')]:
        fig,ax=plt.subplots(figsize=(7.2,4.3))
        for code in ['B0','B2','B5','B6','B10','B13']:
            d=paths[(paths.scenario=='medium')&(paths.code==code)]
            ax.plot(d.year,d[metric]*(100 if metric=='mvi_gdp' else 1),label=code,
                    linestyle='--' if code in ['B5','B13'] else '-')
        ax.set(xlabel='Model year',ylabel=label);ax.legend(ncol=3,frameon=False)
        ax.spines[['top','right']].set_visible(False);fig.tight_layout()
        fig.savefig(figs/f'{filename}.pdf');fig.savefig(ROOT/f'results/figures/{filename}.png',dpi=180);plt.close(fig)
    # Durability is a conditional cash-flow distinction, not an estimated hazard.
    fig,ax=plt.subplots(figsize=(7.2,4.3))
    tt=np.arange(1,51);u=1-1.01**(-tt)
    ax.plot(tt,100*u,label='Equity dividends / identical levy rebates')
    ax.plot(tt,100*u*.99**tt,label='Rebates with assumed 1% annual interruption hazard',linestyle='--')
    ax.set(xlabel='Year',ylabel='Expected payment / distributable profit (%)');ax.legend(frameon=False,fontsize=8)
    ax.spines[['top','right']].set_visible(False);fig.tight_layout()
    fig.savefig(figs/'conditional_durability.pdf');fig.savefig(ROOT/'results/figures/conditional_durability.png',dpi=180);plt.close(fig)
    # Persist configuration and counts; explicitly separate earlier design from additions.
    (ROOT/'configs/comparisons.json').write_text(json.dumps({k:asdict(v) for k,v in COMPARISON_POLICIES.items()},indent=2))
    log={'main_comparison_runs':len(summary),'robustness_comparison_runs':len(robustness),
         'matched_checks':len(checks),'max_matched_error':max(x['max_absolute_error'] for x in checks),
         'max_accounting_error':float(paths.accounting_residual.abs().max())}
    (ROOT/'results/comparison_manifest.json').write_text(json.dumps(log,indent=2))
    print(med[['code','real_gdp','mvi_gdp','tax_gdp','gini_wealth','participant_income_gdp']].to_string(index=False))
    print(json.dumps(log,indent=2))
if __name__=='__main__': main()
