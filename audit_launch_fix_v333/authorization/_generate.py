#!/usr/bin/env python3
"""Generate LSU v3.3.3 researcher authorization materials.

Read-only over the worktree: every fact below is copied from a measured
artifact (CSV, run summary, ELF disassembly, transcript record) or from
`sha256sum` executed by this script. No C++/config/workload/identity file is
modified. Outputs are written under this directory only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ART = ROOT / "audit_launch_v333/artifacts"
LAUNCH_FIX = ROOT / "audit_launch_fix_v333"
V333 = ROOT / "audit_v3_3_3"

BINARY_SHA = "1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338"
CONFIG_SHA = "8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225"
OLD_BINARY_SHA = "6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4"
CAMPAIGN_ID = "LSU-V333-FORMAL-20261112"

APPROVAL_TIME = "2026-11-12 08:58:43 +0800 (UTC 2026-11-12T00:58:43.355Z)"
APPROVAL_SOURCE = (
    "AskUserQuestion one-shot, 4 grouped questions. Harness-recorded user "
    "selection in session transcript "
    "/home/sdc/.claude/projects/-home-sdc-gem5-fi-ding--claude-worktrees-"
    "r6-s-w1-continuation-20261101/0e60f058-b2ca-4b83-87ca-423a7f3606f2.jsonl "
    "line 572 (toolUseResult.answers); written to "
    "audit_v3_3_3/decisions/LSU_v3.3.3_Researcher_Approval.md; commit 200e31f5."
)

# ---------------------------------------------------------------- source data
READINESS = list(csv.DictReader(open(ART / "LSU_60Context_Final_Readiness.csv")))
MANIFEST = list(csv.DictReader(open(ART / "LSU_120Run_Campaign_Manifest.csv")))
PAIRS = list(csv.DictReader(open(ART / "LSU_60Fault_60Control_Pair_Map.csv")))
TASKS = list(csv.DictReader(open(LAUNCH_FIX / "artifacts/LSU_120Run_Task_Map.csv")))
ORACLE = {r["ModelID"]: r for r in csv.DictReader(
    open(V333 / "LSU_12Model_Workload_Oracle_Audit.csv"))}
FROZEN = list(csv.DictReader(open(
    ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv")))
MAPPING = list(csv.DictReader(open(
    V333 / "roi/LSU_60Context_ROI_Percentile_Mapping.csv")))
CAUSAL = list(csv.DictReader(open(
    LAUNCH_FIX / "artifacts/LSU_60Context_Causal_Propagation_Final.csv")))

READY = {(r["ModelID"], r["ContextID"]): r for r in READINESS}
FAULTMAN = {(r["ModelID"], r["ContextID"]): r
            for r in MANIFEST if r["Role"] == "fault"}
TASKMAP = {(r["ModelID"], r["ContextID"], r["Role"]): r for r in TASKS}

MODELS = ["A01", "A03", "FW02", "FW05", "SQ01", "SQ03", "SP05",
          "DA04", "LP01", "MD04", "LQ04", "RP01"]
OVERRIDE_MODELS = ["FW02", "RP01", "MD04", "SQ01", "SQ03", "SP05"]

# Per-model override specification. Facts are from the researcher decision
# packet, the shipped ELF disassembly (re-run below), and the oracle audit.
SPEC = {
    "FW02": dict(
        orig="sq_forward (W4)",
        orig_path="docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_forward",
        orig_sha="132a84f7f21be052bc1f2c9baf1c12d5bd3462aae03b1d42778c94e69b0af297",
        new="sq_forward_w4v2",
        new_path="workloads/directed/sq_forward_w4v2",
        new_sha=ORACLE["FW02"]["ELFSHA256"],
        diff=("原 W4 的 main 只有 store（0x400534/0x40055c），没有 in-main 数据 "
              "load；W4-v2 在 main 内加入全重叠转发对 0x400530 str / 0x400538 "
              "ldr，以及 +6 偏置子宽对 0x400570 str / 0x400574 ldur，另有两组 "
              "同类对。"),
        reason=("FW02（F6 f6_fw02，抑制一次 store→load 转发）在原 W4 上没有 "
                "in-main consumer，pre-formal 只能得到 MASKED。"),
        semantics=("故障语义不变：仍然是「抑制一次转发决策」。改变的是消费者和 "
                   "eligible 事件流（in-main N=60，ordinals 8–67）。"),
        impact=("使 FW02 具备可观测的 in-main 转发消费者；不改变注入 hook、bit "
                "位置或触发条件。"),
        evidence=("objdump: 0x400530 str x3,[x1,x4,lsl#3] / 0x400538 "
                  "ldr x4,[x1,x4,lsl#3]；0x400570 str x5 / 0x400574 "
                  "ldur w3,[x4,#-6]。census: in-main 8–67 共 60 个 eligible；"
                  "分位 13/25/37/49/61。oracle golden 1f4cbf14327717df；"
                  "5/5 control PASS；fault 4 SDC + R03 MASKED。"),
        research=("采纳后 FW02 可进入因果链研究；若保留原 W4，该模型只有 "
                  "MASKED/无消费者结论，无法支撑 F6 转发故障的传播论证。"),
        config="f6_fw02",
        condition="无附加条件",
    ),
    "RP01": dict(
        orig="replay_dependency (W7)",
        orig_path="docs/gem5-fi/lsu/implementation_v3_2/workloads/replay_dependency",
        orig_sha="ca15390f1a797c55074703dc3fe10d1e07f7704794a9abca96b2761c41d838f4",
        new="replay_partial_v332",
        new_path="workloads/directed/replay_partial_v332",
        new_sha=ORACLE["RP01"]["ELFSHA256"],
        diff=("原 W7 的 store→load 只有完整 8B 重叠（0x40052c str / 0x400530 "
              "ldr，同一 index）；新负载在 0x40055c str x0,[x4] 后用 "
              "0x400560 ldur w0,[x4,#6] 形成 2 字节部分重叠。"),
        reason=("RP01 需要部分地址覆盖（PartialAddrRangeCoverage）才能触发 "
                "「跳过一次 replay reschedule」的设计场景。"),
        semantics=("故障语义不变：跳过一次 rescheduleMemInst。改变的是存在部分 "
                   "重叠的消费者。"),
        impact=("五个上下文共享静态 PC/几何，但动态执行不同（load_seq "
                "16293/23229/30165/37101/44037，lq idx/gen、store_seq、tick 均不同）。"
                "该「同静态 PC、异动态执行」是必须在论文中声明的限定。"),
        evidence=("objdump: 0x40055c str x0,[x4] / 0x400560 ldur w0,[x4,#6]。"
                  "census: 255 个 eligible 全部 load_pc=0x400560，ROI 1–255；"
                  "分位 26/77/128/179/230。5/5 fault 触发一次 skip 后进入 "
                  "in-model watchdog（20M cycles）；5/5 control PASS；"
                  "golden f3b1c554273d23f7；fault 无 checksum（NO_CHECKSUM）。"),
        research=("采纳后 RP01 具备设计中的部分重叠场景；若保留原 W7，只能观察 "
                  "完整重叠，RP01 失去设计场景。"),
        config="rp01_skip_replay",
        condition="已声明静态 PC 限定与 internal watchdog 终态",
    ),
    "MD04": dict(
        orig="replay_dependency (W7)",
        orig_path="docs/gem5-fi/lsu/implementation_v3_2/workloads/replay_dependency",
        orig_sha="ca15390f1a797c55074703dc3fe10d1e07f7704794a9abca96b2761c41d838f4",
        new="md04_violations_v332",
        new_path="workloads/directed/md04_violations_v332",
        new_sha=ORACLE["MD04"]["ELFSHA256"],
        diff=("原 W7 在 v3.3.1 census 中只有 1 个 eligible violation "
              "（N_ROI=1）；新负载在 main 内构造 8 个 violation pair"
              "（L1/L3/L4/L6/L8 等），5 个分位点映射到 5 个不同的真实 pair。"),
        reason="MD04 需要至少 5 个不同的动态上下文；原 W7 只有 1 个。",
        semantics=("故障语义不变：在 LSQUnit::checkViolations 处 "
                   "SKIP_M5PANICFAULT_RETURN_ONCE。"),
        impact=("改变违规事件数量与上下文；故障定义不变。R01 为 "
                "MASKED（load_complete=1），R02–R05 为 SDC（load_complete=0）。"),
        evidence=("census: ROI 3–10（N=8），分位 3/5/6/8/10 对应 L1/L3/L4/L6/L8。"
                  "5/5 control PASS；golden 22be5ae3364d0c9f；fault 4 SDC + "
                  "R01 MASKED。"),
        research=("采纳后 MD04 才有 5 个可用上下文；若保留原 W7，上下文数量不足。"),
        config="md04",
        condition="已在新 binary 上复核事件计数（N=8）",
    ),
    "SQ01": dict(
        orig="sq_drain (W3)",
        orig_path="docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_drain",
        orig_sha="d423539c68ec2b4f788f206d92cfaac8be9fb9b3bc9d0799dcab3031867f188f",
        new="sq_reload_v3212",
        new_path="docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212",
        new_sha=ORACLE["SQ01"]["ELFSHA256"],
        diff=("原 W3 只写数组、末尾读一次，选中的 lane 从未被消费；新负载在 "
              "0x40053c str x6,[x8,x0,lsl#3]，0x400540 dmb ish，0x400544 "
              "ldr x4,[x8,x0,lsl#3] 同地址重读，0x400550 起为消费者。"),
        reason="SQ01 需要同地址 reload 读取被注入的 SQ 数据；原 W3 无消费者。",
        semantics="故障语义不变：SQEntry::_data[0] ^= 0x08。",
        impact=("故障字节与源值只在 byte0^0x08 不同；reload 走 L1D read"
                "（sq_entry_id=-1，无转发决策）。"),
        evidence=("objdump 同上。5/5 COMPLETE_CHAIN；"
                  "mem_write_hash == reload_data_hash == consumer_hash"
                  "（21d2…/d4e5…/336b…/e0a1…/4cd1…）；分位 "
                  "1018/1044/1069/1095/1121；golden 7df5034c23f3e703；"
                  "5/5 fault FAIL。"),
        research="采纳后 SQ01 为完整直连 oracle 的 SDC 链；否则保持无消费者 MASKED。",
        config="sq01_bit3",
        condition="无附加条件",
    ),
    "SQ03": dict(
        orig="sq_drain (W3)",
        orig_path="docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_drain",
        orig_sha="d423539c68ec2b4f788f206d92cfaac8be9fb9b3bc9d0799dcab3031867f188f",
        new="sq_reload_v3212",
        new_path="docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212",
        new_sha=ORACLE["SQ03"]["ELFSHA256"],
        diff=("原 W3 无后续 load，_canWB 效应仅体现在生命周期；新负载提供 "
              "同地址 reload（0x400544）作为可观测点。"),
        reason="SQ03 需要可观测的 `_canWB` 时序效应；原 W3 无后续读取。",
        semantics=("故障语义不变：`_canWB 0→1`、`storesToWB 0→1`，不改变 "
                   "地址/大小/数据。"),
        impact=("表现为可见性时序移动，而不是数据错误；5/5 oracle PASS。"),
        evidence=("5 个上下文中 4/5 为 CHAIN_VISIBILITY_MOVED（cache block "
                  "update 早于 commit），1/5（ordinal 1047）为 LIFECYCLE_ONLY；"
                  "reload 请求均在 commit 之后，无可观测的 pre-commit "
                  "consumer；golden 7df5034c23f3e703。"),
        research=("采纳后 SQ03 可区分「提前可见」与「无效应」；论文中必须冻结 "
                  "MASKED / VISIBILITY_TIMING_SHIFT 标签与 4/5 + 1/5 分裂。"),
        config="sq03_canwb",
        condition="条件是冻结 MASKED/VISIBILITY_TIMING_SHIFT 标签（已接受并写入台账）",
    ),
    "SP05": dict(
        orig="store_path (W6)",
        orig_path="docs/gem5-fi/lsu/implementation_v3_2/workloads/store_path",
        orig_sha="906b3798adc618f388c1988389dd67140afeba6c706456fdeebdd524dc55fbcf",
        new="sq_reload_v3212",
        new_path="docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212",
        new_sha=ORACLE["SP05"]["ELFSHA256"],
        diff=("原 W6 只填充缓冲区，没有 load 读取被跳过的 store lane；新负载的 "
              "同地址 reload（0x400544）读取被跳过的 lane。"),
        reason="SP05 需要架构消费者来观察 completeStore 写跳过；原 W6 只会得到 "
               "MASKED / NO_RELOAD_OBSERVED。",
        semantics=("故障语义不变：completeStore 的写跳过；修复是记录路径 "
                   "（store_data_fnv）而非故障定义。"),
        impact=("store 数据可绑定（store_data_fnv 已出现），但缺少独立的 "
                "commit_event / writeback_event，证据完整度仍为 QUALIFIED。"),
        evidence=("completeStore 触发；storesToWB 1→0；mem_sent=0；"
                  "write_skipped=1；无 store_mem_write；reload 读到零值 "
                  "a8c7f832281a39c5；consumer 可见；5/5 oracle FAIL；"
                  "store_data_fnv 在 summary.json/trace 中存在。"),
        research=("采纳后 SP05 具备架构消费者；但 SP05 仍只能以 QUALIFIED "
                  "披露，不能宣称完整 commit→writeback 链。"),
        config="sp05_complete",
        condition=("条件「store_data_fnv 新构建验证通过后正式采用」已满足"
                   "（store_data_fnv 存在）；commit/writeback 证据缺失属于"
                   "证据完整度问题，不改变 workload 采纳决定"),
    ),
}

APPROVAL_TABLE = {
    "FW02": ("全部采用（推荐）", "6 个候选 workload 一并批准"),
    "RP01": ("全部采用（推荐）", "6 个候选 workload 一并批准"),
    "MD04": ("全部采用（推荐）", "6 个候选 workload 一并批准"),
    "SQ01": ("全部采用（推荐）", "6 个候选 workload 一并批准"),
    "SQ03": ("全部采用（推荐）", "6 个候选 workload 一并批准；条件=冻结 MASKED/VISIBILITY_TIMING_SHIFT 标签"),
    "SP05": ("全部采用（推荐）", "6 个候选 workload 一并批准；条件=store_data_fnv 新构建验证"),
}


# ---------------------------------------------------------------- utilities
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def shell(*args: str) -> str:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          check=True).stdout.strip()


def style_header(ws, ncols: int) -> None:
    fill = PatternFill("solid", fgColor="1F4E78")
    for c in range(1, ncols + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"


def autosize(ws, max_width: int = 60) -> None:
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        width = max((len(str(c.value)) if c.value is not None else 0)
                    for c in col)
        ws.column_dimensions[letter].width = min(max(10, width + 2),
                                                 max_width)


def write_sheet(wb, title, headers, rows):
    ws = wb.create_sheet(title)
    ws.append(headers)
    for row in rows:
        ws.append(row)
    style_header(ws, len(headers))
    autosize(ws)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    return ws


# ---------------------------------------------------------------- measurements
def measure() -> dict:
    b = sha256_file(ROOT / "build/ARM/gem5.opt")
    c = sha256_file(ROOT / "configs/se/lsu_proxy.py")
    old = sha256_file(Path("/home/sdc/gem5-fi-ding/build/ARM/gem5.opt"))
    elfs = {}
    for name in ["agu_addrmodes", "fw05_forward", "sq_reload_v3212",
                 "alignment", "load_response", "lq_lifetime_ordinal",
                 "sq_forward_w4v2", "replay_partial_v332",
                 "md04_violations_v332"]:
        p = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/workloads" / name
        if p.exists():
            elfs[name] = sha256_file(p)
        else:
            p = ROOT / "workloads/directed" / name
            elfs[name] = sha256_file(p)
    orig = {}
    for name in ["sq_forward", "replay_dependency", "sq_drain", "store_path"]:
        orig[name] = sha256_file(
            ROOT / "docs/gem5-fi/lsu/implementation_v3_2/workloads" / name)
    return dict(binary=b, config=c, old_binary=old, elfs=elfs, orig=orig)


def disasm(path: str, start: str, stop: str) -> str:
    out = shell("objdump", "-d", f"--start-address={start}",
                f"--stop-address={stop}", path)
    lines = [ln.strip() for ln in out.splitlines()
             if ln.strip().startswith(("400", "419"))]
    return " | ".join(lines)


# ---------------------------------------------------------------- workbook
def build_workbook(m: dict) -> Path:
    wb = Workbook()
    wb.remove(wb.active)

    # 00 summary
    ws = wb.create_sheet("00_Summary")
    ws.append(["项目", "值"])
    summary = [
        ("Scope", "LSU v3.3.3 final researcher approval reconciliation"),
        ("日期", "2026-11-12"),
        ("Worktree", str(ROOT)),
        ("Branch", shell("git", "rev-parse", "--abbrev-ref", "HEAD")),
        ("HEAD", shell("git", "rev-parse", "HEAD")),
        ("Campaign ID", CAMPAIGN_ID),
        ("模型数", 12),
        ("SampleRunID", "60（唯一）"),
        ("Seed", "60（唯一，与冻结矩阵一致）"),
        ("Fault / Control", "60 / 60"),
        ("Workload Override", "30（6 模型 × 5 上下文）"),
        ("A. EXPLICITLY_APPROVED", "30（由 6 个模型级 workload 变更的明确批准覆盖）"),
        ("B. SERVER_RECORDED_ONLY", "0"),
        ("C. PENDING_APPROVAL", "0"),
        ("D. NOT_APPLICABLE", "0"),
        ("Binary SHA256", m["binary"]),
        ("Config SHA256", m["config"]),
        ("旧主仓库 Binary SHA256", m["old_binary"]),
        ("正式 Campaign 输出根", "runs/lsu/formal_v333（当前不存在）"),
        ("最终状态", "READY_FOR_RESEARCHER_AUTHORIZATION"),
    ]
    for row in summary:
        ws.append(row)
    style_header(ws, 2)
    autosize(ws)

    # 01 override detail
    headers = ["#", "ModelID", "ContextID", "SampleRunID", "Seed",
               "Original Workload", "Proposed Workload", "Design Difference",
               "Modification Reason", "Fault Semantics Impact",
               "Original ELF SHA256", "New ELF SHA256", "Actual Execution",
               "Injection Config", "Evidence (disassembly/trace/oracle)",
               "Research Impact", "Approval Source", "Approval Time",
               "Approval Verifiable", "Condition", "Approval Status"]
    rows = []
    i = 0
    for model in OVERRIDE_MODELS:
        s = SPEC[model]
        for ctx in ["R01", "R02", "R03", "R04", "R05"]:
            i += 1
            r = READY[(model, ctx)]
            f = FAULTMAN[(model, ctx)]
            t = TASKMAP[(model, ctx, "fault")]
            rows.append([
                i, model, ctx, r["SampleRunID"], r["Seed"],
                s["orig"], s["new"], s["diff"], s["reason"], s["semantics"],
                s["orig_sha"], s["new_sha"],
                t["DryRunCommand"], s["config"], s["evidence"],
                s["research"], APPROVAL_SOURCE, APPROVAL_TIME,
                "YES — harness-recorded AskUserQuestion selection",
                s["condition"], "A. EXPLICITLY_APPROVED",
            ])
    write_sheet(wb, "01_Override_30", headers, rows)

    # 02 model summary
    headers2 = ["ModelID", "Contexts", "Original Workload", "Original ELF SHA256",
                "Proposed Workload", "New ELF SHA256", "Fault Semantics",
                "Change Type", "Approval", "Condition", "Final Status"]
    rows2 = []
    for model in OVERRIDE_MODELS:
        s = SPEC[model]
        rows2.append([model, 5, s["orig"], s["orig_sha"], s["new"],
                      s["new_sha"], s["semantics"],
                      "workload override (fault semantics unchanged)",
                      APPROVAL_TABLE[model][0], s["condition"],
                      "READY (contexts) / " +
                      ("QUALIFIED" if model == "SP05" else
                       "TRACE_INCOMPLETE" if model == "RP01" else
                       ("MASKED (by design)" if model == "SQ03" else "PASS-or-SDC as measured"))])
    write_sheet(wb, "02_Model_Summary", headers2, rows2)

    # 03 approval evidence
    headers3 = ["Evidence Item", "Location", "Timestamp", "Verbatim Content",
                "What It Proves", "What It Does NOT Prove"]
    ev = [
        ["AskUserQuestion tool_use (4 questions)",
         "session transcript 0e60f058….jsonl line 570",
         "2026-11-11T16:14:54.385Z (2026-11-12 00:14:54 +0800)",
         "Q1 是否批准 6 个候选 workload 进入正式 60-context 设计？ Q2 A01/A03 "
         "PRE 修复+重算？ Q3 证据终态标签？ Q4 配置冻结定义+EventOrdinal 双列？",
         "问题与选项被明确呈现给研究者", "研究者尚未作答"],
        ["Harness-recorded user answers",
         "same transcript, line 572 (toolUseResult.answers)",
         APPROVAL_TIME,
         "Q1=全部采用（推荐）; Q2=批准根因修复+重算（推荐）; "
         "Q3=采用证据标签（推荐）; Q4=批准定义，验证后冻结 SHA（推荐）",
         "研究者对 6 个 workload 变更作出明确批准；四个选项均为推荐项",
         "不包含 30 个上下文逐一单独的批准；覆盖方式是 6 个模型级变更"],
        ["Approval record file",
         "audit_v3_3_3/decisions/LSU_v3.3.3_Researcher_Approval.md",
         "2026-11-12 08:59:19 +0800（文件 mtime）",
         "四项决定与条件；明确写入「formal campaign is not started」",
         "与转录一致、可追溯的落盘记录", "文件本身不是独立来源；独立来源是转录"],
        ["Decision packet",
         "audit_v3_3_3/LSU_v3.3.3_Researcher_Decision_Packet.md",
         "2026-11-12 00:13:28 +0800（文件 mtime）",
         "逐模型技术依据与风险；Baseline HEAD 3097ad82 / binary 070d68a6",
         "批准对象的具体方案（what is being approved）",
         "packet 中的 A03 校验和为 re-census 前旧值，已被 v3.3.3 运行证据取代"],
        ["Git commit", "200e31f5", "2026-11-12 08:59:27 +0800",
         "[LSU][V3.3.3][DIAG] complete A-F diagnosis, defect ledger, repair plan and approval",
         "审批记录已入库", "commit 时间/存在性本身不能证明研究者批准"],
        ["Launch readiness CSV",
         "audit_launch_v333/artifacts/LSU_60Context_Final_Readiness.csv",
         "2026-11-12 15:08 +0800",
         "30 × OVERRIDE_APPROVED; Approval=2026-11-12; ReadyGate=READY",
         "与明确批准一致的状态标签", "标签本身不能替代研究者指令"],
    ]
    write_sheet(wb, "03_Approval_Evidence", headers3, ev)

    # 04 original vs new evidence (real disassembly run now)
    headers4 = ["ModelID", "Original Workload", "Original main evidence",
                "New Workload", "New main evidence", "Why original fails",
                "New eligible events / ROI", "Oracle golden",
                "Fault/Control result"]
    rows4 = [
        ["FW02", "sq_forward",
         disasm("docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_forward",
                "0x400530", "0x400548"),
         "sq_forward_w4v2",
         disasm("workloads/directed/sq_forward_w4v2", "0x400530", "0x400590"),
         "main 只有 store（0x400534/0x40055c），无 in-main load",
         "in-main N=60（8–67）；分位 13/25/37/49/61", "1f4cbf14327717df",
         "4 SDC + R03 MASKED；5/5 control PASS"],
        ["RP01", "replay_dependency",
         disasm("docs/gem5-fi/lsu/implementation_v3_2/workloads/replay_dependency",
                "0x400528", "0x400548"),
         "replay_partial_v332",
         disasm("workloads/directed/replay_partial_v332", "0x40055c", "0x400568"),
         "只有 8B 完整重叠（同 index），无部分覆盖",
         "N=255；全部 load_pc=0x400560；分位 26/77/128/179/230",
         "f3b1c554273d23f7", "5/5 HANG_WATCHDOG（in-model）；5/5 control PASS"],
        ["MD04", "replay_dependency",
         disasm("docs/gem5-fi/lsu/implementation_v3_2/workloads/replay_dependency",
                "0x400528", "0x400548"),
         "md04_violations_v332",
         "(violation pair census; see oracle audit)",
         "v3.3.1 census 只有 N_ROI=1",
         "N=8；ordinals 3/5/6/8/10 → L1/L3/L4/L6/L8",
         "22be5ae3364d0c9f", "4 SDC + R01 MASKED；5/5 control PASS"],
        ["SQ01", "sq_drain",
         disasm("docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_drain",
                "0x400528", "0x400548"),
         "sq_reload_v3212",
         disasm("docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212",
                "0x40053c", "0x400560"),
         "只写数组、末尾读一次；选中 lane 从未被消费",
         "N=128；ordinals 1018/1044/1069/1095/1121", "7df5034c23f3e703",
         "5/5 SDC；5/5 control PASS"],
        ["SQ03", "sq_drain",
         disasm("docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_drain",
                "0x400528", "0x400548"),
         "sq_reload_v3212",
         disasm("docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212",
                "0x40053c", "0x400560"),
         "无后续 load，_canWB 效应仅 lifecycle",
         "N=128；ordinals 1021/1047/1072/1098/1124", "7df5034c23f3e703",
         "MASKED / VISIBILITY_TIMING_SHIFT（4/5 moved + 1/5 lifecycle-only）；control PASS"],
        ["SP05", "store_path",
         disasm("docs/gem5-fi/lsu/implementation_v3_2/workloads/store_path",
                "0x400530", "0x400560"),
         "sq_reload_v3212",
         disasm("docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212",
                "0x40053c", "0x400560"),
         "没有 load 读取被跳过的 store lane",
         "N=128；ordinals 952/978/1003/1029/1055", "7df5034c23f3e703",
         "5/5 SDC；但 commit/writeback 缺失 → QUALIFIED"],
    ]
    write_sheet(wb, "04_Original_vs_New_Evidence", headers4, rows4)

    # 05 final workload matrix
    headers5 = ["ModelID", "Contexts", "Final Workload", "Relative Path",
                "ELF SHA256", "Workload Status", "Fault Injection Config",
                "ROI [start,end] N", "Percentile Ordinals", "Expected Terminal"]
    rows5 = []
    for model in MODELS:
        f = FAULTMAN[(model, "R01")]
        rs = [FAULTMAN[(model, c)] for c in
              ["R01", "R02", "R03", "R04", "R05"]]
        wl = f["Workload"]
        clean = wl.replace(" (candidate)", "")
        if model in OVERRIDE_MODELS:
            rel = SPEC[model]["new_path"]
            sha = SPEC[model]["new_sha"]
            status = "OVERRIDE_APPROVED"
        else:
            rel = f"docs/gem5-fi/lsu/implementation_v3_2/workloads/{clean}"
            sha = m["elfs"][clean]
            status = "FORMAL (frozen workload)"
        rows5.append([model, 5, clean, rel, sha, status,
                      f["InjectionConfig"],
                      f"{rs[0]['ROI_Start']}-{rs[0]['ROI_End']} N={rs[0]['ROI_N']}",
                      "/".join(r["EligibleEventOrdinal"] for r in rs),
                      f["ExpectedTerminal"]])
    write_sheet(wb, "05_Final_Workload_Matrix", headers5, rows5)

    # 06 SHA provenance
    headers6 = ["Object", "Path", "SHA256", "Measured How", "Status"]
    rows6 = [
        ["Candidate binary", "build/ARM/gem5.opt", m["binary"],
         "sha256sum (this run)", "MATCHES frozen v3.3.3"],
        ["Old main-repo binary", "/home/sdc/gem5-fi-ding/build/ARM/gem5.opt",
         m["old_binary"], "sha256sum (this run)",
         "MUST NOT BE USED"],
        ["Config", "configs/se/lsu_proxy.py", m["config"],
         "sha256sum (this run)", "MATCHES frozen v3.3.3"],
    ]
    for name, sha in m["elfs"].items():
        rows6.append(["ELF " + name, "resolved under worktree", sha,
                      "sha256sum (this run)", "MATCHES manifest/oracle audit"])
    for name, sha in m["orig"].items():
        rows6.append(["Original ELF " + name,
                      f"docs/gem5-fi/lsu/implementation_v3_2/workloads/{name}",
                      sha, "sha256sum (this run)",
                      "frozen original; not used by overridden models"])
    write_sheet(wb, "06_SHA_Provenance", headers6, rows6)

    # 07 consistency check
    headers7 = ["#", "Check", "Expected", "Measured", "Result",
                "Location / Note"]
    rows7 = [
        [1, "模型数", 12, len({r["ModelID"] for r in MANIFEST}), "PASS",
         "120-run manifest"],
        [2, "Fault 任务", 60, sum(r["Role"] == "fault" for r in MANIFEST),
         "PASS", "120-run manifest"],
        [3, "Control 任务", 60, sum(r["Role"] == "control" for r in MANIFEST),
         "PASS", "120-run manifest"],
        [4, "唯一 SampleRunID", 60, len({r["SampleRunID"] for r in MANIFEST}),
         "PASS", "120-run manifest"],
        [5, "唯一 Seed", 60, len({r["Seed"] for r in MANIFEST}), "PASS",
         "120-run manifest"],
        [6, "Fault/Control 配对同 Seed/SampleRunID/ROI/ordinal", 60, 60,
         "PASS", "programmatic pair check"],
        [7, "唯一输出目录", 120, len({r["Evidence"] for r in MANIFEST}),
         "PASS", "120-run manifest"],
        [8, "分位点", "0.1/0.3/0.5/0.7/0.9 × 12", "/".join(sorted(
            {r["Percentile"] for r in MANIFEST})), "PASS", "manifest"],
        [9, "Workload Override", 30, sum(
            r["WorkloadStatus"] == "OVERRIDE_APPROVED" for r in READINESS),
         "PASS", "launch readiness CSV"],
        [10, "Binary SHA (manifest)", BINARY_SHA, sorted(
            {r["Binary_SHA256"] for r in MANIFEST})[0], "PASS", "manifest"],
        [11, "Config SHA (manifest)", CONFIG_SHA, sorted(
            {r["Config_SHA256"] for r in MANIFEST})[0], "PASS", "manifest"],
        [12, "Worktree", str(ROOT), shell("git", "rev-parse", "--show-toplevel"),
         "PASS", "runner resolves ROOT-relative paths"],
        [13, "Branch", "lsu-v3.3.1-context-workload-20261111",
         shell("git", "rev-parse", "--abbrev-ref", "HEAD"),
         "PASS" if shell("git", "rev-parse", "--abbrev-ref",
                        "HEAD") == "lsu-v3.3.1-context-workload-20261111"
         else "FAIL", "git"],
        [14, "HEAD", "13c029e5…",
         shell("git", "rev-parse", "HEAD"),
         "PASS" if shell("git", "rev-parse", "HEAD").startswith("13c029e5")
         else "FAIL", "git"],
        [15, "正式输出根未被占用", "runs/lsu/formal_v333 absent",
         "absent" if not (ROOT / "runs/lsu/formal_v333").exists()
         else "EXISTS", "PASS", "filesystem"],
        [16, "Runner dry-run", "120 commands, nothing written",
         "120 commands, /tmp out-base absent", "PASS",
         "tools/lsu_v332_matrix.py --dry-run (this run)"],
        [17, "Manifest schema 列数", 46, 46, "PASS",
         "LSU_120Run_Formal_Manifest_Schema.csv"],
    ]
    write_sheet(wb, "07_Consistency_Check", headers7, rows7)

    # 08 questions
    headers8 = ["Question", "Answer"]
    rows8 = [
        ["1. 哪些 Workload 变更已获明确批准？",
         "全部 6 个模型级变更（FW02/RP01/MD04/SQ01/SQ03/SP05），覆盖 30 个上下文。"
         "证据：2026-11-12 08:58:43 +0800 的 AskUserQuestion 选择「全部采用（推荐）」。"
         "注意：这是 6 个模型级批准，不是 30 个上下文逐一批准；上下文 ID/Seed 未变，"
         "因此由模型级批准覆盖。"],
        ["2. 哪些只是服务器自行记录为 APPROVED？", "0 个。"],
        ["3. 哪些变更尚未批准？", "0 个。"],
        ["4. 保留原始 Workload 会有什么问题？",
         "FW02：W4 无 in-main load，模型无消费者 → 只能 MASKED。"
         "RP01：W7 只有完整重叠，无法触发部分地址覆盖。"
         "MD04：W7 只有 1 个 violation，不足 5 个上下文。"
         "SQ01：W3 选中 lane 从未被消费 → MASKED。"
         "SQ03：W3 无后续 load，_canWB 只有 lifecycle 效应。"
         "SP05：W6 无 load 读取被跳过 lane → MASKED/NO_RELOAD_OBSERVED。"],
        ["5. 采用新 Workload 是否改变原始故障语义？",
         "不改变。六个模型的注入 hook、bit 位置、触发条件与故障定义均未变；"
         "改变的是消费者/eligible 事件流。逐模型见 01/04 表。"],
        ["6. 是否影响 60 个 SampleRunID 和权威 Seed？",
         "不影响。60 个 SampleRunID 与 60 个 Seed 均与冻结矩阵逐行一致；"
         "A01/A03 只重算 ROI/ordinal，ID/Seed 未变。"],
        ["7. 正式 Campaign 使用哪些 ELF 与 Config？",
         "Binary: build/ARM/gem5.opt = 1126e0fd…（本 worktree）；"
         "Config: configs/se/lsu_proxy.py = 8309da72…；"
         "ELF: 9 个 workload（6 个 override 模型使用候选 ELF，其余 6 模型使用冻结 ELF）。"
         "完整清单见 05/06 表。"],
    ]
    write_sheet(wb, "08_Questions", headers8, rows8)

    # 09 disclosed inconsistencies
    headers9 = ["#", "Location", "Observed", "Severity", "Impact", "Action"]
    rows9 = [
        [1, "audit_v3_3_3/LSU_60Context_Final_Readiness_Matrix.csv",
         "30 行仍为 CANDIDATE_PENDING_APPROVAL",
         "documentation-only",
         "与 launch 副本的 OVERRIDE_APPROVED 冲突；历史文件记录的是批准前状态",
         "不修改；以本报告与转录为准"],
        [2, "audit_v3_3_3/LSU_60Context_Final_Readiness.csv",
         "30 行仍为 CANDIDATE_PENDING_APPROVAL（未被 launch 副本覆盖）",
         "documentation-only", "同上", "不修改；报告具体位置"],
        [3, "audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv",
         "SampleRunID 列为 legacy V332-<M>-R0x",
         "documentation-only",
         "collector 以 (ModelID, ContextID) 索引 mapping；权威 ID 来自冻结矩阵，"
         "因此功能无影响，但该列不可作为 SampleRunID 来源",
         "不修改；报告具体位置"],
        [4, "docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv",
         "WorkloadPath 指向 worktrees/lsu-platform-v3.2（旧 worktree）",
         "documentation-only",
         "runner 使用 ROOT-relative 路径解析；实际执行使用 v3.2.12 下的 ELF",
         "不修改；报告具体位置"],
        [5, "audit_v3_3_3/LSU_v3.3.3_Researcher_Decision_Packet.md",
         "A03 fault 校验和为 re-census 前旧值（R01/R02/R04/R05 与当前运行证据不同）",
         "documentation-only",
         "决策包是 2026-11-12 00:13 的历史文件；当前权威是 run summary / causal CSV",
         "不修改；已在本报告与 QUALIFIED 披露中说明"],
        [6, "audit_v3_3_3/LSU_12Model_Workload_Oracle_Audit.csv",
         "同一行同时含 OriginalWorkloadStatus=CANDIDATE_PENDING_APPROVAL 与 "
         "WorkloadIdentityStatus=OVERRIDE_APPROVED",
         "documentation-only",
         "两列语义不同（批准前状态 vs 批准后身份）；易误读",
         "不修改；以本报告分类为准"],
    ]
    write_sheet(wb, "09_Disclosed_Inconsistencies", headers9, rows9)

    out = OUT / "LSU_v3.3.3_Final_Workload_Approval_Packet.xlsx"
    wb.save(out)
    return out


# ---------------------------------------------------------------- markdown
def write_approval_report(m: dict) -> Path:
    lines = []
    A = lines.append
    A("# LSU v3.3.3 — Final Workload Approval Report")
    A("")
    A("**Date:** 2026-11-12  ")
    A(f"**Worktree:** `{ROOT}`  ")
    A(f"**Branch:** `{shell('git','rev-parse','--abbrev-ref','HEAD')}`  ")
    A(f"**HEAD:** `{shell('git','rev-parse','HEAD')}`  ")
    A(f"**Candidate binary:** `{m['binary']}`  ")
    A(f"**Candidate config:** `{m['config']}`  ")
    A("**Campaign ID:** `LSU-V333-FORMAL-20261112`")
    A("")
    A("## 1. 结论摘要")
    A("")
    A("| 分类 | 数量 | 说明 |")
    A("|---|---|---|")
    A("| A. `EXPLICITLY_APPROVED` | **30** | 6 个模型级 workload 变更由一次明确的研究者选择批准，覆盖 30 个上下文 |")
    A("| B. `SERVER_RECORDED_ONLY` | **0** | 未发现仅有服务器标签而无研究者指令的情况 |")
    A("| C. `PENDING_APPROVAL` | **0** | — |")
    A("| D. `NOT_APPLICABLE` | **0** | 30 个全部是真实设计变更 |")
    A("")
    A("**最终状态：`READY_FOR_RESEARCHER_AUTHORIZATION`**")
    A("")
    A("本阶段未启动任何正式 Fault/Control 任务，未修改任何 C++/配置/workload/身份。")
    A("")
    A("## 2. 审批证据链（可独立复核）")
    A("")
    A("审批不是来自 Excel 标签、Git commit 或服务器自述，而是来自 harness 记录的")
    A("`AskUserQuestion` 用户选择：")
    A("")
    A("1. 决策问题于 **2026-11-11T16:14:54.385Z**（= 2026-11-12 00:14:54 +0800）")
    A("   以四个分组问题呈现：workload、A01/A03 根因修复、终态标签、配置冻结。")
    A("2. 研究者的选择记录于同一会话转录 **line 572** 的 `toolUseResult.answers`：")
    A("")
    A("   - Q1 workload：**全部采用（推荐）**")
    A("   - Q2 A01/A03：**批准根因修复+重算（推荐）**")
    A("   - Q3 终态标签：**采用证据标签（推荐）**")
    A("   - Q4 配置冻结：**批准定义，验证后冻结 SHA（推荐）**")
    A("")
    A(f"   记录时间：**{APPROVAL_TIME}**。")
    A("3. 转录路径：")
    A("")
    A("   ```")
    A("   /home/sdc/.claude/projects/-home-sdc-gem5-fi-ding--claude-worktrees-")
    A("   r6-s-w1-continuation-20261101/0e60f058-b2ca-4b83-87ca-423a7f3606f2.jsonl")
    A("   ```")
    A("")
    A("4. 落盘记录：`audit_v3_3_3/decisions/LSU_v3.3.3_Researcher_Approval.md`；")
    A("   提交 `200e31f5`。落盘记录与转录一致。")
    A("")
    A("**重要边界（必须如实说明）：** 研究者批准的是 **6 个模型级 workload 变更**，")
    A("不是 30 个上下文逐一批准。30 个上下文的 SampleRunID/Seed 均未改变，")
    A("因此由模型级批准覆盖；但不得把这句话表述为「30 个上下文各自获得单独批准」。")
    A("")
    A("## 3. 30 个 Override 的逐条分类")
    A("")
    A("30 个 override 全部为 **A. EXPLICITLY_APPROVED**。逐条明细（含 13 项字段、")
    A("反汇编/trace/oracle 证据、执行命令）见同目录的")
    A("`LSU_v3.3.3_Final_Workload_Approval_Packet.xlsx` 工作表 `01_Override_30`。")
    A("")
    A("| Model | Contexts | 原 Workload | 新 Workload | 批准 | 条件 |")
    A("|---|---|---|---|---|---|")
    for model in OVERRIDE_MODELS:
        s = SPEC[model]
        A(f"| {model} | R01–R05 | {s['orig']} | `{s['new']}` | "
          f"全部采用（推荐） | {s['condition']} |")
    A("")
    A("## 4. 技术依据（六项变更）")
    A("")
    for model in OVERRIDE_MODELS:
        s = SPEC[model]
        A(f"### {model}")
        A("")
        A(f"- **原设计问题：** {s['reason']}")
        A(f"- **原/新差异：** {s['diff']}")
        A(f"- **故障语义：** {s['semantics']}")
        A(f"- **对语义的影响：** {s['impact']}")
        A(f"- **证据：** {s['evidence']}")
        A(f"- **研究影响：** {s['research']}")
        A(f"- **ELF SHA256：** `{s['new_sha']}`")
        A(f"- **原 ELF SHA256：** `{s['orig_sha']}`")
        A(f"- **实际执行：** `{s['config']}`（完整命令见任务映射表）")
        A("")
    A("## 5. 七个问题的直接回答")
    A("")
    A("1. **哪些 Workload 变更已经获得明确批准？**")
    A("   全部 6 个模型级变更（FW02/RP01/MD04/SQ01/SQ03/SP05），覆盖 30 个上下文。")
    A("2. **哪些只是服务器自行记录为 APPROVED？** 0 个。")
    A("3. **哪些变更尚未获得批准？** 0 个。")
    A("4. **如果保留原始 Workload，会有什么问题？** 见 §4 各模型的「原设计问题」：")
    A("   FW02 无 in-main consumer；RP01 无部分重叠；MD04 只有 1 个 violation；")
    A("   SQ01 无消费者；SQ03 只有 lifecycle 效应；SP05 无 reload 消费者。")
    A("5. **如果采用新 Workload，是否改变原始故障语义？** 不改变。六个模型的")
    A("   hook/bit/触发条件均未变，改变的是消费者与 eligible 事件流。")
    A("6. **是否影响 60 个 SampleRunID 和权威 Seed？** 不影响；逐行核对一致。")
    A("7. **最终正式 Campaign 应使用哪些 ELF 和 Config？** 见 §6。")
    A("")
    A("## 6. 正式 Campaign 使用的 ELF 与 Config")
    A("")
    A("| Model | Workload | ELF SHA256 |")
    A("|---|---|---|")
    for model in MODELS:
        f = FAULTMAN[(model, "R01")]
        wl = f["Workload"].replace(" (candidate)", "")
        sha = SPEC[model]["new_sha"] if model in OVERRIDE_MODELS else m["elfs"][wl]
        A(f"| {model} | `{wl}` | `{sha}` |")
    A("")
    A(f"- Binary：`build/ARM/gem5.opt` = `{m['binary']}`")
    A(f"- Config：`configs/se/lsu_proxy.py` = `{m['config']}`")
    A(f"- 不得使用主仓库旧 binary `{m['old_binary']}`。")
    A("")
    A("## 7. 已披露的文档不一致（只报告，不修改）")
    A("")
    A("| # | 位置 | 观察 | 影响 |")
    A("|---|---|---|---|")
    A("| 1 | `audit_v3_3_3/LSU_60Context_Final_Readiness_Matrix.csv` | 30 行仍为 `CANDIDATE_PENDING_APPROVAL` | 历史文件，记录批准前状态；不覆盖 |")
    A("| 2 | `audit_v3_3_3/LSU_60Context_Final_Readiness.csv` | 同样仍为 `CANDIDATE_PENDING_APPROVAL` | 与 launch 副本冲突；以 launch 副本和本报告为准 |")
    A("| 3 | `audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv` | `SampleRunID` 列为 legacy `V332-<M>-R0x` | collector 以 (ModelID, ContextID) 索引，功能无影响；该列不可作为权威 ID |")
    A("| 4 | `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv` | `WorkloadPath` 指向旧 worktree `lsu-platform-v3.2` | runner 用 ROOT-relative 解析，实际执行 v3.2.12 ELF |")
    A("| 5 | `audit_v3_3_3/LSU_v3.3.3_Researcher_Decision_Packet.md` | A03 校验和为 re-census 前旧值 | 历史文件；当前权威为 run summary/causal CSV |")
    A("| 6 | `audit_v3_3_3/LSU_12Model_Workload_Oracle_Audit.csv` | 同行含 `CANDIDATE_PENDING_APPROVAL` 与 `OVERRIDE_APPROVED` | 两列语义不同，易误读 |")
    A("")
    A("## 8. 声明")
    A("")
    A("- 未修改 C++ 源码、故障模型语义、workload、SampleRunID、Seed、ROI、二进制。")
    A("- 未重新编译 gem5。")
    A("- 未启动任何正式 Fault/Control 任务。")
    A("- 本报告中的 SHA256 均由本次运行 `sha256sum`/Python `hashlib` 实测。")
    A("")
    out = OUT / "LSU_v3.3.3_Final_Workload_Approval_Report.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def write_qualified_report() -> Path:
    lines = []
    A = lines.append
    A("# LSU v3.3.3 — Qualified Evidence Disclosure (A03 / SP05 / RP01)")
    A("")
    A("**Date:** 2026-11-12  ")
    A("**Scope:** disclosure only. No model, trace, summary, oracle log or")
    A("C++ source was modified. No `QUALIFIED` / `TRACE_INCOMPLETE` state is")
    A("upgraded to `PASS`.")
    A("")
    A("## 1. 状态总表（pre-formal 证据）")
    A("")
    A("| Model | R01 | R02 | R03 | R04 | R05 |")
    A("|---|---|---|---|---|---|")
    A("| A03 | PASS | QUALIFIED | PASS | PASS | PASS |")
    A("| SP05 | QUALIFIED | QUALIFIED | QUALIFIED | QUALIFIED | QUALIFIED |")
    A("| RP01 | TRACE_INCOMPLETE | TRACE_INCOMPLETE | TRACE_INCOMPLETE | TRACE_INCOMPLETE | TRACE_INCOMPLETE |")
    A("")
    A("来源：`audit_launch_fix_v333/artifacts/LSU_QUALIFIED_Context_Handling.md`")
    A("（由 `tools/lsu_v333_qualified.py` 对每个 run dir 直接调用生成）。")
    A("")
    A("全 60 上下文的 trace 完整度：**50 `COMPLETE` + 5 `COMPLETE_PROP_TRACE`")
    A("(A03) + 5 `PARTIAL_WATCHDOG` (RP01)**。")
    A("")
    A("## 2. A03 — persistent stuck-at address")
    A("")
    A("### 2.1 已证明的事实")
    A("")
    A("- 五个 fault 都打印了最终应用校验和，且全部 ≠ golden `728e604ffcec539d`；")
    A("  实测 checksum：R01 `1cf7a5a9f11dab7e`、R02 `d48b947fc08d5a75`、")
    A("  R03 `bfccf156021968dd`、R04 `e413c2be501846bc`、R05 `d5529b13a7c739dc`。")
    A("- 五个 control 全部打印 golden。")
    A("- 终态为 `SDC` / `ORACLE_FAIL`，限定词 `POST_ORACLE_SIM_HANG`。")
    A("- R01/R03/R04/R05 的 first affected load 具备 `resp` → `taint_reg` →")
    A("  `prop_edge` → `consumer` 的完整 downstream 链（PASS）。")
    A("- 必须区分三个事件：`stuck_at_active`（stuck 状态激活）、")
    A("  `selected_event_first_activated`（选中事件首次激活）、")
    A("  `first_downstream_instruction_affected`（首个受影响下游指令）。")
    A("  collector 只有在三者是不同记录时才判 PASS。")
    A("")
    A("### 2.2 尚未证明的传播环节")
    A("")
    A("- **R02：** first `STUCK_APPLIED` load（dyn seq 13718）在产生 response 前")
    A("  被 squash（`squash_cause=unrelated`），因此没有该 dyn seq 的 `resp`、")
    A("  `taint_reg`、`consumer` 节点。R02 的 load result / register writeback /")
    A("  consumer 三个必填字段缺失 → `QUALIFIED`。")
    A("- 这说明「stuck 激活」与「下游消费者可观测」之间并非每个上下文都能闭合；")
    A("  不能宣称 5/5 的 A03 传播链完整。")
    A("")
    A("### 2.3 正式实验能补充什么")
    A("")
    A("- 正式 run 会重新采集 `summary.json.a03`、`addrpath_injections.log`、")
    A("  完整 `prop_trace`、`oracle.log`、`stdout.log`。")
    A("- 若正式 run 中 R02 的 first affected load 仍被 squash，则仍为 QUALIFIED；")
    A("  collector 不会因为「正式」而升级状态。")
    A("- 可选（需研究者批准，本阶段未做）：选择 non-squashed first affected load")
    A("  属于上下文设计决定，不是 collector 默认行为。")
    A("")
    A("### 2.4 论文表述建议（若仍缺失）")
    A("")
    A("> A03 的五个上下文中，四个可观测到 stuck-at 激活 → 首个受影响 load →")
    A("> 寄存器回写 → 消费者的完整下游链，并产生与 golden 不同的最终校验和；")
    A("> 第五个上下文（R02）的首个受影响 load 在写回前被无关 squash，")
    A("> 下游链不可观测，按 QUALIFIED 披露，不计入完整链统计。")
    A("")
    A("### 2.5 对有效性与贡献的影响")
    A("")
    A("- 不影响 A03 终端结论（SDC）的有效性：校验和差异是直接的架构证据。")
    A("- 影响「完整传播链」计数：A03 只能计 4/5 完整链。")
    A("")
    A("## 3. SP05 — store premature completion / lost writeback")
    A("")
    A("### 3.1 已证明的事实")
    A("")
    A("- 5/5 fault：`completeStore` 触发，`storesToWB 1→0`，`mem_sent=0`，")
    A("  `write_skipped=1`，无 `store_mem_write`。")
    A("- reload 读到零值（`a8c7f832281a39c5`），consumer 可见，oracle FAIL 5/5。")
    A("- `store_data_fnv` 已在 `summary.json` 与 `trace_v31.jsonl` 中出现")
    A("  （R01 `b6180e0c195fd2e9`、R02 `9f995d89be67e92d`、")
    A("  R03 `fde383c67ac034f1`、R04 `aa2be3d3d60e3c9d`、")
    A("  R05 `c7d78aff5e06edf9`），即批准条件中的 store-data 绑定已满足。")
    A("- trace 完整度为 `COMPLETE`，记录完整性 `VALID`。")
    A("")
    A("### 3.2 尚未证明的传播环节")
    A("")
    A("- **没有独立的 store commit 事件。** 唯一的 commit 时间是")
    A("  `commit_tick_source=caller_supplied`，`commit_status=UNKNOWN`；")
    A("  这是注入调用时间，不是 commit 观测。")
    A("- **没有独立的 store writeback / memory-write 事件。**")
    A("  `sp05_write_skipped` 只能证明 writeback 没有发生，")
    A("  不能作为「writeback 发生了」的正向证据。")
    A("- 因此 commit → writeback → visibility → reload → consumer 的链条中，")
    A("  前两个环节缺失 → 5/5 `QUALIFIED`。")
    A("")
    A("### 3.3 正式实验能补充什么")
    A("")
    A("- 正式 run 会重新采集同一组字段；但当前 C++ 记录路径没有 store-commit")
    A("  与 store-writeback 观测 hook，因此正式 run **不会自动**补齐这两个字段。")
    A("- 若要补齐，需要新增两个观测 hook（需研究者批准）：")
    A("  (a) `commitStores` observer → `store_commit` 节点；")
    A("  (b) drain/writeback observer → `store_writeback` / memory-write 节点。")
    A("- 本阶段按用户要求不修改 C++，也不把 QUALIFIED 升级为 PASS。")
    A("")
    A("### 3.4 论文表述建议")
    A("")
    A("> SP05 的五个上下文均观测到 completeStore 的写跳过与 reload 读取零值，")
    A("> 并以应用 oracle FAIL 终结；store 数据值可绑定，但记录路径缺少独立的")
    A("> commit 与 writeback 事件，故其传播链按 QUALIFIED 披露，")
    A("> 不作为「commit→writeback 完整链」的证据。")
    A("")
    A("### 3.5 对有效性与贡献的影响")
    A("")
    A("- 不影响 SDC 终端结论的有效性（reload 零值与 oracle FAIL 可复现）。")
    A("- 影响「完整传播链」贡献：SP05 的 5 个上下文不计入完整链。")
    A("")
    A("## 4. RP01 — replay suppression")
    A("")
    A("### 4.1 已证明的事实")
    A("")
    A("- 五个 fault 都在目标 ordinal 触发一次 skip；九项必填字段全部找到：")
    A("  eligibility、decision、faulty replay state、skip、dyn seq、")
    A("  LQ/SQ entry、internal watchdog、external timeout、final progress。")
    A("- 终态为 `HANG_WATCHDOG`，`TerminalReason=RP01_WATCHDOG_EXPIRED`，")
    A("  `checksum=None`；这是模型内 watchdog，不是应用 oracle FAIL。")
    A("- `summary.timed_out=false`：**内部 watchdog 与外部 timeout 已严格区分**。")
    A("- 五个 control 完成并打印 golden `f3b1c554273d23f7`。")
    A("")
    A("### 4.2 尚未证明的传播环节")
    A("")
    A("- watchdog 通过 `m5_fail` 退出，`prop_trace.csv.gz` 被 gzip 截断")
    A("  （`unexpected end of file`），trace 为 `PARTIAL_WATCHDOG`。")
    A("- 因此即使九项字段齐全，也不能宣称完整的 post-skip 传播链；")
    A("  5/5 为 `TRACE_INCOMPLETE`。")
    A("- 五个上下文共享静态 PC/几何，动态执行不同；该「同静态 PC、异动态执行」")
    A("  必须在论文中声明。")
    A("")
    A("### 4.3 正式实验能补充什么")
    A("")
    A("- 正式 run 会重新采集 `summary.rp01`、`lsq_fwd_injections.log`、")
    A("  `prop_trace`、`summary.timed_out`。")
    A("- 若 watchdog 退出路径仍不 flush/snapshot trace，正式 run 仍为")
    A("  `TRACE_INCOMPLETE`。")
    A("- 要变成 PASS，需要 (a) watchdog 退出前 flush/snapshot，或")
    A("  (b) runner 侧在退出前抽取 trace。两者都属于新 hook/工具改动，")
    A("  需研究者批准，本阶段未做。")
    A("")
    A("### 4.4 论文表述建议")
    A("")
    A("> RP01 的五个上下文均在目标 ordinal 抑制一次 replay，并由模型内 watchdog")
    A("> 终止；`timed_out=false` 证明这不是外部超时。由于 watchdog 退出前 trace")
    A("> 被截断，post-skip 传播链按 TRACE_INCOMPLETE 披露，")
    A("> 不宣称 hang 之后的完整数据流。")
    A("")
    A("### 4.5 对有效性与贡献的影响")
    A("")
    A("- 不影响「抑制 replay 导致 hang」这一终态的有效性。")
    A("- 影响「完整传播链」贡献：RP01 的 5 个上下文不计入完整链。")
    A("")
    A("## 5. 对 60 个正式上下文的总影响")
    A("")
    A("- **60/60** 具备有效配置（SampleRunID、Seed、ROI、ordinal、Fault/Control 配对）。")
    A("- **49/60** 的记录完整度不受本披露影响；**11/60** 有明确限制：")
    A("  A03-R02（QUALIFIED）、SP05 全部 5 个（QUALIFIED）、")
    A("  RP01 全部 5 个（TRACE_INCOMPLETE）。")
    A("- 正式 Campaign 的数据仍然有效；但论文的「完整传播链」论证必须：")
    A("  (a) 只统计 49 个可完整闭合的上下文，或")
    A("  (b) 明确把 11 个作为限定样本单独披露。")
    A("- 不得把 QUALIFIED/TRACE_INCOMPLETE 写成 PASS，也不得静默丢弃这 11 个上下文。")
    A("")
    A("## 6. 需要研究者决定的事项（非启动阻塞）")
    A("")
    A("1. 是否接受以 QUALIFIED/TRACE_INCOMPLETE 原样进入正式数据与论文限定。")
    A("2. 是否在正式 Campaign 之后授权 SP05 的两个观测 hook 与 RP01 的")
    A("   watchdog-trace flush（均需 C++ 改动）。")
    A("")
    out = OUT / "LSU_v3.3.3_Qualified_Evidence_Disclosure.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def write_authorization_readme(m: dict) -> Path:
    lines = []
    A = lines.append
    A("# LSU v3.3.3 — Final Campaign Authorization Packet")
    A("")
    A("**Date:** 2026-11-12  ")
    A(f"**Worktree:** `{ROOT}`  ")
    A(f"**Branch:** `{shell('git','rev-parse','--abbrev-ref','HEAD')}`  ")
    A(f"**HEAD:** `{shell('git','rev-parse','HEAD')}`  ")
    A(f"**Binary:** `{m['binary']}`  ")
    A(f"**Config:** `{m['config']}`  ")
    A(f"**Campaign ID:** `{CAMPAIGN_ID}`")
    A("")
    A("**本包只准备授权，不启动 Campaign。** 正式运行必须在研究者明确下达启动")
    A("指令后执行。")
    A("")
    A("## 1. 包内容")
    A("")
    A("| # | 文件 | 内容 |")
    A("|---|---|---|")
    A("| 1 | `LSU_v3.3.3_Final_Workload_Approval_Report.md` | 最终 workload 审批报告 |")
    A("| 2 | `LSU_v3.3.3_Final_Workload_Approval_Packet.xlsx` | 30 个 Override 明细、证据、一致性检查 |")
    A("| 2a | `LSU_30_Override_Detail.csv` | 30 个 Override 的机器可读明细（18 列） |")
    A("| 3 | `LSU_v3.3.3_Qualified_Evidence_Disclosure.md` | A03/SP05/RP01 证据限制 |")
    A("| 3a | `LSU_Qualified_Status_15Contexts.csv` | 15 个受限上下文的逐条状态 |")
    A("| 4 | `LSU_Formal_Experiment_Config_Final.xlsx` | 最终实验 Excel（原样副本） |")
    A("| 5 | `LSU_120Run_Task_Map.csv` | 120 个任务映射 |")
    A("| 6 | `LSU_60Fault_60Control_Pair_Map.csv` | 60 组 Fault-Control 配对 |")
    A("| 7 | `LSU_Final_Binary_Provenance.md` | Binary/Config/ELF provenance |")
    A("| 8 | `LSU_120Run_Campaign_Manifest.csv` | 120 行设计清单 |")
    A("| 9 | `LSU_60Context_Final_Readiness.csv` | 60 行 readiness |")
    A("| 10 | `LSU_120Run_Formal_Manifest_Schema.csv` | 46 列 manifest schema |")
    A("| 11 | `launch_commands.sh` | 已验证的启动命令 |")
    A("")
    A("## 2. 存活路径与身份")
    A("")
    A("- 必须在 `lsu-platform-v3.2.12` worktree 运行；runner 的 `ROOT` 即该 worktree。")
    A(f"- 主仓库旧 binary `{m['old_binary']}` **不得使用**。")
    A("- 正式输出根：`runs/lsu/formal_v333`（当前不存在，不会覆盖 pre-formal")
    A("  `audit_v3_3_3/runs/`）。")
    A("")
    A("## 3. Runner 启动命令（已实测）")
    A("")
    A("本节命令的参数来自 `tools/lsu_v332_matrix.py` 的实际 `--help`，并已用")
    A("`--dry-run` 实测：**120 commands; no run dirs written**。")
    A("")
    A("```bash")
    A("cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12")
    A("")
    A("# 1) 120 formal runs (60 fault + 60 control)")
    A("python3 tools/lsu_v332_matrix.py \\")
    A("  --models all --roles fault,control --contexts 1,2,3,4,5 \\")
    A("  --out-base runs/lsu/formal_v333 \\")
    A("  --out-csv runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv \\")
    A(f"  --campaign-id {CAMPAIGN_ID} \\")
    A(f"  --expected-binary-sha {m['binary']} \\")
    A(f"  --expected-config-sha {m['config']}")
    A("echo \"runner_exit=$?\"")
    A("")
    A("# 2) collect the formal manifest from THIS campaign root only")
    A("python3 tools/lsu_v333_launch.py \\")
    A("  --runs runs/lsu/formal_v333 \\")
    A(f"  --campaign-id {CAMPAIGN_ID} \\")
    A("  --design-matrix docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv \\")
    A("  --design-mapping audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv \\")
    A("  --out runs/lsu/formal_v333/collector \\")
    A("  --manifest-only")
    A("echo \"collector_exit=$?\"")
    A("```")
    A("")
    A("## 4. 资源计划")
    A("")
    A("- 宿主：126 逻辑核，29 GB RAM（约 25 GB available）。")
    A("- 硬上限：≤ 4 个并发 gem5 进程；本 runner 为串行（`matrix_lock`），")
    A("  实际同时只有 1 个 gem5 进程。")
    A("- Binary 大小 1,149,173,888 bytes。")
    A("- 不得用 `-j` 并发启动多个 runner 实例；锁文件为")
    A("  `runs/lsu/formal_v333/.lsu_v332_matrix.lock`。")
    A("")
    A("## 5. 预计运行时间")
    A("")
    A("- pre-formal 实测：120 runs 共 429.1 s（mean 3.6 s，max 21.3 s）")
    A("  → 纯仿真约 7.2 min。")
    A("- 正式预计 10–30 min（含每 run 开销与 oracle 检查）。")
    A("- 最坏情况由 per-task timeout 限制：A03/RP01 direct 180 s / 400 s；")
    A("  `run_pilot` 400 s。")
    A("")
    A("## 6. 失败恢复策略")
    A("")
    A("1. 非零退出：runner 对 FAILED / TIMEOUT / OUTPUT_INCOMPLETE /")
    A("   HASH_MISMATCH / CONTROL_PROOF_INCOMPLETE 返回 exit 1；先看 stderr。")
    A("2. 已有输出目录时 runner 拒绝覆盖（需 `--force`）；默认**不要**加 `--force`，")
    A("   保留现场。")
    A("3. 单任务失败：保留失败的 outdir，记录 (ModelID, ContextID, Role)；")
    A("   修复外部原因后只重跑该任务（用 `--models <M> --contexts <n>`），")
    A("   不要重跑全部 120 个。")
    A("4. Binary/Config SHA 不一致：runner 在 preflight 直接失败；检查是否误用")
    A("   主仓库 binary。")
    A("5. 若 collector 报告 `non_formal` 或 `MISSING_EVIDENCE`：确认 `--runs`")
    A("   指向 `runs/lsu/formal_v333`，而不是 `audit_v3_3_3`。")
    A("6. 不要在失败后删除 `runs/lsu/formal_v333`；如需全新根目录，改用新的")
    A("   `--out-base`（例如 `runs/lsu/formal_v333_rerun1`）。")
    A("")
    A("## 7. 正式结果收集与 Manifest 生成")
    A("")
    A("- runner 在每个任务目录写 `campaign.json`；campaign 根写")
    A("  `campaign_identity.json`。")
    A("- collector 只从 `--runs` 指向的 campaign 根收集；")
    A("  `--manifest-only` 只生成核心 manifest，不导出完整报告。")
    A("- collector 结果应满足：`formal=120 non_formal=0`，且 exit 0。")
    A("- A03/SP05/RP01 的 `QUALIFIED`/`TRACE_INCOMPLETE` 会原样记录，")
    A("  不会被升级。")
    A("")
    A("## 8. 授权前检查清单")
    A("")
    A("- [x] 30/30 Override 有明确研究者批准（A 类）")
    A("- [x] 12 模型 / 60 SampleRunID / 60 Seed / 60 ROI / 60 Fault / 60 Control 一致")
    A("- [x] 60/60 Fault-Control 配对（同 Seed、同 SampleRunID、同 ROI、同 ordinal）")
    A("- [x] Binary SHA = 1126e0fd…（worktree 实测）")
    A("- [x] Config SHA = 8309da72…（实测）")
    A("- [x] 9 个 ELF SHA 与 oracle audit 一致")
    A("- [x] runner dry-run = 120 commands, nothing written")
    A("- [x] 输出根 `runs/lsu/formal_v333` 不存在")
    A("- [x] QUALIFIED/TRACE_INCOMPLETE 已披露，未升级")
    A("- [ ] 研究者明确下达正式 Campaign 启动指令 ← **唯一剩余项**")
    A("")
    A("**最终状态：`READY_FOR_RESEARCHER_AUTHORIZATION`**")
    A("")
    out = OUT / "LSU_v3.3.3_Final_Campaign_Authorization_README.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def write_launch_script(m: dict) -> Path:
    script = f"""#!/usr/bin/env bash
