"""tests/test_fsu_rate_ordinals.py — F1/F2/F3 确定性 rate ordinal 语义。"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fsu_rate_ordinals as O
import fsu_seed_audit as A
import fsu_seed_runner as R

RATES = {"F1": 1_000_000, "F2": 100_000, "F3": 10_000}


# ---------- interval 边界 / ordinal 契约 ----------

@pytest.mark.parametrize("freq,rate", sorted(RATES.items()))
def test_interval_bounds_all_seeds(freq, rate):
    lo, hi = O.interval_bounds(rate, 50)
    assert lo == rate // 2 and hi == rate + rate // 2
    for seed in range(20):
        doc = O.build_rate_ordinals(rate * 4, rate, 50, seed, warmup=7)
        assert doc["interval_bounds"] == {"lo": lo, "hi": hi}
        for iv in doc["intervals"]:
            assert lo <= iv <= hi, (freq, seed, iv)
        for o in doc["ordinals"]:
            assert o > 7
        # ordinal 是 warmup 起的 interval 累加值
        acc = 7
        for o, iv in zip(doc["ordinals"], doc["intervals"]):
            acc += iv
            assert o == acc
        assert doc["injection_count"] == len(doc["ordinals"])
        assert doc["ordinal_index"] == list(range(len(doc["ordinals"])))


@pytest.mark.parametrize("freq,rate", sorted(RATES.items()))
def test_ordinals_strictly_increasing_and_within_N(freq, rate):
    doc = O.build_rate_ordinals(rate * 10, rate, 50, 12345)
    assert doc["ordinals"]
    assert doc["ordinals"] == sorted(set(doc["ordinals"]))
    assert all(1 <= o <= rate * 10 for o in doc["ordinals"])


def test_same_seed_replays_exactly():
    a = O.build_rate_ordinals(200_000, 10_000, 50, 42, warmup=3)
    b = O.build_rate_ordinals(200_000, 10_000, 50, 42, warmup=3)
    assert a == b
    assert O.canonical_bytes(a) == O.canonical_bytes(b)
    assert O.ordinals_sha256(a) == O.ordinals_sha256(b)


def test_different_seeds_differ():
    seqs = {tuple(O.build_rate_ordinals(200_000, 10_000, 50, s)["intervals"])
            for s in (1, 2, 3, 4)}
    assert len(seqs) == 4


def test_N_below_first_ordinal_is_zero_injection():
    ref = O.build_rate_ordinals(1_000_000, 10_000, 50, 7)
    first = ref["first_ordinal"]
    assert O.build_rate_ordinals(first - 1, 10_000, 50, 7)["ordinals"] == []
    # 恰好命中边界：N == first ordinal 时产生且仅产生第一个注入点。
    hit = O.build_rate_ordinals(first, 10_000, 50, 7)
    assert hit["ordinals"] == [first]


def test_interval_boundary_values_hit_lo_and_hi():
    lo, hi = O.interval_bounds(10_000, 50)
    span = hi - lo + 1
    low = O.build_rate_ordinals(lo, 10_000, 50, 0,
                                u64_source=lambda: 0)
    assert low["intervals"] == [lo] and low["ordinals"] == [lo]
    # 首次抽到 span-1 -> 取模后正好是 hi；N=hi 时恰好命中上界。
    high = O.build_rate_ordinals(hi, 10_000, 50, 0,
                                 u64_source=lambda: span - 1)
    assert high["intervals"] == [hi] and high["ordinals"] == [hi]
    # N=hi-1 时同一个上界 interval 越界 -> 零注入。
    miss = O.build_rate_ordinals(hi - 1, 10_000, 50, 0,
                                 u64_source=lambda: span - 1)
    assert miss["ordinals"] == []


def test_zero_jitter_is_exact_rate():
    doc = O.build_rate_ordinals(100_000, 10_000, 0, 9)
    assert set(doc["intervals"]) == {10_000}
    assert doc["ordinals"] == [10_000, 20_000, 30_000, 40_000, 50_000,
                               60_000, 70_000, 80_000, 90_000, 100_000]


def test_F1_N_1_5M_always_reaches_first_injection():
    lo, hi = O.interval_bounds(1_000_000, 50)
    assert hi == 1_500_000
    for seed in range(50):
        doc = O.build_rate_ordinals(1_500_000, 1_000_000, 50, seed)
        assert doc["injection_count"] >= 1, seed
        assert doc["first_ordinal"] <= 1_500_000


def test_warmup_and_empty_roi():
    doc = O.build_rate_ordinals(100_000, 10_000, 50, 1, warmup=99_999)
    assert doc["ordinals"] == []          # 剩余预算 1 < 最小间隔
    doc2 = O.build_rate_ordinals(100_000, 10_000, 0, 1, warmup=50_000)
    assert doc2["ordinals"] == [60_000, 70_000, 80_000, 90_000, 100_000]


def test_invalid_inputs_rejected():
    for args in [(-1, 10_000, 50, 1), (10, 0, 50, 1), (10, 10_000, 100, 1),
                 (10, 10_000, -1, 1), (10, 10_000, "x", 1),
                 (10, 10_000, 50, -1)]:
        with pytest.raises(ValueError):
            O.build_rate_ordinals(*args)


def test_sha256_is_stable_and_content_addressed():
    a = O.build_rate_ordinals(50_000, 10_000, 50, 5)
    b = O.build_rate_ordinals(50_000, 10_000, 50, 6)
    assert O.ordinals_sha256(a) != O.ordinals_sha256(b)
    assert len(O.ordinals_sha256(a)) == 64


# ---------- freq 标签 ↔ rate 语义门禁 ----------

def test_freq_rate_validation():
    good = {"rate_divisor": 10_000, "jitter_pct": 50}
    assert O.validate_rate_for_freq("F3", good) == {
        "rate_divisor": 10_000, "jitter_pct": 50, "warmup": 0}
    with pytest.raises(O.RateSemanticsError):
        O.validate_rate_for_freq("F3", None)
    with pytest.raises(O.RateSemanticsError):
        O.validate_rate_for_freq("F3", {"rate_divisor": 100_000,
                                        "jitter_pct": 50})
    with pytest.raises(O.RateSemanticsError):
        O.validate_rate_for_freq("F1", {"rate_divisor": 10_000,
                                        "jitter_pct": 50})
    with pytest.raises(O.RateSemanticsError):
        O.validate_rate_for_freq("F0", good)
    assert O.validate_rate_for_freq("F0", None) is None


def _manifest(tmp_path, freq="F3", rate=None):
    wl = tmp_path / "wl"
    wl.write_text("#!/bin/sh\nexit 0\n")
    wl.chmod(0o755)
    gem5 = tmp_path / "gem5"
    gem5.write_text("#!/bin/sh\nexit 0\n")
    gem5.chmod(0o755)
    injector = {"component": "fsu", "fpu_mode": {"bitseg": "mant_lo"},
                "max_faults": 1, "first_clock": 0}
    if rate is not None:
        injector["rate"] = rate
    m = {
        "run_id": f"FSU-FP04-{freq}-W4", "model_id": "FP04",
        "unit": "FSU Pipe", "freq": freq, "load_id": "W4",
        "submodel": "FP04-c",
        "workload": {"binary": str(wl), "golden": "a" * 64,
                     "oracle_kind": "array_hash", "oracle_tol": 0},
        "config_family": "C3", "injector": injector,
        # F3 is DEFERRED_BY_USER in the active F0/F5 scope; this fixture
        # exercises legacy rate parsing only, in a temporary out-root.
        "scope_test_mode": True,
        "limits": {"timeout_s": 10},
    }
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(m), encoding="utf-8")
    return p, gem5


def test_runner_rejects_freq_label_without_rate(tmp_path):
    """只改 freq 标签、缺少真实 ordinal 语义时 runner 必须拒绝。"""
    mp, gem5 = _manifest(tmp_path, "F3", rate=None)
    with pytest.raises(O.RateSemanticsError):
        R.run_seed(mp, 1, out_root=tmp_path / "runs", gem5=gem5,
                   root=Path(__file__).resolve().parents[1],
                   runner=lambda cmd, timeout: (0, "", "", False))
    # 不得留下 attempt 伪证据。
    assert not (tmp_path / "runs/FSU-FP04-F3-W4/seed1").exists()


def test_runner_rejects_wrong_rate_divisor(tmp_path):
    mp, gem5 = _manifest(tmp_path, "F3",
                         rate={"rate_divisor": 100_000, "jitter_pct": 50})
    with pytest.raises(O.RateSemanticsError):
        R.run_seed(mp, 1, out_root=tmp_path / "runs", gem5=gem5,
                   root=Path(__file__).resolve().parents[1],
                   runner=lambda cmd, timeout: (0, "", "", False))


def test_runner_rejects_rate_on_F0(tmp_path):
    mp, gem5 = _manifest(tmp_path, "F0",
                         rate={"rate_divisor": 10_000, "jitter_pct": 50})
    with pytest.raises(O.RateSemanticsError):
        R.run_seed(mp, 1, out_root=tmp_path / "runs", gem5=gem5,
                   root=Path(__file__).resolve().parents[1],
                   runner=lambda cmd, timeout: (0, "", "", False))


# ---------- runner 正向 rate 路径 ----------

def _evt(**kw):
    import fsu_prop_fields as P
    d = {k: "" for k in P.PROP_EVT_FIELDS}
    d.update(kw)
    return P.PREFIX + " " + " ".join(f"{k}={d[k]}" for k in P.PROP_EVT_FIELDS)


def _full_chains(n, runid, sample, ordinals, incomplete_fault=None):
    lines, eid, tick = [], 0, 100
    for i in range(n):
        fid = str(i + 1)
        b = dict(run_id=runid, sample_run_id=sample, fault_id=fid,
                 model_id="FP04", unit="FSU_Pipe", freq="F3",
                 load_id="W4", submodel="FP04-c",
                 field="mant_lo", precision="fp64", lane_width="64",
                 lane_offset="0", bit_indices="5", bit_in_lane="5",
                 field_lo="0", field_hi="17",
                 fault_mask="0x0000000000000020",
                 lane_mask="0x00000000000000000000000000000020",
                 before="0x3ff0000000000000",
                 after="0x3ff0000000000020",
                 full_before="0x00000000000000003ff0000000000000",
                 full_after="0x00000000000000003ff0000000000020",
                 eligible_ordinal=str(ordinals[i]),
                 rate_divisor="10000", jitter_pct="50",
                 interval=str(ordinals[i] - (ordinals[i - 1] if i else 0)),
                 ordinal_index=str(i))
        def e(**kw):
            nonlocal eid, tick
            row = _evt(event_id=str(eid), tick=str(tick), **b, **kw)
            eid += 1
            tick += 1
            return row
        if incomplete_fault is not None and fid == str(incomplete_fault):
            lines += [
                e(kind="fault_applied", activated="0"),
                e(kind="carrier_state", parent_event_id=str(eid - 1)),
                e(kind="not_activated", parent_event_id=str(eid - 1),
                  activated="0"),
            ]
            continue
        lines += [
            e(kind="fault_applied", activated="1"),
            e(kind="carrier_state", parent_event_id=str(eid - 1)),
            e(kind="operand_read", parent_event_id=str(eid - 1), activated="1"),
            e(kind="execute", parent_event_id=str(eid - 1)),
            e(kind="prf_writeback", parent_event_id=str(eid - 1)),
            e(kind="commit", parent_event_id=str(eid - 1),
              detection_layer="L5", outcome="errant_commit",
              oracle_diff="array_hash_diff"),
        ]
    return lines


def _rate_runner(commands, n, incomplete_fault=None):
    import gzip

    def runner(cmd, timeout):
        commands.append(cmd)
        outdir = Path(cmd[cmd.index("-d") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        if "--fpu_count_only" in cmd:
            (outdir / "fpu_injections.log").write_text(
                "CHAOS_ELIGIBLE_COUNT=57347\n", encoding="utf-8")
            (outdir / "stats.txt").write_text("simSeconds 1\n", encoding="utf-8")
            return 0, "", "", False
        (outdir / "fpu_injections.log").write_text(
            f"faults_injected: {n}\n", encoding="utf-8")
        (outdir / "stats.txt").write_text("simSeconds 1\n", encoding="utf-8")
        (outdir / "prop_evt.txt.gz").write_bytes(gzip.compress(
            ("\n".join(_full_chains(
                n, "FSU-FP04-F3-W4", "s1",
                O.build_rate_ordinals(57347, 10_000, 50, 1)["ordinals"],
                incomplete_fault=incomplete_fault)) + "\n").encode()))
        return 0, "ARRAYHASH=" + "0" * 64, "", False
    return runner


def test_runner_rate_mode_generates_ordinals_and_admits(tmp_path):
    doc = O.build_rate_ordinals(57347, 10_000, 50, 1)
    n = doc["injection_count"]
    assert n >= 1
    mp, gem5 = _manifest(tmp_path, "F3",
                         rate={"rate_divisor": 10_000, "jitter_pct": 50})
    cmds = []
    res = R.run_seed(mp, 1, out_root=tmp_path / "runs", gem5=gem5,
                     root=Path(__file__).resolve().parents[1],
                     runner=_rate_runner(cmds, n))
    assert res["status"] == "admitted", res
    attempt = Path(res["attempt"])
    ord_doc = json.loads((attempt / "ordinals.json").read_text())
    assert ord_doc["ordinals"] == doc["ordinals"]
    man = json.loads((attempt / "manifest.json").read_text())
    assert man["rate"]["generator"] == O.GENERATOR
    assert man["rate"]["version"] == O.GENERATOR_VERSION
    assert man["rate"]["seed"] == 1
    assert man["rate"]["eligible_total"] == 57347
    assert man["rate"]["ordinals"] == doc["ordinals"]
    assert len(man["rate"]["ordinals_sha256"]) == 64
    rep = json.loads((attempt / "chain_report.json").read_text())
    assert rep["rate_ok"] is True
    assert rep["expected_injections"] == n
    assert rep["actual_injections"] == n
    assert rep["all_faults_present"] is True
    assert len(rep["fault_terminals"]) == n
    assert set(rep["fault_terminals"].values()) == {"full"}
    assert rep["run_level_oracle"]["category"] == "SDC"
    inj = next(c for c in cmds if "--fpu_count_only" not in c)
    assert "--fpu_rate_ordinals" in inj
    assert inj[inj.index("--fpu_rate_ordinals") + 1] == \
        ",".join(str(x) for x in doc["ordinals"])
    assert "--fpu_events_to_skip" in inj
    assert inj[inj.index("--fpu_events_to_skip") + 1] == "0"


def _run_multi(tmp_path, n=4, incomplete_fault=None):
    mp, gem5 = _manifest(tmp_path, "F3",
                         rate={"rate_divisor": 10_000, "jitter_pct": 50})
    res = R.run_seed(
        mp, 1, out_root=tmp_path / "runs", gem5=gem5,
        root=Path(__file__).resolve().parents[1],
        runner=_rate_runner([], n, incomplete_fault=incomplete_fault))
    return res


def test_multi_fault_doc_and_audit_are_per_fault(tmp_path):
    res = _run_multi(tmp_path, n=4)
    assert res["status"] == "admitted", res
    attempt = Path(res["attempt"])
    md = (attempt / "FSU-FP04-F3-W4-seed1.md").read_text(encoding="utf-8")
    for fid in ("1", "2", "3", "4"):
        assert f"### fault {fid}" in md
    # 第 5 节事件表必须覆盖全部 fault 的主链事件。
    rep = json.loads((attempt / "chain_report.json").read_text())
    for fid, fr in rep["chain"]["faults"].items():
        for eid in fr["path_event_ids"]:
            assert f"| {eid} |" in md, (fid, eid)
    # 逐 fault 终局表必须在 Markdown 中。
    assert "### 逐 fault 终局" in md
    audit = A.audit_attempt(attempt)
    assert audit["ok"] is True, audit["failures"]
    # audit_attempt does not write; write_audit does.
    full = A.write_audit(attempt)
    assert full["ok"] is True and full["certified"] is True
    assert full["fault_count"] == 4
    assert full["all_faults_admitted"] is True
    assert full["all_faults_certified"] is True
    assert set(full["fault_terminals"].values()) == {"full"}


def test_audit_detects_one_fault_terminal_tamper(tmp_path):
    res = _run_multi(tmp_path, n=4)
    attempt = Path(res["attempt"])
    md = attempt / "FSU-FP04-F3-W4-seed1.md"
    text = md.read_text(encoding="utf-8").replace(
        "| 3 | full |", "| 3 | contained_L3 |")
    md.write_text(text, encoding="utf-8")
    audit = A.audit_attempt(attempt)
    assert audit["ok"] is False
    assert any("fault 3 MD terminal" in f for f in audit["failures"])


def test_audit_detects_missing_fault_chain_in_md(tmp_path):
    res = _run_multi(tmp_path, n=4)
    attempt = Path(res["attempt"])
    rep = json.loads((attempt / "chain_report.json").read_text())
    eid = rep["chain"]["faults"]["2"]["path_event_ids"][2]
    md = attempt / "FSU-FP04-F3-W4-seed1.md"
    text = "\n".join(l for l in md.read_text(encoding="utf-8").splitlines()
                     if f"| {eid} |" not in l)
    md.write_text(text, encoding="utf-8")
    audit = A.audit_attempt(attempt)
    assert audit["ok"] is False
    assert any("fault 2 MD 覆盖主链全部事件" in f
               for f in audit["failures"])


def test_one_incomplete_fault_blocks_seed_certification(tmp_path):
    res = _run_multi(tmp_path, n=4, incomplete_fault=2)
    assert res["status"] == "failed"
    attempt = Path(res["attempt"])
    rep = json.loads((attempt / "chain_report.json").read_text())
    assert rep["actual_injections"] == 4
    assert rep["chain"]["faults"]["2"]["terminal"] == "not_activated"
    assert rep["chain"]["faults"]["2"]["admitted"] is False
    assert rep["chain"]["certified"] is False
    assert not (attempt.parent / "AUTHORITATIVE").exists()
    audit = A.audit_attempt(attempt)
    assert audit["ok"] is False


def test_runner_zero_ordinal_keeps_attempt_not_activated(tmp_path):
    mp, gem5 = _manifest(tmp_path, "F1",
                         rate={"rate_divisor": 1_000_000, "jitter_pct": 50})

    def runner(cmd, timeout):
        outdir = Path(cmd[cmd.index("-d") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "fpu_injections.log").write_text(
            "CHAOS_ELIGIBLE_COUNT=100\n", encoding="utf-8")
        (outdir / "stats.txt").write_text("simSeconds 1\n", encoding="utf-8")
        return 0, "", "", False

    res = R.run_seed(mp, 1, out_root=tmp_path / "runs", gem5=gem5,
                     root=Path(__file__).resolve().parents[1], runner=runner)
    assert res["status"] == "not_activated"
    assert res["reason"] == "eligible_below_first_ordinal"
    attempt = Path(res["attempt"])
    assert (attempt / ".not_activated").exists()
    assert (attempt / "ordinals.json").exists()
    assert not (attempt / "inject").exists()
    assert not (attempt.parent / "AUTHORITATIVE").exists()
    note = json.loads((attempt / "not_activated.json").read_text())
    assert note["eligible_total"] == 100
