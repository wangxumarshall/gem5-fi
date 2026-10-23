#!/usr/bin/env python3
"""test_lsu_r6_reconcile_realroot.py — L34 语义合流：7 条强制性质 + 真证据根复验。

背景（§二 强制证明 + 强制复验）：合并 `r6-gate` 的**净新语义**（D1/D5、D2、D3、D4
+ L29 接线）到集成分支基线后，必须在**真证据根** `LSU_CHAIN_EVIDENCE_ROOT=
/home/sdc/gem5-fi-ding` 上复验 7 条性质与 4 条逐 RunID 判决，而不是在**没有
`runs/lsu/` 的 worktree 根**上（L29 的 evaluated=45 即在那种根上算出，导致
`unproven`/`evidence_missing` 语义反向）。

诚实纪律：
- 真证据根缺 `runs/lsu/` 或 pilot 流 → 打印 `SKIPPED`（本套件对证据的判定依赖
  真实流；缺资产时如实跳过，绝不伪造通过）。
- 断言全部来自**真实命令输出/真实流**；合成夹具只用于钉死**规则谓词**，
  真流判决另行逐条引用。

用法：python3 tests/test_lsu_r6_reconcile_realroot.py   （退出码 0=全 PASS / SKIPPED）
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "tools"))

import lsu_prop_fields as P        # noqa: E402
import lsu_chain_check as CC       # noqa: E402
import lsu_ready_contract as RC    # noqa: E402

RD = Path(os.environ.get("LSU_CHAIN_EVIDENCE_ROOT", "/home/sdc/gem5-fi-ding"))
FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  PASS {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILED.append(name)


def _evts(lines):
    """Compact fixtures with a default per-fault linear parent chain."""
    out, last = [], {}
    for line in lines:
        explicit = "parent_event_id=" in line
        e = P.parse_line(line)
        if e is None:
            continue
        fid = e.get("fault_id", "")
        if not explicit:
            e["parent_event_id"] = last.get(fid, "")
        if e.get("event_id", ""):
            last[fid] = e["event_id"]
        out.append(e)
    return out


def _adm(events, run_id, containment=None, activated=1, rc=0):
    return CC.check_admission({"run_id": run_id, "activated": activated,
                               "events": events, "rc": rc,
                               "containment": containment})


# ── 真证据根先决条件 ────────────────────────────────────────────────────────
print(f"evidence_root = {RD}")
PILOT_DIR = RD / "runs/lsu/r6_tlb_pilot2"
if not PILOT_DIR.is_dir():
    print(f"SKIPPED [L34-reconcile] 真证据根缺 pilot 证据：{PILOT_DIR} 不存在"
          f"（设 LSU_CHAIN_EVIDENCE_ROOT 指向含 runs/lsu/ 的真根后重跑）")
    sys.exit(0)

# ── [1] 性质 1：chain_end 绝不独自证明 L5 (D1) ───────────────────────────────
print("[1] 性质 1：chain_end 生命周期标记绝不独自证明 L5")
only_end = _evts([
    "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=1",
    "PROP-EVT: kind=addr_form fault_id=1 event_id=1 tick=2",
    "PROP-EVT: kind=lsq_push fault_id=1 event_id=2 tick=3",
    "PROP-EVT: kind=tlb_translate fault_id=1 event_id=3 tick=4",
    "PROP-EVT: kind=resp fault_id=1 event_id=4 tick=5",
    "PROP-EVT: kind=taint_reg fault_id=1 event_id=5 tick=6",
    "PROP-EVT: kind=errant_commit fault_id=1 event_id=6 tick=7",
    "PROP-EVT: kind=chain_end fault_id=1 event_id=7 tick=8 "
    "outcome=errant_commit_seen detection_layer=None contained=0 corr=none",
])
f = CC.check_chain(only_end)["faults"]["1"]
check("chain_end 不占层 → L4->L5 missing", f["edges"]["L4->L5"] == "missing",
      str(f["edges"]))
check("chain_end-only 终局非 full", f["terminal"] != "full", f["terminal"])
r = _adm(only_end, "T00-F0-W0")
check("chain_end-only 不准入 + ready_by_chain_end_only 响亮",
      r["admitted"] is False
      and "ready_by_chain_end_only" in " ".join(r["violations"]),
      str(r["violations"]))

# ── [2] 性质 2：L5 须 detection_layer + outcome + 链关联 corr (D1) ───────────
print("[2] 性质 2：L5 须同时具备 detection_layer + outcome + 链关联 corr")
mk = lambda **kw: P.parse_line("PROP-EVT: kind=errant_commit fault_id=1 "
                               + " ".join(f"{k}={v}" for k, v in kw.items()))
check("三要素齐全 + 链关联 corr → 真实检测事件",
      CC._explicit_l5(mk(detection_layer="Software", outcome="SDC",
                         corr="taint_prop")) is True)
check("缺 detection_layer → 否", CC._explicit_l5(mk(outcome="SDC",
      corr="taint_prop")) is False)
check("缺 outcome（run_end）→ 否", CC._explicit_l5(mk(
      detection_layer="Software", outcome="run_end", corr="taint_prop")) is False)
check("缺链关联 corr（none）→ 否", CC._explicit_l5(mk(
      detection_layer="Software", outcome="SDC", corr="none")) is False)
check("生命周期 chain_end 即使载荷齐全也恒否（corr=none）",
      CC._explicit_l5(P.parse_line(
          "PROP-EVT: kind=chain_end fault_id=1 detection_layer=Software "
          "outcome=SDC corr=none")) is False)

# ── [3] 性质 3：边只能沿 parent_event_id 连续 DAG（断链不得补造） ────────────
print("[3] 性质 3：边须由 parent_event_id 连续 DAG 举证")
dangling = _evts([
    "PROP-EVT: kind=inj fault_id=2 event_id=0 tick=1",
    "PROP-EVT: kind=addr_form fault_id=2 event_id=1 tick=2 "
    "parent_event_id=0",
    "PROP-EVT: kind=lsq_push fault_id=2 event_id=2 tick=3 "
    "parent_event_id=998",           # 悬空父 → 祖先链在 L1 断开
    "PROP-EVT: kind=tlb_translate fault_id=2 event_id=3 tick=4 "
    "parent_event_id=2",
])
f3 = CC.check_chain(dangling)["faults"]["2"]
check("悬空 parent → L1->L2 missing（祖先不连续不得补造）",
      f3["edges"]["L1->L2"] == "missing", str(f3["edges"]))

# ── [4] 性质 4：不得跨请求 / 跨故障 / 跨样本拼接 (D3) ────────────────────────
print("[4] 性质 4：禁跨请求 / 跨故障 / 跨样本拼接")
# T 族 L0→L3 连续可证，但所选祖先上相邻见证携带不同 request_id（真实 T04 形状）
stitched = _evts([
    "PROP-EVT: kind=inj run_id=T00-F0-W0 fault_id=4 event_id=0 tick=1",
    "PROP-EVT: kind=tlb_lookup run_id=T00-F0-W0 fault_id=4 event_id=1 tick=2 "
    "dyn_inst_seq=7 request_id=7 va=1000 entry_index=1 field=post_lookup "
    "state_before=x state_after=y",
    "PROP-EVT: kind=tlb_translate_result run_id=T00-F0-W0 fault_id=4 "
    "event_id=2 tick=3 dyn_inst_seq=7 request_id=7 va=1000 pa=2000 "
    "field=ok detection_layer=Hardware outcome=Detected/Contained",
    "PROP-EVT: kind=resp run_id=T00-F0-W0 fault_id=4 event_id=3 tick=4 "
    "dyn_inst_seq=7 request_id=8",
])
r4 = _adm(stitched, "T00-F0-W0")
check("跨请求（所选祖先相邻见证 req 7→8）被拒（D3 整条祖先口径）",
      "cross_request_edge" in " ".join(r4["violations"]),
      str(r4["violations"]))
# 跨故障：另一 fault_id 的同层事件不得互证
cross_fault = _evts([
    "PROP-EVT: kind=inj fault_id=5 event_id=0 tick=1",
    "PROP-EVT: kind=addr_form fault_id=5 event_id=1 tick=2",
    "PROP-EVT: kind=resp fault_id=6 event_id=2 tick=3 parent_event_id=1",
])
f4b = CC.check_chain(cross_fault)["faults"]["5"]
check("跨故障（fault 6 事件不得替 fault 5 补 L2）",
      f4b["edges"]["L1->L2"] == "missing", str(f4b["edges"]))
# 同一 RunID 的两个**样本**（seed1/seed2）联合读入 → 契约按样本逐一评估，
# 任一未准入即整体不准入（绝不把多样本缝成一条链）。
tmp = Path(tempfile.mkdtemp(prefix="l34recon_"))
p1, p2 = tmp / "seed1", tmp / "seed2"
p1.write_text("PROP-EVT: kind=inj fault_id=1 event_id=0 tick=1\n"
              "PROP-EVT: kind=addr_form fault_id=1 event_id=1 tick=2\n",
              encoding="utf-8")
p2.write_text("PROP-EVT: kind=unknown_probe fault_id=1 event_id=0 tick=1\n",
              encoding="utf-8")
pilots = {f"T99-F0-W0-seed{i}": {"path": str(p), "faults": 1}
          for i, p in ((1, p1), (2, p2))}
ca = RC.chain_admission("T99-F0-W0", pilots=pilots, evidence_root="/")
check("多样本：任一未准入 → 整体不准入（不跨样本拼接）",
      ca["admitted"] is False and ca["n_samples"] == 2,
      str({k: ca[k] for k in ("admitted", "n_samples", "evaluated")}))
check("未准入样本响亮给因（violations 非空）", bool(ca["violations"]))

# ── [5] 性质 5：cache_access 不得冒充族专属 L1 (D4) ─────────────────────────
print("[5] 性质 5：cache_access 不得冒充非 cache 族的 L1")
fake = _evts([
    "PROP-EVT: kind=inj run_id=L04-F0-W5 fault_id=1 event_id=0 tick=1",
    "PROP-EVT: kind=cache_access run_id=L04-F0-W5 fault_id=1 event_id=1 "
    "tick=2 va=1000 pa=2000",
])
r5 = _adm(fake, "L04-F0-W5")
check("LQ 族 cache_access 冒充 L1 → cache_access_faked_l1",
      r5["admitted"] is False
      and "cache_access_faked_l1" in " ".join(r5["violations"]),
      str(r5["violations"]))
tlb_fake = _evts([
    "PROP-EVT: kind=inj run_id=T01-F0-W4 fault_id=1 event_id=0 tick=1",
    "PROP-EVT: kind=cache_access run_id=T01-F0-W4 fault_id=1 event_id=1 tick=2 "
    "va=1000 pa=2000",
])
r5b = _adm(tlb_fake, "T01-F0-W4")
check("TLB 族 cache_access 冒充 → tlb_l1_faked_by_cache_access",
      r5b["admitted"] is False
      and "tlb_l1_faked_by_cache_access" in " ".join(r5b["violations"]),
      str(r5b["violations"]))
check("族由 RunID 前缀判定（T→tlb / L→lq / C→cache）",
      CC._family_of(only_end) == "generic"
      and CC._family_of([{"run_id": "C01-F0-W6"}]) == "cache"
      and CC._family_of([{"run_id": "T01-F0-W4"}]) == "tlb"
      and CC._family_of([{"run_id": "L01-F0-W5"}]) == "lq")

# ── [6] 性质 6：显式 containment 可准入，但仅当后续层无更深传播 (D2) ────────
print("[6] 性质 6：显式 containment 准入须以「后续层确无更深传播」+「流已收口」为前提")
def _cont(run, extra=()):
    return _evts([
        f"PROP-EVT: kind=inj run_id={run} fault_id=1 event_id=0 tick=1",
        f"PROP-EVT: kind=tlb_lookup run_id={run} fault_id=1 event_id=1 tick=2 "
        "dyn_inst_seq=7 request_id=7 va=1000 entry_index=1 field=post_lookup "
        "state_before=x state_after=y",
        f"PROP-EVT: kind=tlb_translate_result run_id={run} fault_id=1 "
        "event_id=2 tick=3 dyn_inst_seq=7 request_id=7 va=1000 pa=2000 "
        "field=walk_refill_lost detection_layer=L2 contained=1 "
        # [R6-FIXB] 真实检测事件须带**链关联 corr**（真实 T05/T08 的
        # tlb_translate_result 为 corr=seq_primary/origin）——缺 corr 的事件
        # 不构成 L5/含住证据。
        "outcome=translation_blocked corr=origin",
        # [R6-FIXB] 含住主张只对**完整收口**的流成立：正常退出 ⇒ 退出回调
        # 发射 chain_end（abort 截断样本没有，见 §[8] T08 实况）。
        f"PROP-EVT: kind=chain_end run_id={run} fault_id=1 event_id=3 tick=4 "
        "outcome=run_end detection_layer=None contained=0 corr=none",
        *extra,
    ])
ok = _cont("T77-F0-W4")
b = CC.containment_from_events(ok, "T77-F0-W4")
check("显式含住证据 → 束合法 (layer=L2, na=L3..L5)",
      bool(b) and b["layer"] == "L2" and b["na_layers"] == ["L3", "L4", "L5"],
      str(b))
check("显式含住 → admitted=True",
      _adm(ok, "T77-F0-W4", containment=b)["admitted"] is True)
deep = _cont("T78-F0-W4", ["PROP-EVT: kind=resp run_id=T78-F0-W4 fault_id=1 "
                           "event_id=3 tick=4 dyn_inst_seq=7 request_id=7"])
check("含住层之后仍有更深见证 → 主张不成立（束=None）",
      CC.containment_from_events(deep, "T78-F0-W4") is None)
check("无证据 → 不猜测（束=None）",
      CC.containment_from_events(_evts([
          "PROP-EVT: kind=inj fault_id=1 event_id=0 tick=1"]), "N1") is None)

# ── [7] 性质 7：evidence_root 必须指向真证据根 ──────────────────────────────
print("[7] 性质 7：evidence_root 必须指向真证据根（worktree 根会产出反向计数）")
check("真根含 runs/lsu/（准入性先决）", (RD / "runs/lsu").is_dir())
check("--evidence-root 显式优先", RC._evidence_root("/explicit/root")
      == Path("/explicit/root"))
os.environ["LSU_CHAIN_EVIDENCE_ROOT"] = str(RD)
check("env LSU_CHAIN_EVIDENCE_ROOT 生效",
      RC._evidence_root(None) == RD)
del os.environ["LSU_CHAIN_EVIDENCE_ROOT"]
check("缺省回落 REPO（= 本 worktree）", RC._evidence_root(None) == RC.REPO)
wt_root = RC.REPO
wt_has_pilots = (wt_root / "runs/lsu/r6_tlb_pilot2").is_dir()
print(f"  INFO worktree 根 {wt_root} 含 pilot 流 = {wt_has_pilots}")

# ── [8] 强制复验：4 条逐 RunID 判决（真根、真流） ───────────────────────────
print("[8] 强制复验（LSU_CHAIN_EVIDENCE_ROOT=%s）" % RD)
PILOTS = RC._load_pilots(RC.PILOT_EVIDENCE)
CASES = {
    "T04-F0-W4": "runs/lsu/r6_tlb_pilot2/T04-F0-W4/seed1/prop_evt.txt.gz",
    "T08-F0-W4": "runs/lsu/r6_tlb_C_T08-F0-W4/T08-F0-W4/seed1/"
                 "prop_evt.txt.gz",
    "T05-F0-W4": "runs/lsu/r6_tlb_pilot2/T05-F0-W4/seed1/prop_evt.txt.gz",
    "T01-F0-W4": "runs/lsu/r6_tlb_F_T01-F0-W4/T01-F0-W4/seed1/"
                 "prop_evt.txt.gz",
    "T10-F0-W4": "runs/lsu/r6_tlb_F_T10-F0-W4/T10-F0-W4/seed1/"
                 "prop_evt.txt.gz",
    "L01-F0-W5": "runs/lsu/r6_lq_L01-F0-W5_s6/L01-F0-W5/seed1/"
                 "prop_evt.txt.gz",
}
verdicts = {}
for rid, rel in CASES.items():
    p = RD / rel
    check(f"{rid} 真流在盘上（非「no file」）", p.is_file(), str(p))
    if not p.is_file():
        continue
    ev, _tr = P.read_events(p)
    verdicts[rid] = _adm(ev, rid,
                         containment=CC.containment_from_events(ev, rid))
    print(f"  INFO {rid}: admitted={verdicts[rid]['admitted']} "
          f"terminal={verdicts[rid]['terminal']} n_ev={len(ev)} "
          f"violations={verdicts[rid]['violations'][:1]}")

check("T04-F0-W4 因跨请求拼接被拒（拒绝理由须点名 cross_request_edge）",
      verdicts.get("T04-F0-W4", {}).get("admitted") is False
      and "cross_request_edge"
      in " ".join(verdicts["T04-F0-W4"]["violations"]),
      str(verdicts.get("T04-F0-W4", {}).get("violations")))
_ev04 = P.read_events(RD / CASES["T04-F0-W4"])[0]
_ch04 = [e for e in _ev04 if e.get("fault_id") == "1"]
_fam04 = CC._family_of(_ch04)
t04_brk = CC._ancestry_request_breaks(_ch04, _fam04,
                                      CC._best_ordered_path(_ch04, _fam04))
_ex = [(a.get("kind"), a.get("request_id"), b.get("kind"),
        b.get("request_id")) for a, b in t04_brk[:2]]
print(f"  INFO T04 祖先跨请求首例 = {_ex}")
check("T04 祖先上跨请求对计数 > 0（真实证据，非空报）", len(t04_brk) > 0,
      str(len(t04_brk)))
check("T04 首例为同层 resp 跨请求（D3 点名形状）",
      any(x[0] == "resp" and x[2] == "resp" and x[1] != x[3] for x in _ex),
      str(_ex))
# [R6-FIXB] 缺陷 #5 修正：T08 的 prop_evt 流是**截断**的（gzip EOF）。含住是对
# "该层之后无传播"的断言，只在**完整收口**（退出回调发射 chain_end）的流上可证
# ——截断流里"更深的层未出现"只反映截断，不反映含住。故 T08 **不得**再凭
# containment 准入（旧口径判 admitted=True 是缺陷）。
_ev08, _tr08 = P.read_events(RD / CASES["T08-F0-W4"])
check("T08-F0-W4 真流确为截断（read_events → truncated=True）",
      _tr08 is True, str(_tr08))
check("T08-F0-W4 截断流不得因 containment 准入（缺陷 #5 修正）",
      verdicts.get("T08-F0-W4", {}).get("admitted") is False
      and CC.containment_from_events(_ev08, "T08-F0-W4") is None,
      str(verdicts.get("T08-F0-W4")))
check("T08-F0-W4 拒绝理由响亮点名 containment_on_unclosed_stream",
      "containment_on_unclosed_stream"
      in " ".join(verdicts.get("T08-F0-W4", {}).get("violations", [])),
      str(verdicts.get("T08-F0-W4", {}).get("violations")))
# [R6-FIXB] 反证（不过度收紧）：T05-F0-W4 是**完整**运行的真实含住证据
# （truncated=False + chain_end 收口 + tlb_translate_result dl=L2 contained=1
# field=effective_pa_unchanged，其后无更深见证）——合法含住仍必须可准入。
_ev05, _tr05 = P.read_events(RD / CASES["T05-F0-W4"])
_b05 = CC.containment_from_events(_ev05, "T05-F0-W4")
check("T05-F0-W4 真流为完整运行（truncated=False）", _tr05 is False,
      str(_tr05))
check("T05-F0-W4 合法含住仍可准入（real-evidence containment 不过度收紧）",
      verdicts.get("T05-F0-W4", {}).get("admitted") is True
      and bool(_b05) and _b05["layer"] == "L2"
      and _b05["na_layers"] == ["L3", "L4", "L5"],
      str(verdicts.get("T05-F0-W4")))
check("T05-F0-W4 准入依据是真实检测事件（非生命周期链末）",
      _b05["metrics"]["L2"]["kind"] == "tlb_translate_result", str(_b05))
for rid in ("T01-F0-W4", "T10-F0-W4"):
    check(f"{rid} 未被链末/更深层见证误准入",
          verdicts.get(rid, {}).get("admitted") is False,
          str(verdicts.get(rid)))
    check(f"{rid} 未准入理由点名 no_closed_chain_and_no_containment",
          "no_closed_chain_and_no_containment"
          in " ".join(verdicts.get(rid, {}).get("violations", [])),
          str(verdicts.get(rid, {}).get("violations")))
# 注册表可解析性：真根下这些 RunID 不得判成「无文件」
for rid in ("T04-F0-W4", "T08-F0-W4", "T05-F0-W4", "T01-F0-W4", "T10-F0-W4",
            "S10-F5-W9"):
    ca = RC.chain_admission(rid, pilots=PILOTS, evidence_root=str(RD))
    check(f"注册表 {rid} 在真根下 evaluated>0（不再是「无文件」）",
          ca["evaluated"] > 0, str({k: ca[k] for k in
                                    ("n_samples", "evaluated", "note")}))
ca_l01 = RC.chain_admission("L01-F0-W5", pilots=PILOTS, evidence_root=str(RD))
if ca_l01["evaluated"] == 0:
    print(f"  INFO L01-F0-W5 注册表缺陷（pilot_evidence.json 无该 RunID 条目）: "
          f"{ca_l01['note']} —— 流在盘上（见上），门禁在流级已评估并如实拒绝，"
          f"仅注册表未登记；补登记属注册表 owner 的 1 行数据修复。")

# ── [9] 325 行计数须在真根上计算 ───────────────────────────────────────────
print("[9] 325 行计数（真证据根）")
with tempfile.TemporaryDirectory(prefix="l34contract_") as td:
    out = Path(td) / "ready_contract.json"
    env = dict(os.environ, LSU_CHAIN_EVIDENCE_ROOT=str(RD))
    cp = subprocess.run([sys.executable, str(REPO / "tools" /
                                             "lsu_ready_contract.py"),
                         "--out", str(out)],
                        capture_output=True, text=True, cwd=str(REPO), env=env)
    # 退出码语义：GO→0 / 否则 1（325 全阻塞 ⇒ 必须 1，非静默 0）
    check("契约 rc 与裁决一致（NO-GO ⇒ rc=1）",
          cp.returncode == 1 and out.is_file(), f"rc={cp.returncode}")
    doc = json.loads(out.read_text(encoding="utf-8"))
    rows = doc["entries"]
    cg = doc["chain_gate"]
    st = doc["status"]
    print(f"  INFO total={doc['total']} status={st} "
          f"blocked_by_category={doc['blocked_by_category']}")
    print(f"  INFO chain_gate={ {k: v for k, v in cg.items() if k != 'rule'} }")
    check("total == 325", doc["total"] == 325, str(doc["total"]))
    check("计数自洽 total == READY+PARTIAL+BLOCKED", doc["self_consistent"])
    check("门禁对每一行评估（recorded==rows_total==325）",
          cg["recorded"] == 325 and cg["rows_total"] == 325, str(cg))
    check("chain_gate.evidence_root == 真证据根",
          cg["evidence_root"] == str(RD), cg["evidence_root"])
    check("READY == 0（无链证据即不准入；硬门生效）",
          st.get("READY", 0) == 0 and st.get("BLOCKED", 0) == 325
          and st.get("PARTIAL", 0) == 0, str(st))
    check("链已准入的行全部仍被上游独立阻塞（准入≠解锁）",
          cg["admitted"] == len(cg["blocked_upstream_admitted"])
          and all((r.get("chain") or {}).get("admitted") is not True
                  or r["status"] == "BLOCKED" for r in rows),
          str(cg["blocked_upstream_admitted"]))
    # [R6-FIXB] 旧值 = [T06-F0-W4, T08-F0-W4]：两行都是**截断流**上的含住准入
    # （缺陷 #5）。收口后二者一律不准入；当前 325 行里唯一凭真实含住准入的是
    # T05-F0-W4（完整运行：truncated=False + chain_end 收口），且它同样被上游
    # FS-INFRA 独立阻塞 —— 准入 ≠ 解锁这一性质不变。
    check("准入行 = T05-F0-W4（完整运行的显式含住；T06/T08 截断流不再准入）",
          sorted(cg["blocked_upstream_admitted"]) == ["T05-F0-W4"]
          and cg["admitted"] == 1
          and "T06-F0-W4" not in cg["blocked_upstream_admitted"]
          and "T08-F0-W4" not in cg["blocked_upstream_admitted"],
          str(cg["blocked_upstream_admitted"]))
    check("已评估=64 / 未准入(有样本)=44 / 无样本=197",
          cg["evaluated"] == 64 and cg["unproven"] == 44
          and cg["evidence_missing"] == 197
          and doc["blocked_by_category"].get("CHAIN-EVIDENCE-MISSING") == 197
          and doc["blocked_by_category"].get("CHAIN-UNPROVEN") == 44,
          str({k: cg[k] for k in ("evaluated", "unproven", "evidence_missing")}))
    check("上游独立阻塞 84 行分类不变（RULING6/FS-INFRA24/MODE-UNIMPL3/"
          "UNRESOLVED4/FS-MULTICORE35/LICENSE12）",
          all(doc["blocked_by_category"].get(k) == v for k, v in
              (("RULING", 6), ("FS-INFRA", 24), ("MODE-UNIMPL", 3),
               ("UNRESOLVED", 4), ("FS-MULTICORE", 35), ("LICENSE", 12))),
          str(doc["blocked_by_category"]))
    # 任一 admitted 行都不得因链准入而变 READY（variant 2 containment ≠ 全局准入）
    check("无任何行因 containment 而 READY",
          not any(r["status"] == "READY" for r in rows))
    check("无行因 activated/RC0 判 READY（禁入门槛）",
          all(r["category"] != "OK" for r in rows))

print()
if FAILED:
    print(f"FAILURES: {FAILED}")
    sys.exit(1)
print("ALL PASS")
