#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_seed_audit.py — 逐 seed 证据与 Markdown 审计（门禁 10）。

审计对象：runs/fsu/<RunID>/seed<N>/attempt-<k>/
检查:
  - manifest / chain_report / seed Markdown 的 RunID、seed、workload、
    gem5 二进制、源码 HEAD 身份一致；
  - prop_evt 可完整解析、gzip 未截断、事件 sample_run_id 全为本 seed；
  - chain_report 与原始事件流重算结果一致（terminal/admitted/violations）；
  - Markdown 事件表的每个 event_id 在原始流中存在，kind/parent 一致；
    原始主链每个 event_id 在 Markdown 中出现；
  - Markdown 的 terminal / admitted 与 chain_report 一致；
  - evidence_sha256.json 中每个文件哈希仍匹配；
  - stats.txt 非空；admitted=True 且 violations=[]。

用法: python3 tools/fsu_seed_audit.py <attempt_dir>
退出码 0 = 全部通过；1 = 有失败项。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_chain_check as C  # noqa: E402
import fsu_prop_fields as P  # noqa: E402
import fsu_config_profile as CP  # noqa: E402


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _md_event_rows(md: str):
    rows, inside = [], False
    for line in md.splitlines():
        if line.startswith("## 5."):
            inside = True
            continue
        if inside and line.startswith("## 6."):
            break
        if not inside or not line.startswith("|"):
            continue
        if line.startswith("|---") or "| kind | event_id |" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3:
            rows.append(cells)
    return rows


def _md_value(md: str, label: str):
    m = re.search(re.escape(label) + r"\s*\**([^*\n]+?)\**\s*$", md, re.M)
    return m.group(1).strip() if m else None


FP_FIELDS = {
    "fp64": {
        "sign": (63, 63), "exp_hi": (58, 62), "exp_lo": (52, 57),
        "mant_hi": (35, 51), "mant_mid": (18, 34), "mant_lo": (0, 17),
    },
    "fp32": {
        "sign": (31, 31), "exp_hi": (27, 30), "exp_lo": (23, 26),
        "mant_hi": (15, 22), "mant_mid": (8, 14), "mant_lo": (0, 7),
    },
}
FIELD_SUBMODEL = {
    "sign": "FP04-a", "exp_hi": "FP04-b", "exp_lo": "FP04-b",
    "mant_hi": "FP04-c", "mant_mid": "FP04-c", "mant_lo": "FP04-c",
}
MODE_FIELDS = {"uniform", "recurring_result_stuck", "fma_intermediate",
               "rounding_sub", "permanent_stuck"}
ROOT_KINDS = ("fault_applied", "fault_installed")


def _mask_hex(value, default=None):
    """Parse a PROP-EVT mask (0x... string or decimal) to int."""
    text = str(value or "").strip()
    if not text:
        return default
    try:
        return int(text, 0)
    except ValueError:
        return None


def _hex_int(value, default=0):
    text = str(value or "").strip()
    if not text:
        return default
    try:
        return int(text, 16)
    except ValueError:
        return None


def _dec_int(value, default=None):
    """bit_indices / field_lo / field_hi are emitted as decimal strings."""
    text = str(value or "").strip()
    if not text:
        return default
    try:
        return int(text, 10)
    except ValueError:
        return None


