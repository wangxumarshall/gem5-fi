#!/usr/bin/env python3
"""lsu_r6_rejudge.py — [MDSPEC][R6-REJUDGE] offline strict re-judgement of the
12-RunID hard-regression set against the CURRENT strict chain checker.

Why: every pilot ``chain_report.json`` on disk was produced by the checker
living in ``.claude/worktrees/r6-tlb-hooks/tools/``, which is based on
``293b4003`` and therefore lacks the family-aware DAG rules (``317c71bf``) and
``check_admission`` (``9a7da7cf``).  Those reports are NOT authoritative.
The raw PROP-EVT streams are preserved on disk, so the strict verdict can be
recomputed **offline — no gem5 re-run required**.

This tool does not re-implement the checker: it imports it
(``tools.lsu_chain_check``) and calls the two public entry points
``check_chain(events, oracle_outcome=...)`` and ``check_admission(bundle)``.
It only ADDS honest bookkeeping the checker does not do (stream completeness,
sentinel-vs-empty field accounting, per-layer kind listing, correlation-key
continuity, "injection value before/after" extraction).

Real stream line format (the pre-existing ``runs/lsu/r6_evt.py`` parser bug
was that it assumed ``prop-evt`` lowercase / a whitespace header; the real
formatter emits ``PROP-EVT: kind=<k> key=value …``):

    PROP-EVT: kind=inj run_id=T04-F0-W4 sample_run_id=s1 fault_id=1 event_id=0 …

Usage:
  python3 tools/lsu_r6_rejudge.py                     # all 12 canonical RunIDs
  python3 tools/lsu_r6_rejudge.py --run-id T04-F0-W4  # one RunID
  python3 tools/lsu_r6_rejudge.py --stream /path/prop_evt.txt.gz --run-id X
  python3 tools/lsu_r6_rejudge.py --root DIR [--root DIR2] --json OUT --md OUT

Exit code: 0 always (this is a reporting tool; verdicts are in the output).
"""
import argparse
import hashlib
import gzip
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lsu_prop_fields as P          # noqa: E402
import lsu_chain_check as C          # noqa: E402

# ---------------------------------------------------------------------------
# The 12 RunIDs the user mandated (T2' forced regression).  Split by the
# historical (NON-authoritative) claim, kept only as provenance.
# ---------------------------------------------------------------------------
FALSELY_FULL = [
    "T02-F0-W4", "T02-F2-W4", "T04-F0-W4", "T04-F2-W4", "T04-F6-W4",
]
PREVIOUSLY_INCOMPLETE = [
    "T01-F0-W4", "T01-F1-W4", "T01-F2-W4", "T03-F5-W4",
    "T10-F0-W4", "T10-F1-W4", "T10-F2-W4",
]
CANONICAL_12 = FALSELY_FULL + PREVIOUSLY_INCOMPLETE

DEFAULT_ROOT = "/home/sdc/gem5-fi-ding/runs/lsu"

# Values that LOOK populated but mean "not recorded" on this stream — the
# strict checker's "non-empty field" test cannot see them (a real honest
# accounting gap, reported separately from `missing_mandatory_metric`).
SENTINELS = {"none", "unknown", "-1", "na", "n/a"}


# ---------------------------------------------------------------------------
# stream discovery / completeness
# ---------------------------------------------------------------------------
def find_candidates(run_id, roots):
    """All ``<root>/**/<run_id>/seed*/prop_evt.txt.gz`` streams on disk."""
    out = []
    for root in roots:
        root = Path(root)
        if not root.is_dir():
            continue
        for hit in root.glob(f"**/{run_id}/seed*/prop_evt.txt.gz"):
            out.append(hit.resolve())
    return sorted(set(out))


def sha256_of(path, limit=None):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gz_readable(path):
    """(ok, error) — full sequential read/decompress of the gzip member.

    A truncated writer (killed gem5) leaves an incomplete deflate stream:
    either ``EOFError`` ("Compressed file ended before the end-of-stream
    marker") or ``gzip.BadGzipFile``.
    """
    try:
        with gzip.open(path, "rb") as fh:
            while fh.read(1 << 20):
                pass
        return True, ""
    except (EOFError, gzip.BadGzipFile, OSError) as exc:
        return False, f"{type(exc).__name__}: {exc}"


