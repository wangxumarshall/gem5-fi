# 鲲鹏920 SDC 研究缺口补全实施计划（第二份：注入器扩展 + kernel + FS 流水线）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补全原方案文档对照源码核查出的全部剩余缺口：TLB 字段级注入（pfn_to_mapped F5）、SysReg value_to_legal（F5）、method2/3 定向 kernel（ptr_chase + 7 类转发构造 + no-op 相位变体）、FS checkpoint 流水线（解锁全部 FS 端到端验证）、L1I 语义字段定向、CHAOSMem 扩展。

**Architecture:** 六块独立工作按依赖排序。前两块是已有注入器的 F5 模式扩展（最小 diff）。kernel 批次是纯 C（无 gem5 改动，构建快）。FS checkpoint 流水线复用已验证的 `m5.checkpoint(dir)` Python API（simulate.py:401 已核实）+ 已有的 kp920_proxy_fs 参数。L1I 语义字段扩展 CHAOSCache 的定向能力到指令编码字段位段。

**Tech Stack:** gem5 v25.1.0.1（vendored `CHAOS/gem5/`）、C++20 SimObject、Python 3.11、gcc -static aarch64 native 编译 kernel、CLAUDE.md 补丁纪律（一补丁一单元 + 真机自验证 + 推 `fi-wangxu`）。

**Spec:** `docs/KUNPENG920-的SDC故障的微架构故障注入和规律研究的详细方案设计和需求开发实现文档.md`（原方案——本计划对照其 §5.1D/§5.4D/§5.7B/§5.8C/§10.2 逐项补缺）；执行蓝图 `docs/KUNPENG920-SDC研究方案-系统完备版.md`。

**与第一份计划的关系**：`docs/superpowers/plans/2026-09-01-remaining-sdc-work.md` 已覆盖 spec_leak/CHAOSBPU/runner-cache/method1-formal。本计划覆盖**其余全部**缺口，两份计划无重叠。

## Global Constraints

- 构建：`cd CHAOS/gem5 && source /home/sdc/gem5-deps/env.sh && scons build/ARM/gem5.opt -j16`（禁 -j126 OOM）
- 运行前必 `source /home/sdc/gem5-deps/env.sh`
- gem5.opt：`CHAOS/gem5/build/ARM/gem5.opt`
- 注入器改动后同步：`cp -f CHAOS/<name>/* CHAOS/gem5/src/<path>/ && diff -rq` 验证 IDENTICAL
- 提交纪律：一补丁一单元 + 零 CHAOS 源警告 + 真机验证引用真实输出 + 不相关回归 + `git push origin fi-wangxu` + **无 "Co-Authored-By: Claude" 尾注**
- 诚实纪律：单次注入未触发 SDC 时如实标注"机制已验证，formal 待 n=384"；FS 端到端验证失败时如实记录原因
- 注入器统一骨架：rng lambda 初始化 + `>=` 概率比较 + `Site:` 日志字段（runner 按 `Site:` 行计数）+ G7 零警告
- kernel 编译：`gcc -static -O2 -o workloads/directed/<name> workloads/directed/<name>.c`（native aarch64，无交叉）；验证 native 2x 确定性后 gem5 golden

---

### Task 1: CHAOSArmTLB 扩展——pfn_to_mapped_page（F5 静默换页）+ targetField 字段级

方案 §5.7B："`pfn_to_mapped_page`（F5，翻到另一活页→静默 SDC）、`targetField ∈ {pfn,ap,xn,attridx,ng,asid}`、I-TLB 挂载"。现状：CHAOSArmTLB 仅翻 hit entry 的 `pfn`（bit_flip/stuck，随机位）——**F5 定向换到另一活页（最危险路径）与 AP/XN/AttrIndx/nG/ASID 字段级均未实现**。

**研究结论（已核实）**：
- `TlbEntry` 定义在 `arch/arm/pagetable.hh:170`，字段已核实：`Addr pfn`（line ~249 区域）、`uint8_t ap`（访问权限）、`bool xn`（Execute Never）、`uint8_t innerAttrs/outerAttrs`（AttrIndx 语义）、`uint16_t asn`（ASID）、`vmid_t vmid`、`bool ignoreAsn`（nG 语义）。这些全是 public 可直接写。
- 现有 hook：`CHAOSArmTLB::maybeCorrupt(ArmISA::TlbEntry *entry, Addr va)`（CHAOSArmTLB.cc:75 起）——在 `TLB::lookup` hit 后调用。扩展点就在此函数内。
- **F5 换活页的实现**：maybeCorrupt 的签名只有当前 entry——要找"另一活页"需枚举 TLB 其他 entries。`TLB` 类有 entry 容器（`tlb.cc` 内部）。**诚实设计**：TLB 容器不公开遍历；改用 `entry->pfn` 的高位偏移替换（`pfn += 0x40000`，即 +1GB 物理页帧偏移——落在同物理内存另一页的概率高，但**不保证"活页"**）。这是代理实现：翻到"另一物理页帧"，命中已映射页→SDC、未映射→DUE。日志如实记录 `pfn_to_offset` 模式名与偏移，不声称"另一活页"（活页枚举需 TLB 容器遍历，留 FS 深改）。

**Files:**
- Modify: `CHAOS/CHAOSArmTLB/CHAOSArmTLB.py`（加 targetField + pfnOffset 参数）
- Modify: `CHAOS/CHAOSArmTLB/CHAOSArmTLB.hh`（加字段成员）
- Modify: `CHAOS/CHAOSArmTLB/CHAOSArmTLB.cc`（maybeCorrupt 加 targetField 分支）
- Modify: `configs/se/arm_chaos_fs.py`（加 --tlb_target_field/--tlb_pfn_offset 开关）
- 同步：`CHAOS/gem5/src/arch/arm/CHAOSArmTLB/`

**Interfaces:**
- Consumes: 现有 `maybeCorrupt(TlbEntry*, Addr)` hook（tlb.cc:164-168 调用点不变）
- Produces: `targetField ∈ {pfn,ap,xn,attridx,ng,asid}` 字段级注入；`pfnOffset`（F5 定向页帧偏移，默认 0=旧随机位翻转行为）

- [ ] **Step 1: CHAOSArmTLB.py 加参数**

在 `CHAOS/CHAOSArmTLB/CHAOSArmTLB.py` 的 `bitsToChange` 参数后加：

```python
    # §5.7B: field-level injection (targetField) + F5 pfn offset.
    targetField = Param.String("pfn",
        "TLB entry field to corrupt: pfn (page frame, default) | ap (access "
        "permissions) | xn (execute-never) | attridx (memory attributes via "
        "innerAttrs) | ng (nG via ignoreAsn) | asid (ASN). Field-level "
        "quantification of the TLB protection boundary.")
    pfnOffset = Param.UInt64(0,
        "F5 directed pfn offset: when nonzero, pfn += pfnOffset (a "
        "legal-domain substitute to ANOTHER page frame — proxy for "
        "'another live page'; hit mapped -> SDC, unmapped -> DUE). "
        "0 = legacy random-bit flip on pfn.")
```

- [ ] **Step 2: CHAOSArmTLB.hh 加成员**

在 `CHAOS/CHAOSArmTLB/CHAOSArmTLB.hh` 的 `int num_bits_to_change;` 后加：

```cpp
    std::string target_field;   // pfn/ap/xn/attridx/ng/asid
    uint64_t pfn_offset;        // F5 directed pfn substitute (0=legacy bitflip)
```

- [ ] **Step 3: CHAOSArmTLB.cc 扩展 maybeCorrupt**

构造函数初始化列表（`num_bits_to_change(p.bitsToChange),` 后）加：

```cpp
          target_field(p.targetField),
          pfn_offset(p.pfnOffset),
```

在 maybeCorrupt 内、现有 `Addr old_pfn = entry->pfn;` 之前插入 targetField 分支：

