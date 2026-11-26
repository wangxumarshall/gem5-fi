#!/usr/bin/env python3
"""Validate an executed RF/WB run set against the frozen plan and expectation.

Checks:
  * every planned (model, context, timing) sample exists with a trace;
  * every Fault trace has exactly one injection event;
  * non-M005 injection ordinal == plan ordinal;
    M005 injection producer seq == plan target sequence;
  * every gem5 index rc == 0;
  * every Control matches golden;
  * classification reproduces the frozen class table.

Use --allow-partial after a Smoke run (it checks only samples that exist).
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import re
import subprocess
import sys

INJ = {
    'M001': 'M001_INJECT',
    'M002': 'M002_COMMIT',
    'M003': 'M003_INJECT',
    'M004': 'M004_SKIP_INSTTOCOMMIT',
    'M005': 'M005_SKIP_GLOBAL_READY',
}
MODELS = ['M001', 'M002', 'M003', 'M004', 'M005']
CTX = ['C01', 'C02', 'C03', 'C04', 'C05']
FAIL = []


def check(cond, msg):
    print(('PASS: ' if cond else 'FAIL: ') + msg)
    if not cond:
        FAIL.append(msg)


def load_plan(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def trace_events(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, newline='') as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', required=True)
    ap.add_argument('--traces', default='')
    ap.add_argument('--plan', required=True)
    ap.add_argument('--expected', default='')
    ap.add_argument('--golden', required=True)
    ap.add_argument('--allow-partial', action='store_true')
    ap.add_argument('--skip-classify', action='store_true')
    args = ap.parse_args()
    traces = args.traces or os.path.join(args.runs, '..', 'traces')
    traces = os.path.abspath(traces)
    plan = load_plan(args.plan)
    if args.allow_partial:
        check(0 < len(plan) <= 25, f'partial plan has 1..25 rows (got {len(plan)})')
    else:
        check(len(plan) == 25, f'plan has 25 model/context rows (got {len(plan)})')

    expected = {}
    if args.expected:
        with open(args.expected, newline='') as f:
            for r in csv.DictReader(f, delimiter='\t'):
                expected[(r['model'], r['context'], r['timing'])] = r['class']

    present = 0
    missing = 0
    for row in plan:
        model, ctx = row['model'], row['context']
        for tim in ('T01', 'T02', 'T03'):
            sid = row[f'sample_id_{tim}']
            d = os.path.join(args.runs, sid)
            tr = os.path.join(traces, sid + '.csv')
            exists = os.path.isdir(d) and os.path.exists(tr)
            if not exists:
                missing += 1
                if not args.allow_partial:
                    check(False, f'{sid} result dir and trace exist')
                continue
            present += 1
            check(True, f'{sid} result dir and trace exist')
            evs = trace_events(tr)
            inj = [e for e in evs if e.get('event') == INJ[model]]
            check(len(inj) == 1, f'{sid} has exactly one {INJ[model]} event (got {len(inj)})')
            if len(inj) == 1:
                e = inj[0]
                if model == 'M005':
                    want = row[f'target_seq_{tim}']
                    check(want != '' and e.get('seq') == want,
                          f'{sid} injected producer seq {e.get("seq")} == {want}')
                else:
                    want = row[tim]
                    check(e.get('ordinal') == want,
                          f'{sid} injected ordinal {e.get("ordinal")} == {want}')

    # Controls: every present control must match golden.
    controls = 0
    for d in sorted(glob.glob(os.path.join(args.runs, 'CTRL-RFWB-*-RUN'))):
        name = os.path.basename(d)
        m = re.match(r'CTRL-RFWB-(M\d+)-(C\d+)-RUN$', name)
        if not m:
            continue
        controls += 1
        model, ctx = m.groups()
        got = [l for l in open(os.path.join(d, 'stdout.txt'), errors='ignore').read().splitlines()
               if l.startswith('OUT ')] if os.path.exists(os.path.join(d, 'stdout.txt')) else None
        g = os.path.join(args.golden, f'{model}_{ctx}.txt')
        want = [l for l in open(g).read().splitlines() if l.startswith('OUT ')] if os.path.exists(g) else None
        check(got is not None and want is not None and got == want,
              f'{name} matches golden')

    if not args.allow_partial:
        check(present == 75, f'75 Fault samples present (got {present})')
        check(missing == 0, f'no missing Fault samples (got {missing})')
        check(controls == 25, f'25 Controls present (got {controls})')
        counts = {}
        if args.expected:
            for c in expected.values():
                counts[c] = counts.get(c, 0) + 1
            check(counts.get('ACTIVATED_SDC') == 32, 'expected SDC=32')
            check(counts.get('ACTIVATED_MASKED') == 28, 'expected MASKED=28')
            check(counts.get('ACTIVATED_SQUASHED') == 2, 'expected SQUASHED=2')
            check(counts.get('ROB_HEAD_BLOCKED') == 13, 'expected ROB_HEAD_BLOCKED=13')
    else:
        print(f'PARTIAL: present={present}, missing={missing}, controls={controls}')

    # gem5 return codes from the index, when present.
    idx = os.path.join(args.runs, 'index.tsv')
    if os.path.exists(idx):
        badrc = []
        with open(idx, newline='') as f:
            for r in csv.DictReader(f, delimiter='\t'):
                try:
                    rc = int(r.get('rc', '0'))
                except ValueError:
                    rc = 1
                if rc != 0:
                    badrc.append((r.get('sample'), rc))
        check(not badrc, f'all gem5 return codes are 0 (bad: {badrc[:5]})')

    if not args.skip_classify and present:
        out = os.path.join(args.runs, 'fault_classification.tsv')
        cmd = [sys.executable, os.path.join(os.path.dirname(__file__), 'classify_results.py'),
               '--runs', args.runs, '--traces', traces, '--out', out]
        if args.expected:
            cmd += ['--expected', args.expected]
        if args.allow_partial:
            cmd += ['--allow-partial']
        print('CLASSIFY:', ' '.join(cmd))
        rc = subprocess.call(cmd)
        check(rc == 0, 'classification matches frozen table')
    elif args.skip_classify:
        print('SKIP: classification (--skip-classify)')

    if FAIL:
        print(f'\n{len(FAIL)} failure(s)')
        raise SystemExit(1)
    print('\nall result checks passed')


if __name__ == '__main__':
    main()
