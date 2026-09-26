# LSU W0+W1 — 平台落地与机制核实 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地 LSU 北极星的 B0 平台（新配置家族 C4-LSU，19 参数 + S 变体，端到端接线）并完成机制核实九项（回填 09 §2 表）——达成里程碑 M0「平台就绪」。

**Architecture:** `configs/se/lsu_proxy.py` 克隆 `ooo_proxy.py` 全注入器面、只替换平台段（B0 = O3_ARM_v7a_3 基线 + DTLB=32）；缓存几何/L2 预取器在 `_pre_instantiate` 钩子内覆盖（stdlib 缓存惰性创建，`arm_chaos_cache.py:83-113` 先例）；runner/schema/validator 三文件同步接新家族 `C4-LSU`。W1 为纯源码核实，产出回填 09 §2。

**Tech Stack:** gem5 v25.1.0.1（vendored）stdlib board + classic caches；Python 3 配置脚本；无新 C++。

**Spec:** `docs/gem5-fi/lsu/09-implementation-plan.md`（总纲 W0/W1，裁决规则 §6）+ `docs/gem5-fi/lsu/02-parameter-baseline.md`（B0 19 参数唯一权威）+ `docs/gem5-fi/lsu/00-overview.md` §1（统一基线条款）。

## Global Constraints

- 分支 `fi-ding`；显式路径 staging，绝不 `git add -A`；commit message 不以 `Co-Authored-By:` 结尾；push 被拒先 `git pull --rebase --autostash origin fi-ding`。
- **00–08 是裁决权威**（09 §6.1）：B0 定值只从 02 表取；O3 core 其余参数按 00 §1 统一基线条款 = `O3_ARM_v7a_3` 全套（`CHAOS/gem5/configs/common/cores/arm/O3_ARM_v7a.py:163-204`）。
- **全量构建已在跑**（PID 814400，日志 `/tmp/gem5_opt_build.log`，-j16 OOM 纪律）——**禁止再启动第二个构建**；Task 1 的运行类步骤以构建完成为门。
- B0 19 参数（02 表，逐项显式设置，默认同值者也显式以防上游漂移）：LQ/SQ=16/16 · Load FU 1 个(MemRead/FloatMemRead opLat=2) · Store FU 1 个(MemWrite/FloatMemWrite opLat=2) · LSQDepCheckShift=0 · LSQCheckLoads=1 · SSIT/LFST=1024/1024 · store_set_clear_period=250000 · cacheLoadPorts/cacheStorePorts=200/200 · DTLB=32 全相联 LRU · L2 TLB=1280/5-way · L1D 32KiB/2-way/lat 2-2-2/MSHR 6/targets 8/writebuf 16 · Cache line 64B(gem5 默认) · L1D ECC/parity 关 · 预取器 L2 StridePrefetcher(degree=8, latency=1, prefetch_on_access=True) · 时钟 2.6GHz 仅换算。
- **stdlib 偏离修正（关键）**：stdlib `L1DCache/L1ICache/L2Cache` 默认各挂一个 `StridePrefetcher()`（`classic/caches/l1dcache.py:56,67`）——B0 预取器**只在 L2**，L1D/L1I 预取器必须显式置 NULL。
- S5（启用保护）= 注入器侧 `protection_model`（gem5 v25 classic cache 无 ECC 参数，CHAOSCache 已实现 b9f2425）——配置层无旋钮，在 lsu_proxy 注释与本计划声明，不伪造配置参数。
- 回归锚：`workloads/directed/reg_chain` golden 校验和 `f247ef3fe6f02cfd`（C4-LSU 与 C0/C3 三家都必须不变）。
- W0 = 1 个 commit（家族端到端：lsu_proxy + 三文件接线 + 验证）；W1 = 1 个 commit（09 §2 回填）。

## 已核实事实（2026-09-25 Explore 代理 + 亲自读源，全部带行号）

