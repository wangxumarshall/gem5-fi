# SDCShield 检测效果 gem5 故障注入评估——实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 通过 CHAOS/gem5 故障注入量化 SDCShield 测试用例的 SDC 检出率 `P_detect = Detected/(Detected+Escape)` 与盲区分布，回答"哪些微架构故障形态 sdcshield 查得出来、哪些静默漏过"。

**Architecture:** 双模式混合设计。**SE-O3 主战场**：把 sdcshield 测试用例提取为静态双通道内核（通道 A = 原测试内部校验，检出=Detected；通道 B = 独立全状态 checksum，判别 Escape/Masked），跑 19 注入器全量位点 × 瞬态/永久故障模型 × N=400 战役。**FS 保真验证臂**：真 sdcshield 二进制装入 gem5-fs Ubuntu 磁盘，经 fs_checkpoint 两阶段流水线在真实 Linux 上接受 TLB/PTW/SysReg/Cache/Mem 注入（小 N 交叉验证）。

**Tech Stack:** CHAOS/gem5 25.1.0.1（ArmO3CPU SE + ArmBoard FS checkpoint，注入器 21+1 类）；sdcshield 子模块 07be34e2（只读，不改其源码）；tools/{runner,campaign,classify}.py 战役工具链；静态 aarch64 C 内核（宿主 openEuler 24.03 SP3 aarch64 原生编译）。

## Global Constraints（全任务隐含遵守）

- **一补丁一单元**：每个 Task = 恰好一个 commit；不捆绑、不并行；完成一个（验证→commit→push）再下一个。
- **三步真机自验证**：干净构建/零新警告 + 功能验证引用真实输出 + 至少一个不相关回归（既有内核 golden 不变：`reg_chain` `f247ef3fe6f02cfd`）。
- **分支纪律**：在 `fi-wx-verify-sdcshield` 分支工作并 push（绝不 push main）；commit 不得以 `Co-Authored-By: Claude` 结尾。
- **sdcshield 子模块只读**：本计划不改 sdcshield 源码（其 CLAUDE.md 有 DCO/CI 门槛）；提取式内核放本仓 `workloads/sdcshield/`。
- **gem5.opt 全量前置**：本仓 `CHAOS/gem5/build/ARM/gem5.opt`（2026-08-27）只含 7 个 CHAOS 类，**Task 0.1 完成前任何注入实验无效**；产物拷贝纪律：scons 产物落仓库根 `build/` 须 cp 回 `CHAOS/gem5/build/ARM/`；**campaign 与构建绝不并行**。
- **预注册判据不可改**（J1–J4 见下）；阴性结果如实归档；统计一律 Wilson 95% CI + raw/active 双口径。
- **超时口径**：runner `CHAOS_HANG_TIMEOUT`（默认 600s）；每个新内核先标定 ITERS 使 gem5 O3 单跑 ≤120s。
- **不改 x86 路径；不改 19 注入器既有语义**（新代码只加 oracle/路由/配置参数）。

## 预注册判据（J1–J4，裁决时不得改）

- **J1（工具有效性）**：全部双通道内核无注入对照（N=20/内核）100% 全绿——`SDCSHIELD_FAILS=0` 且 checksum==golden 且 exit 0。任何失败=FP 底噪，必须先归因清零再进主战役。
- **J2（瞬态到达性检出）**：fpu_special_values 类（常量 golden 逐字节比对）预期 `P_detect → 1.0`；fma 类（in-run `fmaf` 参考 + 1e-6 容差）预期 mantissa 位段 `P_detect` 显著低于 sign/exp 位段（容差盲区预言）。若 fma 类整体 `P_detect` 显著 <1，即发现真实容差/校验窗口盲区——两个方向都是有效结论，如实裁决。
- **J3（永久故障盲区，补 harp_wrap deferred 缺口）**：CHAOSFUPerm × fma 类的 `P_detect` **低于** CHAOSFPU 瞬态 × fma 类（Wilson CI 不重叠为显著）。预言依据：in-run 参考双通道同损（tools/harp_wrap.py:142-145 已登记的结构性弱点，SDCED-7.1 permanent 子臂从未跑过）。
- **J4（SE-FS 交叉一致性）**：共享臂（Cache data / Mem）上真二进制 `result: fail` 率与 SE 内核 `P_detect` 方向一致、量级相当（≤2× 或 CI 重叠）；不符则归因真实 OS/框架差异如实报告（描述性判据，不设阈值裁决）。

## 与裁决依据的链接

FS vs SE 裁决与位点×故障模型裁决的完整实证依据见 `findings.md` F-SS-1..F-SS-7（2026-09-22）：真二进制 SE 三重阻断（prctl fatal @syscall_emul.cc:79 + pre-main 确定性崩溃 @tick 123,543,000 + 信号 syscall 忽略；/bin/true 对照 exit 0 @tick 116,528,000 证明 SE ld.so 本身健康）；SDC 高发位点全 O3-only；探针脚本 `fi_research/probes/se_sdcshield_probe.py` 留档。

---

### Task 0.1: 全量注入器 gem5.opt 就位与双锚回归

**Files:**
- Create: `tools/verify_gem5_injectors.sh`（注入器类数 + 双锚回归一体脚本）
- 二进制操作（gitignored）：`cp /home/sdc/wangxu/gem5-fi-fuzz/CHAOS/gem5/build/ARM/gem5.opt CHAOS/gem5/build/ARM/gem5.opt`

**Interfaces:**
- Produces: 后续所有任务依赖的可写前提——`CHAOS/gem5/build/ARM/gem5.opt` 含全部 22 个 CHAOS 类（21 注入器 + CHAOSCov）；`tools/verify_gem5_injectors.sh` 可重复执行给出 PASS/FAIL。

