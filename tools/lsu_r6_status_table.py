#!/usr/bin/env python3
"""lsu_r6_status_table.py — [MDSPEC][R6-FIXD2] 逐 RunID 权威状态表（两轴表达）。

规格：`docs/gem5-fi/lsu/mdspec/R6-PILOT-ADMISSION-SPEC.md`（§4 状态表 / §5 门禁）
    + `docs/gem5-fi/lsu/mdspec/R6-RULINGS-20261023.md`（**裁决 B — 两轴表达**，权威）。
本工具产出**唯一权威**的逐 RunID 表（JSON + Markdown），每行给出**两条正交轴**
（互不覆盖），并打印两轴计数 + `blocker_code` 分类。

**轴 A `evidence_state`（磁盘实际观测进度，仅五值，永不为 BLOCKED）**：

  NOT_RUN           权威根下**没有任何流** —— 未测量。**绝不被契约 BLOCKED 顶掉**
                    （这正是旧表"325 全短路 BLOCKED ⇒ NOT_RUN 永不出现"的修复）。
  EVIDENCE_MISSING  证据被**声称**（pilot_evidence.json 列了该 RunID/seed）但文件
                    在权威根下缺失/不可读（悬空引用）——与"从未运行"不同。
  TRUNCATED         有流，但 gzip 读不到 EOF 或 stats.txt 缺失/0 字节（流不完整）。
  UNPROVEN          全流完整且有激活，但链**未过** `check_admission`（或完整流内
                    根本没有激活）——"测了但证不出来"。
  PILOT_READY       全部激活样本准入 + 无截断 + 无 Unknown + 无 oversized
                    （**纯磁盘/链事实**，与 eligibility 无关；见裁决 B 要求 1）。

**轴 B `eligibility`（是否被规格/基础设施/模式能力阻塞）**：

  RUNNABLE          无上游独立阻塞。
  BLOCKED           有上游独立阻塞（FS-INFRA / RULING / LICENSE / FS-MULTICORE /
                    MODE-UNIMPL / UNRESOLVED …，取自契约的**上游**判定
                    upstream_status/category，而非其链门禁后的收尾 status）。
                    另给出 `blocker_code`（分类）与 `blocker_detail`（说明）。

**轴 C `policy_state`（R6-FREQPOLICY 频率政策，第三条正交只读轴）**：

  NORMAL            F0-F5 常规单元格（required_seeds=3，进统计）。
  STRESS_ONLY       代表性 F6（每个 F6 model 一个；required_seeds=1，不进统计）。
  STRESS_REDUNDANT  冗余 F6（被代表覆盖；required_seeds=0，不调度、不进统计）。
  UNKNOWN           overlay 缺失/不可读，或 RunID 不在权威 325 `entries` 内
                    （legacy CSV-only F6 等）——"不可治理"，响亮降级，
                    **绝不静默等于 NORMAL**。

  唯一裁决源 = `tools/lsu_freq_policy.py` + `R6-FREQUENCY-POLICY.json`（本工具
  绝不重推导政策规则；查法与 ready_contract 同一 `_load_policy_index` 习语）。
  政策**只报告、不裁决**：`policy_state` 在两轴判定全部完成后最后写入，绝不
  改写 evidence_state/eligibility/legacy state，反之亦然。政策不要求的单元格
  （如 STRESS_REDUNDANT 无流）如实记 NOT_RUN，**绝不**因此记
  EVIDENCE_MISSING/TRUNCATED/failure——磁盘事实照旧，政策轴负责解释
  "为何无需跑"。

两轴**并存**（裁决 B 硬性要求）：
  * 有 blocker 的行，`evidence_state` **仍如实显示**其磁盘事实，同时
    `eligibility=BLOCKED` —— 两者并存，不是二选一。
  * **不得**因 contract 有 blocker 就把磁盘事实短路成 BLOCKED。
  * 权威汇总**同时**报告：各 `evidence_state` 数量 · `RUNNABLE`/`BLOCKED` 数量 ·
    `PILOT_READY` 数量 · `blocker_code` 分类数量；并显式声明
    "`BLOCKED=0` 只表示该维度无 blocker，**不代表**全部实验可运行/已通过"。
  * 正式实验准入依据**仍是 `PILOT_READY`**（evidence PILOT_READY ∧ eligibility
    RUNNABLE），不以 `BLOCKED=0` 代替。

遗留字段（**非权威，仅为向后兼容保留**）：`state`（旧一轴六态），其 BLOCKED 仅当
"本可 PILOT_READY 却被上游阻塞"时出现；下游不得再用它做权威汇报。`STATES`
常量（六值）同样为遗留兼容。

诚实纪律（逐条实现）：
  * 磁盘上没有流 ⇒ NOT_RUN，**不等于** BLOCKED，也**不得**解释成"无传播/Masked"。
  * 截断流上**不得**认证（与 Lane B 的 containment 口径一致）。
  * 链判定**调用真检查器** `lsu_chain_check.check_admission`（本工具不自写规则）。

evidence root（**与契约同一个、且被明确记录**）：`--evidence-root`，缺省
`$LSU_CHAIN_EVIDENCE_ROOT`，再缺省仓库根；流自 `<root>/runs/lsu` 读取。
若与 `ready_contract.json` 的 `chain_gate.evidence_root` 不一致，**响亮**告警并记录。

用法：
  LSU_CHAIN_EVIDENCE_ROOT=/home/sdc/gem5-fi-ding \
    python3 tools/lsu_r6_status_table.py [--out-json ...] [--out-md ...]
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sys
import time
import zlib
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import lsu_chain_check as C            # noqa: E402  真检查器（唯一链/准入判定源）
import lsu_prop_fields as P            # noqa: E402  真 PROP-EVT 解析器
# [R6-FREQPOLICY] 频率政策 overlay（可选依赖）：第三条只读正交轴 policy_state
# 的唯一裁决源，绝不参与 evidence_state/eligibility 裁决（政策排除 ≠ 技术
# BLOCKED）。与 ready_contract/lsu_campaign 同一习语：模块/JSON 缺失 ⇒
# 该轴整体降级 UNKNOWN（响亮），绝不崩、绝不静默等于 NORMAL。
try:
    import lsu_freq_policy as FPOL     # noqa: E402
except Exception:                      # pragma: no cover - overlay optional
    FPOL = None

# 轴 A：磁盘事实（仅五值，永不为 BLOCKED）
EVIDENCE_STATES = ("NOT_RUN", "EVIDENCE_MISSING", "TRUNCATED", "UNPROVEN",
                   "PILOT_READY")
# 轴 B：是否被阻塞（附 blocker_code / blocker_detail）
ELIGIBILITIES = ("RUNNABLE", "BLOCKED")
# 轴 C：频率政策（R6-FREQPOLICY，只读正交；来源唯一 = lsu_freq_policy overlay，
# 绝不在此重推导）。UNKNOWN 不在三元组内：它是 overlay 缺失/RunID 不受管时的
# 响亮降级值（"不可治理"），绝不与 NORMAL 等同。
POLICY_STATES = ("NORMAL", "STRESS_ONLY", "STRESS_REDUNDANT")
POLICY_DEGRADED = "UNKNOWN"
# 遗留一轴六态常量（非权威，仅向后兼容；BLOCKED 为旧口径的合成值）
STATES = EVIDENCE_STATES + ("BLOCKED",)
BLOCKER_CODE_ZERO_NOTE = (
    "BLOCKED=0 只表示该统计维度中没有 blocker，不代表全部实验可运行或已通过；"
    "正式准入依据仍是 PILOT_READY（evidence_state=PILOT_READY 且 eligibility=RUNNABLE）。"
)
POLICY_AXIS_NOTE = (
    "policy_state 是第三条只读正交轴（唯一裁决源 lsu_freq_policy + "
    "R6-FREQUENCY-POLICY.json）：STRESS_ONLY/STRESS_REDUNDANT 表示政策不要求"
    "更多种子，绝不因此被计为 failure/BLOCKED/EVIDENCE_MISSING——"
    "evidence_state/eligibility 仍如实报告磁盘与上游事实；UNKNOWN=overlay "
    "缺失或 RunID 不在权威 325 entries（不可治理），响亮降级，绝不静默等于 NORMAL。"
)
DEFAULT_POLICY_OVERLAY = REPO / "docs/gem5-fi/lsu/mdspec/R6-FREQUENCY-POLICY.json"

DEFAULT_CONTRACT = REPO / "docs/gem5-fi/lsu/mdspec/ready_contract.json"
DEFAULT_PILOTS = REPO / "docs/gem5-fi/lsu/mdspec/pilot_evidence.json"
_RUNID_RE = re.compile(r"^[A-Z]\d{2}-F\d+-W\d+$")
_STREAM_NAMES = ("prop_evt.txt.gz", "prop_evt.txt")
EVENT_CAP = 200000        # 真检查器超线性；超大流不跑检查器 ⇒ 记 UNPROVEN（响亮）


def resolve_evidence_root(arg=None):
    """(root, source) —— 明确记录证据根来源，绝不隐式。"""
    if arg:
        return Path(arg), "--evidence-root"
    env = os.environ.get("LSU_CHAIN_EVIDENCE_ROOT")
    if env:
        return Path(env), "$LSU_CHAIN_EVIDENCE_ROOT"
    return REPO, "default(repo root)"


def _load_policy_index(path=None):
    """[R6-FREQPOLICY] run_id -> run_policy 索引（唯一来源 lsu_freq_policy；
    与 ready_contract 同一查法：仅权威 `entries`，legacy CSV-only F6 不在内）。

    模块/JSON 缺失或损坏 → None：政策轴整体降级 UNKNOWN（policy_states
    响亮计数），evidence_state/eligibility 不受任何影响 —— 政策不是技术门禁。
    """
    if FPOL is None:
        return None
    try:
        pol = FPOL.load_policy(path) if path is not None else FPOL.load_policy()
    except Exception:
        return None
    return {e["run_id"]: e["run_policy"] for e in pol.get("entries", [])}


# ------------------------------------------------------------------ discovery
class Sample:
    __slots__ = ("path", "seed_dir", "seed", "run_id", "events", "event_count",
                 "truncated", "stats_ok", "activated", "has_unknown",
                 "admission", "oversized")

    def __init__(self, path, seed_dir, seed, run_id):
        self.path = path
        self.seed_dir = seed_dir
        self.seed = seed
        self.run_id = run_id
        self.events = []
        self.event_count = 0
        self.truncated = True
        self.stats_ok = False
        self.activated = False
        self.has_unknown = False
        self.admission = None
        self.oversized = False

    @property
    def complete(self):
        return (not self.truncated) and self.stats_ok

    def read(self):
        """单遍流式读取（[R6-FREQPOLICY] 再生成前提，**非规则变更**）。

        旧实现经 P.read_events 把**整条流**驻留内存：2026-10-24 起 runs/lsu
        出现 6 条 1.3–2.8 GB 级 w1b 巨流（T04-F0/F2/F6-W4 seed2），旧实现被
        OOM-kill（exit 137），权威表无法再生成。本方法改为单遍流式解析，
        判定口径与旧实现**逐位等价**：
          * 同一 parse_line（CONSUMER-SUMMARY 行不以 PROP-EVT 开头 ⇒ 同被
            parse_line 判 None；read_events 本就丢弃 summary 行，且
            parse/validate_consumer_summary 均为全函数、无 raise 路径）；
          * truncated ≡ read_events 的 (EOFError,BadGzipFile,OSError,
            zlib.error) 截断标记 ∨ _gzip_eof 的 EOF 复核——两者是对同一
            文件的同一整遍迭代、同一异常集合（UnicodeDecodeError 在
            errors="replace" 下不可触发），故单遍异常标记即两者的析取
            （省去旧实现的两遍解压）。zlib.error（deflate 载荷损坏，
            **非 OSError 子类**）显式入集 = 恢复 4dd4e8b0 之前旧外层
            except Exception 的截断韧性：腐蚀流 ⇒ 诚实 TRUNCATED（保留
            已解析前缀），绝不 exit-1 杀死全根再生成；
          * activated/has_unknown 用与旧 any() **完全相同**的谓词逐事件累计；
          * 事件列表仅在未超 EVENT_CAP 时保留（超限样本本就不进
            check_admission——oversized——事件无需驻留）；EVENT_CAP 判定改用
            event_count，adjudicate 其余逻辑分毫不变。
        """
        events, trunc = [], False
        activated = has_unknown = oversized = False
        opener = gzip.open if self.path.suffix == ".gz" else open
        try:
            with opener(self.path, "rt", errors="replace") as f:
                for line in f:
                    if oversized:
                        # 已超 EVENT_CAP：检查器不会再跑，事件无需驻留；只继续
                        # 扫激活/Unknown/截断。子串预筛是保守超集（大小写不
                        # 敏感化后再判），命中才走 parse_line 精判。
                        if ("inj" not in line
                                and "unknown" not in line.lower()):
                            continue
                    evt = P.parse_line(line)
                    if evt is None:
                        continue
                    fid = str(evt.get("fault_id", ""))
                    if fid not in ("", "0"):
                        if evt.get("kind") == "inj":
                            activated = True
                        if (str(evt.get("evidence_status", "")).strip().lower()
                                == "unknown" or evt.get("kind") == "unknown"):
                            has_unknown = True
                    if not oversized:
                        events.append(evt)
                        if len(events) > EVENT_CAP:
                            oversized = True
                            events = []   # 超大流：不进检查器，事件不再驻留
        # [R6-FREQPOLICY-fix] zlib.error（deflate 载荷损坏，Error -3）
        # **不是 OSError 子类**，必须显式列出：gzip 头完好但压缩数据不可
        # 解码同样是 "读不到 EOF" 的磁盘事实 ⇒ 诚实 TRUNCATED（保留已解析
        # 前缀），绝不令一条腐蚀流以 exit 1 杀死 ~35 分钟的全根再生成
        # （write_outputs 在最后，崩溃 = 全部输出丢失）。刻意保持显式异常
        # 元组而非恢复宽泛 except Exception——解析/判定逻辑 bug 必须响亮
        # 崩溃，不得被静默吞成截断。
        except (EOFError, gzip.BadGzipFile, OSError, UnicodeDecodeError,
                zlib.error):
            trunc = True
        self.events = events
        self.event_count = (EVENT_CAP + 1) if oversized else len(events)
        self.truncated = trunc
        self.stats_ok = _stats_ok(self.seed_dir)
        self.activated = activated
        self.has_unknown = has_unknown
        return self


def _stats_ok(seed_dir: Path) -> bool:
    st = seed_dir / "stats.txt"
    try:
        return st.is_file() and st.stat().st_size > 0
    except OSError:
        return False


def _runid_of(path_dir: Path, known: set) -> str | None:
    for anc in [path_dir] + list(path_dir.parents):
        name = anc.name
        if name in known:
            return name
        if _RUNID_RE.fullmatch(name):
            return name
        for tok in re.split(r"[_]", name):
            if _RUNID_RE.fullmatch(tok):
                return tok
    return None


def discover(runs_root: Path, known: set) -> dict:
    by_run: dict = {}
    if not runs_root.is_dir():
        return by_run
    for name in _STREAM_NAMES:
        for p in runs_root.rglob(name):
            if name == "prop_evt.txt" and (p.parent / "prop_evt.txt.gz").exists():
                continue
            seed_dir = p.parent
            rid = _runid_of(seed_dir, known)
            if rid is None:
                continue
            m = re.fullmatch(r"seed(\d+)", seed_dir.name)
            if m is None and seed_dir.name != rid:
                continue                      # 嵌套调试产物不计为样本
            seed = m.group(1) if m else "?"
            by_run.setdefault(rid, []).append(
                Sample(p, seed_dir, seed, rid).read())
    return by_run


# ------------------------------------------------------------------ adjudication
def _claim_paths(pilots: dict, runid: str, root: Path, runs_root: Path):
    """registry 中该 RunID 及其 seed 样本**声称**的证据路径。

    返回 (claimed, missing, outside)：
      missing = 权威根下**不存在**者（悬空引用 ⇒ EVIDENCE_MISSING）；
      outside = 存在但**不在权威 runs 根之内**者（草稿/他处 worktree 的产物，
                不构成权威证据 ⇒ 该行仍按磁盘事实记 NOT_RUN，但如实披露）。
    """
    seed_re = re.compile(rf"^{re.escape(runid)}-seed\d+$")
    claimed, missing, outside = 0, [], []
    rr = Path(runs_root).resolve()
    for k, v in pilots.items():
        if k != runid and not seed_re.match(k):
            continue
        for rel in (v.get("paths") or ([v["path"]] if v.get("path") else [])):
            claimed += 1
            p = (root / rel)
            if not p.exists():
                missing.append(rel)
            else:
                try:
                    p.resolve().relative_to(rr)
                except ValueError:
                    outside.append(rel)
    return claimed, missing, outside


def _unknown_present(samples) -> bool:
    return any(s.has_unknown for s in samples if s.activated)


def adjudicate(runid, samples, entry, pilots, root, runs_root, policy_idx=None):
    contract_up = (entry or {}).get("upstream_status")
    upstream_cat = (entry or {}).get("upstream_category") or ""
    # [R6-FIXD] 上游阻塞取自契约的**上游**判定（链门禁之前），绝不取它的收尾
    # status —— 否则"契约判 325 全 BLOCKED（实为链门禁降级）"会把每一行短路。
    upstream_blocked = (contract_up == "BLOCKED")
    row = {
        "run_id": runid,
        "unit": (entry or {}).get("unit", ""),
        "model": (entry or {}).get("model", ""),
        "freq": (entry or {}).get("freq", ""),
        "contract_status": (entry or {}).get("status", ""),
        "contract_upstream_status": contract_up,
        "upstream_block": upstream_cat if upstream_blocked else "NONE",
        "upstream_blocked": upstream_blocked,
    }
    samples = sorted(samples, key=lambda s: s.seed)
    complete = [s for s in samples if s.complete]
    truncated = [s for s in samples if not s.complete]
    activated = [s for s in samples if s.activated]

    # 真检查器：逐激活样本 check_admission（超大流不跑，记 oversized）
    for s in activated:
        if s.event_count > EVENT_CAP:
            s.oversized = True
            continue
        s.admission = C.check_admission({
            "run_id": runid, "activated": 1, "events": s.events, "rc": 0,
            "containment": C.containment_from_events(s.events, runid),
        })

    admitted = [s for s in activated
                if (s.admission or {}).get("admitted") is True]
    refused = [s for s in activated if s not in admitted]
    claimed, missing, outside = _claim_paths(pilots, runid, root, runs_root)

    cond = {
        "not_run": len(samples) == 0,
        "evidence_missing": (len(samples) == 0 and claimed > 0 and missing),
        "truncated": bool(truncated) and bool(samples),
        "unproven": (bool(complete) and (not activated or bool(refused))),
        "pilot_ready": (bool(activated) and not refused and not truncated
                        and not _unknown_present(activated)
                        and not any(s.oversized for s in activated)),
        "blocked": upstream_blocked,
    }
    # ---- 轴 A：磁盘事实（五值，**永不为 BLOCKED**）——纯磁盘/链优先级 ----
    if not samples:
        ev_state = "EVIDENCE_MISSING" if cond["evidence_missing"] else "NOT_RUN"
    elif truncated:
        ev_state = "TRUNCATED"
    elif not activated or refused:
        ev_state = "UNPROVEN"
    elif cond["pilot_ready"]:
        ev_state = "PILOT_READY"
    else:
        ev_state = "UNPROVEN"          # oversized / Unknown 等：证不出来
    # ---- 轴 B：是否被上游独立阻塞（与轴 A 正交，绝不覆盖轴 A）----
    eligibility = "BLOCKED" if upstream_blocked else "RUNNABLE"
    blocker_code = (upstream_cat.strip() or "BLOCKED") if upstream_blocked else "NONE"
    if upstream_blocked:
        blocker_detail = (
            f"上游独立阻塞 {blocker_code}（契约 upstream_status="
            f"{contract_up!r} / upstream_category={upstream_cat!r}）；"
            f"磁盘事实仍如实记为 evidence_state={ev_state}（两轴并存，"
            f"不因 blocker 短路）")
    else:
        blocker_detail = "无上游独立阻塞"
    # ---- 遗留单轴（非权威，仅向后兼容）：BLOCKED 仅当旧口径下会压制 PILOT_READY ----
    legacy_blocked = (bool(samples) and not truncated and bool(activated)
                      and not refused and upstream_blocked)
    state = "BLOCKED" if legacy_blocked else ev_state

    row["conditions"] = cond
    row["evidence_state"] = ev_state
    row["eligibility"] = eligibility
    row["blocker_code"] = blocker_code
    row["blocker_detail"] = blocker_detail
    row["state"] = state          # 遗留：非权威
    row.update({
        "samples": len(samples),
        "complete_streams": len(complete),
        "truncated_streams": len(truncated),
        "activated_samples": len(activated),
        "admitted_samples": len(admitted),
        "unknown_samples": sum(1 for s in activated if s.has_unknown),
        "claimed_evidence": claimed,
        "missing_evidence": missing,
        "claimed_outside_runs_root": outside,
        "result_dir": ";".join(sorted({str(s.seed_dir.parent) for s in samples})),
        "failure_reason": _reason(ev_state, eligibility, blocker_code, cond,
                                  refused, samples, upstream_cat, missing,
                                  outside),
    })
    # ---- 轴 C：频率政策（R6-FREQPOLICY，只读正交）——**最后**写入，绝不参与
    # 上面任何判定（政策排除 ≠ 技术 BLOCKED）；overlay 缺失/RunID 不在权威
    # 325 entries（legacy CSV-only F6 等）⇒ UNKNOWN（不可治理，响亮），
    # 绝不静默等于 NORMAL。
    row["policy_state"] = (policy_idx or {}).get(runid, POLICY_DEGRADED)
    return row


def _reason(state, eligibility, blocker_code, cond, refused, samples,
            upstream_cat, missing, outside=()):
    if state == "NOT_RUN":
        base = "not measured: 权威根下无任何 prop_evt 流（未执行）——非 BLOCKED"
        if outside:
            base += (f"；另有 {len(outside)} 条 pilot 路径存在但**不在权威 runs 根内**"
                     f"（草稿/他处产物，不构成权威证据，如 {outside[0]}）")
        return base
    if state == "EVIDENCE_MISSING":
        return ("证据被声称但文件在权威根下缺失：%s（悬空引用）"
                % ", ".join(missing[:3]))
    if state == "TRUNCATED":
        n = sum(1 for s in samples if not s.complete)
        return f"{n}/{len(samples)} 流截断或不完整（stats.txt 缺失/0 字节或 gzip 无 EOF）"
    if state == "UNPROVEN":
        if not any(s.activated for s in samples):
            base = "完整流内无注入（fault_id≠0 的 inj）——未激活，未测量；非 Masked"
        else:
            base = (f"{len(refused)} 个激活样本未过 check_admission"
                    f"（含 oversized/Unknown）")
    elif state == "PILOT_READY":
        base = "全部激活样本准入，无截断，无 Unknown"
    else:
        base = f"evidence_state={state}"
    # 轴 B 单独表达：无论磁盘事实如何，blocker 都如实附记（两轴并存）
    if eligibility == "BLOCKED":
        base += (f"；且被上游独立阻塞 {blocker_code or upstream_cat or 'BLOCKED'}"
                 f"——规格/基础设施阻塞不可解除，绝不计为可准入 PILOT_READY")
    return base


# ---------------------------------------------------------------------- build
def build(contract_path, pilots_path, root, runs_root, policy=None):
    """policy: run_id -> run_policy 索引。[R6-FREQPOLICY] 轴 C **只报告**：
    None = 自动加载默认 overlay；{} = 显式无 overlay（每行 policy_state=
    UNKNOWN）；dict = 直接使用。无论取值如何，evidence_state/eligibility/
    legacy state 的判定路径分毫不变 —— 政策排除 ≠ 技术 BLOCKED。"""
    contract = {}
    if contract_path and Path(contract_path).is_file():
        contract = json.loads(Path(contract_path).read_text(encoding="utf-8"))
    entries = {e["run_id"]: e for e in contract.get("entries", [])}
    pilots = {}
    if pilots_path and Path(pilots_path).is_file():
        pilots = json.loads(Path(pilots_path).read_text(encoding="utf-8")).get(
            "pilots", {}) or {}
    if policy is None:
        policy = _load_policy_index()
    pol_idx = policy or {}
    # 权威集合 = 契约的 RunID（矩阵口径，325 项）；证据里出现的**非矩阵**
    # RunID 单独披露（extra_evidence_runids），不混进权威表。
    known = set(entries)
    by_run = discover(Path(runs_root), known)
    extra = sorted(set(by_run) - known)
    rows = [adjudicate(rid, by_run.get(rid, []), entries.get(rid), pilots,
                       Path(root), Path(runs_root), pol_idx)
            for rid in sorted(known)]
    gate_root = ((contract.get("chain_gate") or {}).get("evidence_root"))
    meta = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "spec": "docs/gem5-fi/lsu/mdspec/R6-PILOT-ADMISSION-SPEC.md",
        "contract": str(contract_path),
        "evidence_root": str(root),
        "evidence_root_source": "unspecified(build)",
        "runs_root": str(runs_root),
        "contract_chain_gate_evidence_root": gate_root,
        "evidence_root_matches_contract": (
            gate_root is None or
            Path(gate_root).resolve() == Path(root).resolve()),
        "total_runids": len(rows),
        "extra_evidence_runids": extra,
        # [R6-FREQPOLICY] 轴 C 元数据：来源路径 + 是否真加载（False ⇒ 全体
        # UNKNOWN，不可治理，绝不静默当作 NORMAL）
        "policy_overlay": str(DEFAULT_POLICY_OVERLAY),
        "policy_overlay_loaded": bool(pol_idx),
    }
    return meta, rows, contract


def summarize(meta, rows, contract):
    counts = Counter(r["state"] for r in rows)          # 遗留单轴
    ev_counts = Counter(r["evidence_state"] for r in rows)   # 轴 A
    el_counts = Counter(r["eligibility"] for r in rows)      # 轴 B
    pol_counts = Counter(r["policy_state"] for r in rows)    # 轴 C
    blk_counts = Counter(r["blocker_code"] for r in rows
                         if r["eligibility"] == "BLOCKED")
    # 正式准入依据 = PILOT_READY（evidence PILOT_READY ∧ eligibility RUNNABLE）
    admissible = sorted(r["run_id"] for r in rows
                        if r["evidence_state"] == "PILOT_READY"
                        and r["eligibility"] == "RUNNABLE")
    # [R6-FREQPOLICY] 轴 C 汇总：UNKNOWN 仅在出现时列出（overlay 缺失/不受管
    # ⇒ 响亮，绝不静默）。与逐行 policy_state 同源 tally（Σ == total）。
    pol_states = {s: pol_counts.get(s, 0) for s in POLICY_STATES}
    if pol_counts.get(POLICY_DEGRADED):
        pol_states[POLICY_DEGRADED] = pol_counts[POLICY_DEGRADED]
    return {
        "states": {s: counts.get(s, 0) for s in STATES},     # 遗留（非权威）
        "evidence_states": {s: ev_counts.get(s, 0) for s in EVIDENCE_STATES},
        "eligibility": {e: el_counts.get(e, 0) for e in ELIGIBILITIES},
        "policy_states": pol_states,
        "policy_axis_note": POLICY_AXIS_NOTE,
        "pilot_ready": {
            "count": len(admissible),
            "run_ids": admissible,
            "basis": "evidence_state=PILOT_READY ∧ eligibility=RUNNABLE",
        },
        "evidence_pilot_ready_count": ev_counts.get("PILOT_READY", 0),
        "blocker_codes": dict(sorted(blk_counts.items())),
        "blocker_code_zero_note": BLOCKER_CODE_ZERO_NOTE,
        "streams": {
            "total": sum(r["samples"] for r in rows),
            "complete": sum(r["complete_streams"] for r in rows),
            "truncated": sum(r["truncated_streams"] for r in rows),
            "activated": sum(r["activated_samples"] for r in rows),
            "admitted": sum(r["admitted_samples"] for r in rows),
        },
        "runids_without_stream": sum(1 for r in rows if r["samples"] == 0),
        "evidence_root": meta["evidence_root"],
        "pilot_ready_list": admissible,               # 遗留别名（=准入清单）
        "upstream_blocked": sorted(r["run_id"] for r in rows
                                   if r["upstream_blocked"]),
        "extra_evidence_runids": meta.get("extra_evidence_runids", []),
    }


MD_COLS = ["run_id", "unit", "model", "evidence_state", "eligibility",
           "policy_state", "blocker_code", "state", "contract_upstream_status",
           "upstream_block", "samples", "activated_samples", "admitted_samples",
           "failure_reason"]


def write_outputs(out_json, out_md, meta, rows, sumry):
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(out_json).write_text(json.dumps(
        {"meta": meta, "summary": sumry, "rows": rows},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    L = ["# R6 逐 RunID 权威状态表（两轴 + 政策轴：evidence_state × eligibility × policy_state）",
         "",
         f"- 生成时间：{meta['generated_at']}",
         f"- 证据根：`{meta['evidence_root']}`（runs 根 `{meta['runs_root']}`）",
         f"- 契约 `chain_gate.evidence_root`：`{meta['contract_chain_gate_evidence_root']}`"
         f" —— 一致：{'是' if meta['evidence_root_matches_contract'] else '否（响亮告警）'}",
         f"- 总 RunID：{meta['total_runids']}",
         f"- 政策 overlay：`{meta.get('policy_overlay', '')}`"
         f" —— 已加载：{'是' if meta.get('policy_overlay_loaded') else '否（轴 C 全体 UNKNOWN，不可治理）'}",
         "",
         "## 轴 A — evidence_state 计数（磁盘事实，仅五值，永不为 BLOCKED）", ""]
    for s in EVIDENCE_STATES:
        L.append(f"- {s}: {sumry['evidence_states'][s]}")
    L += ["", "## 轴 B — eligibility 计数（是否被上游独立阻塞）", ""]
    for e in ELIGIBILITIES:
        L.append(f"- {e}: {sumry['eligibility'][e]}")
    L += ["", "## 轴 C — policy_state 计数（R6-FREQPOLICY 频率政策，只读正交）", ""]
    for s, n in sumry["policy_states"].items():
        L.append(f"- {s}: {n}")
    L += ["", f"> {sumry['policy_axis_note']}", "",
          "## blocker_code 分类计数", ""]
    for code, n in (sumry["blocker_codes"] or {}).items():
        L.append(f"- {code}: {n}")
    if not sumry["blocker_codes"]:
        L.append("- （无，BLOCKED=0）")
    L += ["",
          f"> {sumry['blocker_code_zero_note']}",
          "",
          f"- 正式准入（PILOT_READY ∧ RUNNABLE）：{sumry['pilot_ready']['count']} 个 "
          f"{', '.join(sumry['pilot_ready']['run_ids']) or '（无）'}",
          f"- 其中 evidence_state=PILOT_READY 的行数（纯磁盘事实）："
          f"{sumry['evidence_pilot_ready_count']}",
          f"- 遗留单轴 `state` 计数（**非权威**）："
          + " ".join(f"{s}={sumry['states'][s]}" for s in STATES)]
    st = sumry["streams"]
    L += ["",
          f"- 流：total={st['total']} complete={st['complete']} "
          f"truncated={st['truncated']} activated={st['activated']} "
          f"admitted={st['admitted']}",
          f"- 无任何流的 RunID（从未执行 ⇒ NOT_RUN）："
          f"{sumry['runids_without_stream']}",
          f"- 上游阻塞（eligibility=BLOCKED）：{len(sumry['upstream_blocked'])} 个 "
          f"{', '.join(sumry['upstream_blocked']) or '（无）'}",
          "", "## 权威表（两轴并存 + 政策只读轴）", "",
          "| " + " | ".join(MD_COLS) + " |",
          "|" + "|".join("---" for _ in MD_COLS) + "|"]
    for r in rows:
        cells = []
        for k in MD_COLS:
            v = r.get(k, "")
            if isinstance(v, bool):
                v = "yes" if v else "no"
            cells.append(str(v).replace("|", "\\|").replace("\n", " ")[:200])
        L.append("| " + " | ".join(cells) + " |")
    Path(out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(out_md).write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence-root", default=None,
                    help="证据根（默认 $LSU_CHAIN_EVIDENCE_ROOT 或仓库根）")
    ap.add_argument("--runs-root", default=None,
                    help="流根（默认 <evidence-root>/runs/lsu）")
    ap.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    ap.add_argument("--pilots", default=str(DEFAULT_PILOTS))
    ap.add_argument("--out-json", default=str(
        REPO / "docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.json"))
    ap.add_argument("--out-md", default=str(
        REPO / "docs/gem5-fi/lsu/mdspec/R6-STATUS-TABLE.md"))
    a = ap.parse_args()

    root, src = resolve_evidence_root(a.evidence_root)
    runs_root = Path(a.runs_root) if a.runs_root else Path(root) / "runs/lsu"
    meta, rows, contract = build(a.contract, a.pilots, root, runs_root)
    meta["evidence_root_source"] = src
    sumry = summarize(meta, rows, contract)
    write_outputs(a.out_json, a.out_md, meta, rows, sumry)

    print(f"[r6-status] evidence_root={meta['evidence_root']} (source={src}) "
          f"matches_contract={meta['evidence_root_matches_contract']}")
    print(f"[r6-status] total_runids={meta['total_runids']}")
    print("[r6-status] axis A evidence_state（磁盘事实，永不为 BLOCKED）:")
    for s in EVIDENCE_STATES:
        print(f"[r6-status]   {s}: {sumry['evidence_states'][s]}")
    print("[r6-status] axis B eligibility:")
    for e in ELIGIBILITIES:
        print(f"[r6-status]   {e}: {sumry['eligibility'][e]}")
    print("[r6-status] axis C policy_state（R6-FREQPOLICY，只读正交）:")
    for s, n in sumry["policy_states"].items():
        print(f"[r6-status]   {s}: {n}")
    if sumry["policy_states"].get(POLICY_DEGRADED):
        print("[r6-status] WARNING: policy overlay 缺失/不可读或存在不受管 "
              "RunID —— 对应行 policy_state=UNKNOWN（不可治理），绝不等于 NORMAL")
    print("[r6-status] blocker_code 分类:")
    if sumry["blocker_codes"]:
        for code, n in sumry["blocker_codes"].items():
            print(f"[r6-status]   {code}: {n}")
    else:
        print("[r6-status]   （无，BLOCKED=0）")
    print(f"[r6-status] 正式准入 PILOT_READY(∧RUNNABLE): "
          f"{sumry['pilot_ready']['count']} 个 "
          f"{', '.join(sumry['pilot_ready']['run_ids']) or '（无）'}")
    print(f"[r6-status] NOTE: {sumry['blocker_code_zero_note']}")
    st = sumry["streams"]
    print(f"[r6-status] streams total={st['total']} complete={st['complete']} "
          f"truncated={st['truncated']} activated={st['activated']} "
          f"admitted={st['admitted']} runids_without_stream="
          f"{sumry['runids_without_stream']}")
    if not meta["evidence_root_matches_contract"]:
        print("[r6-status] WARNING: 状态表证据根与契约 chain_gate.evidence_root "
              "不一致 —— 两者必须同源（否则两张表描述不同证据）")
    print(f"[r6-status] wrote {a.out_json} and {a.out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
