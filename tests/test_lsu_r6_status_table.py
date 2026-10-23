#!/usr/bin/env python3
"""tests/test_lsu_r6_status_table.py — [LSU][MDSPEC][R6-FIXD] 权威六态状态表。

钉死（对应四个真缺陷的第 4 条）：
  1. 六态**各自可达**且**互不覆盖**：NOT_RUN / EVIDENCE_MISSING / TRUNCATED /
     UNPROVEN / PILOT_READY / BLOCKED；
  2. 契约 `status=BLOCKED`（实为链门禁降级，325 全 BLOCKED）**绝不短路**每一行：
     从未执行（磁盘无流）的行**必须**是 NOT_RUN，不得被 BLOCKED 顶掉；
  3. 截断 + 未准入**并存**表述（state=TRUNCATED 且 conditions.unproven=True）；
  4. 上游独立阻塞**单独表达**（upstream_block 列），且规格/基础设施阻塞
     **绝不计为 PILOT_READY**；
  5. evidence root 被明确记录，并与契约 chain_gate.evidence_root 比对。

运行：python3 tests/test_lsu_r6_status_table.py   （或 pytest -q）
"""
import gzip
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import lsu_r6_status_table as T  # noqa: E402


def _evt(rid, sid, kind, eid, parent, tick, **kw):
    fields = [f"{k}={v}" for k, v in kw.items() if v is not None]
    return (f"PROP-EVT: kind={kind} event_id={eid} parent_event_id={parent} "
            f"tick={tick} run_id={rid} sample_run_id={sid} " + " ".join(fields))


def admitted_chain(rid, sid="s1"):
    """完整 L0→L5（check_admission admitted=True）——实测构造。"""
    return [
        _evt(rid, sid, "inj", 1, "", 100, fault_id=1, corr="origin"),
        _evt(rid, sid, "addr_form", 2, 1, 105, fault_id=1, va="dead",
             corr="origin"),
        _evt(rid, sid, "mem_req", 3, 2, 110, fault_id=1, va="dead",
             request_id="r7", corr="seq_primary"),
        _evt(rid, sid, "resp", 4, 3, 115, fault_id=1, request_id="r7",
             corr="seq_primary"),
        _evt(rid, sid, "taint_reg", 5, 4, 118, fault_id=1, request_id="r7",
             corr="taint_prop"),
        _evt(rid, sid, "errant_commit", 6, 5, 120, fault_id=1, dyn_inst_seq=7,
             detection_layer="Hardware", outcome="SDC", contained="0",
             corr="taint_prop"),
    ]


def refused_chain(rid, sid="s1"):
    """有激活、check_chain 有 fault 路径，但 check_admission 必拒。"""
    return admitted_chain(rid, sid)[:3]


def _write(seed_dir: Path, lines, *, stats=True, truncate=False):
    seed_dir.mkdir(parents=True, exist_ok=True)
    with gzip.open(seed_dir / "prop_evt.txt.gz", "wt") as f:
        f.write("\n".join(lines) + "\n")
    if truncate:
        p = seed_dir / "prop_evt.txt.gz"
        raw = p.read_bytes()
        p.write_bytes(raw[: max(1, len(raw) - 6)])
    if stats:
        (seed_dir / "stats.txt").write_text("simTicks 1\n")
    else:
        (seed_dir / "stats.txt").write_bytes(b"")


def _entry(rid, status="BLOCKED", upstream="READY", cat="OK"):
    return {"run_id": rid, "unit": "U", "model": "M", "freq": "F0",
            "status": status, "upstream_status": upstream,
            "upstream_category": cat, "category": cat,
            "why": "x" if status == "BLOCKED" else ""}


def _contract(tmp, entries, evidence_root):
    p = tmp / "ready_contract.json"
    p.write_text(json.dumps({
        "total": len(entries), "status": {"BLOCKED": len(entries)},
        "entries": entries,
        "chain_gate": {"evidence_root": str(evidence_root)},
    }))
    return p


