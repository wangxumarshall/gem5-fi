#!/usr/bin/env python3
"""Dry-run validation of the RF/WB final design and file set.

No gem5 run is performed.  This is the release's dependency/design gate:
models, contexts, timing plan, 75 Fault + 25 Control conditions, frozen
classification, patch, workloads, golden, and repository hygiene.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import math
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MODELS = ['M001', 'M002', 'M003', 'M004', 'M005']
CTX = ['C01', 'C02', 'C03', 'C04', 'C05']
TIM = ['T01', 'T02', 'T03']
FAIL = []
PASS = 0


def check(cond, msg):
    global PASS
    if cond:
        print('PASS:', msg)
        PASS += 1
    else:
        print('FAIL:', msg)
        FAIL.append(msg)


def load_tsv(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def ceil_ord(n, num, den):
    return (n * num + den - 1) // den


def main():
    # ---- targets / models / contexts ----
    targets = load_tsv(os.path.join(ROOT, 'configs', 'targets.tsv'))
    check(len(targets) == 25, f'targets.tsv has 25 rows (got {len(targets)})')
    check(len({(r['model'], r['context']) for r in targets}) == 25,
          'targets.tsv (model, context) keys are unique')
    for m in MODELS:
        rows = [r for r in targets if r['model'] == m]
        check(len(rows) == 5, f'{m} has 5 target rows')
        check({r['context'] for r in rows} == set(CTX), f'{m} covers C01..C05')
        for r in rows:
            check(r['workload'] == f'rfwb_0{m[-1]}', f'{m} {r["context"]} workload rfwb_0{m[-1]}')
            check(int(r['producer_pc'], 16) > 0, f'{m} {r["context"]} producer PC valid')
            if m in ('M001', 'M003', 'M005'):
                check(int(r['second_pc'], 16) > 0, f'{m} {r["context"]} second PC valid')
            else:
                check(r['second_pc'] == '0x0', f'{m} {r["context"]} second PC unused')

    models = load_tsv(os.path.join(ROOT, 'configs', 'fault_models', 'models.tsv'))
    check([r['model'] for r in models] == MODELS, 'models.tsv lists M001..M005 in order')
    ctxrows = load_tsv(os.path.join(ROOT, 'configs', 'contexts', 'contexts.tsv'))
    check(len(ctxrows) == 25, 'contexts.tsv has 25 rows')

    # ---- workloads / golden ----
    srcs = sorted(glob.glob(os.path.join(ROOT, 'workloads', 'source', 'rfwb_0*.c')))
    asms = sorted(glob.glob(os.path.join(ROOT, 'workloads', 'source', 'rfwb_0*.S')))
    check(len(srcs) == 5 and len(asms) == 5, 'five .c and five .S workload sources')
    check(len(glob.glob(os.path.join(ROOT, 'golden', 'M*_C0*.txt'))) == 25,
          '25 golden files')

    freeze = {}
    for r in load_tsv(os.path.join(ROOT, 'manifests', 'source_freeze_manifest.tsv')):
        freeze[r['Key']] = r['PathOrValue'], r['SHA256_or_Value']
    for i in range(1, 6):
        base = os.path.join(ROOT, 'workloads', 'build', f'rfwb_0{i}')
        check(os.path.isfile(base), f'base ELF rfwb_0{i} exists')
        check(sha256(base) == freeze[f'Workload0{i}ELF'][1],
              f'base ELF rfwb_0{i} matches freeze manifest SHA256')
        for c in range(1, 6):
            link = os.path.join(ROOT, 'workloads', 'build', f'rfwb_0{i}_C0{c}')
            check(os.path.islink(link), f'{os.path.basename(link)} is a symlink')
            if os.path.islink(link):
                check(os.readlink(link) == f'rfwb_0{i}', f'{os.path.basename(link)} -> rfwb_0{i}')
                check(sha256(link) == sha256(base), f'{os.path.basename(link)} equals base ELF')

    # ---- timing plan ----
    plan = load_tsv(os.path.join(ROOT, 'configs', 'timing', 'frozen_timing_plan.tsv'))
    check(len(plan) == 25, f'timing plan has 25 rows (got {len(plan)})')
    p = {(r['model'], r['context']): r for r in plan}
    for m in MODELS:
        for c in CTX:
            r = p.get((m, c))
            check(r is not None, f'timing plan has {m} {c}')
            if not r:
                continue
            n = int(r['N'])
            check(r['status'] == 'PASS', f'{m} {c} timing PASS')
            check(n >= 3, f'{m} {c} N>=3')
            want = [ceil_ord(n, 1, 10), ceil_ord(n, 5, 10), ceil_ord(n, 9, 10)]
            check([int(r['T01']), int(r['T02']), int(r['T03'])] == want,
                  f'{m} {c} ordinals are ceil(10/50/90% of N)')
            for tim in TIM:
                check(bool(r[f'sample_id_{tim}']), f'{m} {c} {tim} sample id present')
                if m == 'M005':
                    check(bool(r[f'target_seq_{tim}']), f'M005 {c} {tim} target seq present')
    for c, want_n, want_o in (
            ('C01', 6, (1, 3, 6)), ('C02', 6, (1, 3, 6)), ('C03', 8, (1, 4, 8)),
            ('C04', 6, (1, 3, 6)), ('C05', 8, (1, 4, 8))):
        r = p[('M005', c)]
        check(int(r['N']) == want_n, f'M005 {c} corrected N={want_n}')
        check((int(r['T01']), int(r['T02']), int(r['T03'])) == want_o,
              f'M005 {c} corrected ordinals {want_o}')

    corr = load_tsv(os.path.join(ROOT, 'configs', 'timing', 'corrected_prescan_summary.tsv'))
    check(len(corr) == 5, 'corrected_prescan_summary.tsv has 5 M005 rows')
    for r in corr:
        q = p[('M005', r['context'])]
        check((r['N'], r['T01'], r['T02'], r['T03']) ==
              (q['N'], q['T01'], q['T02'], q['T03']),
              f'M005 {r["context"]} frozen timing equals corrected summary')

    smap = load_tsv(os.path.join(ROOT, 'configs', 'timing', 'evidence_sample_ids.tsv'))
    check(len(smap) == 75, 'evidence_sample_ids.tsv has 75 rows')
    for r in smap:
        q = p[(r['model'], r['context'])]
        check(q[f'sample_id_{r["timing"]}'] == r['sample_id'],
              f'{r["model"]} {r["context"]} {r["timing"]} sample id matches map')

    # ---- 75 Fault + 25 Control ----
    cond = load_tsv(os.path.join(ROOT, 'manifests', 'experiment_conditions.tsv'))
    fault = [r for r in cond if r['record_type'] == 'Fault']
    ctrl = [r for r in cond if r['record_type'] == 'Control']
    check(len(fault) == 75, f'75 Fault conditions (got {len(fault)})')
    check(len(ctrl) == 25, f'25 Control conditions (got {len(ctrl)})')
    check(len({r['sample_id'] for r in cond}) == 100, 'all 100 sample ids unique')
    for m in MODELS:
        for c in CTX:
            keys = {(r['model'], r['context'], r['timing']) for r in fault}
            for tim in TIM:
                check((m, c, tim) in keys, f'Fault condition {m} {c} {tim} present')
            check(sum(1 for r in ctrl if r['model'] == m and r['context'] == c) == 1,
                  f'Control {m} {c} present once')
    for r in fault:
        q = p[(r['model'], r['context'])]
        check(r['ordinal'] == q[r['timing']], f'{r["sample_id"]} ordinal matches plan')
        if r['model'] == 'M005':
            check(r['target_seq'] == q[f'target_seq_{r["timing"]}'],
                  f'{r["sample_id"]} target seq matches plan')
    exp = load_tsv(os.path.join(ROOT, 'configs', 'fault_models', 'frozen_classification.tsv'))
    check(len(exp) == 75, 'frozen classification has 75 rows')
    counts = {}
    for r in exp:
        counts[r['class']] = counts.get(r['class'], 0) + 1
    check(counts.get('ACTIVATED_SDC') == 32, 'frozen SDC=32')
    check(counts.get('ACTIVATED_MASKED') == 28, 'frozen MASKED=28')
    check(counts.get('ACTIVATED_SQUASHED') == 2, 'frozen SQUASHED=2')
    check(counts.get('ROB_HEAD_BLOCKED') == 13, 'frozen ROB_HEAD_BLOCKED=13')
    ekey = {(r['model'], r['context'], r['timing']): r['class'] for r in exp}
    for r in fault:
        check(r['expected_class'] == ekey[(r['model'], r['context'], r['timing'])],
              f'{r["sample_id"]} expected class matches frozen table')

    # ---- patch / source ----
    patch = os.path.join(ROOT, 'src', 'RF_WB_Source_Injection_Final.patch')
    check(os.path.isfile(patch), 'RF/WB patch exists')
    check(sha256(patch) == '87c8968fe1e555db97fc8b5e735e6e975fdafa1e9f867732789d9e5822f8e60a',
          'patch SHA256 matches the frozen manifest')
    pfiles = [l.split()[2][2:] for l in open(patch) if l.startswith('diff --git ')]
    check(len(pfiles) == 12, f'patch touches 12 files (got {len(pfiles)})')
    check('CHAOS/gem5/src/cpu/o3/rfwb.cc' in pfiles, 'patch adds rfwb.cc')
    check('CHAOS/gem5/src/cpu/o3/rfwb.hh' in pfiles, 'patch adds rfwb.hh')
    for f in ('rfwb.cc', 'rfwb.hh'):
        check(os.path.isfile(os.path.join(ROOT, 'src', 'rfwb', f)), f'src/rfwb/{f} exists')
    cc = open(os.path.join(ROOT, 'src', 'rfwb', 'rfwb.cc')).read()
    for ev in ('M001_INJECT', 'M002_COMMIT', 'M003_INJECT',
               'M004_SKIP_INSTTOCOMMIT', 'M005_SKIP_GLOBAL_READY',
               'RFWB_TARGET_SEQ'):
        check(ev in cc, f'rfwb.cc contains {ev}')
    base = open(os.path.join(ROOT, 'manifests', 'source_baseline.txt')).read()
    check('2f4e00b434ec8690fbb8cb6965e435094de7e784' in base, 'source baseline commit recorded')
    check('f34ae2d1e8f002c03e919218ef4f2c00e40b0a95' in base, 'source tree recorded')

    # ---- reports ----
    for m in MODELS:
        rp = os.path.join(ROOT, 'reports', f'RF_WB_{m}_Propagation_Report.md')
        check(os.path.isfile(rp), f'{m} propagation report exists')
        if os.path.isfile(rp):
            t = open(rp).read()
            check(len(re.findall(r'^#### C0[1-5]-T0[1-3]', t, re.M)) == 15,
                  f'{m} report has 15 chains')
    check(os.path.isfile(os.path.join(ROOT, 'reports', 'RF_WB_Overall_Experiment_Summary.md')),
          'overall summary exists')

    # ---- hygiene ----
    check(os.path.isfile(os.path.join(ROOT, 'README.md')), 'README.md exists')
    readme = open(os.path.join(ROOT, 'README.md')).read() if os.path.exists(os.path.join(ROOT, 'README.md')) else ''
    check('reproduction/reproduce_all.sh' in readme, 'README references reproduce_all.sh')
    bad = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if '/runs' in dirpath or dirpath.endswith('/runs'):
            continue
        for name in filenames:
            pth = os.path.join(dirpath, name)
            if name.endswith(('.o', '.pyc', '.pyo')) or name == '__pycache__':
                bad.append(pth)
            try:
                if os.path.getsize(pth) > 20 * 1024 * 1024:
                    bad.append(pth + ' (>20MB)')
            except OSError:
                pass
    check(not bad, f'no build caches or >20MB files (bad: {bad[:5]})')
    hard = []
    workdir_literal = '/'.join(['', 'home', 'sdc', 'gem5-fi-RF_WB'])
    for pth in (glob.glob(os.path.join(ROOT, 'scripts', '**', '*.sh'), recursive=True) +
                glob.glob(os.path.join(ROOT, 'scripts', '**', '*.py'), recursive=True) +
                glob.glob(os.path.join(ROOT, 'reproduction', '*'))):
        try:
            t = open(pth, errors='ignore').read()
        except (OSError, UnicodeDecodeError):
            continue
        if workdir_literal in t:
            hard.append(os.path.relpath(pth, ROOT))
    check(not hard, f'no hard-coded workdir paths in scripts (bad: {hard})')
    for d in ('Batch01', 'Batch02_traces', 'Batch02_results', 'Batch03_traces',
              'Batch03_results', 'results', 'traces', '.v5_stage', 'source'):
        check(not os.path.exists(os.path.join(ROOT, d)), f'no evidence/build dir {d}')

    if FAIL:
        print(f'\n{PASS} passed, {len(FAIL)} failed')
        raise SystemExit(1)
    print(f'\nALL DESIGN CHECKS PASSED ({PASS})')


if __name__ == '__main__':
    main()