- **stdlib 缓存惰性创建**：cache 对象在 `sim.run()` 内 `incorporate_cache` 才创建（`abstract_board.py:456→485` → `simulator.py:552-558`），构造 `Simulator` 前不可覆盖；唯一覆盖时点 = `_pre_instantiate` 钩子，节点名 `l1d-cache-0` / `l1i-cache-0` / `l2-cache-0`（`getattr(ch, name)`，hyphen 命名，`private_l1_private_l2_cache_hierarchy.py:137-145` + `abstract_cache_hierarchy.py:72`）。先例：`configs/se/arm_chaos_cache.py:83-113`。
- **FU/IQ**：v25 FU pool 挂在 IQUnit 上（`BaseO3CPU.py:187` `instQueues = VectorParam.IQUnit(...)`）；v7a FU 定义 `O3_ARM_v7a.py:43-128`（Load `:104-109` MemRead/FloatMemRead opLat=2 count=1；Store `:112-117` 同构）；`O3_ARM_v7a_IQ(IQUnit)` numEntries=32 `:158-160`；`O3_ARM_v7a_3` 全类体 `:163-204`（含 BTB `:131-142`、BiMode BP `:146-155`、延迟/宽度全表）。
- **TLB**：`cpu0.mmu.dtb.size`（`ArmTLB.py:74` 默认 64，全相联默认 `:75-77`，LRU 默认 `:82-84`）；`cpu0.mmu.l2_shared`（`ArmMMU.py:101-104` 默认即 1280/5-way）；stdlib O3 core 的 mmu 可达（`BaseCPU.py:131` + `ArmCPU.py:62-63` + `base_cpu_core.py:163-165`；FS 先例 `arm_chaos_fs.py:233` `dtb = cpu0.mmu.dtb`）。
- **缓存 B0 锚**：v7a DCache `:222-232`（=02 r13-r17 逐项吻合）、ICache `:208-218`、L2 `:236-249`（1MiB/16-way/12-12-12/MSHR16/tgts8/wb8/mostly_excl/RandomRP + StridePrefetcher(8,1,True)）。
- **接线三文件**：`tools/runner.py:43-54` CONFIG_FAMILY dict；`:456-471` config_params 白名单（现 C2-only）；`:440-443` --ctrace C3-only 守卫（lsu_proxy 克隆了同面，需放行 C4-LSU）；`schemas/manifest.schema.json:75-83` config_family 枚举（注意 C1 枚举/字典失配先例——三文件必须同步）；`tools/manifest_validate.py:36` CONFIG_FAMILIES 元组。
- **CHAOSMem 频率比**：ooo_proxy 已按 2.6GHz 算 385 t/cyc（`ooo_proxy.py:494-499`）——克隆体沿用，仅换常量名。

## File Structure

```
configs/se/lsu_proxy.py                 [Create — 克隆 ooo_proxy.py + 平台段替换]
tools/runner.py                         [Modify :43-54, :440-443, :456-471]
schemas/manifest.schema.json            [Modify :75-83 枚举]
tools/manifest_validate.py              [Modify :36 元组]
docs/gem5-fi/lsu/09-implementation-plan.md  [Modify — W1 回填 §2 表]
```

---

### Task 1: C4-LSU 配置家族端到端（W0，1 个 commit）

**Files:**
- Create: `configs/se/lsu_proxy.py`
- Modify: `tools/runner.py`、`schemas/manifest.schema.json`、`tools/manifest_validate.py`
- Test: `/tmp/lsu_w0_check.py`（config.ini 断言脚本，一次性，不入库）

**Interfaces:**
- Produces: 配置家族 `C4-LSU`（manifest `platform.config_family` 枚举新值）；`lsu_proxy.py` CLI 新增 `--variant {B0,S1,S2,S3,S4}`（其余参数面与 ooo_proxy 逐字节相同）；`platform.config_params` 对 C4-LSU 支持 `{"variant"}`。W2+ 的 LSU 注入器将在此家族上挂载。
- Consumes: `build/ARM/gem5.opt`（构建中）、`workloads/directed/reg_chain`。

- [x] **Step 0: 提交本计划文件**

```bash
git add docs/superpowers/plans/2026-09-25-lsu-w0-w1-platform-mechanism.md
git commit -m "docs(plans): LSU W0+W1 execution plan (B0 platform + mechanism verification)"
git push origin fi-ding   # 被拒则 git pull --rebase --autostash origin fi-ding 后重推
```

- [x] **Step 1: 创建 lsu_proxy.py（克隆 + 七处手术替换）**

```bash
cp configs/se/ooo_proxy.py configs/se/lsu_proxy.py
```

然后按序应用以下编辑（其余内容——全部 16 个注入器挂载块、全部注入器参数、maxinsts 块、Simulator/run——**保持与 ooo_proxy.py 逐字节相同**）：

**Edit A（头部注释，原 :1-24 全部替换）**：

```python
# lsu_proxy.py — C4-LSU SE config (docs/gem5-fi/lsu north-star platform, B0).
#
# Mirrors configs/se/ooo_proxy.py (stdlib SimpleBoard + classic L1/L2 +
# SimpleProcessor + the 16 CHAOS injector mount blocks) BUT sets the LSU
# fault-injection north-star platform = B0 baseline
# (docs/gem5-fi/lsu/02-parameter-baseline.md, 19 参数):
#   B0 = O3_ARM_v7a_3 示例基线 (00 §1 统一基线条款; O3_ARM_v7a.py:163-204)
#        + DTLB=32 (TC'23 显式覆盖, 02 r11) —— 其余 18 项与 v7a 示例一致:
#   LQ/SQ=16/16, Load FU 1 (MemRead/FloatMemRead opLat=2) + Store FU 1
#   (MemWrite/FloatMemWrite opLat=2), LSQDepCheckShift=0, LSQCheckLoads=1,
#   SSIT/LFST=1024/1024, store_set_clear_period=250000, cache ports 200/200
#   (澄清: 近似不限流), L2 TLB=1280/5-way (ArmMMU 默认, 显式固化),
#   L1D 32KiB/2-way/lat 2-2-2/MSHR 6/targets 8/writebuf 16,
#   L1I 32KiB/2-way/lat 1-1-1/MSHR 2 (00 §1 跟随 v7a ICache),
#   L2 1MiB/16-way/lat 12-12-12/MSHR 16 + StridePrefetcher(degree=8,
#   latency=1, prefetch_on_access=True) @L2 —— B0 预取器在 L2 (02 r19)。
#   HONEST: ① stdlib L1D/L1I/L2 默认各挂 StridePrefetcher() (偏离 B0),
#   本配置在 _pre_instantiate 钩子内将 L1D/L1I 预取器显式置 NULL; ② S5
#   (启用保护) = 注入器侧 protection_model (gem5 v25 classic cache 无 ECC
#   参数, CHAOSCache protectionModel 已实现) —— 配置层无旋钮, 如实声明;
#   ③ 2.6GHz 仅用于换算 (02 r20, 05 r18: 1ms=2.6M cycles), 注入频率以
#   eligible event 为分母。
#
# USAGE (identical injector arg surface to ooo_proxy.py):
#   gem5.opt --outdir=<dir> configs/se/lsu_proxy.py --cmd=<bin> --cpu O3 \
#       [--variant B0|S1|S2|S3|S4] [--chaos_lsqfwd ...]
```

