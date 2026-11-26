#!/usr/bin/env python3
"""analyze_5x3_final_v6.py — final statistical-caliber & producer-mapping revision.

Offline only. Re-analyzes R1 (runs/) + R2 (runs_r2/) traces.

Revision over v5:
  * Mutually exclusive 4-way source-operand producer classification
    (ResolvedProducer / SquashedProducer / InitialStateSource / UnresolvedProducer)
    with TotalSources == sum(check).
  * Producer state fields (PriorWriterSeq/Phys/State/Committed/Squashed) come from
    real commit/squash events; a non-squashed speculative writer is SpeculativeWriter,
    not "committed".
  * ReachableUnresolvedDependency counts only UnresolvedProducer (not initial/squashed).
  * GraphComplete is 4-way: TraversalExhausted / TargetInputProvenanceComplete /
    DownstreamPropagationGraphComplete / FullCausalGraphComplete.
"""
import csv, json
from collections import defaultdict, Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / 'work/FPU_SIMD_5x3_FORMAL'
RUNS1 = BASE / 'runs'
RUNS2 = BASE / 'runs_r2'
COUNTS1 = BASE / 'counts'
COUNTS2 = BASE / 'counts_r2'
MAGIC = (0x3149554650465046).to_bytes(8, 'little')
CONTEXTS = ['C01', 'C02', 'C03', 'C04', 'C05']
TIMINGS = ['T01', 'T02', 'T03']
OUTPUT_FIELDS = ['raw0', 'raw1', 'raw2', 'fpsr', 'fpcr', 'nzcv', 'status', 'qc', 'lane']
RECORD_ID_FIELDS = ['model', 'ctx', 'mode', 'it']


def records(path):
    try:
        b = Path(path).read_bytes()
    except OSError:
        return []
    out, i = [], 0
    while True:
        i = b.find(MAGIC, i)
        if i < 0 or i + 128 > len(b):
            break
        v = [int.from_bytes(b[i + 8 * k:i + 8 * k + 8], 'little') for k in range(16)]
        out.append(dict(model=v[1], ctx=v[2], mode=v[3], it=v[4], raw0=v[5],
                        raw1=v[6], fpsr=v[7], fpcr=v[8], nzcv=v[9], lane=v[10],
                        status=v[11], raw2=v[12], qc=v[13]))
        i += 128
    return out


def events(path):
    ev = []
    try:
        for l in open(path):
            l = l.strip()
            if l.startswith('{'):
                try:
                    ev.append(json.loads(l))
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return ev


def akey(reg):
    if reg is None:
        return None
    arch = reg.get('arch')
    cls = reg.get('class')
    if arch is None or arch < 0 or cls in (None, 'Invalid', 'miscellaneous'):
        return None
    return (cls, arch)


def is_store_op(op):
    return op.startswith('str') or op.startswith('stp') or op.startswith('st1') \
        or op.startswith('stur') or op.startswith('stx')


def role(is_store, idx):
    if not is_store:
        return 'OPERAND'
    if idx == 0:
        return 'ADDRESS'
    return 'DATA'


