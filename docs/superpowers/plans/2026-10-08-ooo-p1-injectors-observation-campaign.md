# OOO P1：57 模型注入器 + L0–L5 观测链 + Campaign 引擎 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 关闭 G0-02（57 模型唯一实现映射 + 确定性测试），交付 P3 pilot 所需的全部注入工作面、观测链与 campaign 引擎。

**Architecture:** 以 e3217105 审计（已实现 9 / 部分 34 / 未实现 14）为工作清单，按故障家族逐单元补齐 vendored gem5 树（`CHAOS/gem5/src/`）中的注入器子模式；观测链（L0–L5 + 守恒）收敛到 `tools/classify.py` 唯一口径；campaign 引擎（`tools/ooo_campaign.py`）串联 manifest/seed/guard/recover 全链。每单元一提交，提交前 100% 实测。

**Tech Stack:** gem5 v25.1.0.1 vendored（C++ 注入器四件套 .hh/.cc/.py/SConscript）· Python 3.9（tools/）· 兼容运行时（F-008：`lsu_keeper/compat` loader + PYTHONHOME）· ooo_guard 4 槽 · ooo_recover。

**Spec:** `docs/gem5-fi/ooo/03-design-matrix.md` + `09-v2-coverage-audit.md` + `d-bridge-v1-v2.csv`（U0 入库后为本计划权威规格）× `docs/gem5-fi/ooo/总方针.md` §5/§6/§8.2 × `task_plan.md` P1 七项检查单。

## Global Constraints（每单元隐含遵守）

- gem5 C++ 增量编译：`scons -j8` + flock 单实例（`tools/ooo_guard.py run --type build` 包裹），仓根 `build/ARM/gem5.opt`（经 `CHAOS/gem5/build/ARM → ../../../build/ARM` 符号链接）。
- gem5 运行双轨（U1c 落地后生效，此前维持 compat 单轨）：sdc 构建（sha 63f50c40…，`build/ARM/gem5.opt.sdc-py311`）一律经兼容 loader（`C=/home/share/suke/wangxu/lsu_keeper/compat; PYTHONHOME=$C $C/lib/ld-linux-aarch64.so.1 --library-path $C/lib64:/usr/lib64 build/ARM/gem5.opt.sdc-py311 ...`）；login01 原生 py3.9 重建产物（U1c 后一切增量构建）**原生直跑，禁止套 compat loader/PYTHONHOME**（3.9 二进制错配 3.11 stdlib 必炸，见 F-011）。
- 触发语义只用 `src/cpu/o3/chaos_trigger.hh`（F0–F5）；`lastClock=0`（不受限）；`maxFaults` 控数；`rngSeed` 复现。
- ARM64：整数寄存器 index ≥32 为 banked（31=XZR 排除）；NEON/向量寄存器故障掩码必须 64 位。
- 新组件全链接线：注入器四件套 → `configs/se/ooo_proxy.py` 挂载 flag → `tools/runner.py` dispatch → `schemas/manifest.schema.json` 枚举 → `tools/manifest_validate.py`。未全链接线 = 拒绝，不半路由。
- 诚实：近似/BLOCKED-no-hook 显式三态记录（实现/近似/BLOCKED），不静默打勾。
- 提交格式 `[OOO][P1][U<n>] ...`，bundle 通道推送（远程移动先分析再 rebase）；`git add` 显式路径，禁 `git add -A`。
- P2 归属（本计划不做但被引用）：W1 构建（DR-001 方案A，tarball 已上传 sha256 7bc51c7d…）、W3/W8/W9/W13 探针负载开发、golden ≥3 次复验——家族单元的探针深验证在 P2 补。

## 现状基线（审计数字，勿重算）

- 已实现(9): D01 FD01 FD03 FR01 FR05 FR07 R01 R05 R07；未实现(14): B08 B09 D06 D07 D09 FB06 FB08 FB09 FD05 FD07 FD09 FR08 FR09 R08；部分(34)。
- 模式面：`configs/se/ooo_proxy.py`（835 行）已挂 17 个 CHAOS SimObject（含 CHAOSCommitTrace/CHAOSMicroSnap），参数面与 arm_chaos.py 同构。
- 基建：`tools/ooo_guard.py`（4 槽，F-022 口径）、`tools/ooo_recover.py`（原子 COMPLETE + 五态扫描）。
- 参考 golden（workloads/ooo/README.md 台账）：smoke=45737cc9a76c0dce、dep_chain int=98e5e31e726e383f、rob_fill int=19eab7d0de27237e。

---

### Task U0：设计文档桥接（规格入库）

**Files:**
- Create: `docs/gem5-fi/ooo/03-design-matrix.md`（自 e3217105）
- Create: `docs/gem5-fi/ooo/09-v2-coverage-audit.md`（自 e3217105）
- Create: `docs/gem5-fi/ooo/d-bridge-v1-v2.csv`（自 e3217105）
- Modify: `docs/gem5-fi/ooo/findings.md`（溯源注记）

**Interfaces:**
- Produces: 后续所有单元的权威规格文件（03 表=57 模型逐条定义；09 表=工作面缺口清单；d-bridge=v1→v2 血统 116 行）。

- [x] **Step 1:** 从共享对象库取三文件（worktree 与主树同库）：
```bash
cd /home/share/suke/wangxu/gem5-fi-ooo
git show e3217105:docs/gem5-fi/ooo/03-design-matrix.md > docs/gem5-fi/ooo/03-design-matrix.md
git show e3217105:docs/gem5-fi/ooo/09-v2-coverage-audit.md > docs/gem5-fi/ooo/09-v2-coverage-audit.md
git show e3217105:docs/gem5-fi/ooo/d-bridge-v1-v2.csv > docs/gem5-fi/ooo/d-bridge-v1-v2.csv
```
- [x] **Step 2:** 完整性断言（行数与来源 commit 记录进 findings）——实测：03=158 行/09=98 行/d-bridge=117 行（116 数据行 ✓）。：
```bash
wc -l docs/gem5-fi/ooo/03-design-matrix.md docs/gem5-fi/ooo/09-v2-coverage-audit.md docs/gem5-fi/ooo/d-bridge-v1-v2.csv
grep -c "已实现\|未实现\|部分" docs/gem5-fi/ooo/09-v2-coverage-audit.md   # 预期 >0（审计状态行）
tail -1 docs/gem5-fi/ooo/d-bridge-v1-v2.csv                                # 预期 116 行数据的最后一行
```
- [x] **Step 3:** findings.md 环境表加一行"设计规格"（来源 e3217105、桥接日期、哈希），并注明与本工作树 HEAD 的差异仅为 P0 三提交（3b7a0854/ce8d6d8a/362e01c3，不触 docs/gem5-fi/ooo 设计文件）。
- [x] **Step 4:** 提交 `[OOO][P1][U0] 设计文档桥接：03-design-matrix/09-audit/d-bridge 入库（源 e3217105）`。——实测：commit bde8ee94（原 31c1494c，2026-10-08 11:32:17 +0800 原始提交；因 LSU 连续前进 3671113c/127b54a3/72278a27 两次重放，均文件零差异），含三文件 + findings 设计规格行。

### Task U1：`tools/ooo_models.py` 机读映射表

**Files:**
- Create: `tools/ooo_models.py`
- Test: 内置 `--check` 自校验模式（无独立测试文件，表驱动）

**Interfaces:**
- Consumes: U0 的 03 表 + `docs/gem5-fi/ooo/完整任务执行清单.md`（310 ITEM）。
- Produces: `MODELS: dict[model_id -> {unit, excel_row, fault_type, freqs, workloads, n_submodels, impl_status, injector, mount_flag, submodels: [letters]}]`（**2026-10-08 修订**：unit 即 family——03 表唯一分类轴；submodels 为字母表+数量断言——03 详表子模型列是自由文本「FD01-a opcode字段单bit；…」，不存在结构化 field/mode 列，结构化详情由 U2–U8 实现单元直接读 03 详表；excel_row/freqs/workloads 为 U11 manifest 必需元数据）；CLI `python3 tools/ooo_models.py --check`（校验 310 ITEM 模型引用全命中 + 57 模型全覆盖 + 头行无静默跳过 + 编号连续 001..310）与 `--item ITEM-xxx`（打印单项映射，也接受模型 ID）。U11 campaign 引擎 import 此表生成 manifest 的 model 元数据。

- [x] **Step 1:** 写 `tools/ooo_models.py`：57 模型静态表（数据从 03 表转录，impl_status 三态 initial 从 09 审计抄录），`--check` 模式解析完整任务执行清单.md 的 ITEM 头（`### ITEM-xxx — <model>-<freq>-W<n>`）并交叉校验。——实测：896 行；静态表由 03/09 重解析生成后逐字段核对；--check 五组校验（索引字段/审计判定/子模型字母/注入器布线/清单 ITEM 交叉）。
- [x] **Step 2:** 运行校验，预期输出：
```
$ python3 tools/ooo_models.py --check
models: 57 | items_scanned: 310 | item_refs_resolved: 310 | unresolved: 0
impl_status: implemented=9 partial=34 unimplemented=14
```
实测一致（exit=0），另输出 `OK: 静态表 ↔ 03 索引/详表 ↔ 09 逐模型判定 ↔ 清单 ITEM 三方一致`。
- [x] **Step 3:** 边界自测：临时把一个 ITEM 引用改成不存在的模型（sed 备份/还原），确认 `--check` 报 unresolved>0 且 exit≠0（防"永远通过"假校验）。——实测（/tmp 副本，hash 锁定原件不动）：T1 头格式损坏（D01→DX1）首跑暴露**静默跳过缺陷**（items_scanned=309 仍 OK）→ 修复加「头行全解析/条目数=310/编号连续 001..310」三断言 → 复测 T1 exit=1（`清单条目数 309 != 预期 310`）；T2 审计注入器损坏 exit=1；T3 索引 freqs 损坏 exit=1；T4 未知模型 D91 exit=1 unresolved=1；T5 原件复验 exit=0 且清单 sha256 f520d42a…30c91 前后不变。
- [x] **Step 4:** 提交 `[OOO][P1][U1] tools/ooo_models.py 57 模型机读映射 + 310 ITEM 交叉校验`。

### Task U1b：`ooo_guard.py` guard_pid 竞态移植（F-025）

**Files:**
- Modify: `tools/ooo_guard.py`（cmd_run 锁结构 + 陈旧判定/release 确认/clear-stale 判活）
- Test: `tools/tests/test_ooo_guard_f025.py`（独立脚本，不经 pytest）

**Interfaces:**
- Consumes: LSU 轨道 6d1662ee 的修复语义（guard_pid = run 进程 pid，存活至 run 结束；pid 字段 spawn 后被覆盖为 gem5 子进程 pid 仅作 TRIP 定位）。
- Produces: 锁 JSON 新增 `guard_pid` 字段；判活函数 `_lock_owner_pid(lock) -> int`（有 guard_pid 用之，老格式回退 pid）。

**背景（必须先读）:** F-025 事故——cmd_run spawn 后锁内 `pid` 更新为 gem5 子进程 pid；gem5 正常退出→release 间有 0-60s（monitor 60s 采样延迟）死 pid 窗口；并发 gate 按 pid 判活 → 把正常收尾中的槽误判为泄漏槽 → GATE BLOCKED。4 并发下每槽 ~30s 假陈旧暴露/轮转，LSU 波次 4 于 26 分钟内两次 fail-fast。`tools/ooo_guard.py`（自 lsu_guard@f0a5b249 适配）同病：`lock["pid"], lock["pgid"], lock["cmd"] = proc.pid, ...`（cmd_run 内）+ 判活走 `lock.get("pid")`。参考实现：`git show 6d1662ee -- tools/lsu_guard.py`。

