"""Shared reader for R6-S W1 (LSQFwd) seed evidence.

One seed lives in ``<root>/manifest.json`` plus ``<root>/<RUN_ID>/`` holding
``cell_results.json``, ``chain_report.json`` and ``seed<N>/`` with the raw
propagation streams.  Everything here is read-only; nothing is inferred or
normalised beyond parsing.
"""
import gzip
import hashlib
import json
import os
import re

BIN_SHA256 = "6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4"

CANARY_ROOT = "/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2/w1canary/S01-F1-W1_s1"
W1E_ROOT = "/home/sdc/gem5-fi-ding/runs/lsu/r6_s_repair2/w1e"

# Layer labels used only for display.  The authoritative layer evidence is the
# per-fault `edges` map in chain_report.json; audit_r6_w1_docs.py checks that
# every claimed layer agrees with the edge that carries it.
KIND_LAYER = {
    "inj": "L0",
    "lsq_push": "L1",
    "sq_entry": "L1",
    "lsq_sendfrag": "L2",
    "mem_req": "L2",
    "tlb_translate": "L2",
    "request_fork": "L2",
    "lsq_fwd": "L2",
    "resp": "L3",
    "sq_writeback": "L3",
    "sq_complete": "L3",
    "taint_reg": "L4",
    "consumer": "L4",
    "squash_discarded": "L4",
    "store_not_retired": "L5",
    "errant_commit": "L5",
    "chain_end": "—",
}
KIND_SEMANTICS = {
    "inj": "CHAOSLSQFwd 在 store->load forward 路径注入单比特翻转",
    "sq_entry": "被污染的 store 数据进入 Store Queue 条目",
    "lsq_fwd": "该 store 的数据被 forward 给年轻 load（故障值离开 SQ）",
    "resp": "load 响应携带被污染的数据返回执行级",
    "taint_reg": "目的架构/物理寄存器被标记为 tainted",
    "consumer": "污点寄存器的后续消费者指令",
    "errant_commit": "被污染的指令在错误数据下提交（L5 errant commit）",
    "store_not_retired": "store 生命周期结束但未 retire（containment 检查点）",
    "squash_discarded": "未提交 store 随 squash 丢弃",
    "sq_writeback": "SQ 写回/包构建",
    "sq_complete": "SQ 条目完成",
    "lsq_push": "LSQ 入队",
    "lsq_sendfrag": "LSQ 请求分片发送",
    "mem_req": "存储请求创建",
    "tlb_translate": "地址翻译",
    "request_fork": "请求分叉",
    "chain_end": "生命周期结束标记（仿真结束，不是 L5 证据）",
}

CAPTURE_KINDS = {"inj", "errant_commit", "store_not_retired", "squash_discarded",
                 "chain_end"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_roots(extra=()):
    roots = [CANARY_ROOT]
    if os.path.isdir(W1E_ROOT):
        for name in sorted(os.listdir(W1E_ROOT)):
            p = os.path.join(W1E_ROOT, name)
            if os.path.isdir(p) and re.match(r"^S\d{2}-[A-Z]\d+-W1_s[123]$", name):
                roots.append(p)
    roots.extend(extra)
    seen, out = set(), []
    for r in roots:
        r = os.path.abspath(r)
        if r not in seen and os.path.isfile(os.path.join(r, "manifest.json")):
            seen.add(r)
            out.append(r)
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
            "inj_log": os.path.join(seed_dir, "lsq_fwd_injections.log"),
            "config": os.path.join(seed_dir, "config.json"),
        },
    }
    sample["cell"] = json.load(open(sample["paths"]["cell_results"]))
    sample["chain"] = json.load(open(sample["paths"]["seed_chain_report"]))
    return sample


def fault_path_ids(chain):
    ids = {}
    for fid, f in (chain.get("faults") or {}).items():
        ids[fid] = [str(x) for x in (f.get("path_event_ids") or [])]
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


def parse_injection_log(path):
    rows = []
    with open(path, errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("Cycle:"):
                continue
            d = {}
            for tok in line.split(", "):
                k, _, v = tok.partition(": ")
                d[k.strip()] = v.strip()
            rows.append(d)
    return rows


_L0 = re.compile(r"CHAOS_L0_FUNNEL:\s+CHAOSLSQFwd\s+attempted=(\d+)\s+"
                 r"eligible=(\d+)\s+injected=(\d+)\s+activated=(\d+)")
_TRIG = re.compile(r"CHAOS_LSU_TRIGGER:\s+injector=CHAOSLSQFwd\s+tier=(\S+)\s+"
                   r"attempted=(\d+)\s+eligible=(\d+)\s+injected=(\d+)\s+"
                   r"first_eligible_tick=(\d+)\s+last_eligible_tick=(\d+)")


def parse_funnel_line(text):
    m = _L0.search(text)
    if not m:
        return None
    return dict(zip(("attempted", "eligible", "injected", "activated"),
                    (int(x) for x in m.groups())))


def parse_run_out(path):
    text = open(path, errors="replace").read()
    out = {"funnel": parse_funnel_line(text), "trigger": None,
           "segv": None, "detect_lines": []}
    m = _TRIG.search(text)
    if m:
        out["trigger"] = {"tier": m.group(1), "attempted": int(m.group(2)),
                          "eligible": int(m.group(3)), "injected": int(m.group(4)),
                          "first_eligible_tick": int(m.group(5)),
                          "last_eligible_tick": int(m.group(6))}
    for line in text.splitlines():
        if line.startswith("CHAOS_GUEST_SEGV_EXIT:"):
            out["segv"] = line
        elif line.startswith("CHAOS_DETECT:"):
            out["detect_lines"].append(line)
    return out


def parse_stats(path):
    stats = {}
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
    if runout["funnel"] is None:
        # CHAOSLSQFwd's end-of-run funnel line is written to the injection log.
        runout["funnel"] = parse_funnel_line(
            open(sample["paths"]["inj_log"], errors="replace").read())
    return {
        "path_ids": ids,
        "events": ev,
        "inj": parse_injection_log(sample["paths"]["inj_log"]),
        "runout": runout,
        "stats": parse_stats(sample["paths"]["stats"]),
    }
