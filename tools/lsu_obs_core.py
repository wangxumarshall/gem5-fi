#!/usr/bin/env python3
"""lsu_obs_core.py — LSU L0-L5 观测链核心（OBS 计划 T2，用户指令 2026-10-12 二）。

纯函数库（无 gem5 依赖）：每样本 observation.json 的组装、校验与原子落盘。

层级语义（用户指令 2026-10-12 二.2-二.4 钉死；生产者/消费者契约见各工具头）：
  L0 注入漏斗与注入明细（stdout CHAOS_LSU_TRIGGER + <family>_injections.log）
  L1 µarch 影子快照比对（tools/micro_diff.py diff()，msnap=W2.4 契约）
  L2 提交流比对（tools/commit_diff.py compare()，ctrace=W2.1 契约，五分类）
  L3 传播证据：fanout 仅 PRF 可用（method=proxy）；非 PRF 家族 = unsupported
     + chain_complete=false（辅助 commit 足迹单列，绝不冒充传播证据）
  L4 首次检测/异常点与距 L0 延迟；detector 未接线（W6）→ detected_na=true，
     绝不以 detected_na 冒充 Detected/Contained
  L5 九分类 = 五类结局（lsu_l5_classify）+ 首检四类（Hardware RAS/OS/
     Application/None，总方针 §32"首检来源必须且只能是…中的一项"）

诚实规则（硬编码，违反即 violation/degradation，绝不静默）：
  * activated=0 → L1-L4 全部 "N/A(inactive_no_activation)"
  * Crash/Timeout 在首次错误提交前终止 → L2 "not_observed_before_crash/_timeout"
  * 截断 trace → truncated=true 且仅前缀可读证据（commit_diff 截断打捞契约）
  * identity/文件缺失/sha 不符 = fatal violation → 不得 finalize/COMPLETE

落盘协议：一切先写 <sample>.staging/，finalize_sample 校验后 os.rename 成
正式目录并写 COMPLETE；已有 COMPLETE 的目录只读核验（verify_complete），
绝不覆盖；无 COMPLETE 的残留目录 quarantine 改名保留证据。
"""
import fcntl
import gzip
import hashlib
import json
import os
import re
import shutil
import sys
import time
from contextlib import contextmanager
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))          # commit_diff / micro_diff
import commit_diff                       # noqa: E402  L2 五分类比对器（W2.2）
import micro_diff                        # noqa: E402  L1 影子快照比对器（W2.4）

SCHEMA = "lsu-observation-v1"
COMPLETE = "COMPLETE"
GZIP_MAGIC = b"\x1f\x8b"

# 九分类（五类结局 + 首检四类）。首检四类 = 总方针.md:32 的钉死枚举。
OUTCOME_CLASSES = ["Masked", "Detected/Contained", "SDC", "Crash", "Timeout"]
FIRST_DETECTION_SOURCES = ["Hardware RAS", "OS", "Application", "None"]

# fatal violation 的机器可判定标记（finalize 拒绝；其余 violation 亦记录但
# 同样阻断——observation.json 的 violations 非空即不落 COMPLETE，degradations
# 才是不阻断的诚实降级标记）
FATAL_VIOLATION_PREFIXES = ("identity", "file_missing", "sha_mismatch",
                            "observation_unparseable", "l5_error",
                            "funnel_missing")


# ---------------------------------------------------------------- basics
def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json_atomic(path, obj):
    path = str(path)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, path)


