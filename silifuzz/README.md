# silifuzz — SiliFuzz (Fuzzing CPUs by Proxy) 的 ARM64 规格复现

本目录依据 `docs/papers/ref/silifuzz.pdf`（K. Serebryany et al.,
*SiliFuzz: Fuzzing CPUs by proxy*, 2021）第 2 节，在当前可用条件下复现
SiliFuzz 的完整流水线。目标架构为 ARM64（仓库 `AGENTS.md` 约束），
运行平台为 aarch64 openEuler / Kunpeng 920。

论文条款到代码的逐条映射见 [`docs/paper-mapping.md`](docs/paper-mapping.md)，
真实测量见 [`docs/measurements.md`](docs/measurements.md)，与原文的差距见
[`docs/limitations.md`](docs/limitations.md)，与当前 sdcfuzz 项目的核心差异见
[`docs/vs-sdcfuzz.md`](docs/vs-sdcfuzz.md)。2026-11-14 的独立复核（重构建、
55 项测试、12,211,456 次 sweep、4 核窗口）见
[`docs/reproduction-2026-11-14.md`](docs/reproduction-2026-11-14.md)。

## 组件

| 论文 | 本目录 |
| --- | --- |
| Snapshot（§2.2） | `include/silifuzz/snapshot.hh`、`src/snapshot.cc`、`tools/sfsnapshot.py` |
| Player（§2.3，driver + harness 双进程） | `src/player.cc`、`src/harness.cc`、`bin/sf_player` |
| 反汇编器代理（XED） | `proxies/capstone_fuzz.cc`（Capstone ARM64） |
| ifuzz 生成器 | `tools/ifuzzgen`（syzkaller ifuzz arm64） |
| 模拟器代理（Unicorn） | `proxies/unicorn_fuzz.cc`（Unicorn ARM64） |
| 端态修复（§2.4.4） | `src/sf_fix.cc` |
| Checker（§2.5） | `src/sf_checker.cc` |
| 机群窗口与反馈闭环（§2.5.2/§2.6） | `tools/fleet.py`、`tools/quarantine.py` |
| 模板配对语料（本项目新增） | `tools/pairgen.py` |

## 构建

依赖：Linux aarch64、g++/clang++、Python 3、Go（仅 ifuzz）。

```bash
cd silifuzz
./scripts/build_deps.sh      # 拉取并插桩构建 Capstone 5.0.7 / Unicorn 2.1.4（需要网络）
make -j
```

如果 `third_party/` 已存在（本机已构建），`make` 直接使用；`make clean` 不会
删除 `third_party/`。

## 快速开始

```bash
make test        # 格式/跨语言/player/e2e/fleet 全部真实测试
```

生成语料 — 修复 — 回放：

```bash
./bin/ifuzzgen -n 1000 -seed 1 -out work/cand/ifuzz
./bin/sf_fix --in work/cand/ifuzz --out work/corpus/demo --source ifuzz \
  --jobs 8 --spread
./bin/sf_player --corpus work/corpus/demo --core 0 --limit 200
```

128 核采样检查（论文的 50/1000 批处理）：

```bash
./bin/sf_checker --corpus work/corpus --cores 0-127 --seconds 120 \
  --out work/check
```

4 核 / 2 分钟机群窗口（轮转覆盖 128 核）：

```bash
python3 tools/fleet.py --corpus work/corpus --db work/fleet/results.db \
  --out-root work/fleet/runs --cores 0-127 --window-cores 4 \
  --window-seconds 120 --windows 4
```

隔离/复测闭环（合成注入，**不代表真实硬件缺陷**）：

```bash
./bin/sf_checker --corpus work/corpus --cores 4-5 --seconds 10 \
  --inject flip:0:0:1:0 --out work/inject
python3 tools/quarantine.py --db work/fleet/results.db \
  --inject flip:0:0:1:0 --repeat 3
```

完整复现（生成 + 修复 + 128 核 sweep + 4 核窗口）：

```bash
FUZZ_SECONDS=180 ./scripts/run_scale.sh
```

## 实测摘要（详见 docs/measurements.md）

- 语料：95,402 条基线（ifuzz 92,652 / Capstone 1,600 / Unicorn 1,150，
  约 203 MiB（212.6 MB））；2026-11-14 规模复核新建 **505,020 条**（约 50 万，全部
  ifuzz，约 1.05 GiB）。