def stream_status(stream):
    """COMPLETE | TRUNCATED | INCOMPLETE_NO_STATS | MISSING.

    A stream can only *establish completeness* when (a) the gzip member
    decompresses to its end-of-stream marker and (b) the sibling ``stats.txt``
    exists and is non-empty (i.e. gem5 reached its own exit/summary path).
    """
    if stream is None:
        return "MISSING", {"gz_ok": None, "stats_bytes": None}
    gz_ok, gz_err = gz_readable(stream)
    stats = stream.parent / "stats.txt"
    stats_bytes = stats.stat().st_size if stats.exists() else None
    if not gz_ok:
        return "TRUNCATED", {"gz_ok": False, "gz_error": gz_err,
                             "stats_bytes": stats_bytes}
    if not stats_bytes:
        return "INCOMPLETE_NO_STATS", {"gz_ok": True, "stats_bytes": stats_bytes}
    return "COMPLETE", {"gz_ok": True, "stats_bytes": stats_bytes}


def oracle_of(stream):
    """Runner oracle for this sample, if a report sibling carries one.

    Returns (oracle_outcome, source_path).  This is a *read* of the runner's
    own classification (the old chain_report.json / cell_results.json), never
    a re-derivation, and its provenance is printed with the verdict.
    """
    for name in ("chain_report.json", "cell_results.json"):
        p = stream.parent / name
        if not p.exists():
            continue
        try:
            doc = json.loads(p.read_text())
        except (OSError, ValueError):
            continue
        if name == "chain_report.json" and doc.get("oracle_outcome"):
            return doc["oracle_outcome"], str(p)
        runs = doc.get("runs") or []
        if runs and runs[0].get("outcome"):
            return runs[0]["outcome"], str(p)
    # the outdir-level report (one level above seedN/)
    for name in ("chain_report.json", "cell_results.json"):
        p = stream.parent.parent / name
        if not p.exists():
            continue
        try:
            doc = json.loads(p.read_text())
        except (OSError, ValueError):
            continue
        if name == "chain_report.json" and doc.get("oracle_outcome"):
            return doc["oracle_outcome"], str(p)
        runs = doc.get("runs") or []
        if runs and runs[0].get("outcome"):
            return runs[0]["outcome"], str(p)
    return None, None


# ---------------------------------------------------------------------------
# honest bookkeeping the checker does not do
# ---------------------------------------------------------------------------
def _is_sentinel(value):
    return str(value).strip().lower() in SENTINELS


def layer_inventory(events, fault_id, family):
    """kind list per layer (L0..L5) over the whole fault chain."""
    inv = {L: [] for L in C.LAYERS}
    for evt in events:
        if evt.get("fault_id", "") != fault_id:
            continue
        layer = C._layer_of(evt, family)
        if layer in inv:
            inv[layer].append(evt.get("kind", "?"))
    return {L: sorted(set(k)) for L, k in inv.items()}


def layer_kind_counts(events, fault_id, family):
    inv = {L: {} for L in C.LAYERS}
    for evt in events:
        if evt.get("fault_id", "") != fault_id:
            continue
        layer = C._layer_of(evt, family)
        if layer in inv:
            k = evt.get("kind", "?")
            inv[layer][k] = inv[layer].get(k, 0) + 1
    return inv


def field_gaps(events, fault_id, family):
    """Per-layer accounting of REQUIRED_FIELDS that are empty vs sentinel.

    `empty` = the checker's/family contract's mandatory fields recorded blank
    ("k="); `sentinel` = populated with a placeholder that means "not
    recorded" but passes a non-empty test.  Both are honest failures of
    "每层必录指标"; they are reported separately because they fail for
    different reasons.
    """
    out = []
    seen = set()
    for evt in events:
        if evt.get("fault_id", "") != fault_id:
            continue
        kind = evt.get("kind", "")
        if kind in seen:
            continue
        seen.add(kind)
        layer = C._layer_of(evt, family)
        for f in P.REQUIRED_FIELDS.get(kind, []):
            v = evt.get(f, "")
            if not str(v).strip():
                out.append({"layer": layer, "kind": kind, "field": f,
                            "state": "empty"})
            elif _is_sentinel(v):
                out.append({"layer": layer, "kind": kind, "field": f,
                            "state": f"sentinel:{v}"})
    return out