- [ ] **Step 1: 拷贝全量二进制并核对类数**

```bash
cp /home/sdc/wangxu/gem5-fi-fuzz/CHAOS/gem5/build/ARM/gem5.opt \
   CHAOS/gem5/build/ARM/gem5.opt
nm -C CHAOS/gem5/build/ARM/gem5.opt | grep -cE '^\S+ [TW] gem5::CHAOS'
```
Expected: ≥22 个类符号（Reg/PhysReg/Mem/Cache/LSQFwd/AddrPath/PTW/RenameMap/FreeList/ROB/IQ/RAS/Exec/FPU/L1DForward/BPU/ExMon/ArmTLB/ArmSysReg/FUPerm/GateFU/Cov；逐一 `nm -C ... | grep 'gem5::CHAOSFUPerm'` 抽查 3 个此前缺失的类：FUPerm/GateFU/RAS 必须存在）。

- [ ] **Step 2: 写 tools/verify_gem5_injectors.sh**

```bash
#!/usr/bin/env bash
# Verify the CHAOS/gem5 binary carries the full injector set + dual anchors.
set -u
cd "$(dirname "$0")/.."
G5=CHAOS/gem5/build/ARM/gem5.opt
MISSING=0
for c in CHAOSReg CHAOSPhysReg CHAOSMem CHAOSCache CHAOSLSQFwd CHAOSAddrPath \
         CHAOSPTW CHAOSRenameMap CHAOSFreeList CHAOSROB CHAOSIQ CHAOSRAS \
         CHAOSExec CHAOSFPU CHAOSL1DForward CHAOSBPU CHAOSExMon CHAOSArmTLB \
         CHAOSArmSysReg CHAOSFUPerm CHAOSGateFU CHAOSCov; do
    nm -C "$G5" | grep -q "gem5::$c" || { echo "MISSING class: $c"; MISSING=1; }
done
[ $MISSING -eq 0 ] && echo "injector classes: 22/22 OK"
# anchor 1: reg_chain golden (no injection)
OUT=$(mktemp -d)
timeout 300 "$G5" --quiet --outdir=$OUT configs/se/arm_chaos.py \
    --cpu O3 --cmd workloads/directed/reg_chain --workload_args "200" \
    2>/dev/null | grep -oE '^[0-9a-f]{16}$' | tail -1
echo "anchor1 reg_chain: $OUT_result (expect f247ef3fe6f02cfd)"
# anchor 2: injector sanity — CHAOSReg fires and changes the checksum
timeout 300 "$G5" --quiet --outdir=$OUT configs/se/arm_chaos.py \
    --cpu O3 --cmd workloads/directed/reg_chain --workload_args "200" \
    --chaos_reg --fault_type bit_flip --rng_seed 1 --first_clock 5000 \
    --max_faults 1 2>/dev/null | grep -cE 'FAULT|Old|New' || true
echo "anchor2 chaos_reg log lines present (expect >=1)"
```
（脚本收尾时对两个锚做硬判：checksum 相等 → `exit 0`，否则 `exit 1`。）

- [ ] **Step 3: 运行脚本，引用真实输出**

Run: `bash tools/verify_gem5_injectors.sh`
Expected: `injector classes: 22/22 OK`；anchor1 输出 `f247ef3fe6f02cfd`；anchor2 注入日志 ≥1 行；exit 0。

- [ ] **Step 4: Commit**

```bash
git add tools/verify_gem5_injectors.sh
git commit -m "feat(ss-fi): Task 0.1 全量注入器 gem5.opt 就位——22 类核对+reg_chain 双锚回归脚本"
```

---

### Task 0.2: 双通道内核模板 + fma_dual（首个内核）

**Files:**
- Create: `workloads/sdcshield/fma_dual.c`、`workloads/sdcshield/Makefile`
- Modify: `tools/runner.py:43-59`（GOLDEN_IDS 表加 `fmadual-golden-v1`）

**Interfaces:**
- Produces（后续所有内核任务复用的**双通道输出协议**）：stdout 打两行——`SDCSHIELD_FAILS=<uint>`（通道 A：原测试校验，>0 = Detected）+ 独立一行的 `<16-hex>`（通道 B：全状态 checksum，与既有 `_CHECKSUM_RE` 兼容）。exit code = `g_fails ? 1 : 0`。
- 提取规则（每个内核任务相同）：①计算与校验**忠实移植** sdcshield 测试体（指令形态保留：NEON/SVE intrinsic 原样）；②`random_device`→定长种子、`test_time_condition`→编译期 `ITERS`（确定性适配，检测语义不变，逐内核文档化）；③`report_fail`（首错即停）→ `g_fails++; break;`。

- [ ] **Step 1: 写 workloads/sdcshield/fma_dual.c**（移植源：`sdcshield/tests/cpu/fma/fma.cpp`——NEON `vfmaq_f32` vs `fmaf` 软件参考 + 1e-6 容差 + store/reload 一致性）

