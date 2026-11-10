# 上游 D13 完整性核查与本地同步

日期：2026-11-10
背景：此前本仓库的 `sdcfuzz/operand_heuristic.py` 是本地启发式，不能作为
D13 对照臂。用户要求严格按文档的 D13 口径，验证上游实现完整性并同步到本地。

## 单元

### 单元 1：原样同步上游 D13

- [x] 从上游 `sdcfuzz` 仓库（`707db35d`）复制:
  - `gem5_config/workloads/sdc_probe_workload_d13.c`
  - `gem5_config/workloads/sdc_probe_workload_random.c`（B 基线）
  - `LICENSE`（Apache-2.0）
  到 `sdcfuzz/upstream/d13/`，逐字节不改。
- [x] 记录 sha256、来源路径、上游重复副本（`seeds/gem5/...` 哈希一致）。
- [x] 新增 `README.md`，明确“这是上游 D13，不是本地启发式”。

### 单元 2：完整性核查与真实运行

- [x] 文档语义逐项映射到代码（随机候选/定向变异/`popcount(x^(x+1))`/
      纯随机保留/每轮重选/200 轮输出）。
- [x] `scripts/test-d13-upstream.sh`：
  - 校验 vendored 文件 sha256；
  - 交叉编译 D13 与 B；
  - 原生运行 golden：D13 `SUM=118831515424667458 CRC=dbc8bf2a`，
    B `SUM=10721424292087689827 CRC=6728fc4a`；
  - 两次 D13 输出一致（确定性）；
  - 原生 gem5 O3 运行 golden；
  - CHAOSReg 单次注入冒烟（`numFaultsInjected=1`）。
- [x] `tests/test_d13_upstream.py`：哈希、关键函数/变异片段、README 边界。
- [x] 额外用上游 `two_level_taishan.py --mode baseline` 在原生 gem5 上复现
      同一 golden（手工记录在验证文档）。

### 单元 3：文档与路线图

- [x] 新增 `docs/sdcfuzz/d13-upstream-verification.md`。
- [x] 更新 `docs/sdcfuzz/d13-baseline-reproduction.md`、`phase0-verification.md`
      与 `roadmap.yaml` 的 D13 证据。
- [x] 更新 `tests/test_sdcfuzz_operand_heuristic.py` 的 `d13` 别名，避免继续
      把本地启发式称作 D13。
- [x] 重新生成 `ROADMAP.md`/路线图 SVG/PNG。
- [x] 勾选本计划。

## 验证记录（真实输出）

```text
$ bash scripts/test-d13-upstream.sh
sha256 ok: sdc_probe_workload_d13.c
sha256 ok: sdc_probe_workload_random.c
sha256 ok: LICENSE
D13 native: SUM=118831515424667458 CRC=dbc8bf2a
D13 native determinism: pass
B native:   SUM=10721424292087689827 CRC=6728fc4a
gem5 O3:    SUM=118831515424667458 CRC=dbc8bf2a
FI smoke:   integer[29] bit_flip Mask=0x800, numFaultsInjected=1
D13 provenance, golden output, determinism, gem5 baseline and FI smoke passed
```

静态：

```text
$ python3 -m pytest tests/test_d13_upstream.py -q
3 passed
```

## 边界

- 只同步 D13 workload 与 B 基线，不同步上游完整 4×100 实验编排
  （`sim_sweep.py`/`two_level_taishan.py` 仍在外部仓库）。
- 单次 FI 冒烟这次是 Masked；不把它说成 SDC 检出率，4×100 统计仍以
  `docs/sdcfuzz/d13-baseline-reproduction.md` 为准。
- `roadmap.yaml` 的 `p0-d13` 仍记 `done-external`：代码已本地同步并实测，
  但完整 400 次实验证据仍是外部记录。
