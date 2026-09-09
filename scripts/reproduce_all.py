#!/usr/bin/env python3
"""Reproduce the entire offline numerical package, with explicit scenario inputs."""
from __future__ import annotations
import argparse, hashlib, json, sys, platform, subprocess, time, os
os.environ.setdefault("MPLBACKEND", "Agg")
# Fix BLAS thread count for predictable small-matrix performance and reproduction.
for _thread_variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_thread_variable] = os.environ.get("SSM_NUM_THREADS", "1")
from pathlib import Path
from dataclasses import asdict, replace
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import pandas as pd
import yaml
from scipy.stats import qmc, spearmanr
from ssm.model import Parameters, POLICIES, AI_SCENARIOS, simulate, frontier
from make_figures import make_figures
from make_workbook import make_workbook


def write_csv(df, name):
    path=ROOT/'results'/'tables'/name
    df.to_csv(path,index=False,float_format='%.12g')
    return path


def run_main():
    paths=[]; agents=[]; summaries=[]
    for scenario,overrides in AI_SCENARIOS.items():
        p=replace(Parameters(),years=100,**overrides)
        for code,pol in POLICIES.items():
            df,a=simulate(p,pol)
            df['scenario']=scenario;df['code']=code
            paths.append(df)
            a['scenario']=scenario;a['code']=code;a['terminal_year']=int(df.year.iloc[-1]);agents.append(a)
            for horizon in [10,25,50,100]:
                sub=df[df.year<=horizon]
                last=sub.iloc[-1]
                rec={'scenario':scenario,'code':code,'horizon':horizon,'calendar_horizon':p.start_year+horizon,'completed':int(last.year)==horizon,
                     'last_year':int(last.year),'status':last.status,
                     'max_inflation':sub.inflation.max(),'peak_mvi':sub.mvi_gdp.max(),
                     'peak_mvi_year':int(sub.loc[sub.mvi_gdp.idxmax(),'year']),
                     'mean_tax_gdp':sub.tax_gdp.mean(),
                     'max_accounting_error':sub.accounting_residual.abs().max(),
                     'max_equity_error':sub.equity_residual.max()}
                for c in ['real_gdp','nominal_gdp','inflation','usownership_share','mvi_gdp','tax_gdp',
                          'gini_wealth','gini_income','top10_wealth','top1_wealth','median_income','median_use_dividend',
                          'fiscal_issuance_gdp','net_seigniorage_gdp','burn_gdp','money_gdp','velocity',
                          'coverage_shortfall','labour_share','ordinary_discounted_dividends']:
                    rec[c]=last[c] if rec['completed'] else np.nan
                summaries.append(rec)
    paths=pd.concat(paths,ignore_index=True)
    # Monetary amounts are scaled only; this is not an estimated EU forecast.
    anchor=json.loads((ROOT/'data/processed/anchors.json').read_text())
    gdp=anchor['eu_gdp_eur_2025'];pop=anchor['population_scaling_2026']
    paths['gdp_2025_eur_trillion']=paths.real_gdp*gdp/1e12
    paths['gdp_nominal_eur_trillion']=paths.nominal_gdp*gdp/1e12
    paths['mvi_real_eur_resident_year']=paths.mvi_real_resident_equivalent*gdp/pop
    paths['mvi_nominal_eur_resident_year']=paths.mvi_gdp*paths.nominal_gdp*gdp/pop
    write_csv(paths,'trajectories.csv');write_csv(pd.concat(agents,ignore_index=True),'terminal_agents.csv')
    summary=pd.DataFrame(summaries);write_csv(summary,'horizons.csv')
    return paths,summary


