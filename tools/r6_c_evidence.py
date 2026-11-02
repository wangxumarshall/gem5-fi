"""Shared reader for R6-C (L1d-Cache / CHAOSCache) seed evidence.

One seed lives in ``<root>/manifest.json`` plus ``<root>/<RUN_ID>/`` holding
``cell_results.json``, ``chain_report.json`` and ``seed<N>/`` with the raw
propagation streams.  Everything here is read-only; nothing is inferred or
normalised beyond parsing.

This module is the cache-family sibling of ``r6_w1_evidence`` (LSQFwd).  The
two deliberately stay separate: the injection log format, funnel line and the
event-kind vocabulary differ per family, and reusing the LSQFwd table would
silently mislabel cache kinds.
"""
import gzip
import hashlib
import json
import os
import re

BIN_SHA256 = "REPLACED_AT_RUNTIME"  # set by the caller from the manifest

# ONE classifier, no drift: the observation-layer table is the authoritative
# `tools/lsu_prop_fields.KIND_LAYER` (also consumed by lsu_chain_check).  Do
# not fork it here.  A local fallback exists only so this reader can still
# render evidence if the sibling module is moved; it is never preferred.
try:
    import lsu_prop_fields as _P
    KIND_LAYER = dict(_P.KIND_LAYER)
except Exception:                                    # pragma: no cover
    KIND_LAYER = {
        "inj": "L0", "addr_form": "L1", "mem_req": "L2", "resp": "L3",
        "taint_reg": "L4", "consumer": "L4", "errant_commit": "L4",
        "store_not_retired": "L4", "squash_discarded": "L4",
        "cache_access": "L1", "cache_return": "L2", "cache_fill": "L2",
        "cache_evict": "L2", "mshr_free": "L2", "cache_writeback": "L3",
        "lq_complete": "L3", "chain_end": "L5",
    }

# Kept as the documented cache-family name; it is the same object content.
CACHE_KIND_LAYER = KIND_LAYER
GENERIC_KIND_LAYER = KIND_LAYER


def layer_of(kind, evt=None):
    """Observation layer, with the D1 L5 promotion and lifecycle exclusion.

    Mirrors `lsu_chain_check._layer_of`: a real detection event (explicit
    detection_layer/outcome) occupies L5; chain_end is a lifecycle marker and
    occupies no layer.
    """
    if kind == "chain_end":
        return "—"
    if evt is not None and evt.get("detection_layer") in ("L1", "L2", "L3",
                                                          "L4", "L5"):
        return evt["detection_layer"]
    if evt is not None and evt.get("outcome") and evt.get("corr") == "taint_prop":
        return "L5"
    return KIND_LAYER.get(kind, "—")

CACHE_KIND_SEMANTICS = {
    "inj": "CHAOSCache 在 L1d 数据/标签/状态位注入故障",
    "cache_access": "需求访问命中被污染 cache line（L1 lookup）",
    "cache_return": "cache 命中返回被污染数据",
    "cache_fill": "line fill 携带被污染数据进入 cache",
    "cache_evict": "被污染 line 被替换/驱逐",
    "cache_writeback": "被污染 line 写回下一级",
    "mem_req": "缓存未命中产生存储请求",
    "request_fork": "地址广播把同一被污染 line 归因到新请求（显式桥）",
    "resp": "load 响应携带被污染数据返回执行级",
    "lq_complete": "load 队列完成",
    "taint_reg": "目的物理寄存器被标记为 tainted",
    "consumer": "污点寄存器的后续消费者指令",
    "errant_commit": "被污染指令在错误数据下提交（L5 errant commit）",
    "store_not_retired": "store 生命周期结束但未 retire（containment）",
    "squash_discarded": "未提交指令随 squash 丢弃",
    "chain_end": "生命周期结束标记（仿真结束，不是 L5 证据）",
}

# Only these kinds are useful for the narrative beyond each fault's canonical
# path; capturing every consumer would blow up memory on large streams.
CAPTURE_KINDS = {
    "inj", "errant_commit", "store_not_retired", "squash_discarded",
    "chain_end", "request_fork",
}

DEFAULT_ROOT = "/home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/runs"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_seeds(root):
    """Yield seed roots (dirs holding manifest.json) under ``root``.

    Accepts both the flat layout (``<root>/<RUNID>_s<SEED>/manifest.json``) and
    an explicitly named root.  Returns ``(root, run_id, seed)`` tuples.
    """
    out = []
    if os.path.isfile(os.path.join(root, "manifest.json")):
        cands = [root]
    else:
        cands = []
        for name in sorted(os.listdir(root)):
            p = os.path.join(root, name)
            if os.path.isdir(p) and os.path.isfile(os.path.join(p, "manifest.json")):
                cands.append(p)
    for p in cands:
        try:
            man = json.load(open(os.path.join(p, "manifest.json")))
            out.append((p, man.get("run_id", ""), int(man.get("seed", 0))))
        except Exception:
            continue
    return out


