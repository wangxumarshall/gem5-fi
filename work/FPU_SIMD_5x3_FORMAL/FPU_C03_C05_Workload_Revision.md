# C03 / C05 负载修订说明

批号 `FPU_SIMD_5x3_FORMAL` · 生成 2026-11-23

不改变 12 个故障模型的 `FaultMechanism / TargetInstruction / Hook / fault 操作 /
EligibleEventCondition`。仅修改负载的**指令顺序**（C03）与**分支/循环结构**（C05）。

---

## 1. C03 修订：覆盖提前到首次消费之前

### 修改前（错误：消费在覆盖前）
```asm
fpu_target_r:
    fadd  s0, s1, s2        ; faulted s0
    fmov  w10, s0           ; 消费错误
    str   w10, [x9]         ; 错误入 raw0
    movz  w7, #0x3f80
    movk  w7, #0, lsl #16
    fmov  s0, w7            ; 覆盖（太晚）
```

### 修改后（正确：覆盖在消费前）
```asm
fpu_target_r:
    fadd  s0, s1, s2        ; faulted s0  (phys P1)
    movz  w7, #0x3f80
    movk  w7, #0, lsl #16
    fmov  s0, w7            ; 立即覆盖 s0 = 1.0 (phys P2，P1 失效)
    fmov  w10, s0           ; 消费覆盖后的正确值 (P2)
    str   w10, [x9]         ; raw0 = 1.0 (== Control)
```

各模型覆盖指令（写后清除原目的地，均为**写型**、不读故障值）：
| kind | 覆盖指令 | 说明 |
|---|---|---|
| scalar (M001–M005) | `movz/movk + fmov s0, w7`（s0=1.0） | 写 s0，不读 s0 |
| gpr (M006) | `mov x0, #0` | 写 x0，不读 x0 |
| fcmp (M007) | `cmp xzr, xzr` | 确定性写 NZCV，不读 faulted NZCV |
| vec/xtn2 (M008–M012) | `movi v0.16b, #0` | 写 v0=0，不读 v0 |

**证据链**：`fault_inject`（故障施加）→ `target_end` dest 记录**错误值**
（如 M001 `0x40800005`）→ 覆盖指令重命名目的寄存器（错误值失效）→ 消费者读
覆盖后的正确值 → `raw0`/`raw2` 与 Control 逐字节一致。修订后 **n_direct=0**
（无消费者读取故障版本的目的寄存器），`raw0_diff=False`，`overwritten=True`。

---

## 2. C05 修订：训练与测量解耦，T03 命中 squash

### 修改前（N=64，T03=58 commit，无法证明 squash）
单循环，每迭代执行目标 1 次，末次（ordinal 64）误预测 squash，但
T03=ceil(0.9×64)=58 落在已提交事件上。

### 修改后（N=9，T01/T02/T03 = 1/5/9，T03=9=squash）
把分支预测器训练（TRAIN=40 次“taken”）与目标执行（测量 9 次）解耦，
使 T03=ceil(0.9×9)=9 精确落在误预测后的推测执行上：

```asm
_start:
    msr fpsr, xzr; msr fpcr, xzr
    adr x20, outbuf
    mov x21, #0            ; 合格序数/输出槽位
    mov x19, #40           ; 训练迭代计数（目标被 gate 关闭）
    mov x24, #9            ; 测量阶段目标执行次数
    mov w4, #0x3f800000; fmov s21, w4
c05_loop:
    mov w4, #0x3f800000
    mov w26, #0x40000000
    cmp x19, #0
    ccmp x24, #1, #0, eq   ; Z = (x19==0 && x24==1) -> 末次测量
    csel w4, w26, w4, eq   ; 末次 -> s20=2.0(not-taken)
    fmov s20, w4
    fdiv s20, s20, s21     ; ×8（延迟分支解析）
    fcmp s20, s21
c05_branch:
    b.eq c05_taken         ; 训练 48 次 taken，末次 mispredict
    b   c05_done
c05_taken:
    cbz x19, c05_emit      ; 训练期跳过目标
    sub x19, x19, #1
    b   c05_loop
c05_emit:
    add x8, x20, x21, lsl #7; add x9, x8, #40
    <record header> <load inputs>
fpu_target_r:
    <target> <consume> <flags>
    add x21, x21, #1; sub x24, x24, #1; b c05_loop
c05_done:
    <标记槽位 x21(=8) 为 0x55 squashed> <写 9 条记录> exit
```

- 训练期 40 次 + 测量期 8 次共 48 次“taken” → 预测器可靠，末次（x24==1）
  `b.eq` 预测 taken、实际 not-taken → 真实误预测。
- 目标在预测 taken 路径、分支解析（8×FDIV 延迟）前被推测执行，随后被 squash。
- `ccmp`+`csel` 无分支地选择 1.0/2.0，避免引入第二个误预测分支；`cbz` gate
  在训练期跳过目标（目标不执行，不计入合格事件）。

---

## 3. 新旧 eligible-event / ordinal 对照

| 上下文 | 旧 N | 旧 ordinal | 新 N | 新 ordinal |
|---|---|---|---|---|
| C03（12 模型） | 100 | 10/50/90 | **100**（不变） | 10/50/90（不变） |
| C05（12 模型） | 64 | 7/32/58 | **9** | **1/5/9** |

C05 新 N=9 满足 N≥3、三个 ordinal 互不相同（1/5/9）。T01/T02 落在已提交测量
目标上（错误提交传播 → SDC），T03=9 落在误预测推测路径上（错误 squash）。

---

## 4. 保护与可复现

- 旧负载源码/ELF 备份于
  `work/FPU_SIMD_5x3_FORMAL/workloads_pre_r2_backup/`。
- 旧 C03/C05 运行与 Trace（`runs/`、`counts/`）保留未动。
- 新运行写入 `runs_r2/`、`counts_r2/`。
- 生成器 `scripts/gen_5x3_workloads.py`（`N_C05=9, TRAIN=40`）；可复用：
  `python3 scripts/gen_5x3_workloads.py`。