**Edit B（import 行，原 :28 在末尾追加名字）**：

```python
from m5.objects import CHAOSReg, CHAOSPhysReg, CHAOSMem, CHAOSLSQFwd, CHAOSRenameMap, CHAOSFreeList, CHAOSROB, CHAOSIQ, CHAOSExec, CHAOSFPU, CHAOSL1DForward, CHAOSBPU, CHAOSAddrPath, CHAOSDecode, CHAOSExMon, CHAOSRAS, CHAOSProbe, CHAOSCommitTrace, CHAOSMicroSnap, FUDesc, FUPool, OpDesc, IQUnit, StridePrefetcher, RandomRP, SimpleBTB, BTBSetAssociative, BiModeBP, ReturnAddrStack, BranchPredictor, LRURP, NULL
```

（`NULL` 若 ImportError：改从 `m5.params` 导入并在报告记录。）

**Edit C（OOO dict 块，原 :43-53 替换为）**：

```python
# ---- C4-LSU B0 baseline (02-parameter-baseline.md 19 参数; O3 core 其余
# 参数 = O3_ARM_v7a_3 全套, 00 §1 统一基线条款, O3_ARM_v7a.py:163-204) ----
LSU_CLK = "2.6GHz"   # 02 r20: 仅用于换算 (05 r18: 1ms=2,600,000 cycles)

# FUPool = O3_ARM_v7a_FUP (O3_ARM_v7a.py:43-128; 02 r4/r5 的 Load/Store FU
# 修正即此定义): Simple_Int×2 + Complex_Int×1 + Load×1 + Store×1 + FP×2.
class LSU_Simple_Int(FUDesc):
    opList = [OpDesc(opClass="IntAlu", opLat=1)]
    count = 2

class LSU_Complex_Int(FUDesc):
    opList = [
        OpDesc(opClass="IntMult", opLat=3, pipelined=True),
        OpDesc(opClass="IntDiv", opLat=12, pipelined=False),
        OpDesc(opClass="System", opLat=3, pipelined=True),
    ]
    count = 1

class LSU_Load(FUDesc):
    opList = [OpDesc(opClass="MemRead", opLat=2),
              OpDesc(opClass="FloatMemRead", opLat=2)]
    count = 1

class LSU_Store(FUDesc):
    opList = [OpDesc(opClass="MemWrite", opLat=2),
              OpDesc(opClass="FloatMemWrite", opLat=2)]
    count = 1

class LSU_FP(FUDesc):
    # 逐字复制 O3_ARM_v7a_FP (O3_ARM_v7a.py:59-100) 的 opList, count = 2
    opList = []
    count = 2

class LSU_FUP(FUPool):
    FUList = [LSU_Simple_Int(), LSU_Complex_Int(), LSU_Load(),
              LSU_Store(), LSU_FP()]

class LSU_BTB(SimpleBTB):
    # O3_ARM_v7a.py:131-142
    numEntries = 2048
    tagBits = 18
    associativity = 1
    instShiftAmt = 2
    btbReplPolicy = LRURP()
    btbIndexingPolicy = BTBSetAssociative(
        num_entries=Parent.numEntries,
        set_shift=Parent.instShiftAmt,
        assoc=Parent.associativity,
        tag_bits=Parent.tagBits,
    )

class LSU_BP(BranchPredictor):
    # O3_ARM_v7a.py:146-155 (BiMode 8192×2bit + BTB 2048 + RAS 16)
    conditionalBranchPred = BiModeBP(
        globalPredictorSize=8192,
        globalCtrBits=2,
        choicePredictorSize=8192,
        choiceCtrBits=2,
    )
    btb = LSU_BTB()
    ras = ReturnAddrStack(numEntries=16)
    instShiftAmt = 2

class LSU_IQ(IQUnit):
    # O3_ARM_v7a.py:158-160 (numEntries=32, fuPool=v7a FUP)
    fuPool = LSU_FUP()
    numEntries = 32
```

（注意：`LSU_FP.opList` 执行时**必须**逐字填入 `O3_ARM_v7a.py:60-99` 的全部 39 个 OpDesc——执行者打开该文件照抄，禁止留空。`Parent` 需要 `from m5.params import Parent` 若 m5.objects 未导出——执行时验证。）

