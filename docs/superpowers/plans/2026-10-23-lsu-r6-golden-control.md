# [LSU][MDSPEC][R6-GOLDEN] 阴性/黄金对照可用且可验证（L6-v2）

Lane L6-v2 · worktree `.claude/worktrees/r6-pilot` · branch `r6-pilot` · base `97f74786`
Owner 路径：`tools/lsu_gem5_bin.py`、`tools/lsu_r6_golden_control.py`、
`tests/test_lsu_r6_golden_control.py`、`tools/lsu_runner.py`、`tools/lsu_unit_pilot.py`、
outdir `runs/lsu/r6_golden_*`。**不改 C++，不改其他 `tools/lsu_*.py`。**

## 问题（实测，不是推断）

1. **错二进制**：golden 路径未走 `$LSU_GEM5_BIN`，回了主 checkout 的
   `/home/sdc/gem5-fi-ding/CHAOS/gem5/build/ARM/gem5.opt`（另一条 track）。
   实录 `runs/lsu/r6_tlb_verify/golden/run.log`：
   `timeout: 无法运行命令 ".../CHAOS/gem5/build/ARM/gem5.opt": No such file or directory`
   → 对照从未运行，却可能被当成"控制组"证据。
   正确二进制：`.claude/worktrees/r6-tlb-hooks/CHAOS/gem5/build/ARM/gem5.opt`。
2. **截断即伪阴性**：`runs/lsu/r6_tlb_negative2/seed1/prop_evt.txt.gz` 238 B（仅表头），
   `gzip.open(...).read()` 抛
   `EOFError: Compressed file ended before the end-of-stream marker`
   —— 被杀 run 的"0 个 inj"必须与真阴性区分。

## 单元（一个提交 = 一个单元）

- [x] **T1 二进制解析唯一来源** `tools/lsu_gem5_bin.py`：`$LSU_GEM5_BIN` → 本 checkout
      `CHAOS/gem5/build/ARM/gem5.opt`；缺则 `SystemExit`；**绝不回落主树** `build/ARM/gem5.opt`。
- [x] **T2 对照入口** `tools/lsu_r6_golden_control.py`：命令形状与 R6 采样一致；判据 =
      `rc` 干净 ∧ `stats.txt` 非空 ∧ `prop_evt` 流完整（含 gzip 收尾标记）∧ 0 个
      `inj`/`chain_end`。二进制按 `--workdir` 所属 checkout 解析（避免"配置取自 A、二进制取自 B"）。
- [x] **T3 SE 执行链去硬编码** `tools/lsu_runner.py::g5_path()` /
      `tools/lsu_unit_pilot.py` 统一委托 `lsu_gem5_bin`，不再出现裸 `REPO/"build/ARM/gem5.opt"`。
- [x] **T4 契约测试** `tests/test_lsu_r6_golden_control.py`：断言 golden 路径**无主树绝对路径**
      代码常量（docstring 纪实引用不算）、SE 链**无裸 `build/ARM/gem5.opt`** 且走统一解析器、
      判据（0 inj → PASS）、截断流必须识别且不得判"完成"。
- [x] **T5 真机验证**：`runs/lsu/r6_golden_verify`（未注入）跑完 → 判定 PASS。

## 验证命令 + 真实输出

```
$ python3 tests/test_lsu_r6_golden_control.py        # → ALL PASS, exit 0
$ python3 -m py_compile tools/lsu_gem5_bin.py tools/lsu_r6_golden_control.py \
      tools/lsu_runner.py tools/lsu_unit_pilot.py tests/test_lsu_r6_golden_control.py
PY_COMPILE_OK
$ env -u LSU_GEM5_BIN python3 tools/lsu_r6_golden_control.py --dry-run \
      --workdir <r6-tlb-hooks> ...                   # → binary = r6-tlb-hooks 构建 (source=worktree-default)
$ LSU_GEM5_BIN=<r6-tlb-hooks>/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_r6_golden_control.py --dry-run ...
      # → binary = r6-tlb-hooks 构建 (source=LSU_GEM5_BIN)
$ timeout 300 python3 tests/test_lsu_fs_infra.py      # 回归：ALL PASS, exit 0
```

对照真机（`runs/lsu/r6_golden_verify/seed1`，PID 2817828，11:02:41→11:35，hostSeconds 1976.86）：

```
stream: present=True readable=True truncated=False
kind_counts: {}
completed: (True, 'stats.txt 非空且 prop_evt 流完整（含 gzip 收尾标记）')
verdict: PASS — no inj / chain_end — injection path proven inactive
stats.txt = 427088 B ；board.terminal: [tlb_probe.rcS] ... rounds ok=10/10
```

## 残余风险

- gem5 自身 `rc` 未落盘（启动方未保留 stdout 尾/`golden_run.log`）——"干净结束"由
  两条独立信号证明：gzip 收尾标记（仅 exit callback 写）+ 仅退出时才写的 `stats.txt` 非空
  （被杀的 run 两者皆无，见 negative2）。
- `tools/lsu_campaign.py::G5` 默认仍是 repo 根 `build/ARM/gem5.opt`（**campaign/注入路径**，
  非 golden 路径）；缺 `LSU_GEM5_BIN` 时**响亮 SystemExit**，不静默跑错二进制。不在本 lane 范围。