def correlation_report(events, fault_id, family, path):
    """fault_id / parent_event_id DAG / request_id / walk_id / dyn_inst_seq.

    `parent_is_linear` is the honest structural observation: on all existing
    T-series streams `parent_event_id == event_id - 1`, i.e. the "DAG" is a
    degenerate linear list and carries no semantic edge — cross-branch
    splicing cannot be excluded by the parent relation alone.
    """
    chain = [e for e in events if e.get("fault_id", "") == fault_id]
    fids = sorted({e.get("fault_id", "") for e in events
                   if e.get("fault_id", "") not in ("", "0")})
    ids = [int(e["event_id"]) for e in chain
           if str(e.get("event_id", "")).lstrip("-").isdigit()]
    linear = bool(ids) and ids == list(range(min(ids), max(ids) + 1))
    root_ok = all(
        (e.get("parent_event_id", "") == "" and e["event_id"] == str(min(ids)))
        or (str(e.get("parent_event_id", "")).lstrip("-").isdigit()
            and int(e["parent_event_id"]) == int(e["event_id"]) - 1)
        for e in chain if str(e.get("event_id", "")).lstrip("-").isdigit()
    ) if ids else False
    ticks = [C._tick(e) for e in chain]
    path_rids = []
    path_seqs = []
    for e in path:
        r = str(e.get("request_id", "")).strip()
        s = str(e.get("dyn_inst_seq", "")).strip()
        if r:
            path_rids.append((C._layer_of(e, family), e.get("kind"), r))
        if s:
            path_seqs.append((C._layer_of(e, family), e.get("kind"), s))
    walk_ids = sorted({str(e.get("walk_id", "")).strip()
                       for e in chain if str(e.get("walk_id", "")).strip()
                       and str(e.get("walk_id", "")).strip() != "0"})
    return {
        "fault_ids_present": fids,
        "chain_event_count": len(chain),
        "parent_ids_contiguous": linear and root_ok,
        "parent_relation_is_linear": linear,
        "tick_monotonic": ticks == sorted(ticks),
        "path_request_ids": path_rids,
        "path_request_ids_consistent": bool(path_rids) and len(
            {r for _, _, r in path_rids}) == 1,
        "path_dyn_inst_seqs": path_seqs,
        "path_dyn_inst_seqs_consistent": bool(path_seqs) and len(
            {s for _, _, s in path_seqs}) == 1,
        "path_seq_break": [f"{L}:{k}={s}" for L, k, s in path_seqs],
        "walk_ids_nonzero": walk_ids,
    }


def forbidden_patterns(events, fault_id, family, path, verdict):
    """The user's explicit fail list, evaluated verbatim and separately from
    the checker so a checker loophole is still visible in this table."""
    viol = []
    if family == "tlb":
        l1w = next((e for e in path if C._layer_of(e, family) == "L1"), None)
        if l1w is not None and l1w.get("kind") != "tlb_lookup":
            viol.append(f"l1_faked_by_cache_access(L1={l1w.get('kind')})")
    l5w = next((e for e in path if C._layer_of(e, family) == "L5"), None)
    if l5w is not None:
        dl = str(l5w.get("detection_layer", "")).strip()
        if l5w.get("kind") == "chain_end" and (not dl or _is_sentinel(dl)):
            viol.append(f"l5_is_chain_end_only(kind=chain_end "
                        f"detection_layer={dl or '<empty>'})")
        for f in ("detection_layer", "contained", "outcome"):
            if _is_sentinel(l5w.get(f, "")) and f != "outcome":
                viol.append(f"l5_{f}_sentinel:{l5w.get(f)}")
    inj = next((e for e in events if e.get("kind") == "inj"
                and e.get("fault_id") == fault_id), None)
    if inj is not None and not (str(inj.get("before", "")).strip()
                                and str(inj.get("after", "")).strip()):
        viol.append("l0_inj_before_after_empty")
    # independent cross-request probe: the checker only compares *adjacent*
    # path witnesses with BOTH request_ids stamped, so one hollow witness in
    # the middle hides a request change over a longer span.
    stamped = [(C._layer_of(e, family), e.get("kind"),
                str(e.get("request_id", "")).strip())
               for e in path
               if str(e.get("request_id", "")).strip() not in ("", "0")]
    if len({r for _, _, r in stamped}) > 1:
        viol.append("cross_request_on_proven_path("
                    + "→".join(f"{L}:{r}" for L, _, r in stamped) + ")")
    unk = C._has_unknown(events)
    if unk is not None:
        viol.append(f"unknown_in_activated_chain(kind={unk.get('kind')})")
    for e in events:
        if e.get("fault_id") != fault_id:
            continue
        for f in ("detection_layer", "contained", "outcome", "evidence_status"):
            if str(e.get(f, "")).strip().lower() == "unknown":
                viol.append(f"literal_unknown:{e.get('kind')}.{f}")
    return sorted(set(viol))