def build_adj_v6(ev):
    """Speculative-map (last writer) replay with 4-way mutually-exclusive
    source-operand producer classification and per-writer commit/squash state."""
    renames = {e['seq']: e for e in ev if e.get('event') == 'rename'}
    commit_set = {e.get('seq') for e in ev if e.get('event') == 'commit'}
    squash_set = {e.get('seq') for e in ev if e.get('event') == 'squash'}
    last_writer = {}          # arch -> (seq, phys, is_squashed)
    consumers_of = defaultdict(list)
    dest_phys = {}
    op_of = {}
    store_addr = {}
    unresolved_src_count = defaultdict(int)
    counts = Counter()
    src_cls = []              # per-source classification (for audits)
    for seq in sorted(renames):
        r = renames[seq]
        op = (r.get('op') or '').strip()
        op_of[seq] = op
        st = is_store_op(op)
        for s in r.get('src', []):
            a = akey(s)
            if a is None:
                continue
            counts['total'] += 1
            src_phys = s.get('phys')
            if a in last_writer:
                pseq, pphys, p_sq = last_writer[a]
                phys_ok = (src_phys == pphys)
                p_committed = pseq in commit_set
                p_state = ('Committed' if p_committed else
                           ('Squashed' if p_sq else 'SpeculativeWriter'))
                if p_sq:
                    cat = 'SquashedProducer' if phys_ok else 'UnresolvedProducer'
                else:
                    cat = 'ResolvedProducer' if phys_ok else 'UnresolvedProducer'
                if phys_ok:
                    ci = dict(cseq=seq, idx=s.get('idx'), arch=s.get('arch'),
                              cls=s.get('class'), src_phys=src_phys,
                              producer_phys=pphys)
                    consumers_of[pseq].append(ci)
                    if st and s.get('idx') == 0:
                        store_addr[seq] = dict(addr_producer=pseq, idx=s.get('idx'),
                                               arch=s.get('arch'), cls=s.get('class'),
                                               src_phys=src_phys, producer_phys=pphys)
            else:
                cat = 'InitialStateSource'
                pseq = pphys = None
                p_state = 'None'
            counts[cat] += 1
            if cat == 'UnresolvedProducer':
                unresolved_src_count[seq] += 1
            src_cls.append(dict(seq=seq, arch=s.get('arch'), cls=s.get('class'),
                                src_phys=src_phys, category=cat,
                                prior_seq=pseq, prior_phys=pphys, prior_state=p_state))
        for d in r.get('dest', []):
            a = akey(d)
            if a is not None:
                dest_phys.setdefault(seq, {})[a] = d.get('phys')
                last_writer[a] = (seq, d.get('phys'), seq in squash_set)
    return (consumers_of, dest_phys, op_of, store_addr, unresolved_src_count,
            counts, src_cls, commit_set, squash_set)


def value_maps(ev):
    issue = {}
    wb = {}
    for e in ev:
        if e.get('event') == 'issue':
            issue[e['seq']] = {s.get('idx'): s.get('value') for s in e.get('src', [])}
        elif e.get('event') == 'writeback':
            wb[e['seq']] = {(d.get('class'), d.get('arch')): d.get('value')
                            for d in e.get('dest', [])}
    return issue, wb


def output_compare(rec, crec):
    if len(rec) != len(crec):
        return False, [dict(slot='COUNT', field='_count', fault_val=len(rec),
                            ctrl_val=len(crec))]
    diffs = []
    for i in range(len(rec)):
        for fid in RECORD_ID_FIELDS:
            if rec[i][fid] != crec[i][fid]:
                diffs.append(dict(slot=i, field='id:' + fid, fault_val=rec[i][fid],
                                  ctrl_val=crec[i][fid]))
        for f in OUTPUT_FIELDS:
            if rec[i][f] != crec[i][f]:
                diffs.append(dict(slot=i, field=f, fault_val=rec[i][f],
                                  ctrl_val=crec[i][f]))
    return True, diffs


def target_end_dest_map(ev, ordinal):
    for e in ev:
        if e.get('event') == 'target_end' and e.get('ordinal') == ordinal:
            m = {}
            for d in e.get('dest', []):
                cls = d.get('class')
                if cls in ('miscellaneous', 'Invalid', None):
                    continue
                m[(cls, d.get('arch'))] = d.get('value')
            return m
    return {}