```cpp
        // §5.7B: field-level injection. targetField selects which TlbEntry
        // field is corrupted (pfn/ap/xn/attridx/ng/asid); pfnOffset (F5)
        // substitutes the pfn with pfn+offset (another page frame — proxy
        // for another live page; field enumeration of the TLB container
        // is not public, honest proxy documented in the param help).
        if (pfn_offset != 0 && target_field == "pfn") {
            // F5 directed: pfn -> pfn + offset (legal-domain substitute).
            Addr old_pfn = entry->pfn;
            entry->pfn = old_pfn + pfn_offset;
            stats->numFaultsInjected++;
            ++faults_injected_count;
            if (write_log) {
                *(log_stream->stream())
                    << "Tick: " << curTick()
                    << ", Site: arm_tlb_lookup_hit"
                    << ", Mode: pfn_to_offset (F5)"
                    << ", VA: 0x" << std::hex << va
                    << ", old_pfn: 0x" << old_pfn
                    << ", new_pfn: 0x" << entry->pfn
                    << ", pfnOffset: 0x" << pfn_offset << std::dec
                    << std::endl;
            }
            return;
        }
        // Field-level bit flip on the selected field (legacy path is
        // targetField=pfn, which preserves the original behavior).
        if (target_field == "ap") {
            uint8_t old_ap = entry->ap;
            entry->ap ^= (uint8_t)(mask ? (mask & 0xff) : (1u << (rng() % 3)));
            stats->numFaultsInjected++; ++faults_injected_count;
            if (write_log) {
                *(log_stream->stream())
                    << "Tick: " << curTick() << ", Site: arm_tlb_lookup_hit"
                    << ", Mode: field_ap"
                    << ", VA: 0x" << std::hex << va
                    << ", old: 0x" << (unsigned)old_ap
                    << ", new: 0x" << (unsigned)entry->ap << std::dec
                    << std::endl;
            }
            return;
        }
        if (target_field == "xn") {
            entry->xn = !entry->xn;
            stats->numFaultsInjected++; ++faults_injected_count;
            if (write_log) {
                *(log_stream->stream())
                    << "Tick: " << curTick() << ", Site: arm_tlb_lookup_hit"
                    << ", Mode: field_xn (toggle)"
                    << ", VA: 0x" << std::hex << va << std::dec
                    << std::endl;
            }
            return;
        }
        if (target_field == "attridx") {
            entry->innerAttrs ^= (uint8_t)(mask ? (mask & 0xff) : (1u << (rng() % 8)));
            stats->numFaultsInjected++; ++faults_injected_count;
            if (write_log) {
                *(log_stream->stream())
                    << "Tick: " << curTick() << ", Site: arm_tlb_lookup_hit"
                    << ", Mode: field_attridx"
                    << ", VA: 0x" << std::hex << va << std::dec
                    << std::endl;
            }
            return;
        }
        if (target_field == "ng") {
            entry->ignoreAsn = !entry->ignoreAsn;
            stats->numFaultsInjected++; ++faults_injected_count;
            if (write_log) {
                *(log_stream->stream())
                    << "Tick: " << curTick() << ", Site: arm_tlb_lookup_hit"
                    << ", Mode: field_ng (ignoreAsn toggle)"
                    << ", VA: 0x" << std::hex << va << std::dec
                    << std::endl;
            }
            return;
        }
        if (target_field == "asid") {
            entry->asn ^= (uint16_t)(mask ? (mask & 0xffff) : (1u << (rng() % 16)));
            stats->numFaultsInjected++; ++faults_injected_count;
            if (write_log) {
                *(log_stream->stream())
                    << "Tick: " << curTick() << ", Site: arm_tlb_lookup_hit"
                    << ", Mode: field_asid"
                    << ", VA: 0x" << std::hex << va << std::dec
                    << std::endl;
            }
            return;
        }
        // target_field == "pfn" && pfn_offset == 0: fall through to the
        // existing pfn bit-flip/stuck path (legacy behavior unchanged).
```

注意：`mask` 变量在现有代码里是 `uint64_t mask = fault_mask ? fault_mask : generateRandomMask(num_bits_to_change);`——上面引用前确认它已计算（现有代码在分支后算 mask，执行时把 mask 计算提到这些分支之前，或各分支内自行生成——**采用后者：各分支内联生成，不动现有 mask 计算**。上面代码已按各分支内联写）。

- [ ] **Step 4: arm_chaos_fs.py 加开关**

在 `configs/se/arm_chaos_fs.py` 的 `--tlb_rng_seed` 参数后加：

```python
p.add_argument("--tlb_target_field", default="pfn",
               choices=["pfn","ap","xn","attridx","ng","asid"],
               help="CHAOSArmTLB field-level target (§5.7B).")
p.add_argument("--tlb_pfn_offset", type=lambda x:int(x,0), default=0,
               help="F5 directed pfn offset (pfn+=offset, another page frame).")
```

CHAOSArmTLB 挂载处（`arm_tlb = CHAOSArmTLB(...)`）加两行：

```python
            targetField=args.tlb_target_field,
            pfnOffset=args.tlb_pfn_offset,
```

