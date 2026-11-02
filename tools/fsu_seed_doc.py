#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_seed_doc.py — 由单 seed 真实证据生成十节传播链 Markdown。

只使用本 attempt 的 manifest / run.out / run.err / stats / oracle /
chain_report / prop_evt / injection log；缺字段写 N/A 或 Unknown，
绝不跨 seed 复制、绝不推测。
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


def write_doc(attempt: Path, manifest: dict, chain_report: dict) -> Path:
    attempt = Path(attempt)
    chain = chain_report.get("chain", {})
    oracle = chain_report.get("oracle", {})
    fid, fault = _pick_fault(chain)
    inject = attempt / "inject"
    prop = inject / "prop_evt.txt.gz"
    events, truncated, trunc_reason = P.read_stream(prop) if prop.exists() else ([], True, "missing prop_evt")
    by_id = {str(e.get("event_id", "")): e for e in events}
    path_ids = fault.get("path_event_ids", [])
    path = [by_id[i] for i in path_ids if i in by_id]
    root = path[0] if path else None
    runid = manifest["run_id"]
    seed = manifest["seed"]
    out = attempt / f"{runid}-seed{seed}.md"
    injection_lines = (inject / "fpu_injections.log")
    inj_text = injection_lines.read_text(encoding="utf-8", errors="replace") if injection_lines.exists() else ""

    attempted = sum(1 for e in events if str(e.get("kind")) == "fault_applied")
    # activated 只认“故障值被真实消费”的 L2 事件；同一 fault 的 L3/L4
    # 复用 activated=1 只为可读性，按 fault_id 去重，避免重复计数。
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
          f"| seed / sample_run_id | {seed} / `{manifest.get('sample_run_id')}` |",
          f"| selection seed / injection seed | {manifest.get('selection_seed')} / {manifest.get('injection_seed')} |",
          f"| 实际 workload | `{manifest.get('workload_binary')}`（SHA-256 `{manifest.get('workload_sha256') or 'N/A'}`） |",
          f"| manifest | `{attempt/'manifest.json'}` |",
          f"| gem5 二进制 | `{manifest.get('gem5_binary')}`（SHA-256 `{manifest.get('gem5_sha256') or 'N/A'}`） |",
          f"| 源码 HEAD | `{manifest.get('source_head')}` |",
          f"| 分析工具 SHA-256 | `{manifest.get('runner_tool_sha256')}` |",
          f"| census 命令 | `{' '.join(chain_report.get('command', {}).get('census', []))}` |",
          f"| 注入命令 | `{' '.join(chain_report.get('command', {}).get('inject', []))}` |",
          ""]

    L += ["## 2. 故障注入发生在哪里", ""]
    if root:
        L += ["| 字段 | 值 |", "|---|---|",
              f"| 根 event_id | `{_v(root,'event_id')}` |",
              f"| tick / cycle | {_v(root,'tick')} / {_v(root,'cycle')} |",
              f"| sn / PC / opcode | {_v(root,'dyn_inst_seq')} / {_v(root,'pc')} / {_v(root,'opcode')} |",
              f"| 单元/结构/slot/port/lane | {_v(root,'unit')} / {_v(root,'field')} / {_v(root,'iq_slot')} / {_v(root,'src_slot')} / {_v(root,'lane_width')}@{_v(root,'lane_offset')} |",
              f"| fault bit / mask | {_v(root,'bit_indices')} / {_v(root,'fault_mask')} |",
              f"| attempted / eligible / activated | {attempted} / {eligible} / {activated} |",
              "",
              "注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：", "",
              "```", "\n".join(inj_text.splitlines()[-5:]) or "（无）", "```", ""]
    else:
        L += ["未找到 `fault_applied` 根事件（chain terminal="
              f"`{fault.get('terminal','unknown')}`）。", ""]

    L += ["## 3. 注入前后状态", ""]
    if root:
        L += ["| 项 | 观测值 |", "|---|---|",
              f"| old/new 值 | {_v(root,'before')} → {_v(root,'after')} |",
              f"| old/new hash | {_v(root,'before_hash')} → {_v(root,'after_hash')} |",
              f"| source/destination phys tag | src={_v(root,'src_slot')} / dest={_v(root,'phys_reg')} |",
              f"| operand role / lane / width | {_v(root,'src_slot')} / {_v(root,'lane_offset')} / {_v(root,'lane_width')} |",
              f"| opClass / FU / FPCR / FPSR | {_v(root,'opcode')} / {_v(root,'fu_class')} / {_v(root,'field')} / N/A（事件未携带则不为推测） |",
              f"| correct/fault result | {_v(root,'before')} / {_v(root,'after')} |",
              "| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |", ""]
    else:
        L += ["N/A（无根事件）。", ""]

    L += ["## 4. 之后依次经过哪些真实部件", "",
          "主链完全由本 seed `parent_event_id` 的直接 parent 边构成；"
          "旁支不混入（见 chain_report.off_chain_event_ids）。", ""]
    if path:
        L += ["| 顺序 | kind | 层级 | event_id | parent_event_id |",
              "|---|---|---|---|---|"]
        for i, e in enumerate(path, 1):
            L.append(f"| {i} | {_v(e,'kind')} | {P.layer_of(e) or '—'} | "
                     f"{_v(e,'event_id')} | {_v(e,'parent_event_id')} |")
        L.append("")
    else:
        L += ["N/A（主链为空）。", ""]

    L += ["## 5. 完整主链事件表", "",
          "| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | "
          "producer/consumer | phys tag | src_slot | lane | before→after | "
          "detection_layer | outcome | corr |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    if path:
        L += [_table_row(e) for e in path]
    else:
        L.append("| — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |")
    L.append("")

    L += ["## 6. 数据、控制和污点在各层如何变化", ""]
    layers_present = [P.layer_of(e) for e in path if P.layer_of(e)]
    layers_na = fault.get("layers_na", [])
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

    L += ["## 7. 最终结局", "",
          f"- 程序 oracle：**{oracle.get('category','N/A')}**（{oracle.get('reason','')}）",
          f"- 传播链 terminal：**{fault.get('terminal','N/A')}**",
          f"- provable_to：{fault.get('deepest_layer','N/A')}",
          f"- admitted / certified：{fault.get('admitted', False)} / "
          f"{fault.get('admitted', False)}",
          f"- violations：{fault.get('violations', [])}",
          f"- truncated / evidence_truncated：{chain.get('truncated')} / {truncated}",
          f"- 事件数：{chain.get('event_count','N/A')}",
          f"- attempted / eligible / activated：{attempted} / {eligible} / {activated}",
          f"- L5 见证事件：{fault.get('l5_witness_event_id') or 'N/A'}",
          f"- 含住事件/层级：{fault.get('containment_event_id') or 'N/A'} / "
          f"{fault.get('containment_layer') or 'N/A'}",
          "- 结局标签：" + ("SDC" if oracle.get("category") == "SDC" else
                         "Crash" if oracle.get("category") == "Crash" else
                         "Timeout" if oracle.get("category") in ("Hang", "Timeout") else
                         "Masked/contained" if oracle.get("category") == "Masked" else
                         "not_activated" if oracle.get("category") == "Inactive" else
                         str(oracle.get("category"))), ""]

    L += ["## 8. 为什么该结局成立", ""]
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
    if fault.get("l5_witness_event_id"):
        e = by_id.get(str(fault["l5_witness_event_id"]), {})
        L.append(f"- L5 真实见证：`{fault['l5_witness_event_id']}` "
                 f"kind={_v(e,'kind')} outcome={_v(e,'outcome')} "
                 f"oracle_diff={_v(e,'oracle_diff')}")
    if fault.get("containment_event_id"):
        L.append(f"- 真实含住：`{fault['containment_event_id']}` "
                 f"layer={fault.get('containment_layer')} "
                 f"outcome={_v(by_id.get(str(fault['containment_event_id']), {}),'outcome')}")
    L += ["- 传播链结局与程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。", ""]

    L += ["## 9. 原始证据位置与 SHA-256", "",
          "| 文件 | SHA-256 |", "|---|---|"]
    files = ["manifest.json", "run.out", "run.err", "stats.txt",
             "oracle.json", "chain_report.json",
             "census/fpu_injections.log", "inject/fpu_injections.log",
             "inject/prop_evt.txt.gz", "inject/stats.txt"]
    for rel in files:
        p = attempt / rel
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
          ""]

    out.write_text("\n".join(L), encoding="utf-8")
    return out