def analyze(model, ctx, timing, q):
    sid = 'FPU-M%03d-%s-%s' % (model, ctx, timing)
    base = RUNS2 if ctx in ('C03', 'C05') else RUNS1
    rdir = base / sid
    cdir = base / ('CTRL-FPU-M%03d-%s' % (model, ctx))
    s = json.loads((rdir / 'summary.json').read_text())
    ev = events(rdir / 'events.jsonl')
    rec = records(rdir / 'stdout.txt')
    cev = events(cdir / 'events.jsonl')
    crec = records(cdir / 'stdout.txt')

    fi = [e for e in ev if e.get('event') == 'fault_inject']
    tb = [e for e in ev if e.get('event') == 'target_begin']
    te = [e for e in ev if e.get('event') == 'target_end']
    wb = {e.get('seq') for e in ev if e.get('event') == 'writeback'}
    cm = {e.get('seq') for e in ev if e.get('event') == 'commit'}
    sq_ev = {e.get('seq'): e for e in ev if e.get('event') == 'squash'}
    bm = [e for e in ev if e.get('event') == 'branch_mispredict']
    cfi = [e for e in cev if e.get('event') == 'fault_inject']

    tseq = next((e['seq'] for e in tb if e.get('ordinal') == q), None)
    f = fi[0] if fi else None

    fault_applied = (s.get('applied', 0) >= 1 and f is not None
                     and tseq is not None and f.get('seq') == tseq
                     and f.get('ordinal') == q)
    te_seq = next((e for e in te if e.get('ordinal') == q), None)
    target_end_ok = te_seq is not None and tseq is not None and te_seq.get('seq') == tseq
    target_wb = tseq is not None and tseq in wb
    target_commit = tseq is not None and tseq in cm
    target_squash = tseq is not None and tseq in sq_ev

    tbt = next((e.get('tick') for e in tb if e.get('ordinal') == q), None)
    tsth = sq_ev.get(tseq, {}).get('tick') if tseq else None
    tthread = next((e.get('thread', 0) for e in tb if e.get('ordinal') == q), 0)
    target_mispredict = False
    if tseq is not None and tsth is not None and tbt is not None:
        for b in bm:
            if (b.get('thread', 0) == tthread and b.get('seq', 0) < tseq
                    and b.get('pred_taken') != b.get('actual_taken')
                    and tbt <= b.get('tick', 0) <= tsth):
                target_mispredict = True
                break

    control_clean = (len(cfi) == 0 and
                     json.loads((cdir / 'summary.json').read_text()).get('applied', 0) == 0)
    trace_complete = tseq is not None and target_end_ok and target_wb

    count_match, diffs = output_compare(rec, crec)
    has_output_diff = len(diffs) > 0
    output_match = count_match and not has_output_diff

    fdest = target_end_dest_map(ev, q)
    cdest = target_end_dest_map(cev, q)
    changed_keys = sorted(k for k in set(fdest) | set(cdest)
                          if fdest.get(k) != cdest.get(k))
    error_produced = len(changed_keys) > 0

    (consumers_of, dest_phys, op_of, store_addr, unresolved_src_count,
     counts, src_cls, commit_set, squash_set) = build_adj_v6(ev)
    renames = {e['seq']: e for e in ev if e.get('event') == 'rename'}
    issue_vals, wb_vals = value_maps(ev)

    # target input provenance
    target_srcs = [c for c in src_cls if c['seq'] == tseq]
    target_input = Counter(c['category'] for c in target_srcs)
    target_input_unresolved = target_input.get('UnresolvedProducer', 0)
    target_input_provenance_complete = (target_input_unresolved == 0)

    tdest_archs = set()
    tdest_phys = {}
    tr = renames.get(tseq)
    if tr:
        for d in tr.get('dest', []):
            a = akey(d)
            if a is not None:
                tdest_archs.add(a)
                tdest_phys[a] = d.get('phys')

    direct = []
    arch_writer = {}
    overwrite_info = {}
    for seq in sorted(renames):
        r = renames[seq]
        if seq > tseq:
            for sacc in r.get('src', []):
                a = akey(sacc)
                if a in tdest_archs and arch_writer.get(a) == tseq:
                    direct.append(seq)
            for d in r.get('dest', []):
                a = akey(d)
                if a in tdest_archs and arch_writer.get(a) == tseq and a not in overwrite_info:
                    overwrite_info[a] = dict(seq=seq, phys=d.get('phys'))
        if seq not in squash_set:
            for d in r.get('dest', []):
                a = akey(d)
                if a is not None:
                    arch_writer[a] = seq
    n_direct = len(direct)
    changed_archs = set(changed_keys)
    overwritten_archs = set(overwrite_info)
    all_changed_overwritten = (len(changed_archs) > 0 and
                               changed_archs.issubset(overwritten_archs))
    overwrites_committed = all(
        overwrite_info[a]['seq'] in cm and overwrite_info[a]['seq'] not in sq_ev
        for a in changed_archs if a in overwrite_info)
    overwritten = len(overwritten_archs) > 0

    def consumer_state(cseq):
        if cseq in squash_set:
            return 'SQUASHED'
        if cseq in commit_set:
            return 'COMMITTED'
        if cseq in wb:
            return 'EXECUTED'
        return 'UNKNOWN'

    def vp_evidence(w, cseq, ci, cstate, phys_ok, w_tainted, r, selfdep):
        if (w_tainted or cstate in ('UNKNOWN', 'SQUASHED') or not phys_ok
                or r == 'ADDRESS' or selfdep):
            return 'UnknownInfluence'
        producer_wb = wb_vals.get(w, {}).get((ci['cls'], ci['arch']))
        consumer_issue = issue_vals.get(cseq, {}).get(ci['idx'])
        if producer_wb is not None and consumer_issue is not None and producer_wb == consumer_issue:
            return 'FaultValueReachedConsumer' if w == tseq else 'OperandReadVerified'
        return 'RegisterDependencyObserved'

    tainted = set()
    expanded = set()
    edge_seen = set()
    edges = []
    depth = {tseq: 0}
    queue = [tseq]
    unresolved = 0
    blocked_paths = 0
    downstream_unresolved = 0

    def make_edge(w, cseq, ci, dep_type, cstate, depth_v, w_tainted):
        op = op_of.get(cseq, '')
        st = is_store_op(op)
        r = role(st, ci['idx'])
        phys_ok = (ci['producer_phys'] == ci['src_phys'])
        if r == 'ADDRESS':
            kind = 'StoreAddressDependency'
        elif r == 'DATA':
            kind = 'StoreDataDependency'
        else:
            kind = 'RegisterDependency'
        selfdep = any(d.get('arch') == ci['arch'] and d.get('class') == ci['cls']
                      for d in renames.get(cseq, {}).get('dest', []))
        ev2 = vp_evidence(w, cseq, ci, cstate, phys_ok, w_tainted, r, selfdep)
        return dict(
            ModelID='FPU-M%03d' % model, ContextID=ctx, WhenID=timing,
            RunID=sid, ProducerSeq=w, ConsumerSeq=cseq,
            ProducerPhys=ci['producer_phys'], ConsumerSrcPhys=ci['src_phys'],
            PhysVerified=phys_ok, DependencyType=dep_type, SourceIdx=ci['idx'],
            SourceArch=ci['arch'], SourceClass=ci['cls'], OperandRole=r,
            EdgeKind=kind, ValuePropagationEvidence=ev2,
            IsStore=st, StoreOp=op if st else '',
            ConsumerState=cstate, WritebackStatus=cseq in wb,
            CommitStatus=cseq in commit_set, SquashStatus=cseq in squash_set,
            Depth=depth_v)

    while queue:
        w = queue.pop(0)
        expanded.add(w)
        w_tainted = w in tainted
        for ci in consumers_of.get(w, []):
            cseq = ci['cseq']
            ekey = (w, cseq, ci['idx'])
            if ekey in edge_seen:
                continue
            edge_seen.add(ekey)
            cstate = consumer_state(cseq)
            if ci['producer_phys'] != ci['src_phys']:
                cstate = 'UNKNOWN'
            is_tainted = w_tainted or cstate in ('UNKNOWN', 'SQUASHED') or \
                (ci['producer_phys'] != ci['src_phys'])
            if is_tainted:
                tainted.add(cseq)
                if w_tainted:
                    blocked_paths += 1
            if cstate in ('UNKNOWN', 'SQUASHED'):
                unresolved += 1
            edges.append(make_edge(w, cseq, ci,
                                   'DIRECT' if w == tseq else 'INDIRECT',
                                   cstate, depth.get(w, 0) + 1, w_tainted))
            if cseq not in expanded and cseq not in queue:
                depth[cseq] = depth.get(w, 0) + 1
                downstream_unresolved += unresolved_src_count.get(cseq, 0)
                queue.append(cseq)

    for e in edges:
        if e['IsStore']:
            cseq = e['ConsumerSeq']
            ainfo = store_addr.get(cseq)
            if ainfo and (ainfo['addr_producer'], cseq, ainfo['idx']) not in edge_seen:
                edge_seen.add((ainfo['addr_producer'], cseq, ainfo['idx']))
                c = consumer_state(cseq)
                edges.append(make_edge(
                    ainfo['addr_producer'], cseq,
                    dict(idx=ainfo['idx'], arch=ainfo['arch'], cls=ainfo['cls'],
                         src_phys=ainfo['src_phys'], producer_phys=ainfo['producer_phys']),
                    'ADDR', c, e['Depth'], False))

    traversal_exhausted = (not queue)
    pending_nodes = len(queue)
    phys_mismatch_edges = sum(1 for e in edges if not e['PhysVerified'])
    reachable_unresolved = target_input_unresolved + downstream_unresolved
    downstream_propagation_complete = (traversal_exhausted and pending_nodes == 0
                                       and downstream_unresolved == 0
                                       and phys_mismatch_edges == 0
                                       and unresolved == 0)
    full_causal_complete = (target_input_provenance_complete
                            and downstream_propagation_complete)

    masked_overwrite = (fault_applied and target_commit and not target_squash
                        and error_produced and overwritten and n_direct == 0
                        and all_changed_overwritten and overwrites_committed
                        and output_match)
    squashed = (fault_applied and target_squash and not target_commit
                and target_wb and target_mispredict and control_clean
                and target_end_ok and output_match)

    if not trace_complete:
        terminal = 'PARTIAL_TRACE'
    elif not fault_applied:
        terminal = 'INJECTION_MISS'
    elif not count_match:
        terminal = 'OUTPUT_MISMATCH'
    elif squashed:
        terminal = 'SQUASHED'
    elif has_output_diff:
        terminal = 'WRONG_RESULT'
    elif masked_overwrite:
        terminal = 'MASKED_OVERWRITE'
    elif n_direct == 0 and not overwritten:
        terminal = 'MASKED_NO_CONSUMER'
    else:
        terminal = 'OTHER'

    row = dict(model=model, ctx=ctx, timing=timing, sid=sid, ordinal=q,
               round='R2' if ctx in ('C03', 'C05') else 'R1',
               target_seq=tseq, fault_applied=fault_applied,
               error_produced=error_produced, target_end_ok=target_end_ok,
               target_writeback=target_wb, target_committed=target_commit,
               target_squashed=target_squash, target_mispredict=target_mispredict,
               control_clean=control_clean, overwritten=overwritten,
               all_changed_overwritten=all_changed_overwritten,
               overwrites_committed=overwrites_committed,
               n_changed_dest=len(changed_keys), n_direct=n_direct,
               count_match=count_match, n_diff=len(diffs), output_match=output_match,
               masked_overwrite=masked_overwrite, squashed=squashed,
               terminal=terminal,
               resolved_producer=counts['ResolvedProducer'],
               squashed_producer=counts['SquashedProducer'],
               initial_state_source=counts['InitialStateSource'],
               unresolved_producer=counts['UnresolvedProducer'],
               total_sources=counts['total'],
               global_unresolved_producer_count=counts['UnresolvedProducer'],
               target_input_unresolved_count=target_input_unresolved,
               target_input_provenance_complete=target_input_provenance_complete,
               reachable_unresolved_dependency=reachable_unresolved,
               downstream_unresolved_dependency=downstream_unresolved,
               traversal_exhausted=traversal_exhausted,
               downstream_propagation_complete=downstream_propagation_complete,
               full_causal_graph_complete=full_causal_complete,
               pending_nodes=pending_nodes, unresolved_edges=unresolved,
               phys_mismatch_edges=phys_mismatch_edges, blocked_paths=blocked_paths,
               n_edges=len(edges), exit_code=s.get('exit_code'))
    return row, edges, target_srcs