- [ ] **Step 5: 同步构建 + 真机验证**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
cp -f CHAOS/CHAOSArmTLB/*.{py,hh,cc} CHAOS/gem5/src/arch/arm/CHAOSArmTLB/
diff -rq CHAOS/CHAOSArmTLB/ CHAOS/gem5/src/arch/arm/CHAOSArmTLB/   # 期望 IDENTICAL
cd CHAOS/gem5 && source /home/sdc/gem5-deps/env.sh
scons build/ARM/gem5.opt -j16 2>&1 | grep -iE "error|done building" | tail -3
# 预期 scons: done building targets.
chmod +x build/ARM/gem5.opt
```

回归（TLB 是 FS-only，SE 下挂载即验证不崩）：

```bash
G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
timeout 150 "$G5" --quiet --outdir=runs/u1_reg configs/se/arm_chaos.py \
    --cmd=workloads/directed/reg_chain --cpu=O3 2>&1 | grep -E "^[0-9a-f]{16}$" | tail -1
# 预期 f247ef3fe6f02cfd（golden 不变）
```

FS 功能验证（pfnOffset F5——预期 DUE：翻到未映射页帧 → kernel panic，或 SDC：翻到已映射页）：

```bash
timeout 250 "$G5" --quiet --outdir=runs/u1_f5tlb configs/se/arm_chaos_fs.py \
    --kernel=gem5-fs/vmlinux --disk=gem5-fs/ubuntu.img \
    --bootloader=gem5-fs/boot.arm64 --root-partition=/dev/vda1 \
    --cpu=Atomic --platform=V1 \
    --chaos_armtlb --tlb_probability=1.0 --tlb_first_clock=50000 \
    --tlb_max_faults=1 --tlb_rng_seed=20260825 \
    --tlb_target_field=pfn --tlb_pfn_offset=0x40000 2>&1 | tail -3
grep -E "pfn_to_offset" runs/u1_f5tlb/armtlb_injections.log 2>/dev/null | head -2
```

预期：`armtlb_injections.log` 出现 `Mode: pfn_to_offset (F5), old_pfn: 0x..., new_pfn: 0x...` 行（引用实际输出）。系统可能 panic（DUE 方向）或继续（SDC 方向）——两者都如实记录。

字段级验证（ap 字段）：

```bash
timeout 250 "$G5" --quiet --outdir=runs/u1_ap configs/se/arm_chaos_fs.py \
    --kernel=gem5-fs/vmlinux --disk=gem5-fs/ubuntu.img \
    --bootloader=gem5-fs/boot.arm64 --root-partition=/dev/vda1 \
    --cpu=Atomic --platform=V1 \
    --chaos_armtlb --tlb_probability=1.0 --tlb_first_clock=50000 \
    --tlb_max_faults=1 --tlb_rng_seed=20260825 \
    --tlb_target_field=ap 2>&1 | tail -3
grep -E "field_ap" runs/u1_ap/armtlb_injections.log 2>/dev/null | head -2
# 预期 'Mode: field_ap, old: 0x.., new: 0x..' 行
```

- [ ] **Step 6: 提交**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
git add CHAOS/CHAOSArmTLB/ CHAOS/gem5/src/arch/arm/CHAOSArmTLB/ configs/se/arm_chaos_fs.py
git commit -m "§5.7B: CHAOSArmTLB 字段级注入 + pfn_to_offset F5

方案 §5.7B 的 targetField 全集 + F5 换页帧：
- targetField ∈ {pfn(默认,旧行为), ap, xn, attridx(经innerAttrs), ng(经
  ignoreAsn), asid}——TLB 保护边界的字段级量化
- pfnOffset (F5): pfn += offset 定向换到另一页帧（活页枚举需 TLB 容器
  遍历不公开——诚实代理：页帧偏移，命中已映射页->SDC / 未映射->DUE）

真机自验证：
1. 构建：零 CHAOS 源警告（G7）
2. SE 回归：golden=f247ef3fe6f02cfd（TLB hook SE 短路不变）
3. FS pfnOffset=0x40000: 日志 'Mode: pfn_to_offset (F5), old_pfn->new_pfn'
   （引用实际输出）；系统归宿（DUE/继续）如实记录
4. FS targetField=ap: 日志 'Mode: field_ap, old->new'
诚实边界：pfnOffset 是页帧偏移代理非'另一活页'枚举；I-TLB 挂载与
L2 TLB（gem5 无 ARM L2 TLB 模型）未实现。"
git push origin fi-wangxu
```

---

### Task 2: CHAOSArmSysReg 扩展——value_to_legal（F5）

方案 §5.7B："`value_to_legal`（F5）"。现状：CHAOSArmSysReg 仅 bit_flip/stuck（位翻转）——**F5"换成一个合法系统寄存器值"未实现**（如 ttbr0_el1 的读值换成 ttbr1_el1 的值——换页表基址，静默 SDC 方向）。

**研究结论**：`CHAOSArmSysReg::maybeCorrupt(uint32_t idx, const char *reg_name, RegVal &val)`（CHAOSArmSysReg.cc:145 起）hook 在 `readMiscRegNoEffect` 返回路径。F5 实现：按白名单配对表把当前寄存器的读值替换成"配对寄存器的值域内的合法值"——最简诚实实现：**位清零到典型复位值**（如 TTBR 的低位对齐值是合法页表基址形态）或**与白名单另一寄存器互换语义值**（复杂）。采用：`value_to_legal = 把读值按位 AND 一个"合法掩码"（如 TTBR 的 0xxxxxxxxxfffff000——页表基址对齐形态），产生一个仍是合法基址形态但指向错误页表的新值**。

**Files:**
- Modify: `CHAOS/CHAOSArmSysReg/CHAOSArmSysReg.py/.hh/.cc`
- Modify: `configs/se/arm_chaos_fs.py`
- 同步：`CHAOS/gem5/src/arch/arm/CHAOSArmSysReg/`

**Interfaces:**
- Produces: `faultType` 增 `value_to_legal` 选项；行为 = 读值 AND 合法形态掩码（TTBR 类：`~0xFFF` 页表对齐 + 高位保留；通用：保留高 32 位清低 32 位——诚实标注为"合法值域形态替换"）

- [ ] **Step 1: .py faultType 加选项**

`CHAOS/CHAOSArmSysReg/CHAOSArmSysReg.py` 的 faultType 参数改为：

```python
    faultType = Param.String("bit_flip",
        "bit_flip | stuck_at_zero | stuck_at_one | random | value_to_legal "
        "(F5: AND the read value with a legal-form mask — e.g. TTBR aligned "
        "to page-table base form — producing a WRONG but legal-shaped value; "
        "silent wrong-page-table direction)")
```

- [ ] **Step 2: .hh/.cc 实现 value_to_legal**

`.hh` 的 FaultType enum 加 `ValueToLegal`；`stringToFaultType` 加映射；`faultTypeToString` 加 case（G7）。

`.cc` maybeCorrupt 的 switch 加 case（在 `case FaultType::BitFlip:` 前插）：

```cpp
            case FaultType::ValueToLegal: {
                // F5 (§5.7B): AND with a legal-form mask. For TTBR-class
                // registers (page-table bases), ~0xFFF aligns to a page-
                // table base FORM — the new value is a legal shape but a
                // WRONG base (silent wrong-page-table direction). For
                // others, keep the upper half (control bits live high).
                bool is_ttbr = (reg_name &&
                    (strstr(reg_name, "ttbr0") || strstr(reg_name, "ttbr1")));
                RegVal legal_mask = is_ttbr ? ~(RegVal)0xFFF
                                            : ((RegVal)0xFFFFFFFFULL << 32);
                RegVal old_val = val;
                val &= legal_mask;
                if (val == old_val) return false;  // already legal-form: no-op
                break;
            }
```

注意 `#include <cstring>`（strstr）加到 .cc 顶部。`stats->numFaultsInjected++` 等公共计数在 switch 后已有，无需重复。

- [ ] **Step 3: arm_chaos_fs.py 透传**

`--sysreg_fault_type` 不可用时（现有 config 硬编码 `faultType="bit_flip"`）——改挂载处：

```python
p.add_argument("--sysreg_fault_type", default="bit_flip",
               choices=["bit_flip","stuck_at_zero","stuck_at_one","random","value_to_legal"])
```

挂载处 `faultType="bit_flip"` 改 `faultType=args.sysreg_fault_type`。

- [ ] **Step 4: 构建 + FS 验证**

```bash
cd /home/sdc/wangxu/gem5-fi-wangxu
cp -f CHAOS/CHAOSArmSysReg/*.{py,hh,cc} CHAOS/gem5/src/arch/arm/CHAOSArmSysReg/
cd CHAOS/gem5 && source /home/sdc/gem5-deps/env.sh && scons build/ARM/gem5.opt -j16 2>&1 | grep -iE "error|done" | tail -2
chmod +x build/ARM/gem5.opt
G5=$PWD/build/ARM/gem5.opt
cd ../..
# SE 回归
timeout 150 "$G5" --quiet --outdir=runs/u2_reg configs/se/arm_chaos.py \
    --cmd=workloads/directed/reg_chain --cpu=O3 2>&1 | grep -E "^[0-9a-f]{16}$" | tail -1
# 预期 f247ef3fe6f02cfd
# FS value_to_legal on ttbr0_el1
timeout 250 "$G5" --quiet --outdir=runs/u2_v2l configs/se/arm_chaos_fs.py \
    --kernel=gem5-fs/vmlinux --disk=gem5-fs/ubuntu.img \
    --bootloader=gem5-fs/boot.arm64 --root-partition=/dev/vda1 \
    --cpu=Atomic --platform=V1 \
    --chaos_sysreg --sysreg_probability=1.0 --sysreg_first_clock=100000 \
    --sysreg_max_faults=2 --sysreg_rng_seed=20260825 \
    --sysreg_fault_type=value_to_legal \
    --sysreg_target_regs="ttbr0_el1,ttbr1_el1" 2>&1 | tail -3
grep -E "value_to_legal|Reg: ttbr" runs/u2_v2l/arm_sysreg_injections.log 2>/dev/null | head -3
```

预期：日志出现 `Reg: ttbr0_el1 ... new: 0x...000`（低位被清成页表对齐形态——引用实际输出）。若 `old == new`（读值本已对齐）则 no-return——换 first_clock 或 max_faults=5 重试。

- [ ] **Step 5: 提交**

```bash
git add CHAOS/CHAOSArmSysReg/ CHAOS/gem5/src/arch/arm/CHAOSArmSysReg/ configs/se/arm_chaos_fs.py
git commit -m "§5.7B: CHAOSArmSysReg value_to_legal (F5 合法值域形态替换)

F5: 读值 AND 合法形态掩码——TTBR 类 ~0xFFF（页表基址对齐形态，错误但
合法形态的基址=静默换页表方向）；其他寄存器保留高 32 位。
真机自验证：（引用实际输出：ttbr value_to_legal 日志行 + SE golden 回归）
诚实边界：形态替换非语义配对（未枚举'另一寄存器的值'）；ttbr 之外的
掩码是通用高位保留。"
git push origin fi-wangxu
```

---

### Task 3: method2/3 定向 kernel 批次（ptr_chase + fwd_7case + no-op 变体）

方案 §5.1D/§5.4D：`ptr_chase_kernel`（method2 链表遍历）、method3 的 7 类定向构造（同址/部分重叠/4K 别名/双候选/未就绪 replay/DMB-DSB/LDXR-STXR，**各加/不加热路径 no-op ALU 两变体**——现场 Probe H/X 证明 no-op ALU 是相位判别器：100%→10-20%）。

**研究结论（现场依据已核实，reproduce-method3.md §3.1/3.2）**：
- 现场 Probe A/D/E/F（三必要条件）：去 store / 固定地址 / 跨 NUMA / 限单行 → PASS（归零）
- 现场 Probe H/X（非判别器但相位证据）：加 1 条语义 no-op ALU → 100%→10%/20%
- gem5 侧已有：CHAOSLSQFwd 五模式（structuralFault/fwd_source_sub/stale_line_replay/phaseOffset/D2）+ fp_fwd_kernel
- **本任务产出一个 kernel 文件含 7 类构造 × 2 变体（argv 选择），供 CHAOSLSQFwd 各模式配对 formal**

**Files:**
- Create: `workloads/directed/fwd_7case.c`（7 类构造，argv[2] 选类型，argv[3] 选 no-op 变体）
- Create: `workloads/directed/ptr_chase.c`（method2 链表）

**Interfaces:**
- Produces: `fwd_7case <iters> <case: same|partial|alias4k|twocand|replay|dmb|ldxr> [noop]`；`ptr_chase <iters>`。均输出 16-hex checksum（stdout）+ iters/fails（stderr）

- [ ] **Step 1: 写 fwd_7case.c**

```bash
cat > workloads/directed/fwd_7case.c << 'EOF'
/* fwd_7case.c — method3 directed forwarding constructions (plan §5.4D).
 * 7 cases x 2 variants (with/without a hot-path no-op ALU — the field's
 * phase discriminator: Probe H/X showed ONE no-op ALU collapses the rate
 * 100% -> 10-20%). Each case stresses a distinct store->load forwarding
 * CAM geometry; pairing with CHAOSLSQFwd modes quantifies per-geometry
 * SDC exposure.
 *
 * Usage: fwd_7case <iters> <same|partial|alias4k|twocand|replay|dmb|ldxr> [noop]
 * Output: 16-hex checksum (stdout) + iters/fails (stderr).
 */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define N 4096

static uint32_t rng_s = 0xC0FFEE11u;
static inline uint32_t xs32(void){uint32_t x=rng_s;x^=x<<13;x^=x>>17;x^=x>>5;rng_s=x;return x;}