- [x] **Step 1:** 写失败测试 `tools/tests/test_ooo_guard_f025.py`：构造锁文件 A{guard_pid: 死pid, pid: 死pid}（老格式→判陈旧，预期 stale=True）与 B{guard_pid: 本进程pid, pid: 死pid}（新格式正常收尾窗口→预期 stale=False），断言 `_lock_owner_pid` 回退语义与判活结果。——实测：12 检查点（T1a-d 回退语义 / T2 判活 / T3 收尾窗口不误报 / T4 真泄漏拒入 / T5a-b release 确认 / T6a-c clear-stale 双字段+存活拒清）。
- [x] **Step 2:** 运行确认失败：`python3 tools/tests/test_ooo_guard_f025.py` → FAIL（`_lock_owner_pid` 不存在）。——实测：`AttributeError: module 'ooo_guard' has no attribute '_lock_owner_pid'` exit=1（红态证据）。
- [x] **Step 3:** 移植修复：cmd_run acquire 时写 `guard_pid: os.getpid()`；spawn 覆盖仅 `pid/pgid/cmd`；`_lock_owner_pid(lock)` helper；陈旧判定、release confirm、clear-stale 判活全部改走 `_lock_owner_pid`。——实测：11 处替换（_slot_holders/_gate_result/_try_acquire 字段+判活+拒因文案/_release/clear-stale 双分支判活+双字段接受+文案/cmd_run finally confirm=os.getpid()），py_compile CLEAN。
- [x] **Step 4:** 运行测试通过：`python3 tools/tests/test_ooo_guard_f025.py` → PASS。——实测：`SELFTEST PASS (12 checks, 0 failed)` exit=0（含 T4 拒因原文 `guard_pid=999001 已退出但未记录处置`、T5b `confirm-pid 999001 与锁内 guard_pid <本进程> 不符`）。
- [x] **Step 5:** 回归：隔离 GUARD_DIR 下重跑 T1–T6 精简版（gate/acquire/release/status/clear-stale/run 快命令），输出与 Unit1 记录一致。——实测（OOO_GUARD_DIR=/tmp/ooo-guard-reg）：R1 空态 4 槽 null；R2 acquire 入 slot 0 且锁含 guard_pid；R3 status 持有；R4 错 confirm REFUSED（guard_pid 不符）；R5 正确 confirm RELEASED；R6 陈旧 A 锁 acquire REFUSED（guard_pid=999003）；R7a 错 pid NOTE 未处置→R7b 对 pid CLEARED→re-acquire 成功→释放；R8 gate ok=false 仅因 LSU CP4 重建编译进程在跑（正确阻断，同 P0 Unit1 原始观察；MemAvailable 303.5GiB、无陈旧槽误报、slots 0/4）。**run 快命令无法当跑**（gate 正确阻断）——cmd_run 释放路径变更（confirm=os.getpid()）已由 T5a/b 单元级覆盖（即 cmd_run finally 的同一 _release 调用），全路径 E2E 待 login01 无编译进程时复验（U2 构建守卫周期必然复跑该路径）。
- [x] **Step 6:** 提交 `[OOO][P1][U1b] ooo_guard guard_pid 竞态移植（F-025，对齐 LSU 6d1662ee）`。

### Task U1c：login01 原生 py3.9 构建平台复活（F-008 修订；U2–U9 前置门）

**Files:**
- Modify: `CHAOS/gem5/src/python/gem5/simulate/simulator.py`（仅 1 行：line 104 `Optional[str | Path]` → `Optional[Union[str, Path]]`；`Union` 已在 line 38 导入）
- Modify: `docs/gem5-fi/ooo/findings.md`（新增 F-011；F-008 修订注记）
- Modify: `docs/gem5-fi/ooo/progress.md`（Session 004）
- Test: 静态三重探针（全树 AST 注解位扫描 / py3.9 compile / PYTHONVERBOSE import 审计）+ 实机四 golden 原生两态

**Interfaces:**
- Consumes: F-008 证物 `build/ARM/gem5.opt.login01-py39-broken`（G0-01 clean build，src 与 sdc 构建逐字节一致）；PYTHONVERBOSE 探针 `/tmp/pyv.err`（sdc+compat 实跑 RC=0 FINAL=45737cc9a76c0dce，104 个 stdlib 文件来源全清单）。
- Produces: login01 原生 py3.9 `build/ARM/gem5.opt`（shim 后）原生直跑 stdlib board 配置；`build/ARM/gem5.opt.sdc-py311`（sdc 证物硬链接保全）；U2–U9 全部 C++ 单元的构建平台（改码→guard 增量重建→原生直跑）。

**背景（必须先读）:** F-008 判「任何 login01 原生构建对 stdlib board 配置结构性不可用」，实证失败点仅 `simulator.py:104` 签名注解 PEP 604（def 时求值）。2026-10-08 全树量化（AST 扫描 + PYTHONVERBOSE 实测）：①244 文件（src/python/gem5 + m5 + configs）py3.9 语法零违例；②AST 注解位 PEP 604 全树（含 build/ARM/python 生成件）= **恰 1 站点 1 文件**（simulator.py:104）；③运行时 3.10+ API（with_stem/hardlink_to/zip strict/TypeAlias/slots=True/isinstance-|）全树零命中；④import 链 104 个 stdlib 模块在系统 py3.9 全部可解析（re/importlib.resources 系 3.9↔3.11 布局差异、解释器内部自理；importlib._abc 为 3.11 stdlib 内部依赖、gem5 代码零直接引用；零 C 扩展模块依赖）。DT_NEEDED 文件名欺骗已证死路（F-011：getpath 按编译期版本号推 sys.path=lib64/python3.9/*，compat 无此树 → encodings 缺失 → RC=134 SIGABRT）。

- [x] **Step 1:** findings.md 落 F-011（pylie 负结果：根因 sys.path 版本推导 + 证据 /tmp/pylie-smoke.log）。——实测：F-011 行已插（F-010 后），含 sys.path 三行推导 + encodings 缺失 + RC=134 全链。
- [x] **Step 2:** 打补丁：simulator.py line 104 `outdir: Optional[str | Path] = None` → `outdir: Optional[Union[str, Path]] = None`（等价改写、注解仍求值、语义不变；Union 已导入）。——实测：grep 确认 line 104 已为 Union 形。
- [x] **Step 3:** 静态复验：全树 AST 注解位扫描 = 0 站点；patched simulator.py py3.9 compile CLEAN。——实测：4 根（src/python/gem5、src/python/m5、configs、build/ARM/python）注解位 total=0、SyntaxError=0，STEP3: PASS。
- [x] **Step 4:** 保全 sdc 证物（rebuild 覆写 gem5.opt 前必做）：`ln build/ARM/gem5.opt build/ARM/gem5.opt.sdc-py311`（同 inode 加一链接）。——实测：ls -li 双文件同 inode 135108174027414400。
- [x] **Step 5:** 等 LSU CP4 scons（pid 3323664，-T 14400）退出且 gate 无编译进程后，guard 包裹增量重建：`python3 tools/ooo_guard.py run --type build --desc u1c-shim-rebuild --log /tmp/u1c-build.log -- bash -c 'cd CHAOS/gem5 && scons -j8 build/ARM/gem5.opt'` → 预期 `scons: done`（引用尾行）。——实测：LSU CP4 12:37:40 完成后 12:51:36 启动（guard 4037686 / scons 4037691，python3 绝对路径 scons -j8）；末次心跳 13:41:49 elapsed_s=3012.7 warning=false trip=null；产物 build/ARM/gem5.opt 1,227,788,056B @ 13:40；build_lock 释放（guard status 实测 null）。env 切换 compat-py311→native-py39 触发全量重链，全程 50 分钟。
- [ ] **Step 6:** 原生两态 × 四 golden（系统 py3.9 直跑，无 loader/无 PYTHONHOME）：
```bash
cd /home/share/suke/wangxu/gem5-fi-ooo
build/ARM/gem5.opt --outdir=/tmp/u1c-s1 configs/se/ooo_proxy.py --cmd workloads/ooo/smoke/smoke --cpu O3        # FINAL=45737cc9a76c0dce（s2 复跑逐字节一致）
build/ARM/gem5.opt --outdir=/tmp/u1c-di configs/se/ooo_proxy.py --cmd workloads/ooo/dep_chain/dep_chain --cpu O3   # FINAL=98e5e31e726e383f
build/ARM/gem5.opt --outdir=/tmp/u1c-dv configs/se/ooo_proxy.py --cmd workloads/ooo/dep_chain/dep_chain_vec --cpu O3 # FINAL=b1e661a247b95774
build/ARM/gem5.opt --outdir=/tmp/u1c-rf configs/se/ooo_proxy.py --cmd workloads/ooo/rob_fill/rob_fill --cpu O3     # FINAL=19eab7d0de27237e
```
  回归对照：同四命令以 `gem5.opt.sdc-py311` + compat loader 复跑，FINAL 全一致（平台切换不改变仿真确定性）。——实测：/tmp/u1c-verify.log 原生 5 跑全 PASS——smoke1=smoke2=45737cc9a76c0dce（rc=0，确定性复现逐字节一致）、dep_chain_int=98e5e31e726e383f（50s）、dep_chain_vec=b1e661a247b95774（49s）、rob_fill_int=19eab7d0de27237e（46s）；compat 回归（sdc-py311 + loader + PYTHONHOME）：smoke=45737cc9a76c0dce、dep_chain_int/vec、rob_fill_int 全 PASS（compat-sdc 行）。
- [x] **Step 7:** F-008 修订（「结构性不可用」→「单行 PEP604 shim 后可用」）+ progress Session 004 + 提交 `[OOO][P1][U1c] login01 原生 py3.9 平台复活：simulator.py 单行 shim + 四 golden 原生实测（F-008 修订 + F-011）` + bundle 推送。——实测：本提交（F-008 修订行/F-011 结果已落 findings.md；Session 004 已落 progress.md；bundle 推送见 Session 004 证据）。
- 失败处置：原生运行暴露进一步 3.10+ 运行时错误 → 逐站点同法迭代（同单元内）；不可收敛 → findings 记 BLOCKED + 转 DR-003（python3.11 bin+include 供给申请）。

**对 U2+ 的效力：** U1c 落地前 U2–U9 全部阻塞（新 C++ 必须重建、重建产物仅原生可跑）；落地后运行命令原生直跑（U2 Step 4 已随本修订改原生形态）。

### Task U2：流水时序族 A（D07 R08 FD09 FR09）

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/chaos_decode.hh/.cc`（D07：decode 事件提前/延后/丢失/重复）
- Modify: `CHAOS/gem5/src/cpu/o3/chaos_renamemap.hh/.cc`（R08：rename 时序扰动）
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSFPU*.hh/.cc` 或对应 FP 路径（FD09/FR09）
- Modify: `configs/se/ooo_proxy.py`（挂载参数：`--timing_mode {early,late,dup,drop}` 族）
- Modify: `tools/runner.py` dispatch + `schemas/manifest.schema.json` + `tools/manifest_validate.py`
- Modify: `tools/ooo_models.py`（impl_status 更新）

**Interfaces:**
- Consumes: chaos_trigger.hh F0–F5（时序扰动用 F2 窗口/F5 持续语义）；U1 映射表。——**Step 2 范围决策（2026-10-08，先行编辑）**：四模型触发面沿用既有注入器统一面（probability/first/last/max_faults/rng_seed + geometric skip——即 D01 工程轨 F0 语义的现有实现），不新增 chaos_trigger.hh 事件档（F4E/F6E）。理由：16 个既有 mode 全部走该面，runner/campaign/schema 零改线即可 F0 两态验证；F4/F6 的 eligible-event 档语义属 campaign 层（工作簿口径：F4=每 10 万 eligible 事件连发 2-4、F6=首个 eligible 确定性），在任一 F4/F6 pilot ITEM 排程前必须先补 chaos_trigger.hh 事件档 + runner freq→flags 映射（硬门槛，写入本注记）。geometric skip 对 F6 的「保证激活」意图不受损（跳过数种子确定，仍必激活）。
- Produces: 每模型子模式 flag，U10 观测链可从 simout 证据日志读 attempted/eligible/activated。**Step 2 实现修订（2026-10-08）**：子模式并入既有单一 `Param.String mode` 面——`--decode_mode decode_timing_{early,late,drop,dup}` / `fp_decode_timing_*`、`--rename_mode rename_timing_{early,late,dup,drop}`（16 个既有 mode 同一先例，零新增 py 参数）；本行原例 `--decode_timing early` 为示意形式。

**规格（03 表原文为准）:** D07=译码事件时序（提前/延后/丢失/重复）；R08=RAT 更新时序；FD09/FR09=FP 流水对应面。实现优先在既有 decode/rename 钩子内加事件移位/复制/丢弃逻辑，不新增 SimObject 时先复用 CHAOSDecode/CHAOSRenameMap 载体。

- [x] **Step 1:** 读 03 表四模型条目 + CHAOSDecode/CHAOSRenameMap 现有源码，列出每子模式的挂点与数据流（写入本任务执行注记，提交附）。——执行注记如下（2026-10-08 实读源码）：

  **编号对齐（先行事实）**：CHAOSDecode.hh Mode 枚举注释里的 "D01-D07" 引用 04-design-matrix 旧编号（D07=ImmBitflip2）；本轨道权威编号是 03 表（D07=时序，U1 注册表口径，unimplemented）。运行时映射以 runner.py sub_field→--decode_mode 为准（16 个既有 mode 名），新时序模式取独立名 decode_timing_*/rename_timing_*，无命名冲突。已实现 9 模型（D01/FD01/FD03/R01/FR01/R05/FR05/R07/FR07）不受影响。

  **挂点与数据流（gem5 v25 O3 实测行号）**：
  - fetch.cc:1259（既有）：fetch 内联 decode 后 → maybeCorruptEncoding（编码族，不动）。
  - decode.cc:663-699：Decode::decodeInsts 主循环，:696 `toRename->insts[toRenameIndex] = inst` 是 decode 输出锁存器的写入沿——**D07/FD09 全部四子模式的载体**。新方法 `maybePerturbDecodeTiming(inst, prev_tuple)` 在此调用（cpu->chaosDecode 空指针守卫，既有模式不动）：
    - **a 提前（读旧 tuple）**：victim 指令 N 保持自身 seq/timing，但其 staticInst 绑定替换为前一有效指令 N-1 的 decode tuple（锁存器早读=旧值被再次消费；下游读到旧值 → activated）。等价表象：N-1 的操作在 N 的位置重复执行一次。
    - **b 延后**：victim 本周期不写入 toRename（held 1 拍，payload 不变，次周期正常发出）——纯时延，多数为性能损失（Masked 基线）。
    - **c 丢失**：victim 不进入 toRename 且标记跳过（该指令永不 rename/execute/commit——丢失一次 decode 事务）。
    - **d 重复**：victim 额外复制一份 DynInst（新 seqNum，同 staticInst）一并写入 toRename——同 uop 双发。
    - eligibility（03 原文）：连续两条有效整数指令且 tuple 不同（D07）；FD09 同谓词限 FP/SIMD（opClass∈scalar Float*∪SimdFloat*，CHAOSFPU.cc:88-98 先例）。activated 判定按 03：仅当下游因此读取旧值/漏发/重复/变序。F0/F4/F6 经 chaos_trigger.hh。
  - rename_map.hh:143/308 setEntry（既有 CHAOS hook）+ :265 UnifiedRenameMap::rename 内 freeList getReg——**R08-a/b 载体**：
    - **a RAT 更新延后**：CHAOSRenameMap 挂起 (arch,phys) 写入一拍（pending 队列，次时钟沿经自调度事件回放）；窗口内该 arch_reg 读到旧映射（下游读旧值 → activated）。**a 提前**：同一挂起写在下一 tick 之始（任何 rename lookup 之前）回放——两种 1 拍斜偏，读窗口不同（tick 末回放=晚，tick 始=早），cycle-true 且可实现；gem5 子更新本是 tick 内原子，纯粹的"提前一整拍"不存在可观测面，此映射如实记入 honesty 注记。
    - **b free-list 弹出提前/延后**：弹出延后一拍（phys reg 残留 free list 头部一个窗口——同窗另一 rename 可能弹出同号 → 双重分配=静默 SDC 源）；提前=弹出在 tick 始执行（仅顺序效应）。
    - eligibility：同周期至少 2 条可重命名指令（R08）；FR09 限 FP/SIMD dest。
  - commit.cc:1352 `rob->insertInst(inst)`（v25 特有：ROB 插入在 Commit tick 的 fromIEW 缓冲处理内）+ iew.cc dispatchInsts 的 IQ insert——**R08-c/FR09-c 载体**：
    - **c ROB/IQ 分配丢失**：跳过一次 insert（指令执行但无 ROB 条目 → 永不提交/计数缺一 → Timeout 或静默跳过）；**重复**（Step-4 第2轮后修订）：~~同 inst 双 insert~~ → **rename 历史簿记条目复制**（rename.cc push_front 处对 victim 的 RenameHistory 二次压栈）。依据：双 ROB insert 在 v25 list-ROB 上不成立——commit 首次 retire 即清 InROB 标志，第二节点触发 `readHeadInst: isInROB()` 断言 abort（r08-dup/fr09-dup rc=134，/tmp/u2-runs/r08-dup.out:20）。历史条目复制的可观测口径不变（双提交/计数翻倍）：commit 侧 removeFromHistory 同轮消费两条同 sn 条目 → prevPhysReg 双重 freeList->addReg（freelist 出现重复 phys → 后续两次 rename 弹出同号 → 物理寄存器别名 = 静默 SDC 源），committedMaps 计数 +2。语义上更贴 03 原文（R08=RAT 更新时序，历史条目即 RAT 更新记录）。
    - honesty：v25 把 ROB 插入放 commit.cc 而非 iew.cc（与经典 O3 文献不同）——挂点以代码为准，注记留档。
  - 每模型独立可关；W3/W5（D07）、W4/W5（R08）、W8/W9（FD09）、W9/W10（FR09）工作负载不在本单元（两态验证用 dep_chain int，golden=98e5e31e726e383f）。

