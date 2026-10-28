#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-A2] 同源 repeat 载体契约（repeat_factor + ITER oracle）。

背景：F1/F2/F4 的首火位置在 eligible 序数空间（F1 max=1,290,806；
F2/F4 max=140,806），而短探针每次只产生 ~2.6-3.2k eligible。用户工作令
授权“重复执行同一工作负载”扩展 eligible 流，但必须：
  * workload ID 不变（同源 probe_once + 外层 repeat，不换载体）；
  * 每迭代独立校验 golden（ITER:<n>:<hex> 行）；
  * manifest 记录 repeat_factor；
  * 频率间隔/seed/trigger 算法不变；
  * 有界（REPEAT_MAX），未知组合响亮拒绝而不是猜。

本测试钉死：
  1. 实测 repeat 表（census 2026-10-28）与上限；
  2. F0/F5/F6 不 repeat；未 census 的 F1/F2/F4 返回 None（上游拒绝）；
  3. ITER 行解析（完成几趟就是几趟，缺行不补）；
  4. resolve_cell 对 F1/F2/F4 真的把 --chaos_repeat 放进 gem5 flags。

用法：python3 tests/test_lsu_r6a2_repeat.py （退出码 0=全 PASS）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import lsu_campaign as LC  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("   <- " + detail if not cond else ""))
    if not cond:
        FAILED.append(name)


def main():
    print("[1] repeat 上限与实测表")
    # [R6-A4] 上限由实测过滤后流决定：A08-a W5 需要 84,418（旧 4,096 会
    # 静默 clamp）。131,072 是有界且实测可完成的（每趟 7.5–31 ms ⇒ ≤44 min
    # /样本），依据记录在 lsu_campaign.REPEAT_MAX_BASIS；不是放宽为无限。
    check("REPEAT_MAX == 131072", LC.REPEAT_MAX == 131072,
          str(LC.REPEAT_MAX))
    check("REPEAT_MAX covers max measured R",
          LC.REPEAT_MAX >= max(v for v in LC.REPEAT_FACTOR.values()),
          str(LC.REPEAT_MAX))
    check("REPEAT_MAX_BASIS recorded",
          isinstance(LC.REPEAT_MAX_BASIS, dict)
          and bool(LC.REPEAT_MAX_BASIS.get("basis")), str(
              LC.REPEAT_MAX_BASIS))
    # [R6-A4 2026-10-28] 键扩为 (model,freq,binary,submodel)，repeat_factor_for
    # 在**无 seed** 时返回各 submodel 的保守最大值（生产路径总是传 seed）。
    # 因此 A04/A06 的旧 3 元组期望值随子模型重 census 而更新：
    #   A04 mini: max(a04_same_object=375, a04_same_page=212) = 375
    #   A06 agu : max(a06_size=1123, a06_mask=1123)          = 1123
    #   A06 sq  : max(1295, 1295)                            = 1295
    # A01/A02 的既有合格值（4023/434）保持不变（用户工作令）。
    expect = {
        ("A01", "F1", "agu_addrmodes"): 4023,
        ("A01", "F1", "gap_bfs"): 6,
        ("A01", "F2", "agu_addrmodes"): 434,
        ("A04", "F2", "mini_check"): 375,
        ("A07", "F4", "sq_forward"): 934,
        ("A06", "F2", "agu_addrmodes"): 1123,
        ("A06", "F2", "sq_forward"): 1295,
    }
    for key, val in expect.items():
        got = LC.repeat_factor_for(*key)
        check(f"{key} == {val}", got == val, str(got))

    print("[2] 非间隔 tier 不 repeat；未 census 的间隔 tier 响亮返回 None")
    check("F0 -> 1", LC.repeat_factor_for("A01", "F0", "agu_addrmodes") == 1)
    check("F5 -> 1", LC.repeat_factor_for("A03", "F5", "agu_addrmodes") == 1)
    check("F6 -> 1", LC.repeat_factor_for("A04", "F6", "agu_addrmodes") == 1)
    check("unknown F2 -> None",
          LC.repeat_factor_for("A01", "F2", "not_a_workload") is None)

    print("[3] ITER 行独立解析（缺行不补）")
    text = ("ITER:0:728e604ffcec539d\n"
            "ITER:1:728e604ffcec539d\n"
            "728e604ffcec539d\n")
    it = LC.parse_iter_checksums(text)
    check("两条 ITER", it == [(0, "728e604ffcec539d"),
                              (1, "728e604ffcec539d")], str(it))
    check("裸 checksum 不算 ITER",
          LC.parse_iter_checksums("deadbeefdeadbeef\n") == [])
    check("截断在第 2 趟 -> 只有 1 条",
          LC.parse_iter_checksums("ITER:0:728e604ffcec539d\n") ==
          [(0, "728e604ffcec539d")])

    print("[4] resolve_cell 把 repeat 放进 gem5 flags（F1/F2/F4）")
    def resolve(rid, model, freq, workload):
        cell = [""] * 12
        cell[LC.COL_RUNID] = rid
        cell[LC.COL_MODEL] = model
        cell[LC.COL_UNIT] = "AGU"
        cell[LC.COL_FREQ] = freq
        cell[LC.COL_WORKLOAD] = workload
        return LC.resolve_cell(cell)

    flags, _g, _b = resolve("A01-F1-W3", "A01", "F1", "AGU-AddrModes")
    check("A01-F1-W3 flags 非空", flags is not None, str(_g))
    if flags:
        i = flags.index("--chaos_repeat") if "--chaos_repeat" in flags else -1
        check("A01-F1-W3 --chaos_repeat 4023",
              i >= 0 and flags[i + 1] == "4023", str(flags[-4:]))
    flags0, _g, _b = resolve("A01-F0-W3", "A01", "F0", "AGU-AddrModes")
    check("A01-F0-W3 不带 --chaos_repeat",
          flags0 is not None and "--chaos_repeat" not in flags0,
          str(flags0 and flags0[-4:]))

    if FAILED:
        print(f"R6-A2 REPEAT TEST: {len(FAILED)} FAILURE(S)")
        return 1
    print("R6-A2 REPEAT TEST: ALL PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