```c
/* fma_dual.c — dual-channel extraction of sdcshield test `fma`
 * (sdcshield/tests/cpu/fma/fma.cpp @ 07be34e2).
 * Channel A (detection semantics): NEON vfmaq_f32 vs fmaf software
 *   reference (approx_equal 1e-6) + store/reload consistency; first
 *   mismatch stops the loop (report_fail semantics), g_fails counts it.
 * Channel B (independent oracle): FNV-1a over every iteration's hardware
 *   result vector — separates Escape (clean check, wrong state) from
 *   Masked on clean runs.
 * Adaptations (detection-neutral, documented): random_device{}() -> seed
 *   42 xorshift32 (static C build, no libstdc++); test_time_condition ->
 *   fixed ITERS. */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <arm_neon.h>

#define VECTOR_SIZE 8
#ifndef ITERS
#define ITERS 200000
#endif

static uint64_t g_fails;
static uint64_t fnv1a(uint64_t h, const void *p, size_t n) {
    const uint8_t *b = (const uint8_t *)p;
    for (size_t i = 0; i < n; i++) { h ^= b[i]; h *= 1099511628211ULL; }
    return h;
}
static uint32_t xs32(uint32_t *s) {          /* deterministic data source */
    uint32_t x = *s; x ^= x << 13; x ^= x >> 17; x ^= x << 5; *s = x; return x;
}
static float frand(uint32_t *s, float lo, float hi) {
    return lo + (hi - lo) * ((float)xs32(s) / 4294967295.0f);
}
static void software_fma(const float *a, const float *b, const float *c, float *r) {
    for (int i = 0; i < VECTOR_SIZE; ++i) r[i] = fmaf(a[i], b[i], c[i]);
}
static int approx_equal(const float *x, const float *y) {
    for (int i = 0; i < VECTOR_SIZE; ++i) {
        float diff = fabsf(x[i] - y[i]);
        float tol = 1e-6f * fmaxf(fabsf(x[i]), fabsf(y[i]));
        if (diff > tol && diff > 1e-7f) return 0;
    }
    return 1;
}
int main(void) {
    alignas(16) float a[VECTOR_SIZE], b[VECTOR_SIZE], c[VECTOR_SIZE], result[VECTOR_SIZE];
    float ref[VECTOR_SIZE];
    uint32_t seed = 42;
    uint64_t h = 1469598103934665603ULL;
    for (uint32_t it = 0; it < ITERS; it++) {
        for (int i = 0; i < VECTOR_SIZE; i++) {
            a[i] = frand(&seed, -100.0f, 100.0f);
            b[i] = frand(&seed, -100.0f, 100.0f);
            c[i] = frand(&seed, -100.0f, 100.0f);
        }
        float32x4_t va_l = vld1q_f32(a),   va_h = vld1q_f32(a + 4);
        float32x4_t vb_l = vld1q_f32(b),   vb_h = vld1q_f32(b + 4);
        float32x4_t vc_l = vld1q_f32(c),   vc_h = vld1q_f32(c + 4);
        vst1q_f32(result,     vfmaq_f32(vc_l, va_l, vb_l));
        vst1q_f32(result + 4, vfmaq_f32(vc_h, va_h, vb_h));
        h = fnv1a(h, result, sizeof result);            /* channel B */
        software_fma(a, b, c, ref);
        float sb[VECTOR_SIZE], rb[VECTOR_SIZE];
        memcpy(sb, result, sizeof sb);
        memcpy(rb, sb, sizeof rb);
        if (!(approx_equal(result, ref) && memcmp(rb, result, sizeof rb) == 0)) {
            g_fails++;                                  /* channel A */
            break;                                      /* report_fail = 首错即停 */
        }
    }
    printf("SDCSHIELD_FAILS=%llu\n", (unsigned long long)g_fails);
    printf("%016llx\n", (unsigned long long)h);
    return g_fails ? 1 : 0;
}
```

- [ ] **Step 2: 写 Makefile（模板，后续内核任务追加目标）**

```makefile
# workloads/sdcshield/Makefile — dual-channel sdcshield extraction kernels.
# Static aarch64 ELFs (repo workload convention); host is aarch64 openEuler 24.03.
CC      ?= gcc
CFLAGS  ?= -static -O2 -Wall -Wextra
KERNELS = fma_dual

all: $(KERNELS)
fma_dual: fma_dual.c
	$(CC) $(CFLAGS) -o $@ $< -lm
clean:
	rm -f $(KERNELS)
.PHONY: all clean
```

- [ ] **Step 3: 构建 + 原生确定性验证（跑两次输出必须逐字节一致）**

Run: `cd workloads/sdcshield && make && ./fma_dual > /tmp/f1.log && ./fma_dual > /tmp/f2.log && diff /tmp/f1.log /tmp/f2.log && cat /tmp/f1.log`
Expected: 无 diff；输出两行——`SDCSHIELD_FAILS=0` 与 `<16-hex>`（记下该 hex = H_native）。

- [ ] **Step 4: gem5 三方一致（O3 无注入 == 原生）**

Run: `cd ../../ && timeout 600 ./CHAOS/gem5/build/ARM/gem5.opt --quiet --outdir=/tmp/g5fma configs/se/arm_chaos.py --cpu O3 --cmd workloads/sdcshield/fma_dual 2>/dev/null | grep -E 'SDCSHIELD_FAILS|^[0-9a-f]{16}$'`
Expected: `SDCSHIELD_FAILS=0` 且 hex == H_native（native==gem5 三方一致达成，golden = H_native）。若 gem5 单跑 >120s，回到 fma_dual.c 调低 `ITERS` 重跑 Step 3-4（ITERS 标定结果记入提交信息）。

- [ ] **Step 5: GOLDEN_IDS 登记**

`tools/runner.py` 的 `GOLDEN_IDS` 表（runner.py:43-59）追加一行：
```python
    "fmadual-golden-v1": "<H_native>",
```

- [ ] **Step 6: 回归 + Commit**

Run: `bash tools/verify_gem5_injectors.sh`（锚不变）
```bash
git add workloads/sdcshield/fma_dual.c workloads/sdcshield/Makefile tools/runner.py
git commit -m "feat(ss-fi): Task 0.2 双通道内核模板+fma_dual——NEON vfma vs fmaf 参考+独立 FNV checksum，native==gem5 三方一致"
```

---

### Task 0.3: classify/runner 的 sdcshield_dual oracle（Detected/Escape 类）

**Files:**
- Modify: `tools/classify.py`（新增 `classify_run_sdcshield()`）
- Modify: `tools/runner.py:471-489`（oracle 分支加 `sdcshield_dual`）
- Test: `tests/test_classify_sdcshield.py`