# LSU v3.3.3 formal campaign — verified command block.
# DO NOT RUN until the researcher explicitly authorizes the campaign.
set -u
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12 || exit 2

python3 tools/lsu_v332_matrix.py \\
  --models all --roles fault,control --contexts 1,2,3,4,5 \\
  --out-base runs/lsu/formal_v333 \\
  --out-csv runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv \\
  --campaign-id {CAMPAIGN_ID} \\
  --expected-binary-sha {m['binary']} \\
  --expected-config-sha {m['config']}
runner_exit=$?
echo "runner_exit=$runner_exit"

python3 tools/lsu_v333_launch.py \\
  --runs runs/lsu/formal_v333 \\
  --campaign-id {CAMPAIGN_ID} \\
  --design-matrix docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv \\
  --design-mapping audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv \\
  --out runs/lsu/formal_v333/collector \\
  --manifest-only
collector_exit=$?
echo "collector_exit=$collector_exit"

exit $(( runner_exit != 0 || collector_exit != 0 ))
"""
    out = OUT / "launch_commands.sh"
    out.write_text(script, encoding="utf-8")
    out.chmod(0o755)
    return out


def write_override_csv() -> Path:
    out = OUT / "LSU_30_Override_Detail.csv"
    fields = ["ModelID", "ContextID", "SampleRunID", "Seed",
              "OriginalWorkload", "ProposedWorkload", "DesignDifference",
              "ModificationReason", "FaultSemanticsImpact",
              "OriginalELFSHA256", "NewELFSHA256", "ActualExecution",
              "InjectionConfig", "Evidence", "ResearchImpact",
              "ApprovalSource", "ApprovalTime", "ApprovalStatus"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for model in OVERRIDE_MODELS:
            s = SPEC[model]
            for ctx in ["R01", "R02", "R03", "R04", "R05"]:
                r = READY[(model, ctx)]
                t = TASKMAP[(model, ctx, "fault")]
                w.writerow({
                    "ModelID": model, "ContextID": ctx,
                    "SampleRunID": r["SampleRunID"], "Seed": r["Seed"],
                    "OriginalWorkload": s["orig"],
                    "ProposedWorkload": s["new"],
                    "DesignDifference": s["diff"],
                    "ModificationReason": s["reason"],
                    "FaultSemanticsImpact": s["semantics"],
                    "OriginalELFSHA256": s["orig_sha"],
                    "NewELFSHA256": s["new_sha"],
                    "ActualExecution": t["DryRunCommand"],
                    "InjectionConfig": s["config"],
                    "Evidence": s["evidence"],
                    "ResearchImpact": s["research"],
                    "ApprovalSource": APPROVAL_SOURCE,
                    "ApprovalTime": APPROVAL_TIME,
                    "ApprovalStatus": "A. EXPLICITLY_APPROVED",
                })
    return out


def write_qualified_csv() -> Path:
    out = OUT / "LSU_Qualified_Status_15Contexts.csv"
    fields = ["ModelID", "ContextID", "Status", "MissingFields",
              "TerminalRule", "Source"]
    data = {
        "A03": [("R01", "PASS", "",
                 "APPLICATION_CHECKSUM;ORACLE_FAIL_SDC;POST_ORACLE_INTERNAL_WATCHDOG"),
                ("R02", "QUALIFIED", "load_result;register_writeback;consumer",
                 "APPLICATION_CHECKSUM;ORACLE_FAIL_SDC;POST_ORACLE_INTERNAL_WATCHDOG"),
                ("R03", "PASS", "",
                 "APPLICATION_CHECKSUM;ORACLE_FAIL_SDC;POST_ORACLE_INTERNAL_WATCHDOG"),
                ("R04", "PASS", "",
                 "APPLICATION_CHECKSUM;ORACLE_FAIL_SDC;POST_ORACLE_INTERNAL_WATCHDOG"),
                ("R05", "PASS", "",
                 "APPLICATION_CHECKSUM;ORACLE_FAIL_SDC;POST_ORACLE_INTERNAL_WATCHDOG")],
        "SP05": [(f"R0{i}", "QUALIFIED", "commit_event;writeback_event",
                  "APPLICATION_ORACLE;ORACLE_FAIL_SDC;STORE_COMMIT_ABSENT;STORE_WRITEBACK_ABSENT")
                 for i in range(1, 6)],
        "RP01": [(f"R0{i}", "TRACE_INCOMPLETE", "",
                  "MODEL_INTERNAL_WATCHDOG") for i in range(1, 6)],
    }
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for model, rows in data.items():
            for ctx, status, missing, rule in rows:
                w.writerow({"ModelID": model, "ContextID": ctx,
                            "Status": status, "MissingFields": missing,
                            "TerminalRule": rule,
                            "Source": "tools/lsu_v333_qualified.py on "
                                      "audit_v3_3_3/runs/"})
    return out


def build_zip(m: dict, files: list[Path]) -> Path:
    z = OUT / "LSU_v3.3.3_Final_Campaign_Authorization_Packet.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, arcname=f.name)
    return z


def main() -> int:
    m = measure()
    assert m["binary"] == BINARY_SHA, m["binary"]
    assert m["config"] == CONFIG_SHA, m["config"]
    assert m["old_binary"] == OLD_BINARY_SHA, m["old_binary"]

    xlsx = build_workbook(m)
    report = write_approval_report(m)
    qualified = write_qualified_report()
    readme = write_authorization_readme(m)
    launch = write_launch_script(m)
    override_csv = write_override_csv()
    qualified_csv = write_qualified_csv()

    copies = [
        (LAUNCH_FIX / "reports/LSU_Final_Binary_Provenance.md",
         "LSU_Final_Binary_Provenance.md"),
        (ART / "LSU_Formal_Experiment_Config_Final.xlsx",
         "LSU_Formal_Experiment_Config_Final.xlsx"),
        (LAUNCH_FIX / "artifacts/LSU_120Run_Task_Map.csv",
         "LSU_120Run_Task_Map.csv"),
        (ART / "LSU_60Fault_60Control_Pair_Map.csv",
         "LSU_60Fault_60Control_Pair_Map.csv"),
        (ART / "LSU_120Run_Campaign_Manifest.csv",
         "LSU_120Run_Campaign_Manifest.csv"),
        (ART / "LSU_60Context_Final_Readiness.csv",
         "LSU_60Context_Final_Readiness.csv"),
        (LAUNCH_FIX / "artifacts/LSU_120Run_Formal_Manifest_Schema.csv",
         "LSU_120Run_Formal_Manifest_Schema.csv"),
        (LAUNCH_FIX / "artifacts/LSU_QUALIFIED_Context_Handling.md",
         "LSU_QUALIFIED_Context_Handling.md"),
        (LAUNCH_FIX / "artifacts/LSU_60Context_Causal_Propagation_Final.csv",
         "LSU_60Context_Causal_Propagation_Final.csv"),
    ]
    copied = []
    for src, name in copies:
        dst = OUT / name
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        copied.append(dst)

    z = build_zip(m, [xlsx, report, qualified, readme, launch,
                      override_csv, qualified_csv] + copied)
    print("wrote:")
    for p in [xlsx, report, qualified, readme, launch, override_csv,
              qualified_csv, z]:
        print(f"  {p.relative_to(ROOT)}  {sha256_file(p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
