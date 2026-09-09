"""Single-panel figures; default matplotlib colours, no hidden styling."""
from pathlib import Path
import shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def make_figures(root):
    table=root/'results/tables';out=root/'results/figures'
    t=pd.read_csv(table/'trajectories.csv');s=pd.read_csv(table/'sensitivity.csv')
    r=pd.read_csv(table/'robustness_paths.csv');f=pd.read_csv(table/'frontier.csv')
    def save(name,xlab,ylab,title):
        ax=plt.gca();ax.set(xlabel=xlab,ylabel=ylab,title=title)
        ax.spines[['top','right']].set_visible(False)
        handles,labels=ax.get_legend_handles_labels()
        if handles:ax.legend(frameon=False,fontsize=8)
        plt.tight_layout();plt.savefig(out/(name+'.pdf'),bbox_inches='tight');plt.savefig(out/(name+'.png'),dpi=160,bbox_inches='tight')
        shutil.copy2(out/(name+'.pdf'),root/'paper/figures'/(name+'.pdf'));plt.close()
    med=t[(t.scenario=='medium')&(t.year<=50)]
    for field,name,ylabel in [('mvi_gdp','transfer_paths','Transfer / GDP (%)'),
                            ('tax_gdp','tax_paths','Residual conventional tax / GDP (%)'),
                            ('gini_wealth','wealth_paths','Wealth Gini (book equity + real money)')]:
        plt.figure(figsize=(6.9,3.9))
        for code in ['B0','B1','B2','B5','B6','B7']:
            z=med[med.code==code];scale=1 if field=='gini_wealth' else 100
            plt.plot(z.year,z[field]*scale,label=code,linewidth=1.7)
        save(name,'Years from model start',ylabel,'Medium automation: policy comparison')
    plt.figure(figsize=(6.9,3.9))
    for code in ['B2','B3','B4','B6','B8']:
        z=med[med.code==code];plt.plot(z.year,z.inflation*100,label=code,linewidth=1.7)
    save('inflation_paths','Years from model start','Annual inflation (%)','Price stability is conditional on the fiscal closure')
    plt.figure(figsize=(6.9,3.9));z=med[med.code=='B6']
    for col,label in [('labour_share','Labour income'),('use_dividend_gdp','Usownership dividends'),('mvi_gdp','Universal transfer')]:
        plt.plot(z.year,100*z[col],label=label,linewidth=1.8)
    save('income_transition','Years from model start','Share of GDP (%)','B6: income-source transition (not an exhaustive partition)')
    plt.figure(figsize=(6.9,3.9))
    for sc in ['slow','medium','fast']:
        z=t[(t.scenario==sc)&(t.code=='B6')];plt.plot(z.year,100*z.usownership_share,label=sc)
    save('equity_transition','Years from model start','User-held equity (%)','Firm-specific usownership; no pooling is imposed')
    plt.figure(figsize=(6.9,3.9))
    for sc in ['slow','medium','fast']:
        z=t[(t.scenario==sc)&(t.code=='B6')];plt.plot(z.year,z.real_gdp,label=sc)
    save('real_output','Years from model start','Real GDP (initial = 1)','Illustrative resource-constrained trajectories, not forecasts')
    plt.figure(figsize=(6.9,3.9));z=med[med.code=='B6']
    for col,label in [('fiscal_issuance_gdp','Issuance before burn'),('burn_gdp','Burn'),('net_seigniorage_gdp','Net monetary financing')]:
        plt.plot(z.year,100*z[col],label=label)
    save('monetary_flows','Years from model start','Share of GDP (%)','B6: distinguish issuance, monetary levy and net financing')
    plt.figure(figsize=(6.9,3.9))
    for eps in [1,4,10]:
        z=f[(f.k0==.6)&(f.elasticity==eps)&(f.growth==.03)]
        plt.plot(100*z.demurrage,100*z.gross,label=f'Demand elasticity {eps}')
    save('frontier','Annual uniform demurrage (%)','Gross financing capacity / GDP (%)','Analytical envelope: 3% real growth and 2% inflation')
    plt.figure(figsize=(6.9,3.9))
    for name,label in [('baseline','Baseline'),('low_coverage','20% excluded'),('score_attack','20% score capture'),
                       ('liquidation_no_vesting','Early liquidation'),('liquidation_with_vesting','Vesting + liquidation')]:
        z=r[r.experiment==name];plt.plot(z.year,z.gini_wealth,label=label)
    save('participation_risks','Years from model start','Wealth Gini','Participation, score integrity and transfer restrictions')
    plt.figure(figsize=(6.9,3.9))
    for name,label in [('baseline','Relative floor 25%'),('low_relative_floor','Relative floor 15%'),
                       ('high_relative_floor','Relative floor 40%'),('fixed_real_floor','Fixed real floor')]:
        z=r[r.experiment==name];plt.plot(z.year,100*z.mvi_gdp,label=label)
    save('sunset_conditions','Years from model start','Transfer / GDP (%)','The income objective determines whether a sunset occurs')
    plt.figure(figsize=(6.9,3.9));z=s[s.code=='B6']
    plt.scatter(z.dilution_cap*100,z.mvi_gdp*100,s=20,alpha=.65)
    save('sensitivity_scatter','Annual dilution cap (%)','Year-50 MVI / GDP (%)','128 Latin-hypercube designs; not a probability forecast')
