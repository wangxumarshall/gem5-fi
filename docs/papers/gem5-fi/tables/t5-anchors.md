### 5.0 已验证锚点表（本方案撰写期间实跑，真实 gem5 输出）

> **诚实声明**：以下锚点均在本方案撰写期间用 `CHAOS/gem5/build/ARM/gem5.opt`（重建后，mtime 2026-08-30 10:19，1.05GB）实跑获得，命令与输出可复现。运行前须 `source /home/sdc/gem5-deps/env.sh`（设 LD_LIBRARY_PATH 含 libprotobuf + libabsl）。这是"已验证"而非"预期"。

| 锚点 | 注入器/kernel/配置 | 命令（要点） | 真实输出 | 状态 |
|---|---|---|---|---|
| golden 基线 | 无注入 / `reg_chain` / O3 | `gem5.opt arm_chaos.py --cmd=reg_chain --cpu=O3` | `f247ef3fe6f02cfd` | ✅ 已复现（与 STATUS.md 一致） |
| GPR SDC（X3 bit0） | CHAOSPhysReg arch_frontend / `reg_chain` | `--chaos_phys --phys_mode=arch_frontend --phys_target_arch=3 --probability=1.0 --first_clock=100000 --max_faults=1 --rng_seed=20260825 --fault_type=bit_flip` | 输出 `d43a25d7fcc218b7`（≠ golden → SDC）；注入日志 `Cycle:100000 PhysReg[220] (<= ArchReg[3]) Mask:0x...800...`；read-trace `reads_before_overwrite=25000/50000/75000/100000/125000 overwritten=0` | ✅ 已复现（与 STATUS.md `d43a25d7fcc218b7` 一致） |
| LSQ 转发 SDC | CHAOSLSQFwd / `fp_fwd_kernel` | `--chaos_lsqfwd --probability=1.0 --first_clock=1000000 --max_faults=1 --rng_seed=20260825 --fault_type=bit_flip` | `SDC@it=232 i=58 golden=3ffad444e2800000 actual=3ffad444e6800000 xor=0000000004000000`，`iters=500 fails=1`；对照无注入 `iters=500 fails=0` | ✅ 已复现（XOR bit30 = double 尾数高位，吻合 method3 位谱） |
| **method1 历史残留 SDC** | CHAOSRenameMap f5_substitute / `accum_kernel` X9 | `--chaos_rat --rat_mode=f5_substitute --rat_target_arch=9 --probability=1.0 --first_clock=100000 --max_faults=1 --rng_seed=20260825` | `iters=500 fails=1`（golden `fails=0`）；日志 `ArchReg[9]->PhysReg[199] (stolen from donor arch 13, was PhysReg[62])` | ✅ 已复现（F5 偷映射在长存活累加器传播为 SDC，方案 §5.2 验收锚点 P(history_residue)>0） |
| core179 D1 撕裂移位 | CHAOSLSQFwd byte_lane_skew rol1 / `fp_fwd_kernel` | `--chaos_lsqfwd --lsq_structural_fault=byte_lane_skew --lsq_skew_bytes=1 --first_clock=1000000 --max_faults=1` | `actual=003ffad444e28000`（golden 右旋1字节），`xor=3fc52e90a6628000` 多位散布 | ✅ 已复现（H5 主线就位，rol1 签名方向与现场 35/36 汉明重量一致） |

> **锚点解读**：
> - **GPR SDC** 完整演示 §5.1 机制：arch_frontend 模式经前端 RAT 定位 `ArchReg[3]→PhysReg[220]`，注入后该物理寄存器被读 125000+ 次才覆写（`overwritten=0` 至观察窗口末），SDC 经长读传播窗口扩散——这是 method1 "状态泄漏"签名在仿真侧的可观察代理。
> - **LSQ 转发 SDC** 的 XOR `0x04000000` 落在 double 尾数高位（bit 30，非符号位），与现场 method3 "float 尾数 85% / double 93% / 符号 0–1" 的位谱规律方向一致（§6.2），构成仿真-现场对照生态效度的初步证据（E2）。