@contextmanager
def file_lock(path, timeout_s=7200.0, poll_s=5.0):
    """跨进程 advisory 锁（flock；Linux stdlib）。

    用途（Subagent-A 上抛，主负责人裁决后实现）：多个 obs driver **进程**
    共享同一 outdir_root/golden 时，per-key golden 生成必须跨进程互斥——
    进程内 threading.Lock 只防同进程 worker。超时抛 TimeoutError（绝不
    无声永久等待）。锁文件本身残留无害（advisory，flock 随 fd 关闭释放）。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(path, "a+")
    deadline = time.time() + timeout_s
    while True:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except OSError:
            if time.time() > deadline:
                fh.close()
                raise TimeoutError(f"file_lock 超时（{timeout_s}s）: {path}")
            time.sleep(poll_s)
    try:
        yield
    finally:
        try:
            fcntl.flock(fh, fcntl.LOCK_UN)
        finally:
            fh.close()


def baseline_key(ident):
    """no-fault golden 的缓存键：观测身份的规范化哈希。

    ident 必须含（调用方负责）：gem5_opt_sha256 / lsu_proxy_sha256 /
    workload / workload_sha256 / cpu / variant / maxinsts / obs_flags /
    env / checkpoint。任一变化 → 不同键 → 缓存 miss 重跑（身份漂移防御）。
    """
    blob = json.dumps(ident, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


def gz_probe(path):
    """通用 gzip 完整性探针：行数 / 是否截断 / 字节数。

    截断 = 解码流在 trailer 前结束（EOFError/BadGzipFile）或文件不可读。
    行数按完整行计（截断尾行不计）。绝不把截断报成完整。
    """
    p = Path(path)
    out = {"path": str(p), "bytes": 0, "rows": 0, "truncated": False,
           "readable": False, "error": None}
    if not p.exists():
        out["error"] = "file missing"
        return out
    out["bytes"] = p.stat().st_size
    if out["bytes"] == 0:
        out["error"] = "empty file"
        return out
    try:
        with open(p, "rb") as f:
            magic = f.read(2)
        fh = gzip.open(p, "rt", encoding="utf-8", errors="replace") \
            if magic == GZIP_MAGIC else open(p, "rt", encoding="utf-8",
                                             errors="replace")
        try:
            for raw in fh:
                out["rows"] += 1
        except (EOFError, OSError) as e:
            out["truncated"] = True
            out["error"] = f"truncated: {e}"
        finally:
            fh.close()
    except OSError as e:
        out["truncated"] = True
        out["error"] = f"unreadable: {e}"
        return out
    out["readable"] = True
    return out


# ---------------------------------------------------------------- L0
_FUNNEL_RE = re.compile(
    r"CHAOS_LSU_TRIGGER: .*?attempted=(\d+) eligible=(\d+) injected=(\d+)")
# 注入行契约（addrpath/lsqfwd 等家族共用日志格式，见 s319 实测行）：
#   Tick: 887040, Site: lsq_sendFragmentToTranslation, mode=low_bit_flip,
#   old_vaddr=0x7ffffefd00, new_vaddr=0x87ffffefd00, faults_injected: 1 ...
_INJ_RE = re.compile(
    r"Tick:\s*(\d+),\s*Site:\s*([^,]+),\s*mode=([^,]+)"
    r"(?:,\s*old_(\w+)=([^,]*),\s*new_(\w+)=([^,]*))?"
    r".*?faults_injected:\s*(\d+)")


def parse_l0(stdout_text, injlog_text, source_names=("stdout", "injections.log")):
    """L0：漏斗三元组 + 逐注入明细。

    abort 路径回退与 lsu_l5_classify 同口径：abort/abort-class 运行到不了
    exit callback，stdout 无 funnel 行 → injected 取注入日志 Site 行计数
    （attempted/eligible 诚实记 None，不猜）。两者皆无 → violation。
    """
    out = {"attempted": None, "eligible": None, "injected": None,
           "activated": None, "funnel_source": None,
           "injections": [], "violations": []}
    for line in (injlog_text or "").splitlines():
        if "Site: " not in line:
            continue
        im = _INJ_RE.search(line)
        if not im:
            out["violations"].append(
                f"injection_line_unparsed: {line[:120]}")
            continue
        tick, site, mode = int(im.group(1)), im.group(2).strip(), im.group(3)
        old_f, old_v, new_f, new_v = im.group(4), im.group(5), im.group(6), im.group(7)
        n = int(im.group(8))
        out["injections"].append({
            "tick": tick, "site": site, "mode": mode, "faults": n,
            "field": (f"{old_f}->{new_f}" if old_f else None),
            "old": old_v, "new": new_v,
            "dynamic_target": old_f.replace("_vaddr", "") if old_f else None,
            "raw": line,
        })
    m = _FUNNEL_RE.search(stdout_text or "")
    if m:
        out["attempted"], out["eligible"], out["injected"] = \
            (int(x) for x in m.groups())
        out["funnel_source"] = source_names[0]
        if out["injected"] and not out["injections"]:
            out["violations"].append(
                "injections_log_missing: funnel injected>0 但注入日志无 Site 行")
    elif out["injections"]:
        # abort 回退（lsu_l5_classify 同款）：injected = Site 行计数
        out["injected"] = len(out["injections"])
        out["funnel_source"] = f"injection-log-fallback({source_names[1]})"
    else:
        out["violations"].append(
            "funnel_missing: stdout 无 CHAOS_LSU_TRIGGER 行且注入日志无 Site 行")
    return out


# ---------------------------------------------------------------- L5 辅助
def first_detection_source(l5):
    """首检四类映射（总方针 §32 枚举；映射可复核，raw crash_kind 并记）。

    Masked/SDC/Timeout = 无检测（None）；guest crash = OS（内核陷入可见）；
    simulator_assert = 模拟器 DUE（非架构检测，按 None 记并加 note——
    audit() 本就将其单列于五类之外）；真 detector 接线后由此处替换。
    """
    outcome = (l5 or {}).get("outcome")
    note = None
    if outcome == "Crash" and (l5 or {}).get("crash_kind") == "guest_or_unknown":
        src = "OS"
        note = "guest crash observed via kernel trap; detector signal not wired"
    elif outcome == "Crash":
        src = "None"
        note = "simulator_assert DUE is not an architectural detection (audit 单列)"
    else:
        src = "None"
    if (l5 or {}).get("detected_na"):
        note = (note + "; " if note else "") + "no detector wired (W6): detected_na=true, never counted as Detected"
    return src, note


# ---------------------------------------------------------------- L1/L2
def build_l1(ref_path, fault_path, ipc_hide_pct=50.0, inactive=False):
    """L1：msnap 影子比对。inactive → N/A(inactive_no_activation)。"""
    if inactive:
        return {"status": "N/A(inactive_no_activation)",
                "reason": "activated=0（用户指令 2026-10-12 二.4）"}
    probe_ref, probe_run = gz_probe(ref_path), gz_probe(fault_path)
    entry = {
        "status": None, "ref": probe_ref, "fault": probe_run,
        "micro_diff": None,
    }
    try:
        res = micro_diff.diff(str(ref_path), str(fault_path), ipc_hide_pct)
    except Exception as e:  # micro_diff.ParseError/OSError → 诚实 error 态
        entry["status"] = "error"
        entry["error"] = f"micro_diff: {e}"
        return entry
    first_snap = res["rat_div_first_snap"]
    if first_snap is None:
        first_snap = res["occ_dev_first_snap"]
    if first_snap is None:
        first_snap = res["ipc_dev_first_snap"]
    entry["status"] = "complete"
    entry["micro_diff"] = {
        "no_divergence": res["no_divergence"],
        "first_divergence_snap_seq": first_snap,
        "rat_div_first_snap_by_class": res["rat_div_first_snap_by_class"],
        "rat_div_max_by_class": res["rat_div_max_by_class"],
        "occ_dev_first_snap": res["occ_dev_first_snap"],
        "ipc_dev_first_snap": res["ipc_dev_first_snap"],
        "max_ipc_dev_pct": res["max_ipc_dev_pct"],
        "snaps_aligned": res["snaps_aligned"],
        "hash_table_consistent": res["hash_table_consistent"],
        "run_truncated": res["run_truncated"],
        "ref_truncated": res["ref_truncated"],
    }
    if not res["hash_table_consistent"]:
        entry["status"] = "error"
        entry["error"] = "hash/table consistency violation (format drift)"
    return entry


def _tick_from_ctrace_line(raw):
    """ctrace 行的第 3 列是 tick（W2.1 契约：seq,tid,tick,pc,op,ndest,...）。"""
    try:
        return int(raw.split(",")[2])
    except (IndexError, ValueError):
        return None


def build_l2(ref_path, fault_path, l5=None, tick_tol=0, inactive=False):
    """L2：ctrace 五分类比对 + 首个错误提交。

    Crash/Timeout 在首次错误提交前终止 → status "not_observed_before_crash"
    /"not_observed_before_timeout"（用户指令 2026-10-12 二.4）；截断由
    commit_diff 的截断打捞契约如实标注（truncated_no_divergence_in_prefix
    绝不折叠成 no_divergence）。
    """
    if inactive:
        return {"status": "N/A(inactive_no_activation)",
                "reason": "activated=0（用户指令 2026-10-12 二.4）"}
    probe_ref, probe_run = gz_probe(ref_path), gz_probe(fault_path)
    entry = {"status": None, "ref": probe_ref, "fault": probe_run,
             "commit_diff": None}
    # 空 trace 前置守卫（2026-10-12 E2E s416 实测发现，必须在 compare 之前
    # ——commit_diff 会把空 run 误判为全量 instruction_flow_change）：
    # fault ctrace 0 完整行 + Crash/Timeout → not_observed_before_*。
    # 根因是 W2.1 生产者契约：ctrace 每 FLUSH_EVERY 行批量 gzflush，abort
    # 早于首个刷盘点 → 0 字节文件（指令实际已提交，只是未被刷出）；msnap
    # 每行 flush 不受影响。绝不把空 trace 判成 diverged/no_divergence。
    outcome_pre = (l5 or {}).get("outcome")
    if (probe_run.get("rows") == 0 and outcome_pre in ("Crash", "Timeout")):
        entry["status"] = ("not_observed_before_crash"
                           if outcome_pre == "Crash"
                           else "not_observed_before_timeout")
        entry["note"] = (f"空 trace（0 完整行"
                         f"{'，截断' if probe_run.get('truncated') else '，未截断'}）"
                         f"：abort 早于 ctrace 首个 FLUSH_EVERY 刷盘点"
                         f"（W2.1 生产者批量 flush 契约；run 实际提交数见 "
                         f"msnap/commit 计数）；诚实记 not_observed，"
                         f"绝不判 diverged")
        return entry
    try:
        res = commit_diff.compare(str(ref_path), str(fault_path), tick_tol)
    except commit_diff.TraceError as e:
        # 边界（真实可发生）：abort 早到 ctrace 连一条完整行都没有——
        # commit_diff 按钉死契约拒绝打捞空前缀。Crash/Timeout 样本此时
        # 诚实记 not_observed_before_*（0 行前缀证据在 probe 里），其余
        # outcome 记 error（空 trace 不是"无分歧"证据）。
        outcome = (l5 or {}).get("outcome")
        if (probe_run["truncated"] and probe_run["rows"] == 0
                and outcome in ("Crash", "Timeout")):
            entry["status"] = ("not_observed_before_crash" if outcome == "Crash"
                               else "not_observed_before_timeout")
            entry["commit_diff"] = None
            entry["note"] = (f"空前缀（0 完整行）+ {outcome}："
                             f"commit_diff 拒绝打捞空前缀（{e}）；"
                             f"截断证据见 fault probe")
            return entry
        entry["status"] = "error"
        entry["error"] = f"commit_diff: {e}"
        return entry
    fd = res.get("first_divergence")
    first_errant = None
    if fd:
        raw_line = fd.get("run_line") or fd.get("ref_line") or ""
        first_errant = {
            "seq": fd["seq"], "class": fd["class"], "class_zh": fd["class_zh"],
            "level": fd["level"], "detail": fd["detail"],
            "tick": _tick_from_ctrace_line(raw_line),
            "pc": (raw_line.split(",")[3] if len(raw_line.split(",")) > 3
                   else None),
        }
    outcome = (l5 or {}).get("outcome")
    terminated = res["verdict"] in ("no_divergence",
                                    "truncated_no_divergence_in_prefix") \
        and not fd
    if terminated and outcome == "Crash":
        status = "not_observed_before_crash"
    elif terminated and outcome == "Timeout":
        status = "not_observed_before_timeout"
    else:
        status = "complete"
    entry["status"] = status
    entry["commit_diff"] = {
        "verdict": res["verdict"],
        "primary_class": res["primary_class"],
        "latency_seq": res["latency_seq"],
        "first_errant_commit": first_errant,
        "total_divergence_points": res["total_divergence_points"],
        "divergence_counts": res["divergence_counts"],
        "tick_tol": res["tick_tol"],
        "aligned_pairs": res["aligned_pairs"],
        "ref_instructions": res["ref_instructions"],
        "run_instructions": res["run_instructions"],
        "ref_truncated": res["ref_truncated"],
        "run_truncated": res["run_truncated"],
        "aux": res["aux"],
    }
    return entry


def build_l3(family, l2, prf_only=("physreg",), method=None, inactive=False):
    """L3：传播证据。非 PRF 家族 = unsupported（用户指令 2026-10-12 二.3）。

    auxiliary_commit_footprint 是 L2 副产品（分歧点统计），单列呈现，
    明确不冒充 source-read/动态指令关联/传播 tag。
    """
    if inactive:
        return {"status": "N/A(inactive_no_activation)",
                "reason": "activated=0（用户指令 2026-10-12 二.4）"}
    cd = (l2 or {}).get("commit_diff") or {}
    aux = {
        "n_divergence_points": cd.get("total_divergence_points"),
        "divergence_counts": cd.get("divergence_counts"),
        "first_errant_seq": (cd.get("first_errant_commit") or {}).get("seq"),
        "note": "L2 commit 足迹副产品；不是传播证据（不冒充）",
    }
    if family in prf_only and method == "fanout_proxy":
        return {"status": "complete", "method": "proxy",
                "caveat": "fanout.py PRF proxy: upper-bound liveness window, "
                          "source reads not traced",
                "auxiliary_commit_footprint": aux}
    return {"status": "unsupported", "method": None,
            "reason": (f"非 PRF 家族（{family}）：source-read/动态指令关联/"
                       f"传播 tag 未实现（Phase B，OBS 计划 T9）；fanout 仅"
                       f"PRF 可用且为 proxy 口径"),
            "auxiliary_commit_footprint": aux}


def _msnap_tick_at(fault_msnap_path, snap_seq):
    """L4 用：取 fault msnap 某 snap_seq 的 tick（小文件二次遍历可接受）。"""
    try:
        snaps, _trunc = micro_diff.load_snaps(str(fault_msnap_path))
    except Exception:
        return None
    for r in snaps:
        if r["snap_seq"] == snap_seq:
            return r["tick"]
    return None


def build_l4(l0, l1, l2, l5, fault_msnap_path=None, inactive=False):
    """L4：首次检测/异常点与距 L0 延迟。detector 未接线 → detected_na。"""
    if inactive:
        return {"status": "N/A(inactive_no_activation)",
                "reason": "activated=0（用户指令 2026-10-12 二.4）"}
    out = {
        "status": "complete",
        "detector": "none_wired", "detected": False, "detected_na": True,
        "first_anomaly": None,
        "note": "LSU Detected/Contained 需真实 detector 信号（W6）；"
                "detected_na=true 绝不冒充 Detected（用户指令 2026-10-12 二.3）",
    }
    inj_tick = (l0["injections"][0]["tick"] if l0.get("injections") else None)
    candidates = []
    # BUG-6 修复（BUG-4 修复引入）：not_observed 条目的 commit_diff=None——
    # dict.get(k, {}) 的默认值只在键缺失时生效，键存在且为 None 时返回 None
    # → 必须 or {} 兜底（2026-10-12 恢复链 s416 重跑实测 AttributeError）
    l2f = ((l2 or {}).get("commit_diff") or {}).get("first_errant_commit")
    if l2f:
        candidates.append({"source": "L2", "tick": l2f.get("tick"),
                           "seq": l2f.get("seq")})
    l1d = ((l1 or {}).get("micro_diff") or {}).get("first_divergence_snap_seq")
    if l1d is not None:
        candidates.append({"source": "L1", "snap_seq": l1d,
                           "tick": (_msnap_tick_at(fault_msnap_path, l1d)
                                    if fault_msnap_path else None)})
    if candidates:
        # 首异常 = 最早 tick 的可观测分歧（tick 缺失时按来源优先级 L2>L1）
        c = sorted(candidates, key=lambda x: (x.get("tick") is None,
                                              x.get("tick") or 0))[0]
        if c.get("tick") is not None and inj_tick is not None:
            c["latency_ticks_from_first_injection"] = \
                max(0, c["tick"] - inj_tick)
        out["first_anomaly"] = c
    return out


# ---------------------------------------------------------------- assembly
def build_observation(identity, l0, l1, l2, l3, l4, l5, replay, files,
                      degradations=None):
    """组装 observation.json v1（含 chain_complete 判定与九分类）。"""
    violations = list(l0.get("violations") or [])
    for lv, entry in (("L1", l1), ("L2", l2)):
        if entry.get("status") == "error":
            violations.append(f"{lv}_error: {entry.get('error')}")
    if (l5 or {}).get("error"):
        violations.append(f"l5_error: {l5['error']}")
    src, src_note = first_detection_source(l5)
    l5n = dict(l5 or {})
    l5n["first_detection_source"] = src
    if src_note:
        l5n["first_detection_source_note"] = src_note
    # activated 口径以 L5 verdict 为准（lsu_l5_classify 运行级 activated）
    l0n = dict(l0)
    l0n["activated"] = (l5 or {}).get("activated")
    if l0n["activated"] is None:
        l0n["activated"] = l0n.get("injected")
        l0n["activated_source"] = "fallback=injected (L5 verdict 缺 activated)"
    obs = {
        "schema": SCHEMA,
        "identity": identity,
        "L0": l0n,
        "L1": l1,
        "L2": l2,
        "L3": l3,
        "L4": l4,
        "L5": l5n,
        "replay_determinism": replay,
        "violations": violations,
        "degradations": list(degradations or []),
        "files": files,
    }
    ok, reason = chain_complete(obs)
    obs["chain_complete"] = ok
    obs["chain_status_reason"] = reason
    return obs


def chain_complete(o):
    """完整链判定（OBS 计划 T2 钉死规则；返回 (bool, reason)）。

    activated=0：L0/L5 完整 + L1-L4 全 N/A(inactive) → True（无事可观测）。
    activated>0：L1-L4 全 complete（含 not_observed_before_crash/_timeout
    的诚实终态）→ 但 LSU 家族 L3=unsupported（Phase B 前）→ False。
    任何 violation / L5 无结论 / replay 未验证 → False。
    """
    if o.get("violations"):
        return False, "violations present: " + "; ".join(o["violations"][:3])
    l0, l5 = o.get("L0", {}), o.get("L5", {})
    if l0.get("injected") is None:
        return False, "L0 funnel missing"
    if (l5.get("outcome") in (None, "INCONCLUSIVE")):
        return False, "L5 无有效结局"
    rd = o.get("replay_determinism") or {}
    if not rd.get("verified"):
        return False, "replay determinism 未验证"
    if not l0.get("activated"):
        for lv in ("L1", "L2", "L3", "L4"):
            if o[lv].get("status") != "N/A(inactive_no_activation)":
                return False, f"activated=0 但 {lv} 非 N/A(inactive)"
        return True, "inactive 样本：L0/L5 完整，L1-L4 N/A(inactive)"
    ok_states = {"complete", "not_observed_before_crash",
                 "not_observed_before_timeout"}
    for lv in ("L1", "L2", "L4"):
        if o[lv].get("status") not in ok_states:
            return False, f"{lv} status={o[lv].get('status')}"
    if o["L3"].get("status") != "complete":
        return False, (f"L3 {o['L3'].get('status')}"
                       f"（{o['L3'].get('reason') or 'proxy 口径'}）——"
                       f"非 PRF 家族完整链待 Phase B 传播 tag")
    return True, "L0-L5 complete"


# ---------------------------------------------------------------- finalize
def quarantine(path):
    """无 COMPLETE 的残留目录改名保留（绝不删除/覆盖）。"""
    p = Path(path)
    if not p.exists():
        return None
    q = p.with_name(p.name + f".quarantine.{time.strftime('%Y%m%d_%H%M%S')}")
    os.rename(p, q)
    return q


def finalize_sample(staging, final):
    """staging → 校验 → 原子 rename → COMPLETE。

    校验：observation.json 可解析；files 全部存在且 sha256 复核一致；
    violations 为空（degradations 不阻断）。任一失败 → 不 rename，
    staging 原样保留返回 None。final 已存在且含 COMPLETE → 拒绝（调用方
    应先 verify_complete 跳过）；final 存在但无 COMPLETE → quarantine。
    """
    staging, final = Path(staging), Path(final)
    if (final / COMPLETE).exists():
        return None  # 调用方职责：COMPLETE 只读核验后跳过，绝不覆盖
    try:
        obs = json.loads((staging / "observation.json").read_text(
            encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise RuntimeError(f"finalize 拒绝：observation.json 不可解析: {e}")
    if obs.get("violations"):
        raise RuntimeError(
            f"finalize 拒绝：violations 非空: {obs['violations'][:3]}")
    for fe in obs.get("files", []):
        fp = Path(fe["path"])
        if not fp.is_absolute():
            fp = staging / fp
        if not fp.exists():
            raise RuntimeError(f"finalize 拒绝：文件缺失 {fe['path']}")
        if sha256_file(fp) != fe["sha256"]:
            raise RuntimeError(f"finalize 拒绝：sha 不符 {fe['path']}")
    if final.exists():
        quarantine(final)
    os.rename(staging, final)
    write_json_atomic(final / COMPLETE, {
        "finalized_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "schema": SCHEMA,
        "observation_sha256": sha256_file(final / "observation.json"),
        "git_commit": (obs.get("identity") or {}).get("git_commit"),
        "baseline_key": (obs.get("identity") or {}).get("baseline_key"),
    })
    return final


def verify_complete(d, ident):
    """COMPLETE 目录只读核验（绝不重跑/覆盖）。

    ident 只需包含要核验的键（如 git_commit/gem5_opt_sha256/baseline_key）。
    返回 (ok, reason)；ok=False 时调用方不得将该样本计为完成。
    """
    d = Path(d)
    if not (d / COMPLETE).exists():
        return False, "no COMPLETE marker"
    try:
        obs = json.loads((d / "observation.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return False, f"observation.json unreadable: {e}"
    ident_obs = obs.get("identity") or {}
    for k, v in (ident or {}).items():
        if ident_obs.get(k) != v:
            return False, (f"identity drift: {k} expected {v} got "
                           f"{ident_obs.get(k)}")
    files = obs.get("files") or []
    if not files:
        return False, "files list empty"
    spot = Path(files[0]["path"])
    if not spot.is_absolute():
        spot = d / spot
    if not spot.exists():
        return False, f"evidence file missing: {files[0]['path']}"
    if sha256_file(spot) != files[0]["sha256"]:
        return False, f"evidence sha mismatch: {files[0]['path']}"
    return True, "ok"