**Interfaces:**
- Produces: `classify_run_sdcshield(stdout, stderr, returncode, faults_injected, golden_checksum, timed_out) -> (cls, reason)`，`cls ∈ {SimulatorError, Hang, Crash, Inactive, Detected, Escape, Masked}`：
  - `Detected`：exit 正常收尾且 `SDCSHIELD_FAILS>0`（工作负载侧检测器报警——**本计划的核心新类**）
  - `Escape`：`SDCSHIELD_FAILS==0` 且 checksum ≠ golden（静默漏过——盲区）
  - `Masked`：`SDCSHIELD_FAILS==0` 且 checksum == golden
  - SimulatorError/Hang/Crash/Inactive 语义与既有六类一致（复用 `_is_simerr`/超时/陷阱判定）
- manifest 字段：`oracle.kind: sdcshield_dual`；runner 分支模式与既有 `fail_count`（runner.py:471-489）完全同构。

- [ ] **Step 1: 写失败测试 tests/test_classify_sdcshield.py**

```python
"""classify_run_sdcshield: dual-channel (SDCSHIELD_FAILS + 16-hex) oracle."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from classify import classify_run_sdcshield

GOLDEN = "0123456789abcdef"

def test_detected():
    out = "SDCSHIELD_FAILS=3\nfedcba9876543210\n"
    cls, why = classify_run_sdcshield(out, "", 1, 1, GOLDEN, False)
    assert cls == "Detected" and "fails=3" in why

def test_escape():
    out = "SDCSHIELD_FAILS=0\nfedcba9876543210\n"   # check clean, state wrong
    cls, _ = classify_run_sdcshield(out, "", 0, 1, GOLDEN, False)
    assert cls == "Escape"

def test_masked():
    out = f"SDCSHIELD_FAILS=0\n{GOLDEN}\n"
    cls, _ = classify_run_sdcshield(out, "", 0, 1, GOLDEN, False)
    assert cls == "Masked"

def test_inactive_zero_faults():
    cls, _ = classify_run_sdcshield("SDCSHIELD_FAILS=0\nx\n", "", 0, 0, GOLDEN, False)
    assert cls == "Inactive"

def test_simerr_priority():
    cls, _ = classify_run_sdcshield("", "panic: boom", 1, 1, GOLDEN, False)
    assert cls == "SimulatorError"

def test_crash_trap():
    cls, _ = classify_run_sdcshield("", "Simulated exit code: 133 (SIOT)", 133, 1, GOLDEN, False)
    assert cls == "Crash"
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest tests/test_classify_sdcshield.py -v`
Expected: FAIL — `ImportError: cannot import name 'classify_run_sdcshield'`。

- [ ] **Step 3: 实现 classify_run_sdcshield（classify.py，置于 classify_run 之后）**

```python
_SDCS_FAILS_RE = re.compile(r"^SDCSHIELD_FAILS=(\d+)\s*$", re.MULTILINE)

def classify_run_sdcshield(stdout, stderr, returncode, faults_injected,
                           golden_checksum, timed_out=False):
    """Dual-channel sdcshield oracle: SDCSHIELD_FAILS line (channel A =
    the test's own check -> Detected) + standalone 16-hex checksum line
    (channel B = independent full-state hash -> Escape/Masked split)."""
    if _is_simerr(stderr):
        return "SimulatorError", "gem5 panic/assert (tool failure)"
    if timed_out and not stdout:
        return "Hang", "timeout, no output"
    if faults_injected == 0:
        return "Inactive", "0 valid injections"
    text = stdout + "\n" + stderr
    m = _SDCS_FAILS_RE.search(text)
    if not m:
        return "Crash", "no SDCSHIELD_FAILS line (aborted before epilogue)"
    fails = int(m.group(1))
    if fails > 0:
        return "Detected", f"sdcshield check fired: fails={fails}"
    ck = extract_checksum(text)          # 复用既有 16-hex 提取
    if ck and ck.lower() == (golden_checksum or "").lower():
        return "Masked", "check clean, state matches golden"
    return "Escape", "check clean, state deviates (blind spot)"
```
（`extract_checksum` 若私有则导出；`_is_simerr` 已存在——与 fail_count 分支同一来源。trap/exit≠0 且有 FAILS 行的情况归 `Detected`（检测器先于崩溃触发）；无 FAILS 行的 trap 走上面 `Crash`。）

- [ ] **Step 4: runner.py oracle 分支（与 fail_count 同构，插在其后）**

```python
    elif oracle_kind == "sdcshield_dual":
        from classify import classify_run_sdcshield
        cls, reason = classify_run_sdcshield(
            r.stdout or "", r.stderr or "", r.returncode,
            faults, args.golden_checksum, timed_out)
```

- [ ] **Step 5: 测试通过 + 端到端实跑验证**

Run: `python3 -m pytest tests/test_classify_sdcshield.py -v`
Expected: 6/6 PASS。
端到端（真实注入检出闭环）：`--chaos_fpu --fault_mask` 目标 mantissa 位段跑 fma_dual 一个 seed，引用真实输出证明出现 `RESULT: ... classification=Detected`（或如实记录该 seed 是 Masked 并换 seed 至首个非 Masked——证明 oracle 通路本身工作）。
回归：`python3 -m pytest tests/ -q`（既有套件全绿）。

- [ ] **Step 6: Commit**

```bash
git add tools/classify.py tools/runner.py tests/test_classify_sdcshield.py
git commit -m "feat(ss-fi): Task 0.3 sdcshield_dual oracle——工作负载侧 Detected/Escape 分类+runner 路由+pytest 6 用例"
```

---

### Task 0.4: campaign.py 的 Detected/Escape 列与 P_detect

