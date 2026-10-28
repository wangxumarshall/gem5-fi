#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-A4] F2/gap_bfs repeat census 契约（TDD 先行）。

背景（已实证，不再调查根因）：
  * F2 = mean 100000 eligible events、±50% jitter；首火位是 eligible 计数的
    序号：scheduleNext(warmup) 里 next_fire = warmup + 50000 + lcg(seed)%100000
    （CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh:224/291，
    chaosSampleLCG 在 chaos_event_sample.hh:49）。seed1/2/3 的 F2 首火位
    必须由该 LCG **独立重算**，不得照抄报告里的 max=140806。
  * 旧 REPEAT_FACTOR 按裸访存流标定；A04/A05-d/A06/A08 的 eligible 是
    子模型过滤后的流（实测 A05-F2-W3 s1 R=434：attempted=156129、
    eligible=91623、injected=0 —— 91623 < 140806）。因此 repeat 键必须带
    submodel，且 submodel 由 seed 奇偶决定（A04/A06/A08）。
  * 旧 resolver 在 seed 未知时查 (model,freq,binary)，A04/A06/A08 会在
    seed 已知后选错键。resolve_cell 必须接受 seed 并在 seed 已知后查键；
    缺键/超界仍要**响亮 BLOCKED**，不许猜。

本测试钉死：
  1. 过滤后 eligible 的 E1/delta 解析与 repeat 公式
     R = 1 + ceil((1.2*max_first_fire - E1)/delta)，下限 1、最小性、delta<=0 响亮报错；
  2. gap_bfs F2 有实测条目、resolver 不再 BLOCKED；
  3. 三个 seed 首火位取最大值、R 覆盖 1.2×max；R 上界超出 → 响亮 BLOCKED；
  4. 不改变 F2 随机序列（LCG/首火位与冻结实现一致；tier/warmup/span flags 不变）；
  5. submodel 由 seed 奇偶推导，repeat 键按 submodel 分桶；
  6. 重复次数足够时真实运行 injected=1，且三方注入计数一致
     （run.out CHAOS_LSU_TRIGGER / addrpath_injections.log FUNNEL / campaign 分类）。
     该集成用例是**慢测试**（真实 gem5），标记 @pytest.mark.slow，但不跳过真断言。

用法：python3 tests/test_lsu_r6a4_repeat_census.py   （退出码 0=全 PASS）
      pytest tests/test_lsu_r6a4_repeat_census.py -q