**Edit D（平台参数 args，原 :59-67 的 --rob/--phys_int/--phys_float/--phys_vec 四个参数删除，替换为）**：

```python
# --- C4-LSU variant knob (02 敏感性配置列; S5=注入器侧, 不在此) ---
p.add_argument("--variant", default="B0", choices=["B0", "S1", "S2", "S3", "S4"],
               help="B0 baseline or S1(DTLB=64)/S2(L1D 64KiB/4-way)/"
                    "S3(LSQDepCheckShift=4)/S4(prefetcher@L1D) variant")
```

**Edit E（缓存层级 + 平台参数应用 + 钩子，原 :400-436 整段替换为）**：

```python
# C4-LSU cache hierarchy: stdlib 骨架只为 board 布线; 全部几何在下方
# _pre_instantiate 钩子内覆盖 (stdlib 缓存 sim.run() 时才惰性创建,
# arm_chaos_cache.py:83-113 先例)。B0 三级 = v7a ICache/DCache/L2。
cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="32KiB", l1i_size="32KiB", l2_size="1MiB",
)
memory = SingleChannelDDR3_1600("1GiB")
processor = SimpleProcessor(cpu_type=cpu_map[args.cpu], num_cores=1, isa=ISA.ARM)
core0 = processor.get_cores()[0]
cpu0 = core0.core  # the underlying BaseCPU SimObject

# ---- apply B0 (02 表 19 参数逐项显式; O3 core 其余 = v7a_3, 00 §1) ----
if args.cpu == "O3":
    cpu0.LQEntries = 16                    # 02 r2 (v7a:164; BaseO3CPU 默认 32)
    cpu0.SQEntries = 16                    # 02 r3 (v7a:165)
    cpu0.LSQDepCheckShift = 0              # 02 r6 (v7a:166; 默认 4) — S3=4
    cpu0.LSQCheckLoads = True              # 02 r7 (BaseO3CPU.py:147 默认 True)
    cpu0.LFSTSize = 1024                   # 02 r8 (BaseO3CPU.py:157 默认)
    cpu0.SSITSize = "1024"                 # 02 r8 (BaseO3CPU.py:158 默认, 字符串)
    cpu0.store_set_clear_period = 250000   # 02 r9 (BaseO3CPU.py:152 默认)
    cpu0.cacheLoadPorts = 200              # 02 r10 (默认; 澄清: 不限流)
    cpu0.cacheStorePorts = 200             # 02 r10
    if args.variant == "S3":
        cpu0.LSQDepCheckShift = 4          # 02 r6 敏感性配置
    # 02 r11: DTLB=32 全相联 LRU (ArmTLB.py:74 默认 64; S1=64 回默认);
    # 02 r12: L2 TLB 1280/5-way (ArmMMU.py:101-104 默认, 显式固化)
    cpu0.mmu.dtb.size = 64 if args.variant == "S1" else 32
    cpu0.mmu.l2_shared.size = 1280
    cpu0.mmu.l2_shared.assoc = 5
    # -- O3 core 其余 = O3_ARM_v7a_3 (O3_ARM_v7a.py:163-204) --
    cpu0.numPhysIntRegs = 128
    cpu0.numPhysFloatRegs = 192
    cpu0.numPhysVecRegs = 48
    cpu0.numROBEntries = 40
    cpu0.fetchWidth = 3; cpu0.fetchBufferSize = 16; cpu0.decodeWidth = 3
    cpu0.renameWidth = 3; cpu0.dispatchWidth = 6; cpu0.issueWidth = 8
    cpu0.wbWidth = 8; cpu0.commitWidth = 8; cpu0.squashWidth = 8
    for _d in ("decodeToFetchDelay", "renameToFetchDelay", "iewToFetchDelay",
               "commitToFetchDelay", "renameToDecodeDelay", "iewToDecodeDelay",
               "commitToDecodeDelay", "iewToRenameDelay", "commitToRenameDelay",
               "commitToIEWDelay", "renameToIEWDelay", "issueToExecuteDelay",
               "iewToCommitDelay", "renameToROBDelay"):
        setattr(cpu0, _d, 1)
    cpu0.fetchToDecodeDelay = 3
    cpu0.decodeToRenameDelay = 2
    cpu0.trapLatency = 13; cpu0.backComSize = 5; cpu0.forwardComSize = 5
    cpu0.branchPred = LSU_BP()
    cpu0.instQueues = [LSU_IQ()]
    print(f"[lsu_proxy] B0 params applied (variant={args.variant}): "
          f"LQ/SQ=16, DepShift={cpu0.LSQDepCheckShift}, "
          f"DTLB={cpu0.mmu.dtb.size}, L2TLB=1280/5, ROB=40, "
          f"PRF 128/192/48, IQ=32(1L+1S FU opLat=2), width 3/6/8")

board = SimpleBoard(
    clk_freq=LSU_CLK,   # 02 r20: 2.6GHz 仅用于换算
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

board.set_se_binary_workload(binary=FileResource(args.cmd, override=True))

# B0 缓存几何 + L2 预取器 —— _pre_instantiate 钩子内覆盖 (唯一可设时点)。
_applied_b0 = [False]
_orig_pi = cache_hierarchy._pre_instantiate
def _lsu_b0_caches(root):
    _orig_pi(root)
    if _applied_b0[0]:
        return
    _applied_b0[0] = True
    l1d = getattr(cache_hierarchy, "l1d-cache-0", None)
    l1i = getattr(cache_hierarchy, "l1i-cache-0", None)
    l2 = getattr(cache_hierarchy, "l2-cache-0", None)
    assert l1d is not None and l1i is not None and l2 is not None, \
        "[lsu_proxy] cache nodes missing after _pre_instantiate"
    # L1D (02 r13/r15/r16/r17 = v7a DCache :222-232)
    l1d.size = "32KiB"; l1d.assoc = 2
    l1d.tag_latency = 2; l1d.data_latency = 2; l1d.response_latency = 2
    l1d.mshrs = 6; l1d.tgts_per_mshr = 8; l1d.write_buffers = 16
    l1d.writeback_clean = True
    l1d.prefetcher = NULL   # stdlib 默认挂 StridePrefetcher() — B0 只允许 L2 有
    # L1I (00 §1 跟随 v7a ICache :208-218)
    l1i.size = "32KiB"; l1i.assoc = 2
    l1i.tag_latency = 1; l1i.data_latency = 1; l1i.response_latency = 1
    l1i.mshrs = 2; l1i.tgts_per_mshr = 8; l1i.writeback_clean = True
    l1i.prefetcher = NULL
    # L2 (00 §1 跟随 v7a L2 :236-249, 显式固化)
    l2.size = "1MiB"; l2.assoc = 16
    l2.tag_latency = 12; l2.data_latency = 12; l2.response_latency = 12
    l2.mshrs = 16; l2.tgts_per_mshr = 8; l2.write_buffers = 8
    l2.clusivity = "mostly_excl"
    l2.replacement_policy = RandomRP()
    if args.variant == "S2":
        l1d.size = "64KiB"; l1d.assoc = 4              # 02 r13 敏感性
    if args.variant == "S4":                            # 02 r19 敏感性: 预取器挂 L1D
        l1d.prefetcher = StridePrefetcher(degree=8, latency=1,
                                          prefetch_on_access=True)
        l2.prefetcher = NULL
    else:
        l2.prefetcher = StridePrefetcher(degree=8, latency=1,
                                         prefetch_on_access=True)
    print(f"[lsu_proxy] B0 caches applied (variant={args.variant}): L1D "
          f"{'64KiB/4' if args.variant == 'S2' else '32KiB/2'}-way lat222 "
          f"MSHR6/t8/wb16 + L1I 32KiB/2 lat111 MSHR2 + L2 1MiB/16 lat12 "
          f"MSHR16 + StridePrefetcher(8,1,on)@{'L1D' if args.variant == 'S4' else 'L2'}")
cache_hierarchy._pre_instantiate = _lsu_b0_caches
```

