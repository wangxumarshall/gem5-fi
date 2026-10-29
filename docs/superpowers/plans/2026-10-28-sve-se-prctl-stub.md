# 2026-10-28 SVE SE prctl stub——打通 SDCShield 真二进制运行的 VL 探测屏障

## 目标

SDCShield 真二进制（`/home/sdc/wangxu/sdcshield-main/builddir/sdcshield`）在
gem5 SE 模式下死于 `fatal: syscall prctl (#167) unimplemented`（实测）。框架层
`arm64_spec_get`/worker VL pin 需要 `PR_SVE_GET_VL(51)`/`PR_SVE_SET_VL(50)`。
本计划为 ARM64 SE syscall 表补一个 prctl handler，使 512-bit 腿（SVE 全 VL
验证运动）能在 SE 里跑真二进制。

## 契约（对齐 sdcshield 框架 `framework/device/cpu/arm64/arm64_vl.h`）

- `PR_SVE_GET_VL` → 返回当前 VL **字节数**（正数）。
- `PR_SVE_SET_VL`：请求 ≥ 当前配置 VL → 返回授予的 VL 字节数；请求 < 当前
  VL → `-EINVAL`（gem5 SE 单档限制，warn_once 如实警告）。
- 其它 option → 返回 0（忽略）。
- **关键**：返回 0 会被框架判为"执行层忽略"→ ENOSYS → 测试 SKIP，所以成功
  路径必须返回正的 VL 字节数。VL 来自 `BaseISA::getVectorLengthInBytes()`
  （`src/arch/arm/isa.hh` 公有虚方法，`sveVL*16` 字节；SE 下 `sveVL =
  p.sve_vl_se`）。

## 改动点（一个 patch）

- Modify: `CHAOS/gem5/src/arch/arm/linux/se_workload.cc`
  - 表定义前（`SyscallTable32` 之前，`namespace ArmISA` 内）加静态
    `prctlFunc(SyscallDesc*, ThreadContext*, long option, long arg2)`。
  - 64-bit 表 `{base + 167, "prctl"}`（~679 行）改为
    `{base + 167, "prctl", prctlFunc}`。
  - 32-bit compat 表的 `{base + 172, "prctl"}`（~302 行）**不接**：
    `SyscallABI32` 的 guest_abi Argument 特化排除 wide 类型（`long` 8 字节），
    同一 handler 挂 32-bit 表无法通过模板实例化；且 AArch32 无 SVE，
    PR_SVE_* 不会合法出现。64-bit 表才是实测触发 fatal 的那张。

## 验证

- [ ] Step 3 增量重建：`scons -C CHAOS/gem5 build/ARM/gem5.opt -j16`，
  零新 warning；产物拷回 `CHAOS/gem5/build/ARM/gem5.opt`（README:113-116
  陷阱）；`tools/verify_gem5_injectors.sh` 通过（19 CHAOS 类在位）。
- [ ] Step 4 spike：`scripts/eigen-sve-double/gem5/run_sve.sh` 跑真二进制
  `sve_rot_ldr_at_top --vl 4`（512-bit），`fatal: syscall prctl (#167)
  unimplemented` 消失（出现下一个 fatal 属预期，Task 5 迭代）；跑完
  `rm -rf m5out`。
- [ ] Step 5 回归：既有 dual kernel（fpu_special_sve_dual）无注入跑绿，
  `SDCSHIELD_FAILS=0`。

## 交付

stub commit（一 patch 一 unit）+ 重建后的 gem5.opt（CHAOS 路径）。
