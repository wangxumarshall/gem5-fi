#!/usr/bin/env python3
"""[MDSPEC][B2] 126 BLOCKED 逐项裁决与互斥分类（用户第 5 点）。

用户要求：126 个 BLOCKED 必须逐项解决，或列出**需要批准的延期清单**；
阻塞原因按**互斥类别**统计。

互斥分类（按优先级取第一个命中，每个 RunID 恰属一类）：

  RULING        模型级裁决封锁（A06 load 侧 + byte-enable 待 spike）
  LICENSE       SPEC CPU2017 需授权（W11）
  FS-MULTICORE  需多核 FS 基础设施（litmus / PARSEC）
  FS-INFRA      需 FS 基础设施（TLB 翻译负载）
  MODE-UNIMPL   规格表 10 明写"先实现：…"——该子模型模式未实现
  HOOK-UNIMPL   规格表 9 实现状态=需新增，但无模式缺口标注（钩子待补）
  OK            无上述阻塞

输出 blocked_triage.md：分类统计 + 逐 RunID 明细 + 需用户批准的延期清单。
用法：python3 tools/lsu_blocked_triage.py --map <runid_map.json> --out <md>
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

# 优先级序（先匹配者胜）——类别名保持稳定，下游脚本按名引用。
CLASS_ORDER = ["RULING", "LICENSE", "FS-MULTICORE", "FS-INFRA",
               "WORKLOAD-GAP", "MODE-UNIMPL", "HOOK-UNIMPL", "UNRESOLVED",
               "PLATFORM-DEFECT", "CHAIN-UNPROVEN", "CHAIN-EVIDENCE-MISSING",
               "UNCLASSIFIED", "OK"]

# [R5-U4] 单一分类来源。本工具曾自带一套正则（`先实现：`/`spec:需新增` 等旧
# 词表），在 runid_map 措辞演进后整体失配，产出 `MODE-UNIMPL=23`、且**没有**
# UNRESOLVED 桶，与权威契约（`lsu_ready_contract._classify`）的 84 项分类
# 相互矛盾（同一台账三处总数 126/100/106）。按 CLAUDE.md「One classifier,
# no drift」，改为**从契约产物读取已判定的 category**，不再自行重判。
CONTRACT_CATS = {"RULING", "LICENSE", "FS-MULTICORE", "FS-INFRA",
                 "WORKLOAD-GAP", "MODE-UNIMPL", "UNRESOLVED", "PLATFORM-DEFECT",
                 # [R6-GATE] 链准入门禁新增的两类阻塞（契约 _classify 产出）
                 "CHAIN-UNPROVEN", "CHAIN-EVIDENCE-MISSING",
                 "UNCLASSIFIED"}


def classify_from_contract(entry):
    """契约行 → (class, 理由原文)。契约已在 build_contract 中判定 category。"""
    cat = entry.get("category") or "UNCLASSIFIED"
    why = entry.get("why") or entry.get("resolve_reason") or ""
    return (cat if cat in CONTRACT_CATS else "UNCLASSIFIED"), why

_RULING = re.compile(r"campaign:BLOCKED|A06")
_LICENSE = re.compile(r"spec-license|SPEC CPU2017")
_FS_MC = re.compile(r"multicore")
_FS_INFRA = re.compile(r"fs-infra")
_MODE_UNIMPL = re.compile(r"先实现：|mode unimplemented")
# 事件源/钩子缺口（非模式语义缺失）：只有事件源、无干净钩子、RMW 数据面
# 钩子缺失、无 busy/occupancy 注入点等。
_HOOK_UNIMPL = re.compile(r"spec:需新增|consumer-side|no clean hook|RMW|"
                          r"deferred$|无 SE 载体映射|NOT-MAPPED")


def classify(entry):
    """→ (class, 理由原文)。互斥：按 CLASS_ORDER 取首个命中。"""
    reasons = " ; ".join(entry.get("status_reasons", []))
    specs = entry.get("impl_status", "") or ""
    hook_txt = entry.get("missing_hooks", "") or ""
    if _RULING.search(reasons):
        return "RULING", reasons
    if _LICENSE.search(reasons):
        return "LICENSE", reasons
    if _FS_MC.search(reasons):
        return "FS-MULTICORE", reasons
    if _FS_INFRA.search(reasons):
        return "FS-INFRA", reasons
    if _MODE_UNIMPL.search(hook_txt) or "先实现" in hook_txt:
        return "MODE-UNIMPL", hook_txt[:160]
    if _HOOK_UNIMPL.search(reasons) or specs.startswith("需新增"):
        return "HOOK-UNIMPL", reasons or specs
    return "OK", ""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--map", help="runid_map.json（旧口径，自带正则分类）")
    ap.add_argument("--contract", help="ready_contract.json（权威口径，"
                    "直接读其 category —— 推荐，杜绝分类漂移）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--approval-out", default=None,
                    help="同时产出『需用户裁决清单』md（同一分类来源，防漂移）")
    a = ap.parse_args()
    if not (a.map or a.contract):
        ap.error("必须给 --contract（推荐）或 --map")

    if a.contract:
        doc = json.loads(Path(a.contract).read_text(encoding="utf-8"))
        entries = doc["entries"]
        source = f"ready_contract.json（权威契约；契约总数 {doc['status']}）"
    else:
        entries = json.loads(Path(a.map).read_text(encoding="utf-8"))["entries"]
        source = "runid_map.json（旧口径）"

    blocked = [e for e in entries if e["status"] == "BLOCKED"]

    rows, per_class = [], defaultdict(list)
    for e in blocked:
        if a.contract:
            cls, why = classify_from_contract(e)
        else:
            cls, why = classify(e)
        per_class[cls].append(e["run_id"])
        rows.append((e["run_id"], e.get("unit", ""),
                     e.get("model") or e.get("model_id", ""), cls, why))

    cnt = Counter(r[3] for r in rows)
    assert sum(cnt.values()) == len(blocked), "分类必须守恒（互斥且完备）"
    for c in CLASS_ORDER:
        if c not in cnt and c != "OK":
            cnt[c] = 0

    L = [f"# {len(blocked)} BLOCKED 逐项裁决（互斥分类）", "",
         f"- 分类来源：{source}",
         f"- BLOCKED 总数：{len(blocked)}（守恒校验通过：Σ 分类 == 总数）",
         f"- 分类统计：" + " / ".join(f"{c}={cnt[c]}" for c in CLASS_ORDER), "",
         "## 互斥类别定义", "",
         "| 类别 | 含义 | 解除条件 |", "|---|---|---|",
         "| RULING | 模型级裁决封锁（A06 load 侧 / byte-enable） | §2.c 路径 spike 验证 + 测试 |",
         "| LICENSE | SPEC CPU2017 授权缺失（W11） | 取得授权 |",
         "| FS-MULTICORE | 需多核 FS（litmus/PARSEC 语义） | 多核 FS 基础设施落地 |",
         "| FS-INFRA | 需 FS 基础设施（TLB 翻译负载） | FS checkpoint 流水线 |",
         "| WORKLOAD-GAP | 规格负载在 FS 下不可得（GAP/Graph500 等） | 取得并装入合法 FS 载体，或规格裁决 |",
         "| MODE-UNIMPL | 规格表 10 标注『先实现』的子模型模式 | 实现该模式 + 测试 |",
         "| HOOK-UNIMPL | 钩子/载体缺口（无模式标注） | 补钩子或补 SE 载体映射 |",
         "| OK | 无上述阻塞（应为 0） | — |", "",
         "## 需用户批准的延期清单", "",
         "以下类别**在可预见范围内无法由本轨道单方面解除**，需批准延期：",
         ""]
    # [R6-GATE] CHAIN-* 也列入本清单：它们不是范围性延期，而是**证据门**——
    # 只能由该 cell 产出「过 check_admission 的 activated pilot」解除（见 MECH）。
    deferrable = [c for c in ("LICENSE", "FS-MULTICORE", "FS-INFRA",
                              "WORKLOAD-GAP", "RULING", "UNRESOLVED",
                              "CHAIN-UNPROVEN",
                              "CHAIN-EVIDENCE-MISSING") if cnt[c]]
    for c in deferrable:
        ids = per_class[c]
        L.append(f"- **{c}**（{len(ids)} 个）：{', '.join(sorted(ids))}")
    if not deferrable:
        L.append("- （无）")
    L += ["", "可自行解除（不需批准，但需实现工作）："]
    for c in ("MODE-UNIMPL", "HOOK-UNIMPL"):
        if cnt[c]:
            L.append(f"- {c}（{cnt[c]} 个）：见下表逐项理由")
    L += ["", "## 逐项明细", "",
          "| RunID | 单元 | 模型 | 互斥类别 | 理由 |", "|---|---|---|---|---|"]
    for rid, unit, model, cls, why in sorted(rows):
        L.append(f"| {rid} | {unit} | {model} | {cls} | {why[:150]} |")

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")

    if a.approval_out:
        MECH = {
            "RULING": ("A06 load 侧定宽完成契约；load SHRINK 结构性不可达（已源码实证与契约钉死）",
                       "实现 load 侧 size 注入 + byte-enable 钩子，或规格裁决仅保留 widen"),
            "LICENSE": ("SPEC CPU2017 需授权；仓库内无任何 SPEC 二进制/golden 可替代",
                        "取得授权，或书面同意以 SE 近似负载替代（改变规格负载）"),
            "FS-MULTICORE": ("语义需多核 FS（litmus MP/SB/LB/IRIW、PARSEC 共享队列）",
                             "多核 FS 平台 + 载具落地"),
            "FS-INFRA": ("**并非缺 FS 基础设施**（该旧措辞已被本轮真机证据反驳）："
                         "载体/checkpoint 齐备，本集成二进制下 T01-F0-W4 产出真实注入"
                         "（arm_tlb_lookup_hit，pfn 0x81d75→0x100000000081d75），"
                         "T04-F0-W4 activated=1 / outcome=Crash / 链 L0→L5 full（1572 事件）。"
                         "真正的阻塞是**逐格 campaign 入口 pilot 未完成**——T05/T06/T07/T08"
                         "为本轮新实现模式、T10 PPN 分层未参数化，均无真机 pilot；"
                         "且 runid_map 的 workload 级静态键 TLB-AliasPerm 仍整批拒绝该负载。",
                         "逐格（含 T05–T08 新模式）真机 30 activated pilot 后，"
                         "解除 TLB-AliasPerm 键并重生成 runid_map → 契约"),
            "WORKLOAD-GAP": (
                "**规格负载在 FS 下不可得**：T08-W9 要求 GAP/Graph500；当前只有 "
                "SE 版 gap_bfs，FS 镜像内没有 GAP/Graph500，armtlb 载体固定为 "
                "tlb_probe.rcS——在 W9 上跑 tlb_probe 会静默改变实验身份。",
                "取得合法 AArch64 GAP/Graph500 并装入 FS 镜像（或不改变语义的 "
                "FS 载体），验证 guest 真执行、oracle 哈希与 walk hook 可观测；"
                "否则保持 BLOCKED_WORKLOAD_GAP。"),
            "UNRESOLVED": ("S10-F2 为规格结构性拒绝（F2 首抽下界 ≫ 实测流长）；"
                           "S01/S02-F0-W1 待 span census 收敛",
                           "规格级重划 cell（长载体）或接受拒绝；census 收敛后写入 span"),
            # [R6-GATE] 证据门（非范围性延期）：解除条件 = 该 cell 产出过
            # check_admission 的 activated pilot。
            "CHAIN-UNPROVEN": (
                "**非范围性延期——链准入门禁（R6-GATE）**：该 cell 的 pilot "
                "PROP-EVT 未过 `lsu_chain_check.check_admission`（无 family-"
                "specific 完整 L0→L5 链，也无显式 containment 且后续层 N/A"
                "(contained)）；此前仅凭 coverage PASS 即判 READY 是假象。",
                "为该 cell 产出真实 activated pilot，其链须满足：完整 L0→L5 "
                "链（同 parent-event DAG、无 Unknown、无跨分支/跨请求/逆时拼接、"
                "逐层必录指标齐），或显式 containment 路径。解除后重生成契约。"),
            "CHAIN-EVIDENCE-MISSING": (
                "**非范围性延期——链准入门禁（R6-GATE）**：契约无该 cell 的 "
                "pilot PROP-EVT 证据（或证据根不可达）——链不可证，故不得判 "
                "READY（绝不因缺证据默认通过）。",
                "为该 cell 运行 pilot 并把 prop_evt 纳入 pilot_evidence.json "
                "（或设 LSU_CHAIN_EVIDENCE_ROOT 指向证据根），再重生成契约。"),
        }
        M = [f"# 需用户裁决 / 延期清单（{len(blocked)} BLOCKED 中的不可自解项）", "",
             f"> 生成自 `tools/lsu_blocked_triage.py --contract`，与 `blocked_triage.md` "
             f"**同一分类来源**（{source}）。", ""]
        total = 0
        for c in deferrable:
            ids = sorted(per_class[c])
            total += len(ids)
            mech, unblock = MECH.get(c, ("—", "—"))
            M += [f"## {c}（{len(ids)} 项）", "",
                  f"- **阻塞机理**：{mech}",
                  f"- **解除条件**：{unblock}",
                  f"- **建议处置**：批准延期，或按上述条件解除", "",
                  "| RunID |", "|---|"]
            M += [f"| {i} |" for i in ids]
            M += [""]
        M += [f"**合计 {total} 项**（其余 {len(blocked) - total} 项为可自行实现，"
              f"见 `blocked_triage.md`）。", ""]
        ao = Path(a.approval_out)
        ao.parent.mkdir(parents=True, exist_ok=True)
        ao.write_text("\n".join(M) + "\n", encoding="utf-8")
        print(f"[triage] approval list → {ao}（{total} 项）")
    print(f"[triage] BLOCKED={len(blocked)} " +
          " ".join(f"{c}={cnt[c]}" for c in CLASS_ORDER) + f" → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
