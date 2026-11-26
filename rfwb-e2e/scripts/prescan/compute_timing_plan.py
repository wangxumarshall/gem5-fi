#!/usr/bin/env python3
"""Compute T01/T02/T03 from eligible-event scan traces.

Definition (frozen experiment design):
  T01 = ceil(0.10 * N), T02 = ceil(0.50 * N), T03 = ceil(0.90 * N)
  N = number of eligible events; require N >= 3 and three distinct ordinals.

Eligible event by model:
  M001  M001_MARKER_READ        (consumer-side marker read)
  M002  M002_VEC_ELIGIBLE       (one per vector instruction seq)
  M003  M003_CONSUMER_READ      (read-port consumer read)
  M004  M004_ELIGIBLE           (executed, non-squashed completion event)
  M005  M005_WB                 with a matching M005_CONSUMER_RENAME
                                (same PhysRegId + generation) AFTER the WB.
        This is the corrected WB-before-Rename definition; a Rename before WB
        is NOT eligible.  M005 must use the resulting target sequence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import os
import sys

MODELS = ['M001', 'M002', 'M003', 'M004', 'M005']
CTX = ['C01', 'C02', 'C03', 'C04', 'C05']
TIM = ['T01', 'T02', 'T03']
EVENT = {
    'M001': 'M001_MARKER_READ',
    'M002': 'M002_VEC_ELIGIBLE',
    'M003': 'M003_CONSUMER_READ',
    'M004': 'M004_ELIGIBLE',
    'M005': 'M005_WB',
}


def ceil_ord(n, num, den):
    return (n * num + den - 1) // den


def read_rows(path):
    rows = []
    with open(path, newline='') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return rows
        for lineno, row in enumerate(reader, start=2):
            if len(row) < 14:
                continue
            rows.append({
                'line': lineno,
                'tick': row[0],
                'event': row[4],
                'seq': row[7],
                'phys': row[9],
                'gen': row[11] if len(row) >= 15 else 'NA',
                'extra': ','.join(row[14:]) if len(row) >= 15 else ','.join(row[13:]),
            })
    return rows


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def find_scans(dirs, strict_duplicates=False):
    """Find one scan per (model, context).

    Directories are searched in the order given.  If the same scan name exists
    in more than one directory the first directory wins; a conflicting copy is
    reported.  This matters for M005: the corrected Batch03 scan supersedes the
    historical Batch02 scan, so callers must pass Batch03 before Batch02 (or
    simply pass a single authoritative scan directory).
    """
    found = {}
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not (name.startswith('SCAN-') and name.endswith('-N.csv')):
                continue
            parts = name[:-4].split('-')
            if len(parts) != 4:
                continue
            _, model, ctx, _ = parts
            if model not in MODELS or ctx not in CTX:
                continue
            p = os.path.join(d, name)
            key = (model, ctx)
            if key in found:
                if sha256(found[key]) != sha256(p):
                    if strict_duplicates:
                        raise SystemExit(
                            f'ERROR: conflicting scan copies for {model} {ctx}: '
                            f'{found[key]} vs {p}')
                    print(f'WARNING: conflicting scan copies for {model} {ctx}; '
                          f'using {found[key]} (ignored {p})', file=sys.stderr)
            else:
                found[key] = p
    return found


def eligible_events(rows, model):
    if model != 'M005':
        out = []
        seen = set()
        for r in rows:
            if r['event'] != EVENT[model]:
                continue
            if model == 'M002':
                # The ELF counts one eligible vector event per instruction seq.
                if r['seq'] in seen:
                    continue
                seen.add(r['seq'])
            out.append(r)
        return out

    # Corrected M005: WB-before-Rename with the same PhysRegId + generation.
    wbs = [r for r in rows if r['event'] == 'M005_WB']
    renames = {}
    for r in rows:
        if r['event'] == 'M005_CONSUMER_RENAME':
            renames.setdefault((r['phys'], r['gen']), []).append(r['line'])
    out = []
    for wb in wbs:
        later = [ln for ln in renames.get((wb['phys'], wb['gen']), []) if ln > wb['line']]
        if later:
            out.append(wb)
    return out


def load_sample_map(path):
    d = {}
    if not path:
        return d
    with open(path, newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            d[(r['model'], r['context'], r['timing'])] = r
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--traces', action='append', required=True,
                    help='directory containing SCAN-*.csv (repeatable)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--sample-map', default='',
                    help='optional evidence sample-id map TSV')
    ap.add_argument('--allow-missing', action='store_true')
    ap.add_argument('--strict-duplicates', action='store_true',
                    help='fail instead of preferring the first scan directory')
    ap.add_argument('--strict-target-seq', action='store_true',
                    help='fail if a fresh M005 target sequence differs from the frozen map')
    args = ap.parse_args()

    scans = find_scans(args.traces, args.strict_duplicates)
    sample_map = load_sample_map(args.sample_map)
    rows_out = []
    failures = []

    for model in MODELS:
        for ctx in CTX:
            key = (model, ctx)
            if key not in scans:
                if args.allow_missing:
                    continue
                raise SystemExit(f'ERROR: missing scan for {model} {ctx}')
            rows = read_rows(scans[key])
            ev = eligible_events(rows, model)
            n = len(ev)
            ords = ([ceil_ord(n, 1, 10), ceil_ord(n, 5, 10), ceil_ord(n, 9, 10)]
                    if n else [0, 0, 0])
            ok = n >= 3 and len(set(ords)) == 3
            tseq = [ev[o - 1]['seq'] if ok and 1 <= o <= n else '' for o in ords]
            status = 'PASS' if ok else 'BLOCKED'
            if not ok:
                failures.append(f'{model} {ctx}: N={n} ordinals={ords}')

            sids = []
            for tim, o, seq in zip(TIM, ords, tseq):
                canonical = f'RFWB-{model}-{ctx}-{tim}-F0'
                sid = canonical
                m = sample_map.get((model, ctx, tim))
                if m:
                    if m.get('sample_id'):
                        sid = m['sample_id']
                    want_seq = (m.get('target_seq') or '').strip()
                    if model == 'M005' and want_seq and seq and want_seq != str(seq):
                        msg = (f'M005 {ctx} {tim} target seq differs from the frozen '
                               f'run: scan={seq} frozen={want_seq}')
                        if args.strict_target_seq:
                            raise SystemExit('ERROR: ' + msg)
                        print('WARNING: ' + msg + ' (ordinal identity preserved)',
                              file=sys.stderr)
                sids.append(sid)

            rows_out.append([
                model, ctx, str(n), str(ords[0]), str(ords[1]), str(ords[2]),
                tseq[0], tseq[1], tseq[2], status,
                sids[0], sids[1], sids[2], os.path.relpath(scans[key]),
            ])

    header = ('model\tcontext\tN\tT01\tT02\tT03\t'
              'target_seq_T01\ttarget_seq_T02\ttarget_seq_T03\tstatus\t'
              'sample_id_T01\tsample_id_T02\tsample_id_T03\tscan_file')
    with open(args.out, 'w') as f:
        f.write(header + '\n')
        for r in rows_out:
            f.write('\t'.join(r) + '\n')

    print(header)
    for r in rows_out:
        print('\t'.join(r))
    if failures:
        print('\nBLOCKED conditions:', file=sys.stderr)
        for x in failures:
            print('  ' + x, file=sys.stderr)
        raise SystemExit(1)
    print(f'\nwrote {args.out}: {len(rows_out)} conditions, all PASS')


if __name__ == '__main__':
    main()