- [x] **Step 2:** 实现四模型子模式（每模型独立可关）。——执行注记（2026-10-08 实落地）：

  **实际文件**（Step-1 已记 v25 载体，文件名以仓库为准）：`CHAOS/gem5/src/cpu/o3/CHAOSDecode/{.hh,.cc,.py}`（D07/FD09 全四臂：fetch.cc buildInst 前 stale-tuple 重绑 a 臂 + decode.cc emit 点 b/c/d 臂）、`CHAOS/gem5/src/cpu/o3/CHAOSRenameMap/{.hh,.cc,.py}`（R08/FR09：rename_map.hh UnifiedRenameMap::rename 后回滚-挂起 a 轴 + free_list.hh PRE-pop 延后 b 轴 + commit.cc getInsts rob->insertInst c 轴丢/重）、fetch.cc/decode.cc/commit.cc/free_list.hh/rename_map.hh 挂点。

  **RAT 回放忠实度修订（复查自纠）**：a 轴回放为**条件回放**——表项仍等于挂起前旧映射才落，否则记 `honest_skip reason=newer_write_absorbed`（窗口内同 arch 更新写入被吸收）；无条件回放会把更新映射 revert 成旧值，超出 1 拍可见窗语义。

  **dispatch 子模式键位**：campaign 侧新增 `MODEL_SUBMODES`（arm 键 `early|late|drop|dup`，03 表时序臂词汇），`--submode` CLI 必填于多臂模型（缺省/拼错响亮拒）；run_id 嵌入 arm（如 `D07-early-F0-W3`）保证 run_key/seed 空间按臂隔离。注册表字母对照：D07/FD09 a/b/c/d=early/late/drop/dup 一一对应；R08/FR09 的 03 子模型列是 a/b/c 三字母、c=「丢失/重复」两臂——drop 与 dup 为 c 的两次独立 run；rename_timing_early 实现 a 轴（tick 始回放，honesty 映射已记 Step-1）。FR09 走 W7.2 `_vec` 类轴（sub_field `rename_timing_*_vec` → `--rename_target_class vec`）。

  **campaign 运行门时序（诚实顺序）**：dispatch/runner/schema 接线本步落地；`impl_status` 维持 unimplemented 到 Step 5（两态实测后才翻 implemented）——期间 campaign 对四模型的拒绝信息即 impl_status 门，属预期响亮化。schema component 枚举已含 decode/rat，无 schema 改动。
- [x] **Step 3:** 增量编译（guard 包裹）：`python3 tools/ooo_guard.py run --type build --desc u2-build --log /tmp/u2-build.log -- bash -c 'cd CHAOS/gem5 && scons -j8 build/ARM/gem5.opt'` → 预期 `scons: done`（引用尾行）。——进行中注记（2026-10-08）：
  - build1（17:51，exit 2）：nohup 环境无 `scons` 命令（pip --user 安装）→ 改 `python3 -m SCons`。
  - build2（17:52-17:59，exit 2）：`CHAOSRenameMap.hh` 内 `namespace gem5 { namespace o3 { class DynInst; } }` 写在 `namespace gem5 {}` 内部——namespace 定义名查找只搜最内层围封域，内部重开 `gem5` 实际**新建嵌套 gem5::gem5**，经 free_list.hh→cpu.hh 全链污染（/tmp/u2-outer.log:1111 起 `namespace 'gem5::gem5'` 连锁错）→ 改为与相邻行一致的裸 `namespace o3 { class DynInst; }`。教训记档：**CHAOS*.hh 头文件内 fwd-decl 一律抄相邻行形式，不得在 namespace gem5 内再包 gem5**。
  - build2 同批 decode.cc 3 错（build3 修复）：①CHAOSDecode 不完整类型（decode.cc 原只见 cpu.hh 前置声明）→ 加 `#include "cpu/o3/CHAOSDecode/CHAOSDecode.hh"`（fetch.cc:56 同式）；②③`std::unique_ptr<PCStateBase> dup_pc = inst->pcState().clone();` 拷贝初始化撞 explicit ctor → 改直接初始化括号形（fetch.cc:1166 同式）。
  - build3 实测通过（2026-10-08 18:02–18:08，guard run-finish）：`"exit_code": 0`、`scons: done building targets` ×1、elapsed 422s；仅 3 条 C++ warning 且全部位于本单元未触碰文件（CHAOSIQ.hh:135/136 -Wreorder、CHAOSPhysReg.cc:548 unused tid，皆为早前单元已提交代码），U2 触碰文件 0 warning 0 error；产物 build/ARM/gem5.opt 18:07:36 落盘 1227805584 B。
- [x] **Step 4:** 两态验证（每模型 × 注入关闭/开启，dep_chain int，golden=98e5e31e726e383f）。**前置 U1c：重建产物原生直跑（无 loader 前缀）**：
```bash
cd /home/share/suke/wangxu/gem5-fi-ooo
# 关闭态（不带注入 flag）→ FINAL=98e5e31e726e383f（golden 匹配）
build/ARM/gem5.opt --outdir=/tmp/u2-off configs/se/ooo_proxy.py --cmd workloads/ooo/dep_chain/dep_chain --cpu O3
# 开启态（示例 D07-early）→ 证据日志含 attempted/eligible/activated 计数，FINAL 偏离或 Masked
build/ARM/gem5.opt --outdir=/tmp/u2-on configs/se/ooo_proxy.py --cmd workloads/ooo/dep_chain/dep_chain --cpu O3 \
  --chaos_decode --decode_mode decode_timing_early --decode_max_faults 1 --decode_rng_seed 42
```
预期：关闭态 FINAL 与 golden 一致；开启态 simout/注入器 summary 含 `attempted>=1` 且分类非 clean（或显式 activated=0 时记录 eligible 不足，不得伪造激活）。