**Edit F（CHAOSMem 频率比块）**：块内两处 `OOO["clk"]` 改为 `LSU_CLK`（`_freq` 计算行与 print 行）。

**Edit G（自查）**：`grep -n "OOO\[" configs/se/lsu_proxy.py` 应零命中；`grep -n "ooo_proxy"` 除注释历史引用外应零命中（头部 USAGE 示例路径改为 lsu_proxy.py）。

- [x] **Step 2: 三文件接线（逐字 diff）**

`tools/runner.py:43-54` CONFIG_FAMILY dict 增加（保持其余行不动）：

```python
    "C4-LSU": os.path.join(REPO, "configs/se/lsu_proxy.py"),
```

`tools/runner.py:440-443` --ctrace 守卫放宽（lsu_proxy 克隆了同一 trace 面）：

```python
    if args.ctrace and cfg_family not in ("C3", "C4-LSU"):
        sys.exit(f"[runner] --ctrace requires C3/C4-LSU (only "
                 f"configs/se/ooo_proxy.py and configs/se/lsu_proxy.py define "
                 f"--chaos_ctrace/--ctrace_file; config_family={cfg_family}). "
                 f"Aborting.")
```

`tools/runner.py:461-471` config_params 白名单改为按家族：

```python
    cfg_params = m.get("platform", {}).get("config_params") or {}
    if cfg_params:
        if cfg_family == "C4-LSU":
            supported = {"variant"}  # lsu_proxy.py S-variant knob
        else:
            supported = {"rob", "phys_int", "phys_float", "lq", "sq"}  # kp920_proxy.py knobs
        unsupported = set(cfg_params) - supported
        if unsupported:
            sys.exit(f"[runner] platform.config_params keys {sorted(unsupported)} "
                     f"not in supported set {sorted(supported)} for family "
                     f"{cfg_family}. Aborting.")
        if cfg_family not in ("C2", "C4-LSU"):
            sys.exit(f"[runner] platform.config_params is C2/C4-LSU-only "
                     f"(microarch knobs); config_family={cfg_family}. Aborting.")
```

`schemas/manifest.schema.json:75-83` 枚举数组追加 `"C4-LSU"`（加在 `"C3"` 之后）。

`tools/manifest_validate.py:36`：

```python
CONFIG_FAMILIES = ("C0", "C1", "C2", "C0-CACHE", "C0-FS", "C2-FS", "C3", "C4-LSU")
```