"""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC          # noqa: E402
import lsu_repeat_census as RC    # noqa: E402

# 冻结二进制（主 agent 统一构建，Lane A 不重建）
FROZEN_SHA = ("c52ef2257bb9dad6ddf593a1dbca51d5"
              "096e52ac790ec901c46ebf9c7114c71e")

# 实测证据根
RUNS = Path("/home/sdc/gem5-fi-ding/runs/lsu")

# 一个真实的 CHAOS_LSU_TRIGGER teardown 行（A05-F2-W3 seed1，R=434，
# runs/lsu/r6_a_r6a3_A05-F2-W3_s1/.../run.out）——用它钉住解析契约。
REAL_TRIGGER_LINE = (
    "CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F2 attempted=156129 "
    "eligible=91623 injected=0 first_eligible_tick=197890 "
    "last_eligible_tick=211522850 fires=n/a no_effect=n/a "
    "(activated=W3-L0-layer)")
REAL_FUNNEL_LINE = (
    "FUNNEL: attempted=156129 eligible=91623 injected=0")


def _cell(rid, model, freq, workload):
    cell = [""] * 12
    cell[LC.COL_RUNID] = rid
    cell[LC.COL_MODEL] = model
    cell[LC.COL_UNIT] = "AGU"
    cell[LC.COL_FREQ] = freq
    cell[LC.COL_WORKLOAD] = workload
    return cell


# ---------------------------------------------------------------- [1] LCG
def test_lcg_and_first_fire_match_frozen_implementation():
    """首火位 = warmup + iv/2 + lcg(seed)%iv，与 chaos_lsu_trigger.hh 逐位一致。"""
    # 冻结实现的 LCG 常数（chaos_event_sample.hh:49）
    assert RC.LCG_MUL == 6364136223846793005
    assert RC.LCG_ADD == 1442695040888963407
    # lcg(1) 的 64 位值（独立重算）
    assert RC.lcg(1) == 7806831264735756412
    assert RC.lcg(2) == 14170967488582549417
    assert RC.lcg(3) == 2088359638719790806

    # F2：warmup=0（非 F0），iv=100000 -> 50000 + lcg%100000
    assert RC.first_fire("F2", 1) == 106412
    assert RC.first_fire("F2", 2) == 99417
    assert RC.first_fire("F2", 3) == 140806
    assert RC.max_first_fire("F2") == 140806
    # F1：iv=1e6 -> 500000 + lcg%1000000
    assert RC.first_fire("F1", 3) == 1290806
    assert RC.max_first_fire("F1") == 1290806
    # F2/F4 同抽签位置（intervalEvents 都是 1e5）
    assert RC.first_fire("F4", 3) == RC.first_fire("F2", 3)
    # warmup 平移首火位
    assert RC.first_fire("F2", 3, warmup_events=7) == 140806 + 7


# ------------------------------------------------------- [2] 解析 + 公式
def test_parse_trigger_and_filtered_eligible_formula():
    t = RC.parse_trigger_summary(REAL_TRIGGER_LINE)
    assert t == {"injector": "CHAOSAddrPath", "tier": "F2",
                 "attempted": 156129, "eligible": 91623, "injected": 0}
    assert RC.parse_trigger_summary("nothing here") is None
    assert RC.parse_funnel(REAL_FUNNEL_LINE) == (156129, 91623, 0)
    assert RC.parse_funnel("nothing here") is None

    # 旧表裸流（E1=2789, delta=384.5）-> 434，这是既有 A01-F2-agu 的值
    import math
    assert RC.compute_repeat(2789, 384.5, 140806) == 434
    assert RC.compute_repeat(2789, 384.5, 140806) == (
        1 + math.ceil((1.2 * 140806 - 2789) / 384.5))

    # 下限 1：E1 已覆盖 1.2×max（gap_bfs E1=264751 >> 168967.2）
    assert RC.compute_repeat(264751, 261909, 140806) == 1
    # 边界：E1 一旦 >= 1.2*max 就只需 1 趟（用 ceil 保证确实覆盖）
    assert RC.compute_repeat(math.ceil(1.2 * 140806), 1, 140806) == 1
    assert RC.compute_repeat(int(1.2 * 140806), 1, 140806) == 2  # 168967 < 168967.2

    # 最小性：R 覆盖 1.2×max，但 R-1 不覆盖
    for E1, delta in ((1685, 207.5), (110, 41.0), (3187, 783.5)):
        r = RC.compute_repeat(E1, delta, 140806)
        assert E1 + (r - 1) * delta >= 1.2 * 140806
        assert E1 + (r - 2) * delta < 1.2 * 140806

    # delta<=0（流不随 repeat 增长）：绝不除零/编造，响亮报错
    with pytest.raises(ValueError):
        RC.compute_repeat(2789, 0, 140806)
    with pytest.raises(ValueError):
        RC.compute_repeat(2789, -1.0, 140806)


# ------------------------------------------- [3] submodel 由 seed 奇偶决定
def test_submodel_by_seed_parity():
    assert LC.submodel_for("A04", 1) == "a04_same_object"
    assert LC.submodel_for("A04", 2) == "a04_same_page"
    assert LC.submodel_for("A04", 3) == "a04_same_object"
    assert LC.submodel_for("A06", 1) == "a06_size"
    assert LC.submodel_for("A06", 2) == "a06_mask"
    assert LC.submodel_for("A08", 1) == "a08_channel"
    assert LC.submodel_for("A08", 2) == "a08_pair_swap"
    # 无子模型
    for m in ("A01", "A02", "A05", "A07"):
        assert LC.submodel_for(m, 1) == ""
        assert LC.submodel_for(m, 2) == ""


def test_repeat_keys_are_submodel_scoped():
    for key in LC.REPEAT_FACTOR:
        assert len(key) == 4, key
        model, freq, binary, submodel = key
        assert freq in {"F1", "F2", "F4"}
        if model in {"A04", "A06", "A08"}:
            assert submodel, ("submodel-keyed model must not carry an empty "
                              "submodel key: %r" % (key,))
        else:
            assert submodel == "", key
    # A01/A02/A05 的现有合格值保持不变（用户工作令）
    assert LC.repeat_factor_for("A01", "F1", "agu_addrmodes", seed=1) == 4023
    assert LC.repeat_factor_for("A01", "F2", "agu_addrmodes", seed=1) == 434
    assert LC.repeat_factor_for("A02", "F2", "agu_addrmodes", seed=1) == 434
    # 无 seed 的只读查询（ready-contract）取各 submodel 的最大值（保守），
    # 绝不因"缺 seed"把可跑的行误报为不可跑；运行路径永远带 seed。
    assert LC.repeat_factor_for("A04", "F2", "agu_addrmodes") == 1021
    assert LC.repeat_factor_for("A04", "F2", "mini_check") == 375
    # [R6-A4] 抬上限到 131072（config+workload+新二进制）后，A08-a 的实测 R
    # 生成真实命令；不伪造、不 clamp。
    assert LC.repeat_factor_for("A08", "F2", "agu_addrmodes", seed=1) == 15706
    assert LC.repeat_factor_for("A08", "F2", "sq_forward", seed=1) == 84418
    assert 15706 <= LC.REPEAT_MAX and 84418 <= LC.REPEAT_MAX
    f, _g, why = LC.resolve_cell(
        _cell("A08-F2-W3", "A08", "F2", "AGU-AddrModes"), seed=1)
    assert f is not None, why
    assert f[f.index("--chaos_repeat") + 1] == "15706", f
    f5, _g5, why5 = LC.resolve_cell(
        _cell("A08-F2-W5", "A08", "F2", "SQ-Forward"), seed=3)
    assert f5 is not None, why5
    assert f5[f5.index("--chaos_repeat") + 1] == "84418", f5
    # A08-b 结构不可达（delta=0）-> 没有键
    assert LC.repeat_factor_for("A08", "F2", "agu_addrmodes", seed=2) is None


# ------------------------------------------------ [4] gap_bfs 解 BLOCKED
@pytest.mark.parametrize("model", ["A01", "A02"])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_gap_bfs_f2_resolver_not_blocked(model, seed):
    rid = "%s-F2-W9" % model
    flags, golden, binary = LC.resolve_cell(
        _cell(rid, model, "F2", "GAP/Graph500"), seed=seed)
    assert flags is not None, (rid, golden)
    assert binary == "gap_bfs", binary
    assert golden == LC.GOLDENS["gap_bfs"]
    assert ("%s", model) and ("A01", "F2", "gap_bfs", "") in LC.REPEAT_FACTOR
    rep = LC.repeat_factor_for(model, "F2", "gap_bfs", seed=seed)
    assert rep is not None and 1 <= rep <= LC.REPEAT_MAX
    if rep > 1:
        i = flags.index("--chaos_repeat")
        assert flags[i + 1] == str(rep)
    else:
        assert "--chaos_repeat" not in flags
        # E1 已覆盖首火位 -> R=1，依据必须写在表注释里（实测 E1 >= 1.2*max）
        assert LC.repeat_evidence(model, "F2", "gap_bfs", seed)["R"] == 1


# --------------------------------- [5] seed 已知后按 submodel 选键 + F2 不变
def test_resolve_selects_submodel_key_and_f2_sequence_unchanged():
    cell = _cell("A04-F2-W3", "A04", "F2", "AGU-AddrModes")
    f1, g1, b1 = LC.resolve_cell(cell, seed=1)
    f2, g2, b2 = LC.resolve_cell(cell, seed=2)
    assert f1 is not None and f2 is not None
    assert b1 == b2 == "agu_addrmodes"

    # F2 随机序列不变：tier/warmup/span 与冻结参数化一致（非 F0 -> 0/1000）
    for flags in (f1, f2):
        assert flags[flags.index("--addrpath_lsu_tier") + 1] == "F2"
        assert flags[flags.index("--addrpath_warmup_events") + 1] == "0"
        assert flags[flags.index("--addrpath_span_events") + 1] == "1000"
        # repeat 只加 --chaos_repeat，不改 trigger 的 seed 旗标
        assert "--addrpath_rng_seed" not in flags

    # seed 奇偶选择不同 submodel -> 必须查不同键（值可不同）
    r1 = LC.repeat_factor_for("A04", "F2", "agu_addrmodes", seed=1)
    r2 = LC.repeat_factor_for("A04", "F2", "agu_addrmodes", seed=2)
    assert r1 is not None and r2 is not None
    keys = LC.REPEAT_FACTOR
    assert ("A04", "F2", "agu_addrmodes", "a04_same_object") in keys
    assert ("A04", "F2", "agu_addrmodes", "a04_same_page") in keys

    # submodel flags 由同一函数在 resolve 之后追加（与 run_single_cell 同源）
    af1 = LC.apply_seed_variant_flags("A04", "F2", 1, "agu_addrmodes", f1)
    af2 = LC.apply_seed_variant_flags("A04", "F2", 2, "agu_addrmodes", f2)
    assert "--agu_object_spec" in af1
    assert af2[af2.index("--agu_pre_mode") + 1] == "a04_same_page"
    assert af1[af1.index("--agu_pre_mode") + 1] == "a04_same_object"


# ------------------------------- [6] 缺键/超界响亮 BLOCKED（绝不自造数值）
def test_missing_key_and_over_cap_blocked_loudly(monkeypatch):
    cell = _cell("A04-F2-W3", "A04", "F2", "AGU-AddrModes")

    # 缺键：未 census 的 workload
    cell_bad = _cell("A04-F2-W3", "A04", "F2", "AGU-AddrModes")
    cell_bad[LC.COL_WORKLOAD] = "SQ-Forward"   # A04 无 sq_forward 的 F2 键
    flags, _g, reason = LC.resolve_cell(cell_bad, seed=1)
    assert flags is None and "repeat-factor-unmeasured" in reason

    # 超界：真实表上人工放大 -> BLOCKED(repeat-factor-over-cap)
    monkeypatch.setitem(
        LC.REPEAT_FACTOR,
        ("A04", "F2", "agu_addrmodes", "a04_same_object"),
        LC.REPEAT_MAX + 1)
    flags, _g, reason = LC.resolve_cell(cell, seed=1)
    assert flags is None and "repeat-factor-over-cap" in reason

    # 表里没有的 seed=-derived submodel：残表只留一个也要拒绝（不猜另一支）
    monkeypatch.delitem(
        LC.REPEAT_FACTOR, ("A04", "F2", "agu_addrmodes", "a04_same_page"))
    flags, _g, reason = LC.resolve_cell(cell, seed=2)
    assert flags is None and "repeat-factor-unmeasured" in reason


# ------------------- [6b] config/binary 同源（并发 session 漂移的响亮拒绝）
def test_census_refuses_config_newer_than_frozen_binary(tmp_path, monkeypatch):
    """census 必须与冻结二进制同源：带 measureEligible 的 config 直接拒绝。"""
    bad = tmp_path / "lsu_proxy_new.py"
    bad.write_text(
        "ap = CHAOSAddrPath(measureEligible=False)\n"
        "if args.chaos_repeat > 131072: p.error('x')\n")
    monkeypatch.setenv("LSU_PROXY_CONFIG", str(bad))
    with pytest.raises(SystemExit) as exc:
        RC.config_proxy(tmp_path)
    assert "measureEligible" in str(exc.value)
    # 与冻结二进制同源的 config（HEAD pin）可用且不含该参数
    monkeypatch.delenv("LSU_PROXY_CONFIG")
    p = RC.config_proxy(tmp_path)
    txt = p.read_text()
    assert "measureEligible" not in txt
    # [R6-A4] the config/workload cap was raised to 131072 after the filtered
    # census; the pinned HEAD config must carry that same explicitly recorded
    # bound (still finite, still a loud p.error above it).
    assert "chaos_repeat must be in 1.." in txt
    assert "CHAOS_REPEAT_CAP = 131072" in txt


# ---------------------------------------- [7] REPEAT_MAX 有实测上界依据
def test_repeat_max_basis_is_measured():
    basis = LC.REPEAT_MAX_BASIS
    assert basis["measured_worst_run_s"] > 0
    assert basis["binary_sha256"]
    assert basis["basis"].strip()
    # 上界必须覆盖实测需要的最大 R（否则那个样本只能响亮 BLOCKED）
    summary = RC.load_census_summary()
    if summary:
        for key, rec in summary.items():
            if rec.get("blocked"):
                continue
            assert rec["R"] <= LC.REPEAT_MAX, (key, rec["R"], LC.REPEAT_MAX)
    assert LC.REPEAT_MAX >= 4096


# ------------- [7b] 冻结二进制的首火位与 LCG 推导逐位一致（真实证据）
def test_frozen_binary_first_fire_matches_lcg():
    """A01-F2-W9 seed1：注入日志的中途 FUNNEL 行给出真实发射点。

    冻结二进制在 eligible=106,412 处发射（injected=1），与
    chaos_lsu_trigger.hh 的 warmup(0)+50000+lcg(1)%100000 独立推导值
    完全相同 —— 证明"只改 repeat，不改 F2 随机序列"。
    """
    ilog = (RC.default_outroot() / "r6_a4_census_A01-F2-W9_r1" /
            "addrpath_injections.log")
    assert ilog.exists(), ("census 证据缺失：%s（先跑 "
                           "tools/lsu_repeat_census.py）" % ilog)
    funnels = [(int(a), int(b), int(c))
               for a, b, c in RC._FUNNEL_RE.findall(
                   ilog.read_text(errors="replace"))]
    fired = [f for f in funnels if f[2] == 1]
    assert fired, funnels
    assert fired[0][1] == RC.first_fire("F2", 1) == 106412, fired[0]
    # seed2/seed3 的推导值（单测 [1] 已钉）不同，证明确实按 seed 变化
    assert len({RC.first_fire("F2", s) for s in (1, 2, 3)}) == 3


# ----------------------------- [8] 真实运行：足够 repeat -> injected=1（慢）
@pytest.mark.slow
def test_real_run_injects_at_R_with_three_way_count_consistency():
    """真实 gem5：repeat=R 时 F2 首火被真实跨越，三方计数一致。

    读取 census 落盘的 summary（由 tools/lsu_repeat_census.py 生成），
    以其中的 E1/delta/R 真实重跑一次；summary 缺失 = 证据缺失 = 失败
    （不跳过：跳过会把"没测"伪装成"通过"）。
    """
    key = "A05-d-W3"
    summary = RC.load_census_summary()
    assert summary is not None, (
        "census summary 缺失：先运行 tools/lsu_repeat_census.py 生成 "
        "runs/lsu/r6_a4_census_*/summary.json")
    assert key in summary, sorted(summary)
    rec = summary[key]
    assert not rec.get("blocked"), rec
    R = rec["R"]
    assert R <= LC.REPEAT_MAX
    # R 的最小性：覆盖 1.2×max，但 R-1 不覆盖
    assert rec["E1"] + (R - 1) * rec["delta"] >= 1.2 * rec["max_first_fire"]
    assert rec["E1"] + (R - 2) * rec["delta"] < 1.2 * rec["max_first_fire"]

    out = RC.run_key_once(key, R, RC.default_outroot() / "verify_injected")
    trig = RC.parse_trigger_summary(
        (out["outdir"] / "run.out").read_text(errors="replace"))
    assert trig is not None and trig["tier"] == "F2"
    assert trig["injected"] == 1, trig
    assert trig["eligible"] >= RC.first_fire("F2", rec["seed"]), trig
    assert out["exit_code"] == 0, out

    # 三方一致：run.out / addrpath_injections.log FUNNEL / campaign 分类
    log_text = (out["outdir"] / "addrpath_injections.log").read_text(
        errors="replace")
    funnel = RC.parse_funnel(log_text)
    assert funnel == (trig["attempted"], trig["eligible"], 1), funnel
    assert out["campaign"]["injected"] == 1, out["campaign"]
    assert out["campaign"]["eligible"] == trig["eligible"]
    # 每趟都真实完成（不补行）
    assert out["iter_count"] == R, (out["iter_count"], R)
    # 证据里的二进制必须与 summary 所属批次记录的一致（同一批证据 = 同一
    # 二进制；census 时的冻结二进制是 FROZEN_SHA=c52ef225…）。
    meta = json.loads(
        (RC.default_outroot() / "batch_manifest.json").read_text())
    assert out["binary_sha256"] == meta["binary_sha256"], (
        out["binary_sha256"], meta["binary_sha256"])
    assert out["workload_sha256"] == meta.get(
        "workloads_sha256", {}).get("agu_addrmodes", out["workload_sha256"])


def main():
    """脚本式入口：pytest 之外也能自跑（慢测试照跑，不跳过）。"""
    rc = pytest.main([str(Path(__file__)), "-q", "-p", "no:cacheprovider"])
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