- 单核回放约 5,400 条/秒；128 核 50/1000 sampled 99,835 次/秒；128 核全量
  sweep 274,516 次/秒；4 核 / 2 分钟窗口约 4.3 万次/秒。
- 95k 语料：12,211,456 次 sweep、5,160,039 次 4 核窗口，均 0 不匹配；
  505k 语料：**64,642,560 次 sweep、5,168,126 次 4 核窗口，均 0 不匹配**。
- 没有发现真实硬件缺陷；检测/隔离闭环用合成注入验证。

## 模板配对语料（2026-11-23）

两套方法，别混用：

- **原文口径** `tools/pairgen_paper.py`：生成端零定向（ifuzz 无过滤 + Capstone/Unicorn 代理 +
  原样 fixer），只在事后按**代理覆盖区域**选流（`tools/covfingerprint/` 读回 SanitizerCoverage
  计数器）。产物 [`evidence/pairs-paper-2026-11-23/`](evidence/pairs-paper-2026-11-23/)，
  方法与上限见 [`docs/pairs-paper-2026-11-23.md`](docs/pairs-paper-2026-11-23.md)。
  实测上限：满纯度最长流只有 3–4 条指令，覆盖率 0.13–0.50；o2 的 `b.ne` 在 95,475 条语料里
  0 次，`dup` 各 15 次，v5 的 LSE 只有 3 种各 1 次（另 4 种 0 次）。
- **定向扩展** `tools/pairgen.py`：给生成器加约束（词表、补表、按类均衡、寄存器分区），
  能拿到"类覆盖 100%"的配对，但分布不是 SiliFuzz，只能作为对照。

`tools/pairgen.py` 为 `sdcfuzz/upstream/seeds/` 的 20 个微架构模板各生成 **1 条**
SiliFuzz 指令流，并走完 `ifuzz → sf_fix → sf_player → sf_checker → fleet` 全流水线：

- 判据是 **ifuzz 编码类**（`arm64.ParseInsn`），不是 objdump 助记符；
  模板的每个指令类都必须在流里出现（覆盖率 1.0），且流不引入模板外的类。
- 每条流的最终 `.sfs` 都被重新审计：代码段逐字节等于被选候选，端态 PC 落在末尾
  `BRK`（`SIGTRAP`），即整条流被执行完；中途夭折的候选一律丢弃换下一个。
- 机群校验：128 核 sweep 2560 次、50/1000 采样 764,152 次、4 核窗口 2×60 s，
  全部 0 不匹配。

产物与逐配对证据见 [`evidence/pairs-2026-11-23/`](evidence/pairs-2026-11-23/)，
方法与边界见 [`docs/pairs-2026-11-23.md`](docs/pairs-2026-11-23.md)。
`tools/ifuzzgen` 新增 `-lse` / `-branch-ext` / `-vec-ext` / `-words` /
`-balance-classes` 五个**默认关闭**的开关；不加开关时指令集与上游逐字节一致。

复现：

```bash
python3 tools/pairgen.py analyze  --work work/pairs-20261123 --variants 8 --seed 1
python3 tools/pairgen.py generate --work work/pairs-20261123 --n 400 --keep 200 --seed 1
python3 tools/pairgen.py fix      --work work/pairs-20261123
python3 tools/pairgen.py verify   --work work/pairs-20261123 --cores 0-127
python3 tools/pairgen.py report   --work work/pairs-20261123 --copy-to <dir>
```

## 目录

```text
include/ src/        快照格式、player、fixer、checker
proxies/             Capstone/Unicorn libFuzzer 目标
tools/               ifuzzgen、Python 快照库、fleet、quarantine、统计
tests/               单元、跨语言、player、端到端、fleet 测试
scripts/             build_deps.sh、run_scale.sh
docs/                paper-mapping / measurements / limitations / vs-sdcfuzz /
                     reproduction-2026-11-14
evidence/            真实运行日志与汇总 JSON（数字来源）
third_party/         构建产物（gitignore，脚本可重建）
work/                corpus / 中间语料（gitignore）
```

## 许可

`tools/ifuzzgen/ifuzz` 来自 syzkaller，Apache-2.0，见
`tools/ifuzzgen/LICENSE.syzkaller`。其余代码为本仓库新增。