**Files:**
- Modify: `tools/campaign.py:363-384`（cells.csv 列与汇总）+ 分类计数循环
- Test: `tests/test_campaign_sdcshield_columns.py`

**Interfaces:**
- Produces: cells.csv 新列 `Detected, Escape, P_detect, P_detect_lo, P_detect_hi`；`P_detect = Detected/(Detected+Escape)`（分母 0 时置 NaN 并在 summary.md 标注 `no-reachable-faults`）；Wilson 区间复用 `campaign.py:55-67` 既有实现。其余列（SDC/Crash/...）保持——兼容非 dual 内核混跑同一战役。

- [ ] **Step 1: 失败测试**（构造含 Detected/Escape 行的临时 cells 输入，断言新列存在且 P_detect/区间计算正确；0/5 时 P_detect=0、区间含 rule-of-3；5/5 时 P_detect=1）
- [ ] **Step 2: 跑 pytest 确认 FAIL**
- [ ] **Step 3: 实现**：tally 循环加 `Detected`/`Escape` 计数；`cells.csv` 列拼接处加四列；Wilson 复用。summary.md 末尾追加 per-cell `P_detect` 表。
- [ ] **Step 4: pytest PASS + 用 Task 0.3 端到端产物跑一次 3-run 迷你 campaign，引用真实 cells.csv 行**
- [ ] **Step 5: Commit**：`feat(ss-fi): Task 0.4 campaign Detected/Escape/P_detect 列+pytest`

---

### Task 1.1: 既有内核 × sdcshield 测试域对照审计

**Files:**
- Create: `docs/sdcshield-fi/kernel-provenance-audit.md`

**Interfaces:**
- Produces: 三分类裁决表，锁定 Phase 1 的复用/新增清单——**复用升级**（movbe、crc_state→双通道化，Task 1.8/1.9）、**新增提取**（fma 已在 0.2；fpu_special_values/lsu_store_forward/l2c_cross_cache_line/memcpy_l1d/sve512_f64_chain/agu_stress_2src，Task 1.2-1.7）、**对照参考**（gemm_float/double、svd_iterative、fma_reduction、madd_chain、smulh_adds——保持 checksum-only，战役中作"无检测器基线"对照臂）。

- [ ] **Step 1: 逐行核对**（读源码，非 README）：`workloads/directed/{movbe_kernel,crc_state_kernel,gemm_double_kernel,...}.c` vs `sdcshield/tests/cpu/` 对应测试——计算形态、校验模式（常量 golden / in-run 参考 / 往返）、指令形态（NEON/SVE/标量）三列对照。
- [ ] **Step 2: 写裁决表**（每行：sdcshield 测试 → 既有内核/新增 → 检测语义等价性判定 → 依据文件:行号）。
- [ ] **Step 3: Commit**：`docs(ss-fi): Task 1.1 内核语义对照审计——复用/新增/对照三分类`

---

### Task 1.2–1.7: 六个新双通道内核（每 Task 一内核一 commit）

统一模板与验证协议（每个 Task 相同，以下只写各内核的**差异内容**）：

**共同 Files:** Create `workloads/sdcshield/<name>_dual.c`；Modify `workloads/sdcshield/Makefile`（KERNELS 追加）、`tools/runner.py`（GOLDEN_IDS 加 `<name>dual-golden-v1`）。

**共同 Steps（每内核 6 步）：**
- [ ] S1 写 `<name>_dual.c`：忠实移植计算与校验（指令形态原样），套 Task 0.2 双通道模板（`SDCSHIELD_FAILS=` + 16-hex 行 + exit 规则 + `g_fails++/break` 首错即停）；`random_device`→定种子、时间循环→`ITERS`（编译期，注释文档化）。
- [ ] S2 Makefile 加目标 + `make` 零警告。
- [ ] S3 原生跑两次 diff 逐字节一致，记 H_native。
- [ ] S4 gem5 O3 无注入 == H_native；ITERS 标定单跑 ≤120s（写入提交信息）。
- [ ] S5 GOLDEN_IDS 登记 + `bash tools/verify_gem5_injectors.sh` 回归。
- [ ] S6 Commit：`feat(ss-fi): Task 1.x <name>_dual——<检测语义一句话>，native==gem5 三方一致`。

各内核差异：

**Task 1.2 fpu_special_values_dual**（源：`sdcshield/tests/cpu/fma/fpu_special_values.cpp`）
- 检测语义：特殊值（±Inf/NaN/±0/次正规/最大正规）经 NEON FMA 运算后**与 golden 常量逐字节 memcmp**（非容差比较）——常量 golden 型，J2 的"无容差"对照内核。
- 通道 B：对每轮运算输出向量 FNV；首错即停。

**Task 1.3 lsu_store_forward_dual**（源：`sdcshield/tests/cpu/` 下 `lsu_store_forward_arm.cpp`——先 `grep -rl lsu_store_forward sdcshield/tests/` 定位）
- 检测语义：store→同地址 load 转发窗口的多样长度/偏移组合，转发结果 vs 重取（reload）一致性校验——直击 CHAOSLSQFwd F5/F6 与 CHAOSL1DForward 位点。
- 通道 B：对所有 buffer 状态 FNV。

**Task 1.4 l2c_cross_cache_line_dual**（源：`l2c_cross_cache_line_arm` 测试）
- 检测语义：跨 cache line 的 store/reload 往返一致性（CORE179 判别式）；工作集按 L2 域定尺寸（对齐既有 l2c 臂 512KiB/8-way）。

**Task 1.5 memcpy_l1d_dual**（源：`memcpy_l1d_size` 测试）
- 检测语义：L1D 域尺寸 memcpy 后源/目的逐字节 memcmp——cache data 阵列位点的直接靶。

