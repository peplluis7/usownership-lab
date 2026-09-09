# usownership-lab
# Usownership and the AI Ownership Transition

Reproducible simulation framework for the AI ownership transition: usownership, programmable money, seigniorage, MVI, automation scenarios, and long-run capital redistribution from 2027 to 2077.

This repository implements the synthetic stock-flow-consistent laboratory used in the paper. It is a mechanism study, not an estimated forecast of the European Union or any other economy.

## Core research question

Can a rapid AI/robotics transition be made less disruptive if two mechanisms operate on different time scales?

1. **Income bridge:** MVI and bounded monetary financing protect household access to current output while labour income is disrupted.
2. **Ownership bridge:** contribution-weighted **usownership** gradually turns users and contributors into owners of the firms whose automated capital is becoming more productive.

The model tests the proposed mechanisms against stronger counterfactuals, including targeted and universal transfers, capital-focused taxation, equal equity grants and matched dividend levies.

## Two clocks in the paper

- **2027-2037:** proposed institutional experimentation and adoption window.
- **2027-2077:** 50-year structural horizon used to study ownership accumulation, dividend income and whether MVI/seigniorage dependence declines.

The simulator retains `year` as the model index and adds `calendar_year`; model year 10 is 2037 and model year 50 is 2077.

## What the simulator contains

- heterogeneous households;
- three firm sectors with different automation exposure;
- endogenous labour-income shares;
- retained-earnings capital accumulation;
- resource constraints;
- recurring firm-specific usownership grants;
- contribution, concave-consumption and equal-grant scoring rules;
- vesting and secondary-sale/reconcentration experiments;
- MVI / income-floor policies;
- adaptive, fixed and fiscal-dominant monetary closures;
- progressive or flat monetary holding levies/demurrage;
- endogenous transaction-money demand;
- conventional taxation and capital-tilted tax counterfactuals;
- matched dividend-levy counterfactuals;
- accounting checks for money, goods and equity.

The paper's full experiment contains **549 executed macro paths**:

- 30 main policy x AI paths;
- 36 robustness paths;
- 384 paired sensitivity paths (128 Latin-hypercube configurations x 3 policies);
- 99 strengthened policy-comparison paths.

## Central 50-year medium-AI comparison

The frozen results included in `results/tables/policy_comparison_summary.csv` reproduce the paper's central mechanism comparison:

| Policy | MVI/GDP at year 50 | Tax/GDP | User equity | Book-wealth Gini |
|---|---:|---:|---:|---:|
| B2 universal support, no user equity | 19.03% | 37.04% | 0.00% | 0.754 |
| B5 universal support + usownership | 10.57% | 28.53% | 29.67% | 0.583 |
| B6 usownership + holding-levy monetary architecture | 10.16% | 27.13% | 29.67% | 0.584 |
| B13 targeted protection + usownership hybrid | 1.91% | 18.75% | 29.67% | 0.595 |

These are **conditional model outputs**, not policy forecasts or causal estimates.

## Installation

Python 3.11+ is required. The frozen environment used for the current release is listed in `requirements.txt`.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
```

## Quick verification

```bash
python -m pytest -q
```

The release test suite checks stock-flow consistency, equity conservation, matched-payout equivalence, dilution arithmetic, money-demand behaviour, vesting and the 2027/2037/2077 calendar mapping.

For a quick end-to-end smoke run with a reduced sensitivity sample:

```bash
python scripts/reproduce_all.py --samples 8
```

## Reproduce the paper's full numerical experiment

```bash
python scripts/reproduce_all.py --samples 128
python -m pytest -q
```

To regenerate numerical results, figures, tables **and compile the bundled LaTeX manuscript and supplement**:

```bash
python scripts/reproduce_all.py --samples 128 --compile
```

A TeX distribution with `pdflatex`/`latexmk` is required only for the final command.

## Run one scenario

Edit a YAML file in `configs/` or copy `configs/baseline.yaml`, then run:

```bash
python scripts/run_scenario.py \
  --config configs/medium_ai.yaml \
  --policy B6 \
  --output results/custom/medium_B6
```

The trajectory includes both `year` and `calendar_year`.

## Policy codes

- **B0** targeted tax-transfer comparator
- **B1** no household transfer
- **B2** universal transfer + residual tax
- **B3** fiscal-dominant monetary transfer
- **B4** fiscal dominance + currency burn
- **B5** usownership + residual tax
- **B6** SSM/usownership hybrid
- **B7** equal citizen-equity comparator
- **B8** fixed money growth + usownership
- **B9** no-tax stress case
- **B10** capital-tilted tax + universal transfer
- **B11** matched dividend levy for B5
- **B12** matched levy for B6
- **B13** usownership + targeted income protection

## Repository map

```text
usownership-ai-transition/
├── src/ssm/model.py              # economic state transitions and accounting
├── configs/                      # frozen parameters and policy definitions
├── scripts/
│   ├── reproduce_all.py          # main reproduction pipeline
│   ├── run_comparisons.py        # matched fiscal / ownership counterfactuals
│   ├── run_scenario.py           # user-edited single-scenario runner
│   ├── make_figures.py
│   ├── make_workbook.py
│   └── compile_paper.py
├── tests/                        # accounting and regression checks
├── results/tables/               # frozen full-run CSV outputs
├── results/figures/              # generated figures
├── paper/                        # SCED manuscript + supplement + LaTeX sources
├── docs/                         # model scope, validation and source ledger
├── data/                         # public calibration anchors / metadata
└── notebooks/                    # lightweight exploration notebook
```

## Model status and limitations

The model is deliberately transparent rather than exhaustive. In particular, it does **not** contain a complete transition for commercial-bank credit, sovereign debt, international trade/capital flows, endogenous firm entry, market equity valuation or empirically estimated participation responses. It uses official macro anchors where documented, but household distributions and many behavioural coefficients are synthetic assumptions.

The model therefore asks **whether a mechanism can work under stated conditions**, not whether a specific country will follow the simulated path.

See `docs/RESEARCH_SCOPE_AND_GAPS.md`, `docs/VALIDATION.md` and the online supplement for details.

## Usownership terminology

The paper uses **usownership** for the generalized institution in which a user can progressively become an owner through recurring, contribution-weighted equity awards. The public code uses `usownership` / `usownership_share` consistently. Internal variables such as `use_share` refer to the participant dividend-income share and are not a second institutional concept.

## Reproducibility provenance

The bundled full-run CSVs derive from the verified 549-path numerical experiment used for the manuscript. Release v0.3.0 changes public terminology from `useownership` to `usownership` and maps model time onto a 2027 start date; it does not change the economic equations or frozen numerical values. A fresh reduced-sample end-to-end smoke run and the full unit/accounting test suite were executed after the refactor.

## Citation

See `CITATION.cff`. When the journal article receives a DOI, I'll update the preferred citation and archive the GitHub release with Zenodo or an equivalent repository to obtain a permanent software DOI.

## Licence

MIT
