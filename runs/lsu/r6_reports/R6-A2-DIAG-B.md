# R6-A2 阶段 1 · Lane B 只读诊断报告 — 真实 AGU 操作数/寻址模式、A04-a 对象登记、A05-a/b/c/d 操作数级 hook

- Lane: B（只读诊断；唯一写入 = 本文件）。Date: 2026-10-28。
- Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026`
- Branch/HEAD: `fix/r6-a-unit-20261028` / `defb3e0d`
- 方法：只读 `grep/Read/sed`、`objdump/readelf/nm`、`git log`。**未构建、未启动 gem5/scons/campaign/pytest、未改任何源码/配置/测试、未做 git 写操作。**
- 前序权威输入：`runs/lsu/r6_reports/R6-A-FINAL-REPORT.md`、`R6-A-STATUS.md`、`R6-A-DIAG-B.md`、`docs/gem5-fi/lsu/mdspec/{runid_map.json,coverage_matrix.md}`。本报告**不重做**既有静态审计，只回答 A2 阶段 1 的新问题（真实操作数定位 / 对象登记 / 操作数级 hook 设计 / 风险）。

---

## 0. 结论先行（八条，全部有源码或二进制实证）

| # | 结论 | 关键证据 |
|---|---|---|
| C1 | **gem5 O3 没有单一 AGU execute 函数**。EA 由 ISA 生成的 `initiateAcc` 逐指令类计算；O3 侧只有两个同构分发点 `LSQUnit::executeLoad/executeStore`，且 `chaosAguResumeInst` 复制了整段分发（三处）。 | `iew.cc:1194,1223,1237,1253,1429,1440,1453`；`lsq_unit.cc:710,725,782,798`；`dyn_inst.cc:377,386` |
| C2 | 现有 PRE 钩子 `CHAOSAddrPath::maybeCorruptPre` 位于 `LSQ::pushRequest` 入口 = **EA 计算之后**，只拿得到最终 `addr`、`size`、`isLoad`、`flags`、`dyn_inst_seq`、`byte_enable`；**拿不到 base/index 寄存器值、extend 类型、shift 量、寻址模式**。 | `lsq.cc:772,800`；`CHAOSAddrPath.cc:462-465` |
| C3 | 真实操作数只存在于 ISA 生成代码的局部变量：`XBase = xc->getRegOperand(this,0)`、`XOffset = getRegOperand(this,1)`、`EA = XBase + extendReg64(XOffset, type, shiftAmt, 64)`；`type/shiftAmt` 是 **StaticInst 成员（所有动态实例共享）**，只能复制到局部再用，**绝不能原地改**。 | `build/ARM/arch/arm/generated/exec-ns.cc.inc:57690-57745`（`LDRB64_REG::initiateAcc`）；源码真源 `ldr64.isa:111-141,187-194`、`str64.isa:121-141,151-158`、`mem64.hh:228-243` |
| C4 | **"EA 计算前"唯一干净插入点 = ISA `buildEACode()` 生成的 `initiateAcc` 里、EA 表达式之前**。备选（pushRequest 重算）需要给 `MemoryReg64` 加访问器并重读操作数，且**无法表达 A05-d 的写回**（写回是独立 microop，decode 时已构造）。 | 见 §1.4 |
| C5 | **A05-a/b/c 在 W3 `agu_addrmodes` 上结构性 ineligible**：main 的 164 行反汇编里**没有任何标量 register-offset / sxtw / uxtw**；只有 2 条 **SIMD** `ldr q0,[x4,x2]`/`str q0,[x2,x1]`（0x4006a8/0x4006b0，32 次循环）。C 源码的 base+index/extend 循环被 -O2 强度削减成 post-index 指针步进。W0 `mini_check` **有**标量 reg-offset（`ldr x0,[x1,x0,lsl #3]` @0x4005d8，S=1；`ldr x2,[x20,x1]` @0x4006b8，S=0）。 | `objdump -d --disassemble=main`（见 §3.0 原文） |
| C6 | W3 是 A05-d 的合格载体（pre: `ldr x1,[x2,#8]!` @0x400604；post: 多条 `ldr x*,[x*],#8`、`strb w2,[x3],#-1`）。 | 同上 |
| C7 | **对象登记不需要改 workload**：SE 进程 ELF 的 `.symtab` 带 `st_value` **和 `st_size`**（`array` 0x493000/512B、`output` 0x493200/512B、`data` 0x4919a0/512B），且 gem5 会把 **LOCAL OBJECT 符号**装入 `SymbolTable`。 | `readelf -sW`；`base/loader/elf_object.cc:186-225`；`base/loader/object_file.hh:130`；`sim/process.hh:234` |
| C8 | **W0 的 `data` 符号重名**（0x4919a0/512 与 0x496e80/8 两条同名 LOCAL）：`SymbolTable::insert` 对重名**静默丢弃后者**，按名字登记会得到不确定结果 ⇒ 必须支持显式 `addr+size` 登记，或在 startup 阶段响亮拒绝。 | `readelf -sW`；`base/loader/symtab.cc`（`insert`：`nameMap.insert(...).second==false → return false`） |

---

## 1. 真实 AGU 操作数 / 寻址模式定位

### 1.1 完整调用链（file:line + 函数签名）

```
IEW::executeInsts()                                   cpu/o3/iew.cc:1194  if (inst->isMemRef())   ← 单条 DynInst = 一个 microop
  ├─ atomic:  ldstQueue.executeStore(inst)             iew.cc:1223
  ├─ load:    ldstQueue.executeLoad(inst)              iew.cc:1237
  └─ store:   ldstQueue.executeStore(inst)             iew.cc:1253
        ↓
Fault LSQUnit::executeLoad(const DynInstPtr &inst)     cpu/o3/lsq_unit.cc:710
    load_fault = inst->initiateAcc();                  lsq_unit.cc:725
Fault LSQUnit::executeStore(const DynInstPtr &store_inst)  lsq_unit.cc:782
    Fault store_fault = store_inst->initiateAcc();     lsq_unit.cc:798
        ↓
Fault DynInst::initiateAcc()                           cpu/o3/dyn_inst.cc:377
    fault = staticInst->initiateAcc(this, traceData);  dyn_inst.cc:386   ← this(DynInst) 作为 ExecContext
        ↓
Fault <ISA>::LoadReg64::initiateAcc(ExecContext *xc, traceData)   [生成代码]
    XBase   = (xc->getRegOperand(this, 0) & mask(...));
    XOffset = (xc->getRegOperand(this, 1) & mask(...));
    EA = XBase + extendReg64(XOffset, type, shiftAmt, 64);          ← ★真实 EA / 操作数
        ↓
Fault DynInst::initiateMemRead(Addr,unsigned,Flags,byte_enable)   dyn_inst.cc:423  (load)
Fault DynInst::writeMem(uint8_t*,unsigned,Addr,Flags,...)         dyn_inst.cc:444  (store)
Fault DynInst::initiateMemAMO(...)                                dyn_inst.cc:456  (atomic)
        ↓
Fault CPU::pushRequest(...)                            cpu/o3/cpu.hh:661-669
        ↓
Fault LSQ::pushRequest(...)                            cpu/o3/lsq.cc:772
    size = cpu->chaosAddrPathPre->maybeCorruptPre(...)  lsq.cc:800          ← ★现有 PRE 钩子（EA 之后）
    cpu->chaosPropagation->registerInjection(...)       lsq.cc:809-813
    inst->effAddr = request->getVaddr();                lsq.cc:939          ← 故障 EA 写入 effAddr
```

生成代码实物（`build/ARM/arch/arm/generated/exec-ns.cc.inc:57690-57745`，`LDRB64_REG::initiateAcc`）：

```cpp
uint64_t XBase = 0; uint64_t XOffset = 0;
XBase   = (xc->getRegOperand(this, 0) & mask(aarch64 ? 64 : 32));
XOffset = (xc->getRegOperand(this, 1) & mask(aarch64 ? 64 : 32));
EA = XBase + extendReg64(XOffset, type, shiftAmt, 64);
unsigned memAccessFlags = 0|ArmISA::MMU::AllowUnaligned;
fault = initiateMemRead(xc, traceData, EA, Mem, memAccessFlags);
```

### 1.2 操作数 / 寻址模式数据落点（类 + 字段 + 谁在用）

| 数据 | 定义位置 | 类型/语义 | 在何处参与 EA |
|---|---|---|---|
| `Memory64::dest/base/baseIsSP/numMicroops=3/uops` | `arch/arm/insts/mem64.hh:108-152` | `RegIndex base` | `XBase` 读取 slot 0 |
| `MemoryImm64::imm` | `mem64.hh:156-170` | `int64_t` 立即数 | `self.offset = " + imm"`（`ldr64.isa:183`） |
| `MemoryReg64::offset/type/shiftAmt` | `mem64.hh:228-243` | `RegIndex offset; ArmExtendType type; uint64_t shiftAmt` | `self.offset = " + extendReg64(XOffset, type, shiftAmt, 64)"`（`ldr64.isa:190`） |
| `MemoryPreIndex64` / `MemoryPostIndex64` | `mem64.hh:202-226` | 继承 `MemoryImm64`，**仅立即数**（AArch64 架构如此） | pre: `EA = XBase + imm`；post: `EA = XBase`（`buildEACode` 的 `if not self.post`，`ldr64.isa:136-141`） |
| `ArmExtendType` 枚举 | `arch/arm/types.hh:222-232` | `UXTB=0,UXTH=1,UXTW=2,UXTX=3,SXTB=4,SXTH=5,SXTW=6,SXTX=7` | `extendReg64` 的 `len`/`sign_extend` |
| `ArmStaticInst::extendReg64(uint64_t base, ArmExtendType, uint64_t shiftAmt, uint8_t width)` | `arch/arm/insts/static_inst.cc:134-168` | 低 `len` 位取出、左移 `shiftAmt`、可选符号扩展、按 `width` 掩码 | EA 的 offset 项 |
| 写回（pre/post） | `microop`：`MicroAddXiUop`（`macromem.isa:606`，源码 `macromem.cc:408,434`）/ `MicroAddXERegUop`（`macromem.isa:621`，`macromem.cc:1189,1297,1365`） | 宏操作第 2 个 uop，`base = base (+ imm / + extend(offset))` | **EA 之后**；decode 时构造 |
| 宏操作的 uop 组装 | `arch/arm/isa/templates/mem.isa:1006-1050`（`LoadStoreImmConstructor`）、`:1180-1215`（`LoadRegConstructor`） | `uops[0]=acc_name`（算 EA），`uops[1]=wb_decl` | — |
| A32 版（非本轮 W3 载体） | `arch/arm/insts/mem.hh:314-330`（`MemoryReg`）、模板 `arch/arm/isa/templates/mem.isa:75-130`（`ea_code` 里 `EA = Base`） | `shiftAmt/shiftType/index` | A64 走 `mem64.hh`，不是这条 |

结论：**操作数级故障需要的信息全部在 ISA 生成代码里（局部 `XBase/XOffset` + 成员 `type/shiftAmt/imm/base/offset`）**，在 pushRequest 处已全部丢失（只剩合成后的 EA）。

### 1.3 现有 CHAOSAddrPath 钩子的精确时序与可见性

- `maybeCorruptPre(Addr&, unsigned, bool, Request::Flags&, uint64_t dyn_inst_seq, std::vector<bool>&)` — `CHAOSAddrPath.hh:53-55`，调用点 `lsq.cc:800`。
- 时序：**EA 已算出**（`initiateAcc` 内，早于 `DynInst::initiateMemRead/writeMem`）；PRE 钩子本身在 `lsq.cc:800`，而 `request->initiateTranslation()` 在 `lsq.cc:933`（`SingleDataRequest::initiateTranslation` 在 `:1052`，最终 `sendFragmentToTranslation` 才触发 POST 钩子 `maybeCorrupt`）。即：**先 EA → 再 PRE → 再 split/Request → 再 DTLB(POST)**，PRE 在 EA 之后、DTLB 之前。
- 可见：`addr`（最终 EA）、`size`、`isLoad`、`flags`、`dyn_inst_seq`、`byte_enable`。
- 不可见：`base`/`index` 寄存器号与值、`type`、`shiftAmt`、`imm`、pre/post 模式、`DynInst` 句柄本身（只有 seqNum 被传进来）。
- 因此 A05-a/b/d **在物理上无法**由该钩子表达；现有 `a05_shift`（`CHAOSAddrPath.cc:626-632`）只能做"最终 EA 低字节旋转"，与"改 shift 操作数并真实重算 EA"无关（见 §5 风险 R1）。

### 1.4 "EA 计算前"插入点：两种可行设计

#### 设计 A（推荐）：ISA `buildEACode()` 生成操作数钩子

- 位置：`arch/arm/isa/insts/ldr64.isa:111-141` 与 `str64.isa:121-141` 的 `buildEACode()`；生成物在 `build/ARM/arch/arm/generated/exec-ns.cc.inc`（EA 行前）。
- 新增（Arm 侧，独立文件，避免污染 ISA 语义文件）：

```cpp
// arch/arm/insts/chaos_agu_operands.hh  —— 仅 O3 注入器使用；未挂载时零开销（一次全局指针判空）
namespace gem5 { namespace ArmISA {

enum class ChaosAguFaultKind : uint8_t { None, SwapBaseIndex, SwapExtend, SetShift,
                                          PrePostInvert };

struct ChaosAguRegView {              // 传给回调的"真实操作数快照"
    Addr     pc;
    bool     is_load;
    unsigned size;                    // ≈ sizeof(Mem)，生成代码里传入
    RegIndex base_reg, index_reg;
    uint64_t base_val, index_val;
    ArmExtendType type;
    uint64_t shift;
    // 输出
    uint64_t new_base_val, new_index_val;
    ArmExtendType new_type;
    uint64_t new_shift;
    bool     applied;
};

using ChaosAguRegHookFn = bool (*)(ExecContext *xc, ChaosAguRegView &v);
void setChaosAguRegHook(ChaosAguRegHookFn fn);          // CHAOSAddrPath::startup() 调；nullptr = 关
bool chaosAguRegOperands(ExecContext *xc, bool is_load, unsigned size,
                         RegIndex base_reg, RegIndex index_reg,
                         uint64_t &base_val, uint64_t &index_val,
                         ArmExtendType &type, uint64_t &shift);   // 生成代码调用
} }
```

- 生成代码改造（最小面，只改 register-offset 与 pre/post 两类；imm（无写回）不生成钩子）：

```python
# ldr64.isa / str64.isa  (LoadRegInst64.__init__)
self.offset = (";\n"
  "        {\n"
  "            uint64_t _cb = XBase, _ci = XOffset; ArmExtendType _ct = type; uint64_t _cs = shiftAmt;\n"
  "            ArmISA::chaosAguRegOperands(xc, /*is_load=*/true, sizeof(Mem), base, offset,\n"
  "                                        _cb, _ci, _ct, _cs);\n"
  "            EA = _cb + extendReg64(_ci, _ct, _cs, 64);\n"
  "        }")

# pre/post（LoadPre64/Post64 的 buildEACode 分支）
#   pre : chaosOff 默认 imm；post: chaosOff 默认 0；钩子可互换 → EA = XBase + chaosOff
#   WB microop 保持 base = base + imm（两模式最终基址相同，语义正确）
```

- 优点：**字面意义上"EA 计算前改写操作数"**；拿得到真实 base/index 值与 extend/shift；单点覆盖 IEW 正常路径 + `chaosAguResumeInst` 复制路径（`iew.cc:1429-1453`）+ 翻译延迟重执行；O3 侧零改动。
- 代价：改 2 个 vendored ISA 生成文件（`arch/arm/isa/insts/ldr64.isa`、`str64.isa`）+ 1 个新 `.hh/.cc` + `SConscript`；所有 ARM 指令**重新生成并重编译**（`scons` 全量 ARM 目标，成本一次）。
- 语义护栏（必须写死）：`type/shiftAmt` 是 StaticInst 成员、**跨动态实例共享** ⇒ 只能复制到局部 `_ct/_cs` 再改；任何原地 `type = ...` 会污染后续全部同类指令（见 §5 R2）。

#### 设计 B（备选）：pushRequest 处用操作数重算 EA

- 需要：给 `MemoryReg64` 增加 `baseReg()/indexReg()/extendType()/shiftAmt()` 访问器（`mem64.hh:228-243` 当前全 `protected`），并在 `lsq.cc:800` 把 `inst` 传进钩子，用 `inst->getRegOperand(inst->staticInst.get(), 0/1)` 读值（`dyn_inst.hh:1214-1220`，`renamedSrcIdx(idx)`；reg-offset 生成代码已把 `base` 放 slot0、`offset` 放 slot1，见 `build/.../decoder-ns.cc.inc:90` 与 `decoder-ns.hh.inc:122752`）。
- 能实现 a/b/c（等价于"重算 EA"），**不能实现 d 的写回**（写回 microop 在 decode 时已构造，`templates/mem.isa:1006-1050`）。
- 额外风险：`DynInst` 源操作数槽位顺序是 ISA 生成约定，不是稳定 API；跨架构/微操作（如 `_dest==_index` 时会插入 `MicroUopRegMov`，`templates/mem.isa:1133-1145`）需另行判断；且第二次"重算"与 ISA 首次计算重复，属于"事后覆盖 EA"而非"EA 计算前改操作数"。

**推荐 A；B 仅作为 A 不可落地时的降级方案，且必须如实标注"EA 事后重算"而非"操作数改写"。**

### 1.5 是否有统一 AGU execute 点 —— 两条路径的差异

**没有单一函数。** O3 侧只有 `LSQUnit::executeLoad`（`lsq_unit.cc:710`）与 `LSQUnit::executeStore`（`:782`）两个同构入口；EA 的算术在 ISA 生成的 `initiateAcc` 里逐类展开。差异：

| 维度 | load 路径 | store 路径 | atomic 路径 |
|---|---|---|---|
| IEW 分发 | `iew.cc:1237` | `iew.cc:1253` | `iew.cc:1223`（`isAtomic()` 走 executeStore） |
| LSQUnit | `executeLoad` | `executeStore` | `executeStore` |
| DynInst 入口 | `initiateMemRead`（`dyn_inst.cc:423`） | `writeMem`（`:444`） | `initiateMemAMO`（`:456`，带 `amo_op`） |
| 失败/重执行 | **翻译延迟 → `deferMemInst` → 再次进入 `executeLoad` → 再算一次 EA**（`iew.cc:1239-1245`） | 同样可能 defer（`iew.cc:1255-1261`） | 同 store |
| 提前的副作用 | 无 | `storeQueue[idx]` 数据/size 在 `executeStore` 里设定；`canWB` 等 | 同 store |
| 微操作 | 无写回的 reg-offset 是单指令；pre/post 是 macroop，uop[0] 算 EA、uop[1] 写回 | 同 | 无 |
| A07 特殊路径 | `chaosAguResumeInst`（`iew.cc:1404-1453`）**逐字复制** executeInsts 的 memRef 分支 | 同 | 同 |

**对设计的直接影响**：(a) 任何"在 O3 侧 arm 一次、在 ISA 侧消费"的两点设计，必须在 `iew.cc:1215`（正常）与 `iew.cc:1429-1453`（resume）**两处**布置；把全部逻辑放进 ISA 钩子则自动覆盖两者 ⇒ 这是推荐设计 A 的另一理由。(b) 翻译延迟会**二次进入** `executeLoad/Store` ⇒ 同一 `dyn_inst_seq` 的故障必须**按 seq 缓存、幂等地重放**，不能每次重掷（否则故障在重执行时静默消失或重复计数，见 §5 R3）。

---

## 2. A04-a 同对象地址替换的真实对象注册机制

### 2.1 工作负载与 oracle 对象（源码 + 二进制实证）

| 项 | W3 `agu_addrmodes` | W0 `mini_check` |
|---|---|---|
| 源码 | `workloads/directed/agu_addrmodes.c` | `workloads/directed/mini_check.c` |
| oracle 对象 | `static unsigned long array[N] __attribute__((aligned(4096)));`（N=64，512B，`agu_addrmodes.c:19-21`）+ `output[N]`（512B） | `static unsigned long data[N];`（N=64，512B，`mini_check.c:28`）+ `mmap` 8192B 的 page1/page2（`:57-72`） |
| 对象地址来源 | **ELF 符号表**：`array`=0x493000/512B，`output`=0x493200/512B（`readelf -sW`，LOCAL OBJECT）；无 m5 pseudo-op、无输出文件 | `data`=0x4919a0/512B **且** 0x496e80/8B（**同名两条 LOCAL**）；mmap 区无符号 |
| 逐地址 oracle | 无（仅末尾 FNV-1a 校验和） | 无（同左） |
| 对齐 | `aligned(4096)` ⇒ base 页对齐，元素 8B 自然对齐 | `.bss` 内，实测 32B 对齐；元素 8B |
| 有效访问范围 | `[array, array+512)`；注意 `output` 紧邻**同一 4KiB 页** | `[data,data+512)` + page1 256 槽 `[pages,pages+4096)` |

即：**objbase/size 可直接从 SE 进程 ELF 的 `.symtab` 取得（含 st_size）**，无需 workload 改动；`elem_width`（8B）无法从符号取得，须由配置给出。

### 2.2 最小可用"对象登记"机制（推荐设计）

**登记来源优先级**：① 显式 `addr + size + elem_width`（最确定，规避重名/剥离 symtab）→ ② `symbol name` 解析（用同一 ELF 的 `st_value`/`st_size`）→ ③ 二者都给则交叉校验，不一致即 fatal。**绝不退回同页代理。**

访问路径（已在源码确认可用）：

```cpp
Process *p = cpu->tcBase(0)->getProcessPtr();          // cpu/thread_context.hh:147
loader::SymbolTable &st = p->objFile->symtab();         // sim/process.hh:234; base/loader/object_file.hh:130
auto it = st.find("array");                             // base/loader/symtab.hh:453-457
uint64_t base = it->address(), size = it->sizeOrDefault(0);   // symtab.hh:105-118
```

注意：`SEWorkload::symtab()/insertSymbol()` 在 SE 下 `panic`（`sim/se_workload.hh:68-82`），因此**不能**用 `m5 addsymbol`（`sim/pseudo_inst.cc:253-276` 会先调用它）做 SE 登记；应直接走 `Process::objFile->symtab()`。`ElfObject` 会把 `STB_LOCAL`/`STT_OBJECT` 一并插入（`base/loader/elf_object.cc:186-225`），所以 `array/output/data` 都在表里。

**配置协议（新增 SimObject 参数，`CHAOSAddrPath.py`）**：

```python
aguObjectSpec = Param.String("",   '对象登记，分号分隔；每项 '
    '"id:symbol:size:elem_width[:align]" 或 "id:@addr:size:elem_width"；'
    '例: "arr:array:512:8:8" 或 "arr:@0x4919a0:512:8"；A04-a 必需，缺失即 fatal')
```
- `id`：object_id（证据用）；`size`：对象字节数；`elem_width`：元素宽度（target 必须是元素起点且 `target % size(访问宽度)==0`）；`align` 可选（默认 = elem_width）。
- 解析时机：`CHAOSAddrPath::startup()`（此时所有 SimObject 已构造、`Process` 已加载 ELF，`sim/process.cc:164` 已填充符号表）。
- **响亮拒绝**（fatal/panic，绝不降级）：
  1. 需要对象表的模式（`a04_same_object`）但 `aguObjectSpec` 为空；
  2. 符号不存在 / `sizeIsValid()==false` / 给定 size 与符号 size 不符；
  3. `elem_width==0`、`size % elem_width != 0`、`base % elem_width != 0`；
  4. 名字解析出的地址不在进程 image 段内（用 `loader::MemoryImage`，`base/loader/memory_image.hh:52`，可选增强）；
  5. 多进程/多线程（`getProcessPtr()` 非唯一）→ 拒绝（本家族为单进程 SE）；
  6. FS 平台（无 SE `Process`）→ 拒绝（A04-a 仅 SE；FS 另需裁决）。
- 启动打印一行 `CHAOS_AGU_OBJECTS: id=arr base=0x.. size=512 elem=8 symbol=array`（可审计）。

**eligibility（源 EA 属对象）**——必须放在**触发决策之前**（照抄 A06 的 `a06_load_declined` 纪律，`CHAOSAddrPath.cc:498-601`），否则 F0 的 `spent` 会被不合格事件吞掉：

```cpp
// 仅当 a04_same_object
const Obj *o = findObject(addr, size);   // addr >= o->base && addr + size <= o->base + o->size
if (!o) { ++obs_pre_a04_not_in_object; return size; }        // 不计 eligible、不消耗预算
const uint64_t src_off = addr - o->base;
if (src_off % size != 0) { ++obs_pre_a04_unaligned_source; return size; }
```

**target 选择（同对象、!=source、size 对齐、不越界）**：

```
k_max = o->size / o->elem_width
候选 k ∈ [0,k_max)，k != src_off/o->elem_width（若 src_off 是元素起点；否则按字节槽）
target = o->base + k*o->elem_width
约束：target != addr；target % size == 0（按访问宽度对齐，规格"size 对齐"）；
      target + size <= o->base + o->size（不越界）；
      若要求"生命周期"：对象全程存活（静态/全局或 main 期 mmap）——本轮两个载体都满足
随机选一个满足约束 k（确定性 rng；失败则 ++obs_pre_a04_no_candidate，不注入）
```
注意：`size` 在此处是**整个访问宽度**（split 发生在 pushRequest 之后：`lsq.cc:887-915` 才构造 `SplitDataRequest`），所以越界检查用完整 size 是正确的。

**证据字段**（扩展现有 `registerInjection`，`CHAOSPropagation.hh:228`）：

```
object_id, base, size, elem_width, source_offset, source_elem, target_offset, target_elem,
replace_distance, same_cache_line(=64B), old_addr, new_addr, size, isLoad
```

**子模型路由（消除代理）**：

| preMode 值 | 含义 | eligibility |
|---|---|---|
| `a04_same_object`（新） | A04-a | 源 EA 完全落在登记对象内；target 同对象、对齐、不越界 |
| `a04_same_page`（新） | A04-b | 同 4KiB 页；target 按**访问宽度**对齐（不是固定 16B）；!=source；SE 页粒度映射保证已映射 |
| `a04_subst`（旧） | **废弃别名 → 配置期 `p.error` 拒绝**（沿用 `a06s_store_size` 先例，`CHAOSAddrPath.cc:706-724`、`lsu_proxy.py` choices） | — |

### 2.3 需改的文件（A04-a）

| 类别 | 文件 |
|---|---|
| C++ | `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.{hh,cc}`（对象表、eligibility、target、证据、summary） |
| C++（共享） | `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{hh,cc}`（新证据字段/节点） |
| C++（可选） | `CHAOS/gem5/src/cpu/o3/lsq.cc`（若需把 `inst` 传入 PRE 钩子；A04-a 仅用 EA/size，**不必**改） |
| Config | `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.py`（`aguObjectSpec`）；`configs/se/lsu_proxy.py`（`--agu_object_spec`、validation、choices） |
| Tools | `tools/lsu_campaign.py`（`MODEL_FLAGS["A04"]` → `a04_same_object` + `--agu_object_spec`；W0 用显式 addr 因重名）、`tools/lsu_runid_map.py`（`SPEC_IMPL_LANDED`）、`tools/lsu_prop_fields.py`/`lsu_chain_check.py`（新字段） |
| Workload | **无需改**（ELF 符号 + 配置 size/elem_width 足够）。可选：把 W0 的两条同名 `data` 重命名为 `oracle_data`（行为/校验和不变，但二进制哈希变 ⇒ 需重验 golden 并更新 manifest）；或对 W0 一律用 `addr+size` 登记 |
| Docs/status | `docs/gem5-fi/lsu/mdspec/*`、XLSX（主 agent，非实现 owner） |

---

## 3. A05-a/b/c/d 真实操作数级 hook 设计

### 3.0 前提事实：W3 载体的指令形态（决定可行性）

`objdump -d workloads/directed/agu_addrmodes --disassemble=main`（164 行）真实输出（摘）：

```
  400558: f8408441  ldr x1, [x2], #8        ; post-index
  4005c0: f84084a2  ldr x2, [x5], #8        ; post-index
  400604: f8408c41  ldr x1, [x2, #8]!       ; pre-index（唯一一条）
  400678: 38403441  ldrb w1, [x2], #3       ; post-index（byte）
  40068c: f947fc82  ldr x2, [x4, #4088]     ; base+imm
  4006a8: 3ce26880  ldr q0, [x4, x2]        ; ★SIMD register-offset（循环 32 次）
  4006b0: 3ca16840  str q0, [x2, x1]        ; ★SIMD register-offset（循环 32 次）
  400710: 381ff462  strb w2, [x3], #-1      ; post-index（负立即数）
```

- **无任何标量 `sxtw/uxtw/lsl #3`**；唯一标量 reg-offset 形态不存在。
- 两条 SIMD reg-offset 走 `neon64_mem.isa` 的 `MicroNeonMemOp`：其 EA 是 `EA = XURa + imm`（`neon64_mem.isa:57-59`），`XURa` 由**decode 期构造的独立地址 microop** 预算出。因此标量寄存器钩子**不覆盖**它们；若要纳入 A05-a/c，必须另在 NEON 宏操作构造处加钩子（更大改动，且模型范围是否包含 SIMD 属裁决问题）。
- W0 `mini_check`（有标量 reg-offset）真实输出（摘）：
```
  4005d8: f8607820  ldr x0, [x1, x0, lsl #3]  ; ★标量 reg-offset, S=1, shift=3
  4006b8: f8616a82  ldr x2, [x20, x1]         ; ★标量 reg-offset, S=0, shift=0
  400520: f8008460  str x0, [x3], #8          ; post-index
```

**结论（必须写进状态表）**：
1. A05-d 在 W3 上有充足合格事件（pre 1 条 + post 多条，含负立即数）。
2. A05-a/c 在 **W3 上无标量合格事件**（只有 2 条 SIMD）；A05-b 在 W3 上无合格事件。
3. 让 A05-a/b/c 在 W3 上有覆盖，只有三条路，且都需裁决/新载体：
   - (i) 重建 W3（asm 屏障保住 `ldr x,[xN,xM,lsl #k]` / `wM,uxtw|sxtw`），**golden 变**（校验和会变，因为新增/改变访问序列；若只插入不改变数据流可用 volatile 屏障保持校验和）；
   - (ii) 把 A05 载体换成 W0（有标量 reg-offset 的两种 shift；但 A05 的 RunID 固定 W3 ⇒ **频率/负载策略裁决**）；
   - (iii) 裁决"SIMD reg-offset 纳入 A05-a/c 范围"并给 NEON 路径加钩子。

### 3.1 公共机制（四子模型共用）

- **触发资格 = 指令形态**：钩子只在 register-offset（a/b/c）或 pre/post（d）的生成代码里发出 ⇒ `attempted/eligible` 分母天然等于"命中对应寻址模式"的流（正是 A05 触发列语义），**不支持的形态根本不进入钩子 ⇒ 结构上不消耗注入预算**。
- **触发/证据/漏斗**仍全部在 `CHAOSAddrPath`：ISA 钩子通过全局函数指针回调（`setChaosAguRegHook`），回调内 `dynamic_cast<o3::DynInst*>(xc)` 取 `seqNum`（RTTI 可用：`cpu/o3/lsq.cc:437,468`、`dyn_inst.cc:428` 已用 `dynamic_cast`），再调 `lsuTrigger->onAttempt()/onEligible()/noteOutcome()`（`chaos_lsu_trigger.hh:245,253,307`）。
- **守卫**：`di == nullptr || di->cpu != o3cpu_resolved` → 直接返回（覆盖 Atomic/Simple/checker CPU 误入）。
- **幂等**：决策按 `dyn_inst_seq` 缓存（`struct {uint64_t seq; ChaosAguFaultKind kind; ...}` 单槽）；同一 seq 的重执行（翻译延迟，`iew.cc:1239-1245`）**重放同一决策**，不重掷、不二次计数。
- **no-op 守卫**：改完操作数后若 `new_EA == old_EA`（或该子模型对该值不可见），计 `no_effect`（`noteOutcome(false)`）并**不写日志为 injected**——与 R6-F5-NOEFFECT 计数纪律一致（`chaos_lsu_trigger.hh:303-315`）。
- **证据**：每次注入写一行 injection log（沿用 `/tmp` 外 `addrpath_injections.log` 格式，追加字段）+ PROP `inj`/`addr_form` 节点（`registerInjection` 扩展版本）。

### 3.2 A05-a：base/index 互换

- **适用形态**：标量 `MemoryReg64`（AArch64 "Register offset"，无写回）。AArch64 的 register-offset 形态**没有** pre/post 变体（pre/post 仅立即数，`mem64.hh:202-226`），所以 a 与 d 的指令集合天然不相交。
- **ineligible**：
  1. `shift == 0` 时加法可交换 ⇒ `EA` 恒不变（**结构性 no-op**）：只有 S=1（shift=log2(size)）才可能有变化。⇒ 必须 `shift != 0` 才 eligible；否则计 `no_effect`。
  2. `new_EA == old_EA`（如 base==index）→ no_effect。
  3. 非标量形态（SIMD/无写回立即数）→ 不进入钩子。
- **新值计算**：
```cpp
new_EA = index_val + extendReg64(base_val, type, shift, 64);   // 互换后
old_EA = base_val  + extendReg64(index_val, type, shift, 64);
```
  ⚠ 用 `extendReg64` 必须用**新 base 的低位**；`type` 保持不变（a 只换来源、不换 extend）。
- **期望值示例（W0 0x4005d8 `ldr x0,[x1,x0,lsl #3]`，base=x1=`&data[0]`=0x4919a0，index=x0=k）**：old = 0x4919a0 + 8k；new = k + (0x4919a0<<3) = k + 0x248CD00 ⇒ **远超对象/多为未映射 ⇒ Crash 通道（guest SEGV）**，不是 in-object SDC。这是 A05-a 的诚实预期（A05 规格无"同对象"约束）。
- **记录字段**：`old_base, old_index, new_base, new_index, base_reg, index_reg, extend, shift, old_ea, new_ea`。

### 3.3 A05-b：SXTW↔UXTW 互换

- **适用形态**：只有 **W-index** 的 register-offset（`option=010 UXTW` 或 `110 SXTW`；`arch/arm/types.hh:226,230`）。X-index 的 `UXTX/SXTX`（`LSL` 形式）互换在 64 位下**恒等** ⇒ ineligible。
- **可见性前置**：`bits(index_val,31) == 0` 时 UXTW 与 SXTW **同值** ⇒ no-op（必须计 no_effect，不注入）。`bit31==1` 时二者相差 `2^32`。
- **新值计算**：仅替换 `type ∈ {UXTW,SXTW}`，base/index/shift 不变：
```cpp
new_type = (type == UXTW) ? SXTW : UXTW;
new_EA   = base_val + extendReg64(index_val, new_type, shift, 64);
```
- **结构性后果（必须如实报告）**：`±2^32` 的 EA 偏移在现代 SE 进程映像（0x400000 起）上几乎必然落到未映射区 ⇒ **A05-b 的可见结局只有 Crash/翻译阻断**，不可能产生 in-object SDC。若策略要求"故障后仍属同一对象"，A05-b 应判 **structurally ineligible**（不烧预算）。
- **micro-test**：`w4 = 0x80000010; ldr x3,[x0,w4,uxtw]`：old EA = `obj+0x10`（in-object，可达）；new（SXTW）= `obj − 0x7FFFFFF0` ⇒ 未映射 ⇒ 期望 guest SEGV / `crash_translation_blocked`。反向（原 SXTW）无法构造正确 EA，故只测 UXTW→SXTW。
- **记录字段**：`old_type, new_type, index_val, bit31, old_ea, new_ea, outcome(crash/sdc/no_effect)`。

### 3.4 A05-c：shift 量改为另一合法值

- **合法集合**：AArch64 register-offset 的 `S` 位只有两种取值：`shift = 0` 或 `shift = log2(access_size)`。因此"另一合法值"对给定指令是**唯一**的：`shift' = (shift ? 0 : log2(size))`。`size==1`（byte）⇒ `{0}` 单元素 ⇒ ineligible。
- **真实重算**（不是低字节旋转）：
```cpp
new_shift = old_shift ? 0 : (uint64_t)log2(size);
new_EA    = base_val + extendReg64(index_val, type, new_shift, 64);
```
- **ineligible / no-effect**：`size==1`；`index_val==0`（移位无效）；`new_EA==old_EA`；非标量形态。
- **micro-test（W0 有两条互补形态，最佳载体）**：
  - `ldr x0,[x1,x0,lsl #3]`（0x4005d8，S=1，k 循环）：old = `data+8k`；new（shift=0）= `data+k` ⇒ 同为对象内不同元素 ⇒ 期望 **SDC**（校验和改变）或（若 k 使 new 落回同一值）no_effect。
  - `ldr x2,[x20,x1]`（0x4006b8，S=0）：old = `data+off`；new（shift=3）= `data+8*off` ⇒ 可能越出对象 ⇒ SDC 或 Crash。
- **记录字段**：`old_shift, new_shift, size, index_val, old_ea, new_ea`。

### 3.5 A05-d：pre-index ↔ post-index（含写回时机/写回值）

- **适用形态**：仅预/后变址的**立即数**写回形态（`MemoryPreIndex64`/`MemoryPostIndex64`）；`LDP/STP` 的 pre/post 走 macromem（`stp x29,x30,[sp,#-32]!`），**本轮 ineligible**（除非另加 macromem 钩子）。
- **真实语义与可表达边界（关键）**：
  - 架构上 pre: `EA = Xn + imm; Xn = EA`；post: `EA = Xn; Xn = Xn + imm`。两者**写回值相同**（`Xn+imm`），差别在 EA。
  - gem5 的实现：acc microop 算 EA，写回是**最后一个 uop**（`MicroAddXiUop`，`templates/mem.isa:1006-1050`），**pre 与 post 都是"访问之后"写回** ⇒ 本微架构**不建模"写回时机"差异**。
  - 因此 A05-d 的**忠实且唯一的可观测面**是 **EA 的变址模式反转**；只改 EA 就能同时得到"另一模式的 EA + 相同的最终基址"，与架构语义完全一致。
- **新值计算**：
```cpp
// pre 指令（默认 EA = Xn + imm）→ 变址反转：new_EA = Xn
// post 指令（默认 EA = Xn）      → 变址反转：new_EA = Xn + imm
// 写回 microop 不动：Xn ← Xn + imm（两模式相同，正是"另一模式"的正确最终值）
```
- **ineligible**：`imm == 0`（EA 不变）；非 MemoryPre/PostIndex64 形态（含 LDP/STP）；`new_EA == old_EA`。
- **micro-test（W3 现成）**：
  - pre `ldr x1,[x2,#8]!`（0x400604）：old EA = `array+8`，new（post 化）= `array`；写回 `x2 = array+8`（不变）。期望 old/new 之差恰为 `+8`，读到相邻元素 ⇒ 若无错误检测则 Masked、若后续用 x2 则可能 SDC。
  - post `ldr x1,[x2],#8`（0x400558）：old EA = `array`，new（pre 化）= `array+8`，写回 `x2 = array+8`（不变）。
  - 负立即数 `strb w2,[x3],#-1`（0x400710）：old EA = `p`，new = `p-1` ⇒ 明显的相邻字节 SDC。
- **记录字段**：`wb_mode(old: pre|post), old_imm, old_ea, new_ea, base_reg, base_val, wb_value(=base+imm，两模式同), ea_delta`。
- **诚实标注**：`writeback_time_modeled=false`（本模型两模式写回都在访问后，无时序差可改）；若工作令要求"仅改更新时点"，则必须回答：**该差异在本微架构不可观测** ⇒ A05-d 只能按"EA 侧变址模式反转"实现，或判 NOT_MODELABLE（不得用"改写回值"冒充）。

### 3.6 实现风险裁决：改写 arch 寄存器值 vs 仅改发往 LSQ 的 Request

**结论：只能"仅改发往 LSQ 的东西"，即只改 EA；绝不能改写 arch 寄存器值。**

理由（源码事实）：
1. O3 的读操作数走**物理寄存器**：`DynInst::getRegOperand(si, idx)` → `renamedSrcIdx(idx)` → `cpu->getReg(physReg)`（`dyn_inst.hh:1214-1220`）。ISA 代码里的 `xc->getRegOperand` 就是这个。改写"arch 寄存器"没有对应落点。
2. O3 的写操作数走**目的物理寄存器**：`DynInst::setRegOperand` → `renamedDestIdx(idx)`（`dyn_inst.hh:1241-1258`）。它是**目的**通道，用它去写 base/index（源）会落到错误槽位；即使槽位巧合，也是直接写 PRF，绕过 rename 的依赖跟踪，且会被 commit 的寄存器映射/检查器（`cpu->checker`）判为不一致，破坏rename/commit 语义。
3. 用 `xc->setRegOperand` 在 execute 阶段临时改源、再恢复，会污染**同一物理寄存器**的并发消费者（OoO 下多条指令共享 phys reg，读端口无独占），属于不可控副作用。
4. 正确做法是在 **EA 表达式之前**用局部变量替换操作数（设计 A），只让**推导出的 EA** 进入 `initiateMemAcc` → `pushRequest`；下游 `inst->effAddr = request->getVaddr()`（`lsq.cc:939`）、DTLB、cache 全部看到故障 EA，而 base/index 的物理寄存器、依赖链、commit 语义完全不变。
5. 对 A05-d，写回 microop 用**自己的** imm/type 计算（`MicroAddXiUop` 持有 `imm`），与 acc microop 的 EA 互不影响——这正是"只改 EA 不改写回"能精确实现变址反转的根据。

**注意**：若误用"读 `inst->srcRegIdx` 再 `cpu->setReg`"这类写法，会同时破坏 rename 与 checker，属于本模型禁止的实现路径。

---

## 4. 文件所有权建议

### 4.1 需修改文件（按 owner 分组）

| # | 文件 | 改动 | 共享对象 | 建议 owner |
|---|---|---|---|---|
| F1 | `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.{cc,hh,py}` | 新 preMode、对象表、操作数回调、证据、summary、no-op 守卫 | **A01/A02/A03/A04/A06/A07/A08 + S*/L*** 共用 | **A 家族唯一实现 owner**（串行） |
| F2 | `CHAOS/gem5/src/cpu/o3/lsq.cc` | （仅当设计 B）PRE 钩子签名扩展；否则不改 | 全部 LSU + A06 carrier | 共享单一 owner |
| F3 | `CHAOS/gem5/src/arch/arm/isa/insts/ldr64.isa`, `str64.isa` | `buildEACode()` 生成操作数钩子（设计 A） | 语义上只服务 A05；**但重生成整个 ARM** | A05 owner（唯一） |
| F4 | **新** `CHAOS/gem5/src/arch/arm/insts/chaos_agu_operands.{hh,cc}` + `SConscript` | 钩子注册表 + `extendReg64` 复用 + no-op 判定 | 无（新文件） | A05 owner |
| F5 | `CHAOS/gem5/src/arch/arm/insts/mem64.hh` | （仅设计 B）`baseReg()/indexReg()/type()/shift()` 访问器 | 无（A64 内存类） | A05 owner |
| F6 | `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{cc,hh}` | `registerOperandInjection` / 对象字段 / inj 节点 detail | **全部单元**共用 | 共享单一 owner |
| F7 | `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh` | 一般无需改（复用 onAttempt/onEligible/noteOutcome）；若新增事件源则改 | 全部 LSU | 共享单一 owner |
| F8 | `configs/se/lsu_proxy.py` | 新 CLI（`--agu_object_spec`、`--agu_operand_mode`、choices/validation） | 全部模型 | 共享单一 owner |
| F9 | `tools/lsu_campaign.py` | `MODEL_FLAGS["A04"/"A05"]`、`ADDRPATH_F0_SPAN`（新载体 census）、`MODEL_BLOCKED` | 全部单元 | 共享单一 owner |
| F10 | `tools/lsu_runid_map.py` | `SPEC_IMPL_LANDED`（A04/A05）、status/blocker | 全部单元 | 文档 owner（主 agent 协调） |
| F11 | `tools/lsu_prop_fields.py`、`tools/lsu_chain_check.py` | 新证据字段校验/L5 判定（不新增 L5 语义） | 全部单元 | 共享单一 owner |
| F12 | **新** `workloads/directed/agu_operand_modes.c`（+ 二进制 + golden） | A05 a/b/c 的定向 micro-test 载体（asm 显式形态） | A05/A07?（若复用） | 负载 owner（A05） |
| F13 | `workloads/directed/agu_addrmodes.c`（+ 二进制） | **仅当裁决为 (i) 重建 W3**；golden 变，必须重验 | A01/A02/A03/A04/A05/A06/A07/A08 共用 W3 | 负载 owner + 主 agent 批准 |
| F14 | `tests/test_lsu_hook_addrpath*.py`、`tests/test_lsu_a04*.py` | 对象登记/操作数契约回归 | 共享 | 共享单一 owner |
| F15 | `docs/gem5-fi/lsu/mdspec/*`、XLSX、状态表 | 状态/裁决回填 | 全仓 | 主 agent |

### 4.2 串行纪律（必须写进计划）

- **F1/F6/F7/F8/F9/F11** 是所有 A 单元（以及 S/L）交叉点：**同一时刻只允许一个 owner 改**；A05 owner 必须先等 A04 owner 完成 F1 的对象表分支，再在同一文件追加操作数分支（或由 F1 单一 owner 一次性实现两者）。
- **F3/F4/F5** 只服务 A05，可独立；但 F3 触发**全 ARM 重新生成**，必须与所有依赖生成产物的验证批次错开（构建窗口独占）。
- **F13 变 golden** ⇒ 影响 A01–A08 全部 W3 RunID 历史可比性：**必须主 agent/工作令批准**，且新 golden 需 8 对 golden 流 census 重测（`ADDRPATH_F0_SPAN` 全部重算）。
- **F12 新载体** 不改任何既有 RunID 的 golden，风险最低，建议优先。

---

## 5. 风险清单（点名拒绝的"看似实现、实际只改结果"代理路径）

| ID | 被拒绝的路径 | 为何是代理 / 危害 | 正确做法 |
|---|---|---|---|
| R1 | 继续用 `a05_shift` 低字节旋转（`CHAOSAddrPath.cc:626-632`）当作 A05-c | 不读 shift 操作数、不重算 EA、对 base+imm 指令也生效、可 no-op 却计 injected（F-049） | 设计 A 的真实 shift 改写 + 重算 + no-op 守卫 |
| R2 | 在生成代码里**原地改** `type/shiftAmt` 成员 | StaticInst 跨动态实例共享 ⇒ 污染后续所有同类指令，故障"泄漏"到无关指令 | 复制到局部 `_ct/_cs` 再改 |
| R3 | 每次 `executeLoad/Store` 重掷随机决策 | 翻译延迟会二次进入（`iew.cc:1239-1245`）⇒ 故障静默消失或双计 | 按 `dyn_inst_seq` 缓存并幂等重放 |
| R4 | 在 O3 侧 arm、ISA 侧消费，但只在 `iew.cc:1215` 布点 | `chaosAguResumeInst` 复制了整段分发（`iew.cc:1404-1453`）⇒ resume 路径漏注入 | 全部逻辑放进 ISA 钩子（自动覆盖两条路径）；若两点设计，两处都要布 |
| R5 | 用 `xc->setRegOperand`/`cpu->setReg` 改 base/index | 写的是**目的** phys reg（`dyn_inst.hh:1241`），破坏 rename/commit/checker | 只改 EA（§3.6） |
| R6 | A04-a 无对象表时退回 `a04_subst` 同页 16B | 旧 pilot 实证：注入地址 0x48e870 属 glibc 数据段、非 `array`(0x493000)（DIAG-B §4.1） | 未登记即 fatal；`a04_subst` 设废弃别名 |
| R7 | 用 `m5 addsymbol` 做 SE 对象登记 | `SEWorkload::insertSymbol` 在 SE `panic`（`sim/se_workload.hh:76-82`）；且只带地址不带 size/elem_width | `Process::objFile->symtab()`（§2.2） |
| R8 | 按名字登记 W0 的 `data` | 两条同名 LOCAL（0x4919a0/512、0x496e80/8），`SymbolTable::insert` 静默丢后者 ⇒ 结果不确定 | 显式 `addr+size`，或重命名 symbol 后重编 |
| R9 | 把 SIMD `ldr q,[xN,xM]` 当作 A05-a/b/c 已覆盖 | 走 `MicroNeonMemOp`（EA=`XURa+imm`，地址由独立 microop 预算），标量钩子不覆盖；且范围未裁决 | 明确 ineligible，或裁决范围后另加 NEON 钩子 |
| R10 | A05-b "互换"后仍报 injected 而不区分可见性 | `bit31(index)==0` 时 UXTW≡SXTW（no-op）；`bit31==1` 时偏移 ±2^32 ⇒ 只会 Crash | 前置可见性判定 + no_effect 计数；按策略判 ineligible |
| R11 | A05-a 在 shift==0 上注入 | 加法可交换 ⇒ EA 恒不变（no-op） | `shift != 0` 才 eligible |
| R12 | A05-d "改写回值/丢写回"来模拟"更新时点" | 写回值两模式相同；改值＝换语义（越界到 A07-c 领域），且"时机"在本微架构不可观测 | 只做 EA 侧变址反转，并标注 `writeback_time_modeled=false` |
| R13 | 把 A04-b 的对齐固定成 16B（现状） | 与访问宽度无关，`ldrb` 也可能被换成跨元素地址，且"同页合法"未按访问宽度校验 | 按 `size` 对齐；`target+size<=page_end` |
| R14 | 以"注入日志里有 old/new"作为 activated 证据 | A05-a/b/c 的新旧 EA 可能落在未映射区 ⇒ 只有 Crash 通道；不得据此声称 SDC | 三源证据（inj log + CHAOS_LSU_TRIGGER + chain_report）+ 不对 no_effect/crash 混算 |
| R15 | 在对象表里使用 host 端 `nm` 输出硬编码地址 | SE 地址随 ELF 布局；FS/host 不同 | 运行时从目标 ELF 的 `objFile->symtab()` 解析 |

---

## 6. 可执行验证设计（本轮不运行；供实现 owner 照做）

1. **构建**：`cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt`（改 ISA 生成文件后的全量 ARM 重生成；期望 0 warning/0 error）。
2. **A04-a 定向**（新载体或 W3）：
   `build/ARM/gem5.opt --outdir=/tmp/a04a configs/se/lsu_proxy.py --cmd workloads/directed/agu_addrmodes --cpu O3 --chaos_addrpath --agu_pre_mode a04_same_object --agu_object_spec arr:array:512:8:8 --addrpath_lsu_tier F0 --addrpath_rng_seed 1`
   期望：`addrpath_injections.log` 中 `old_addr`/`new_addr` 均 ∈ `[0x493000,0x493200)`，`source_offset != target_offset`、`target_offset % 8 == 0`；启动行 `CHAOS_AGU_OBJECTS` 打印 base/size/elem。
3. **A04-a 负例**：`--agu_object_spec arr:nosuch_symbol:512:8` ⇒ **启动即 fatal**（不得跑完）。
4. **A05-d 定向**：`--agu_operand_mode a05d_prepost`，注入日志应出现 `wb_mode=pre|post, old_ea, new_ea(=old∓imm), wb_value`，且 `delta==±imm`；`ldr x1,[x2,#8]!` 的 old/new 差必须恰为 0x8。
5. **A05-c 定向（W0）**：`--cmd workloads/directed/mini_check --agu_operand_mode a05c_shift`，PC 应命中 0x4005d8/0x4006b8，`old_shift==3→0`（或反向），EA 差 = `(8^k - k)` 级别，oracle 校验和变化 = SDC。
6. **no-op 回归**：构造 `index==0` 的 shift 用例 ⇒ `no_effect` 计数 +1、`injected` 不变（F-049 纪律）。
7. **不受影响回归**：`reg_chain` golden 不变、零 SIGSEGV（Patch discipline 要求）。

---

## 7. UNKNOWN / 边界

- 未构建、未运行；所有"期望值"均由指令编码 + 源码语义推导，**不是实测**。W3/W0 的地址（0x493000/0x4919a0）来自当前二进制 `readelf`，会随重新编译变化。
- SIMD register-offset（`ldr q,[xN,xM]`）的 microop 地址预算细节未逐行定位（`XURa` 的构造处未展开）；本报告只确认其 EA 是 `XURa + imm`（`neon64_mem.isa:57-59`），据此判定标量钩子不覆盖。
- A05-b 的"必然 Crash"是基于 SE 映像布局（image 自 0x400000）的推断，未实测；若 SE 映射跨 4GiB 则可能命中其它已映射区（需实测确认）。
- FS（`kp920_proxy_fs`）无 SE `Process` ⇒ 本报告的 A04-a 登记机制不适用；FS 侧需要独立裁决（不使用 host 符号表）。