——执行注记（2026-10-08，两轮）：
- 第 1 轮（/tmp/u2-verify.sh 17 runs）：off 态 rc=0 50s FINAL=98e5e31e726e383f GOLDEN ✓；16 个 on-state 全部 rc=2 ~1s 即败——`ooo_proxy.py: error: argument --decode_mode: invalid choice: 'decode_timing_early'`。根因：configs/se/ooo_proxy.py 的 `--decode_mode`/`--rename_mode` argparse choices 列表缺 U2 新 token（C++ Param.String 已支持，Python 闸门未同步——接线遗漏，非注入器缺陷）。
- 修复：ooo_proxy.py 两处 choices 追加 8 个 decode/fp_decode_timing_* + 4 个 rename_timing_* token（ast.parse 语法 OK）；campaign CONFIG_SE=ooo_proxy.py 确认全部 OOO 模型只经此配置。单臂冒烟（d07-early）：rc=0，注入证据 `Tick: 417340, Site: fetch_decode, mode=decode_timing_early, ... faults_injected: 1`，FINAL=GOLDEN（Masked，时序臂合理结局）。
- 第 2 轮实测（argparse 修复后，pid 2860033，17/17 完成）：off GOLDEN ✓；15 run rc=0 GOLDEN、2 run **rc=134 abort**（r08-dup/fr09-dup）。**但证据日志暴露 3 缺陷**（详见各行 /tmp/u2-verify.out、/tmp/u2-runs/*）：
  - **缺陷①（decode 错面）**：`maybeCorruptEncoding` 未排除 8 个 timing 模式——W6 位翻面先开火并耗尽 max_faults，d07-early/d07-dup 与 fd09 全部四臂打在 `Site: fetch_decode` 编码损坏面（fd09 甚至打到 INT `str`：fpOnly 门只覆盖六个 W7 编码模式）。正确钩子（maybeStaleTuple/maybeTimingEmit）从未获得事件。d07-late/drop 侥幸走对（RNG 抽签次序不同）。修复：maybeCorruptEncoding 头部加 `if (timingModeActive()) return nullptr;`。
  - **缺陷②（rename dup 崩溃）**：同 inst 双 ROB insert → `rob.cc:513 readHeadInst: Assertion '(*head_thread)->isInROB()' failed`（首次 retire 清标志后第二节点违约）。修复：dup 移至 rename 历史簿记面（上方 c 行修订），commit.cc 移除 chaos_alloc==3 双插分支，maybeTimingAlloc 收窄为 Drop-only。
  - **缺陷③（freelist classValue）**：`UnifiedFreeList::setChaosRenameMap` 只传指针不设 `classValue`（该字段仅在 setChaosFreeList 里赋值）——未挂 CHAOSFreeList 时全部 per-class list 默认 classValue=0(int)，fr09-late（vec 弹出延后）静默 0 激活（log 0 行）。修复：循环内补 `freeLists[i].classValue = i;`（幂等，双注入器并存无害）。
  - 修复后预期：d07-early/dup 走 fetch/decode_emit 正面；fd09 四臂在 dep_chain（纯 int + FP16 仅以 microop 出现，tupleInScope 排除 macro/micro）大概率诚实 0 激活——如实记录（W8/W9 探针负载 P2）；r08/fr09 全臂含 dup 走新面。重建后跑第 3 轮。
- 第 3 轮实测（build4=修复①②③，2026-10-08 18:51 产物，17/17 完成，证据 /tmp/u2-runs/<arm>/{*.out,*_injections.log}）：off GOLDEN ✓（98e5e31e726e383f）；14 run rc=0 且全部 FINAL=GOLDEN；3 run 非 rc=0（d07-dup rc=139、r08-late/r08-dup rc=134，定性见下）。
  - **激活证据全链在案**（每臂 log 首行 faults_injected: 1）：d07-early `Site: fetch_decode, prev_mnemonic=subs, cur_mnemonic=b`（修复①生效：打在 stale-tuple 重绑正面而非 W6 编码面）；d07-late/drop `decode_emit, sn=172, b`；d07-dup `decode_emit, sn=179, ldr`；r08-early `rename_defer, X2, prev_phys=p107, new_phys=p112`；r08-late `freelist_pop_delay, class=int, head_phys=p112`；r08-drop `rob_insert, sn=192, ldr`；r08-dup `rename_history_dup, X2, sn=178, new_phys=p112, prev_phys=p107`；fr09-early `rename_defer, V1, prev_phys=p45, new_phys=p0`；fr09-late `freelist_pop_delay, class=vec, head_phys=p0`（修复③生效：vec 类可激活）；fr09-drop `rob_insert, sn=9729, ldfp16_uop`；fr09-dup `rename_history_dup, V1, sn=9729, new_phys=p0, prev_phys=p45`。**victim 一致性**：r08 三臂同 victim（tick=420035, sn=178, X2, p107→p112）、fr09 三臂同 victim（tick=10287970, sn=9729, V1）——臂间独立 RNG 流下 victim 可复现，注入定位确定。
  - **fd09 四臂诚实 0 激活**（无 log 文件）：dep_chain 纯 int，其 FP16 仅以 microop 出现（ldfp16_uop），tupleInScope 排除 macro/micro 后 eligible=0。符合 Step-4 预期条款（显式 activated=0 + eligible 不足，如实记录）。**scope 增补（第 3 轮决定）**：fd09 四臂 + off 改跑 polybench/gemm（FP 算术密集，FINAL=FNV-1a，注册 golden `polybenchgemm-golden-v1`=116849d3adf3227b）取激活级证据；若 gemm 仍 0 激活则如实记录，激活级验证随 P2 W8/W9 探针负载。
  - **缺陷④（d07-dup rc=139 SIGSEGV——真缺陷，修复已落源码待 build5）**：dup DynInst 未注册 CPU instList——完成期 `removeList.push(inst->getInstListIt())` 持垃圾迭代器，`cleanUpRemovedInsts` 内 list erase 段错误（`_M_unhook`，/tmp/u2-runs/d07-dup.out:20-27）。修复：decode.cc dup 块补 `dup_inst->setInstListIt(cpu->addInst(dup_inst));`（fetch.cc:1041 buildInst 同式，2026-10-08 19:01 落源码，**build5 后第 4 轮复验**）。
  - **缺陷⑤（r08-late rc=134）——定性收口：非 harness 缺陷，注入态固有显现**：`inst_queue.cc:1648 addToProducers: panic: Dependency graph 112 (integer) (flat: 112) not empty!`，abort@tick 505890（远早于正常完成点——fr09 臂 tick 10287970 仍在执行段）。机理：延后臂 fire 后同一拍窗口内后续 int getReg 仍返回同 head → p112 双重分配（**即注入面本体**，free_list.hh:153-156 注释明文「双重分配即故障面」）；IQ dependGraph 单生产者不变量无法表示双 owner，p112 下次再产出时 addToProducers panic——abort 信息自身点名 victim（graph flat 112 == 注入 head_phys p112）。旁证：fr09-late 同模型 vec 臂 fire（p0@10287970）结局 GOLDEN（Masked）——结局依赖 victim 窗口占用（窗口内有无第二次 vec pop 无逐弹日志可证，按 harness 代码复核+结局推断，逐弹留痕属 P2 探针深化），正是 FI 语义。harness 复核：maybeDelayFreePop fire 时不弹、原样返回 head；freePopReplay 下拍 chaosDeferredPop 恰弹一次（非空保护）——与模型文档一致，无实现偏差。**分类：activated=1 + simfail（微架构不变量违约→模拟器中止）**。
  - **r08-dup rc=134——定性：真传播（crash 类，非平台 bug）**：`faults.cc:103 panic: Page table fault when accessing virtual address 0x1f`，abort@tick 511665。机理：历史条目复制 → commit `removeFromHistory` 同轮消费两条同 sn 条目 → prevPhysReg p107 双重 `freeList->addReg` → freelist 重复 → 后续双弹 → 物理别名 → 架构寄存器垃圾值 → workload 解引用 0x1f SEGV。**注入故障完整传播至架构层**（新 dup 面的首个实测传播证据）。分类：activated=1 + crash（DUE 类）。
  - fr09-dup activated=1（V1, p0/p45）但 GOLDEN：fire@10287970 近末端，p45 双 free 后未及双弹/别名消费即正常退出（按结局记录；逐弹留痕 P2）。
- 第 4 轮（build5 = 增量重建含缺陷④修复，2026-10-08 起）：全 17 臂重跑 + fd09@gemm 补充（off+4 臂），逐臂定性（GOLDEN/Masked/simfail/crash/诚实0激活）后收 Step 4。
- 第 4 轮实测（build5，2026-10-08 19:22–19:40，22/22 ALL-DONE，/tmp/u2-r4-runs/，脚本 /tmp/u2-verify4.sh）：build5 增量（decode.cc [CXX]→`scons: done building targets`，0 新告警，exit 0，421s；重建后 `ln -f` 刷新根路径硬链接——同 inode 双名，防 CLAUDE.md 陈旧双路径陷阱）。
  - **dep_chain 17 臂全部复现 round-3 定位（确定性 RNG）**：off GOLDEN；d07-early/late/drop 与 fr09 四臂、r08-early/drop、fd09 四臂（诚实 0 激活）全部 GOLDEN/Masked 且 victim tick/sn 与 round-3 逐字一致；**d07-dup rc=139→rc=0 GOLDEN（缺陷④修复验证通过**，同 victim tick=419650 sn=179 ldr，dup 指令完成期正常回收）；r08-late rc=134（tick 505890 IQ graph 112 panic 逐字复现）、r08-dup rc=134（tick 511665 SEGV 0x1f panic 逐字复现）。
  - **fd09@gemm 补充（5/5）**：g-off FINAL=116849d3adf3227b == 注册 golden `polybenchgemm-golden-v1` ✓；**四臂全部激活**（FP 元组合格）：early `fetch_decode, prev_mnemonic=fmul, cur_mnemonic=fmadd`@62077785；late/drop 同 victim `decode_emit sn=124174 fmadd`@62128990；dup `decode_emit sn=124201 fmadd`@62149010——全 GOLDEN（Masked，单发时序臂合理结局）。FD09 激活级证据闭环（dep_chain 0 激活纯系负载无合格 FP 元组）。
  - Step 4 收口判定：关闭态双负载 golden 匹配 ✓；16 开启臂中 12 臂激活证据+Masked、2 臂激活+Crash（DUE）、2+4 臂按预期（fd09@dep_chain 诚实 0 激活 / fd09@gemm 全激活）；零未解释失败。
- [x] **Step 4b（U10 交接）:** 首个 on-state outdir 跑 `python3 tools/ooo_observe.py <outdir> --golden <golden> --ref-outdir <off outdir>` → L0 计数与注入器日志一致、faults_source 与 verdict 如实收口。——实测（2026-10-08，/tmp/u2-r4-runs/{d07-early,r08-late,r08-dup}，脚本写 exit.rc 后重跑）：
  - d07-early：`rc=0 checksum=98e5e31e726e383f==golden` → **L5 verdict=Masked**（"fault did not propagate"）✓ 与实测结局相符。
  - r08-late / r08-dup：`exit=134 + fault landed (faults_injected=1) + no checksum` → **L5 verdict=Crash（DUE per §2.2）**，分类器明示「NOT a tool failure（真 SimulatorError 须 faults_injected==0）」——**round-3 手工措辞『simfail』按统一分类器口径修正为 Crash(DUE)**；机理注记不变（r08-late=IQ 单生产者不变量违约、r08-dup=架构 SEGV 真传播，两例 panic 文本与 tick 均可区分）。
  - L0 对账（三臂一致）：`legacy_injected_total=1, faults_for_classify=1, faults_source=legacy_injected` == 各臂日志 `faults_injected: 1` ✓；conservation OK ✓。**计划原词 `faults_source=funnel_activated` 按实际修正为 `legacy_injected`**：U2 注入器发 legacy 格式行（`Tick/Site/.../faults_injected: N`），未发 CHAOS_L0_FUNNEL 漏斗行——legacy 即本四模型的证据档（与 CHAOSMem G5 同档），非缺失。
  - 环境注记：ad-hoc 验证脚本不落 `exit.rc`/`simout`（campaign runner 原生会写）——事后按日志实测 rc 写入 exit.rc、按 .out 控制台捕获重建 simout（内容=该次运行 gem5 真实输出），观测链随后 verdict 正常；未来轮次脚本补 `echo $rc > exit.rc` 即免重建。
- [x] **Step 4b（U10 交接）:** 首个 on-state outdir 跑 `python3 tools/ooo_observe.py <outdir> --golden <golden> --ref-outdir <同模型 off 态 outdir>` → L0 计数与注入器日志一致、faults_source 与 verdict 如实收口——U10 的开启态验证在此收口（实测见上方第 4 轮注记：Masked/Crash/Crash 三态相符、legacy 档对账 1==1、原词 funnel_activated 修正为 legacy_injected）。
- [x] **Step 5:** ooo_models.py impl_status 更新四模型 + `--check` 仍 310/310。——实测（2026-10-08）：静态翻 D07/R08→(implemented, CHAOSDecode/CHAOSRenameMap)、FD09/FR09 同构；09 审计表同步四行（注入器/模式面 + 判定 已实现 + 缺口改实测注记）+ 总账（已实现 9→13、未实现 14→10）。`--check`：`models: 57 | items_scanned: 310 | item_refs_resolved: 310 | unresolved: 0`、`impl_status: implemented=13 partial=34 unimplemented=10`、无 CHECK FAILED。
- [x] **Step 6:** 提交 `[OOO][P1][U2] 流水时序族A：D07/R08/FD09/FR09 子模式 + 两态实测`。——实测：commit `107de592`（18 文件，+1029/−49，ooo-exec）。中继推送（login01 无外网，bundle 通道）：`/tmp/u2-oct8.bundle`（32524 B，sha256 `bace010c…d7694`，基 6505d9b1）→ Windows `reach fs read` 字节级落地（sha256 复核一致）→ 本地 fi-ding 集成。**远端两次移动均按规分析后合并（绝不 force）**：① ae6e151e（LSU ITEM-018..026+F-037/F-038，10 提交）→ merge a2cd14d2（progress.md 冲突：pilot 状态取远端较新、集群平台状态取本地较新 U3b+U3 完成，两流事实保留于 merge 注记）；② 01008446（ITEM-026/027 A06 闭合）→ merge 3c9677f6（同规则）。U2 merge 7e19e41e 干净（18 文件 +1029/−49 与原提交一致）。push `01008446..3c9677f6 fi-ding -> fi-ding` ✓，远端 tip `3c9677f6` 复核一致。

### Task U3：流水时序族 B（B08 B09 FB08 FB09）

**Files:** 同 U2 模式，载体 `CHAOSROB*.hh/.cc`（B08/B09：squash/commit 时序扰动）+ FPU 路径（FB08/FB09）；配置/dispatch/schema/validate/models 同步。

**Interfaces:** Consumes U2 的 timing_mode 参数族约定；Produces squash/commit 时序子模式 flag。

**规格:** B08=ROB squash 时序（提前 squash/延迟 squash/squash 丢失导致的假活）；B09=commit 时序；FB08/FB09=FP 对应面。验证负载用 rob_fill int（golden=19eab7d0de27237e，深 ROB/连续 mispredict 特性对口）。

**Step-1 挂点注记（2026-10-08 实读 ooo-exec 源码；文件:行号为 build5 后现状）:**

03 表四模型（03-design-matrix.md L111/L112/L155/L156）→ gem5 v25 载体映射，四臂均为 03 表"提前/延后/丢失/重复"时序扰动、数据载荷保持正确：

- **B08 squash 时序** — 载体 `CHAOSROB` 新增 `squash_timing_{early,late,drop,dup}`。挂点：`ROB::squash()`（rob.cc:476）——mispredict/order-violation（commit.cc:829）与 squashAll 家族（commit.cc:526）的单一漏斗。实证：v25 默认 squashWidth 未设 → doSquash 单拍全量（rob.cc:345），squash 是 ROB 侧点事件；commit 侧下一拍起以 commitWidth 分拍排空 isSquashed 项（commit.cc:953-977）。四臂：
  - `early`(B08-a)=触发拍内标记+当拍启动排空：commit.cc:829 块 rob->squash 后把 commitStatus[tid] 直翻 Running（绕过 ROBSquashing 一拍往返；仅绑 mispredict 块——526 squashAll 各调用方随后自设 ROBSquashing 会覆盖，不作为该臂绑定面）——approx=squash_drain_advanced_1c；
  - `late`(B08-b)=走表延后一拍：ROB::squash 跳过立即 doSquash（squashIt/squashedSeqNum/doneSquashing=false 照设），下一拍由 Commit::tick 既有 doSquash 续走（commit.cc:634）——ROBSquashing 状态门使错误路径不进提交窗（gem5 实现下该 03 危害面不可达，诚实记 perf-only）；
  - `drop`(B08-c)=squash 对 ROB 丢失：不走表、直置 doneSquashing=true——错误路径指令留存 ROB，完成者经 commitHead 错误提交（03 预期"错误路径结果进入完成/提交窗口"）→ SDC/Crash 面；须配 timeout 防 hang；
  - `dup`(B08-d)=同一 squash 二次走表：自然走表 + clockEdge(+1) 事件重放 rob->squash(同界)（重放挂 replay 守卫防递归）——标记幂等，03 自述"重复多为性能损失"，预期多为 Masked/perf。
- **B09 commit 时序** — 载体 `CHAOSROB` 新增 `commit_timing_{early,late,drop,dup}`。挂点：`Commit::commitInsts()`（commit.cc:927 循环）。gem5 提交事务 = {commitHead 判定(993) / ROB pop(retireHead) / doneSeqNum→IEW(1022)——同时驱动 rename 历史走查释放 old-dest（rename.cc:459-463）与 store 落存（iew.cc:1494，均 doneSeqNum 语义）/ updateMiscRegs(1034，AArch64 NZCV 等杂项态提交时落盘)}。四臂各绑一子事件：
  - `early`(B09-a)=grant 提前：commitWidth 用尽当拍额外放行 1 条（循环条件扩展）——按序提交下架构不可见，诚实预期 not-activated/Masked；
  - `late`(B09-c)=old-dest 释放延后一拍：抑制当拍 doneSeqNum 写入（1022 包裹）→ rename 走查+store 落存滞后一拍，下一拍新 doneSeqNum≥界自愈；
  - `drop`(B09-d)=架构状态更新丢失：绑定指令跳过 updateMiscRegs（1034 包裹；资格=numMiscDestRegs>0 即 NZCV/FPSR 写者）→ 陈旧标志位 SDC 面；
  - `dup`(B09-b)=ROB pop 重复：绑定指令成功提交后额外 retireHead 一次——次头未就绪则 readyToCommit 断言中止（Crash DUE 面）；就绪则次头指令从提交流消失（probe/杂项更新丢失；doneSeqNum 累计语义下其 old-dest 仍随后拍释放——"消失"多 Masked、断言面 Crash，如实两态记录）。
- **FB08 FP/SIMD squash 时序** — 载体 `CHAOSROB` 新增 `fp_squash_timing_{early,late,drop,dup}`。early/late/dup=B08 同机制 + 资格门（squash 窗口内含 FP/SIMD 指令；Float*/SimdFloat* opClass 集=CHAOSDecode.cc:78-84 同一谓词；窗口扫描由 ROB::squash 入口预扫 instList 传入注入器）。`drop`(FB08-c)=**结果抑制丢失**：挂点 iew.cc:1169 Execute 侧 squash 跳过块——绑定一条 FP/SIMD 指令不跳过、照常执行回写，错误路径 FP 结果落入已被 squash 释放的 vec 物理寄存器 → 别名污染 SDC 面（回写链 iew.cc:1405 isSquashed 门的旁路实现时一并核查）。FB08-b（FU 取消丢失）=gem5 无独立 FU-cancel 事件（发射自 IQ，squash 即 IQ 摘除）——arch-n/a 诚实记录于审计行。
- **FB09 FP/SIMD commit 时序** — 载体 `CHAOSROB` 新增 `fp_commit_timing_{early,late,drop,dup}`。=B09 四臂 + FP 绑定（early/drop/dup 绑定指令须 FP/SIMD；late 资格=当拍提交含 FP/SIMD）。FB09-c FPSR 面=updateMiscRegs 抑制（FP 杂项写者稀少——rob_fill_fp/gemm 或诚实 0 激活，如实记录，FD09@dep_chain 先例）；FB09-b V 映射面由 U2 FR09-dup(vec) 邻面覆盖、FB09-d old-dest 面由 late 臂+FR09 族邻面覆盖——审计行如实注明。

