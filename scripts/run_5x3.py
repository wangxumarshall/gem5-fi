#!/usr/bin/env python3
"""FPU/SIMD 5x3 formal experiment orchestration.

Authoritative design: inputs/gem5-fi-FPU_SIMD-Final-Paper-Experiment-Plan.xlsx
sheets 24..29.  This driver implements:
  count   : count-only pre-scan of the 60 (ModelID,ContextID) combos -> manifest
  formal  : 180 fault runs (12x5x3) + 60 control baselines (12x5)
  validate: completeness + integrity + fault/control pairing + propagation
            evidence check

All output goes to work/FPU_SIMD_5x3_FORMAL/ (isolated from historical data).
"""
import argparse, concurrent.futures, csv, hashlib, json, os, re, subprocess
import sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEM5 = ROOT / 'gem5/build/ARM/gem5.opt'
CONFIG = ROOT / 'gem5/configs/deprecated/example/se.py'
WL = ROOT / 'work/FPU_SIMD_5x3_FORMAL/workloads/build'
BASE = ROOT / 'work/FPU_SIMD_5x3_FORMAL'
COUNTS = BASE / 'counts'
RUNS = BASE / 'runs'
MAGIC = 0x3149554650465046

# lane per model (R03 anchor): scalar/fcmp -1; SIMD target lane
LANE = {i: -1 for i in range(1, 13)}
LANE.update({8: 7, 9: 3, 10: 7, 11: 7})

CONTEXTS = ['C01', 'C02', 'C03', 'C04', 'C05']
TIMINGS = {'T01': 10, 'T02': 50, 'T03': 90}


def sh(cmd):
    return subprocess.check_output(cmd, text=True)


def target_pc(model, ctx):
    elf = WL / ('fpu_%02d_%s' % (model, ctx))
    for line in sh(['nm', str(elf)]).splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[-1] == 'fpu_target_r':
            return int(parts[0], 16)
    raise RuntimeError('no fpu_target_r in %s' % elf)


def parse_records(path):
    try:
        b = Path(path).read_bytes()
    except OSError:
        return []
    out, i = [], 0
    magic = MAGIC.to_bytes(8, 'little')
    while True:
        i = b.find(magic, i)
        if i < 0 or i + 128 > len(b):
            break
        v = list(int.from_bytes(b[i + 8 * k:i + 8 * k + 8], 'little') for k in range(16))
        out.append(dict(model=v[1], ctx=v[2], mode=v[3], it=v[4], raw0=v[5],
                        raw1=v[6], fpsr=v[7], fpcr=v[8], nzcv=v[9], lane=v[10],
                        status=v[11], raw2=v[12], qc=v[13]))
        i += 128
    return out


def parse_events(path):
    ev = []
    try:
        for line in open(path):
            line = line.strip()
            if line.startswith('{'):
                try:
                    ev.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return ev


def run_one(model, ctx, timing, fault, count_only, ordinal):
    """Run a single gem5 invocation. timing None -> control baseline."""
    sid = ('FPU-M%03d-%s-%s' % (model, ctx, timing)) if timing else \
          ('CTRL-FPU-M%03d-%s' % (model, ctx))
    if count_only:
        rdir = COUNTS / ('M%03d_%s' % (model, ctx))
    else:
        rdir = RUNS / sid
    rdir.mkdir(parents=True, exist_ok=True)
    trace_path = rdir / 'events.jsonl'
    pc = target_pc(model, ctx)
    env = os.environ.copy()
    env.update({
        'FI_ENABLE': '1' if (fault and not count_only) else '0',
        'FI_COUNT_ONLY': '1' if count_only else '0',
        'FI_MODEL': 'M%03d' % model,
        'FI_PC': hex(pc),
        'FI_ORDINAL': str(ordinal),
        'FI_LANE': str(LANE[model]),
        'FI_TRACE': str(trace_path),
        'FI_SAMPLE': sid,
        'FI_PAIR': ('FPU-M%03d-%s' % (model, ctx)),
        'FI_CONTEXT': ctx,
        'FI_MODE': '5x3',
        'FI_STATE': ('SPEC_EXEC_SQUASH' if ctx == 'C05' else 'NORMAL_COMMIT'),
    })
    cmd = [str(GEM5), '--outdir=%s' % rdir, str(CONFIG),
           '--cpu-type=DerivO3CPU', '--caches', '--mem-type=SimpleMemory',
           '--cmd=%s' % (WL / ('fpu_%02d_%s' % (model, ctx)))]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, env=env, stdout=open(rdir / 'stdout.txt', 'wb'),
                           stderr=open(rdir / 'stderr.txt', 'wb'), timeout=300)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        rc = 124
    ev = parse_events(trace_path)
    re_ = list(parse_records(rdir / 'stdout.txt'))
    eligible = max((e.get('eligible_total', 0) for e in ev if e.get('event') == 'run_end'),
                   default=0)
    applied = max((e.get('applied_total', 0) for e in ev if e.get('event') == 'run_end'),
                  default=0)
    tb = [e for e in ev if e.get('event') == 'target_begin']
    te = [e for e in ev if e.get('event') == 'target_end']
    sq = [e for e in ev if e.get('event') == 'squash']
    bm = [e for e in ev if e.get('event') == 'branch_mispredict']
    summary = dict(sid=sid, model=model, ctx=ctx, timing=timing, fault=bool(fault),
                   count_only=count_only, ordinal=ordinal, pc=pc,
                   exit_code=rc, elapsed=round(time.time() - t0, 3),
                   eligible=eligible, applied=applied,
                   n_target_begin=len(tb), n_target_end=len(te),
                   n_squash=len(sq), n_mispredict=len(bm),
                   n_records=len(re_), run_dir=str(rdir))
    (rdir / 'summary.json').write_text(json.dumps(summary, indent=2))
    return summary