static inline uint64_t noop_alu(uint64_t v, int on, uint64_t mask) {
    /* semantic no-op: v & mask == v when mask covers v's hot bits
     * (field Probe H: 'and x2,x19,x20' with i<16383, i&16383==i) */
    return on ? (v & mask) : v;
}

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 2000;
    const char *cs = (argc > 2) ? argv[2] : "same";
    int noop = (argc > 3 && strcmp(argv[3], "noop") == 0);
    uint64_t *buf = aligned_alloc(64, N * sizeof(uint64_t));      /* hot */
    uint64_t *alias = aligned_alloc(64, N * sizeof(uint64_t));    /* 4K-alias partner */
    if (!buf || !alias) return 2;
    for (int i = 0; i < N; i++) { buf[i] = ((uint64_t)xs32()<<32)|xs32(); alias[i] = buf[i]; }

    uint64_t acc = 0; long fails = 0;
    /* no-op mask: covers i<N so v&mask==v for the index path (semantic no-op) */
    const uint64_t nm = (N - 1) | 0xFFFFFFFF00000000ULL;
    for (long it = 0; it < iters; it++) {
        int i = (int)(it % N);
        uint64_t v, expect;
        if (strcmp(cs, "same") == 0) {
            /* case 1: exact same-address store->load (back-to-back) */
            buf[i] = (uint64_t)it + 1; expect = buf[i];
            v = *(volatile uint64_t*)&buf[i];
            v = noop_alu(v, noop, nm);
        } else if (strcmp(cs, "partial") == 0) {
            /* case 2: partial overlap (store 8B, load 4B at +4) */
            uint64_t s = ((uint64_t)it + 1) * 0x0101010101010101ULL;
            memcpy(&buf[i], &s, 8);
            uint32_t lo; memcpy(&lo, (uint8_t*)&buf[i] + 4, 4);
            v = lo; expect = (uint32_t)(s >> 32);
            v = noop_alu(v, noop, 0xFFFFFFFFULL);
        } else if (strcmp(cs, "alias4k") == 0) {
            /* case 3: 4K aliasing (store buf, load alias — same page offset
             * in a different 4K page; stresses the CAM's offset compare) */
            buf[i] = (uint64_t)it + 1; expect = buf[i];
            v = *(volatile uint64_t*)&alias[i];  /* different page, same idx */
            v = noop_alu(v, noop, nm);
            /* alias[i] tracks buf[i] only at setup: expected uses buf —
             * the alias read returns the OLD value unless re-synced. For a
             * deterministic golden we re-sync after the read: */
            acc += v; alias[i] = buf[i]; v = buf[i];
        } else if (strcmp(cs, "twocand") == 0) {
            /* case 4: two candidate stores to the SAME addr in the SQ —
             * the younger must win; a wrong-source forward returns older */
            buf[i] = 0xDEAD0000 + (uint64_t)it;        /* older store */
            buf[i] = 0xBEEF0000 + (uint64_t)it;        /* younger store (wins) */
            expect = 0xBEEF0000 + (uint64_t)it;
            v = *(volatile uint64_t*)&buf[i];
            v = noop_alu(v, noop, nm);
        } else if (strcmp(cs, "replay") == 0) {
            /* case 5: load issued while the store is not yet ready
             * (replay path) — a dependent computation between store and
             * load forces the load to wait/replay */
            buf[i] = (uint64_t)it + 1;
            uint64_t dep = buf[(i + 7) & (N - 1)] & 1;  /* dependent read */
            expect = buf[i] + dep;  /* dep from a STABLE slot: golden deterministic
                                     * only if that slot isn't written this iter —
                                     * (i+7)%N != i always; but it IS written on a
                                     * later iter. Keep it read-only: use a const */
            expect = buf[i];        /* simplify: dep read is read-only side effect */
            v = *(volatile uint64_t*)&buf[i] + dep * 0;  /* dep folded away but
                                             * the LOAD dependency remains */
            v = noop_alu(v, noop, nm);
        } else if (strcmp(cs, "dmb") == 0) {
            /* case 6: DMB between store and load (weak-order barrier) */
            buf[i] = (uint64_t)it + 1; expect = buf[i];
            __asm__ volatile("dmb ish" ::: "memory");
            v = *(volatile uint64_t*)&buf[i];
            v = noop_alu(v, noop, nm);
        } else if (strcmp(cs, "ldxr") == 0) {
            /* case 7: LDXR/STXR exclusive pair (monitor path) */
            uint64_t old = __atomic_load_n(&buf[i], __ATOMIC_RELAXED);
            uint64_t want = old + 1;
            uint64_t got = 0;
            __asm__ volatile(
                "ldxr %0, [%1]\n"
                "add %0, %0, #1\n"
                "stxr %w2, %0, [%1]\n"
                : "=&r"(got) : "r"(&buf[i]), "r"(0) : "memory");
            (void)want; (void)old;
            v = got; expect = got;  /* self-consistent: golden = whatever STXR
                                     * committed (deterministic: LDXR returns
                                     * the stored value, +1, stored again) */
            v = noop_alu(v, noop, nm);
        } else {
            fprintf(stderr, "unknown case %s\n", cs); return 2;
        }
        if (v != expect) fails++;
        acc += v;
    }
    printf("%016lx\n", acc & 0xFFFFFFFFFFFFFFFFULL);
    fprintf(stderr, "iters=%ld fails=%ld variant=%s%s\n",
            iters, fails, cs, noop ? "+noop" : "");
    return (fails > 0) ? 1 : 0;
}
EOF
gcc -static -O2 -o workloads/directed/fwd_7case workloads/directed/fwd_7case.c
# 确定性验证：每 case × 每 variant 跑 2 次须一致
for c in same partial alias4k twocand replay dmb ldxr; do
  for v in "" noop; do
    a=$(workloads/directed/fwd_7case 200 $c $v 2>/dev/null)
    b=$(workloads/directed/fwd_7case 200 $c $v 2>/dev/null)
    [ "$a" = "$b" ] && echo "$c${v:++$v}: OK $a" || echo "$c${v:++$v}: NONDET $a vs $b"
  done
done
```

**注意**：`alias4k` 与 `replay` case 的确定性需重点检查——若 NONDET，修 kernel（alias case 必须让 golden 路径读自己的页；replay case 的依赖读必须读不被写的槽位）。执行者跑上面循环后只提交全 OK 的版本；NONDET 的 case 修到 OK（改 expect 逻辑而非删 case）。

- [ ] **Step 2: 写 ptr_chase.c（method2 链表遍历）**

```bash
cat > workloads/directed/ptr_chase.c << 'EOF'
/* ptr_chase.c — method2 (x10 garbage pointer) directed kernel (plan §5.1D).
 * A linked-list traversal where the chase pointer lives in a register
 * across an indirect-addressing loop (method2's __per_cpu_offset load-use
 * pattern). A PRF/AGU fault on the chase pointer dereferences garbage ->
 * segfault (DUE) or wrong data (SDN). Golden: deterministic chain build.
 * Output: 16-hex checksum + iters/fails.
 */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

#define N 8192
typedef struct node { struct node *next; uint64_t val; } node_t;

static uint32_t rng_s = 0x5A5A1234u;
static inline uint32_t xs32(void){uint32_t x=rng_s;x^=x<<13;x^=x>>17;x^=x>>5;rng_s=x;return x;}

int main(int argc, char **argv) {
    long iters = (argc > 1) ? atol(argv[1]) : 200;
    node_t *nodes = malloc(N * sizeof(node_t));
    if (!nodes) return 2;
    /* deterministic chain: i -> (i*7+3)%N permutation (single cycle iff
     * gcd(7,N)==1 and start reachable; use +1 step for guaranteed cycle) */
    for (int i = 0; i < N; i++) { nodes[i].val = ((uint64_t)xs32()<<32)|xs32(); }
    for (int i = 0; i < N; i++) nodes[i].next = &nodes[(i + 1) % N];

    uint64_t acc = 0; long fails = 0;
    for (long it = 0; it < iters; it++) {
        /* chase: pointer crosses an indirect sub-loop (register-resident) */
        node_t *p = &nodes[it % N];
        uint64_t expect = 0;
        for (int k = 0; k < 64; k++) { expect += p->val; p = p->next; }
        /* recompute the same walk for the golden (data not mutated) */
        node_t *q = &nodes[it % N];
        uint64_t got = 0;
        for (int k = 0; k < 64; k++) { got += q->val; q = q->next; }
        if (got != expect) fails++;
        acc += got;
    }
    printf("%016lx\n", acc & 0xFFFFFFFFFFFFFFFFULL);
    fprintf(stderr, "iters=%ld fails=%ld variant=ptr_chase\n", iters, fails);
    return (fails > 0) ? 1 : 0;
}
EOF
gcc -static -O2 -o workloads/directed/ptr_chase workloads/directed/ptr_chase.c
workloads/directed/ptr_chase 100   # 2x 确定性
workloads/directed/ptr_chase 100
```

- [ ] **Step 3: gem5 golden 验证（两 kernel × 代表 case）**

```bash
G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
source /home/sdc/gem5-deps/env.sh
# ptr_chase golden
timeout 200 "$G5" --quiet --outdir=runs/u3_ptrgold configs/se/arm_chaos.py \
    --cmd=workloads/directed/ptr_chase --cpu=O3 2>&1 | grep -E "^[0-9a-f]{16}$|iters=" | tail -2
# fwd_7case same-case golden（无注入）
timeout 200 "$G5" --quiet --outdir=runs/u3_same configs/se/arm_chaos.py \
    --cmd=workloads/directed/fwd_7case --cpu=O3 2>&1 | tail -3
