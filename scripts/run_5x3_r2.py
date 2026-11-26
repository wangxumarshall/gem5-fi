#!/usr/bin/env python3
"""Round-2 re-run driver: revised C03 + C05 workloads only.

Writes into work/FPU_SIMD_5x3_FORMAL/{counts_r2,runs_r2} so the round-1 results
and raw traces (counts/ and runs/) are preserved untouched.
"""
import argparse, concurrent.futures, json, os, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEM5 = ROOT / 'gem5/build/ARM/gem5.opt'
CONFIG = ROOT / 'gem5/configs/deprecated/example/se.py'
WL = ROOT / 'work/FPU_SIMD_5x3_FORMAL/workloads/build'
BASE = ROOT / 'work/FPU_SIMD_5x3_FORMAL'
COUNTS = BASE / 'counts_r2'
RUNS = BASE / 'runs_r2'

LANE = {i: -1 for i in range(1, 13)}
LANE.update({8: 7, 9: 3, 10: 7, 11: 7})
REV_CTX = ['C03', 'C05']
TIMINGS = {'T01': 10, 'T02': 50, 'T03': 90}


def target_pc(model, ctx):
    out = subprocess.check_output(['nm', str(WL / ('fpu_%02d_%s' % (model, ctx)))],
                                  text=True)
    for line in out.splitlines():
        p = line.split()
        if len(p) >= 3 and p[-1] == 'fpu_target_r':
            return int(p[0], 16)
    raise RuntimeError('no fpu_target_r')


def run_one(model, ctx, timing, fault, count_only, ordinal):
    sid = ('FPU-M%03d-%s-%s' % (model, ctx, timing)) if timing else \
          ('CTRL-FPU-M%03d-%s' % (model, ctx))
    rdir = (COUNTS if count_only else RUNS) / (('M%03d_%s' % (model, ctx)) if count_only else sid)
    rdir.mkdir(parents=True, exist_ok=True)
    pc = target_pc(model, ctx)
    env = os.environ.copy()
    env.update({
        'FI_ENABLE': '1' if (fault and not count_only) else '0',
        'FI_COUNT_ONLY': '1' if count_only else '0',
        'FI_MODEL': 'M%03d' % model,
        'FI_PC': hex(pc),
        'FI_ORDINAL': str(ordinal),
        'FI_LANE': str(LANE[model]),
        'FI_TRACE': str(rdir / 'events.jsonl'),
        'FI_SAMPLE': sid, 'FI_PAIR': 'FPU-M%03d-%s' % (model, ctx),
        'FI_CONTEXT': ctx, 'FI_MODE': '5x3',
        'FI_STATE': 'SPEC_EXEC_SQUASH' if ctx == 'C05' else 'NORMAL_COMMIT',
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
    ev = []
    for l in open(rdir / 'events.jsonl') if (rdir / 'events.jsonl').exists() else []:
        l = l.strip()
        if l.startswith('{'):
            try:
                ev.append(json.loads(l))
            except json.JSONDecodeError:
                pass
    eligible = max((e.get('eligible_total', 0) for e in ev if e.get('event') == 'run_end'),
                   default=0)
    applied = max((e.get('applied_total', 0) for e in ev if e.get('event') == 'run_end'),
                  default=0)
    s = dict(sid=sid, model=model, ctx=ctx, timing=timing, fault=bool(fault),
             count_only=count_only, ordinal=ordinal, pc=pc, exit_code=rc,
             eligible=eligible, applied=applied,
             elapsed=round(time.time() - t0, 3), run_dir=str(rdir))
    (rdir / 'summary.json').write_text(json.dumps(s, indent=2))
    return s


def count(workers):
    jobs = [(m, c) for m in range(1, 13) for c in REV_CTX]
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(run_one, m, c, None, False, True, 1): (m, c) for m, c in jobs}
        for fu in concurrent.futures.as_completed(futs):
            m, c = futs[fu]
            s = fu.result()
            n = s['eligible']
            qs = {t: (n * q + 99) // 100 for t, q in TIMINGS.items()}
            distinct = n >= 3 and len(set(qs.values())) == 3
            rows.append(dict(model=m, ctx=c, N=n, q10=qs['T01'], q50=qs['T02'],
                             q90=qs['T03'], distinct=distinct,
                             status=('READY' if distinct else 'BLOCKED'),
                             pc=hex(s['pc']), exit_code=s['exit_code']))
            print('COUNT M%03d %s N=%d %s/%s/%s %s' %
                  (m, c, n, qs['T01'], qs['T02'], qs['T03'],
                   'READY' if distinct else 'BLOCKED'), flush=True)
    (COUNTS / 'manifest.json').write_text(json.dumps(rows, indent=2))
    return rows


def formal(workers, skip_existing=True):
    cm = {(r['model'], r['ctx']): r for r in json.loads((COUNTS / 'manifest.json').read_text())}
    jobs = []
    for m in range(1, 13):
        for c in REV_CTX:
            r = cm[(m, c)]
            if r['status'] != 'READY':
                continue
            for t in TIMINGS:
                q = {'T01': r['q10'], 'T02': r['q50'], 'T03': r['q90']}[t]
                jobs.append((m, c, t, True, q))
            jobs.append((m, c, None, False, 1))

    def one(j):
        m, c, t, fault, q = j
        sid = ('FPU-M%03d-%s-%s' % (m, c, t)) if t else ('CTRL-FPU-M%03d-%s' % (m, c))
        sp = RUNS / sid / 'summary.json'
        if skip_existing and sp.exists():
            s = json.loads(sp.read_text())
            if s.get('exit_code') == 0:
                return s
        return run_one(m, c, t, fault, False, q)

    ok = fail = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for i, fu in enumerate(concurrent.futures.as_completed(futs), 1):
            j = futs[fu]
            try:
                s = fu.result()
                kind = 'FAULT' if j[3] else 'CTRL '
                print('RUN %3d/%d %s %s rc=%d appl=%d N=%d' %
                      (i, len(futs), kind, s['sid'], s['exit_code'],
                       s['applied'], s['eligible']), flush=True)
                ok += 1
            except Exception as e:
                fail += 1
                print('FAIL %r %s' % (j, e), flush=True)
    (RUNS / 'formal_summary.json').write_text(json.dumps(dict(ok=ok, fail=fail), indent=2))
    return ok, fail


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['count', 'formal'])
    ap.add_argument('--workers', type=int, default=8)
    a = ap.parse_args()
    if a.stage == 'count':
        count(a.workers)
    else:
        formal(a.workers)