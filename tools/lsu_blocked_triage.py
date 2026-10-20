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
               "MODE-UNIMPL", "HOOK-UNIMPL", "OK"]

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
    ap.add_argument("--map", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    entries = json.loads(Path(a.map).read_text(encoding="utf-8"))["entries"]
    blocked = [e for e in entries if e["status"] == "BLOCKED"]

    rows, per_class = [], defaultdict(list)
    for e in blocked:
        cls, why = classify(e)
        per_class[cls].append(e["run_id"])
        rows.append((e["run_id"], e["unit"], e["model_id"], cls, why))

    cnt = Counter(r[3] for r in rows)
    assert sum(cnt.values()) == len(blocked), "分类必须守恒（互斥且完备）"
    for c in CLASS_ORDER:
        if c not in cnt and c != "OK":
            cnt[c] = 0

    L = ["# 126 BLOCKED 逐项裁决（互斥分类）", "",
         f"- BLOCKED 总数：{len(blocked)}（守恒校验通过：Σ 分类 == 总数）",
         f"- 分类统计：" + " / ".join(f"{c}={cnt[c]}" for c in CLASS_ORDER), "",
         "## 互斥类别定义", "",
         "| 类别 | 含义 | 解除条件 |", "|---|---|---|",
         "| RULING | 模型级裁决封锁（A06 load 侧 / byte-enable） | §2.c 路径 spike 验证 + 测试 |",
         "| LICENSE | SPEC CPU2017 授权缺失（W11） | 取得授权 |",
         "| FS-MULTICORE | 需多核 FS（litmus/PARSEC 语义） | 多核 FS 基础设施落地 |",
         "| FS-INFRA | 需 FS 基础设施（TLB 翻译负载） | FS checkpoint 流水线 |",
         "| MODE-UNIMPL | 规格表 10 标注『先实现』的子模型模式 | 实现该模式 + 测试 |",
         "| HOOK-UNIMPL | 钩子/载体缺口（无模式标注） | 补钩子或补 SE 载体映射 |",
         "| OK | 无上述阻塞（应为 0） | — |", "",
         "## 需用户批准的延期清单", "",
         "以下类别**在可预见范围内无法由本轨道单方面解除**，需批准延期：",
         ""]
    deferrable = [c for c in ("LICENSE", "FS-MULTICORE", "FS-INFRA",
                              "RULING") if cnt[c]]
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
    print(f"[triage] BLOCKED={len(blocked)} " +
          " ".join(f"{c}={cnt[c]}" for c in CLASS_ORDER) + f" → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