配置/调度：复用既有 `--chaos_rob --rob_mode --rob_first_clock --rob_max_faults --rob_rng_seed`（ooo_proxy.py:170-203,616+），无新 flag；FP 判定在注入器内（opClass 谓词），不涉 `--rob_target_class`。runner.py rob 块（1040）+ ooo_campaign.py MODEL_DISPATCH/MODEL_SUBMODES 增 B08/B09/FB08/FB09（component=rob, flag=--chaos_rob）四表项，fault_model 元数据循 U2 惯例（early/late/drop=delay_omission、dup=recurring_result_stuck）。验证负载：rob_fill（int，golden 19eab7d0de27237e；二进制 7334 条条件分支→mispredict 面；循环 cmp/adds→NZCV 写者面）+ rob_fill_fp（fp，golden 85085fd5686d173b，FDIV/浮点流）；两态判定 off 对表 FINAL、on 分层记 attempted/激活（L0 funnel/legacy 双源）。

- [x] **Step 1:** 读 03 表四模型 + CHAOSROB 源码，列挂点注记。——实测：上方 Step-1 注记（commit.cc:818 mispredict 块/rob.cc:476 squash 入口/doSquash 单拍全量走表/commit.cc:927·1022·1034/iew.cc:1169·1405 全部实读行号）。
- [x] **Step 2:** 实现四模型子模式。——实测：CHAOSROB.hh/.cc 增 squash 族（maybeSquashTiming：DelayWalk/DropSquash/DupWalk + 重放守卫 + arm/consumeSquashEarlyDrain）与 commit 族（grantExtraCommit/suppressDoneSeqNum/suppressUpdateMiscRegs/extraRetireHead/bypassSquashSkip）+ isFpOpClass 谓词 + chaosWindowHasFP 窗口预扫（rob.cc）；rob.hh/.cc squash 尾挂点；commit.cc mispredict 块 arm/consume + 宽度门 + doneSeqNum/updateMiscRegs 包裹 + 成功块尾 extraRetireHead；iew.cc Execute squash 跳过旁路；ooo_proxy.py --rob_mode choices +16（发现并补上此前缺失的挂载层）；runner.py 16 子模式链；ooo_campaign.py 4 dispatch + 4 submode 表。
- [x] **Step 3:** guard 包裹增量编译 → `scons: done`。——实测：build002 失败（CHAOSROB.cc DynInstPtr 未限定 → 补 o3:: 限定）；build003 编至 18 分钟 mem_footprint.o EIO 中止——根因 /home/share 配额满（并发会话清 4.8G tarball 后解除）；build005 `SCONS RC=0 BUILD COMPLETE`（23:38:49）；b08-early 修复后 build006 `BUILD COMPLETE`（00:15:33，gem5.opt sha256 24bcb506…）零新增告警（6 条全为既有：5 环境类 + 1 CHAOSIQ -Wreorder）。
- [x] **Step 4:** 两态验证（rob_fill int，关闭态 FINAL=19eab7d0de27237e；开启态 attempted>=1 证据）。——实测三轮（/tmp/u3-verify.out 终证）：pass1 24 臂全 rc=2（ooo_proxy.py choices 漏 16 模式→补齐，无重建）；pass2（build5）int-b08-early rc=124 死锁——2.5GB Commit 调试日志定位：commitStatus 同拍翻 Running 使 getInsts（commit.cc:1398 插入门）在错路径指令尚未被 backward squash 标记时入 ROB，sn=173 僵尸头 + ROB 128/128 永久阻塞→commit.hh/cc 增 chaosSkipGetInsts 单拍抑制；pass3（build6）26/26：off 两态 GOLDEN（19eab7d0de27237e / rob_fill_fp 85085fd5686d173b），on 24 臂 20 激活/4 诚实 0 激活（int-fb08×4 squash 窗口无 FP、int-fb09-drop fmov 无 misc dest），结果 20 GOLDEN(Masked) + int-b08-drop rc=124 Timeout（walk 丢失面）+ 3×rc=134 Crash DUE（b09-dup/fb09-dup(int/fp) retireHead 断言）；int-fb09-early/late 在静态库 sparse FloatMiscOp(fmov) 上激活（sn 10045/535381）。
- [x] **Step 5:** ooo_models.py 更新 + `--check` 310/310。——实测：B08(R27)/B09(R28)/FB08(R56)/FB09(R57) impl_status→implemented + injector→CHAOSROB；`python3 tools/ooo_models.py --check` → `models: 57 | items_scanned: 310 | item_refs_resolved: 310 | unresolved: 0 | impl_status: implemented=17 partial=34 unimplemented=6 | OK: 静态表 ↔ 03 索引/详表 ↔ 09 逐模型判定 ↔ 清单 ITEM 三方一致`；09 审计行 47/48/76/77 同步翻已实现（含两态实测注记）；回归 test_ooo_classify 26/26 + test_ooo_guard_f025 12/12 PASS。
- [x] **Step 6:** 提交 `[OOO][P1][U3] 流水时序族B：B08/B09/FB08/FB09 子模式 + 两态实测`。——实测：commit `d8ed7271`（15 文件，+824/−27，ooo-exec；d8ed7271 正文原记 13 文件系列举笔误，实为 15：CHAOSROB.hh/.cc/.py、commit.hh/.cc、iew.hh/.cc、rob.hh/.cc 共 9 源文件 + ooo_proxy.py + runner.py/ooo_campaign.py/ooo_models.py + 09 审计 + 本计划）。中继推送（login01 无外网，bundle 通道）：`/tmp/u3-relay.bundle`（23880 B，sha256 `0b11ec4a…c9649`，基 107de592，含 22417e69+d8ed7271）→ Windows `reach fs read` cmd 重定向字节级落地（sha256 复核一致）→ 本地 fi-ding 集成：远端 fi-ding 已含 U2 中继线（3c9677f6）且其上 LSU 线新增 5 提交至 43ab2400——与 U3 delta 15 文件仅计划文件重叠（远端已载 22417e69 同文 U2 勾选），merge `d5464fdc` 干净零冲突（15 文件 +824/−27 与原提交一致）。push `43ab2400..d5464fdc fi-ding -> fi-ding` ✓，远端 tip `d5464fdc` fetch 复核一致。

### Task U4：控制状态换值族（D06 FD05）

**Files:** 载体 `CHAOSDecode*.hh/.cc`（D06：sf/S/shift/extend/signed 控制位换值）+ FP decode 路径（FD05：scalar↔vector/element-width 合法组合换值）；配置/dispatch/schema/validate/models 同步。

**Interfaces:** Consumes U1 表 + chaos_trigger F0/F1；Produces `--decode_ctl_swap <field>` / `--fp_ctl_swap <mode>` 子模式 flag。

**规格:** D06=译码控制字段换为另一合法值（N/Z/C/V 标志语义、移位类型 LSL↔LSR↔ASR↔ROR、extend 类型、signedness）；FD05=FP 标量↔向量/元素宽度合法组合互换（保持指令合法，制造语义级偏差——预期 SDC 倾向而非 Crash）。

> **U4 Step-1 执行注记（GNU-as 闭环对表，2026-10-09）**：03 表已读（D06-a..e / FD05-a..c 全部 8 子模式）。对表产物 `/tmp/u4/`（持久化 `runs/ooo-node/evidence/u4-step1/`）：`corpus.s` 97 条正例（定寄存器 x0/x1/x2·w/v/d/s，覆盖 D06 五子模式与 FD05 三子模式全部目标家族 + imm6>=32 边界 4 条）+ `neg.s` 22 条负例（b/bl/cbz/csel/ccmp/adr/ldr/str/ldp/ldxr/stxr/ret/nop/movz + ldr d/q/str s/fcmp/fmov/fcvt/scvtf）→ host `gcc -c` + objdump 取全部真值编码；`u4rules.py` 70 行换值规则（D06 21：a=8 sf/b=6 setflags/c=4 shift/d=1 extend/e=2 signedness；FD05 49：a=12 scalar-vector/b=15 elem-width/c=22 lane-count）+ `u4pairs.py` 56 指定对 + `u4verify.py` 五轴闭环校验：① 56 对 src&mask==match 且 src^xor==dst，且 xor&mask==0 的双向行回程成立、!=0 的方向性行不重复匹配；② 213 规则×正例再译码（`.inst` 重汇编——`.word` 受 aarch64 $d mapping-symbol 害全假阴性，改 `.inst` 后得真值）：每条匹配均落真实指令且寄存器序号序列保持；条件行 `_sh_x`（x→w 移位形式）imm6>=32 时必须 undefined（4 条边界行实证刻画）；③ 22 负例零匹配（含 `movz x0,#1` 曾误中 D06a_log_imm——bit23 区分逻辑立即数(0)与 MOVZ/MOVN/MOVK(1)，钉死后排除）；④ FD05 对全部 int 标量正例零泄漏；⑤ 每规则 >=1 正例匹配 → **ALL-PASS**（corpus=97 neg=22 rules=70 pairs=56 mod_checks=213）。汇编器实教（已并入规则常量）：ROR 在 ADD/SUB 移位形式非法（只 LSL/LSR/ASR → add 行 lsl<->lsr、asr->lsl）；MUL 3-same 无 .2d 变体（宽度换值限 .8h<->.4s + q0 行）；逻辑立即数 N 位（bit22）随 sf 联动（sf=0 须 N=0 → 掩码钉 N=0，N=1 源诚实排除）；3-same SIMD 一律 bit21=1（match byte2|=0x20）；ADD/SUB bit21=1 即 extend 形式（option[15:13]+imm3 别名 imm6 可达 32..63）→ D06-c 钉 bit21=0 只打移位形式；extend 形式 8 种 extend 在 w 上全合法 → extend 形式 sf 双向安全，移位形式 x→w 仅 imm6<32 安全（拆 _w 无条件 / _x 条件两行，注入器 decodeChaos 再译码门兜底）。

