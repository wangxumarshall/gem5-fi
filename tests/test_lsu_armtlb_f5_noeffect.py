# tests/test_lsu_armtlb_f5_noeffect.py
"""R6-F5-NOEFFECT 合同测试（纯离线，不跑 gem5）。

钉住：F5 的四方计数必须一致 ——
  trigger summary 的 injected / no_effect / fires，
  CHAOS_LSU_NOEFFECT 的 effective_injected / no_effect / fires，
  armtlb_injections.log 中 Site: arm_tlb_lookup_hit 且 effective: 1 的行数，
  stats.txt 的 board.chaos_armtlb.numFaultsInjected。
且 fires == injected + no_effect 必须成立。
"""
import re, textwrap, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def assert_f5_noeffect_consistency(outdir):
    """返回违规字符串列表（空 = 通过）。"""
    outdir = Path(outdir)
    bad = []
    td = None
    for cand in sorted(outdir.rglob("stats.txt")):
        if cand.stat().st_size > 0:
            td = cand.parent
            break
    if td is None:
        return ["no non-empty stats.txt found"]
    stdout = (td / "run.out").read_text(errors="replace") if (td / "run.out").exists() else ""

    def last(pat):
        m = re.findall(pat, stdout)
        return m[-1] if m else None

    trig = last(r"CHAOS_LSU_TRIGGER:\s*injector=(\S+)\s+tier=F(\d+)\s+attempted=(\d+)\s+"
                r"eligible=(\d+)\s+injected=(\d+).*?fires=(\d+)\s+no_effect=(\d+)")
    noeff = last(r"CHAOS_LSU_NOEFFECT:\s*injector=(\S+)\s+tier=F(\d+)\s+requested=(\S+)\s+"
                 r"effective=(\S+)\s+attempted=(\d+)\s+eligible=(\d+)\s+fires=(\d+)\s+"
                 r"effective_injected=(\d+)\s+no_effect=(\d+)")
    if trig is None:
        return ["CHAOS_LSU_TRIGGER line with fires/no_effect not found in run.out"]
    if noeff is None:
        return ["CHAOS_LSU_NOEFFECT line not found in run.out"]

    t_inj, t_fires, t_noeff = int(trig[4]), int(trig[5]), int(trig[6])
    n_fires, n_eff, n_noeff, n_req, n_efftier = int(noeff[6]), int(noeff[7]), int(noeff[8]), noeff[2], noeff[3]

    logf = td / "armtlb_injections.log"
    logged = 0
    if logf.exists():
        for line in logf.open(errors="replace"):
            if "Site: arm_tlb_lookup_hit" in line and "effective: 1" in line:
                logged += 1
    else:
        bad.append("armtlb_injections.log missing")

    stats = None
    m = re.search(r"board\.chaos_armtlb\.numFaultsInjected\s+(\d+)", (td / "stats.txt").read_text(errors="replace"))
    if m:
        stats = int(m.group(1))
    else:
        bad.append("stats.txt missing board.chaos_armtlb.numFaultsInjected")

    if t_fires != t_inj + t_noeff:
        bad.append(f"trigger: fires({t_fires}) != injected({t_inj}) + no_effect({t_noeff})")
    if n_fires != n_eff + n_noeff:
        bad.append(f"noeffect: fires({n_fires}) != effective_injected({n_eff}) + no_effect({n_noeff})")
    for name, val in (("trigger.fires", t_fires), ("noeffect.fires", n_fires)):
        if val != t_fires:
            bad.append(f"{name} disagrees with trigger.fires={t_fires}")
    if t_inj != n_eff:
        bad.append(f"trigger.injected({t_inj}) != noeffect.effective_injected({n_eff})")
    if t_noeff != n_noeff:
        bad.append(f"trigger.no_effect({t_noeff}) != noeffect.no_effect({n_noeff})")
    if n_eff != logged:
        bad.append(f"effective_injected({n_eff}) != injection-log effective rows({logged})")
    if stats is not None and stats != n_eff:
        bad.append(f"stats.numFaultsInjected({stats}) != effective_injected({n_eff})")
    if n_req != n_efftier:
        bad.append(f"requested tier({n_req}) != effective tier({n_efftier})")
    return bad


def test_synthetic_consistent():
    """合成一致样本：必须 0 违规。"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "T03-F5-W4" / "seed1"
        p.mkdir(parents=True)
        (p / "run.out").write_text(textwrap.dedent("""\
            CHAOS_LSU_TIER_CAP: requested=F5 effective=F5 lookup_tier_enabled=1
            CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F5 attempted=900 eligible=900 injected=3 first_eligible_tick=1 last_eligible_tick=9 fires=900 no_effect=897 (activated=W3-L0-layer)
            CHAOS_LSU_NOEFFECT: injector=CHAOSArmTLB tier=F5 requested=F5 effective=F5 attempted=900 eligible=900 fires=900 effective_injected=3 no_effect=897 first_no_effect_tick=2 last_no_effect_tick=900
            """))
        (p / "armtlb_injections.log").write_text("".join(
            f"Tick: {i}, Site: arm_tlb_lookup_hit, VA: 0x1, old_pfn: 0x2, new_pfn: 0x1, "
            f"FaultType: stuck_at_zero, Mask: 0x1, effective: 1\n" for i in range(3)))
        (p / "stats.txt").write_text("board.chaos_armtlb.numFaultsInjected 3\n")
        assert assert_f5_noeffect_consistency(d) == []


def test_synthetic_inconsistent_is_loud():
    """人为制造不一致：必须被点名，绝不静默通过。"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "T03-F5-W4" / "seed1"
        p.mkdir(parents=True)
        (p / "run.out").write_text(textwrap.dedent("""\
            CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F5 attempted=900 eligible=900 injected=5 first_eligible_tick=1 last_eligible_tick=9 fires=900 no_effect=897 (activated=W3-L0-layer)
            CHAOS_LSU_NOEFFECT: injector=CHAOSArmTLB tier=F5 requested=F5 effective=F5 attempted=900 eligible=900 fires=900 effective_injected=3 no_effect=897 first_no_effect_tick=2 last_no_effect_tick=900
            """))
        (p / "armtlb_injections.log").write_text("")
        (p / "stats.txt").write_text("board.chaos_armtlb.numFaultsInjected 3\n")
        bad = assert_f5_noeffect_consistency(d)
        assert bad, "inconsistent counts must be reported"
        assert any("fires" in b or "injected" in b for b in bad)


if __name__ == "__main__":
    test_synthetic_consistent()
    test_synthetic_inconsistent_is_loud()
    print("test_lsu_armtlb_f5_noeffect: ALL PASS")