def load_manifest():
    """12 models x 5 contexts (fault matrix 180 + control baselines 60)."""
    pairs = []
    for model in range(1, 13):
        for c in CONTEXTS:
            for t in TIMINGS:
                pairs.append(dict(model=model, ctx=c, timing=t, kind='fault'))
            pairs.append(dict(model=model, ctx=c, timing=None, kind='control'))
    return pairs


def count_stage(workers=6):
    jobs = [(m, c) for m in range(1, 13) for c in CONTEXTS]
    rows = []
    futs = {}

    def one(m, c):
        return run_one(m, c, None, False, True, 1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        for m, c in jobs:
            futs[ex.submit(one, m, c)] = (m, c)
        for fu in concurrent.futures.as_completed(futs):
            m, c = futs[fu]
            try:
                s = fu.result()
            except Exception as e:
                rows.append(dict(model=m, ctx=c, N=None, status='ERROR',
                                 reason=repr(e)))
                print('COUNT ERROR M%03d %s: %r' % (m, c, e), flush=True)
                continue
            n = s['eligible']
            qs = {t: (n * q + 99) // 100 for t, q in TIMINGS.items()}
            distinct = len(set(qs.values())) == 3 and n >= 3
            rows.append(dict(model=m, ctx=c, N=n, q10=qs['T01'], q50=qs['T02'],
                             q90=qs['T03'], distinct=distinct,
                             status=('READY' if distinct else 'BLOCKED'),
                             n_squash=s['n_squash'], n_mispredict=s['n_mispredict'],
                             pc=hex(s['pc']), n_records=s['n_records'],
                             exit_code=s['exit_code']))
            print('COUNT M%03d %s N=%d ordinal=%s/%s/%s %s' %
                  (m, c, n, qs['T01'], qs['T02'], qs['T03'],
                   'READY' if distinct else 'BLOCKED'), flush=True)
    with open(BASE / 'FPU_5x3_CountOnly_Manifest.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['model', 'ctx', 'N', 'q10', 'q50',
                                          'q90', 'distinct', 'status', 'n_squash',
                                          'n_mispredict', 'pc', 'n_records',
                                          'exit_code'])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    (COUNTS / 'manifest.json').write_text(json.dumps(rows, indent=2))
    return rows


def formal_stage(limit=None, workers=8, skip_existing=True):
    manifest = json.loads((COUNTS / 'manifest.json').read_text())
    by = {(r['model'], r['ctx']): r for r in manifest}
    jobs = []
    for p in load_manifest():
        r = by[(p['model'], p['ctx'])]
        if r['status'] != 'READY':
            continue
        if p['kind'] == 'fault':
            q = {'T01': r['q10'], 'T02': r['q50'], 'T03': r['q90']}[p['timing']]
            jobs.append(dict(model=p['model'], ctx=p['ctx'], timing=p['timing'],
                             fault=True, ordinal=q))
        else:
            jobs.append(dict(model=p['model'], ctx=p['ctx'], timing=None,
                             fault=False, ordinal=1))
    if limit:
        jobs = jobs[:limit]
    ok, fail = 0, []

    def one(j):
        sid = ('FPU-M%03d-%s-%s' % (j['model'], j['ctx'], j['timing'])) \
            if j['timing'] else ('CTRL-FPU-M%03d-%s' % (j['model'], j['ctx']))
        sp = RUNS / sid / 'summary.json'
        if skip_existing and sp.exists():
            s = json.loads(sp.read_text())
            if s.get('exit_code') == 0:
                return s
        return run_one(j['model'], j['ctx'], j['timing'], j['fault'], False,
                       j['ordinal'])

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for i, fu in enumerate(concurrent.futures.as_completed(futs), 1):
            j = futs[fu]
            try:
                s = fu.result()
                kind = 'FAULT' if j['fault'] else 'CTRL '
                print('RUN %3d/%d %s %s rc=%d appl=%d N=%d' %
                      (i, len(futs), kind, s['sid'], s['exit_code'],
                       s['applied'], s['eligible']), flush=True)
                ok += 1
            except Exception as e:
                fail.append((j, repr(e)))
                print('FAIL %r %s' % (j, e), flush=True)
    (RUNS / 'formal_summary.json').write_text(
        json.dumps(dict(ok=ok, fail=len(fail)), indent=2))
    return ok, fail


def validate():
    """Cross-check every planned run has evidence and correct fault/control state."""
    manifest = COUNTS.exists() and json.loads((COUNTS / 'manifest.json').read_text()) or []
    by = {(r['model'], r['ctx']): r for r in manifest}
    problems = []
    rows = []
    for p in load_manifest():
        model, ctx = p['model'], p['ctx']
        r = by.get((model, ctx), {})
        if r.get('status') != 'READY':
            problems.append((p, 'pre-scan BLOCKED/not-ready'))
            continue
        if p['kind'] == 'fault':
            q = {'T01': r['q10'], 'T02': r['q50'], 'T03': r['q90']}[p['timing']]
            sid = 'FPU-M%03d-%s-%s' % (model, ctx, p['timing'])
            want = dict(applied=1, fault=True, ordinal=q)
        else:
            sid = 'CTRL-FPU-M%03d-%s' % (model, ctx)
            want = dict(applied=0, fault=False, ordinal=1)
        sp = RUNS / sid / 'summary.json'
        if not sp.exists():
            problems.append((sid, 'missing summary.json'))
            continue
        s = json.loads(sp.read_text())
        rows.append(s)
        if s.get('applied') != want['applied']:
            problems.append((sid, 'applied=%s want %s' % (s.get('applied'), want['applied'])))
        if s.get('n_records', 0) == 0:
            problems.append((sid, 'zero records'))
        evp = RUNS / sid / 'events.jsonl'
        if not evp.exists():
            problems.append((sid, 'missing events.jsonl'))
    with open(BASE / 'FPU_5x3_Validation_Report.txt', 'w') as f:
        f.write('planned=%d validated=%d problems=%d\n' %
                (len(load_manifest()), len(rows), len(problems)))
        for p, why in problems:
            f.write('%s : %s\n' % (p, why))
    print('validated %d runs, %d problems' % (len(rows), len(problems)))
    return rows, problems


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['count', 'formal', 'validate'])
    ap.add_argument('--limit', type=int)
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--models', default='')
    ap.add_argument('--contexts', default='')
    a = ap.parse_args()
    sel_models = {int(x) for x in a.models.split(',')} if a.models else None
    sel_ctx = set(a.contexts.split(',')) if a.contexts else None

    if a.stage == 'count':
        def jobs():
            return [(m, c) for m in range(1, 13) for c in CONTEXTS
                    if (sel_models is None or m in sel_models)
                    and (sel_ctx is None or c in sel_ctx)]
        rows = []
        futs = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
            for m, c in jobs():
                futs[ex.submit(run_one, m, c, None, False, True, 1)] = (m, c)
            for fu in concurrent.futures.as_completed(futs):
                m, c = futs[fu]
                try:
                    s = fu.result()
                except Exception as e:
                    rows.append(dict(model=m, ctx=c, N=None, status='ERROR',
                                     reason=repr(e)))
                    print('COUNT ERROR M%03d %s: %r' % (m, c, e), flush=True)
                    continue
                n = s['eligible']
                qs = {t: (n * q + 99) // 100 for t, q in TIMINGS.items()}
                distinct = n >= 3 and (len(set(qs.values())) == 3)
                rows.append(dict(model=m, ctx=c, N=n, q10=qs['T01'],
                                 q50=qs['T02'], q90=qs['T03'],
                                 distinct=distinct,
                                 status=('READY' if distinct else 'BLOCKED'),
                                 n_squash=s['n_squash'],
                                 n_mispredict=s['n_mispredict'],
                                 pc=hex(s['pc']), n_records=s['n_records'],
                                 exit_code=s['exit_code']))
                print('COUNT M%03d %s N=%d ordinal=%s/%s/%s %s' %
                      (m, c, n, qs['T01'], qs['T02'], qs['T03'],
                       'READY' if distinct else 'BLOCKED'), flush=True)
        with open(BASE / 'FPU_5x3_CountOnly_Manifest.csv', 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['model', 'ctx', 'N', 'q10', 'q50',
                                              'q90', 'distinct', 'status',
                                              'n_squash', 'n_mispredict', 'pc',
                                              'n_records', 'exit_code'])
            w.writeheader()
            for r in rows:
                w.writerow(r)
        (COUNTS / 'manifest.json').write_text(json.dumps(rows, indent=2))
    elif a.stage == 'formal':
        formal_stage(a.limit, a.workers)
    else:
        validate()