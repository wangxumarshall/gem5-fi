# FSU 夜间自主推进队列（2026-11-04）

> 本文件是上下文压缩后的恢复入口。**先读本文件 + `docs/superpowers/plans/2026-11-04-fsu-night-f5-w4-w5-fr03-w6.md`，再从 `progress.md` 恢复。**
> 分支只允许 `fsu`；不创建 worktree；不改 `/home/sdc/gem5-fi-ding`。

## 0. 基线（2026-11-04 00:00 核对）

- HEAD `f0aaa060396b793310d783a56402bf004ed029ed`（`fsu`），与 `origin/fsu` 0/0。
- 工作区 clean。
- 历史视图 **27/519 seed、9/173 RunID**；活跃 F0/F5 **18/240 seed、6/80 RunID**。
- FSU 测试 **247 passed**：`pytest tests/test_fsu_*.py tests/test_chaos_fsu_*.py tests/test_chaos_vec_stuck_cpp.py tests/test_chaos_physreg_generation_cpp.py -q`
- 非 FSU 回归 **20 passed**：`pytest tests/test_lsu_freq_policy.py tests/test_lsu_armtlb_f5_noeffect.py -q`
- 资源：96 核、313 GB 内存、负载 ~0.15；gem5 串行，最多并发 2；构建 `-j16`。
- W5 suite 的 5 个 component run 只计 1 个正式 seed。

## 1. 任务队列（按顺序；完成一项勾一项）

- [ ] A. F5 计数与传播证据加固（代码 + host 单测 + 文档）
  - [ ] A1 countOnly/fault-run/warm-up/post-install 分开计数并发射
  - [ ] A2 warm-up 边界测试（0 / 1 / >eligible；安装是否计 exposure 明确）
  - [ ] A3 不把 fault-run eligible != golden census 一律判错；记录 delta + 运行内守恒
  - [ ] A4 `exposures_total = sampled_unique + omitted`，按 exposure_id 去重
  - [ ] A5 sampled/dropped 仅观测采样，文档写明
  - [ ] A6 百万级计数 uint64 + 事件预算显式失败/预注册采样
  - [ ] A7 同一 consumer 多 exposure 来源：有界多来源摘要，不静默只留第一条
  - [ ] A8 一条到 L5 的链只认证该路径；Markdown 分节报告
  - [ ] A9 首次激活/最终统计/chain_end 在 tracer 关闭前写入（含提前终止测试）
- [ ] B. FP06-F5-W4 gate + 正式 3 seed
  - [ ] B1 复核 W4 workload/golden/B0/decode/eligible（rate-v1 2,097,155）
  - [ ] B2 短 W4 全量 exposure 记录 vs bounded sampling 对照 gate
  - [ ] B3 正式规模 bounded gate（计数准确、事件/内存/文件有界、flush/正常退出/提前终止）
  - [ ] B4 预注册 seed1/2/3（FP06-a/b/c）并跑 seed1 → audit → seed2 → seed3
- [ ] C. FP06-F5-W5 suite gate + 正式 3 seed
  - [ ] C1 复用 W5 五程序身份；核对 binary/manifest/golden 实际哈希
  - [ ] C2 suite 级 F5 预注册（每 component 一个永久 fault）
  - [ ] C3 五程序 F5 gate（5/5 component audit）
  - [ ] C4 正式 suite seed1 → seed2 → seed3；15 component 只计 3 seed
- [ ] D. FR03 完整闭环 + gate + 正式 W3 3 seed
  - [ ] D1 runner/schema 显式 CHAOSPhysReg 路径
  - [ ] D2 L5 commit/squash/first-impact/oracle
  - [ ] D3 O3 容器级 rename/free/realloc/squash 测试
  - [ ] D4 跨 generation 持久、旧 generation 不串入新 generation
  - [ ] D5 int/float/Vec、不同 phys cell、非目标 lane 不串扰
  - [ ] D6 读暴露与写入重施加分别计数
  - [ ] D7 真实可分配目标；mask/polarity 固定
  - [ ] D8 FR03-F5-W3 非正式 gate（连续写/squash/重分配/链身份/真实 L5/runner 路径）
  - [ ] D9 gate 全过后正式 seed1/2/3；否则保留 gate PARTIAL
- [ ] E. W6 artifact + F0/F5 可执行任务
  - [ ] E1 SVD 既有组件身份核对
  - [ ] E2 FFT 固定输入 + 来源/许可证 + 可重复构建 + native/gem5 golden + 数值 oracle
  - [ ] E3 真实稀疏线性系统（非 SpMV 代理）+ 同上
  - [ ] E4 suite_hash / component identity / 计数协议
  - [ ] E5 FP04-F0-W6 gate → 正式 3 seed
  - [ ] E6 FP06-F5-W6 gate → 正式 3 seed（若组件齐全）

## 2. 文件所有权（同一文件只允许一个 agent 修改）

| Owner | 文件 |
|---|---|
| Agent A（F5 hardening/W4） | `CHAOS/gem5/src/cpu/o3/CHAOSFPU/*`、`tools/fsu_seed_audit.py`、`tools/fsu_chain_check.py`、`tools/fsu_seed_doc.py`、`tests/test_chaos_fsu_f5_cpp.py`、`tests/test_fsu_chain_check.py`、`tests/test_fsu_seed_audit.py` |
| Agent B（FR03） | `CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/*`、`regfile.hh`、`free_list.hh`、`commit.cc`（仅新增 hook 调用）、`rob.cc`（仅新增 hook 调用）、`dyn_inst.cc`（仅新增 hook 调用）、`tests/test_chaos_physreg_generation_cpp.py`、`tests/unit/*`、`docs/gem5-fi/fsu/FR03-GENERATION-SEMANTICS.md` |
| Agent C（W5/W6） | `tools/fsu_suite.py`、`tools/fsu_suite_runner.py`、`tests/test_fsu_suite*.py`、`configs/fsu/suites/*`、`workloads/directed/fft_*`、`workloads/directed/sparse_*`、`tools/fsu_w6_*.py`、`tests/test_fsu_w6_*.py`、`docs/gem5-fi/fsu/W6-*.md` |
| 主 agent（整合） | `tools/fsu_seed_runner.py`、`schemas/manifest.schema.json`、`configs/fsu/FSU-FP06-F5-W4*.json`、`configs/fsu/FSU-FP06-F5-W5*.json`、`docs/gem5-fi/fsu/*STATUS*`、`runs/**`、git 提交/推送 |

**禁止**：agent 不得运行 scons/gem5（主 agent 统一构建）；不得修改 `runs/` 正式证据；不得改源注册表 `runids.json` 的 173 RunID。

## 3. 阻塞清单

| 日期 | 任务 | 阻塞 | 证据/尝试 | 状态 |
|---|---|---|---|---|
| 2026-11-04 | — | — | — | 无 |

## 4. 恢复命令

```bash
cd /home/sdc/gem5-fi-fsu
git status --porcelain=v1; git log --oneline -3
python3 tools/fsu_index.py            # 以磁盘 AUTHORITATIVE + audit 重算
python3 -m pytest tests/test_fsu_*.py tests/test_chaos_fsu_*.py tests/test_chaos_vec_stuck_cpp.py tests/test_chaos_physreg_generation_cpp.py -q
```

## 5. 进度日志（只追加）

- 2026-11-04 00:00 基线核对完成；建立队列；启动 A/B/C 三个 subagent。