- [x] **Step 1:** 读 03 表两模型全部子模式条目；用 GNU as 对表验证每个换值组合仍是合法编码（`aarch64-linux-gnu-as` 不在集群，用 host `gcc -c` + objdump 反汇编对表；产出对表清单入执行注记）。——实测：ALL-PASS（corpus=97 neg=22 rules=70 pairs=56 mod_checks=213；证据 `runs/ooo-node/evidence/u4-step1/u4-verify.out`，规则/对表/语料同目录）。
- [x] **Step 2:** 实现（合法值域表驱动：每控制字段的合法值枚举 + 换值映射）。——实测：8 模式全进 CHAOSDecode——.hh（枚举+8 表声明+matchCtlSwapRule/injectCtlSwap 声明+闭环溯源注记）与 .cc（70 行 8 表由 u4rules.py **程序化生成** cc_tables.txt 免手工转录；switch 匹配器；stringToMode/modeToString 8 项；is_ctlswap_mode **无 fpOnly 门**（表即门——FD05-b/c 整数 SIMD lane 属子模式范围）；资格分支；dispatch；injectCtlSwap：xor→decodeChaos 重译码→"unknown" 拒绝→寄存器序号判定（CC/Misc 类过滤+仅低 16 位索引+顺序敏感——setflags ±NZCV 与 FD05-a d↔v 类变化合法放行，结构意外拦截）→honest_skip/inject 双日志）；接线 4 文件（CHAOSDecode.py 模式文档串、ooo_proxy.py choices、runner.py sub_field 元组+注记、ooo_campaign.py MODEL_DISPATCH D06/FD05+MODEL_SUBMODES D06 a-e/FD05 a-c fault_model=legal_domain_sub）；ooo_models.py 翻转属 Step 5（U2 惯例：两态验证后再翻，campaign 此前大声拒绝为设计行为）；ast.parse 4 文件语法全过（编译属 Step 3）；证据 `runs/ooo-node/evidence/u4-step2/`（cc_tables.txt+inject_ctlswap.txt+9 补丁脚本）。
- [x] **Step 3:** guard 包裹增量编译 → `scons: done`。——实测：`nohup build-gem5.sh`（flock 单实例）→ `SCONS RC=0` + `BUILD COMPLETE`（logs/gem5-build-007.out，2026-10-09T08:17:22+08:00）；CHAOSDecode.cc 干净重编；新增警告 **0**（日志仅 5 条既有工具链 Warning: GCC 版本/tcmalloc/HDF5/capstone/systemc，与 006 相同）；新二进制 sha256 `4add2fcd90a3e7264a298e735743d5d8924d6b84c36e6e9ea759c938efc65632`（state/gem5.opt.sha256）。
- [x] **Step 4:** 两态验证（dep_chain int 关闭态 golden；开启态每子模式一次，验证换值后指令仍合法提交且结果偏差被 L1 层捕获）。
  - 2026-10-09 完成（build 007, sha256 4add2fcd…65632）。关闭态 golden 复核：dep_chain 98e5e31e726e383f / rob_fill_fp 85085fd5686d173b / gap 2ec8c1e59f2808c5，全部 rc=0、无注入日志文件。
  - 开启态 8/8 子模式全部真激活（`--chaos_decode --decode_mode <m> --decode_max_faults 1 --decode_rng_seed 42`，timeout 300，ooo_proxy.py --cpu O3）：
    - D06a `subs x1,w1,w3`→w 窄化（ctl_swap_sf, D06a_add_imm 行）；D06b `add`→`adds` bit29（D06b_add_imm）；D06c lsl→lsr（D06c_add_lsl）；D06d extend bit13（D06d_ext_type）；D06e 符号位 bit15（D06e_ext_sign）——5/5 全 Masked/GOLDEN，rc=0 合法提交。
    - FD05b `add v2.2d`→`v2.16b`（rob_fill_fp, FD05b_add_q1, FINAL 095b9bccf5a979a4 ≠ golden → **SDC/WRONG**）；gap 上 `add v1.4s`→`v1.16b`（同规则行）→ Masked —— 同一子模式两态（SDC+Masked）均实测。
    - FD05a `fadd d0,d0,d1`→`fadd v0.2d`（gap 0x400814, FD05a_fadd_d0, xor 0x5000fc00）→ Masked；FD05c `add v1.4s`→`add v1.2s`（gap 0x400534, FD05c_add_s1, Q 位 xor 0x40000000）→ **SDC/WRONG**（FINAL 913fd8766684d963）。
  - FD05a/c 在 rob_fill_fp 上 0 激活（种子 42/7/123 共 6 轮 loglines=0）——合格位点位于永不执行的 libc 区（0x45aabc/0x45aacc/0x45aae4）；换 gap 工作负载（d 形标量 + .4s 向量位點在 app 热核）后即真激活，全部尝试如实记录。
  - 证据：runs/ooo-node/evidence/u4-step4/（summary.txt 18 行全记录、6 脚本/输出、15 份 decode_injections.log）。专用激活面 W9 NEON-LaneProbe 属 P2。
- [x] **Step 5:** ooo_models.py 更新 + `--check`。
  - 2026-10-09 完成。——实测：静态翻 D06(R7)/FD05(R34) → (implemented, CHAOSDecode)；`python3 tools/ooo_models.py --check` → `models: 57 | items_scanned: 310 | item_refs_resolved: 310 | unresolved: 0`、`impl_status: implemented=19 partial=34 unimplemented=4`、`OK: 静态表 ↔ 03 索引/详表 ↔ 09 逐模型判定 ↔ 清单 ITEM 三方一致`（翻转前 CHECK FAILED 拦 4 项 = D06/FD05 静态↔文档差，即门在工作）。
  - 09 审计同步：D06/FD05 逐模型行翻已实现（含 GNU 对表 + 两态实测注记）；总账修真 已实现 13→19（补 U3 漏更的 B08/B09/FB08/FB09 + 本单元 D06/FD05）、未实现 10→4（D09, FB06, FD07, FR08）；WB3 段头 14→4 + 族表加状态列（流水时序 U2/U3 已实现、控制状态换值 U4 已实现、拼接/配对=U5 工作面、decode 卡死 D09 未实现）；F-010 注记算术更新（19+0+4≠57，逐模型表权威不变）。
  - 回归：test_ooo_classify 26/26 PASS（SELFTEST PASS (26 checks, 0 failed)）+ test_ooo_guard_f025 12/12 PASS（SELFTEST PASS (12 checks, 0 failed)）。
- [x] **Step 6:** 提交 `[OOO][P1][U4] D06/FD05 控制状态合法换值 + GNU 对表`。
  - 2026-10-09 完成。——实测：commit `1927018e`（9 文件，+460/−25，ooo-exec：CHAOSDecode.hh/.cc/.py、ooo_proxy.py、runner.py、ooo_campaign.py、ooo_models.py、09 审计、本计划）。中继推送（login01 无外网，bundle 通道）：`/tmp/u4-relay.bundle`（18429 B，sha256 `512c0998…06465`，基 d8ed7271，含 8a0c7b50+1927018e）→ Windows `reach fs read` 字节级落地（sha256 复核一致）→ 本地 fi-ding 集成：远端未移动（origin/fi-ding = d5464fdc），重叠恰 2 提交、merge-base d8ed7271 符合设计，merge `c148f141` 干净零冲突（9 文件 +461/−26 = 8a0c7b50 勘误 +1/−1 与 1927018e +460/−25 之和）。push `d5464fdc..c148f141 fi-ding -> fi-ding` ✓，远端 tip `c148f141` fetch 复核一致。

### Task U5：拼接/配对族（FD07 FR08 FB06）

**Files:** 载体 CHAOSDecode（FD07：shuffle/permute/lane-select 编码表）+ 新钩子 DynInst::setRegOperand（FR08：preserve/zero/merge 换值；FB06-b：dest tag 互换）+ inst_queue.cc processFUCompletion（FB06-c：完成事件配对交换）；配置/dispatch/schema/validate/models 同步。

**Interfaces:** Consumes U1 表；Produces lane 元数据与完成事件配对子模式 flag。

**规格（03-design-matrix 权威）:** FD07(R36)=向量立即数/shuffle/permute/lane-mask 拼接元数据（a imm 片段交换、b lane 选择循环移位、c shuffle selector 互换、d 上一条 lane mask）；FR08(R46)=标量写/窄 lane 写/全宽写的 preserve/zero/merge 语义换值（a/b/c）+ 新旧 lane 错误拼接（d）；FB06(R54)=FU 完成事件配对换值（a ROB index〔gem5 恒等=alias-of-c〕、b 目的 tag、c 动态指令 ID）。NEON 掩码一律 64 位（Global Constraints）。

- [x] **Step 1:** 读 03 表三模型 + 现有 FPU/向量路径源码，列挂点注记。
  - 2026-10-09 完成。三模型挂点注记（源码实证）：
  - **FD07（R36，Decode，4 臂）→ CHAOSDecode 扩展**（U4 表驱动同构）。app 代码指令面普查（objdump 0x40xxxx）：gap/dep_chain 近同构——**EXT 121 位点**（0x400d08 `ext v0.16b,v0,v0,#8` + 0x408c94 簇 `ext v.16b,vN,vM,#15`）、MOVI 9、DUP 6、UZP1 2；INS/TBL/ZIP 仅在 libc 静态区。四臂映射：a=MOVI/MVNI imm 片段交换；b=EXT #imm（bits[14:11]，16b 域 0-15/8b 域 0-7）±1 旋转 + DUP lane index 旋转；c=EXT/UZP/ZIP/TRN/TBL 的 Rn↔Rm 互换（bits[20:16]↔bits[9:5]）；d=上一条 lane mask（CHAOSDecode 1-entry 历史槽）——app 面无 INS/lane-mask 指令，预期诚实 0 激活（W9 NEON-LaneProbe 属 P2）。**谓词设计点**：c 臂纯源互换改变序号序列顺序，U4 顺序敏感谓词会误拒——c 臂用排序后（multiset）比较，a/b/d 保持序列比较。表照 U4 惯例 GNU-as 闭环对表后再进 .cc。
  - **FR08（R46，Rename，4 臂）→ 新钩子 `DynInst::setRegOperand`（void* 重载，dyn_inst.hh:1235）**：dest VecRegClass 时 prevDestIdx(idx)→cpu->getReg(prev_phys) 可取旧版本容器（实证该写点 = 结果→PRF 唯一路径，cpu->setReg→physRegFile）。A64 语义事实：S/D 标量 FP 写零扩展未写位（zero 语义）、INS 读改写保留（preserve 语义）——两语义并存可换值。四臂：a=preserve→zero（INS 族未写 lane 清零）；b=zero→preserve（标量 FP 写上 64/96 位换旧值）；c=merge 换值（全宽写部分 lane 保留旧值）；d=新旧 lane 错误拼接（未写 lane 取旧值但旋转错位）。载体：cpu.hh 加 chaosVecMerge 式指针+setter（lsqFwd 自挂惯例）；部分宽度判定经 opClass/StaticInst。工作负载面：gap app d 形 FMUL/FADD 4 位点已证执行（FD05a 用的 0x400814 同面）；rob_fill_fp 3 位点在未执行 libc 区。
  - **FB06（R54，Dispatch/ROB，3 臂）→ CHAOSROB 扩展 + 两钩子**：c=动态指令ID 配对换值挂 inst_queue.cc:842 processFUCompletion（FUCompletion 是"放行执行"信号，值在 executeInsts:1274 才算——实证）+ 完成事件登记表（:989 创建时记录 seqNum→DynInst、process 注销）：X 的事件放行 Y、Y 的事件欠账放行 X（真交换：双完成错序，无死锁无双发，对应 03 表"早完成/永不完成"与"静默交换"两面）；b=目的 tag 配对换值挂同一 setRegOperand 钩子——X 的结果写 Y 的 dest physreg（Y=ROB instList 在飞 FP/SIMD 有有效 dest 非squashed，经 cpu->chaosROB 扫描）→ X 自己 physreg 陈旧+Y 静默换值双面；**a=ROB index 配对换值恒等问题**：gem5 DynInst 无 robIdx 字段（identity=seqNum 与 ROB 槽位 1:1），a 与 c 同一钩子——如实注记 a=arch-alias-of-c（审计行注明，不造假模式；U3 FB08-b arch-n/a 先例）。触发条件 ≥2 FP/SIMD 在飞（候选集空=诚实跳过）。
  - **Step 4 工作负载修正（计划即事实）**：dep_chain_vec 全 FMLA（1056 位点普查）对 FD07 零合格位点、对 FR08 无部分宽度写——两态验证改用 **gap**（FD07 EXT app 位点 + FR08 d 形标量 FP 已证执行）+ **rob_fill_fp**（FB06 FP 密集在飞≥2 常态）；下文 Step 4 原文的 dep_chain vec golden 说明按此替换，gap golden=2ec8c1e59f2808c5（已复核）。
