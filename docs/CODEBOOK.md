# Simulation codebook

## Time

- `year`: model year, starting at 1.
- `calendar_year`: `start_year + year`; default `start_year=2027`.
- Model year 10 = 2037; model year 50 = 2077.

## Core stocks

- `cash`: household sovereign transaction-money balances.
- `K`: sectoral productive capital.
- `ordinary`: legacy/private ownership shares by household and sector.
- `cohorts`: successive usownership equity cohorts.
- `U`: cumulative participation/usownership equity.

## Production and automation

`automation(t,p)` produces a logistic automation path by sector. Automation changes labour shares and raises productivity through the scenario-specific `ai_gain`. Productive capacity is bounded by an explicit resource ceiling.

## Usownership

`dilution(a,p)` determines the maximum new equity issue associated with automation above a threshold. `contribution_scores(...)` assigns the new cohort using one of four rules:

- equal;
- consumption;
- concave consumption;
- contribution-weighted participation.

`update_equity(...)` performs exact dilution accounting so each firm's equity sums to one after every issue.

`usownership_share` is the user-held legal corporate equity share reported by the simulation. In matched-levy counterfactuals, a shadow participation register is retained while legal user equity is zero.

## Income

Household income contains wage income, ordinary capital income, usownership participant income and MVI/transfers. The model records both participant income and the transfer required to maintain the selected income floor.

## Money and seigniorage

The monetary identity is checked every period:

`closing money - opening money = fiscal issuance - currency burn`.

`fiscal_issuance_gdp` is issuance before the holding levy; `burn_gdp` is permanent withdrawal; `net_seigniorage_gdp` is net monetary expansion. The code never equates a percentage increase in money with the same percentage of GDP.

## Demurrage / holding levy

`levy(...)` can be flat or progressive and can protect a transactional balance. The levy reduces balances, but the model also allows money demand to fall when expected inflation, the levy or alternative returns make holding the currency less attractive.

## Fiscal closure

In adaptive cases a bounded scalar root chooses a conventional tax rate so the desired money stock can be met. Consequently near-target inflation can rely on substantial residual taxation. Fiscal-dominant variants instead use a fixed tax rule and let monetary issuance close the fiscal balance.

## Main result columns

- `real_gdp`, `nominal_gdp`
- `inflation`
- `labour_share`
- `usownership_share`
- `participant_income_gdp`
- `mvi_gdp`
- `fiscal_issuance_gdp`
- `net_seigniorage_gdp`
- `burn_gdp`
- `money_gdp`, `velocity`
- `tax_gdp`
- `gini_income`, `gini_wealth`
- `coverage_shortfall`
- `accounting_residual`, `goods_residual`, `equity_residual`

All GDP shares are fractions in the CSV files unless a column explicitly states other units.
