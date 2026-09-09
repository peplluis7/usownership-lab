# Reproducibility protocol

## Frozen paper run

The paper reports a 549-path experiment:

- 30 main trajectories;
- 36 robustness trajectories;
- 384 sensitivity trajectories;
- 99 strengthened comparison trajectories.

Run:

```bash
python scripts/reproduce_all.py --samples 128
python -m pytest -q
```

## Fast local smoke run

```bash
python scripts/reproduce_all.py --samples 8
python -m pytest -q
```

The smoke run intentionally does not reproduce the paper's 128-point sensitivity design. It verifies that all modules, output writers, policy comparisons, matched-payout checks, figures and workbook generation execute together.

## Frozen numerical release

`results/tables/` contains the complete paper-run outputs. `results/csv_sha256.json` contains hashes of those tables. Version 0.3.0 changes terminology and calendar labels only; the economic core is unchanged from the verified full run.

## What must match

A valid reproduction should satisfy:

1. cash accounting residuals close to machine precision;
2. goods accounting residuals close to machine precision;
3. corporate equity conservation close to machine precision;
4. exact cash-flow equivalence for B5/B11 and B6/B12 under the matching assumptions;
5. central medium-AI year-50 outcomes within floating-point tolerance of the frozen release tables.