def _field_violations(evt):
    """Validate one L0 root's field/lane/mask semantics.

    Legacy D2 events have no `precision`/`lane_mask`/`full_*`; they are
    interpreted as FP64, lane_width=64, lane_offset=0 (their emitted
    contract). New D3 events carry all fields explicitly.
    """
    v = []
    fid = str(evt.get("fault_id", "?"))
    field = str(evt.get("field", "")).strip()
    lane_w = int(str(evt.get("lane_width") or 64))
    lane_o = int(str(evt.get("lane_offset") or 0))
    if lane_w not in (8, 16, 32, 64):
        v.append(f"fault {fid}: invalid lane_width {lane_w}")
        return v
    if lane_o < 0 or lane_o >= 128 // lane_w:
        v.append(f"fault {fid}: invalid lane_offset {lane_o} for width {lane_w}")
        return v
    prec = str(evt.get("precision", "")).strip()
    if not prec and field in FP_FIELDS["fp64"]:
        prec = "fp64"  # legacy D2 event (only FP64 fields existed)
    if field not in MODE_FIELDS:
        if prec not in FP_FIELDS:
            v.append(f"fault {fid}: unknown field '{field}' / precision '{prec}'")
            return v
        lo, hi = FP_FIELDS[prec][field] if field in FP_FIELDS[prec] else (None, None)
        if lo is None:
            v.append(f"fault {fid}: field '{field}' not in {prec} table")
            return v
        want_sub = FIELD_SUBMODEL.get(field)
        sub = str(evt.get("submodel", "")).strip()
        # FP04-d is the NEON lane-result domain, orthogonal to the field
        # axis: a lane-selected run (lane_offset > 0) may carry any field.
        lane_domain = (sub == "FP04-d" and lane_o > 0)
        if want_sub and sub and sub != want_sub and not lane_domain:
            v.append(f"fault {fid}: field {field} requires {want_sub}, "
                     f"event submodel={sub}")
    mask = _hex_int(evt.get("fault_mask"))
    if mask is None or mask == 0:
        v.append(f"fault {fid}: missing/zero fault_mask")
        return v
    if lane_w < 64 and (mask >> lane_w):
        v.append(f"fault {fid}: fault_mask 0x{mask:x} exceeds lane_width {lane_w}")
    bit = _dec_int(evt.get("bit_indices"), default=None)
    if bit is None:
        v.append(f"fault {fid}: missing bit_indices")
        return v
    lane_base = lane_o * lane_w
    rel = bit - lane_base
    if rel < 0 or rel >= lane_w:
        v.append(f"fault {fid}: absolute bit {bit} outside lane "
                 f"{lane_o} width {lane_w}")
        return v
    if field not in MODE_FIELDS:
        lo, hi = FP_FIELDS[prec][field]
        if not (lo <= rel <= hi):
            v.append(f"fault {fid}: bit {rel} outside field {field} [{lo},{hi}]")
        if mask != (1 << rel):
            v.append(f"fault {fid}: fault_mask 0x{mask:x} != 1<<{rel}")
        flo = _dec_int(evt.get("field_lo"))
        fhi = _dec_int(evt.get("field_hi"))
        if flo is not None and fhi is not None and (flo, fhi) != (lo, hi):
            v.append(f"fault {fid}: field_lo/hi ({flo},{fhi}) != "
                     f"{field} ({lo},{hi})")
        bil = _dec_int(evt.get("bit_in_lane"))
        if bil is not None and bil != rel:
            v.append(f"fault {fid}: bit_in_lane {bil} != {rel}")
    lane_mask = _hex_int(evt.get("lane_mask"), default=None)
    if lane_mask is not None:
        want = mask << lane_base
        if lane_mask != want:
            v.append(f"fault {fid}: lane_mask 0x{lane_mask:x} != "
                     f"fault_mask<<{lane_base} (0x{want:x})")
    # [FSU][F5] A permanent stuck-at target keeps ONE fixed mask/polarity.
    # Its before/after pair is a FORCED value, not an XOR: when the correct
    # bit already equals the stuck polarity the pair legitimately differs by
    # zero (exposed-but-not-activated).
    permanent = field == "permanent_stuck"
    pol = None
    if permanent:
        fixed = _mask_hex(evt.get("fixed_mask"), default=None)
        if fixed is None or fixed != mask:
            v.append(f"fault {fid}: fixed_mask {evt.get('fixed_mask')!r} "
                     f"!= fault_mask 0x{mask:x}")
        pol = _dec_int(evt.get("stuck_polarity"), default=None)
        if pol not in (0, 1):
            v.append(f"fault {fid}: stuck_polarity {evt.get('stuck_polarity')!r} "
                     "must be 0 (SA0) or 1 (SA1)")
            pol = None
    before = _hex_int(evt.get("before"), default=None)
    after = _hex_int(evt.get("after"), default=None)
    if before is not None and after is not None:
        if permanent and pol is not None:
            want = (before | mask) if pol else (before & ~mask)
            if after != want:
                v.append(f"fault {fid}: stuck_after 0x{after:x} != "
                         f"forced(before, mask, pol={pol}) 0x{want:x}")
        elif (before ^ after) != mask:
            v.append(f"fault {fid}: before^after 0x{before ^ after:x} "
                     f"!= fault_mask 0x{mask:x}")
    full_before = _hex_int(evt.get("full_before"), default=None)
    full_after = _hex_int(evt.get("full_after"), default=None)
    if full_before is not None and full_after is not None:
        want = mask << lane_base
        if permanent and pol is not None:
            forced = (full_before | want) if pol else (full_before & ~want)
            if full_after != forced:
                v.append(f"fault {fid}: full_after 0x{full_after:x} != "
                         f"forced full_before 0x{forced:x}")
        elif (full_before ^ full_after) != want:
            v.append(f"fault {fid}: full_before^full_after "
                     f"0x{full_before ^ full_after:x} != lane_mask 0x{want:x}")
    return v


