# R4-6 (FS 部分) — FS 基础设施可行性核实 + 阻塞分类

> Worktree `.claude/worktrees/r4-t08fs`，branch `r4-5.9-t08-fs`（base `55b89900`）。
> 本计划是 R4-6 的 **FS 核实子集**（A06 / SPEC 适配不在本子 agent 范围）。
> 禁止 build / 禁止 run gem5（含 FS）；只做只读核实 + 机器可查的验证。

## 目标

把 `blockers_for_approval.md` 的 77 项（RULING 6 + LICENSE 12 + FS-MULTICORE 35 +
FS-INFRA 24）**按"缺什么"分类**，每项给出可复现证据；不臆断、不假报完成。

## 事实基线（实测命令/输出）

- **FS 资产齐备**（`ls -la /home/sdc/gem5-fi-ding/gem5-fs/`）：
  `vmlinux` 237716656 B、`ubuntu.img` 2361393152 B、`boot.arm64` 1432 B、
  20 个 dtb。→ FS-INFRA 的 kernel/disk/bootloader **不缺**。
- **FS checkpoint 存在**（本次发现，纠正旧 help 文本）：
  `runs/lsu/fs_cpt_boot/cpt.237949797015/`（`m5.cpt` 10321253 B + 8 个
  `board.physmem.store*.pmem`）与 `runs/h7formal/mkckpt/cpt.90000000/`
  （`m5.cpt` 10319801 B）。旧 `--fs-checkpoint` help 里的
  `runs/fs_lsu/boot_b0/cpt.*` **不存在**。→ restore 基线句柄已具名。
- **FS 平台是单核**：`configs/se/arm_chaos_fs.py:231`
  `SimpleProcessor(cpu_type=..., num_cores=1, isa=ISA.ARM)`。
  → FS-MULTICORE 需要 **config 改造**（多核 + dtb + 跨核一致性），不是"跑一下"。
- **载荷缺口（真实）**：`workloads/` 下无 litmus / PARSEC / SPEC。
  `find workloads -iname '*litmus*|*parsec*|*spec*'` 只命中
  `directed/spec_leak_probe_kernel`（我方案自造探针，非 SPEC CPU）。
- **载体齐备**：`configs/fs/tlb_probe.rcS`（TLB walk 压力 + md5 oracle，
  `TLB_PROBE_GOLDEN=b6d81b360a5672d80c27430f39153e2c`）、
  `configs/fs/boot_ckpt.rcS`、`configs/fs/m2_ptrchase.rcS`。
- **campaign FS 接线**：`resolve_cell` 对 armtlb family 构造 FS flag 集；
  `--fs-checkpoint` 缺失时 main() 响亮 error（不静默）。
  `fs_asset()` 支持 `LSU_FS_DIR`（worktree 无 3GB 子模块 → 复用主 worktree）。

## 分类结论（每类：缺什么 / 证据 / 可否自行解决）

| 类别 | 项数 | 缺什么 | 证据 | 可否自行解决 |
|---|---|---|---|---|
| **FS-INFRA** | 24 | 无外部资源缺口——缺的是**工时**（build + `--fs-checkpoint` 接线 + 跑通 3 个 T-cell）；载体/资产/checkpoint 全在 | §事实基线 1/2/5/6 | **可以**（集成侧 build + run） |
| **FS-MULTICORE** | 35 | ① 多核 FS config（现为 num_cores=1，需改造 + dtb）；② litmus/PARSEC **载荷二进制**（仓库内不存在） | §事实基线 3/4 | **部分**：config 改造可自行做；litmus/PARSEC 载荷需外部获取 |
| **LICENSE** | 12 | SPEC CPU2017 **许可数据**（合法镜像/license） | `WL_BLOCKED["SPEC"]`；仓库无 SPEC | **否**——真缺外部授权资源 |
| **RULING** | 6 | 用户裁决（A06 load 侧契约等；非本子 agent 范围） | `MODEL_BLOCKED["A06"]` | **否**（需用户裁决） |

分类计数与 `runid_map.json` 的 reason 分类一致（本次实测）：
`workload-level: TLB needs FS`=24（FS-INFRA）、`litmus needs multi-core FS`=29 +
`PARSEC needs multi-core FS`=6 = 35（FS-MULTICORE）、`SPEC license`=12（LICENSE）。

## 任务清单（本 commit：FS 基础设施，独立于 T08）

- [x] 1. `tests/test_lsu_fs_infra.py`：结构面（config/载体/单核/campaign 接线）
      永远可查；资产面（kernel/disk/bootloader）与 checkpoint 面在无资产时
      **SKIP**（不假报），LSU_FS_DIR 显式给出却缺资产时 **FAIL**（声明不成立）。
- [x] 2. `tools/lsu_campaign.py`：纠正 `--fs-checkpoint` help 的陈旧路径
      （`runs/fs_lsu/boot_b0/cpt.*` → 实测存在的两处 cpt 目录）。
- [x] 3. 本计划文件 + `R4-5.9-report.md` §3 精确阻塞清单。
- [x] 4. 单 commit `[LSU][MDSPEC][R4-6-FS]`（T08 已单独 commit `2628a1e6`）。

## 集成侧（main agent）必做清单

1. `LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs python3 tests/test_lsu_fs_infra.py`
   （期望 ALL PASS，含 checkpoint 面）。
2. FS smoke：`--fs-checkpoint runs/lsu/fs_cpt_boot/cpt.237949797015`
   （或 `runs/h7formal/mkckpt/cpt.90000000`）跑通一次 restore；
   restore-tick 基线 = cpt 目录名。
3. FS-INFRA 转 PARTIAL/PASS 需重跑 24 个 T-cell（3 个 T08 + 21 个其余）。
4. FS-MULTICORE 需先决定：是否接受"多核 config 改造 + litmus/PARSEC 外部载荷"。

## 诚实登记

- 本子 agent 未 build、未 run 任何 gem5（含 FS）——所有"跑通"均为集成侧待办。
- litmus/PARSEC/SPEC 载荷**实测不存在**于仓库；断言它们缺外部资源。
- FS-INFRA 的"可以自行解决"是**判断**（资产/载体/checkpoint 实测齐备），
  其成立仍需集成侧真实跑通一次 restore——未跑通前不得标记 PASS。