```

注意：arm_chaos.py 的 `--cmd` 不传 workload 参数（argv）。fwd_7case 的 iters 默认 2000、case 默认 same——golden 即默认路径。**若需跑非默认 case，用 `--workload-args`（campaign.py 有）或直接给 kernel 写死编译期默认**。为简化验证：golden 用默认（same, no-noop）；其余 case 的 gem5 端到端配对留给 formal（kernel 的 native 确定性已保证）。

- [ ] **Step 4: 提交**

```bash
git add workloads/directed/fwd_7case workloads/directed/fwd_7case.c \
        workloads/directed/ptr_chase workloads/directed/ptr_chase.c
git commit -m "§5.1D/§5.4D: method2/3 定向 kernel（ptr_chase + fwd_7case 7类×2变体）

- ptr_chase: method2 链表遍历（chase 指针跨间接子循环寄存器驻留——
  __per_cpu_offset load-use 模式）；native 2x 确定性 + gem5 golden
- fwd_7case: method3 7类转发几何（same/partial/alias4k/twocand/replay/
  dmb/ldxr）× noop 变体（现场 Probe H/X：1条 no-op ALU 100%->10-20%
  相位判别器）。每 case native 2x 确定性（引用实际输出）

供 CHAOSLSQFwd 五模式配对 formal（几何×故障模式×相位的 P_SDC 矩阵）。"
git push origin fi-wangxu
```

---

### Task 4: FS checkpoint 流水线（Atomic boot → m5.checkpoint → restore 切 O3 → ROI 注入）

方案 §10.2：**"FS campaign（TLB/PTW/AGU/系统级）：Atomic boot → `m5 checkpoint` → restore 切 O3 → ROI 单故障 → 分类"**。这是 D1/D4/AddrPath/SysReg/PTW 五个 FS 注入器端到端验证的共同解锁项（此前全部诚实标注"待 checkpoint"）。

**研究结论（已核实）**：
- `Simulator.save_checkpoint(dir)` 存在（`src/python/gem5/simulate/simulator.py:658`——内部调 `m5.checkpoint(str(dir))`；`m5.checkpoint` 在 `src/python/m5/simulate.py:401`：`drain() + memWriteback + serializeAll(dir)`，已读完整实现）
- **restore 路径（关键核实）**：`board._checkpoint` 由 `set_kernel_disk_workload(..., checkpoint=<dir>)` 设置（`kernel_disk_workload.py:230`），Simulator 首次 `run()` 时经 `_create_cpp_objects(ckpt_dir=...)` 自动 restore（simulator.py:574-580）。**Simulator 构造函数没有 checkpoint 参数**——restore 必须经 workload 设置传入
- 已有资产：`arm_chaos_fs.py`（ArmBoard + VExpress_V1 + 全部 FS 注入器挂载）+ `kp920_proxy` FS 开关

**Files:**
- Create: `configs/se/fs_checkpoint.py`（boot→checkpoint→restore→O3→注入 一体化脚本）
- 不改注入器（全部已就位）

**Interfaces:**
- Consumes: 现有全部 FS 注入器（CHAOSArmTLB/ArmSysReg/AddrPath/PTW）的 `--chaos_*` 挂载参数模式
- Produces: `fs_checkpoint.py --phase=boot|inject` 两阶段流（boot 产 checkpoint 目录；inject 从 checkpoint restore 切 O3 挂注入器跑 ROI）

**关键设计——为什么两阶段而非一体**：checkpoint 必须在 Linux 用户态稳定点（boot 完成后）取，取 checkpoint 需 drain（分钟级）；注入阶段从 checkpoint 反复 restore（每个 seed 一次，秒级恢复）——这正是"checkpoint 策略必需"的原因（方案 §5.7F）。脚本模式：`--phase=boot` 跑到 `m5 checkpoint` 后退出；`--phase=inject --ckpt=<dir>` restore + 切 O3 + 挂注入器。

- [ ] **Step 1: 写 fs_checkpoint.py（boot 阶段）**

```bash
cat > configs/se/fs_checkpoint.py << 'EOF'
#!/usr/bin/env python3
"""fs_checkpoint.py — FS checkpoint pipeline (plan §10.2).

Two-phase FS campaign flow that unlocks FS+O3 end-to-end injection for
CHAOSArmTLB / CHAOSArmSysReg / CHAOSAddrPath / CHAOSPTW:

  phase=boot : Atomic-boot Linux to a stable point, take m5.checkpoint(dir),
               exit. (minutes; done ONCE per kernel/disk combo)
  phase=inject: restore from the checkpoint, switch CPU to O3 (the switch
               cpus pattern), attach CHAOS injectors, run the ROI workload
               with a single fault. (seconds per restore; per-seed)

The boot phase uses a readfile script that waits for boot then calls the
m5 checkpoint via the m5fs device (the stdlib KernelBootedExitHandler
signals boot completion; we then checkpoint from Python).

Usage:
  gem5.opt fs_checkpoint.py --phase=boot --ckpt-dir=cpts/base \
      --kernel=... --disk=... --bootloader=...
  gem5.opt fs_checkpoint.py --phase=inject --ckpt-dir=cpts/base \
      --injector=addrpath --probability=1.0 --seed=20260825 ...
"""
import argparse, os
import m5
from m5.objects import (ArmDefaultRelease, VExpress_GEM5_V1,
                        CHAOSArmTLB, CHAOSArmSysReg, CHAOSAddrPath, CHAOSPTW)
from gem5.components.boards.arm_board import ArmBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy)
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import (KernelResource, DiskImageResource,
                                     BootloaderResource)
from gem5.simulate.simulator import Simulator

p = argparse.ArgumentParser()
p.add_argument("--phase", required=True, choices=["boot", "inject"])
p.add_argument("--ckpt-dir", required=True)
p.add_argument("--kernel", required=True)
p.add_argument("--disk", required=True)
p.add_argument("--bootloader", required=True)
p.add_argument("--root-partition", default="/dev/vda1")
p.add_argument("--mem-size", default="2GiB")
p.add_argument("--platform", default="V1", choices=["V1", "Foundation"])
# inject-phase params
p.add_argument("--injector", default="addrpath",
               choices=["none", "armtlb", "sysreg", "addrpath", "ptw"])
p.add_argument("--probability", type=float, default=1.0)
p.add_argument("--first-clock", type=lambda x: int(x, 0), default=100000)
p.add_argument("--max-faults", type=lambda x: int(x, 0), default=1)
p.add_argument("--seed", type=lambda x: int(x, 0), default=20260825)
p.add_argument("--kp920-proxy", action="store_true",
               help="apply V110 O3 proxy params to the O3 CPU")
args = p.parse_args()

cpu_map_boot = {"Atomic": CPUTypes.ATOMIC}   # boot: Atomic
cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="16KiB", l1i_size="16KiB", l2_size="256KiB")
memory = DualChannelDDR4_2400(size=args.mem_size)
processor = SimpleProcessor(cpu_type=CPUTypes.ATOMIC, num_cores=1, isa=ISA.ARM)
release = ArmDefaultRelease()
platform = VExpress_GEM5_V1() if args.platform == "V1" else None

board = ArmBoard(
    clk_freq="2.6GHz" if args.kp920_proxy else "3GHz",
    processor=processor, memory=memory,
    cache_hierarchy=cache_hierarchy, release=release, platform=platform)

board.set_kernel_disk_workload(
    kernel=KernelResource(local_path=args.kernel),
    disk_image=DiskImageResource(local_path=args.disk,
                                 root_partition=args.root_partition),
    bootloader=BootloaderResource(local_path=args.bootloader),
    kernel_args=["root=" + args.root_partition, "rw",
                 "console=ttyAMA0", "earlycon=pl011,0x1c090000"])

sim = Simulator(board=board, full_system=True)

if args.phase == "boot":
    # Run until the KernelBootedExitHandler fires (boot done), then
    # checkpoint and exit. Simulator.save_checkpoint wraps m5.checkpoint
    # (simulator.py:658) — use the public API.
    sim.run()
    # If we reach here, boot completed (exit event fired). Checkpoint:
    from pathlib import Path
    sim.save_checkpoint(Path(args.ckpt_dir))
    print(f"[fs_checkpoint] boot phase done; checkpoint at {args.ckpt_dir}")
else:
    # inject phase: restore from checkpoint. RESTORE 接入方式（已核实）：
    # board._checkpoint 由 set_kernel_disk_workload(checkpoint=...) 设置
    # （kernel_disk_workload.py:230），Simulator 构造后 run() 时经
    # _create_cpp_objects(ckpt_dir=...) 自动 restore。Simulator 构造函数
    # 没有 checkpoint_path 参数——必须在 workload 设置处传。
    # HONEST FIRST STEP: restore with the SAME Atomic CPU + attach injectors
    # （TLB/SysReg/PTW hooks fire on Atomic; AddrPath 的 lsq.cc hook 是
    # O3-only 保持 deferred）。O3-switch 是第二步。
    board.set_kernel_disk_workload(
        kernel=KernelResource(local_path=args.kernel),
        disk_image=DiskImageResource(local_path=args.disk,
                                     root_partition=args.root_partition),
        bootloader=BootloaderResource(local_path=args.bootloader),
        checkpoint=args.ckpt_dir,      # <- restore 接入点（已核实 API）
        kernel_args=["root=" + args.root_partition, "rw",
                     "console=ttyAMA0", "earlycon=pl011,0x1c090000"])
    # attach the injector via the same _pre_instantiate pattern as
    # arm_chaos_fs.py (copy the attach block from there, parameterized)
    # ... (see Step 2)
    sim = Simulator(board=board, full_system=True)
    sim.run()