- [ ] **Step 2:** 实现三模型子模式。
  - **2026-10-09 用户指令暂停冻结（恢复点在此）**：GNU-as 闭环推导完成约 80%——FD07 五族编码规则**全部实证推导完毕**（EXT/UZP+ZIP 合并行/TBL+TBX/DUP/MOVI 掩码+字段位+域，见 `runs/ooo-node/evidence/u5-step2-frozen/FREEZE-NOTES.md`，含 u5derive.py/u5rules.py 草稿/u5verify.py 脚手架/probe 语料）。恢复顺序：完成 u5verify.py 闭环 ALL-PASS → 程序化生成 C++ VecStitchRule 表 → 三模型实现（挂点见 Step-1 注记）→ 本步收尾。节点已释放（dkill 1773145/1823682，cn22986）、session cron 已取消。
- [ ] **Step 3:** guard 包裹增量编译 → `scons: done`。
- [ ] **Step 4:** 两态验证（工作负载按 Step-1 修正：gap（FD07 EXT/FR08 标量 FP）+ rob_fill_fp（FB06 在飞密集）；gap golden=2ec8c1e59f2808c5、rob_fill_fp golden=85085fd5686d173b 均已复核；开启态逐臂证据）。W9 NEON-LaneProbe 深验证属 P2（探针负载未开发）。
- [ ] **Step 5:** ooo_models.py 更新 + `--check`。
- [ ] **Step 6:** 提交 `[OOO][P1][U5] FD07/FR08/FB06 拼接配对族 + 向量两态实测`。

### Task U6：decode 卡死（D09）

**Files:** 载体 `CHAOSDecode*.hh/.cc`；配置/dispatch/schema/validate/models 同步。

**Interfaces:** Consumes chaos_trigger F5（持续性）语义；Produces `--decode_stuck <bit>` 模式（输出位 stuck-at 跨译码事件持续）。

**规格:** D09=译码输出某位 stuck-at（跨多条指令持续翻转/固定），区别于 D01 单次瞬态。复用 F5（maxFaults 窗口持续）触发；证据须含"多指令命中同一位"的持续性记录（命中指令数 ≥2 的计数器）。

- [ ] **Step 1:** 读 03 表 D09 + chaos_trigger.hh F5 语义。
- [ ] **Step 2:** 实现 stuck-at 持续模式 + 持续性计数器。
- [ ] **Step 3:** guard 包裹增量编译 → `scons: done`。
- [ ] **Step 4:** 两态验证：关闭态 golden；开启态证据日志 `stuck_hits >= 2`（若负载译码窗口内同一位仅命中一次 → 记录 eligible 不足，换 rob_fill 长负载重试，仍不足则如实记录）。
- [ ] **Step 5:** ooo_models.py 更新 + `--check`。
- [ ] **Step 6:** 提交 `[OOO][P1][U6] D09 decode 输出位 stuck-at 持续模式`。

### Task U7：双翻分层批次（D02 R02 B02 FD02 FR02 FB02）

**Files:** 载体=各单元既有单翻注入器（D01/R01/B01/FD01/FR01/FB01 路径）加第二 bit + 距离分层参数；配置/dispatch/schema/validate/models 同步。

**Interfaces:** Consumes 既有单翻实现（已实现 9 中的 D01/FD01/FR01/R01/FB01→B01 需确认载体）；Produces `--dual_flip {adjacent,nonadjacent,crossfield}` 分层子模式。

**规格:** 双 bit 翻转分层——相邻（bit 距离 1）/非相邻（距离 ≥2 同字段）/跨字段（两 bit 不同字段）。每子模式的 bit 距离统计入证据日志。

- [ ] **Step 1:** 读 03 表六模型双翻条目 + 既有单翻源码挂点注记。
- [ ] **Step 2:** 实现双翻 + 距离分层。
- [ ] **Step 3:** guard 包裹增量编译 → `scons: done`。
- [ ] **Step 4:** 两态验证 ×6 模型（每模型选一个子模式实测；bit 距离统计输出引用）。
- [ ] **Step 5:** ooo_models.py 更新 + `--check`。
- [ ] **Step 6:** 提交 `[OOO][P1][U7] 双翻分层：D02/R02/B02/FD02/FR02/FB02`。

### Task U8：换值变体批次（D03-c D04-c/e D05-b/d FD03-d FR03-c R03-c）

**Files:** 载体=对应单元既有注入器（Decode/Rename/Reg/FreeList 族）加换值变体模式；配置/dispatch/schema/validate/models 同步。

**Interfaces:** Consumes 既有 D03/D04/D05/FD03/FR03/R03 部分实现（09 审计"部分"态）；Produces 变体子模式 flag（src 互换/x0 替换/循环移位/上一条 imm 复用/跨 FU 路由）。

**规格:** 六个换值变体子模型——D03-c=源操作数互换；D04-c/e=x0 替换与循环移位变体；D05-b/d=上一条立即数复用与跨 FU；FD03-d/FR03-c/R03-c=各单元对应变体。变体=保持合法性的换值（区别于 bit 翻转）。

- [ ] **Step 1:** 读 03 表六子模型条目 + 09 审计中这六项的"部分"缺口描述，列挂点注记。
- [ ] **Step 2:** 实现六变体。
- [ ] **Step 3:** guard 包裹增量编译 → `scons: done`。
- [ ] **Step 4:** 两态验证 ×6（定向断言：注入点打印 原值→换值 映射，与预期变体语义一致）。
- [ ] **Step 5:** ooo_models.py 更新 + `--check`。
- [ ] **Step 6:** 提交 `[OOO][P1][U8] 换值变体：D03-c/D04-c,e/D05-b,d/FD03-d/FR03-c/R03-c`。

### Task U9：ROB/IQ 面缺口批次（B03-b,c B04-b,d B05-b,d B06-c,d B07 B10-c,d FB03 FB04-c FB10 FR04-b FD04-c FD06-b,c）

**Files:** 载体 `CHAOSROB*.hh/.cc` + `CHAOSIQ*.hh/.cc` + FPU/分支对应面；配置/dispatch/schema/validate/models 同步。

**Interfaces:** Consumes U1 表 + 03 表逐条原文；Produces 逐项三态记录（实现/近似/BLOCKED-no-hook）。

**规格:** ROB/IQ 面的部分态缺口（共 15 子项）。**每项先读 03 表原文**：vendored O3 核（cpu/o3/rob.hh iq.hh）有对应钩子则实现；无钩子且语义必须内核态改变的，按 03 表原文裁 BLOCKED-no-hook（显式记录，不打勾）——但 BLOCKED 需在清单层生成 Decision Request（该模型对应 ITEM 的 pilot 覆盖缺口）。

- [ ] **Step 1:** 逐项读 03 表 + rob.hh/iq.hh 钩子可达性分析，产出 15 项三态预判表（入执行注记；预判 BLOCKED 的项给出具体缺失钩子名）。
- [ ] **Step 2:** 实现"实现/近似"项。
- [ ] **Step 3:** guard 包裹增量编译 → `scons: done`。
- [ ] **Step 4:** 两态验证（每实现项一次；BLOCKED 项记录 Decision Request 到 findings.md）。
- [ ] **Step 5:** ooo_models.py 更新（impl_status 三态如实）+ `--check`。
- [ ] **Step 6:** 提交 `[OOO][P1][U9] ROB/IQ 面缺口：N 实现 / M 近似 / K BLOCKED（明细）`。

### Task U10：L0–L5 观测链 + 分类器收口

**Files:**
- Create: `tools/ooo_observe.py`（L0–L5 事件归一：从各注入器 evidence 日志 + simout + stats.txt 提取 attempted/eligible/activated/首检/主结局/simfail）
- Modify: `tools/classify.py`（OOO 轨道守恒断言：attempted ≥ eligible ≥ activated；结局分类序固定）
- Test: `tools/tests/test_ooo_classify.py`（独立脚本）

**Interfaces:**
- Consumes: 各注入器 evidence 日志格式（U2–U9 约定：每注入器 summary 行 `attempted=N eligible=N activated=N`）+ CHAOSCommitTrace/CHAOSMicroSnap（首检/主结局）。
- Produces: `classify_ooo_run(outdir) -> {L0..L5, verdict, conservation_ok}`；U11 campaign 引擎每样本调用。

**规格:** 总方针 §4 统一观测链——L0 触发面（eligible/activated）；L1 单元内部状态（与无故障影子逐事件比较）；L2 rename 合法性；L3 执行结果；L4 首个错误 commit；L5 检测层级与结局。守恒：分类计数与 gem5 证据一致（G5 证据口径）；首检=首个 L4 偏差；主结局∈{Masked, SDC, Crash/Detected, Timeout}。

- [x] **Step 1:** 写失败测试：`tools/tests/test_ooo_classify.py` 构造 4 个 fixture 目录（clean/Masked/SDC/守恒破坏），断言分类与守恒检测。——2026-10-08 实测：130 行独立脚本，6 fixture（4 必需 + 诚实加测 T5 abort 合法性、T6 确定性交叉），共 19 断言。
- [x] **Step 2:** 运行确认失败（classify_ooo_run 不存在）。——实测：`ModuleNotFoundError: No module named 'ooo_observe'` RC=1（红态）。
- [x] **Step 3:** 实现 `tools/ooo_observe.py` + `tools/classify.py` 扩展。——实测：ooo_observe.py 334 行（collect_l0：21 个 runner 已知日志名 × 3 正则（CHAOS_L0_FUNNEL/CHAOS_L0/faults_injected）+ faults_for_classify 严格活性证据优先级 funnel_activated>l0_hit>legacy_injected>none；observe_run：exit.rc 缺失即 verdict=None 诚实拒判；ref 门控 L1-L4 组装 commit_diff/micro_diff；CLI --json）。classify.py +81 行：check_conservation（attempted≥eligible≥injected≥activated，逐注入器+TOTALS，对齐 chaos_l0.hh 四计数 pinned 格式）+ check_verdict_l0_consistency（Inactive/activated 与 checksum!=golden 交叉、abort 合法性）。单向 import ooo_observe→classify 无环。
- [x] **Step 4:** 测试通过（4/4 PASS，输出引用）。——实测：`SELFTEST PASS (19 checks, 0 failed)` RC=0（F1 Inactive/F2 Masked/F3 SDC/F4 守恒破坏命名注入器+关系/T5 SimulatorError+absent 合法/T6 Inactive+checksum!=golden 违规）。回归：test_ooo_guard_f025.py `SELFTEST PASS (12 checks, 0 failed)`、micro_diff --self-test `11/11 checks PASS`、classify+ooo_observe 导入 OK；`import runner` 失败系 login01 无 pyyaml（环境既有，非本改动引入）。
- [x] **Step 5:** 实机端到端（off-state 真实版 + 开启态诚实延期至 U2 Step 4b）：sdc+compat 双跑 `/tmp/u10-e2e-{a,b}`（smoke/O3，`--chaos_ctrace --chaos_msnap`，各 rc=0，FINAL=45737cc9a76c0dce==golden）。实测①：`python3 tools/ooo_observe.py /tmp/u10-e2e-a --golden 45737cc9a76c0dce` → L0 evidence=absent（off 态无注入日志，与 F1 语义一致）、L5 verdict=Inactive、conservation OK、RC=0。实测②：加 `--ref-outdir /tmp/u10-e2e-b` → L1 no_divergence=True、L2 hash_table_consistent=True、L3 commit_verdict=no_divergence（五类分歧全 0、tick_max_drift=0、无截断）、L4 无首检（同构确定性）。**开启态 L0 计数核对因 U2 未实现（gated on U1c 重建）延期**，已作为 U2 Step 4b 交接项落计划。
- [x] **Step 6:** 提交 `[OOO][P1][U10] L0–L5 观测链 + 守恒分类器 + 4 fixture 单测`。——2026-10-08 补勾（记录修正）：commit `9f4a6946`，提交时复选框漏勾。

### Task U10b：legacy 证据一致性修正（U11 冒烟暴露的 U10 缺陷）

**Files:**
- Modify: `tools/classify.py`（`check_verdict_l0_consistency`：「已落位故障数」按 collect_l0 同源严格优先级取数——funnel→`totals.activated` / l0→`l0_hit_total` / legacy→`legacy_injected_total` / absent→0；现实现恒读 funnel 专用 `totals.activated`，legacy/l0 路径全错）
- Test: `tools/tests/test_ooo_classify.py`（新增 legacy-only fixture：Masked+legacy 无违规【现红：假阳性】、Inactive+legacy_injected=1 有违规【现红：对称假阴性漏报】）

**Interfaces:**
- Consumes: `ooo_observe.collect_l0` 的 l0 dict（`evidence`/`totals`/`l0_hit_total`/`legacy_injected_total`——classify.py 顶部 shape 注释同步扩展两键）。
- Produces: 同签名 `check_verdict_l0_consistency(verdict, l0, checksum, golden)`；funnel 路径行为不变（既有 6 fixture / 19 断言全数保持为回归锚）。

**背景（2026-10-08 U11 Step 3 实机冒烟实证）:** 样本 seed 6566880900823253577（D01-F0-W6，decode opcode_bitflip，ret→hint bit25，rc=0，checksum==golden）verdict=Masked、l0 evidence=legacy、`legacy_injected_total=1`，却被记 `conservation_ok=false` + 违规 "Masked verdict (fault landed) but L0 activated=0"——legacy 日志（decode_injections.log `faults_injected: 1`）语义即「已施加」，分类器 feed（`faults_for_classify` 用 legacy_injected_total）与一致性检查读数（funnel activated）不同源 → 假阳性。对称假阴性：Inactive + legacy_injected=1（注入器说注入了、分类器却判 Inactive——真撒谎）现漏报。同批冒烟另有两处 U11 引擎自身缺陷（`&& echo` 短路丢 exit.rc；`--outdir` 多套一层 m5out/ 致 L0 证据错位）——属未提交的 U11 新代码，修在 U11 内，不立单元。