def run_robustness():
    specs={
        'baseline':({},{}),
        'low_relative_floor':({'income_floor':.15},{}),
        'high_relative_floor':({'income_floor':.40},{}),
        'fixed_real_floor':({'floor_indexation':0.0},{}),
        'no_demurrage':({}, {'demurrage':False}),
        'flat_demurrage':({}, {'progressive':False}),
        'higher_levy':({'demurrage':.10},{}),
        'historical_33pct_levy':({'demurrage':.33,'max_demurrage':.33},{}),
        'low_money_demand':({'money_gdp':.20},{}),
        'high_money_demand':({'money_gdp':1.00},{}),
        'high_opportunity_elasticity':({'liquidity_elasticity':10.0},{}),
        'high_alternative_return':({'alternative_return':.08},{}),
        'supply_shock':({'shock_year':15,'shock_size':.20},{}),
        'money_demand_shock':({'money_preference_shock_year':15,'money_preference_shock':.40},{}),
        'optimistic_forecast':({'forecast_bias':.10},{}),
        'fiscal_capacity_limit':({'max_tax':.35},{}),
        'no_tax':({}, {'monetary':'fiscal','tax_override':0.0}),
        'no_tax_7pct_services':({'government_share':.07},{'monetary':'fiscal','tax_override':0.0}),
        'no_tax_7pct_low_floor':({'government_share':.07,'income_floor':.15},{'monetary':'fiscal','tax_override':0.0}),
        'no_tax_7pct_targeted':({'government_share':.07,'income_floor':.15},{'monetary':'fiscal','tax_override':0.0,'transfers':'targeted'}),
        'no_tax_7pct_high_balances':({'government_share':.07,'income_floor':.15,'money_gdp':1.0},{'monetary':'fiscal','tax_override':0.0}),
        'low_coverage':({'excluded_fraction':.20},{}),
        'score_attack':({'bot_share':.20},{}),
        'consumption_scores':({}, {'scoring':'consumption'}),
        'concave_scores':({}, {'scoring':'concave'}),
        'equal_grants_comparator':({}, {'scoring':'equal'}),
        'fast_equity_diffusion':({'dilution_cap':.05},{}),
        'slow_equity_diffusion':({'dilution_cap':.005},{}),
        'liquidation_no_vesting':({'sell_rate':.25,'vesting_years':0,'transfer_retained_core':0.0},{}),
        'liquidation_with_vesting':({'sell_rate':.25,'vesting_years':10,'transfer_retained_core':.20},{}),
        'unconstrained_resources':({'resource_cap':3,'resource_growth':.08},{}),
        'investment_penalty_zero':({'resource_cap':3,'resource_growth':.08,'dilution_investment_penalty':0.0},{}),
        'investment_penalty_high':({'resource_cap':3,'resource_growth':.08,'dilution_investment_penalty':3.0},{}),
        'very_scarce_resources':({'resource_cap':1.1,'resource_growth':.01},{}),
        'fast_ai':(AI_SCENARIOS['fast'],{}),
        'slow_ai':(AI_SCENARIOS['slow'],{}),
    }
    rows=[];series=[]
    for name,(params,polparams) in specs.items():
        p=replace(Parameters(),**params);pol=replace(POLICIES['B6'],**polparams)
        df,a=simulate(p,pol);df['experiment']=name;series.append(df)
        d=df.iloc[-1].to_dict();d['experiment']=name;d['max_inflation']=df.inflation.max()
        d['peak_mvi']=df.mvi_gdp.max();d['mean_tax_gdp']=df.tax_gdp.mean()
        d['price_band']=bool(df.inflation.abs().max()<=.05)
        d['sunset']=bool(len(df)==50 and (df.tail(5).mvi_gdp<.01).all())
        d['max_accounting_error']=df.accounting_residual.abs().max()
        d['controller_bound_years']=int(df.controller_at_bound.sum())
        rows.append(d)
    write_csv(pd.concat(series,ignore_index=True),'robustness_paths.csv')
    write_csv(pd.DataFrame(rows),'robustness.csv')
    (ROOT/'configs/robustness.yaml').write_text(yaml.safe_dump(specs,sort_keys=True))
    return pd.DataFrame(rows)


def run_sensitivity(samples=128):
    bounds={
        'dilution_cap':(.005,.05),'liquidity_elasticity':(1.0,10.0),'money_gdp':(.20,1.00),
        'income_floor':(.15,.40),'speed':(.08,.30),'midpoint':(10.,40.),
        'ai_gain':(.35,1.6),'resource_growth':(.01,.06),'excluded_fraction':(0,.25),
        'dilution_investment_penalty':(0.,2.0)}
    keys=list(bounds)
    points=qmc.LatinHypercube(d=len(keys),seed=831).random(samples)
    points=qmc.scale(points,[bounds[k][0] for k in keys],[bounds[k][1] for k in keys])
    rows=[]
    for sample,point in enumerate(points):
        values=dict(zip(keys,point))
        p=replace(Parameters(),n=160,**values)
        for code in ['B2','B5','B6']:
            df,_=simulate(p,POLICIES[code]);last=df.iloc[-1]
            row=dict(sample=sample,code=code,**values)
            row.update(terminal_year=int(last.year),status=last.status,
                sunset=bool(len(df)==50 and (df.tail(5).mvi_gdp<.01).all()),
                price_band=bool(df.inflation.abs().max()<=.05),
                mvi_gdp=last.mvi_gdp,gini_wealth=last.gini_wealth,real_gdp=last.real_gdp,
                tax_gdp=last.tax_gdp,usownership_share=last.usownership_share,
                coverage_shortfall=last.coverage_shortfall,max_inflation=df.inflation.max(),
                max_accounting_error=df.accounting_residual.abs().max())
            rows.append(row)
    result=pd.DataFrame(rows);write_csv(result,'sensitivity.csv')
    correlations=[]
    for output in ['mvi_gdp','gini_wealth','tax_gdp','real_gdp','max_inflation']:
        sub=result[result.code=='B6']
        for k in keys:
            r,_=spearmanr(sub[k],sub[output])
            correlations.append({'input':k,'output':output,'spearman_rho':r})
    write_csv(pd.DataFrame(correlations),'sensitivity_correlations.csv')
    return result


