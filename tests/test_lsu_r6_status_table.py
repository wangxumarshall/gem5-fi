#!/usr/bin/env python3
"""tests/test_lsu_r6_status_table.py — [MDSPEC][R6-STATUS][L32] 合成夹具单测。

证明：
  1. 每个状态词都是**可达**的（BLOCKED / NOT_RUN / RUNNING / NO_ACTIVATION /
     INFRA_FAILED / CHAIN_INCOMPLETE / ORACLE_INCOMPLETE / PILOT_READY /
     FORMAL_RUNNING / FORMAL_COMPLETE）。
  2. 截断流（gzip 无 EOF 或 stats.txt 缺失/空）**绝不**计为 complete。
  3. 无流 / 无激活的 RunID **绝不**报 Masked/Contained/"no propagation"。
  4. 与 contract 的类别分歧被如实列出（不静默调和）。

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


def _evt(kind, eid, parent, tick, **kw):
    fields = [f"{k}={v}" for k, v in kw.items() if v is not None]
    return (f"PROP-EVT: kind={kind} event_id={eid} parent_event_id={parent} "
            f"tick={tick} " + " ".join(fields))


def _write_stream(seed_dir: Path, lines, *, gz=True, stats=True, truncate=False):
    seed_dir.mkdir(parents=True, exist_ok=True)
    body = "\n".join(lines) + "\n"
    if gz:
        p = seed_dir / "prop_evt.txt.gz"
        with gzip.open(p, "wt") as f:
            f.write(body)
        if truncate:                       # 掐掉尾部 → gzip 读不到 EOF
            raw = p.read_bytes()
            p.write_bytes(raw[: max(1, len(raw) - 6)])
    else:
        (seed_dir / "prop_evt.txt").write_text(body)
    if stats:
        (seed_dir / "stats.txt").write_text("simTicks 1\n")


FULL_CHAIN = [
    _evt("inj", 1, "", 100, fault_id=1, run_id="X01-F0-W1", corr="origin"),
    _evt("addr_form", 2, 1, 105, fault_id=1, va="dead", corr="origin"),
    _evt("mem_req", 3, 2, 110, fault_id=1, va="dead", dyn_inst_seq=7,
         corr="seq_primary"),
    _evt("resp", 4, 3, 115, fault_id=1, dyn_inst_seq=7, corr="seq_primary"),
    _evt("errant_commit", 5, 4, 120, fault_id=1, dyn_inst_seq=7,
         corr="taint_prop"),
    _evt("chain_end", 6, 5, 125, fault_id=1, outcome="SDC",
         detection_layer="Hardware", contained="0", corr="none"),
]
PARTIAL_CHAIN = FULL_CHAIN[:3]                 # 只到 L2 → 不完整
NO_INJECTION = [
    _evt("cache_access", 1, "", 10, fault_id=0, va="x", pa="y", corr="origin"),
    _evt("cache_return", 2, 1, 11, fault_id=0, pa="y", field="data",
         corr="seq_primary"),
]


def _contract(tmp, entries):
    p = tmp / "ready_contract.json"
    p.write_text(json.dumps({
        "total": len(entries), "status": {"READY": 0, "BLOCKED": 0},
        "entries": entries, "gate": {"binary": "/x/gem5.opt",
                                     "binary_sha256": "aa" * 32},
        "fs_checkpoint": "/cpt/x", "verdict": {"verdict": "NO-GO"},
    }))
    return p


def _entry(rid, status="READY", category="OK"):
    return {"run_id": rid, "unit": "U", "model": "M", "freq": "F0",
            "status": status, "category": category, "family": "fam",
            "why": "blocked-reason" if status == "BLOCKED" else ""}


def build(tmp):
    """构造合成 runs root，返回 {run_id: row}。"""
    root = tmp / "runs"
    # PILOT_READY：完整 L0→L5 链 + oracle + 完整流
    d = root / "r6_a" / "X01-F0-W1" / "seed1"
    _write_stream(d, FULL_CHAIN)
    (d.parent / "cell_results.json").write_text(json.dumps(
        {"runs": [{"seed": 1, "outcome": "Detected/Contained",
                   "chain": {"exit_code": 0}}]}))
    # CHAIN_INCOMPLETE：部分链（有 oracle）
    d = root / "r6_b" / "X02-F0-W1" / "seed1"
    _write_stream(d, PARTIAL_CHAIN)
    (d.parent / "cell_results.json").write_text(json.dumps(
        {"runs": [{"seed": 1, "outcome": "Masked", "chain": {"exit_code": 0}}]}))
    # ORACLE_INCOMPLETE：完整 activation 链但无任何 oracle 记录
    d = root / "r6_o" / "X03-F0-W1" / "seed1"
    _write_stream(d, PARTIAL_CHAIN)
    # NO_ACTIVATION：完整流但无注入
    d = root / "r6_c" / "X04-F0-W1" / "seed1"
    _write_stream(d, NO_INJECTION)
    # INFRA_FAILED：只有截断流
    d = root / "r6_d" / "X05-F0-W1" / "seed1"
    _write_stream(d, FULL_CHAIN, truncate=True, stats=False)
    # NOT_RUN：X06 无任何流（不建目录）
    (root / "r6_none").mkdir(parents=True)
    # RUNNING：显式在飞标记
    d = root / "r6_e" / "X07-F0-W1" / "seed1"
    _write_stream(d, FULL_CHAIN)
    (d / ".running").write_text("1")
    # FORMAL_RUNNING / FORMAL_COMPLETE
    (root / "formal_325" / "X08-F0-W1").mkdir(parents=True)
    (root / "formal_325" / "X08-F0-W1" / ".formal_running").write_text("1")
    (root / "formal_325" / "X09-F0-W1").mkdir(parents=True)
    (root / "formal_325" / "X09-F0-W1" / ".formal_complete").write_text("1")
    # BLOCKED
    entries = [
        _entry("X01-F0-W1"), _entry("X02-F0-W1"), _entry("X03-F0-W1"),
        _entry("X04-F0-W1"), _entry("X05-F0-W1"), _entry("X06-F0-W1"),
        _entry("X07-F0-W1"), _entry("X08-F0-W1"), _entry("X09-F0-W1"),
        _entry("X10-F0-W1", status="BLOCKED", category="RULING"),
    ]
    contract = _contract(tmp, entries)
    meta, rows, _ = T.build_table(contract, root, None, "/cpt/x", {}, None)
    return {r["run_id"]: r for r in rows}, meta


def test_all_states_reachable_and_truncation_not_complete():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        rows, meta = build(tmp)
        expect = {
            "X01-F0-W1": "PILOT_READY",
            "X02-F0-W1": "CHAIN_INCOMPLETE",
            "X03-F0-W1": "ORACLE_INCOMPLETE",
            "X04-F0-W1": "NO_ACTIVATION",
            "X05-F0-W1": "INFRA_FAILED",
            "X06-F0-W1": "NOT_RUN",
            "X07-F0-W1": "RUNNING",
            "X08-F0-W1": "FORMAL_RUNNING",
            "X09-F0-W1": "FORMAL_COMPLETE",
            "X10-F0-W1": "BLOCKED",
        }
        errs = []
        for rid, want in expect.items():
            got = rows[rid]["state"]
            if got != want:
                errs.append(f"{rid}: state={got} want={want} "
                            f"reason={rows[rid]['failure_reason']}")
        assert not errs, "状态不符:\n" + "\n".join(errs)

        # 截断流绝不计为 complete
        assert rows["X05-F0-W1"]["complete_streams"] == 0, "截断流被计入 complete"
        assert rows["X05-F0-W1"]["truncated_streams"] == 1
        # P1 完整流
        assert rows["X01-F0-W1"]["complete_streams"] == 1
        assert rows["X01-F0-W1"]["truncated_streams"] == 0
        # 无流 ⇒ not measured，绝不 Masked/Contained
        assert rows["X06-F0-W1"]["oracle_result"] == "not measured"
        assert rows["X06-F0-W1"]["pilot_seeds"] == 0
        # 无激活 ⇒ oracle 记 not measured
        assert rows["X04-F0-W1"]["oracle_result"] == "not measured"
        assert rows["X04-F0-W1"]["activated_samples"] == 0
        # 全 10 个状态都被命中
        assert set(expect.values()) == set(T.STATES), \
            f"未覆盖全部状态词：{set(T.STATES) - set(expect.values())}"
        # 分歧如实列出（此处全部一致 → 0；X10 BLOCKED 一致）
        sumry = T.summarize(meta, list(rows.values()),
                            json.loads(Path(meta["contract"]).read_text()))
        assert "disagreements" in sumry["ready_vs_contract"]


def test_oversized_guard_never_claims_ready():
    """超上限的 activated 流：真检查器不跑 ⇒ 绝不因"没查出问题"判 PILOT_READY。"""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        root = tmp / "runs"
        d = root / "r6_a" / "X01-F0-W1" / "seed1"
        _write_stream(d, FULL_CHAIN)          # 本来能过门禁的完整链
        (d.parent / "cell_results.json").write_text(json.dumps(
            {"runs": [{"seed": 1, "outcome": "SDC", "chain": {"exit_code": 0}}]}))
        contract = _contract(tmp, [_entry("X01-F0-W1")])
        # cap=3 < 6 事件 ⇒ oversized ⇒ 不跑检查器
        _, rows, _ = T.build_table(contract, root, None, "/cpt", {}, None,
                                   max_chain_events=3)
        assert rows[0]["state"] == "CHAIN_INCOMPLETE", rows[0]
        assert "oversized" in rows[0]["strict_chain_verdict"], rows[0]
        # 同一证据、cap 放宽 ⇒ 恢复 PILOT_READY（证明差别只来自上限，非证据）
        _, rows2, _ = T.build_table(contract, root, None, "/cpt", {}, None,
                                    max_chain_events=1000)
        assert rows2[0]["state"] == "PILOT_READY", rows2[0]


def test_disagreement_reported_not_reconciled():
    """contract 说 READY，但证据只有 NO_ACTIVATION ⇒ 必须列为分歧，不得静默调和。"""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        rows, meta = build(tmp)
        contract = json.loads(Path(meta["contract"]).read_text())
        sumry = T.summarize(meta, list(rows.values()), contract)
        d = sumry["ready_vs_contract"]
        # contract READY 9 个（除 X10）；本表 PILOT_READY 仅 1 个 ⇒ 分歧 = 8
        assert d["disagreement_count"] == 8, d
        assert all(cs == "READY" for _, cs, _ in d["disagreements"])


if __name__ == "__main__":
    fails = 0
    for fn in (test_all_states_reachable_and_truncation_not_complete,
               test_oversized_guard_never_claims_ready,
               test_disagreement_reported_not_reconciled):
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL {fn.__name__}: {e}")
    sys.exit(1 if fails else 0)