- [x] **Step 3: 构建无关检查**

Run: `python3 -m py_compile configs/se/lsu_proxy.py tools/runner.py tools/manifest_validate.py && echo OK`
Expected: `OK`

Run: `python3 tools/manifest_validate.py --self-test 2>/dev/null || python3 -c "import tools.manifest_validate as mv; print('import ok, families:', mv.CONFIG_FAMILIES)"`
Expected: 自测通过或打印含 `C4-LSU` 的元组。

Run: `python3 -c "
import json, sys
sys.path.insert(0, 'tools')
import manifest_validate as mv
m = json.load(open(sorted(__import__('glob').glob('manifests/*.json'))[0]))
m['platform']['config_family'] = 'C4-LSU'
m['platform']['config_params'] = {'variant': 'S1'}
errs = mv.validate(m)
print('C4-LSU manifest validate:', 'PASS' if not errs else errs)"`
Expected: `C4-LSU manifest validate: PASS`

- [x] **Step 4: 构建门（等待全量构建完成）**

Run: `tail -2 /tmp/gem5_opt_build.log; ls -la build/ARM/gem5.opt 2>/dev/null`
Expected: 日志末尾出现 `scons: done building targets.` 且 `build/ARM/gem5.opt` 存在（~百 MB）。构建仍在跑则先做 Task 2，完成后回来自检本步。若日志出现编译错误：**停止，按 CLAUDE.md 系统性排障**，不得继续。

- [x] **Step 5: B0 冒烟 + config.ini 逐项断言**

Run: `build/ARM/gem5.opt --outdir=/tmp/lsu_w0_b0 configs/se/lsu_proxy.py --cmd workloads/directed/reg_chain --cpu O3`
Expected: 正常退出（exit 0）；stdout 含 `[lsu_proxy] B0 params applied (variant=B0)` 与 `[lsu_proxy] B0 caches applied (variant=B0)` 两行；**Final checksum `f247ef3fe6f02cfd`**（golden 不变）。

写 `/tmp/lsu_w0_check.py`（断言脚本）并运行：

```python
#!/usr/bin/env python3
"""W0 B0 config.ini assertion script. Usage: python3 lsu_w0_check.py <outdir> <variant>"""
import configparser, sys

outdir, variant = sys.argv[1], sys.argv[2]
cp = configparser.ConfigParser()
cp.optionxform = str  # keep case
cp.read(f"{outdir}/config.ini")
secs = cp.sections()

def sec(sub):
    hits = [s for s in secs if sub in s]
    assert hits, f"no section matching {sub!r}; sections={secs[:40]}"
    return cp[hits[0]]

def kv(s, key, want):
    got = s.get(key)
    assert got == want, f"{key}: want {want!r} got {got!r}"

cpu = sec("system.cpu")  # first hit = the cpu itself
for k, w in [("LQEntries", "16"), ("SQEntries", "16"),
             ("LSQDepCheckShift", "4" if variant == "S3" else "0"),
             ("numROBEntries", "40"), ("numPhysIntRegs", "128"),
             ("numPhysFloatRegs", "192"), ("numPhysVecRegs", "48"),
             ("fetchWidth", "3"), ("dispatchWidth", "6"), ("issueWidth", "8"),
             ("commitWidth", "8"), ("cacheLoadPorts", "200"),
             ("cacheStorePorts", "200"), ("store_set_clear_period", "250000"),
             ("LFSTSize", "1024"), ("fetchToDecodeDelay", "3"),
             ("trapLatency", "13")]:
    kv(cpu, k, w)

dtb = sec("mmu.dtb")
kv(dtb, "size", "64" if variant == "S1" else "32")
l2tlb = sec("l2_shared")
kv(l2tlb, "size", "1280"); kv(l2tlb, "assoc", "5")

def cache(sub, size, assoc, tag, mshrs, tgts, wb, pre):
    s = sec(sub)
    kv(s, "size", size); kv(s, "assoc", assoc); kv(s, "tag_latency", tag)
    kv(s, "mshrs", mshrs); kv(s, "tgts_per_mshr", tgts)
    if wb is not None:
        kv(s, "write_buffers", wb)
    has_pre = "prefetcher" in s and s.get("prefetcher") not in (None, "", "NULL")
    assert has_pre == pre, f"{sub}: prefetcher presence want {pre} (got {has_pre})"

cache("l1d-cache-0", "65536" if variant == "S2" else "32768",
      "4" if variant == "S2" else "2", "2", "6", "8", "16",
      variant == "S4")
cache("l1i-cache-0", "32768", "2", "1", "2", "8", None, False)
cache("l2-cache-0", "1048576", "16", "12", "16", "8", "8", variant != "S4")
if variant != "S4":
    kv(sec("l2-cache-0.prefetcher"), "degree", "8")
else:
    kv(sec("l1d-cache-0.prefetcher"), "degree", "8")

# FU pool: any OpDesc section with opClass MemRead/MemWrite must have opLat=2
for s in secs:
    sec_d = cp[s]
    if sec_d.get("opClass") == "MemRead" or sec_d.get("opClass") == "FloatMemRead":
        kv(sec_d, "opLat", "2")
    if sec_d.get("opClass") == "MemWrite" or sec_d.get("opClass") == "FloatMemWrite":
        kv(sec_d, "opLat", "2")
assert any(cp[s].get("opClass") == "MemRead" for s in secs), "no MemRead OpDesc found"

print(f"LSU W0 config.ini assertions PASSED (variant={variant})")
```