EOF
```

**诚实的第一步缩减**：完整的 boot→checkpoint→**switch-to-O3**→inject 流水线里，CPU switch 在 stdlib board 上不干净。**本任务第一步交付 Atomic-restore + 注入器**（TLB/SysReg/PTW 的 hook 都在 Atomic 可触发的路径——此前 PTW 的 FS 验证就在 Atomic 下做过 5 注入；AddrPath 是 O3-only 保持 deferred）。O3-switch 作为第二步（若 stdlib 不支持则记为 gem5 限制）。

- [ ] **Step 2: inject 阶段挂注入器（复用 arm_chaos_fs.py 的 _pre_instantiate 模式）**

把 arm_chaos_fs.py 的 `_attach_tlb` hook 块（`cache_hierarchy._pre_instantiate = _attach_tlb` 模式）复制进 fs_checkpoint.py 的 inject 分支，参数化 `args.injector`——四个注入器各一个 if 块（照抄 arm_chaos_fs.py 现有挂载代码，改参数来源为 args）。执行者从 arm_chaos_fs.py 逐块复制（TLB 块/SysReg 块/AddrPath 块/PTW 块），**不新写逻辑**。

- [ ] **Step 3: 真机验证——boot 阶段（长任务，后台）**

```bash
G5=$PWD/CHAOS/gem5/build/ARM/gem5.opt
source /home/sdc/gem5-deps/env.sh
mkdir -p cpts
timeout 580 "$G5" --quiet --outdir=runs/u4_boot configs/se/fs_checkpoint.py \
    --phase=boot --ckpt-dir=cpts/base \
    --kernel=gem5-fs/vmlinux --disk=gem5-fs/ubuntu.img \
    --bootloader=gem5-fs/boot.arm64 --root-partition=/dev/vda1 2>&1 | tail -4
ls cpts/base/ 2>/dev/null | head -4
```

预期：`cpts/base/` 出现 checkpoint 文件（m5.cpt 等）。**这是长任务（Atomic boot ~4-8 分钟）——后台执行。** 若 boot 未到 KernelBooted 就超时，如实记录（boot 时长是已知 FS 边界，方案 §5.7F 已注明），checkpoint 时点前移（用 `--readfile` 挂早期 checkpoint 脚本）作为迭代。

- [ ] **Step 4: 真机验证——inject 阶段（PTW 注入，从 checkpoint restore）**

```bash
timeout 400 "$G5" --quiet --outdir=runs/u4_inj configs/se/fs_checkpoint.py \
    --phase=inject --ckpt-dir=cpts/base \
    --kernel=gem5-fs/vmlinux --disk=gem5-fs/ubuntu.img \
    --bootloader=gem5-fs/boot.arm64 --root-partition=/dev/vda1 \
    --injector=ptw --probability=1.0 --first-clock=1000 \
    --max-faults=3 --seed=20260825 2>&1 | tail -3
grep -E "ptw_descriptor" runs/u4_inj/ptw_injections.log 2>/dev/null | head -2
```

预期：restore 成功（比冷 boot 快得多）+ `ptw_injections.log` 有注入行（first-clock=1000 因为 restore 后 tick 从 checkpoint 继续——时窗要按 restore 后的 tick 域调）。**若 restore 失败（磁盘/设备序列化不兼容），如实记录 gem5 FS checkpoint 的兼容性限制**——这是方案 §10.2 该流水线的第一次真实验证，结果两个方向都有价值。

- [ ] **Step 5: 提交**

```bash
git add configs/se/fs_checkpoint.py
git commit -m "§10.2: FS checkpoint 流水线 v1（boot→m5.checkpoint→restore→Atomic 注入）

方案 §10.2 FS campaign 流水线的首次落地：
- phase=boot: Atomic boot Linux 至 KernelBooted -> m5.checkpoint(dir)
  （simulate.py:401 drain+memWriteback+serializeAll，已核实 API）
- phase=inject: checkpoint restore + 挂注入器（复用 arm_chaos_fs.py 的
  _pre_instantiate 挂载模式，四注入器参数化）+ 单故障 ROI

真机自验证：
- boot: cpts/base 产生 checkpoint 文件（引用实际输出；若 boot 超时如实
  记录 FS 时长边界）
- inject(ptw): restore + ptw_injections.log 注入行（引用实际输出；若
  restore 序列化不兼容如实记录 gem5 限制）

诚实边界：v1 是 Atomic-restore（TLB/SysReg/PTW hook 在 Atomic 可触发）；
O3-switch（AddrPath 的 lsq hook 需要）待 stdlib switchCpus 路径——
gem5 stdlib SimpleProcessor 的 CPU switch 不干净，O3-switch 为第二步。"
git push origin fi-wangxu
```

---

### Task 5: CHAOSCache L1I 语义字段定向（指令编码字段位段）

方案 §5.8C："L1I 语义字段{opcode,Rn,Rm,Rd,imm,cond}"。现状：CHAOSCache 定向到 block+byte，**但无 A64 指令编码字段感知**（哪个字节/位对应 opcode/Rn/Rm/Rd/imm/cond）。l1i_loop.c 注释已说明"可突变 opcode/Rn/Rm/Rd/immediate/condition field"——缺的是注入器的字段映射。

**研究结论（A64 编码字段位段，固定布局）**：
- A64 (32-bit, little-endian in memory)：`opcode[31:24]`（含 op0/主操作码区）、`cond[31]`+低段（条件指令）、`Rd[4:0]`、`Rn[9:5]`、`Rm[20:16]`、`imm[23:10]/[21:10]/[15:0]`（因指令而异——**imm 位段不固定**，诚实处理：提供 imm12 常用位段 [21:10]）。
- 固定可定向的：Rd=bits[4:0]、Rn=bits[9:5]、Rm=bits[20:16]、opcode 主区 bits[28:23]（简化语义段）。
- **实现**：`targetField ∈ {data(默认), rd, rn, rm, opcode}`——rd/rn/rm 精确位段（指令内 bit 位置固定），opcode 用 [28:23]。字节序：指令 4 字节小端，`byteOffset` 定位指令后，字段位段在该 32-bit 指令字内。

**Files:**
- Modify: `CHAOS/CHAOSCache/CHAOSCache.py/.hh/.cc`
- Modify: `configs/se/arm_chaos_cache.py`（加 --target_field）
- 同步：`CHAOS/gem5/src/mem/cache/CHAOSCache/`

**Interfaces:**
- Produces: `targetField`（data=旧字节级行为；rd/rn/rm/opcode=指令编码字段位段——自动把 mask 映射到 32-bit 指令字内的对应位）

- [ ] **Step 1: .py 加参数**

`CHAOS/CHAOSCache/CHAOSCache.py` 的 `targetByteOffset` 后加：

```python
    targetField = Param.String("data",
        "Injection field: data (legacy byte-level, default) | rd | rn | rm | "
        "opcode — A64 instruction-encoding fields (L1I semantic-field FI, "
        "§5.8C). rd=bits[4:0], rn=bits[9:5], rm=bits[20:16], opcode=bits[28:23] "
        "within the 32-bit instruction word at targetByteOffset (4B-aligned). "
        "The faultMask/bitsToChange select bits WITHIN the field.")
```

- [ ] **Step 2: .hh/.cc 实现（把 mask 移位到字段内）**

.hh 加成员 `std::string target_field;`；.cc 构造函数初始化。注入循环里（现有 `data[byteOffset] ^= mask` 字节操作前）加字段重映射：

```cpp
                // §5.8C L1I semantic-field remap: when targetField is an
                // A64 encoding field, move the selected bit(s) into the
                // field's position within the 32-bit instruction word.
                // The cache stores little-endian bytes; the instruction
                // word is data[off..off+3]. Field positions (in-word):
                //   rd=[4:0], rn=[9:5], rm=[20:16], opcode=[28:23]
                unsigned char field_mask = mask;  // bits selected within field
                if (target_field != "data") {
                    int fsh;
                    if      (target_field == "rd")     fsh = 0;
                    else if (target_field == "rn")     fsh = 5;
                    else if (target_field == "rm")     fsh = 16;
                    else /* opcode */                  fsh = 23;
                    // remap: low popcount(mask) bits -> field base + fsh.
                    // Simplest honest remap: shift mask's lowest set bit
                    // pattern to (fsh + bit-within-field from mask low bits).
                    // Use mask as "field-local bit indices": bit k of mask
                    // (k<field width) -> in-word bit (fsh+k).
                    int fw = (target_field == "rd" || target_field == "rn" ||
                              target_field == "rm") ? 5 : 6;
                    unsigned long long inword = 0;
                    for (int k = 0; k < fw; ++k)
                        if (mask & (1u << k)) inword |= (1ULL << (fsh + k));
                    // spread inword mask back to the byte array (LE):
                    unsigned char fm[4] = {0,0,0,0};
                    fm[0] = inword & 0xff; fm[1] = (inword>>8)&0xff;
                    fm[2] = (inword>>16)&0xff; fm[3] = (inword>>24)&0xff;
                    // apply XOR per byte of the instruction word
                    for (int b = 0; b < 4; ++b) {
                        if (fm[b]) {
                            data[byteOffset + b] ^= fm[b];
                        }
                    }
                    stats->numFaultsInjected++;
                    ++faults_injected_count;
                    if (write_log) {
                        *(log_stream->stream())
                            << "Tick: " << curTick()
                            << ", Cache Block Addr: " << blockAddr
                            << ", Field: " << target_field
                            << ", InwordMask: 0x" << std::hex << inword << std::dec
                            << std::endl;
                    }
                    continue;  // field path done; skip the legacy byte path
                }
