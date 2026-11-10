# 实测记录

日期：2026-11-10（Asia/Shanghai）
所有数字均来自 `silifuzz/evidence/` 与 `work/` 下真实命令输出；命令附在每节。
本轮没有发现真实硬件缺陷，检测闭环使用合成注入验证（明确标注 synthetic）。

## 0. 环境

```text
CPU          : HiSilicon Kunpeng-920, 128 CPUs, 1 thread/core, 4 NUMA nodes
               (32 cores each), 2.6 GHz max
OS           : openEuler 24.03 SP4, kernel 6.6.0-159.4.3.154.oe2403sp4.aarch64
Compiler     : g++ 12.3.1, clang 17.0.6 (libFuzzer)
Other        : Python 3.11.6, Go 1.24.2; 30 GiB RAM
Corpus disk  : work/corpus 约 213 MiB
```

`lscpu`、`uname -a` 的完整输出见本文件末尾“采集命令”。

## 1. 语料

```bash
python3 tools/corpus_stats.py work/corpus evidence/corpus-stats.json
```

| 项 | 值 |
| --- | --- |
| snapshot 总数 | **95,402** |
| 磁盘占用 | 212,647,273 B（平均 2,229 B/条） |
| 来源 ifuzz | 92,652 |
| 来源 Capstone（解码器代理） | 1,600 |
| 来源 Unicorn（模拟器代理） | 1,150 |
| 代码长度 | min 8 / p50 68 / p90 120 / max 132 字节 |
| 映射数 | 7 页：95,358；8 页：44 |
| 端态信号 | SIGILL 51,461；SIGSEGV 31,070；SIGTRAP 8,641；SIGBUS 4,230 |

说明：SIGILL 占比高是因为 ifuzz 的 ARM64 指令表会生成未分配编码，且论文明确
要求保留非法指令（附录 B）；SIGTRAP 是正常执行到 `BRK #0` 的快照。

生成命令：

```bash
./bin/ifuzzgen -n 100000 -seed 2026 -min-insns 1 -max-insns 32 \
  -out work/cand/ifuzz-big
./bin/capstone_fuzz -max_total_time=180 -max_len=64 work/corpus-proxy/capstone
./bin/unicorn_fuzz  -max_total_time=240 -max_len=128 work/corpus-proxy/unicorn
```

## 2. 修复（§2.4.4）

```bash
./bin/sf_fix --in work/cand/ifuzz-big --out work/corpus/ifuzz --source ifuzz \
  --jobs 32 --spread --ref-cores 0,32,64,96 --stats evidence/ifuzz-fix.json
```

| 来源 | 候选 | 收录 | 拒绝原因 | 耗时 | 执行次数 | 速率 |
| --- | --- | --- | --- | --- | --- | --- |
| ifuzz | 97,952 | 92,652 | syscall 3,928；timeout 1,372 | 132.4 s | 557,311 | 738 候选/s |
| Capstone | 1,601 | 1,600 | syscall 1 | 0.51 s | 9,607 | 3,157 候选/s |
| Unicorn | 1,151 | 1,150 | size 1 | 0.35 s | 6,910 | 3,285 候选/s |

每条候选平均 6 次执行：映射发现（≥1）+ 同核确定性（3 次）+ 4 个 NUMA 节点
各 1 次。未出现 `nondeterministic` 或 `multi_state` 拒绝（说明所选候选在
4 个参考核上端态一致）；`timeout` 为超过 3 秒的快照。

## 3. 回放吞吐与全量 sweep

单核回放：

```bash
time ./bin/sf_player --corpus work/corpus/ifuzz --core 0 --limit 2000
# real 0m0.390s -> 5,128 snapshots/s（完整 92,652 条 ifuzz 语料）
```

128 核全量 sweep（每条语料在每个核执行一次）：

```bash
./bin/sf_checker --corpus work/corpus --cores 0-127 --seconds 300 \
  --mode sweep --out evidence/sweep
```

| 指标 | 值 |
| --- | --- |
| 执行次数 | **12,211,456**（95,402 × 128，精确相等） |
| 墙钟时间 | 45.473 s |
| 吞吐 | **268,540 次/秒** |
| 不匹配 / 超时 / 错误 | **0 / 0 / 0** |
| 语料读取 | 95,402 次，212,647,273 B |
| I/O 摊薄 | **17.4 B/次执行**（每条快照 2,229 B，跨 128 核复用 → 128×） |

`evidence/sweep/summary.json` 为原始输出，`mismatches.jsonl` 为空。

采样模式（论文 50/1000 批处理）128 核 6 秒实测（9,444 条子语料）：

```bash
./bin/sf_checker --corpus work/corpus-ifuzz-v2 --cores 0-127 --seconds 6 \
  --out work/chk-v6
# executions=601128, exec_per_s=100992.9, mismatches=0, errors=0
# bytes_read/execution = 111.6（快照 2,229 B -> 约 20x 摊薄）
```

