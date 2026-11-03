#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_prop_fields.py — FSU 传播事件流（FSU_PROP-EVT v1）字段注册表与解析器。

设计目标（阶段 C 合同，先于 C++ 发射端落地）:
  - 与 LSU `PROP-EVT` 同族：空格分隔 `key=value`，缺值留空但键不省略；
  - 增加 FSU 专用字段：IQ slot / src_slot / producer-consumer seq /
    phys tag+generation / lane / FU / operand hash / burst / eligible ordinal；
  - 行格式：
      FSU_PROP-EVT: kind=<v> run_id=<v> ... terminal=<v>
  - 解析端对缺失键填 ""，对 gzip 截断置 truncated=True（不静默）；
  - `chain_end` 是生命周期收口，不是 L5（层映射为 None）。

[FSU][F5] 永久故障（一个安装、多次 exposure）:
  - `fault_installed` 是唯一 L0 根；`exposure` 是同一 fault_id 的旁支证据，
    层映射为 None，绝不作为独立 fault 计数；
  - `activation`/`first_impact` 如被显式发射，分别按真实观测层 L2/L5 映射；
  - `install_event`/`fixed_mask`/`stuck_polarity`/`exposures_*` 等字段使
    “一个永久 fault 的完整链”可离线审计，而不依赖每事件新建 fault_id。