def run_frontier():
    rows=[]
    for k0 in [.2,.6,1.0]:
        for eps in [1.,4.,10.]:
            for growth in [.01,.03,.06]:
                for d in np.linspace(0,.40,81):
                    rows.append(dict(k0=k0,elasticity=eps,growth=growth,inflation=.02,demurrage=d,
                                     **frontier(k0,eps,growth,.02,d)))
    df=pd.DataFrame(rows);write_csv(df,'frontier.csv')
    return df


def run_micro():
    cases={
        'AI platform':(['Consumer','Intensive consumer','Evaluator','Domain expert','Plugin creator','Prosumer'],
                       [1,4,2,2,2,3],[0,1,3,3,2,3],[0,0,1,4,5,4]),
        'Autonomous mobility':(['Passenger','Frequent passenger','Safety reporter','Map contributor','Fleet host','Local operator'],
                       [1,4,2,2,3,3],[0,1,3,3,2,3],[0,0,1,3,4,5]),
        'Household robotics':(['Household user','Intensive user','Fault reporter','Accessibility tester','Skill author','Repair prosumer'],
                       [1,4,2,2,2,3],[0,1,3,3,2,3],[0,0,1,4,5,4]),
    }
    rows=[]
    for company,(roles,use,eng,prod) in cases.items():
        score=.35*np.sqrt(np.array(use))+.25*np.array(eng)+.4*np.array(prod)
        n_users=10000;old_shares=1000000;delta=.02;pool=old_shares*delta
        allocated=pool*score/(score.sum()*n_users)
        for i,role in enumerate(roles):
            rows.append(dict(company=company,role=role,users_in_class=n_users,use=use[i],engagement=eng[i],
                             creation=prod[i],score=score[i],shares_per_user=allocated[i],
                             post_issue_equity_per_user=allocated[i]/(old_shares+pool),
                             illustrative_dividend_eur=allocated[i]/(old_shares+pool)*10000000))
    df=pd.DataFrame(rows);write_csv(df,'micro_examples.csv')
    dilution=[]
    for annual in [.005,.02,.05]:
        for years in [10,25,50,100]:
            dilution.append(dict(annual_dilution=annual,years=years,user_share=1-(1+annual)**(-years)))
    write_csv(pd.DataFrame(dilution),'dilution_arithmetic.csv')
    return df