def _decode_violations(evt):
    """Validate the real-instruction decode provenance on a new-gate root.

    Legacy D2/D3 events have no decoded_kind; they are legacy-valid and are
    reported separately, never silently upgraded to decoded evidence.
    """
    kind = str(evt.get("decoded_kind", "")).strip()
    if not kind:
        return []
    v = []
    fid = str(evt.get("fault_id", "?"))
    reliable = str(evt.get("decoded_reliable", "")).strip()
    pm = str(evt.get("precision_match", "")).strip()
    lm = str(evt.get("lane_match", "")).strip()
    if reliable not in ("1", "true", "True"):
        v.append(f"fault {fid}: decoded_reliable != 1")
    if pm not in ("1", "true", "True"):
        v.append(f"fault {fid}: precision_match != 1")
    if lm not in ("1", "true", "True"):
        v.append(f"fault {fid}: lane_match != 1")
    if kind not in ("scalar_vfp", "neon_vector"):
        v.append(f"fault {fid}: decoded_kind {kind} is not injectable")
    bits = str(evt.get("instruction_bits", "")).strip()
    if not bits:
        v.append(f"fault {fid}: missing instruction_bits")
    dec_p = str(evt.get("decoded_precision", "")).strip()
    man_p = str(evt.get("manifest_precision", "")).strip()
    if dec_p not in ("fp32", "fp64"):
        v.append(f"fault {fid}: decoded_precision {dec_p!r} not fp32/fp64")
    if man_p not in ("fp32", "fp64"):
        v.append(f"fault {fid}: manifest_precision {man_p!r} not fp32/fp64")
    if dec_p in ("fp32", "fp64") and man_p in ("fp32", "fp64") and dec_p != man_p:
        v.append(f"fault {fid}: decoded {dec_p} != manifest {man_p}")
    try:
        ew = int(str(evt.get("decoded_element_width", "")))
        lanes = int(str(evt.get("decoded_lanes", "")))
    except ValueError:
        v.append(f"fault {fid}: missing decoded element width / lanes")
        return v
    lane_w = int(str(evt.get("lane_width") or 64))
    lane_o = int(str(evt.get("lane_offset") or 0))
    man_lw = int(str(evt.get("manifest_lane_width") or lane_w))
    if ew <= 0 or lanes <= 0:
        v.append(f"fault {fid}: invalid decoded width/lanes {ew}/{lanes}")
    if man_lw != lane_w:
        v.append(f"fault {fid}: manifest_lane_width {man_lw} != {lane_w}")
    if kind == "scalar_vfp":
        if lanes != 1 or lane_o != 0:
            v.append(f"fault {fid}: scalar decode lanes={lanes} offset={lane_o}")
        if not (lane_w == ew or (ew == 32 and lane_w == 64)):
            v.append(f"fault {fid}: scalar element {ew} vs lane_width {lane_w}")
    else:
        if lane_w != ew:
            v.append(f"fault {fid}: lane_width {lane_w} != element {ew}")
        if not (0 <= lane_o < lanes):
            v.append(f"fault {fid}: lane_offset {lane_o} outside {lanes} lanes")
    return v


def _scheduled_faults(manifest, report):
    expected = report.get("expected_injections")
    if expected is not None:
        return int(expected)
    return int((manifest.get("injector") or {}).get("max_faults", 1))


def _md_fault_rows(md: str):
    """Parse the '### 逐 fault 终局' table → {fault_id: cells}."""
    rows, inside = {}, False
    for line in md.splitlines():
        if line.startswith("### 逐 fault 终局"):
            inside = True
            continue
        if inside and (line.startswith("## ") or line.startswith("- 结局标签")):
            break
        if not inside or not line.startswith("|"):
            continue
        if line.startswith("|---") or "| fault | terminal |" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 8 and cells[0] not in ("fault", "—"):
            rows[cells[0]] = cells
    return rows


