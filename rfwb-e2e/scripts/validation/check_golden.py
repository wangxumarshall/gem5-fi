#!/usr/bin/env python3
"""Compare Control (or one sample's) OUT lines against the independent golden."""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys


def outs(path):
    if not os.path.exists(path):
        return None
    return [ln for ln in open(path, errors='ignore').read().splitlines()
            if ln.startswith('OUT ')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', required=True, help='control results root')
    ap.add_argument('--golden', required=True)
    ap.add_argument('--stdout-name', default='stdout.txt')
    ap.add_argument('--allow-partial', action='store_true')
    args = ap.parse_args()

    ok = bad = 0
    seen = set()
    for d in sorted(glob.glob(os.path.join(args.runs, 'CTRL-RFWB-*-RUN'))):
        name = os.path.basename(d)
        m = re.match(r'CTRL-RFWB-(M\d+)-(C\d+)-RUN$', name)
        if not m:
            continue
        model, ctx = m.groups()
        g = os.path.join(args.golden, f'{model}_{ctx}.txt')
        got = outs(os.path.join(d, args.stdout_name))
        want = outs(g)
        if got is None or want is None:
            print(f'FAIL: missing output/golden for {name}')
            bad += 1
            continue
        if got == want:
            print(f'PASS: {name} matches golden')
            ok += 1
            seen.add((model, ctx))
        else:
            print(f'FAIL: {name} differs from golden')
            bad += 1

    if not args.allow_partial:
        for model in ('M001', 'M002', 'M003', 'M004', 'M005'):
            for ctx in ('C01', 'C02', 'C03', 'C04', 'C05'):
                if (model, ctx) not in seen:
                    print(f'FAIL: missing Control {model} {ctx}')
                    bad += 1
        if ok != 25:
            print(f'FAIL: expected 25 Controls, got {ok}')
            bad += 1

    print(f'controls: {ok} match, {bad} failure(s)')
    raise SystemExit(1 if bad else 0)


if __name__ == '__main__':
    main()
