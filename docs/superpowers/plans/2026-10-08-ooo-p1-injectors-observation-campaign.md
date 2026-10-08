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
- Consumes: chaos_trigger.hh F0–F5（时序扰动用 F2 窗口/F5 持续语义）；U1 映射表。
- Produces: 每模型子模式 flag（如 `--chaos_decode --decode_timing early|late|dup|drop`），U10 观测链可从 simout 证据日志读 attempted/eligible/activated。

**规格（03 表原文为准）:** D07=译码事件时序（提前/延后/丢失/重复）；R08=RAT 更新时序；FD09/FR09=FP 流水对应面。实现优先在既有 decode/rename 钩子内加事件移位/复制/丢弃逻辑，不新增 SimObject 时先复用 CHAOSDecode/CHAOSRenameMap 载体。

- [ ] **Step 1:** 读 03 表四模型条目 + CHAOSDecode/CHAOSRenameMap 现有源码，列出每子模式的挂点与数据流（写入本任务执行注记，提交附）。
- [ ] **Step 2:** 实现四模型子模式（每模型独立可关）。
- [ ] **Step 3:** 增量编译（guard 包裹）：`python3 tools/ooo_guard.py run --type build --desc u2-build --log /tmp/u2-build.log -- bash -c 'cd CHAOS/gem5 && scons -j8 build/ARM/gem5.opt'` → 预期 `scons: done`（引用尾行）。
- [ ] **Step 4:** 两态验证（每模型 × 注入关闭/开启，dep_chain int，golden=98e5e31e726e383f）。**前置 U1c：重建产物原生直跑（无 loader 前缀）**：
```bash
cd /home/share/suke/wangxu/gem5-fi-ooo
# 关闭态（不带注入 flag）→ FINAL=98e5e31e726e383f（golden 匹配）
build/ARM/gem5.opt --outdir=/tmp/u2-off configs/se/ooo_proxy.py --cmd workloads/ooo/dep_chain/dep_chain --cpu O3
# 开启态（示例 D07-early）→ 证据日志含 attempted/eligible/activated 计数，FINAL 偏离或 Masked
build/ARM/gem5.opt --outdir=/tmp/u2-on configs/se/ooo_proxy.py --cmd workloads/ooo/dep_chain/dep_chain --cpu O3 \
  --chaos_decode --decode_timing early --decode_max_faults 1 --decode_rng_seed 42
```
预期：关闭态 FINAL 与 golden 一致；开启态 simout/注入器 summary 含 `attempted>=1` 且分类非 clean（或显式 activated=0 时记录 eligible 不足，不得伪造激活）。
- [ ] **Step 4b（U10 交接）:** 首个 on-state outdir 跑 `python3 tools/ooo_observe.py <outdir> --golden <golden> --ref-outdir <同模型 off 态 outdir>` → L0 funnel 计数与注入器 summary 行一致、faults_source=funnel_activated、verdict 与实测结局相符——U10 的开启态验证在此收口。
- [ ] **Step 5:** ooo_models.py impl_status 更新四模型 + `--check` 仍 310/310。
- [ ] **Step 6:** 提交 `[OOO][P1][U2] 流水时序族A：D07/R08/FD09/FR09 子模式 + 两态实测`。

### Task U3：流水时序族 B（B08 B09 FB08 FB09）

**Files:** 同 U2 模式，载体 `CHAOSROB*.hh/.cc`（B08/B09：squash/commit 时序扰动）+ FPU 路径（FB08/FB09）；配置/dispatch/schema/validate/models 同步。

**Interfaces:** Consumes U2 的 timing_mode 参数族约定；Produces squash/commit 时序子模式 flag。

**规格:** B08=ROB squash 时序（提前 squash/延迟 squash/squash 丢失导致的假活）；B09=commit 时序；FB08/FB09=FP 对应面。验证负载用 rob_fill int（golden=19eab7d0de27237e，深 ROB/连续 mispredict 特性对口）。

- [ ] **Step 1:** 读 03 表四模型 + CHAOSROB 源码，列挂点注记。
- [ ] **Step 2:** 实现四模型子模式。
- [ ] **Step 3:** guard 包裹增量编译 → `scons: done`。
- [ ] **Step 4:** 两态验证（rob_fill int，关闭态 FINAL=19eab7d0de27237e；开启态 attempted>=1 证据）。
- [ ] **Step 5:** ooo_models.py 更新 + `--check` 310/310。
- [ ] **Step 6:** 提交 `[OOO][P1][U3] 流水时序族B：B08/B09/FB08/FB09 子模式 + 两态实测`。

### Task U4：控制状态换值族（D06 FD05）

**Files:** 载体 `CHAOSDecode*.hh/.cc`（D06：sf/S/shift/extend/signed 控制位换值）+ FP decode 路径（FD05：scalar↔vector/element-width 合法组合换值）；配置/dispatch/schema/validate/models 同步。

**Interfaces:** Consumes U1 表 + chaos_trigger F0/F1；Produces `--decode_ctl_swap <field>` / `--fp_ctl_swap <mode>` 子模式 flag。

**规格:** D06=译码控制字段换为另一合法值（N/Z/C/V 标志语义、移位类型 LSL↔LSR↔ASR↔ROR、extend 类型、signedness）；FD05=FP 标量↔向量/元素宽度合法组合互换（保持指令合法，制造语义级偏差——预期 SDC 倾向而非 Crash）。