## 4. 4 核 / 2 分钟机群窗口（§2.5.2）

论文参数：4 核（2 个 HT 对；本机无 SMT，取 4 个物理核）、最多 2 分钟、
窗口轮转覆盖整机。

```bash
python3 tools/fleet.py --corpus work/corpus --db work/fleet/results.db \
  --out-root work/fleet/runs --cores 0-127 --window-cores 4 \
  --window-seconds 120 --windows 4
```

| 窗口 | 核 | 执行次数 | 速率 | 不匹配 |
| --- | --- | --- | --- | --- |
| 1 | 0-3 | 5,191,935 | 43,243.4/s | 0 |
| 2 | 4-7 | 5,143,335 | 42,838.5/s | 0 |
| 3 | 8-11 | 5,199,733 | 43,308.3/s | 0 |
| 4 | 12-15 | 5,048,476 | 42,044.0/s | 0 |

4 个窗口共 **20,583,479** 次执行、0 不匹配（`work/fleet/results.db` 的
`runs` 表；`evidence/fleet.log`）。

## 5. 合成缺陷的检出与隔离

在整机语料上用 4 核窗口注入“x0 bit0 每次翻转”（**synthetic**，不是硬件缺陷）：

```bash
./bin/sf_checker --corpus work/corpus --cores 4-7 --seconds 3 \
  --inject flip:0:0:1:0 --out work/inject-full
```

结果：**124,047 次执行、124,047 次不匹配**（100%，注入直接改写返回的 x0），
速率 40,524/s。随后：

```bash
python3 tools/quarantine.py --db work/fleet/results.db \
  --inject flip:0:0:1:0 --repeat 3 --found work/fleet/found
```

隔离器按 (snapshot, core) 分组、对每组独立复测 3 次，全部复现才 `confirmed`。
在 290 条 e2e 语料上实测 **580 组、580 组确认**（`tests/test_fleet.sh` 输出）。
整机 95,402 条的合成窗口产生 124,047 个不匹配，最多 124,047 个
(snapshot, core) 组；逐组起进程复测的成本过高，本轮没有对整机语料执行
quarantine，只在小语料上验证了闭环。

## 6. 一次 `pstate` 噪声观察与处理

第一次全量 sweep 报告 4 次 `pstate` 差异（12,211,456 次中 4 次），第二次
12,211,456 次中 2 次，`actual_pstate=0x1000`（bit 12，SSBS，内核管理的
推测执行缓解位），全部无法在单核 20 次复测中复现。快照代码在 EL0 只能写
NZCV，SSBS/PAN/SS 等位属于内核状态，因此比较改为只比较 NZCV（bits 28-31）；
修改后第三次全量 sweep 为 0 不匹配。该处理已写入
`docs/paper-mapping.md` 与 `docs/limitations.md`，不是“消除失败”。

## 7. 与论文 §3 的对照

| 论文陈述 | 本机 | 结论 |
| --- | --- | --- |
| 语料约 500,000 | 95,402 | 未达到数量级；代理 fuzz 时间与磁盘/会话预算限制 |
| 40% 仅 Unicorn/XED、20% 仅 ifuzz、40% 两者 | 未测 | 需要已知缺陷机器做归因；本机没有 |
| 45% findings 独有 | 无真实 findings | 不适用 |
| 70% 缺陷影响同一物理核的两个逻辑核 | 无 SMT | 不适用 |
| 50/1000 批处理摊薄 I/O | 111.6–242 B/次 vs 2,229 B/条 | 机制成立，约 10–20× |
| 4 核 / 2 分钟窗口 | 4 核 × 120 s × 4 窗口 | 机制成立，0 不匹配 |

## 8. 复现

```bash
cd silifuzz
./scripts/build_deps.sh          # 首次需要网络；本机已构建
make -j
FUZZ_SECONDS=180 ./scripts/run_scale.sh
```

## 9. 证据文件

```text
evidence/ifuzz-gen.log            ifuzz 生成输出
evidence/ifuzz-fix.json/.log      97,952 候选的修复统计
evidence/capstone-fix.json        Capstone 语料修复统计
evidence/unicorn-fix.json         Unicorn 语料修复统计
evidence/corpus-stats.json        语料统计
evidence/capstone-fuzz.log        解码器代理 libFuzzer 日志
evidence/unicorn-fuzz.log         模拟器代理 libFuzzer 日志
evidence/sweep/summary.json       128 核全量 sweep
evidence/sweep/mismatches.jsonl   空文件（0 不匹配）
evidence/fleet.log                4 核窗口日志
work/fleet/results.db             结果库（SQLite）
```

## 10. 采集命令

```bash
uname -a
lscpu
nproc
free -g
g++ --version | head -1
clang --version | head -1
go version
python3 -c 'import capstone, unicorn; print(capstone.__version__, unicorn.__version__)'
```