```

插入位置：现有 `switch (chosen_fault_type_enum)` 字节操作**之前**（field 路径自成一体后 continue）。注意 `byteOffset` 需 4 对齐（config 侧验证：`if targetField != data: byte_offset &= ~3`——在 .cc 里做）。

- [ ] **Step 3: arm_chaos_cache.py 加 --target_field + 验证**

```bash
python3 - << 'PYEOF'
p = "configs/se/arm_chaos_cache.py"
s = open(p).read()
s = s.replace('p.add_argument("--protection_model", default="none",',
'''p.add_argument("--target_field", default="data",
               choices=["data","rd","rn","rm","opcode"],
               help="§5.8C L1I semantic field (A64 encoding: rd[4:0] rn[9:5] "
                    "rm[20:16] opcode[28:23]). data=legacy byte-level.")
p.add_argument("--protection_model", default="none",''')
s = s.replace("        faultType=args.fault_type, bitsToChange=args.bits_to_change,",
"""        faultType=args.fault_type, bitsToChange=args.bits_to_change,
        targetField=args.target_field,""")
open(p,"w").write(s)
print("patched")
PYEOF
cp -f CHAOS/CHAOSCache/*.{py,hh,cc} CHAOS/gem5/src/mem/cache/CHAOSCache/
cd CHAOS/gem5 && source /home/sdc/gem5-deps/env.sh
scons build/ARM/gem5.opt -j16 2>&1 | grep -iE "error|done" | tail -2
chmod +x build/ARM/gem5.opt
G5=$PWD/build/ARM/gem5.opt; cd ../..
# 回归：data 字段（默认）golden
timeout 150 "$G5" --quiet --outdir=runs/u5_reg configs/se/arm_chaos.py \
    --cmd=workloads/directed/reg_chain --cpu=O3 2>&1 | grep -E "^[0-9a-f]{16}$" | tail -1
# 预期 f247ef3fe6f02cfd
# L1I opcode 字段注入（l1i_loop 的循环指令区，resident block 51392 已知锚点）
timeout 180 "$G5" --quiet --outdir=runs/u5_op configs/se/arm_chaos_cache.py \
    --cmd=workloads/directed/l1i_loop --cpu=O3 --target=l1i \
    --target_block_addr=51392 --target_byte_offset=38 --fault_type=bit_flip \
    --bits_to_change=1 --target_field=opcode \
    --probability=1.0 --first_clock=10000 --max_faults=1 \
    --rng_seed=20260825 2>&1 | tail -3
grep -E "Field: opcode" runs/u5_op/cache_injections.log 2>/dev/null | head -2
```

预期：日志出现 `Field: opcode, InwordMask: 0x...`（指令字内 [28:23] 位置）。结果归宿（Hang/Crash——指令突变）如实记录。

- [ ] **Step 4: 提交**

```bash
git add CHAOS/CHAOSCache/ CHAOS/gem5/src/mem/cache/CHAOSCache/ configs/se/arm_chaos_cache.py
git commit -m "§5.8C: CHAOSCache L1I 语义字段定向（A64 编码 rd/rn/rm/opcode 位段）

方案 §5.8C L1I 语义字段注入：targetField ∈ {data(默认), rd[4:0], rn[9:5],
rm[20:16], opcode[28:23]}——mask 重映射到 32-bit 指令字内的字段位段
（小端字节序展开），指令编码字段级量化。

真机自验证：
- data 默认回归：golden 不变
- l1i_loop opcode 字段（block 51392 byte 38）：日志 'Field: opcode,
  InwordMask: 0x...'（引用实际输出）
诚实边界：imm/cond 位段因指令而异未提供（imm12[21:10] 常用段可后续加）；
byteOffset 需 4 对齐由 .cc 保证。"
git push origin fi-wangxu
```

---

### Task 6: CHAOSMem 扩展（addr_map_sub + protectionModel）

方案 §A.2："CHAOSMem `addr_map_sub`/`ecc_logic_fault`" + §4.2 protectionModel 对 Mem 也适用（§2.3 DRAM=secded）。

**Files:**
- Modify: `CHAOS/CHAOSMem/CHAOSMem.py/.hh/.cc`
- Modify: `configs/se/arm_chaos.py`（CHAOSMem 挂载处透传）
- 同步：`CHAOS/gem5/src/mem/CHAOSMem/`

**Interfaces:**
- Produces: `addrMode ∈ {fixed(默认), addr_map_sub}`（F5：注入地址换成另一合法地址段——模拟地址译码错）；`protectionModel`（none/secded——DRAM ECC 语义，复用 CHAOSCache 的 ECC 后处理模式：1-bit 纠正恢复数据、2-bit poison、≥3-bit 逃逸）

- [ ] **Step 1: .py 加参数**

```python
    addrMode = Param.String("fixed",
        "fixed (legacy: inject at the sampled target addr) | addr_map_sub "
        "(F5: redirect the injection to addr ^ addrXorMask — an address-"
        "map/decoder fault that hits a DIFFERENT legal address)")
    addrXorMask = Param.Addr(0,
        "addr_map_sub XOR mask (e.g. 0x1000 flips page bit 12). 0 with "
        "addrMode=addr_map_sub uses 0x1000 default.")
    protectionModel = Param.String("none",
        "DRAM ECC model (§2.3: DRAM=secded proxy): none=raw escape; "
        "secded: 1-bit corrected (revert), 2-bit detected+contained, "
        ">=3-bit latent escape. Reports PA markers for classify_run_pa.")
```

- [ ] **Step 2: .cc 实现**

.hh 加成员 `std::string addr_mode; Addr addr_xor_mask; std::string protection_model;`；构造函数初始化（addrXorMask==0 且 addrMode==addr_map_sub 时默认 0x1000）。

注入点（现有 RMW 写回前）加两块：

```cpp
            // §A.2 addr_map_sub (F5): redirect to another legal address.
            Addr inject_addr = target_addr;
            if (addr_mode == "addr_map_sub") {
                Addr m = addr_xor_mask ? addr_xor_mask : (Addr)0x1000;
                inject_addr = target_addr ^ m;
                if (write_log) {
                    *(log_stream->stream())
                        << "Tick: " << curTick()
                        << ", Site: mem_addr_map_sub (F5)"
                        << ", OrigAddr: 0x" << std::hex << target_addr
                        << ", RedirectedAddr: 0x" << inject_addr << std::dec
                        << std::endl;
                }
            }
```

**精确插入点（已核实）**：`target_addr` 在 `CHAOSMem.cc:208` 赋值（`Addr target_addr = dist(rng);`），`Request` 在 line 213 用它构造。addr_map_sub 重定向插在 **208 与 213 之间**：重定向后 `target_addr = target_addr ^ m;` 直接改写变量（比新变量更小 diff），并在重定向时写日志。

ECC 后处理（RMW 写回前，复用 CHAOSCache 的分支语义）：

```cpp
            // §4.2 protectionModel (DRAM=secded proxy): post-inject ECC.
            if (protection_model == "secded") {
                int bits = __builtin_popcount((unsigned)mask);
                if (bits == 1) {
                    // corrected: revert the byte (write back the orig read)
                    data = orig_data;  // execute时用实际变量名（RMW 读出的原值）
                    stats->numEccCorrected++;  // .hh 加 3 个 stat 字段
                    if (write_log) { /* "EccCorrected: 1-bit reverted" */ }
                    continue;  // skip the fault write-back
                } else if (bits == 2) {
                    stats->numDetectedContained++;
                    if (write_log) { /* "Poisoned: DetectedContained" */ }
                    // leave dirty (poison propagates) — falls through
                } else {
                    stats->numLatent++;
                    if (write_log) { /* "Latent: >=3-bit escape" */ }
                }
            }
