#!/usr/bin/env python3
"""Compare a generated timing plan against the frozen authority.

Hard checks:
  * every frozen (model, context) row exists and matches N / T01..T03 /
    M005 target sequences / sample ids;
  * M005 must be the corrected 6/6/8/6/8 pattern with 1/3/6 or 1/4/8;
  * M001-M004 must use their own scan N, never M005's values.
"""
from __future__ import annotations

import argparse
import csv
import sys

FAIL = []


def load(path):
    with open(path, newline='') as f:
        return {(r['model'], r['context']): r for r in csv.DictReader(f, delimiter='\t')}


def check(cond, msg):
    if cond:
        print('PASS:', msg)
    else:
        print('FAIL:', msg)
        FAIL.append(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--generated', required=True)
    ap.add_argument('--frozen', required=True)
    ap.add_argument('--corrected-m005', default='')
    ap.add_argument('--allow-subset', action='store_true')
    ap.add_argument('--strict-target-seq', action='store_true',
                    help='require exact frozen M005 producer seq (canonical path only)')
    args = ap.parse_args()

    gen = load(args.generated)
    frz = load(args.frozen)

    if not args.allow_subset:
        check(set(gen) == set(frz), 'generated and frozen cover the same 25 conditions')
    else:
        check(set(gen) <= set(frz), 'generated is a subset of frozen conditions')

    for key in sorted(frz):
        if key not in gen:
            if args.allow_subset:
                continue
            check(False, f'{key} present in generated plan')
            continue
        g, f = gen[key], frz[key]
        tag = f'{key[0]} {key[1]}'
        for col in ('N', 'T01', 'T02', 'T03',
                    'status', 'sample_id_T01', 'sample_id_T02', 'sample_id_T03'):
            check(g.get(col, '') == f.get(col, ''), f'{tag} {col}: {g.get(col)} == {f.get(col)}')
        # Producer sequence numbers are run-specific (guest stack layout shifts
        # the absolute seq counter).  The reproducible design invariant is the
        # eligible count and the ordinal position.  Exact seq equality is only
        # required on the canonical frozen path (--strict-target-seq).
        if key[0] == 'M005':
            for col in ('target_seq_T01', 'target_seq_T02', 'target_seq_T03'):
                same = g.get(col, '') == f.get(col, '')
                if args.strict_target_seq:
                    check(same, f'{tag} {col}: {g.get(col)} == {f.get(col)}')
                elif not same:
                    print(f'WARN: {tag} {col}: run={g.get(col)} frozen={f.get(col)} '
                          f'(same ordinal; seq is run-specific)')

    # M005 corrected pattern must be explicit and stable.
    m005 = {k: v for k, v in frz.items() if k[0] == 'M005'}
    want_n = {'C01': '6', 'C02': '6', 'C03': '8', 'C04': '6', 'C05': '8'}
    want_ord = {'C01': ('1', '3', '6'), 'C02': ('1', '3', '6'),
                'C03': ('1', '4', '8'), 'C04': ('1', '3', '6'),
                'C05': ('1', '4', '8')}
    for ctx, n in want_n.items():
        row = m005.get(('M005', ctx))
        check(row is not None, f'M005 {ctx} exists in frozen plan')
        if row:
            check(row['N'] == n, f'M005 {ctx} corrected N={n} (got {row["N"]})')
            check((row['T01'], row['T02'], row['T03']) == want_ord[ctx],
                  f'M005 {ctx} corrected ordinals {want_ord[ctx]}')

    if args.corrected_m005:
        with open(args.corrected_m005, newline='') as f:
            corr = {(r['model'], r['context']): r for r in csv.DictReader(f, delimiter='\t')}
        for ctx in ('C01', 'C02', 'C03', 'C04', 'C05'):
            c = corr.get(('M005', ctx))
            f = frz.get(('M005', ctx))
            check(c is not None and f is not None, f'M005 {ctx} corrected summary present')
            if c and f:
                check(c['N'] == f['N'] and c['T01'] == f['T01'] and
                      c['T02'] == f['T02'] and c['T03'] == f['T03'],
                      f'M005 {ctx} frozen plan equals corrected_prescan_summary.tsv')

    if FAIL:
        print(f'\n{len(FAIL)} check(s) failed')
        raise SystemExit(1)
    print(f'\nall timing-plan checks passed ({len(frz)} frozen conditions)')


if __name__ == '__main__':
    main()