**Task 1.6 sve512_f64_chain_dual**（源：`sve512_f64_chain_arm` 测试）+ **arm_chaos.py 加 `--sve_vl_se` 参数**
- 检测语义：SVE 全长 f64 FMLA 串行依赖链 vs 标量参考；构建 `-march=armv8.2-a+sve -msve-vector-bits=512`。
- **附加修改（本 Task 内）**：`configs/se/arm_chaos.py` argparse 加 `--sve_vl_se`（int, default 0=不改），实例化处 `isa = ArmISA()` → 按需 `ArmISA(sve_vl_se=args.sve_vl_se)`（参照 `sdcshield/scripts/eigen-sve-double/gem5/se_sve.py:49` 的既有用法）；验证 = 该内核 gem5 跑 `--sve_vl_se 4` 三方一致，且 reg_chain 不传参数行为不变（回归）。

**Task 1.7 agu_stress_2src_dual**（源：`agu_stress_2src` 测试）
- 检测语义：2 源加载 + ALU 旋转 + store/reload/store 的 AGU 吞吐压测链，结果 vs 标量参考（CORE179 触发配方族）。

---

### Task 1.8: movbe 双通道升级

**Files:** Modify `workloads/directed/movbe_kernel.c`、`tools/runner.py`（golden 改 `movbedual-golden-v1`）
- 保留既有 `iters=N fails=M` 输出（兼容 fail_count 语义）；追加通道 B：全状态 FNV 16-hex 独立行 + `oracle.kind: sdcshield_dual` 适配（SDCSHIELD_FAILS 行由 fails= 行别名输出——实现时直接打印 `SDCSHIELD_FAILS=<M>` 第二行，原行保留）。
- 验证：native 两次一致 + gem5 三方一致 + **既有 movbe golden 行为不变对照**（无注入 fails=0）。GOLDEN_IDS 新条目，旧 `movbe-failcount-v1` 保留不删。

### Task 1.9: crc_state 双通道升级
同 Task 1.8 模式（`crc_state_kernel.c`）。

（1.8/1.9 各自完整走 S1-S6 六步协议后 commit。）

---

### Task 2.1: 无注入 FP 底噪臂（J1 判据）

**Files:**
- Create: `tools/ss_fp_floor.sh`、`campaigns/ss-fp-floor.yaml`

- [ ] **Step 1: 写战役**——全部 9 个双通道内核（fma/fpu_special/lsu_sf/l2c/memcpy_l1d/sve512/agu/movbe/crc_state）× N=20，`max_faults: 0`（无注入；campaign manifest 走 `limits: {max_faults: 0}` 或直接 gem5 无 `--chaos_*` 裸跑——实现取后者更简单：脚本循环 `arm_chaos.py --cpu O3 --cmd <kernel>` ×20/内核）。
- [ ] **Step 2: 跑**：`bash tools/ss_fp_floor.sh`（预期总 run 数 9×20=180，单跑 ≤120s，JOBS=8）。
- [ ] **Step 3: 裁决 J1**：全部 180 run 必须 `SDCSHIELD_FAILS=0` + checksum==golden + exit 0。任何失败→根因（浮点容差？ITERS 边界？）→修复重跑（此为 J1 判据，预注册不可降级）。
- [ ] **Step 4: Commit**：`feat(ss-fi): Task 2.1 FP 底噪臂——9 内核×N=20 全绿（J1 PASS）+ artifacts/ss-fp-floor/`

---

### Task 2.2: Tier1-A 浮点臂战役（CHAOSFPU 瞬态位段，N=400）

**Files:**
- Create: `campaigns/ss-t1a-fpu.yaml`、`artifacts/ss-t1a-fpu/`（产物）

**Interfaces:** YAML 仿 `campaigns/t3-1-fsu-formal.yaml`（FPU v3 源读 hook、trigger cycle 5000、`rng_master_seed 20260825`）：

```yaml
campaign_id: ss_t1a_fpu
workload:
  oracle_kind: sdcshield_dual      # golden_id 逐内核 --workload-golden 覆盖
trigger: {mode: cycle, value: 5000}
limits: {max_faults: 1, max_ticks: 0}
injector: fpu
config_family: C0
axes:
  bit_segment: [sign, exp, mantissa, all]
  fault_model: [transient_bit_flip]
defaults:
  rng_master_seed: 20260825
  probability: 0.0005              # 随机位点采样（runner --probability 语义）
```

- [ ] **Step 1: 跑**——3 浮点内核（fma_dual/fpu_special_values_dual/sve512_f64_chain_dual）× 4 位段 × N=400 = 4,800 runs（`campaign.py --n-per-cell 400 --binary ... --workload-golden <id>` 逐内核；sve512 记得透传 `--sve_vl_se 4`——若 campaign.py 无透传口则加 `--gem5-extra-args` 透传参数，属本 Task 内小改+pytest）。
- [ ] **Step 2: cells.csv + summary 落盘**；`P_detect` 按内核×位段矩阵化。
- [ ] **Step 3: J2 初裁**（fma 类 mantissa vs sign/exp 位段 P_detect 对比；fpu_special_values 是否 →1.0）——数据落盘，正式裁决留 Task 2.7。
- [ ] **Step 4: Commit**：`feat(ss-fi): Task 2.2 FPU 瞬态位段臂——3 内核×4 位段×N=400，P_detect 矩阵+J2 初裁`

### Task 2.3: Tier1-B PhysReg 臂（N=400）

仿 `campaigns/prf-formal.yaml`（physreg 路由既有）：6 内核（3 浮点 + lsu_sf/movbe/memcpy_l1d）× {arch_frontend 层, 全位随机} × N=400。bit_indices 轴用既有分层采样（`[[0],[31],[32],[63]]`）；golden 逐内核。产物 `artifacts/ss-t1b-physreg/`。Commit 同模式。

