#!/usr/bin/env python3
"""Run a user-edited parameter YAML without overwriting frozen paper configs."""
import argparse
from dataclasses import fields
from pathlib import Path
import sys
import yaml
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from ssm.model import Parameters, POLICIES, simulate
from run_comparisons import COMPARISON_POLICIES
ALL_POLICIES = {**POLICIES, **COMPARISON_POLICIES}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/baseline.yaml')
    parser.add_argument('--policy', choices=ALL_POLICIES, default='B6')
    parser.add_argument('--output', type=Path, default=ROOT / 'results/custom')
    args = parser.parse_args()
    values = yaml.safe_load(args.config.read_text())
    if not isinstance(values, dict):
        raise SystemExit('The config must contain a mapping of Parameters fields.')
    unknown = set(values) - {f.name for f in fields(Parameters)}
    if unknown:
        raise SystemExit('Unknown parameter names: ' + ', '.join(sorted(unknown)))
    path, people = simulate(Parameters(**values), ALL_POLICIES[args.policy])
    args.output.mkdir(parents=True, exist_ok=True)
    path.to_csv(args.output / 'trajectory.csv', index=False)
    people.to_csv(args.output / 'terminal_agents.csv', index=False)
    print(path.tail(1).to_string(index=False))
    print('Saved results to', args.output)

if __name__ == '__main__':
    main()