Run: `python3 /tmp/lsu_w0_check.py /tmp/lsu_w0_b0 B0`
Expected: `LSU W0 config.ini assertions PASSED (variant=B0)`
（若某断言因 config.ini 命名/格式差异失败：**先怀疑断言脚本的解析假设**，打开 config.ini 对应段核实后再修脚本；若确系参数未生效，回修 lsu_proxy.py——禁止放宽断言迁就错误配置。）

- [x] **Step 6: 变体断言（S1–S4，短运行）**

```bash
for V in S1 S2 S3 S4; do
  build/ARM/gem5.opt --outdir=/tmp/lsu_w0_$V configs/se/lsu_proxy.py \
      --cmd workloads/directed/reg_chain --cpu O3 --variant $V --maxinsts 20000 \
      > /tmp/lsu_w0_$V.out 2>&1 && python3 /tmp/lsu_w0_check.py /tmp/lsu_w0_$V $V
done
```
Expected: 四行 `... assertions PASSED (variant=S1..S4)`；每个 outdir 的 stdout 末尾 checksum 仍为 `f247ef3fe6f02cfd`（maxinsts 截断时若 checksum 行不出现，以 exit 0 + 断言通过为准并在记录注明）。

- [x] **Step 7: golden 回归（三家配置 + 全量重建后的 C0）**

```bash
build/ARM/gem5.opt --outdir=/tmp/lsu_w0_c0 configs/se/arm_chaos.py --cmd workloads/directed/reg_chain --cpu O3 2>&1 | grep -o 'f247ef3fe6f02cfd' && echo C0-GOLDEN-OK
build/ARM/gem5.opt --outdir=/tmp/lsu_w0_c3 configs/se/ooo_proxy.py --cmd workloads/directed/reg_chain --cpu O3 2>&1 | grep -o 'f247ef3fe6f02cfd' && echo C3-GOLDEN-OK
```
Expected: `C0-GOLDEN-OK` 与 `C3-GOLDEN-OK`（证明全量重建 + 接线编辑零附带损伤；ooo_proxy/arm_chaos 源码本任务未触碰）。

- [x] **Step 8: manifest 往返（runner 端到端一次真跑）**

从 `manifests/` 挑一个最小 SE manifest 复制为 `/tmp/lsu_w0_manifest.json`，改：`platform.config_family="C4-LSU"`、`platform.config_params={"variant":"S1"}`、workload 指向 reg_chain、注入器段换成最小 lsq_fwd（或该 manifest 已有的任一 SE 组件）。然后：

Run: `python3 tools/manifest_validate.py /tmp/lsu_w0_manifest.json`（PASS）→ `python3 tools/runner.py /tmp/lsu_w0_manifest.json --config C4-LSU`（按 runner 实际 CLI 语法执行——先 `python3 tools/runner.py --help` 确认 manifest 传参方式）
Expected: runner 打印 `config_family: C4-LSU -> lsu_proxy.py`、运行 exit 0、结果 jsonl 落盘、checksum golden。

- [x] **Step 9: 提交并推送（1 个 commit，含全部验证证据摘要于 message）**

```bash
git add configs/se/lsu_proxy.py tools/runner.py schemas/manifest.schema.json tools/manifest_validate.py
git commit -m "feat(lsu): W0 C4-LSU config family — B0 baseline end-to-end

lsu_proxy.py(克隆 ooo_proxy 全注入器面)+runner/schema/validator 三文件接线。
B0=O3_ARM_v7a_3 基线(00 §1)+DTLB=32(TC'23): 19 参数逐项显式 + S1-S4 变体
(S5=注入器侧 protection_model, classic cache 无 ECC 参数, 已声明); L1D
32KiB/2/lat222/MSHR6/t8/wb16 + L1I 32KiB/2/lat111/MSHR2 + L2 1MiB/16/lat12
+StridePrefetcher(8,1,on)@L2, stdlib L1D/L1I 默认预取器显式置 NULL(偏离修正);
FU 1L+1S opLat=2; --ctrace 放行 C4-LSU; config_params 白名单按家族。
验证: config.ini 断言脚本 B0+S1-S4 全过; reg_chain golden f247ef3fe6f02cfd
三家(C4-LSU/C0/C3)不变; manifest 往返 PASS; py_compile 零输出。"
git push origin fi-ding
```

---

### Task 2: 机制核实九项 + 两项附加裁定（W1，1 个 commit；可与 Task 1 的构建等待期并行）

**Files:**
- Modify: `docs/gem5-fi/lsu/09-implementation-plan.md`（§2 表回填 + 表后附加裁定记录）
- Test: 无（源码核实任务，产出=文档；每条结论必须带 file:line 证据）

**Interfaces:**
- Produces: §2 表九行状态 `待核实 → 已核实`（含结论与行号）；⑦ 的 AGU 截获裁定（W4 依赖）；F6 事件映射表（W2 依赖）。
- Consumes: §2 表的初查锚点（已含路径行号）。