def path_witnesses(chain, family, path):
    return [{"layer": C._layer_of(e, family), "kind": e.get("kind"),
             "event_id": e.get("event_id"),
             "parent_event_id": e.get("parent_event_id"),
             "tick": e.get("tick"), "request_id": e.get("request_id"),
             "walk_id": e.get("walk_id"),
             "dyn_inst_seq": e.get("dyn_inst_seq"),
             "detection_layer": e.get("detection_layer"),
             "contained": e.get("contained"), "outcome": e.get("outcome")}
            for e in path]


def cross_edge_check(chain, family, path):
    """Independent cross-request probe, reported as data (see
    forbidden_patterns for the verdict token): distinct stamped request_ids on
    the proven path, and the total per-layer witness counts."""
    stamped = sorted({str(e.get("request_id", "")).strip() for e in path
                      if str(e.get("request_id", "")).strip() not in ("", "0")})
    chain_stamped = sorted({str(e.get("request_id", "")).strip()
                            for e in chain
                            if str(e.get("request_id", "")).strip()
                            not in ("", "0")})
    return {"path_stamped_request_ids": stamped,
            "chain_stamped_request_id_count": len(chain_stamped)}


# ---------------------------------------------------------------------------
# per-RunID evaluation
# ---------------------------------------------------------------------------
def evaluate_candidate(run_id, stream, checker_blob):
    status, detail = stream_status(stream)
    events, parser_truncated = P.read_events(stream)
    fault_ids = sorted({e.get("fault_id", "") for e in events
                        if e.get("fault_id", "") not in ("", "0")})
    activated = 1 if any(e.get("kind") == "inj" for e in events) else 0
    oracle, oracle_src = oracle_of(stream)
    verdict = C.check_chain(events, oracle_outcome=oracle)
    admission = C.check_admission({
        "run_id": run_id, "activated": activated, "events": events,
        "oracle_outcome": oracle,
    })
    row = {
        "run_id": run_id,
        "stream": str(stream),
        "stream_sha256": sha256_of(stream),
        "stream_bytes": stream.stat().st_size,
        "stream_mtime": int(stream.stat().st_mtime),
        "stream_status": status,
        "stream_detail": detail,
        "parser_truncated": parser_truncated,
        "checker_blob": checker_blob,
        "event_count": len(events),
        "activated": activated,
        "oracle_outcome": oracle,
        "oracle_source": oracle_src,
        "fault_ids": fault_ids,
        "check_chain": verdict,
        "check_admission": admission,
    }
    if not fault_ids:
        row["layers"] = {}
        row["layer_kinds"] = {}
        row["correlation"] = {}
        row["field_gaps"] = []
        row["forbidden"] = ["no_fault_id_in_stream"]
        row["cross_edges"] = []
        return row
    # dominant fault = the one with the longest proven path
    faults = verdict["faults"]
    fid = max(faults, key=lambda k: len(faults[k]["path_event_ids"]))
    family = faults[fid]["family"]
    chain = [e for e in events if e.get("fault_id", "") == fid]
    path = C._best_ordered_path(chain, family)
    row["dominant_fault_id"] = fid
    row["family"] = family
    row["layers"] = layer_inventory(events, fid, family)
    row["layer_kinds"] = layer_kind_counts(events, fid, family)
    row["path_witnesses"] = path_witnesses(chain, family, path)
    row["correlation"] = correlation_report(events, fid, family, path)
    row["field_gaps"] = field_gaps(events, fid, family)
    row["checker_missing_metrics"] = C._missing_metrics(path, family)
    row["forbidden"] = forbidden_patterns(events, fid, family, path, verdict)
    row["cross_edges"] = cross_edge_check(chain, family, path)
    # the fault's own recorded payload (injection value before/after):
    # L0 `inj` is the injector's own registration event; the L1 witness is
    # where the corrupted value first becomes visible; the sibling
    # `armtlb_injections.log` is the injector's ground-truth record.
    inj = next((e for e in events if e.get("kind") == "inj"
                and e.get("fault_id") == fid), None)
    l1w = next((e for e in path if C._layer_of(e, family) == "L1"), None)
    logh = stream.parent / "armtlb_injections.log"
    row["injection"] = {
        "l0_inj": {k: inj.get(k, "") for k in
                   ("kind", "field", "before", "after", "va", "pa",
                    "state_before", "state_after", "dyn_inst_seq")}
        if inj else None,
        "l1_witness": {k: l1w.get(k, "") for k in
                       ("kind", "field", "before", "after",
                        "state_before", "state_after")}
        if l1w is not None else None,
        "injector_log": logh.read_text().strip() if logh.exists() else None,
    }
    return row


