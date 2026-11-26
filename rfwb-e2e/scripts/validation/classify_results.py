#!/usr/bin/env python3
"""Classify RF/WB Fault samples using the frozen classification order.

Inputs:
  --runs     directory containing RFWB-* fault dirs and CTRL-RFWB-*-RUN dirs
  --traces   directory containing the matching RFWB-*.csv traces
  --expected optional frozen fault_classification.tsv (75 rows)
  --out      output TSV

The decision order is intentionally identical to the frozen evidence pipeline:
  injected==0 -> NOT_ACTIVATED
  M004 same-seq squash -> ACTIVATED_SQUASHED
  M004 not ROI_DONE -> ROB_HEAD_BLOCKED
  OUT == Control OUT -> ACTIVATED_MASKED
  no ROI_DONE -> ACTIVATED_NO_PROGRESS
  otherwise -> ACTIVATED_SDC
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import re
import sys

INJECT_EVENTS = {'M001_INJECT', 'M002_COMMIT', 'M003_INJECT',
                 'M004_SKIP_INSTTOCOMMIT', 'M005_SKIP_GLOBAL_READY'}


def outs(text):
    return [l for l in text.splitlines() if l.startswith('OUT ')]


def classify_one(sample, model, ctx, timing, run_dir, trace_path, ctrl_stdout):
    so = open(os.path.join(run_dir, 'stdout.txt'), errors='ignore').read() \
        if os.path.exists(os.path.join(run_dir, 'stdout.txt')) else ''
    sc = open(ctrl_stdout, errors='ignore').read() if os.path.exists(ctrl_stdout) else ''
    done = 'ROI_DONE' in so
    same = outs(so) == outs(sc) and done

    injected = 0
    events = 0
    skip_seq = None
    squash_same_seq = False
    if os.path.exists(trace_path):
        with open(trace_path, newline='') as f:
            for r in csv.DictReader(f):
                ev = r.get('event', '')
                if ev:
                    events += 1
                if ev in INJECT_EVENTS or ev.endswith('INJECT'):
                    injected += 1
                if ev == 'M004_SKIP_INSTTOCOMMIT':
                    skip_seq = r.get('seq')
                if (ev == 'M004_SQUASH' and skip_seq is not None
                        and r.get('seq') == skip_seq):
                    squash_same_seq = True

    if not done:
        terminal = ('NO_RETIREMENT_PROGRESS_BY_MAX_TICKS' if model == 'M004'
                    else 'NO_ROI_DONE/TIMEOUT_OR_HANG')
    elif not same:
        terminal = 'WRONG_ANSWER'
    else:
        terminal = 'MATCH_CONTROL'

    if injected == 0:
        cls = 'NOT_ACTIVATED'
    elif model == 'M004' and squash_same_seq:
        terminal = 'SQUASHED'
        cls = 'ACTIVATED_SQUASHED'
    elif model == 'M004' and not done:
        cls = 'ROB_HEAD_BLOCKED'
    elif terminal == 'MATCH_CONTROL':
        cls = 'ACTIVATED_MASKED'
    elif terminal.startswith('NO_ROI'):
        cls = 'ACTIVATED_NO_PROGRESS'
    else:
        cls = 'ACTIVATED_SDC'
    return [sample, model, ctx, timing, injected, events, terminal, cls]


def key(model, ctx, timing):
    return (model, ctx, timing)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', required=True)
    ap.add_argument('--traces', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--expected', default='')
    ap.add_argument('--allow-partial', action='store_true')
    args = ap.parse_args()

    rows = []
    for d in sorted(glob.glob(os.path.join(args.runs, 'RFWB-*'))):
        sample = os.path.basename(d)
        if not os.path.isdir(d):
            continue
        m = re.match(r'RFWB-(M\d+)-(C\d+)-(T\d+)-F0(?:-A\d+)?$', sample)
        if not m:
            continue
        model, ctx, timing = m.groups()
        ctrl = os.path.join(args.runs, f'CTRL-RFWB-{model}-{ctx}-RUN', 'stdout.txt')
        trace = os.path.join(args.traces, sample + '.csv')
        rows.append(classify_one(sample, model, ctx, timing, d, trace, ctrl))

    with open(args.out, 'w', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n')
        w.writerow(['sample', 'model', 'context', 'timing',
                    'injected_events', 'trace_events', 'terminal', 'class'])
        w.writerows(rows)

    counts = {}
    for r in rows:
        counts[r[7]] = counts.get(r[7], 0) + 1
    for r in rows:
        print('\t'.join(map(str, r)))
    print('counts:', counts)

    bad = 0
    if not args.allow_partial and len(rows) != 75:
        print(f'FAIL: expected 75 fault samples, got {len(rows)}')
        bad += 1
    if args.expected:
        exp = {}
        with open(args.expected, newline='') as f:
            for r in csv.DictReader(f, delimiter='\t'):
                exp[key(r['model'], r['context'], r['timing'])] = r['class']
        for r in rows:
            k = key(r[1], r[2], r[3])
            if k not in exp:
                print(f'FAIL: no expected class for {k}')
                bad += 1
            elif exp[k] != r[7]:
                print(f'FAIL: {k} class {r[7]} != frozen {exp[k]}')
                bad += 1
        if not args.allow_partial and len(exp) != 75:
            print(f'FAIL: expected table has {len(exp)} rows, want 75')
            bad += 1
    raise SystemExit(1 if bad else 0)


if __name__ == '__main__':
    main()