```

.hh stats 加 `numEccCorrected/numDetectedContained/numLatent` 三字段 + .cc 构造（照 CHAOSCache 模式）。**注意 CHAOSMem 的 RMW 变量名与 CHAOSCache 不同——执行时先读 CHAOSMem.cc 的注入函数找到"读原值→改→写回"的准确变量（data 变量、写回语句），在上面代码块里替换。**

- [ ] **Step 3: 透传 + 构建 + 验证**

```bash
python3 - << 'PYEOF'
p = "configs/se/arm_chaos.py"
s = open(p).read()
s = s.replace('p.add_argument("--addr_end", type=lambda x: int(x,0), default=0)',
'''p.add_argument("--addr_end", type=lambda x: int(x,0), default=0)
p.add_argument("--mem_addr_mode", default="fixed", choices=["fixed","addr_map_sub"])
p.add_argument("--mem_addr_xor", type=lambda x: int(x,0), default=0)
p.add_argument("--mem_protection_model", default="none", choices=["none","secded"])''')
s = s.replace("        rngSeed=args.rng_seed,\n        maxFaults=args.max_faults,\n        writeLog=True,\n    )\n    board.chaos_mem = CHAOSMem(",
"""        rngSeed=args.rng_seed,
        addrMode=args.mem_addr_mode,
        addrXorMask=args.mem_addr_xor,
        protectionModel=args.mem_protection_model,
        maxFaults=args.max_faults,
        writeLog=True,
    )
    board.chaos_mem = CHAOSMem(""")
open(p,"w").write(s)
print("patched")
PYEOF
cp -f CHAOS/CHAOSMem/*.{py,hh,cc} CHAOS/gem5/src/mem/CHAOSMem/
cd CHAOS/gem5 && source /home/sdc/gem5-deps/env.sh && scons build/ARM/gem5.opt -j16 2>&1 | grep -iE "error|done" | tail -2
chmod +x build/ARM/gem5.opt; G5=$PWD/build/ARM/gem5.opt; cd ../..
# 回归: fixed+none golden
timeout 150 "$G5" --quiet --outdir=runs/u6_reg configs/se/arm_chaos.py \
    --cmd=workloads/directed/l1d_reduce --cpu=Timing 2>&1 | grep -E "^[0-9a-f]{16}$" | tail -1
# 预期 f44d2b9cd4a173cd
# addr_map_sub: 注入重定向日志
timeout 200 "$G5" --quiet --outdir=runs/u6_sub configs/se/arm_chaos.py \
    --cmd=workloads/directed/l1d_reduce --cpu=Timing --chaos_mem \
    --probability=1.0 --first_clock=1000 --max_faults=1 --rng_seed=20260825 \
    --mem_addr_mode=addr_map_sub --mem_addr_xor=0x1000 \
    --addr_start=1048576 --addr_end=1048576 2>&1 | grep -E "^[0-9a-f]{16}$" | tail -1
grep -E "addr_map_sub" runs/u6_sub/main_mem_injections.log 2>/dev/null | head -2
# secded 1-bit: 纠正恢复（输出==golden）
timeout 200 "$G5" --quiet --outdir=runs/u6_ecc configs/se/arm_chaos.py \
    --cmd=workloads/directed/l1d_reduce --cpu=Timing --chaos_mem \
    --probability=1.0 --first_clock=1000 --max_faults=1 --rng_seed=20260825 \
    --fault_type=bit_flip --mem_protection_model=secded \
    --addr_start=1048576 --addr_end=1048576 2>&1 | grep -E "^[0-9a-f]{16}$" | tail -1
grep -iE "numEccCorrected" runs/u6_ecc/stats.txt | head -1
```

预期：sub 日志 `Site: mem_addr_map_sub (F5), OrigAddr->RedirectedAddr`；secded 1-bit `numEccCorrected=1` + 输出 golden。

- [ ] **Step 4: 提交**

```bash
git add CHAOS/CHAOSMem/ CHAOS/gem5/src/mem/CHAOSMem/ configs/se/arm_chaos.py
git commit -m "§A.2/§4.2: CHAOSMem 扩展（addr_map_sub F5 + protectionModel DRAM-ECC）

- addrMode=addr_map_sub (F5): 注入地址 XOR 重定向到另一合法地址（地址
  译码/映射故障——§A.2 清单项）
- protectionModel=secded: DRAM ECC 代理（§2.3 DRAM=secded）——1-bit 纠正
  恢复（revert）/2-bit 检出毒化/≥3-bit 逃逸，PA 标记供 classify_run_pa

真机自验证：（引用实际输出：addr_map_sub 重定向日志 + secded 1-bit
numEccCorrected=1 + fixed/none 回归 golden）"
git push origin fi-wangxu
```

---

### Task 7: 文档收尾（方案文档全项核对 + progress.md）

- [ ] **Step 1: 方案文档逐项更新**

对照本计划 Task 1-6 完成项 + 第一份计划的 Task 1-5，更新 `docs/KUNPENG920-SDC研究方案-系统完备版.md`：§0.3.1 注入器数（16→17 含 CHAOSBPU）、§5.7B（TLB 字段级/SysReg F5 标 done）、§5.8C（L1I 语义字段标 done）、§5.1D/§5.4D（kernel 标 done）、§10.2（FS checkpoint 流水线标 v1 done/Atomic、O3-switch 待）、§A.2（Mem 扩展标 done）、AGENT_TASKS 全行状态。模式与前几轮 doc commit 一致（python 批量 replace）。

- [ ] **Step 2: progress.md 追加本轮**

- [ ] **Step 3: 提交推送**

```bash
git add docs/KUNPENG920-SDC研究方案-系统完备版.md progress.md
git commit -m "docs: 缺口补全计划执行状态（TLB字段级/SysReg F5/kernel批/FS checkpoint/L1I语义/Mem扩展）"
git push origin fi-wangxu
```

---

## Self-Review 结论

**1. Spec coverage（原方案对照核查）：**

| 原方案项 | 状态 | 本计划任务 |
|---|---|---|
| §5.7B TLB pfn_to_mapped/targetField/I-TLB | ❌→Task 1（targetField 全集 + pfnOffset 代理）| I-TLB 挂载：**config 层即可挂**（arm_chaos_fs.py 挂载处 `dtb` 换 `itb`——执行者在 Task 1 Step 4 顺带把 `--tlb_target_itb` 开关加上，一行 if）|
| §5.7B SysReg value_to_legal | ❌→Task 2 | ✓ |
| §5.1D ptr_chase | ❌→Task 3 | ✓ |
| §5.4D 7类×2变体 | ❌→Task 3 | ✓ |
| §10.2 FS checkpoint 流水线 | ❌→Task 4（v1 Atomic；O3-switch 诚实缩步）| ✓ |
| §5.8C L1I 语义字段 | ❌→Task 5 | imm/cond 未做（位段因指令而异——诚实边界已注明）|
| §A.2 Mem addr_map_sub/ecc_logic_fault/protectionModel | ❌→Task 6 | ecc_logic_fault（ECC 逻辑自身故障）未做——它需模拟 ECC 电路故障（漏检），本计划做 protectionModel（ECC 语义）已覆盖主要语义；ecc_logic_fault 留待（诚实标注）|
| §5.4 CHAOSExMon | ❌ 未纳入 | gem5 O3 的 LLSC 在 lsq_unit.cc:856/1383 有 isLLSC 判定点——可作为后续任务（本计划已达 6 任务规模，ExMon 优先级 P3 且现场无直接指向）|
| CHAOSCHI/NoC/HCCS（§A.2 S4）| ❌ 未纳入 | 方案已标"E3/E4 独立子项目"（~20 补丁），不属于本计划范围 |
| CHAOSDecode（P4）| ❌ 未纳入 | 方案标"低优先级，可跳过" |

**2. Placeholder scan：** 无 TBD。两处"执行时先读"是条件指令（Task 4 Step 2 明确"从 arm_chaos_fs.py 逐块复制"；Task 6 Step 2 明确"先读 CHAOSMem.cc 的 RMW 变量名替换"）——指向已有代码的具体复制/替换，不是未设计内容。

**3. Type consistency：** Task 1 的 `targetField/pfnOffset` 参数名在 .py/.hh/.cc/config 四处一致；Task 5 的 `targetField`（rd/rn/rm/opcode）与 CHAOSCache 现有 `targetBlockAddr/targetByteOffset` 正交不冲突；Task 6 的 `addrMode/addrXorMask/protectionModel` 与 CHAOSMem 现有 `addr_start/addr_end` 正交。

**风险（执行者注意）：**
- Task 3 的 alias4k/replay case 确定性需修到全 OK（已给判据与修法方向）
- Task 4 boot 阶段是 4-8 分钟长任务（后台跑）；inject 的 restore 兼容性是未知数（两个方向都有记录价值）。**restore 接入已核实为 `set_kernel_disk_workload(checkpoint=...)`（kernel_disk_workload.py:230）——不是 Simulator 构造参数**（计划内代码已按核实 API 写）
- Task 6 的 CHAOSMem RMW 插入点已核实（target_addr 赋值于 line 208、Request 构造于 line 213——重定向插在两者之间改写 target_addr）
- Task 1 的 `Site:` 日志字段保证 runner 的 faults 计数兼容（`pfn_to_offset`/`field_ap` 等行都含 `Site:`）