def evaluate_run_id(run_id, roots, override_stream=None):
    if override_stream:
        cands = [Path(override_stream).resolve()]
    else:
        cands = find_candidates(run_id, roots)
    if not cands:
        return {"run_id": run_id, "stream_status": "MISSING",
                "stream": None, "candidates": []}
    checker_blob = hashlib.sha256(
        Path(C.__file__).read_bytes()).hexdigest()
    rows = [evaluate_candidate(run_id, s, checker_blob) for s in cands]
    # canonical candidate = most recent COMPLETE run; then newest; then
    # largest.  All candidates are reported alongside so the choice is visible.
    rank = {"COMPLETE": 2, "INCOMPLETE_NO_STATS": 1, "TRUNCATED": 0}
    rows.sort(key=lambda r: (rank.get(r["stream_status"], -1),
                             r["stream_mtime"], r["event_count"]), reverse=True)
    best = rows[0]
    best["candidates"] = [r["stream"] for r in rows]
    best["all_candidates"] = [{k: r[k] for k in
                               ("stream", "stream_status", "event_count",
                                "stream_sha256", "parser_truncated",
                                "check_chain", "check_admission", "forbidden")}
                              for r in rows]
    return best


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
def _fmt_layers(row):
    if not row.get("layer_kinds"):
        return "n/a"
    parts = []
    for L in C.LAYERS:
        cnt = row["layer_kinds"].get(L) or {}
        if cnt:
            inner = ",".join(f"{k}×{v}" for k, v in sorted(cnt.items()))
            parts.append(f"{L}[{inner}]")
        else:
            parts.append(f"{L}[-]")
    return " ".join(parts)


def _fmt_keys(row):
    c = row.get("correlation") or {}
    if not c:
        return "n/a"
    return (f"fault_id={','.join(c['fault_ids_present']) or 'n/a'}; "
            f"parent_event_id({'contiguous-linear' if c['parent_ids_contiguous'] else 'NON-linear'}); "
            f"request_id={'contig' if c['path_request_ids_consistent'] else 'breaks'}"
            f"{'/' + '|'.join(sorted({r for _, _, r in c['path_request_ids']})) if c.get('path_request_ids') else ''}; "
            f"walk_id={','.join(c['walk_ids_nonzero']) or 'none-nonzero'}; "
            f"dyn_inst_seq={'contig' if c['path_dyn_inst_seqs_consistent'] else 'breaks'}")