- [ ] **Step 1:** 读 03 表两模型全部子模式条目；用 GNU as 对表验证每个换值组合仍是合法编码（`aarch64-linux-gnu-as` 不在集群，用 host `gcc -c` + objdump 反汇编对表；产出对表清单入执行注记）。
- [ ] **Step 2:** 实现（合法值域表驱动：每控制字段的合法值枚举 + 换值映射）。
- [ ] **Step 3:** guard 包裹增量编译 → `scons: done`。
- [ ] **Step 4:** 两态验证（dep_chain int 关闭态 golden；开启态每子模式一次，验证换值后指令仍合法提交且结果偏差被 L1 层捕获）。
- [ ] **Step 5:** ooo_models.py 更新 + `--check`。
- [ ] **Step 6:** 提交 `[OOO][P1][U4] D06/FD05 控制状态合法换值 + GNU 对表`。

### Task U5：拼接/配对族（FD07 FR08 FB06）

**Files:** 载体 NEON/shuffle 路径（FD07：shuffle/lane-mask 元数据）+ FP 完成事件（FR08）+ BPU/分支面（FB06：preserve-zero-merge 配对）；配置/dispatch/schema/validate/models 同步。

**Interfaces:** Consumes U1 表；Produces lane 元数据与完成事件配对子模式 flag。

**规格:** FD07=向量 shuffle/lane-mask 拼接元数据故障；FR08=FP 完成事件配对（source/dest 配对断裂）；FB06=分支融合 preserve-zero-merge 语义。NEON 掩码一律 64 位（Global Constraints）。

- [ ] **Step 1:** 读 03 表三模型 + 现有 FPU/向量路径源码，列挂点注记。
- [ ] **Step 2:** 实现三模型子模式。
- [ ] **Step 3:** guard 包裹增量编译 → `scons: done`。
- [ ] **Step 4:** 两态验证（dep_chain vec 关闭态 golden=b1e661a247b95774；开启态逐 lane 证据）。W9 NEON-LaneProbe 深验证属 P2（探针负载未开发，本单元用 dep_chain vec 的向量段）。
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
- [x] **Step 4:** 提交 `[OOO][P1][U10b] legacy 证据一致性修正：verdict/L0 交叉检查按证据源取数（U11 冒烟实证假阳/假阴对称修复）`。——本提交即 Step 4。

### Task U11：Campaign 引擎 `tools/ooo_campaign.py`

**Files:**
- Create: `tools/ooo_campaign.py`
- Test: 内置 `--selftest`（fixture 模式）+ 实机冒烟

**Interfaces:**
- Consumes: `tools/ooo_models.py`（U1）· `tools/ooo_guard.py`（4 槽 + guard_pid U1b）· `tools/ooo_recover.py`（mark_complete/scan）· `tools/ooo_observe.py`（U10）· 完整任务执行清单.md。
- Produces: CLI——`--item ITEM-xxx --phase {engineering,pilot,screening,confirmatory} --samples N [--sample-index i] [--resume]`；每样本：seed=`SHA256("ooo-fi-v1|"+RunID+"|"+phase+"|"+sample_index)` 低 64 位；run_key=`campaign/phase/RunID/sample_index/seed/config_sha`；manifest 不可变（写后即校验）；输出 `tmp/<run_key>/` → 原子移入 `runs/ooo/<run_key>/` + COMPLETE.json；心跳；资源日志。
- **F-008 硬约束：gem5 调用一律经兼容 loader 封装**（`OOO_GEM5_BIN` 环境变量缺省 `build/ARM/gem5.opt`，实际执行 `PYTHONHOME=$COMPAT $COMPAT/lib/ld-linux-aarch64.so.1 --library-path $COMPAT/lib64:/usr/lib64 $OOO_GEM5_BIN ...`；参考 LSU 轨道 U3' LSU_GEM5_BIN 已验证实现，读其 `tools/lsu_runner.py` 未提交 WIP 可借鉴但不抄代码）。

- [ ] **Step 1:** 写 `--selftest`：fixture manifest 生成（seed 公式断言：`int(sha256("ooo-fi-v1|D01-F0-W3|pilot|7").hexdigest()[:16],16)` 与引擎输出一致）、run_key 唯一性、tmp→原子落位、mark_complete 拒绝篡改。
- [ ] **Step 2:** 运行 `python3 tools/ooo_campaign.py --selftest` → 全 PASS（输出引用）。
- [ ] **Step 3:** 实机冒烟：`--item ITEM-002（D01-F0-W6，coremark 已实现模型） --phase engineering --samples 2`，经 guard 4 槽之一执行，产出 2 个 COMPLETE 目录 + L0 证据。预期：2/2 COMPLETE，resume 重跑 0 新增（跳过已完成）。
- [ ] **Step 4:** 人为中断恢复实测：启动 `--samples 4`，中途 kill（TERM 自身 PGID），`python3 tools/ooo_recover.py` 确认 RUNNING→INTERRUPTED，`--resume` 后 4/4 COMPLETE 且已 COMPLETE 样本未重跑。
- [ ] **Step 5:** 提交 `[OOO][P1][U11] campaign 引擎：seed/manifest/run_key/原子落位/guard/recover 全链 + 中断恢复实测`。

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
