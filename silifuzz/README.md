# silifuzz — SiliFuzz (Fuzzing CPUs by Proxy) 的 ARM64 规格复现

本目录依据 `docs/papers/ref/silifuzz.pdf`（K. Serebryany et al.,
*SiliFuzz: Fuzzing CPUs by proxy*, 2021）第 2 节，在当前可用条件下复现
SiliFuzz 的完整流水线。目标架构为 ARM64（仓库 `AGENTS.md` 约束），
运行平台为 aarch64 openEuler / Kunpeng 920。

论文条款到代码的逐条映射见 [`docs/paper-mapping.md`](docs/paper-mapping.md)，
真实测量见 [`docs/measurements.md`](docs/measurements.md)，与原文的差距见
[`docs/limitations.md`](docs/limitations.md)。

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

- 语料：95,402 条 snapshot（ifuzz 92,652 / Capstone 1,600 / Unicorn 1,150），
  约 213 MiB。
- 单核回放约 5,100 条/秒；128 核 sampled 约 10 万次/秒；128 核全量
  sweep 26.9 万次/秒；4 核 / 2 分钟窗口约 4.2–4.3 万次/秒。
- 128 核全量 sweep：95,402 × 128 = 12,211,456 次执行，45.5 秒，
  0 不匹配；4 个 4 核 / 2 分钟窗口共 20,583,479 次执行，0 不匹配。
- 没有发现真实硬件缺陷；检测/隔离闭环用合成注入验证。

## 目录

```text
include/ src/        快照格式、player、fixer、checker
proxies/             Capstone/Unicorn libFuzzer 目标
tools/               ifuzzgen、Python 快照库、fleet、quarantine、统计
tests/               单元、跨语言、player、端到端、fleet 测试
scripts/             build_deps.sh、run_scale.sh
docs/                paper-mapping / measurements / limitations
evidence/            真实运行日志与汇总 JSON（数字来源）
third_party/         构建产物（gitignore，脚本可重建）
work/                corpus / 中间语料（gitignore）
```

## 许可

`tools/ifuzzgen/ifuzz` 来自 syzkaller，Apache-2.0，见
`tools/ifuzzgen/LICENSE.syzkaller`。其余代码为本仓库新增。