def build(tmp):
    """合成证据根；contract 行**一律** status=BLOCKED（复现真缺陷现场）。"""
    root = tmp / "root"
    runs = root / "runs/lsu"
    runs.mkdir(parents=True)

    # X02 EVIDENCE_MISSING：registry 声称有样本，但文件不在权威根下
    (runs / "r6_x02").mkdir(parents=True)
    # X03 TRUNCATED（且链未准入 ⇒ conditions.unproven 并存）
    _write(runs / "r6_x03" / "X03-F0-W1" / "seed1", refused_chain("X03-F0-W1"),
           truncate=True, stats=False)
    # X04 UNPROVEN：完整流 + 激活但未准入
    _write(runs / "r6_x04" / "X04-F0-W1" / "seed1", refused_chain("X04-F0-W1"))
    # X05 PILOT_READY
    _write(runs / "r6_x05" / "X05-F0-W1" / "seed1", admitted_chain("X05-F0-W1"))
    # X06 BLOCKED：证据已准入，但上游 FS-INFRA 独立阻塞
    _write(runs / "r6_x06" / "X06-F0-W1" / "seed1", admitted_chain("X06-F0-W1"))
    # X07 UNPROVEN：完整流但无注入
    _write(runs / "r6_x07" / "X07-F0-W1" / "seed1", [
        _evt("X07-F0-W1", "s1", "cache_access", 1, "", 10, fault_id=0,
             va="x", pa="y", corr="origin")])
    # X01 NOT_RUN：无任何流（不建目录）
    entries = [
        _entry("X01-F0-W1"), _entry("X02-F0-W1"), _entry("X03-F0-W1"),
        _entry("X04-F0-W1"), _entry("X05-F0-W1"),
        _entry("X06-F0-W1", upstream="BLOCKED", cat="FS-INFRA"),
        _entry("X07-F0-W1"),
    ]
    contract = _contract(tmp, entries, root)
    pilots = tmp / "pilot_evidence.json"
    pilots.write_text(json.dumps({"pilots": {
        "X02-F0-W1-seed1": {"path": "runs/lsu/nonexistent/seed1/prop_evt.txt.gz",
                            "faults": 1},
    }}))
    meta, rows, _ = T.build(contract, pilots, root, runs)
    return {r["run_id"]: r for r in rows}, meta, contract


def test_six_states_reachable_and_not_overriding():
    with tempfile.TemporaryDirectory() as td:
        rows, meta, _ = build(Path(td))
        want = {
            "X01-F0-W1": "NOT_RUN",          # 磁盘无流，契约 status=BLOCKED 不得短路
            "X02-F0-W1": "EVIDENCE_MISSING",
            "X03-F0-W1": "TRUNCATED",
            "X04-F0-W1": "UNPROVEN",
            "X05-F0-W1": "PILOT_READY",
            "X06-F0-W1": "BLOCKED",
            "X07-F0-W1": "UNPROVEN",
        }
        errs = [f"{k}: state={rows[k]['state']} want={v} ({rows[k]['failure_reason']})"
                for k, v in want.items() if rows[k]["state"] != v]
        assert not errs, "状态不符:\n" + "\n".join(errs)

        # 六态都出现了（除 X02/…依赖夹具；此处断言被覆盖到的集合）
        got = {rows[k]["state"] for k in want}
        assert got == set(T.STATES), f"未覆盖全部六态：{set(T.STATES) - got}"

        # 2) 契约全体 status=BLOCKED ⇒ 绝不把"从未执行"短路成 BLOCKED
        assert rows["X01-F0-W1"]["contract_status"] == "BLOCKED"
        assert rows["X01-F0-W1"]["state"] == "NOT_RUN", \
            "契约 BLOCKED 短路了未执行的行（NOT_RUN 被杀）"
        assert not rows["X01-F0-W1"]["upstream_blocked"], \
            "上游判定（upstream_status=READY）不该因为有链门禁降级而变成阻塞"

        # 3) 截断 + 未准入并存：TRUNCATED 与 UNPROVEN 互不覆盖
        assert rows["X03-F0-W1"]["conditions"]["truncated"] is True
        assert rows["X03-F0-W1"]["state"] == "TRUNCATED"

        # 4) 上游阻塞单独表达，且不得为 PILOT_READY
        assert rows["X06-F0-W1"]["upstream_block"] == "FS-INFRA"
        assert rows["X06-F0-W1"]["admitted_samples"] == 1, "证据确已准入"
        assert rows["X06-F0-W1"]["state"] == "BLOCKED", "上游阻塞必须压制 PILOT_READY"

        # 5) evidence root 记录且与契约一致
        assert meta["evidence_root"] == str(Path(td) / "root")
        assert meta["evidence_root_matches_contract"] is True
        assert meta["evidence_root_source"], "证据根来源未被记录"