def load_sample(root):
    """Parse one seed root.  Raises on structurally missing files."""
    man = json.load(open(os.path.join(root, "manifest.json")))
    run_id = man["run_id"]
    seed = int(man["seed"])
    inner = os.path.join(root, run_id)
    seed_dir = os.path.join(inner, f"seed{seed}")
    sample = {
        "root": root,
        "manifest": man,
        "run_id": run_id,
        "seed": seed,
        "inner": inner,
        "seed_dir": seed_dir,
        "paths": {
            "manifest": os.path.join(root, "manifest.json"),
            "cell_results": os.path.join(inner, "cell_results.json"),
            "cell_chain_report": os.path.join(inner, "chain_report.json"),
            "seed_chain_report": os.path.join(seed_dir, "chain_report.json"),
            "prop_evt": os.path.join(seed_dir, "prop_evt.txt.gz"),
            "prop_trace": os.path.join(seed_dir, "prop_trace.csv.gz"),
            "stats": os.path.join(seed_dir, "stats.txt"),
            "run_out": os.path.join(seed_dir, "run.out"),
            "inj_log": os.path.join(seed_dir, "cache_injections.log"),
            "config": os.path.join(seed_dir, "config.json"),
        },
    }
    sample["cell"] = json.load(open(sample["paths"]["cell_results"]))
    sample["chain"] = json.load(open(sample["paths"]["seed_chain_report"]))
    return sample


def fault_path_ids(chain):
    ids = {}
    for fid, f in (chain.get("faults") or {}).items():
        ids[str(fid)] = [str(x) for x in (f.get("path_event_ids") or [])]
    return ids


def scan_events(path, wanted_ids=(), capture_kinds=CAPTURE_KINDS):
    """Stream prop_evt.txt.gz once: counts, per-fault census, wanted events."""
    wanted = {str(x) for x in wanted_ids}
    captured = {}
    kinds = {}
    per_fault = {}
    n = 0
    last_tick = -1
    nonmonotonic = 0
    with gzip.open(path, "rt", errors="replace") as f:
        for line in f:
            if not line.startswith("PROP-EVT: "):
                continue
            d = {}
            for tok in line[10:].split():
                k, _, v = tok.partition("=")
                d[k] = v
            n += 1
            k = d.get("kind", "")
            kinds[k] = kinds.get(k, 0) + 1
            fid = d.get("fault_id", "")
            c = per_fault.setdefault(fid, {})
            c[k] = c.get(k, 0) + 1
            t = int(d.get("tick") or -1)
            if t < last_tick:
                nonmonotonic += 1
            last_tick = max(last_tick, t)
            eid = d.get("event_id")
            if eid in wanted or k in capture_kinds:
                captured[eid] = d
    return {"count": n, "kind_counts": kinds, "per_fault_counts": per_fault,
            "captured": captured, "nonmonotonic_tick": nonmonotonic,
            "last_tick": last_tick}


_INJ = re.compile(r"^Tick:\s*(\d+),\s*Cache Block Addr:\s*([0-9a-fA-Fx]+),"
                  r"\s*Byte Offset:\s*(\d+),\s*FaultType:\s*(\S+),"
                  r"\s*Mask:\s*(\S+)")


def parse_injection_log(path):
    """CHAOSCache log row: Tick, Cache Block Addr, Byte Offset, FaultType, Mask."""
    rows = []
    if not os.path.isfile(path):
        return rows
    with open(path, errors="replace") as f:
        for line in f:
            m = _INJ.match(line.strip())
            if m:
                rows.append({
                    "Tick": m.group(1),
                    "Cache Block Addr": m.group(2),
                    "Byte Offset": m.group(3),
                    "FaultType": m.group(4),
                    "Mask": m.group(5),
                })
    return rows


_FUNNEL = re.compile(r"^FUNNEL:\s*attempted=(\d+)\s+eligible=(\d+)"
                     r"\s+injected=(\d+)")


def parse_funnel(path):
    """Last FUNNEL line wins (the first may be the pre-protection attempt)."""
    last = None
    if not os.path.isfile(path):
        return None
    with open(path, errors="replace") as f:
        for line in f:
            m = _FUNNEL.match(line.strip())
            if m:
                last = {"attempted": int(m.group(1)),
                        "eligible": int(m.group(2)),
                        "injected": int(m.group(3))}
    return last


def parse_run_out(path):
    out = {"funnel": None, "segv": None, "detect_lines": []}
    if not os.path.isfile(path):
        return out
    for line in open(path, errors="replace").read().splitlines():
        if line.startswith("CHAOS_GUEST_SEGV_EXIT:"):
            out["segv"] = line
        elif line.startswith("CHAOS_DETECT:"):
            out["detect_lines"].append(line)
    return out


def parse_stats(path):
    stats = {}
    if not os.path.isfile(path):
        return stats
    with open(path, errors="replace") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2 and not line.startswith("#"):
                stats[parts[0]] = parts[1]
    return stats


def load_streams(sample):
    """Everything a doc/audit needs, with one pass over the event stream."""
    ids = fault_path_ids(sample["chain"])
    wanted = [i for v in ids.values() for i in v]
    ev = scan_events(sample["paths"]["prop_evt"], wanted)
    runout = parse_run_out(sample["paths"]["run_out"])
    runout["funnel"] = parse_funnel(sample["paths"]["inj_log"])
    return {
        "path_ids": ids,
        "events": ev,
        "inj": parse_injection_log(sample["paths"]["inj_log"]),
        "runout": runout,
        "stats": parse_stats(sample["paths"]["stats"]),
    }