def audit_attempt(attempt: Path):
    attempt = Path(attempt)
    checks, failures = [], []

    def check(name, ok):
        checks.append((name, ok))
        if not ok:
            failures.append(name)

    man_path = attempt / "manifest.json"
    rep_path = attempt / "chain_report.json"
    if not man_path.exists() or not rep_path.exists():
        return {"ok": False, "checks": [], "failures": ["manifest/chain_report missing"]}
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    report = json.loads(rep_path.read_text(encoding="utf-8"))
    chain = report.get("chain", {})
    runid = manifest["run_id"]
    seed = manifest["seed"]
    sample = manifest.get("sample_run_id") or f"s{seed}"

    md_path = attempt / f"{runid}-seed{seed}.md"
    check("seed Markdown 存在", md_path.exists())
    md = md_path.read_text(encoding="utf-8") if md_path.exists() else ""

    # 1. 身份一致性
    check("RunID 一致", report.get("run_id") == runid and runid in md)
    check("seed/sample_run_id 一致",
          report.get("seed") == seed and report.get("sample_run_id") == sample
          and sample in md)
    check("workload 二进制身份一致",
          report.get("workload_sha256") == manifest.get("workload_sha256"))
    check("gem5 二进制身份一致",
          report.get("gem5_sha256") == manifest.get("gem5_sha256"))
    check("源码 HEAD 一致", report.get("source_head") == manifest.get("source_head"))

    # 2. 原始事件流
    prop = attempt / "inject/prop_evt.txt.gz"
    check("prop_evt 存在", prop.exists())
    events, truncated, reason = P.read_stream(prop) if prop.exists() else ([], True, "missing")
    check(f"prop_evt 未截断（reason={reason or 'ok'}）", not truncated)
    bad_identity = [e.get("event_id") for e in events
                    if str(e.get("run_id")) != runid
                    or str(e.get("sample_run_id")) != sample]
    check(f"事件身份全为本 seed（越界 {len(bad_identity)}）", not bad_identity)

    # 2.1 字段 / lane / mask 语义（新增门禁，绝不放宽既有门禁）
    roots = [e for e in events if str(e.get("kind")) in ROOT_KINDS]
    scheduled = _scheduled_faults(manifest, report)
    check(f"scheduled({scheduled}) = fault_roots({len(roots)})",
          scheduled == len(roots))
    root_ids = {str(e.get("fault_id")) for e in roots}
    activated_ids = {str(e.get("fault_id")) for e in events
                     if str(e.get("kind")) == "operand_read"
                     and str(e.get("activated")) == "1"}
    check("每个 injected fault 均真实激活",
          bool(root_ids) and activated_ids == root_ids)
    # [FSU][F5] Activation is a property of an exposure, not of a new fault.
    # A permanent-fault root must have at least one activated exposure; the
    # exposure events must never mint additional fault_ids.
    for root in roots:
        if str(root.get("kind")) != "fault_installed":
            continue
        fid = str(root.get("fault_id"))
        acts = [e for e in events
                if str(e.get("kind")) == "exposure"
                and str(e.get("fault_id")) == fid
                and str(e.get("activated")) == "1"]
        check(f"fault {fid} 永久故障至少一次 activated exposure",
              bool(acts))
    for root in roots:
        fid = str(root.get("fault_id"))
        viol = _field_violations(root)
        check(f"fault {fid} 字段/lane/mask 语义", not viol)
        if viol:
            failures.extend(viol)
        dviol = _decode_violations(root)
        check(f"fault {fid} 真实指令解码匹配", not dviol)
        if dviol:
            failures.extend(dviol)
    guard = bool(((manifest.get("injector") or {}).get("fpu_mode") or {})
                 .get("decode_guard"))
    decoded_roots = [r for r in roots if str(r.get("decoded_kind", "")).strip()]
    if guard:
        check("decode_guard: 所有 root 含真实解码字段",
              len(decoded_roots) == len(roots) and bool(roots))
    for key in ("model_id", "submodel", "freq", "load_id"):
        want = manifest.get(key)
        if want:
            got = {str(e.get(key)) for e in roots}
            check(f"事件 {key} 与 manifest 一致", got == {str(want)})
    by_fault = {}
    for e in events:
        by_fault.setdefault(str(e.get("fault_id")), []).append(e)
    for fid, evs in by_fault.items():
        fields = {str(e.get("field")) for e in evs if str(e.get("field"))}
        check(f"fault {fid} 全链 field 一致", len(fields) <= 1)

    # 3. 链重算与 chain_report 一致（逐 fault）
    recomputed = C.check_stream(prop, run_id=runid, sample_run_id=sample) \
        if prop.exists() else {"faults": {}, "admitted_faults": [], "truncated": True}
    recomputed_faults = recomputed.get("faults", {})
    check("重算 admitted_faults 一致",
          recomputed.get("admitted_faults") == chain.get("admitted_faults"))
    check("重算 truncated 一致", recomputed.get("truncated") == chain.get("truncated"))
    # Every injected fault must have a chain; one fault reaching L5 must not
    # certify the others.
    check("事件流 fault 数 = 注入数",
          len(recomputed_faults) == report.get("actual_injections",
                                               len(recomputed_faults)))
    check("所有 fault 均 admitted",
          bool(recomputed_faults)
          and all(r.get("admitted") for r in recomputed_faults.values()))
    check("所有 fault 均 certified",
          bool(recomputed_faults)
          and all(r.get("certified") for r in recomputed_faults.values()))
    for fid, r in recomputed_faults.items():
        old = chain.get("faults", {}).get(fid, {})
        check(f"fault {fid} terminal 一致", r.get("terminal") == old.get("terminal"))
        check(f"fault {fid} violations 一致", r.get("violations") == old.get("violations"))
        check(f"fault {fid} admitted 一致", r.get("admitted") == old.get("admitted"))
        check(f"fault {fid} certified 一致", r.get("certified") == old.get("certified"))

    # 4. Markdown 事件表 ↔ 原始流
    by_id = {str(e.get("event_id")): e for e in events}
    rows = _md_event_rows(md)
    md_ids = [r[1] for r in rows if len(r) > 1]
    for r in rows:
        eid = r[1]
        evt = by_id.get(eid)
        check(f"MD event {eid} 存在于原始流", evt is not None)
        if evt is not None:
            check(f"MD event {eid} kind 一致", r[0] == str(evt.get("kind")))
            check(f"MD event {eid} parent 一致",
                  r[2] == (str(evt.get("parent_event_id")) or "—"))
    # Legacy D0/D2 Markdown has only the singular terminal lines; newer
    # multi-fault docs carry the explicit per-fault table. Both are valid
    # evidence formats, but a new-format doc must cover every fault.
    has_fault_table = "### 逐 fault 终局" in md
    fault_rows = _md_fault_rows(md)
    admitted_fid = None
    for fid, r in chain.get("faults", {}).items():
        if r.get("admitted"):
            admitted_fid = fid
            break
    # A chain with no admitted/certified fault must never pass the gate,
    # even if a tampered report and a regenerated MD agree with each other.
    check("链 admitted=True", chain.get("admitted") is True)
    check("链 certified=True", chain.get("certified") is True)
    check("链 violations=[]", chain.get("violations", []) == [])
    check("存在 admitted fault", admitted_fid is not None)
    check("MD 逐 fault 终局表存在（legacy 单 fault 行）",
          bool(fault_rows) or not has_fault_table)
    # Per-fault Markdown + direct-parent checks.
    for fid, r in sorted(recomputed_faults.items()):
        path_ids = r.get("path_event_ids", [])
        check(f"fault {fid} MD 覆盖主链全部事件",
              all(i in md_ids for i in path_ids))
        path = [by_id[i] for i in path_ids if i in by_id]
        edges_ok = all(
            str(b.get("parent_event_id")) == str(a.get("event_id"))
            for a, b in zip(path, path[1:]))
        check(f"fault {fid} MD/原始流 direct parent", edges_ok)
        cells = fault_rows.get(fid)
        if has_fault_table:
            check(f"fault {fid} MD 逐 fault 终局行存在", cells is not None)
        if cells is not None:
            check(f"fault {fid} MD terminal 一致",
                  cells[1] == str(r.get("terminal")))
            check(f"fault {fid} MD admitted 一致",
                  cells[3] == str(r.get("admitted")))
            check(f"fault {fid} MD certified 一致",
                  cells[4] == str(r.get("certified")))
    if admitted_fid is not None:
        # 5. primary terminal / admitted 一致（兼容单 fault 行）
        term = _md_value(md, "传播链 terminal：")
        check("MD terminal 与 chain_report 一致",
              term is not None and term.strip("* ") == str(
                  chain["faults"][admitted_fid].get("terminal")))
        adm = _md_value(md, "admitted / certified：")
        check("MD admitted/certified 与 chain_report 一致",
              adm is not None and adm.replace(" ", "") in
              (f"{chain['faults'][admitted_fid].get('admitted')}/"
               f"{chain['faults'][admitted_fid].get('certified')}",
               f"{str(chain['faults'][admitted_fid].get('admitted')).lower()}/"
               f"{str(chain['faults'][admitted_fid].get('certified')).lower()}"))

    # 6. 证据哈希
    hp = attempt / "evidence_sha256.json"
    check("evidence_sha256.json 存在", hp.exists())
    if hp.exists():
        hashes = json.loads(hp.read_text(encoding="utf-8"))
        bad = [rel for rel, h in hashes.items()
               if not (attempt / rel).exists() or _sha(attempt / rel) != h]
        check(f"证据 SHA-256 全部匹配（失配 {len(bad)}）", not bad)

    # 7. stats 非空
    stats = attempt / "stats.txt"
    check("stats.txt 非空", stats.exists() and stats.stat().st_size > 0)

    # 7.1 [FSU][D3] Platform profile: a B0 declaration must match the real
    # config.ini of BOTH census and injection. Legacy C3 attempts are not
    # retroactively re-labelled.
    profile = str(manifest.get("config_profile", "") or "")
    if profile == "B0":
        for sub in ("census", "inject"):
            chk = CP.verify_config_profile(
                attempt / sub / "config.ini", "B0")
            check(f"B0 运行态配置匹配（{sub}）", chk["ok"])
    elif profile not in ("", "C3"):
        check(f"未知 config_profile {profile!r}", False)

    # 8. 结论
    if admitted_fid is not None:
        r = chain["faults"][admitted_fid]
        check("admitted=True", r.get("admitted") is True)
        check("violations=[]", r.get("violations") == [])

    return {"ok": not failures, "checks": checks, "failures": failures,
            "attempt": str(attempt)}