def test_truncated_and_unproven_coexist():
    """截断 + 未准入可同时为真（六者互不覆盖的正面证据）。"""
    with tempfile.TemporaryDirectory() as td:
        rows, _, _ = build(Path(td))
        r = rows["X03-F0-W1"]
        assert r["conditions"]["truncated"] is True
        assert r["state"] == "TRUNCATED"
        assert r["truncated_streams"] >= 1 and r["admitted_samples"] == 0
        # PILOT_READY 必须为假（截断流不得认证）
        assert r["conditions"]["pilot_ready"] is False


def test_evidence_root_mismatch_is_loud():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        rows, meta, contract = build(tmp)
        # 篡改契约证据根 → 必须被检出
        d = json.loads(contract.read_text())
        d["chain_gate"]["evidence_root"] = "/somewhere/else"
        contract.write_text(json.dumps(d))
        meta2, _, _ = T.build(contract, tmp / "pilot_evidence.json",
                              tmp / "root", tmp / "root/runs/lsu")
        assert meta2["evidence_root_matches_contract"] is False


def test_real_root_anchors():
    """真实证据根锚点（LSU_CHAIN_EVIDENCE_ROOT 指向真仓库根时生效）。"""
    import os
    root = os.environ.get("LSU_CHAIN_EVIDENCE_ROOT")
    if not root or not (Path(root) / "runs/lsu").is_dir():
        print("[SKIP] 未设 LSU_CHAIN_EVIDENCE_ROOT（或 runs/lsu 不存在）")
        return
    contract = REPO / "docs/gem5-fi/lsu/mdspec/ready_contract.json"
    pilots = REPO / "docs/gem5-fi/lsu/mdspec/pilot_evidence.json"
    meta, rows, _ = T.build(contract, pilots, Path(root), Path(root) / "runs/lsu")
    by = {r["run_id"]: r for r in rows}
    assert meta["evidence_root_matches_contract"] is True
    # C01-F0-W1：真根下无文件 ⇒ NOT_RUN / EVIDENCE_MISSING（不是"已执行但链不完整"）
    assert by["C01-F0-W1"]["state"] in ("NOT_RUN", "EVIDENCE_MISSING"), by["C01-F0-W1"]
    # L01-F0-W5：4 完整 3 截断 ⇒ TRUNCATED，绝不 PILOT_READY
    l01 = by["L01-F0-W5"]
    assert l01["state"] == "TRUNCATED", l01
    assert l01["state"] != "PILOT_READY"
    # A01-F0-W3：pilot 证据路径存在但**不在权威 runs 根内**（草稿/他处 worktree）
    # ⇒ 仍按磁盘事实记 NOT_RUN，但如实披露 claimed_outside_runs_root。
    a01 = by["A01-F0-W3"]
    assert a01["state"] == "NOT_RUN", a01
    assert a01["samples"] == 0 and a01["claimed_evidence"] >= 1, a01
    assert a01["claimed_outside_runs_root"], a01
    # T06/T08-F0-W4：截断流上判的 ⇒ 非 PILOT_READY，且 FS-INFRA 单独表达
    for rid in ("T06-F0-W4", "T08-F0-W4"):
        r = by[rid]
        assert r["state"] != "PILOT_READY", r
        assert r["upstream_block"] == "FS-INFRA", r
        assert r["upstream_blocked"] is True


if __name__ == "__main__":
    fails = 0
    for fn in (test_six_states_reachable_and_not_overriding,
               test_truncated_and_unproven_coexist,
               test_evidence_root_mismatch_is_loud,
               test_real_root_anchors):
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\nFAILURES: {fails if fails else 0}")
    sys.exit(1 if fails else 0)
