#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_seed_doc.py — 由单 seed 真实证据生成十节传播链 Markdown。

只使用本 attempt 的 manifest / run.out / run.err / stats / oracle /
chain_report / prop_evt / injection log；缺字段写 N/A 或 Unknown，
绝不跨 seed 复制、绝不推测。

[D2] 多 fault：每个 fault 都有独立小节（注入位置、前后状态、主链、逐层、
终局、parent 边）；第 5 节事件表包含**所有** fault 的主链事件。run-level
oracle 与每个 fault 的 chain terminal 分开陈述。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fsu_prop_fields as P

LAYERS = ["L0", "L1", "L2", "L3", "L4", "L5"]


def _sha(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return "N/A"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _v(evt, key):
    val = str(evt.get(key, "")).strip() if evt else ""
    return val if val else "—"


def _pick_fault(chain):
    """Primary fault for backward-compatible singular lines: first admitted,
    else the first fault id."""
    faults = chain.get("faults", {})
    for fid, r in sorted(faults.items()):
        if r.get("admitted"):
            return fid, r
    if faults:
        fid = sorted(faults)[0]
        return fid, faults[fid]
    return None, {}


def _table_row(evt):
    return "| " + " | ".join([
        _v(evt, "kind"), _v(evt, "event_id"), _v(evt, "parent_event_id"),
        _v(evt, "tick"), _v(evt, "fault_id"), _v(evt, "dyn_inst_seq"),
        _v(evt, "pc"), _v(evt, "opcode"),
        f"{_v(evt, 'producer_seq')}/{_v(evt, 'consumer_seq')}",
        _v(evt, "phys_reg"), f"{_v(evt, 'src_slot')}",
        f"{_v(evt, 'lane_width')}@{_v(evt, 'lane_offset')}",
        f"{_v(evt, 'before')}→{_v(evt, 'after')}",
        _v(evt, "detection_layer"), _v(evt, "outcome"), _v(evt, "corr"),
    ]) + " |"


def _fault_root(path):
    return path[0] if path else None


def write_doc(attempt: Path, manifest: dict, chain_report: dict) -> Path:
    attempt = Path(attempt)
    chain = chain_report.get("chain", {})
    oracle = chain_report.get("oracle", {})
    rate = chain_report.get("rate") or {}
    faults = chain.get("faults", {})
    primary_fid, primary = _pick_fault(chain)
    inject = attempt / "inject"
    prop = inject / "prop_evt.txt.gz"
    events, truncated, trunc_reason = P.read_stream(prop) if prop.exists() else ([], True, "missing prop_evt")
    by_id = {str(e.get("event_id", "")): e for e in events}

    # Per-fault path event objects, in fault-id order.
    fault_paths = {}
    for fid, fr in sorted(faults.items()):
        fault_paths[fid] = [by_id[i] for i in fr.get("path_event_ids", [])
                            if i in by_id]

    runid = manifest["run_id"]
    seed = manifest["seed"]
    out = attempt / f"{runid}-seed{seed}.md"
    injection_lines = (inject / "fpu_injections.log")
    inj_text = injection_lines.read_text(encoding="utf-8", errors="replace") if injection_lines.exists() else ""

    attempted = sum(1 for e in events if str(e.get("kind")) == "fault_applied")
    # activated 只认“故障值被真实消费”的 L2 事件；按 fault_id 去重。
    activated = len({str(e.get("fault_id"))
                     for e in events
                     if str(e.get("kind")) == "operand_read"
                     and str(e.get("activated")).strip() == "1"})
    eligible = oracle.get("eligible_count", "—")

    L = []
    L += [f"# {runid} seed{seed} 完整传播链", "",
          "> 本文只使用本 seed（sample_run_id="
          f"`{manifest.get('sample_run_id')}`）的原始证据自动生成；"
          "未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。", "",
          "## 1. 实验身份与复现信息", "",
          "| 项 | 值 |", "|---|---|",
          f"| RunID | `{runid}` |",
          f"| 模型/子模型 | {manifest.get('model_id')} / {manifest.get('submodel')} |",
          f"| 单元/频率/负载 | {manifest.get('unit')} / {manifest.get('freq')} / {manifest.get('load_id')} |",
          f"| workload identity | {manifest.get('workload', {}).get('identity', 'N/A')} |",
          f"| seed / sample_run_id | {seed} / `{manifest.get('sample_run_id')}` |",
          f"| selection seed / injection seed | {manifest.get('selection_seed')} / {manifest.get('injection_seed')} |",
          f"| 实际 workload | `{manifest.get('workload_binary')}`（SHA-256 `{manifest.get('workload_sha256') or 'N/A'}`） |",
          f"| manifest | `{attempt/'manifest.json'}` |",
          f"| gem5 二进制 | `{manifest.get('gem5_binary')}`（SHA-256 `{manifest.get('gem5_sha256') or 'N/A'}`） |",
          f"| 源码 HEAD | `{manifest.get('source_head')}` |",
          f"| 分析工具 SHA-256 | `{manifest.get('runner_tool_sha256')}` |",
          f"| census 命令 | `{' '.join(chain_report.get('command', {}).get('census', []))}` |",
          f"| 注入命令 | `{' '.join(chain_report.get('command', {}).get('inject', []))}` |",
          f"| rate（divisor/jitter/warmup） | "
          f"{rate.get('rate_divisor', 'N/A')} / ±{rate.get('jitter_pct', 'N/A')}% / "
          f"{rate.get('warmup', 'N/A')} |",
          f"| eligible_total | {eligible} |",
          f"| ordinals（index: ordinal） | "
          + (", ".join(f"{i}:{o}" for i, o in enumerate(rate.get("ordinals", [])))
             if rate.get("ordinals") else "N/A") + " |",
          f"| ordinals SHA-256 | `{rate.get('ordinals_sha256', 'N/A')}` |",
          f"| 注入数（actual/expected） | "
          f"{chain_report.get('actual_injections', 'N/A')} / "
          f"{chain_report.get('expected_injections', 'N/A')} |",
          f"| fault 数（事件流/injection log） | "
          f"{len(faults)} / {chain_report.get('actual_injections', 'N/A')} |",
          ""]

    L += ["## 2. 故障注入发生在哪里", ""]
    if faults:
        for fid, fr in sorted(faults.items()):
            root = _fault_root(fault_paths.get(fid, []))
            L += [f"### fault {fid}", ""]
            if root:
                L += ["| 字段 | 值 |", "|---|---|",
                      f"| 根 event_id | `{_v(root,'event_id')}` |",
                      f"| tick / cycle | {_v(root,'tick')} / {_v(root,'cycle')} |",
                      f"| sn / PC / opcode | {_v(root,'dyn_inst_seq')} / {_v(root,'pc')} / {_v(root,'opcode')} |",
                      f"| 单元/结构/slot/port/lane | {_v(root,'unit')} / {_v(root,'field')} / {_v(root,'iq_slot')} / {_v(root,'src_slot')} / {_v(root,'lane_width')}@{_v(root,'lane_offset')} |",
                      f"| precision / reg_class | {_v(root,'precision')} / {_v(root,'reg_class')} |",
                      f"| field 范围（lane 内） | {_v(root,'field_lo')}..{_v(root,'field_hi')} |",
                      f"| fault bit（绝对）/ bit_in_lane | {_v(root,'bit_indices')} / {_v(root,'bit_in_lane')} |",
                      f"| fault mask（lane 内）/ lane_mask（128-bit 绝对） | {_v(root,'fault_mask')} / {_v(root,'lane_mask')} |",
                      f"| eligible ordinal / total | {_v(root,'eligible_ordinal')} / {_v(root,'eligible_total')} |",
                      f"| rate divisor / jitter / interval / ordinal_index | "
                      f"{_v(root,'rate_divisor')} / {_v(root,'jitter_pct')} / "
                      f"{_v(root,'interval')} / {_v(root,'ordinal_index')} |",
                      f"| terminal | {fr.get('terminal', 'N/A')} |", ""]
            else:
                L += [f"未找到 `fault_applied` 根事件（fault {fid} terminal="
                      f"`{fr.get('terminal','unknown')}`）。", ""]
        L += ["注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：", "",
              "```", "\n".join(inj_text.splitlines()[-5:]) or "（无）", "```", ""]
    else:
        L += ["未找到任何 `fault_applied` 根事件（chain terminal="
              f"`{primary.get('terminal','unknown')}`）。", ""]

    L += ["## 3. 注入前后状态", ""]
    if faults:
        for fid in sorted(faults):
            root = _fault_root(fault_paths.get(fid, []))
            L += [f"### fault {fid}", ""]
            if root:
                L += ["| 项 | 观测值 |", "|---|---|",
                      f"| old/new 值（lane 内） | {_v(root,'before')} → {_v(root,'after')} |",
                      f"| full 128-bit old/new | {_v(root,'full_before')} → {_v(root,'full_after')} |",
                      f"| old/new hash | {_v(root,'before_hash')} → {_v(root,'after_hash')} |",
                      f"| source/destination phys tag | src={_v(root,'src_slot')} / dest={_v(root,'phys_reg')} |",
                      f"| operand role / lane / width | {_v(root,'src_slot')} / {_v(root,'lane_offset')} / {_v(root,'lane_width')} |",
                      f"| opClass / FU / FPCR / FPSR | {_v(root,'opcode')} / {_v(root,'fu_class')} / {_v(root,'field')} / N/A（事件未携带则不为推测） |",
                      f"| correct/fault result | {_v(root,'before')} / {_v(root,'after')} |",
                      "| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |", ""]
            else:
                L += ["N/A（无根事件）。", ""]
    else:
        L += ["N/A（无根事件）。", ""]

    L += ["## 4. 之后依次经过哪些真实部件", "",
          "主链完全由本 seed `parent_event_id` 的直接 parent 边构成；"
          "旁支不混入（见 chain_report.off_chain_event_ids）。", ""]
    if faults:
        for fid in sorted(faults):
            path = fault_paths.get(fid, [])
            fr = faults[fid]
            L += [f"### fault {fid}（terminal={fr.get('terminal')}）", ""]
            if path:
                L += ["| 顺序 | kind | 层级 | event_id | parent_event_id |",
                      "|---|---|---|---|---|"]
                for i, e in enumerate(path, 1):
                    L.append(f"| {i} | {_v(e,'kind')} | {P.layer_of(e) or '—'} | "
                             f"{_v(e,'event_id')} | {_v(e,'parent_event_id')} |")
                L.append("")
            else:
                L += ["N/A（主链为空）。", ""]
    else:
        L += ["N/A（主链为空）。", ""]

    L += ["## 5. 完整主链事件表", "",
          "| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | "
          "producer/consumer | phys tag | src_slot | lane | before→after | "
          "detection_layer | outcome | corr |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    rows = []
    for fid in sorted(faults):
        rows += [_table_row(e) for e in fault_paths.get(fid, [])]
    if rows:
        L += rows
    else:
        L.append("| — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |")
    L.append("")

    L += ["## 6. 数据、控制和污点在各层如何变化", ""]
    if faults:
        for fid in sorted(faults):
            path, fr = fault_paths.get(fid, []), faults[fid]
            layers_na = fr.get("layers_na", [])
            L += [f"### fault {fid}", ""]
            for layer in LAYERS:
                evs = [e for e in path if P.layer_of(e) == layer]
                if evs:
                    desc = "；".join(f"{e.get('kind')}#{e.get('event_id')}" for e in evs)
                    L.append(f"- **{layer}**：{desc}（本 seed 真实事件）。")
                elif layer in layers_na:
                    L.append(f"- **{layer}**：N/A（本 seed 真实未到达；"
                             f"chain.layers_na 显式记录）。")
                else:
                    L.append(f"- **{layer}**：Unknown（本 seed 未观测到该层事件；"
                             "不推断为 Masked）。")
            L.append("")
    else:
        L += ["N/A（无 fault）。", ""]

    L += ["## 7. 最终结局", "",
          f"- run-level 程序 oracle：**{oracle.get('category','N/A')}**"
          f"（{oracle.get('reason','')}）",
          "- run-level oracle 与 chain terminal 分开记录，互不替代。",
          f"- run-level 注入数（actual/expected）："
          f"{chain_report.get('actual_injections','N/A')} / "
          f"{chain_report.get('expected_injections','N/A')}",
          f"- 全部 injected fault 出现在事件流："
          f"{chain_report.get('all_faults_present','N/A')}",
          f"- 传播链 terminal：**{primary.get('terminal','N/A')}**",
          f"- admitted / certified：{primary.get('admitted', False)} / "
          f"{primary.get('certified', False)}",
          f"- violations（主 fault）：{primary.get('violations', [])}",
          f"- truncated / evidence_truncated：{chain.get('truncated')} / {truncated}",
          f"- 事件数：{chain.get('event_count','N/A')}",
          f"- attempted / eligible / activated：{attempted} / {eligible} / {activated}",
          "",
          "### 逐 fault 终局", "",
          "| fault | terminal | deepest | admitted | certified | violations | L5 witness | containment |",
          "|---|---|---|---|---|---|---|---|"]
    if faults:
        for fid, fr in sorted(faults.items()):
            L.append(f"| {fid} | {fr.get('terminal','N/A')} | "
                     f"{fr.get('deepest_layer','N/A')} | {fr.get('admitted')} | "
                     f"{fr.get('certified')} | {fr.get('violations', [])} | "
                     f"{fr.get('l5_witness_event_id') or 'N/A'} | "
                     f"{fr.get('containment_event_id') or 'N/A'} / "
                     f"{fr.get('containment_layer') or 'N/A'} |")
    else:
        L.append("| — | — | — | — | — | — | — | — |")
    L += ["",
          "- 结局标签（run-level oracle）："
          + ("SDC" if oracle.get("category") == "SDC" else
             "Crash" if oracle.get("category") == "Crash" else
             "Timeout" if oracle.get("category") in ("Hang", "Timeout") else
             "Masked/contained" if oracle.get("category") == "Masked" else
             "not_activated" if oracle.get("category") == "Inactive" else
             str(oracle.get("category"))), ""]

    L += ["## 8. 为什么该结局成立", ""]
    if faults:
        for fid in sorted(faults):
            path, fr = fault_paths.get(fid, []), faults[fid]
            L += [f"### fault {fid}", ""]
            if path:
                L.append("主链每一条边均验证为直接 parent：")
                L.append("")
                for a, b in zip(path, path[1:]):
                    ok = str(b.get("parent_event_id")) == str(a.get("event_id"))
                    L.append(f"- `{_v(a,'event_id')}` ({_v(a,'kind')}) → "
                             f"`{_v(b,'event_id')}` ({_v(b,'kind')})；"
                             f"child.parent={_v(b,'parent_event_id')} "
                             f"{'✓' if ok else '✗'}")
                L.append("")
            if fr.get("l5_witness_event_id"):
                e = by_id.get(str(fr["l5_witness_event_id"]), {})
                L.append(f"- L5 真实见证：`{fr['l5_witness_event_id']}` "
                         f"kind={_v(e,'kind')} outcome={_v(e,'outcome')} "
                         f"oracle_diff={_v(e,'oracle_diff')}")
            if fr.get("containment_event_id"):
                L.append(f"- 真实含住：`{fr['containment_event_id']}` "
                         f"layer={fr.get('containment_layer')} "
                         f"outcome={_v(by_id.get(str(fr['containment_event_id']), {}),'outcome')}")
            L.append("")
    L += ["- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；"
          "若二者存在张力，本文并列保留，不强行调和。",
          "- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求"
          "所有 injected fault 的链均 closed 且无违规。", ""]

    L += ["## 9. 原始证据位置与 SHA-256", "",
          "| 文件 | SHA-256 |", "|---|---|"]
    files = ["manifest.json", "run.out", "run.err", "stats.txt",
             "oracle.json", "chain_report.json", "ordinals.json",
             "not_activated.json",
             "census/fpu_injections.log", "inject/fpu_injections.log",
             "inject/prop_evt.txt.gz", "inject/stats.txt"]
    for rel in files:
        p = attempt / rel
        if p.exists():
            L.append(f"| `{rel}` | `{_sha(p)}` |")
    L += [f"| gem5 二进制 `{manifest.get('gem5_binary')}` | "
          f"`{manifest.get('gem5_sha256') or 'N/A'}` |",
          f"| workload `{manifest.get('workload_binary')}` | "
          f"`{manifest.get('workload_sha256') or 'N/A'}` |", ""]

    L += ["## 10. 诚实边界", "",
          "- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。",
          "- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。",
          "- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。",
          "- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实"
          "commit/arch_state/oracle_diff 见证。",
          f"- 本 seed 含 {len(faults)} 个 fault；每个 fault 的 root/主链/终局独立，"
          "run-level oracle 单独记录。", ""]

    out.write_text("\n".join(L), encoding="utf-8")
    return out