- [x] **Step 1:** 写失败测试：test_ooo_classify.py 加 legacy-only 2 fixture → 运行确认红（引用输出）。——实测红：`FAIL T7 legacy Masked not a violation | ['Masked verdict (fault landed) but L0 activated=0']`、`FAIL T8 Inactive+legacy_injected=1 flagged`、`FAIL T9 l0-hit Masked not a violation`，`SELFTEST FAIL (26 checks, 3 failed)`（T7 精确复现实机假阳性；T8 复现漏报）。（实际加了 3 fixture：T7 走 classify_ooo_run 真实链、T8 纯函数直调钉对称假阴性、T9 钉 l0-hit 路径。）
- [x] **Step 2:** 修 `check_verdict_l0_consistency` 按证据源取数 + shape 注释扩展 → 测试绿 + 既有 19 断言回归（引用输出）。——实测绿：`SELFTEST PASS (26 checks, 0 failed)`（新增 `_landed_faults()`：funnel→totals.activated / l0→l0_hit_total / legacy→legacy_injected_total，与分类器 feed 同源）；回归 `test_ooo_guard_f025.py SELFTEST PASS (12 checks, 0 failed)`、`ooo_campaign --selftest SELFTEST PASS (23 checks, 0 failed)`、micro_diff 11/11、classify+ooo_observe 导入 OK。
- [x] **Step 3:** 实机复验：显式删除缺陷观测产物 `sample_000001_5b223f62efde0249_acda5eee5b0d`（DELETED 留痕文件追加记），`--resume --samples 2` 只重跑该样本 → Masked、conservation_ok=true、violations=[]（引用输出）。——实测：`CAMPAIGN SUMMARY ooo-p1 engineering D01-F0-W6: ran=1 skipped-complete=1 verdicts={"Masked": 1}`；新 observation.json：`verdict=Masked`、`conservation_ok=True`、`violations=[]`、checksum==golden 确定性复现；样本 0（Crash，旧代码下观测即正确）保留跳过。
- [x] **Step 4:** 提交 `[OOO][P1][U10b] legacy 证据一致性修正：verdict/L0 交叉检查按证据源取数（U11 冒烟实证假阳/假阴对称修复）`。——commit `3a142d0c`。

### Task U11：Campaign 引擎 `tools/ooo_campaign.py`

**Files:**
- Create: `tools/ooo_campaign.py`
- Modify: `schemas/manifest.schema.json`（component enum 补 `"decode"`——`manifest_validate.py` COMPONENTS_MAPPED 已于 2f4d364a 含 decode，schema JSON 文件落后 6 项，本单元只补 decode 一项，其余漂移另行记录）
- Modify: `tools/manifest_validate.py`（顶层 `import os, sys, json, yaml` 拆懒加载——login01 无 pyyaml 而 yaml 仅 `_selftest` 样例加载用；campaign 引擎必须在 login01 import 此模块，否则其"stdlib-only"docstring 是谎言）
- Test: 内置 `--selftest`（fixture 模式）+ 实机冒烟

**Interfaces:**
- Consumes: `tools/ooo_models.py`（U1）· `tools/ooo_guard.py`（4 槽 + guard_pid U1b）· `tools/ooo_recover.py`（mark_complete/scan）· `tools/ooo_observe.py`（U10）· 完整任务执行清单.md。
- Produces: CLI——`--item ITEM-xxx --phase {engineering,pilot,screening,confirmatory} --samples N [--sample-index i] [--resume]`；每样本：seed=`SHA256("ooo-fi-v1|"+RunID+"|"+phase+"|"+sample_index)` 低 64 位；run_key=`campaign/phase/RunID/sample_index/seed/config_sha`；manifest 不可变（写后即校验）；输出 `tmp/<run_key>/` → 原子移入 `runs/ooo/<run_key>/` + COMPLETE.json；心跳；资源日志。
- **F-008/F-011 硬约束（2026-10-08 U1c 修订）：gem5 调用经 loader 自动探测**——`OOO_GEM5_BIN`（缺省 `build/ARM/gem5.opt`）：先探测原生（`<bin> --help` 且清掉 PYTHONHOME → rc==0 即原生直执行，U1c 重建完成后应为常态；gem5 v25 无 --version 选项，rc=2，实证）；失败回退兼容 loader（`OOO_COMPAT_DIR` 缺省 lsu_keeper/compat：`PYTHONHOME=$C $C/lib/ld-linux-aarch64.so.1 --library-path $C/lib64:/usr/lib64 <bin>`）；两者皆败 → 显式 BLOCKED 退出，绝不静默降级。原生探测必须显式 unset PYTHONHOME（F-011：3.9 二进制 + 3.11 PYTHONHOME 崩溃）。

- [x] **Step 1:** 写 `--selftest`：fixture manifest 生成（seed 公式断言：`int(sha256("ooo-fi-v1|D01-F0-W3|pilot|7").hexdigest()[:16],16)` 与引擎输出一致）、run_key 唯一性、tmp→原子落位、mark_complete 拒绝篡改。——ooo_campaign.py 854+ 行：T1-T24（seed 公式 3 常量、run_key 唯一性+config 漂移敏感、manifest 经真实 manifest_validate 校验（component=decode）、loud-reject F1/D02/W3/bogus item、假 gem5 全生命周期（staging→原子落位→COMPLETE 绑定→legacy L0）、write-once 跳过+非 COMPLETE 替换+mark_complete 拒绝、命令镜像 runner.py:1276 decode 分发、guard 拒绝→blocked-guard 不落位【T21，缺陷③修复后加】）。
- [x] **Step 2:** 运行 `python3 tools/ooo_campaign.py --selftest` → 全 PASS（输出引用）。——`SELFTEST PASS (24 checks, 0 failed)`（缺陷③修复前 23/23；修复后含 T21 blocked-guard 共 24/24）。
- [x] **Step 3:** 实机冒烟：`--item ITEM-002（D01-F0-W6，coremark 已实现模型） --phase engineering --samples 2`，经 guard 4 槽之一执行，产出 2 个 COMPLETE 目录 + L0 证据。预期：2/2 COMPLETE，resume 重跑 0 新增（跳过已完成）。——首轮冒烟暴露 3 真实缺陷并修复：①inner script `&& echo` 短路丢 abort 的 exit.rc（改 `;` 恒记录）；②`--outdir` 多套 m5out/ 致 L0 证据错位（改直指 run 目录，对齐 runner 惯例）；③guard 门禁拒绝被误记 verdict=None COMPLETE（run-finish 正向证据判定，blocked-guard 大声中止 exit 2——实机复验：陈旧槽下 `campaign exit=2`、无落位）。缺陷产物样本已按 write-once 惯例显式删除并留痕（DELETED-DEFECTIVE-2026-10-08.md 三段）。修复后 2/2 COMPLETE：sample 0 `verdict=Crash rc=134 l0=legacy`（and→orr bit29 传播→Page table fault @0，OOO 轨首例架构级 Crash）、sample 1 `verdict=Masked rc=0 l0=legacy`（ret→hint bit25，checksum==golden）；resume 复跑 `ran=0 skipped-complete=2` ✓。U10b 插曲：样本 1 旧观测带 legacy 假阳性（conservation_ok=false），U10b 修复后删除重跑→`conservation_ok=True violations=[]`。后续中断测试顺带产出样本 2-6（Masked×3 + Crash×1 + Masked，全部 COMPLETE、violations=[]）——超出计划最小样本数，系中断测试需新鲜样本所致，engineering 阶段合法数据。
- [x] **Step 4:** 人为中断恢复实测：启动 `--samples 4`，中途 kill（TERM 自身 PGID），`python3 tools/ooo_recover.py` 确认 RUNNING→INTERRUPTED，`--resume` 后 4/4 COMPLETE 且已 COMPLETE 样本未重跑。——以 `--samples 8 --resume`（7 已 COMPLETE + 样本 7 新跑）等价执行，全链实测：①launch 后 33s 心跳在位；②TERM campaign PGID 902005 + 孤儿目标组 902282（guard 拓扑：目标自成 pgid，须单独清）；③scan 即时 `[RUNNING] ... heartbeat_age=7s 共 1 项: RUNNING=1`（14:36:46）；④心跳冻结 14:36:39.596，600s 阈值后 scan `[INTERRUPTED] ... heartbeat_stale(610s > 600s) 共 1 项: INTERRUPTED=1`（14:46:49，/tmp/u11-interrupted-scan.log）；⑤kill 遗留 guard 陈旧槽按设计处置：验证 902279/902282/902005 死透 → `clear-stale --confirm-dead-pid 902279` → 4 槽全空；⑥`--resume` → `COMPLETE sample_000007 verdict=Masked rc=0 l0=legacy` + `CAMPAIGN SUMMARY ran=1 skipped-complete=7 verdicts={"Masked": 1}`（/tmp/u11-resume.log）；⑦落盘 8/8 COMPLETE（sample_000000..000007 逐目录核验），样本 7 observation：L5.verdict=Masked（checksum==golden 000000000000cf56）、L0 evidence=legacy legacy_injected_total=1、conservation_ok=true violations=[]；⑧被中断 staging 902005 由 resume 自动替换清除（剩余 1008380 为本次 campaign staging，已清空）。附：首次演练 pgrep -f 经 reach 匹配包装进程自杀（F-012），改 staging 目录名定位后干净双杀。
- [x] **Step 5:** 提交 `[OOO][P1][U11] campaign 引擎：seed/manifest/run_key/原子落位/guard/recover 全链 + 中断恢复实测`。——commit `6505d9b1`（2026-10-09 暂停清点时补勾：提交时复选框漏勾，U10 Step-5 先例；U3/U4 均在其后提交故不构成顺序问题）。

### Task U12：P1 收口

**Files:**
- Modify: `docs/gem5-fi/ooo/task_plan.md`（P1 七项检查单勾选 + G0-02 状态）
- Modify: `docs/gem5-fi/ooo/findings.md` / `progress.md`
- Modify: `tools/ooo_models.py`（终态 impl_status）

**Interfaces:**
- Consumes: U0–U11 全部证据。
- Produces: G0-02 填表（57 模型映射 + 确定性测试证据）；P1 检查单七项状态。

- [ ] **Step 1:** 确定性测试：同一 ITEM 同一 sample_index 跑 2 次（不同 wall 时间），断言分类/verdict/FINAL 全一致（引用两次输出）。
- [ ] **Step 2:** 重复 seed 测试：同 seed 不同 run_key 路径重跑，结果一致（引用）。
- [ ] **Step 3:** 入口守卫强制：去掉 guard 直接调引擎内部接口应被拒绝（或引擎唯一入口即经 guard——验证命令引用）。
- [ ] **Step 4:** G0-02 填表：`python3 tools/ooo_models.py --check` 输出 + impl_status 终态统计（预期 implemented+approx+blocked_by_dr = 57，逐项对账 09 审计）。
- [ ] **Step 5:** task_plan P1 检查单勾选（含"每次只启用清单指定子模型"的证据=U11 manifest 单模型断言）。
- [ ] **Step 6:** 提交 `[OOO][P1][U12] P1 收口：确定性/重复seed/守卫强制/G0-02 填表`。

---

## 验证总则

- 每个 Unit 的验证命令在 login01 真实执行并引用实际输出；不通过不得 commit（CLAUDE.md 自验证铁律）。
- 回归锚：每次 C++ 增量编译后跑一次无注入 smoke（FINAL=45737cc9a76c0dce），证明平台未被破坏。
- 家族单元（U2–U9）的"探针深验证"（W3/W8/W9/W13 专属负载）显式属 P2；本计划内以既有负载两态实测为准。
- 每 Unit 完成即 commit+push（bundle 通道）；远程移动时暂停分析→rebase→复验→再推。
- 进度跟踪：每 Unit 开始/完成更新本文件复选框 + progress.md（30 分钟节奏）。

## Self-Review 记录（2026-10-08）

- 规格覆盖：task_plan P1 七项 → U0/U1（映射表）、U2–U9（故障族实现+单因素）、U10（L0–L5/首检/主结局/simfail/守恒）、U11（seed/manifest/run_key/临时目录/COMPLETE/心跳/恢复）、U1b+U11（资源锁入口强制）、U12（确定性/重复 seed/测试）。✔
- 占位扫描：无 TBD/TODO；家族单元的规格引用 03 表原文（U0 入库后为可读规格，符合"spec travels with the plan"）。✔
- 类型一致性：`_lock_owner_pid`（U1b）、`MODELS`/`--check`（U1）、`classify_ooo_run`（U10）、`--item/--samples/--resume`（U11）跨单元引用一致。✔
- 已知风险：U9 BLOCKED 项会留 G0-02 缺口 → Decision Request 流程已定义；U2 时序扰动可能需 O3 核新钩子 → 挂点注记先行，不可行即按 U9 同款三态处理。