def _fmt_verdict(row):
    v = row.get("check_chain") or {}
    adm = row.get("check_admission") or {}
    f = (v.get("faults") or {})
    if not f:
        term = "(none)"
        prov = None
        viol = ["no_fault_chain"]
    else:
        fid = row.get("dominant_fault_id")
        key = fid if fid in f else max(f, key=lambda k: len(f[k]["path_event_ids"]))
        term = f[key]["terminal"]
        prov = f[key]["provable_to"]
        viol = []
    viol = list(viol) + list(adm.get("violations") or [])
    return (f"terminal={term}; provable_to={prov}; "
            f"admitted={adm.get('admitted')}; violations={viol or '[]'}")


def _fmt_injection(row):
    inj = row.get("injection")
    if not inj:
        return "n/a"
    l0 = inj.get("l0_inj") or {}
    l1 = inj.get("l1_witness") or {}
    log = (inj.get("injector_log") or "").splitlines()
    bits = []
    if l0:
        bits.append(f"L0 inj field={l0.get('field') or '?'} "
                    f"before={l0.get('before') or '<empty>'}→"
                    f"after={l0.get('after') or '<empty>'} (pa={l0.get('pa') or '<empty>'})")
    if l1:
        bits.append(f"L1 {l1.get('kind')} field={l1.get('field') or '?'} "
                    f"before={l1.get('before') or '<empty>'}→"
                    f"after={l1.get('after') or '<empty>'}")
    if log:
        bits.append("injector_log: " + log[0].replace("|", "/"))
    return " ; ".join(bits) or "n/a"


