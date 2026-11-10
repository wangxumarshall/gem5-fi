# silifuzz — SiliFuzz (Fuzzing CPUs by Proxy) 的 ARM64 规格复现

本目录依据 `docs/papers/ref/silifuzz.pdf`（K. Serebryany et al.,
*SiliFuzz: Fuzzing CPUs by proxy*, 2021）第 2 节，在当前可用条件下复现
SiliFuzz 的完整流水线。目标架构为 ARM64（仓库 `AGENTS.md` 约束）。

## 组件

| 论文 | 本目录 |
| --- | --- |
| Snapshot（§2.2） | `include/silifuzz/snapshot.hh`、`src/snapshot.cc` |
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
./scripts/build_deps.sh      # 拉取并插桩构建 Capstone / Unicorn（网络）
make -j
```

如果 `third_party/` 已存在（本机已构建），`make` 直接使用。

## 快速开始

```bash
make check                   # 单元与端到端测试
make demo                    # 生成小语料 -> 修复 -> 128 核 checker
```

完整复现（生成大规模语料、4 核 / 2 分钟机群窗口、合成缺陷验证）见
`docs/measurements.md` 与 `docs/paper-mapping.md`。

## 状态与限制

所有结果以 `docs/measurements.md` 中的真实命令输出为准。已知限制见
`docs/limitations.md`：单机、ARM64 only、代理与原文不同、未发现真实硬件缺陷。