- [x] **Step 1: 逐项源码核实（九项，每项给出「xlsx 表述 vs v25.1 实际 vs 对模型行的影响」结论 + file:line）**

核实要点（锚点已在 09 §2 第三列）：
1. ① LQ/SQ：`lsq.hh/.cc`（:761 起 LQ head、LSQRequest 状态机）+ `lsq_unit.hh/.cc`（:247/:287 violation）——确认表项字段构成、head/tail 语义、violation→replay 路径；确认 16/16 只能配置显式落地（已由 W0 完成）。
2. ② SSIT/LFST：`store_set.hh/.cc`（SSITEntry :78、LFST :155）+ 消费方 `mem_dep_unit.cc`——确认 1024/1024 默认（BaseO3CPU.py:157-158）与 S05/S07 落点。
3. ③ DTLB：`ArmTLB.py:74` size 默认 64 + `tlb.hh/.cc`——确认 W0 的 `dtb.size=32` 是唯一配置点、S1=回默认（已由 W0 落地，本项确认无遗漏第二入口）。
4. ④ L1D：v7a `:222-232` 与 02 逐项吻合（已证）；确认 stdlib 覆盖钩子是唯一时点（W0 已实现）。
5. ⑤ 预取器：`stride.hh` + v7a `:247`——确认 B0 预取器参数（degree/latency/on_access）在 v25 StridePrefetcher 的参数名一致。
6. ⑥ exclusive monitor：`isa.cc:1871-1960`（handleLockedRead/Write）+ `insts/macromem.cc`——给出 O01-O09 的注入落点结论（单核 SE 下 LLSC 语义是否可测、多核 FS 差距的准确表述）。
7. ⑦ **AGU 截获裁定（W4 依赖）**：读 `lsq_unit.cc` 的 EA 计算（executeAddrCalc / readAddrCalc 路径）与 `CHAOSAddrPath` 现有挂点（`sendFragmentToTranslation`）——裁定 A01-A08 的注入点：EA 寄存器截获是否需要新挂点（lsq_unit EA 计算后、DTLB 前），还是扩展现有 CHAOSAddrPath；给出明确裁定 + 依据。
8. ⑧ F4/F6 触发差距：`chaos_trigger.hh:23-48`（枚举 F0-F3+F5）——确认 F4/F6 缺失范围与扩展面（W2 的输入）。
9. ⑨ MSHR/fill/writeback：`mshr.hh/.cc` + `cache.cc`/`base.cc` + `write_queue*.cc`——给出 C11/C12/C14 的落点结论。

- [x] **Step 2: F6 事件映射表（W2 依赖，05 r8 的事件枚举 → gem5 具体事件点）**

对 05 r8 列出的 F6 触发事件（TLB hit、SQ forward、dirty eviction、CAS 成功）逐个给出 v25.1 中的具体可挂接点（函数/回调，带 file:line），写进 §2 表后附加小节「F6 事件映射（W2 输入）」。找不到对应物的如实标「无直接对应点，需 W2 造近似事件」。

- [x] **Step 3: 回填 09 §2 表**

把九行「状态」列从「待核实」改为「已核实（N#）」，结论精炼进「v25.1 实际」列（保留初查锚点原文，追加核实结论）；表后新增「W1 核实结论与裁定（2026-09-25）」小节记录 ⑦ 裁定与 F6 映射。**落点修正≠故障语义修正**（09 §6.2）：不得改 00-08 的任何表述。

- [x] **Step 4: 自检 + 提交**

Run: `grep -c '待核实' docs/gem5-fi/lsu/09-implementation-plan.md`
Expected: `0`（九项全部回填；若 F6 映射小节保留必要的「待 W2 落地」措辞，不计入「待核实」——措辞区分）。

```bash
git add docs/gem5-fi/lsu/09-implementation-plan.md
git commit -m "docs(lsu): W1 mechanism verification — nine items adjudicated (M0)

九项机制核实全部回填(file:line 证据); 附加: ⑦ AGU 截获裁定(W4 输入) +
F6 事件映射表(W2 输入)。落点修正不触碰 00-08 故障语义(09 §6.2)。"
git push origin fi-ding
```

---

## Self-Review 结论（写计划时已自查）

- **覆盖**：09 W0 的三段（配置家族/接线/验证）→ Task 1 全部；W1 的三段（九项/附加核实/回填）→ Task 2 全部。B0 19 参数逐项出现在 Edit E 或钩子代码中；S1-S4 在代码与断言脚本中成对出现；S5 诚实声明两处（头部注释 + Global Constraints）。
- **占位符扫描**：唯一运行时填入点是 LSU_FP.opList（指令明确=逐字复制 O3_ARM_v7a.py:60-99 的 39 个 OpDesc，非自由发挥）；无 TBD/TODO。
- **一致性**：家族名 `C4-LSU` 在 runner/schema/validator/commit message 四处一致；`--variant` 值域 {B0,S1,S2,S3,S4} 与断言脚本的 variant 分支一一对应；`LSU_CLK` 替换了全部 `OOO["clk"]` 引用（Edit G 自查命令保证）。