def write_audit(attempt: Path):
    """Recompute the audit gate and persist audit.json / audit.md.

    `certified` is computed from the full gate (identity, gzip EOF, parent
    chain, tick monotonicity, L5 witness, stats, evidence hashes, no
    cross-seed data) — never hard-coded.
    """
    import hashlib as _hashlib
    attempt = Path(attempt)
    res = audit_attempt(attempt)
    manifest = json.loads((attempt / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((attempt / "chain_report.json").read_text(encoding="utf-8"))
    chain = report.get("chain", {})
    oracle = report.get("oracle", {})
    prop = attempt / "inject/prop_evt.txt.gz"
    events, truncated, reason = P.read_stream(prop) if prop.exists() else ([], True, "missing")
    fid, fault = None, {}
    for k, v in sorted(chain.get("faults", {}).items()):
        if v.get("admitted"):
            fid, fault = k, v
            break
    by_id = {str(e.get("event_id")): e for e in events}

    def _fault_detail(k, v):
        path = [by_id[i] for i in v.get("path_event_ids", []) if i in by_id]
        edges = [{"from": a.get("event_id"), "to": b.get("event_id"),
                  "ok": str(b.get("parent_event_id")) == str(a.get("event_id"))}
                 for a, b in zip(path, path[1:])]
        ticks = []
        for e in path:
            try:
                ticks.append(int(str(e.get("tick"))))
            except ValueError:
                pass
        l5_id = v.get("l5_witness_event_id")
        l5 = by_id.get(str(l5_id), {})
        return {
            "fault_id": k,
            "terminal": v.get("terminal"),
            "admitted": v.get("admitted", False),
            "certified": v.get("certified", False),
            "violations": v.get("violations", []),
            "layers": v.get("layers", []),
            "layers_na": v.get("layers_na", []),
            "direct_parent_chain": all(e["ok"] for e in edges) if edges else False,
            "edges": edges,
            "tick_monotonic": all(b >= a for a, b in zip(ticks, ticks[1:])),
            "l5_witness": {"event_id": l5_id, "kind": l5.get("kind"),
                           "outcome": l5.get("outcome")},
            "containment_event_id": v.get("containment_event_id"),
            "containment_layer": v.get("containment_layer"),
        }

    fault_audits = [_fault_detail(k, v)
                    for k, v in sorted(chain.get("faults", {}).items())]
    primary = _fault_detail(fid, fault) if fid is not None else {}
    edges = primary.get("edges", [])
    tick_ok = primary.get("tick_monotonic", False)
    l5_id = primary.get("l5_witness", {}).get("event_id")
    l5 = primary.get("l5_witness", {})
    cross_ok = all(str(e.get("sample_run_id")) == manifest.get("sample_run_id")
                   for e in events)
    hp = attempt / "evidence_sha256.json"
    hashes = json.loads(hp.read_text(encoding="utf-8")) if hp.exists() else {}
    stats = attempt / "stats.txt"
    profile = str(manifest.get("config_profile", "") or "")
    md_path = attempt / f"{manifest.get('run_id')}-seed{manifest.get('seed')}.md"
    md = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    audit = {
        "run_id": manifest.get("run_id"),
        "seed": manifest.get("seed"),
        "sample_run_id": manifest.get("sample_run_id"),
        "attempt": attempt.name,
        "gzip_eof_ok": not truncated,
        "truncation_reason": reason,
        "event_count": len(events),
        "identity_ok": not chain.get("identity_violations"),
        "identity_violations": chain.get("identity_violations", []),
        "direct_parent_chain": all(e["ok"] for e in edges) if edges else False,
        "edges": edges,
        "tick_monotonic": tick_ok,
        "layers": primary.get("layers", []),
        "layers_na": primary.get("layers_na", []),
        "l5_witness": {"event_id": l5_id, "kind": l5.get("kind"),
                       "outcome": l5.get("outcome")},
        "oracle": oracle.get("category"),
        "oracle_reason": oracle.get("reason"),
        "run_level_oracle": report.get("run_level_oracle"),
        "chain_terminal": primary.get("terminal"),
        "fault_count": len(fault_audits),
        "fault_terminals": {x["fault_id"]: x["terminal"]
                            for x in fault_audits},
        "all_faults_admitted": bool(fault_audits)
        and all(x["admitted"] for x in fault_audits),
        "all_faults_certified": bool(fault_audits)
        and all(x["certified"] for x in fault_audits),
        "fault_audit": fault_audits,
        "stats_nonempty": stats.exists() and stats.stat().st_size > 0,
        "evidence_sha256": hashes,
        "cross_seed_ok": cross_ok,
        "decoded_roots": sum(
            1 for e in events
            if str(e.get("kind")) in ROOT_KINDS
            and str(e.get("decoded_kind", "")).strip()),
        "legacy_roots": sum(
            1 for e in events
            if str(e.get("kind")) in ROOT_KINDS
            and not str(e.get("decoded_kind", "")).strip()),
        "decode_guard": bool(((manifest.get("injector") or {}).get("fpu_mode")
                              or {}).get("decode_guard")),
        "config_profile": profile,
        "legacy_md_format": not ("### 逐 fault 终局" in md),
        "admitted": primary.get("admitted", False),
        "certified": bool(res["ok"]) and bool(fault_audits)
        and all(x["certified"] for x in fault_audits),
        "violations": primary.get("violations", []),
        "audit_checks": [{"check": n, "ok": ok} for n, ok in res["checks"]],
        "failures": res["failures"],
        "ok": res["ok"],
    }
    (attempt / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# {audit['run_id']} seed{audit['seed']} 审计", "",
             f"- attempt：`{audit['attempt']}`",
             f"- sample_run_id：`{audit['sample_run_id']}`", "",
             "| 项 | 值 |", "|---|---|",
             f"| gzip EOF 完整 | {audit['gzip_eof_ok']}（{audit['truncation_reason'] or 'ok'}） |",
             f"| event_count | {audit['event_count']} |",
             f"| 身份一致 | {audit['identity_ok']} |",
             f"| 单祖先直接 parent | {audit['direct_parent_chain']} |",
             f"| tick 单调 | {audit['tick_monotonic']} |",
             f"| 层映射 | {', '.join(audit['layers'])}；N/A={audit['layers_na']} |",
             f"| L5 witness | {audit['l5_witness']} |",
             f"| oracle | {audit['oracle']} |",
             f"| chain terminal | {audit['chain_terminal']} |",
             f"| stats 非空 | {audit['stats_nonempty']} |",
             f"| 无跨 seed 复制 | {audit['cross_seed_ok']} |",
             f"| decode_guard | {audit['decode_guard']} |",
             f"| decoded / legacy roots | {audit['decoded_roots']} / {audit['legacy_roots']} |",
             f"| admitted（主 fault） | {audit['admitted']} |",
             f"| certified（全 fault 门禁） | {audit['certified']} |",
             f"| fault 数 | {audit['fault_count']} |",
             f"| 所有 fault admitted | {audit['all_faults_admitted']} |",
             f"| 所有 fault certified | {audit['all_faults_certified']} |",
             f"| violations（主 fault） | {audit['violations']} |", "",
             "## 逐 fault 审计", "",
             "| fault | terminal | admitted | certified | direct parent | tick 单调 | layers | violations |",
             "|---|---|---|---|---|---|---|---|"]
    for x in audit["fault_audit"]:
        lines.append(f"| {x['fault_id']} | {x['terminal']} | {x['admitted']} | "
                     f"{x['certified']} | {x['direct_parent_chain']} | "
                     f"{x['tick_monotonic']} | {', '.join(x['layers'])} | "
                     f"{x['violations']} |")
    lines += ["", "## 边（主 fault）", ""]
    for e in audit["edges"]:
        lines.append(f"- `{e['from']}` → `{e['to']}`：{'✓' if e['ok'] else '✗'}")
    lines += ["", "## 证据 SHA-256", "", "| 文件 | SHA-256 |", "|---|---|"]
    for rel, h in sorted(hashes.items()):
        lines.append(f"| `{rel}` | `{h}` |")
    lines += ["", "## 审计检查", "", "| 检查 | 结果 |", "|---|---|"]
    for c in audit["audit_checks"]:
        lines.append(f"| {c['check']} | {'PASS' if c['ok'] else 'FAIL'} |")
    lines += ["", f"**结论：{'PASS' if audit['ok'] else 'FAIL'}**", ""]
    (attempt / "audit.md").write_text("\n".join(lines), encoding="utf-8")
    return audit


def _suite_components(suite_manifest):
    components = suite_manifest.get("components")
    if not isinstance(components, list) or len(components) != 5:
        raise ValueError("suite_manifest.components must contain 5 entries")
    return components


def audit_suite(seed_dir: Path):
    """Audit a W5 suite seed directory.

    Unlike a single-seed audit, a suite seed is `ok` only when all 5
    component attempts are present, in fixed order, independently audited
    (`audit.json.ok` and `certified`) and their component manifests still
    match the on-disk attempt manifests. Legacy single-seed auditing is
    untouched (`audit_attempt`).
    """
    import fsu_suite as S
    seed_dir = Path(seed_dir)
    checks, failures = [], []

    def check(name, ok, detail=None):
        checks.append((name, ok))
        if not ok:
            failures.append(name if detail is None else f"{name}: {detail}")

    sm_path = seed_dir / "suite_manifest.json"
    check("suite_manifest.json 存在", sm_path.exists())
    if not sm_path.exists():
        return {"ok": False, "checks": checks, "failures": failures,
                "suite_seed_dir": str(seed_dir)}
    try:
        sm = json.loads(sm_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        check("suite_manifest.json 可解析", False, str(e))
        return {"ok": False, "checks": checks, "failures": failures,
                "suite_seed_dir": str(seed_dir)}

    suite = sm.get("suite")
    suite_hash = ""
    try:
        v = S.validate_suite_manifest(suite, require_hashes=True,
                                      require_suite_hash=True)
        suite_hash = v["suite_hash"]
        check("suite 身份与 suite_hash", True)
    except S.SuiteError as e:
        check("suite 身份与 suite_hash", False, str(e))
    if suite_hash and str(sm.get("suite_hash")) != suite_hash:
        check("suite_manifest.suite_hash 与重算一致", False,
              f"{sm.get('suite_hash')} != {suite_hash}")
    else:
        check("suite_manifest.suite_hash 与重算一致", bool(suite_hash))

    try:
        components = _suite_components(sm)
    except ValueError as e:
        check("5 个 component 齐全", False, str(e))
        return {"ok": False, "checks": checks, "failures": failures,
                "suite_seed_dir": str(seed_dir)}
    try:
        S.validate_component_manifests(components, suite)
        check("component manifest 结构/顺序/哈希", True)
    except S.SuiteError as e:
        check("component manifest 结构/顺序/哈希", False, str(e))

    total_eligible = 0
    total_activated = 0
    total_faults = 0
    for comp in components:
        pid = comp.get("program_id")
        attempt = Path(comp.get("attempt", ""))
        if not attempt.is_absolute():
            attempt = seed_dir / attempt
        cm_path = attempt / "component_manifest.json"
        check(f"{pid} attempt 存在", attempt.is_dir())
        check(f"{pid} component_manifest.json 存在", cm_path.exists())
        if not cm_path.exists():
            continue
        try:
            cm = json.loads(cm_path.read_text(encoding="utf-8"))
            S.validate_component_manifest(cm, suite)
            check(f"{pid} component manifest 校验", True)
        except (OSError, json.JSONDecodeError, S.SuiteError) as e:
            check(f"{pid} component manifest 校验", False, str(e))
            continue
        man = attempt / "manifest.json"
        if man.exists():
            check(f"{pid} component_manifest_sha256 与 attempt manifest 一致",
                  _sha(man) == cm.get("component_manifest_sha256"))
        else:
            check(f"{pid} attempt manifest.json 存在", False)
        a = audit_attempt(attempt)
        check(f"{pid} 独立 audit.ok", a["ok"],
              "; ".join(a["failures"][:3]) if a["failures"] else None)
        a_path = attempt / "audit.json"
        aud = {}
        if a_path.exists():
            try:
                aud = json.loads(a_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                aud = {}
        check(f"{pid} audit.certified", aud.get("certified") is True)
        check(f"{pid} component_status=admitted",
              cm.get("component_status") == "admitted")
        # Element oracle: result + raw array must be real and SHA-covered.
        oracle_path = attempt / "oracle_elements.json"
        array_path = attempt / "inject/array.bin"
        check(f"{pid} oracle_elements.json 存在", oracle_path.exists())
        check(f"{pid} inject/array.bin 存在", array_path.exists())
        oracle_covered = False
        hp = attempt / "evidence_sha256.json"
        if oracle_path.exists() and array_path.exists() and hp.exists():
            try:
                hashes = json.loads(hp.read_text(encoding="utf-8"))
                oracle_covered = (
                    hashes.get("oracle_elements.json") == _sha(oracle_path)
                    and hashes.get("inject/array.bin") == _sha(array_path))
            except (OSError, json.JSONDecodeError):
                oracle_covered = False
        check(f"{pid} oracle/array 已被证据 SHA 覆盖", oracle_covered)
        check(f"{pid} component_oracle 为 SDC/MASKED",
              cm.get("component_oracle") in ("SDC", "MASKED"))
        total_eligible += int(cm.get("component_eligible", 0))
        total_activated += int(cm.get("component_activated", 0))
        total_faults += int(cm.get("component_faults", 0))

    report_path = seed_dir / "suite_report.json"
    check("suite_report.json 存在", report_path.exists())
    if report_path.exists():
        try:
            rep = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            rep = {}
        check("suite_report 声明 5 个 component run",
              int(rep.get("component_run_count", -1)) == 5)
        check("suite_report 未把 component 数当 seed 数",
              int(rep.get("formal_suite_seed_count", -1)) == 1)
        check("suite_report suite_hash 一致",
              str(rep.get("suite_hash")) == suite_hash)
        check("suite_report eligible/activated 汇总一致",
              int(rep.get("component_eligible_total", total_eligible))
              == total_eligible
              and int(rep.get("component_activated_total", total_activated))
              == total_activated)

    return {"ok": not failures, "checks": checks, "failures": failures,
            "suite_seed_dir": str(seed_dir), "suite_id": sm.get("suite_id"),
            "suite_hash": suite_hash, "suite_seed": sm.get("suite_seed"),
            "component_run_count": len(components),
            "component_eligible_total": total_eligible,
            "component_activated_total": total_activated,
            "component_fault_total": total_faults}


def write_suite_audit(seed_dir: Path):
    """Persist suite-level audit.json / audit.md from real component evidence."""
    seed_dir = Path(seed_dir)
    res = audit_suite(seed_dir)
    sm_path = seed_dir / "suite_manifest.json"
    sm = json.loads(sm_path.read_text(encoding="utf-8")) if sm_path.exists() else {}
    audit = {
        "suite_id": sm.get("suite_id"),
        "suite_version": sm.get("suite_version"),
        "suite_hash": sm.get("suite_hash"),
        "suite_seed": sm.get("suite_seed"),
        "run_id": sm.get("run_id"),
        "component_run_count": res.get("component_run_count", 0),
        "component_eligible_total": res.get("component_eligible_total", 0),
        "component_activated_total": res.get("component_activated_total", 0),
        "component_fault_total": res.get("component_fault_total", 0),
        "formal_suite_seed_count": 1 if res["ok"] else 0,
        "checks": [{"check": n, "ok": ok} for n, ok in res["checks"]],
        "failures": res["failures"],
        "ok": res["ok"],
    }
    (seed_dir / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# {audit.get('suite_id')} suite seed{audit.get('suite_seed')} 审计",
             "",
             f"- suite_hash：`{audit.get('suite_hash')}`",
             f"- component run：**{audit['component_run_count']}**"
             "（不等于 seed 数；本 suite seed 正式计数为 1）",
             f"- component eligible 合计：{audit['component_eligible_total']}",
             f"- component activated 合计：{audit['component_activated_total']}",
             "", "| 检查 | 结果 |", "|---|---|"]
    for c in audit["checks"]:
        lines.append(f"| {c['check']} | {'PASS' if c['ok'] else 'FAIL'} |")
    lines += ["", f"**结论：{'PASS' if audit['ok'] else 'FAIL'}**", ""]
    (seed_dir / "audit.md").write_text("\n".join(lines), encoding="utf-8")
    return audit


def _is_suite_dir(path: Path):
    p = Path(path)
    return p.is_dir() and (p / "suite_manifest.json").exists()


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="FSU seed/suite 审计器")
    ap.add_argument("attempt", help="single attempt dir or suite seed dir")
    a = ap.parse_args(argv)
    path = Path(a.attempt)
    if _is_suite_dir(path):
        res = audit_suite(path)
        for name, ok in res["checks"]:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        print(json.dumps({"ok": res["ok"], "failures": res["failures"],
                          "suite_seed_dir": str(path)},
                         ensure_ascii=False, indent=2))
        return 0 if res["ok"] else 1
    res = audit_attempt(path)
    for name, ok in res["checks"]:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(json.dumps({"ok": res["ok"], "failures": res["failures"]},
                     ensure_ascii=False, indent=2))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