"""
from __future__ import annotations

import gzip
import zlib
from pathlib import Path

PREFIX = "FSU_PROP-EVT:"
# 发射端复用 CHAOSPropagation 的统一流（PROP-EVT:）；独立文件可用 FSU 前缀。
PREFIXES = ("FSU_PROP-EVT:", "PROP-EVT:")
EVENT_CAP = 200000

# 字段顺序即发射端写入顺序；解析端容忍缺键。
PROP_EVT_FIELDS = [
    "kind", "run_id", "sample_run_id", "fault_id", "event_id",
    "parent_event_id", "tick", "cycle", "core_id", "thread_id",
    "model_id", "submodel", "unit", "freq", "load_id",
    "dyn_inst_seq", "commit_seq", "pc", "opcode",
    "iq_slot", "src_slot", "producer_seq", "consumer_seq",
    "arch_reg", "phys_reg", "reg_generation",
    "lane_width", "lane_offset", "lane_mask",
    "precision", "field_lo", "field_hi", "full_before", "full_after",
    "reg_class", "bit_in_lane",
    "instruction_bits", "decoded_kind", "decoded_precision",
    "decoded_reg_class", "decoded_element_width", "decoded_lanes",
    "decoded_reliable", "manifest_precision", "manifest_lane_width",
    "manifest_lane_offset", "precision_match", "lane_match",
    "decode_reason",
    "fu_class", "fu_index", "field", "bit_indices", "fault_mask",
    "before", "after", "before_hash", "after_hash", "value_hash",
    "eligible_ordinal", "eligible_total", "attempted", "activated",
    "rate_divisor", "jitter_pct", "interval", "ordinal_index",
    "ordinal_generator", "ordinal_generator_version", "ordinal_seed",
    "burst_id", "burst_ordinal", "burst_length",
    "detection_layer", "contained", "outcome", "oracle_diff",
    "evidence_status", "corr", "golden_id", "config_hash", "binary_hash",
    "terminal",
    # [FSU][F5] One permanent fault, many exposures. These fields keep the
    # single installation and the exposure accounting explicit; an exposure
    # event never mints a new fault_id.
    "install_event", "stuck_polarity", "fixed_mask", "first_eligible_sn",
    "exposure_id", "exposure_count", "activated_exposure_count",
    "first_activated_sn", "last_exposure_sn", "affected_sn",
    "correct_before", "stuck_after", "first_impact_latency",
    "sample_policy", "exposures_total", "exposures_sampled",
    "exposures_dropped",
]

# kind → 层级。None = 生命周期/终局标记，不占 L0–L5。
KIND_LAYER = {
    "fault_applied": "L0",
    # [FSU][F5] The one permanent-fault installation is the L0 root. Every
    # later eligible event is an `exposure` branch event (no layer): it is
    # evidence of the same fault, never an independent fault.
    "fault_installed": "L0",
    "exposure": None,
    "carrier_state": "L1",
    # L2：IQ 选择/ready/操作数读取
    "iq_select": "L2", "ready_update": "L2", "operand_read": "L2",
    "producer_consumer_edge": "L2",
    # L3：FSU 执行
    "execute": "L3", "fsu_result": "L3",
    # L4：写回/wakeup/下游消费
    "prf_writeback": "L4", "wakeup": "L4", "consumer": "L4",
    "downstream_read": "L4",
    # L5：架构提交/架构状态/软件 oracle
    "commit": "L5", "arch_state": "L5", "oracle_diff": "L5",
    "sdc_escape": "L5",
    # 显式检测/含住（层级取自 detection_layer）
    "detect": None, "contain": None, "squash": None, "replay": None,
    "overwrite": None, "mask": None, "crash": None, "timeout": None,
    # 生命周期收口与未激活
    "chain_end": None, "not_activated": None,
    # [FSU][F5] Explicit activation / first-impact markers, mapped to their
    # REAL observation layers (a value change is an L2 operand/execute
    # observation; the first architectural impact is L5). The current
    # CHAOSFPU emitter records activation/impact on the exposure/commit
    # events themselves; these kinds are registered so an emitter that
    # chooses explicit markers cannot drift from the checker.
    "activation": "L2", "first_impact": "L5",
}

CONTAIN_KINDS = frozenset({
    "detect", "contain", "squash", "replay", "overwrite", "mask",
    "crash", "timeout",
})
L5_WITNESS_KINDS = frozenset({"commit", "arch_state", "oracle_diff",
                              "sdc_escape", "first_impact"})
LIFECYCLE_KINDS = frozenset({"chain_end"})
# [FSU][F5] Root kinds: an F0-F4 chain starts at fault_applied, an F5
# permanent chain starts at the single fault_installed event.
ROOT_KINDS = frozenset({"fault_applied", "fault_installed"})
# Exposure events are side-branch evidence of the SAME fault. They must
# never be grouped/counted as independent faults.
BRANCH_KINDS = frozenset({"exposure"})
F5_FIELDS = frozenset({
    "install_event", "stuck_polarity", "fixed_mask", "first_eligible_sn",
    "exposure_id", "exposure_count", "activated_exposure_count",
    "first_activated_sn", "last_exposure_sn", "affected_sn",
    "correct_before", "stuck_after", "first_impact_latency",
    "sample_policy", "exposures_total", "exposures_sampled",
    "exposures_dropped",
})
F5_CHAIN_END_FIELDS = frozenset({
    "exposures_total", "activated_exposure_count", "exposures_sampled",
    "exposures_dropped", "sample_policy", "first_eligible_sn",
    "last_exposure_sn",
})

EMPTY_VALUES = ("", "None", "none", "Unknown", "unknown")
CONTAINED_TRUE = ("1", "true", "True", "yes", "Yes")
CLOSED_TERMINALS = frozenset({"full", "crash", "timeout", "sdc"})


def layer_of(evt: dict):
    """事件层级；detect/contain 等取 detection_layer，chain_end 返回 None。"""
    kind = str(evt.get("kind", "")).strip()
    if kind in LIFECYCLE_KINDS:
        return None
    if kind in CONTAIN_KINDS:
        dl = str(evt.get("detection_layer", "")).strip()
        return dl if dl in ("L0", "L1", "L2", "L3", "L4", "L5") else None
    return KIND_LAYER.get(kind)


def parse_line(line: str):
    """解析一条 FSU_PROP-EVT；非本流行返回 None。"""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    pfx = next((p for p in PREFIXES if line.startswith(p)), None)
    if pfx is None:
        return None
    body = line[len(pfx):].strip()
    evt = {}
    for tok in body.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            evt[k] = v
    for k in PROP_EVT_FIELDS:
        evt.setdefault(k, "")
    evt.setdefault("evidence_status", "observed")
    return evt


def read_stream(path):
    """读取 .gz/.txt；返回 (events, truncated, reason)。

    截断/损坏必须显式标记，绝不静默返回“完整”。
    """
    p = Path(path)
    opener = gzip.open if str(p).endswith(".gz") else open
    events, truncated, reason = [], False, ""
    try:
        with opener(p, "rt", encoding="utf-8", errors="replace") as f:
            for line in f:
                evt = parse_line(line)
                if evt is None:
                    continue
                if len(events) >= EVENT_CAP:
                    truncated = True
                    reason = f"event_cap_exceeded({EVENT_CAP})"
                    break
                events.append(evt)
    except (EOFError, gzip.BadGzipFile, OSError, zlib.error) as e:
        truncated = True
        reason = f"{type(e).__name__}:{e}"
    return events, truncated, reason