def render_tables(paths,summary,rob,sens,micro):
    def table(df,name,formats):
        out=df.copy()
        for col,fmt in formats.items():
            out[col]=out[col].map(lambda v: '--' if pd.isna(v) else fmt(v))
        tex=out.to_latex(index=False,escape=True,column_format='l'*len(out.columns))
        (ROOT/'paper/tables'/name).write_text(tex)
    med=summary[(summary.scenario=='medium')&(summary.horizon==50)].copy()
    x=med[['code','completed','real_gdp','mvi_gdp','tax_gdp','gini_wealth','max_inflation']].copy()
    x.loc[~x.completed,'max_inflation']=np.nan
    x.columns=['Policy','Complete','Real GDP','MVI/GDP','Tax/GDP','Wealth Gini','Peak inflation']
    table(x,'benchmarks.tex',{'Complete':lambda x:'yes' if x else 'no','Real GDP':lambda x:f'{x:.2f}',
        'MVI/GDP':lambda x:f'{100*x:.1f}%', 'Tax/GDP':lambda x:f'{100*x:.1f}%',
        'Wealth Gini':lambda x:f'{x:.3f}', 'Peak inflation':lambda x:f'{100*x:.1f}%'})
    x=summary[(summary.code=='B6')].copy()[['scenario','horizon','real_gdp','usownership_share','mvi_gdp','tax_gdp','gini_wealth']]
    x.columns=['AI path','Year','Real GDP','User equity','MVI/GDP','Tax/GDP','Wealth Gini']
    table(x,'projections.tex',{'Real GDP':lambda x:f'{x:.2f}', 'User equity':lambda x:f'{100*x:.1f}%',
        'MVI/GDP':lambda x:f'{100*x:.1f}%', 'Tax/GDP':lambda x:f'{100*x:.1f}%', 'Wealth Gini':lambda x:f'{x:.3f}'})
    chosen=['baseline','low_relative_floor','high_relative_floor','fixed_real_floor','low_coverage','score_attack',
            'consumption_scores','equal_grants_comparator','liquidation_no_vesting','liquidation_with_vesting',
            'supply_shock','fiscal_capacity_limit','historical_33pct_levy']
    x=rob[rob.experiment.isin(chosen)][['experiment','mvi_gdp','gini_wealth','tax_gdp','max_inflation']].copy()
    x['experiment']=x.experiment.str.replace('_',' ')
    x.columns=['Experiment','MVI/GDP','Wealth Gini','Tax/GDP','Peak inflation']
    table(x,'robustness.tex',{'MVI/GDP':lambda x:f'{100*x:.1f}%', 'Tax/GDP':lambda x:f'{100*x:.1f}%',
        'Wealth Gini':lambda x:f'{x:.3f}', 'Peak inflation':lambda x:f'{100*x:.1f}%'})
    x=micro[micro.company=='AI platform'][['role','score','shares_per_user','illustrative_dividend_eur']].copy()
    x.columns=['Role','Score','New shares/person','Dividend/person (EUR)']
    table(x,'micro.tex',{c:lambda v:f'{v:.3f}' for c in x.columns[1:]})
    macros={}
    for code in ['B1','B2','B5','B6','B7']:
        r=med[med.code==code].iloc[0]
        for key in ['mvi_gdp','tax_gdp','gini_wealth','usownership_share','median_income','max_inflation']:
            name='Result'+{'B1':'POne','B2':'PTwo','B5':'PFive','B6':'PSix','B7':'PSeven'}[code]+''.join(z.title() for z in key.split('_'))
            macros[name]=f'{r[key]:.3f}' if key in ['gini_wealth','median_income'] else f'{100*r[key]:.2f}'
    s6=sens[sens.code=='B6']
    macros['SensitivityCount']=str(len(s6));macros['SensitivitySunsets']=str(int(s6.sunset.sum()))
    macros['SensitivityPriceBand']=str(int(s6.price_band.sum()))
    macros['MaxAccountingError']=f'{paths.accounting_residual.abs().max():.2e}'
    (ROOT/'paper/results_macros.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in macros.items()))
    (ROOT/'results/key_findings.json').write_text(json.dumps(macros,indent=2))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--samples',type=int,default=128)
    parser.add_argument('--compile',action='store_true');args=parser.parse_args()
    for p in ['results/tables','results/figures','paper/tables','paper/figures']: (ROOT/p).mkdir(parents=True,exist_ok=True)
    (ROOT/'configs/baseline.yaml').write_text(yaml.safe_dump(asdict(Parameters()),sort_keys=True))
    (ROOT/'configs/policies.json').write_text(json.dumps({k:asdict(v) for k,v in POLICIES.items()},indent=2))
    for name,vals in AI_SCENARIOS.items():
        (ROOT/f'configs/{name}_ai.yaml').write_text(yaml.safe_dump(asdict(replace(Parameters(),**vals)),sort_keys=True))
    # The final reviewed bibliography is bundled with the paper.
    # Do not rebuild it from the source ledger during numerical reproduction.
    print('Running thirty policy/AI trajectories...',flush=True)
    start=time.monotonic()
    paths,summary=run_main()
    print(f'Main paths complete: {time.monotonic()-start:.1f}s',flush=True)
    rob=run_robustness()
    print(f'Robustness complete: {time.monotonic()-start:.1f}s',flush=True)
    print('Running paired Latin-hypercube design...',flush=True)
    sens=run_sensitivity(args.samples);front=run_frontier();micro=run_micro()
    print(f'Numerical experiments complete: {time.monotonic()-start:.1f}s',flush=True)
    render_tables(paths,summary,rob,sens,micro)
    print(f'LaTeX tables complete: {time.monotonic()-start:.1f}s',flush=True)
    make_figures(ROOT)
    print(f'Figures complete: {time.monotonic()-start:.1f}s',flush=True)
    print("Loading comparative module...", flush=True)
    from run_comparisons import main as run_comparisons
    print("Comparative module loaded.", flush=True)
    run_comparisons()
    make_workbook(ROOT)
    print(f'Figures and workbook complete: {time.monotonic()-start:.1f}s',flush=True)
    log={'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,
         'main_runs':30,'comparison_runs':99,'total_macro_runs':30+len(rob)+len(sens)+99,'robustness_runs':len(rob),'paired_sensitivity_runs':len(sens),
         'max_cash_identity_error':float(paths.accounting_residual.abs().max()),
         'max_goods_identity_error':float(paths.goods_residual.abs().max()),
         'max_equity_identity_error':float(paths.equity_residual.abs().max())}
    (ROOT/'results/run_manifest.json').write_text(json.dumps(log,indent=2))
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT/'results/tables').glob('*.csv'))}
    (ROOT/'results/csv_sha256.json').write_text(json.dumps(hashes,indent=2))
    if args.compile:
        subprocess.run([sys.executable,str(ROOT/'scripts/compile_paper.py')],check=True)
    print(json.dumps(log,indent=2))
if __name__=='__main__':main()