### Task 2.4: FUPerm 永久臂（J3 判据，N=200）

**Files:**
- Modify: `tools/runner.py`（组件路由加 `fuperm` → arm_chaos.py 对应 `--chaos_fuperm`；先读 `CHAOS/gem5/src/CHAOSFUPerm/CHAOSFUPerm.py` 确认参数名：per-OpClass 固定 XOR mask）
- Create: `campaigns/ss-t2-fuperm.yaml`
- [ ] S1 runner fuperm 路由 + 注入日志计数（仿 fpu 分支）+ pytest（manifest 路由单测）
- [ ] S2 战役：fma_dual × {fpadd/fpmul OpClass} × N=200（对照 Task 2.2 的 fma 瞬态 cell）
- [ ] S3 J3 裁决：FUPerm P_detect vs CHAOSFPU 瞬态 P_detect，Wilson CI 不重叠性检验，数据落盘
- [ ] S4 Commit：`feat(ss-fi): Task 2.4 FUPerm 永久臂——runner fuperm 路由+N=200，J3 结构盲区裁决`

### Task 2.5: Tier1-C 访存/存储臂（N=400）

- **lsq_fwd 臂**（仿既有 F5/F6 模式）：lsu_store_forward_dual/l2c_cross_cache_line_dual/movbe_dual × {fwd_source_sub, phase_offset} × N=400。
- **l1dfwd 臂**（PCE）：同 3 内核 × N=400。
- **cache 臂**（`arm_chaos_cache.py` 路由）：memcpy_l1d_dual × {l1d data none, l1d data secded, l2 data none, l2 data secded} × N=400（directed block addr 用 Task 1.5 标定出的活跃块）。
- **mem 臂**：memcpy_l1d_dual × {none, secded, ecc_logic_fault} × N=400。
产物 `artifacts/ss-t1c-{lsqfwd,l1dfwd,cache,mem}/`；每臂一 commit 或一 commit 四子表（实现时按"一单元"拆：lsq_fwd+l1dfwd 一个、cache+mem 一个——同为访存域通路但注入器不同，**拆两个 commit**）。

### Task 2.6: 整数/DUE 臂（N=100-400）

- **exec 臂**（int 写回，既有路由）：crc_state_dual/agu_stress_2src_dual × {bitSegment all/low/mid/high} × N=400（Exec 在既有 int 内核上 0/768 全 Masked——CRC/AGU 内核是否同样免疫是本臂的科学问题）。
- **DUE 臂 N=100**：fma_dual × {rob entry_bitflip, rat f5_substitute, iq wake_omit} × N=100——SDC/DUE（Crash/Hang）拆口径报告（预期 DUE 主导，检出=Crash 类非静默；`P_detect` 只对静默类计算，DUE 单列）。
- BPU 臂**不跑**：decoupledFrontEnd 与 stdlib 板不兼容（arm_chaos.py:589-596 注记 + CE-3 收口先例）——引用 Phase 16 既有证据（dir_flip 384/384 Masked 等），在 Task 2.7 报告边界节声明。

### Task 2.7: SE 主战役裁决报告

**Files:**
- Create: `docs/sdcshield-fi/se-verdict.md`

- [ ] 汇总 2.1-2.6 全部 cells.csv → 检出率矩阵（内核域 × 位点 × 故障模型，P_detect + Wilson + raw/active 双口径 + Detected/Escape/Masked/DUE/Inactive 全分类计数）。
- [ ] J1-J3 正式裁决（预注册判据，逐条 PASS/FAIL/不可裁决+归因）；J4 留待 Task 3.5。
- [ ] 盲区归因：每个 `Escape` 占比 >5% 的 cell 给机理假设（容差窗/校验窗口外/双通道同损/Inactive 稀释）+ 证据链接（注入日志 old/new 值 + readtrace 若可用）。
- [ ] 无检测器对照：checksum-only 内核（gemm_double/svd_iterative）同臂 SDC 率 vs 双通道内核 `(Detected+Escape)` 率的一致性（自洽性检查）。
- [ ] Commit：`docs(ss-fi): Task 2.7 SE 主战役裁决——J1-J3 裁决+P_detect 矩阵+盲区归因`

---

### Task 3.1: FS 第二磁盘 + guest 内 sdcshield 就位

**Files:**
- Create: `tools/fs_mk_sdcshield_disk.sh`（mke2fs -d 无 root 制盘）、`gem5-fs-work/sdcshield.img`（产物，gitignore）、`gem5-fs-work/guest_hello.sh`（readfile 脚本）
- Modify: `configs/se/fs_checkpoint.py`（加 `--disk2` 参数挂第二磁盘；`configs/se/arm_chaos_fs.py` 同）
- gitignore：`gem5-fs-work/`

- [ ] **Step 1: 制盘**（sdcshield 静态化处理：真二进制是动态链接——FS 真机有加载器，无需静态；拷贝 `sdcshield/builddir/sdcshield` + `ldd` 依赖的 .so 到盘内 `/libs/`）：
```bash
mkdir -p fsroot/libs fsroot/bin
cp sdcshield/builddir/sdcshield fsroot/bin/
for so in $(ldd sdcshield/builddir/sdcshield | awk '/=> \//{print $3}'); do cp -L "$so" fsroot/libs/; done
truncate -s 256M gem5-fs-work/sdcshield.img
mke2fs -d fsroot -t ext4 gem5-fs-work/sdcshield.img
```
- [ ] **Step 2: readfile 通路验证**——`guest_hello.sh`：`mount /dev/vdb /mnt && LD_LIBRARY_PATH=/mnt/libs /mnt/bin/sdcshield --list-tests | head -5; /sbin/m5 exit`；`fs_checkpoint.py --phase=boot` 重建 checkpoint（磁盘集变了）→ `--phase=inject --readfile guest_hello.sh`，从 `board.terminal` 引用真实 guest 输出（≥350 用例列表头）。
- [ ] **Step 3: guest 内 fma 真跑全绿**：`/mnt/bin/sdcshield -e fma -t 100 -n 1 -f no`，terminal 捕获 `exit: pass`。
- [ ] **Step 4: Commit**：`feat(ss-fi): Task 3.1 FS 第二磁盘+readfile 通路——guest 内 --list-tests 与 fma pass 实证`