def main():
    cm1 = {(r['model'], r['ctx']): r for r in json.loads((COUNTS1 / 'manifest.json').read_text())}
    cm2 = {(r['model'], r['ctx']): r for r in json.loads((COUNTS2 / 'manifest.json').read_text())}
    rows, all_edges = [], []
    pc_audit = []
    ti_audit = []
    for model in range(1, 13):
        for ctx in CONTEXTS:
            cm = cm2 if ctx in ('C03', 'C05') else cm1
            r = cm[(model, ctx)]
            for t in TIMINGS:
                q = {'T01': r['q10'], 'T02': r['q50'], 'T03': r['q90']}[t]
                row, edges, target_srcs = analyze(model, ctx, t, q)
                rows.append(row)
                all_edges.extend(edges)
                pc_audit.append(dict(ModelID='FPU-M%03d' % model, ContextID=ctx,
                                     WhenID=t, ResolvedProducer=row['resolved_producer'],
                                     SquashedProducer=row['squashed_producer'],
                                     InitialStateSource=row['initial_state_source'],
                                     UnresolvedProducer=row['unresolved_producer'],
                                     TotalSources=row['total_sources'],
                                     MutuallyExclusive=(row['resolved_producer'] +
                                        row['squashed_producer'] +
                                        row['initial_state_source'] +
                                        row['unresolved_producer']) == row['total_sources']))
                for ts in target_srcs:
                    ti_audit.append(dict(ModelID='FPU-M%03d' % model, ContextID=ctx,
                                         WhenID=t, TargetSeq=ts['seq'],
                                         SourceArch=ts['arch'], SourceClass=ts['cls'],
                                         SourcePhys=ts['src_phys'],
                                         Category=ts['category'],
                                         PriorWriterSeq=ts['prior_seq'],
                                         PriorWriterPhys=ts['prior_phys'],
                                         PriorWriterState=ts['prior_state']))

    with open(BASE / 'FPU_5x3_Propagation_Evidence_Final_v6.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    with open(BASE / 'FPU_5x3_Causal_Edges_Final_v6.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(all_edges[0].keys()))
        w.writeheader(); w.writerows(all_edges)
    with open(BASE / 'FPU_5x3_Producer_Classification_Audit_v6.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(pc_audit[0].keys()))
        w.writeheader(); w.writerows(pc_audit)
    with open(BASE / 'FPU_5x3_TargetInput_Provenance_Audit_v6.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(ti_audit[0].keys()))
        w.writeheader(); w.writerows(ti_audit)

    term = Counter(r['terminal'] for r in rows)
    vp = Counter(r['ValuePropagationEvidence'] for r in all_edges)
    dep = Counter(r['DependencyType'] for r in all_edges)
    # 4-way totals across all runs
    tot = dict(
        resolved=sum(r['resolved_producer'] for r in rows),
        squashed=sum(r['squashed_producer'] for r in rows),
        initial=sum(r['initial_state_source'] for r in rows),
        unresolved=sum(r['unresolved_producer'] for r in rows),
    )
    tot['sum'] = sum(tot.values())
    tot['total_sources'] = sum(r['total_sources'] for r in rows)
    summary = dict(
        total_fault_runs=len(rows), terminal_counts=dict(term),
        total_edges=len(all_edges),
        direct_edges=dep.get('DIRECT', 0), indirect_edges=dep.get('INDIRECT', 0),
        addr_edges=dep.get('ADDR', 0),
        value_propagation_evidence=dict(vp),
        fault_value_reached_consumer=sum(1 for r in all_edges if r['ValuePropagationEvidence'] == 'FaultValueReachedConsumer'),
        operand_read_verified=sum(1 for r in all_edges if r['ValuePropagationEvidence'] == 'OperandReadVerified'),
        unknown_influence=sum(1 for r in all_edges if r['ValuePropagationEvidence'] == 'UnknownInfluence'),
        phys_mismatch_edges=sum(1 for r in all_edges if not r['PhysVerified']),
        phys_mismatch_by_kind=dict(Counter(r['EdgeKind'] for r in all_edges if not r['PhysVerified'])),
        max_depth=max((int(r['Depth']) for r in all_edges), default=0),
        producer_classification=tot,
        mutually_exclusive=(tot['sum'] == tot['total_sources']),
        global_unresolved_producer_count=tot['unresolved'],
        target_input_unresolved_count=sum(r['target_input_unresolved_count'] for r in rows),
        reachable_unresolved_dependency=sum(r['reachable_unresolved_dependency'] for r in rows),
        downstream_unresolved_dependency=sum(r['downstream_unresolved_dependency'] for r in rows),
        traversal_exhausted=sum(1 for r in rows if r['traversal_exhausted']),
        target_input_provenance_complete=sum(1 for r in rows if r['target_input_provenance_complete']),
        downstream_propagation_complete=sum(1 for r in rows if r['downstream_propagation_complete']),
        full_causal_graph_complete=sum(1 for r in rows if r['full_causal_graph_complete']),
        by_round=dict(Counter(r['round'] for r in rows)),
        injection_miss=[r['sid'] for r in rows if r['terminal'] == 'INJECTION_MISS'],
        partial_trace=[r['sid'] for r in rows if r['terminal'] == 'PARTIAL_TRACE'],
        output_mismatch=[r['sid'] for r in rows if r['terminal'] == 'OUTPUT_MISMATCH'],
    )
    (BASE / 'FPU_5x3_Propagation_Summary_Final_v6.json').write_text(
        json.dumps(summary, indent=2))
    print('fault runs:', len(rows), 'edges:', len(all_edges))
    print('terminal:', dict(term))
    print('VP evidence:', dict(vp))
    print('producer classification:', tot, 'mutually_exclusive:', summary['mutually_exclusive'])
    print('global unresolved:', summary['global_unresolved_producer_count'],
          'target_input_unresolved:', summary['target_input_unresolved_count'],
          'reachable:', summary['reachable_unresolved_dependency'],
          'downstream:', summary['downstream_unresolved_dependency'])
    print('graph: traversal_exhausted=', summary['traversal_exhausted'],
          'target_input_complete=', summary['target_input_provenance_complete'],
          'downstream_complete=', summary['downstream_propagation_complete'],
          'full_complete=', summary['full_causal_graph_complete'])
    print('injection_miss:', summary['injection_miss'], 'partial:', summary['partial_trace'],
          'output_mismatch:', summary['output_mismatch'])


if __name__ == '__main__':
    main()