def render_md(rows, meta):
    out = []
    out.append("# R6-12RUNID — offline strict re-judgement table (L21)")
    out.append("")
    out.append(f"- checker: `tools/lsu_chain_check.py` "
               f"sha256=`{meta['checker_blob'][:16]}` — {meta['checker_commit']}")
    out.append(f"- line format read: `{meta['line_format']}`")
    out.append(f"- generated: {meta['generated']}")
    out.append(f"- **CAVEAT (provisional):** {meta['caveat']}")
    out.append("")
    out.append("## Stream completeness (determines re-run need)")
    out.append("")
    out.append("| RunID | status | events | sha256 | path |")
    out.append("|---|---|---|---|---|")
    for r in rows:
        out.append(f"| {r['run_id']} | {r['stream_status']} | "
                   f"{r.get('event_count', 'n/a')} | "
                   f"{(r.get('stream_sha256') or 'n/a')[:16]} | "
                   f"`{r.get('stream') or '-'}` |")
    out.append("")
    out.append("## Per-RunID strict verdict")
    out.append("")
    out.append("| RunID | stream | injected before→after | L0..L5 kinds | "
               "correlation keys | oracle | chain verdict | forbidden | "
               "evidence path |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        out.append(
            f"| {r['run_id']} | {r['stream_status']} | "
            f"{_fmt_injection(r)} | "
            f"{_fmt_layers(r)} | {_fmt_keys(r)} | "
            f"{r.get('oracle_outcome') or 'n/a'} | "
            f"{_fmt_verdict(r)} | "
            f"{'; '.join(r.get('forbidden') or []) or 'none'} | "
            f"`{r.get('stream') or '-'}` |")
    out.append("")
    out.append("## Per-layer mandatory-metric accounting (canonical candidate)")
    out.append("")
    out.append("`empty` = family-contract field recorded blank; "
               "`sentinel:<v>` = populated with a placeholder "
               f"({sorted(SENTINELS)}) that means 'not recorded'. "
               "Both fail '每层必录指标'; the strict checker's non-empty test "
               "sees neither the sentinel nor (on a non-admitted sample) the "
               "gap.")
    out.append("")
    out.append("| RunID | layer | kind | field | state |")
    out.append("|---|---|---|---|---|")
    for r in rows:
        for g in (r.get("field_gaps") or [])[:40]:
            out.append(f"| {r['run_id']} | {g['layer']} | {g['kind']} | "
                       f"{g['field']} | {g['state']} |")
        for g in (r.get("checker_missing_metrics") or [])[:40]:
            out.append(f"| {r['run_id']} | {g[0]} | {g[2]} | {g[1]} | "
                       f"checker_missing_mandatory_metric |")
    out.append("")
    out.append("## All candidate streams per RunID (multiple outdirs exist)")
    out.append("")
    out.append("| RunID | candidate stream | status | events | terminal | "
               "admitted |")
    out.append("|---|---|---|---|---|---|")
    for r in rows:
        for c in r.get("all_candidates") or [{"stream": "-",
                                              "stream_status": r["stream_status"],
                                              "event_count": "n/a"}]:
            term = "(none)"
            adm = "n/a"
            cc = c.get("check_chain")
            ca = c.get("check_admission")
            if cc:
                f = cc.get("faults") or {}
                if f:
                    k = max(f, key=lambda k2: len(f[k2]["path_event_ids"]))
                    term = f[k]["terminal"]
            if ca:
                adm = ca.get("admitted")
            out.append(f"| {r['run_id']} | `{c['stream']}` | "
                       f"{c['stream_status']} | {c['event_count']} | {term} | "
                       f"{adm} |")
    out.append("")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-id", action="append", default=[],
                    help="RunID to judge (repeatable); default = all 12")
    ap.add_argument("--stream", help="explicit stream path (single RunID)")
    ap.add_argument("--root", action="append", default=[],
                    help=f"search root (repeatable); default {DEFAULT_ROOT}")
    ap.add_argument("--json", help="write JSON report here")
    ap.add_argument("--md", help="write markdown table here")
    args = ap.parse_args()

    run_ids = args.run_id or CANONICAL_12
    roots = args.root or [DEFAULT_ROOT]
    checker_blob = hashlib.sha256(Path(C.__file__).read_bytes()).hexdigest()
    rows = [evaluate_run_id(rid, roots,
                            args.stream if (args.stream and len(run_ids) == 1)
                            else None)
            for rid in run_ids]
    import datetime
    meta = {
        "checker_blob": checker_blob,
        "checker_module": str(C.__file__),
        "checker_commit": "d32cdfe9 (cherry-pick -x of 9a7da7cf, blob "
                          "2191e98b = r6-gate strict checker)",
        "canonical_12": CANONICAL_12,
        "falsely_full_historical": FALSELY_FULL,
        "previously_incomplete_historical": PREVIOUSLY_INCOMPLETE,
        "roots": [str(Path(r).resolve()) for r in roots],
        "line_format": "PROP-EVT: kind=<k> key=value …",
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "caveat": ("Provisional: lane B2-v2 is concurrently changing checker "
                   "semantics (L5 = real detection event; containment option "
                   "reachability; stronger cross-request guard). This table "
                   "must be RE-RUN after B2-v2 lands."),
    }
    doc = {"meta": meta, "rows": rows}
    if args.json:
        Path(args.json).write_text(json.dumps(doc, indent=1,
                                              ensure_ascii=False))
        print(f"wrote {args.json}")
    if args.md:
        Path(args.md).write_text(render_md(rows, meta))
        print(f"wrote {args.md}")
    if not args.json and not args.md:
        for r in rows:
            print(f"=== {r['run_id']}  [{r['stream_status']}] ===")
            if r["stream_status"] == "MISSING":
                print("  MISSING — no prop_evt stream found under "
                      f"{roots}")
                continue
            print(f"  stream: {r['stream']} sha={r['stream_sha256'][:16]} "
                  f"events={r['event_count']}")
            print(f"  oracle: {r.get('oracle_outcome')} "
                  f"({r.get('oracle_source')})")
            print(f"  kinds : {_fmt_layers(r)}")
            print(f"  keys  : {_fmt_keys(r)}")
            print(f"  verdict: {_fmt_verdict(r)}")
            if r.get("forbidden"):
                print(f"  forbidden: {r['forbidden']}")
            if r.get("cross_edges"):
                ce = r["cross_edges"]
                print(f"  path stamped request_ids: "
                      f"{ce.get('path_stamped_request_ids')} "
                      f"(chain has {ce.get('chain_stamped_request_id_count')} "
                      f"distinct)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