### Task 3.2: fs_checkpoint inject × 真二进制打通（无注入全绿）

- [ ] inject 阶段跑真二进制（guest 脚本执行 fma 后 `m5 exit`）；结果回收三通道：`board.terminal`（result: pass/fail）+ `m5 writefile` 导出 guest 侧 YAML 日志 + dmesg（oops）。outcome 分类器 `tools/fs_sdcshield_classify.sh`（result:fail=Detected / Oops=Crash(DUE) / 超时=Hang / pass+无注入对照=基线）。
- [ ] 无注入 × 20 全绿（FS 版 J1）。
- [ ] Commit。

### Task 3.3/3.4: FS 战役（TLB+Cache / PTW+SysReg+Mem，N=32）

仿 `tools/fs_tlb_formal.sh` 驱动模式（restore ~13s/run、JOBS=4、`timeout 150` 量级——真二进制运行更重，超时按 Task 3.2 实测标定）：
- 3.3：`--injector armtlb --tlb-pfn-select-mode mapped_page`（F5 活页）+ `--injector` cache data（fs_checkpoint 若无 cache 臂则经 arm_chaos_fs.py 补挂，属 3.3 内小改）× {fma, memcpy_l1d 真测试} × N=32。
- 3.4：ptw + sysreg + mem{none,secded} × fma × N=32。
- 产物 `artifacts/ss-fs-{tlb,cache,ptw,sysreg,mem}/`；真二进制 `result: fail` 率 + oops/ESR 分布（复用 t3-6 的 dmesg/ESR 提取）。

### Task 3.5: SE-FS 交叉一致性 + FS 报告（J4）

**Files:** Create `docs/sdcshield-fi/fs-cross-validation.md`
- [ ] 共享臂（Cache data / Mem secded）对比：SE 内核 P_detect vs FS 真二进制 result:fail 率；DUE 构成差异（FS 有 kernel oops 通道、SE 无）如实分列。
- [ ] J4 裁决（描述性）+ 差异归因（真实 OS 调度/框架 fork 开销/EDAC 通道不可见）。
- [ ] Commit。

---

### Task 4.1: 登记收尾

- [ ] `AGENT_TASKS.md`：SSFI-0.1..SSFI-4.2 全任务单行登记（depends 链 + assert_hint）；deferred 三项登记（见下）。
- [ ] `task_plan.md` Phase 8 勾选核对 + `progress.md` 收官日记录（每任务真机输出摘要）。
- [ ] Commit：`docs(ss-fi): Task 4.1 登记收尾——AGENT_TASKS/task_plan/progress 三处同步`

### Task 4.2: 诚实边界终审

**Files:** Create `docs/sdcshield-fi/honest-boundaries.md`
- [ ] 必列边界：①mce_check/EDAC 通道在 gem5 不可模型化（guest EDAC 计数恒 0，CHAOSRAS 的 ERR* 抑制是 gem5 内部事件，guest 不可见）；②SE 提取内核保真度论证（计算+校验忠实移植，适配项逐内核列表：定种子/ITERS/xorshift 替代 mt199737）；③真二进制 SE 三重阻断（prctl fatal / pre-main 崩溃 @123,543,000 tick / 信号忽略——`fi_research/probes/se_sdcshield_probe.py` 留档）；④BPU 臂不可挂（引用既有证据）；⑤AddrPath/LSQ-AddrPath 位点 FS+O3 才可达（关联 D-FS-O3-switch）；⑥ρ/检出率均为 gem5 条件概率非 FIT、单机未确认（沿袭 method.md 诚实边界表）。
- [ ] Commit：`docs(ss-fi): Task 4.2 诚实边界终审——六项边界逐条登记`

## Deferred 登记（AGENT_TASKS.md）

- `D-SSE-REAL-BIN`：gem5 SE prctl stub（syscall_emul.cc，~5 行）+ 真二进制 pre-main 崩溃根因（remote-gdb backtrace 定位 ld.so/ctor 路径）→ 若双双落地可把 SE 主战场升级为真二进制。解锁：独立立项（本计划以提取内核承载，不阻塞）。
- `D-FS-O3-SWITCH`：维持既有登记（FS 臂 atomic-only 边界在 Task 4.2 声明）。
- `D-EDAC-CHANNEL`：EDAC/mce_check guest 可见错误通道（需 gem5 RAS→guest 注入模型，超出本计划）。

## Self-Review 清单（写完自查，执行者不再重复）

1. **覆盖**：用户三问——FS vs SE（裁决于架构节+J 判据+Phase 3 交叉）；微架构位点（Tier1/2/3 全注入器矩阵，BPU/AddrPath 边界显式）；故障注入方式（瞬态位段 F1/FUPerm 永久/F5 错源/F6 相位/PCE/ECC 三态）。指标/判据/N/统计口径齐备。
2. **无占位符**：Task 0.2/0.3 含完整代码；1.2-1.9 逐内核有源路径+语义+协议（计算体忠实移植是提取规则本身，非占位）；2.x/3.x 有 YAML/命令/裁决步骤。
3. **命名一致**：`SDCSHIELD_FAILS`/16-hex 行/`sdcshield_dual`/`classify_run_sdcshield`/`P_detect`/`<name>dual-golden-v1`/`artifacts/ss-*`/`docs/sdcshield-fi/` 全文一致。
