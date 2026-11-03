# FSU：W5 suite 身份、逐元素 oracle 与 F5 永久故障（2026-11-03）

> 分支：`fsu`（唯一允许分支）。工作目录 `/home/sdc/gem5-fi-fsu`。
> ACTIVE FREQUENCIES = F0, F5；禁止任何新的 F1/F2/F3/F4 正式实验。
> 本计划每个任务 = 一个提交；gate 不计入 519。

## 0. 基线（开工前已核实）

- HEAD `016aeafd091793578fe651d2929515d1a66dfb24`，与 `origin/fsu` 同步，工作区 clean。
- FSU 测试：`python3 -m pytest tests/test_fsu_*.py tests/test_chaos_fsu_*.py -q` → **125 passed**。
- 历史视图 18/519 seed、6/173 RunID；活跃视图 9/240 seed、3/80 RunID。
- 18/18 历史正式 seed 离线审计通过（只读复验，不修改旧事件）。
- 服务器高负载：`kunpeng-stl-d010`（root）占用 86 核，loadavg 92。规则：
  loadavg > 16 或该进程仍高负载 → 禁止 scons / gem5 / 大规模 native golden；
  只做代码、文档、轻量 Python/host 单元测试。**不终止、不暂停、不干扰该进程。**

## 1. 权威裁决（写入版本化文档 + schema + 测试）

W5 是固定 5 程序 suite，程序顺序**永远**为：

```
gemm → 2mm → lu → cholesky → jacobi-2d
```

- `FSU-FP04-F0-W5` 正式计数仍为 **3 个 suite seed**；每个 suite seed 含
  **5 个 component run**；每个 component run 只跑 1 个程序、只注入 1 次故障，
  独立 census/golden/fault/oracle/传播链审计，独立报告 eligible/activated/
  terminal/oracle。
- 5 个 component 全部 admitted + audit.ok + 逐元素 oracle 通过 → suite seed
  才可认证；任一失败 → 整个 suite seed 不认证，成功 component 证据保留，
  重试新建 attempt，不覆盖。
- 3 个 suite seed = 15 个 component run，但正式计数只 +3；不得把 component
  数量误计为 seed 数量。
- Markdown 必须分别使用 **formal suite seed / component run / component fault**
  三个词，禁止用单个 PolyBench 程序冒充 W5。

### 任务 1：裁决文档 + suite schema（提交 1）
- [ ] 新增 `docs/gem5-fi/fsu/FP04-F0-W5-SUITE-RULING.md`：上述裁决全文、
      计数规则、失败重试规则、术语定义、与 173×3=519 / 80×3=240 的关系。
- [ ] 新增 `schemas/fsu_suite.schema.json`（draft-07）：suite_id、suite_version、
      program_order（固定 5 项）、programs、scale、compiler、oracle、
      suite_hash、program_count=5。
- [ ] 新增 `schemas/fsu_component.schema.json`：suite_id/suite_hash/suite_seed/
      program_id/program_index/program_count/component_attempt/
      component_manifest_sha256/component_{binary,source,golden}_sha256/
      component_status/eligible/activated/terminal/oracle。
- [ ] 测试：schema 必填/枚举/固定顺序；缺 program、重复 program、
      program_count≠5 必须拒绝。

### 任务 2：suite 身份与计数门禁（提交 2）
- [ ] `tools/fsu_suite.py`：
  - `PROGRAM_ORDER = ("gemm","2mm","lu","cholesky","jacobi-2d")`；
  - `compute_suite_hash(suite)`：SHA-256 over canonical JSON，字段严格为
    suite_id、suite_version、program_order、每程序 source/binary SHA、
    固定规模、compiler 版本与构建参数、oracle 版本；**不含**运行结果；
  - `derive_component_seed(suite_seed, program_id, policy_version)`：
    SHA-256(suite_id|suite_version|suite_seed|program_id|policy_version)
    取前 8 字节，0 映射为 1；测试保证 5 个派生 seed 互不相同；
  - `validate_suite_manifest` / `validate_component_manifest`：缺 component、
    重复 component、suite_hash 不匹配、program_index 不匹配、program_count≠5
    全部响亮拒绝；
  - `suite_seed_state(seed_dir)`：只有 `suite_manifest.json` + `audit.json.ok`
    + 5/5 component certified 才返回 admitted。
- [ ] `configs/fsu/suites/polybench-fp-v1.json`：固定顺序、五程序源码/规模/
     编译参数/oracle 版本；binary SHA 在构建后回填，构建前 `pending`。
- [ ] `tests/test_fsu_suite.py`：suite_hash 稳定、篡改任一身份字段必变、
      缺/重复 component 拒绝、派生 seed 确定且唯一。
- [ ] `tests/test_fsu_index.py` 增补：一个 suite seed（5 component）只计 1 seed。

### 任务 3：suite runner / suite audit / suite Markdown（提交 3）
- [ ] `tools/fsu_suite_runner.py`：
  - 对 suite seed 的 5 个程序按固定顺序分别调用
    `fsu_seed_runner.run_seed`，component seed 用任务 2 的派生值；
  - 每个 component 目录：`runs/fsu/<RunID>/seed<N>/components/<program_id>/
    <RunID>/seed<derived>/attempt-<k>/`；
  - component 失败保留 `.failed`，同一 suite seed 不写 `AUTHORITATIVE`；
  - 5/5 passed 后写 `suite_manifest.json`、`suite_report.json`、`audit.json`、
    `FSU-FP04-F0-W5-seed<N>.md`（suite 级，链接 5 个 component attempt），
    最后才写 `AUTHORITATIVE`；
  - 重复 component/缺 component/suite_hash 漂移 → 拒绝运行。
- [ ] `tools/fsu_index.py`：seed 目录含 `suite_manifest.json` 时按 suite
      seed 计数（1 个 seed），component 数量不进入 summary。
- [ ] `tests/test_fsu_suite_runner.py`：假 gemm5 下 5/5 通过计 1 seed；
      任一 component 失败 → suite 不 admitted；重试不覆盖旧 attempt；
      5 个 component 不等于 5 个 seed。

### 任务 4：五程序逐元素 oracle（提交 4）
- [ ] `workloads/ooo/polybench/utilities/gem5fi_oracle.h`（新）：
      `gem5fi_dump_array(path, ptr, count, elem_size)` 以**小端原始字节**写出，
      打印 `ARRAY_SHA256=<64hex> ARRAY_COUNT=<n> ARRAY_PATH=<path>`；
      路径来自 `--array-dump=<path>` 或 `POLYBENCH_ARRAY_DUMP`；
      输出数组域与现有 FINAL 完全相同（gemm C、2mm D、lu A、cholesky
      下三角、jacobi-2d A）。
- [ ] 五个 `*.c` 在 FINAL 块后加入 dump 调用（仅此一处新偏差，PROVENANCE 记录）。
- [ ] `tools/fsu_oracle.py`：读取 meta（dtype=fp32、shape、row-major、
      little-endian、count）、逐元素比较、abs/rel/ULP tolerance、
      mismatch_count/first_mismatch_index/max_abs_error/max_rel_error/max_ulp、
      golden/fault 数组 SHA-256；tolerance 必须在 fault 运行前预注册。
- [ ] `schemas/fsu_oracle.schema.json`。
- [ ] `tests/test_fsu_oracle.py`：形状不一致拒绝、逐元素定位、三种 tolerance、
      SHA-256 稳定、NaN/Inf 规则显式。
- [ ] Makefile 构建五个程序；构建后回填 `configs/fsu/suites/polybench-fp-v1.json`
      的 binary SHA 并重算 suite_hash。

### 任务 5：W5 无故障验证 gate（高负载解除后；不计 519）
- [ ] native 3 次 + gem5 B0 3 次 × 5 程序：
      - 数组形状一致、canonical SHA 稳定、mismatch_count=0、
        tolerance 配置固定、suite_hash 稳定；
      - 证据写入 `runs/fsu-gates/W5-ELEMENT-ORACLE-GATE/`，含 SHA256SUMS。
- [ ] 任一程序不满足 → F0-W5 保持 BLOCKED。

### 任务 6：F0-W5 正式 suite seed（高负载解除后）
- [ ] 顺序：seed1 五 component 全部 L0–L5 + audit.ok → 生成 suite Markdown
      → seed2 → seed3。
- [ ] 完成后 FSU-FP04-F0-W5 = COMPLETE_3_OF_3；
      历史 21/519、7/173；活跃 12/240、4/80。
- [ ] 任一程序失败 → PARTIAL/BLOCKED，不得用其余四个认证 suite。

## 2. F5：一个永久故障、多次 exposure

### 任务 7：F5 事件字段 + 链审计（提交 5）
- [ ] `tools/fsu_prop_fields.py` 增加字段：install_event、stuck_polarity、
      fixed_mask、first_eligible_sn、exposure_id、exposure_count、
      activated_exposure_count、first_activated_sn、last_exposure_sn、
      affected_sn、correct_before、stuck_after、first_impact_latency、
      sample_policy、exposures_total、exposures_sampled、exposures_dropped。
- [ ] kind 映射：`fault_installed`=L0；`exposure`=None（旁支，不占层）；
      `activation`/`first_impact` 按真实层级；`chain_end` 仍不占层。
- [ ] `tools/fsu_chain_check.py`：F5 根可为 `fault_installed`；
      一个 fault 只允许一个安装根；exposure 不得被当成独立 fault；
      首个 activated exposure 必须能连到 L0–L5；安装/exposure 总数/
      dropped 显式校验；EVENT_CAP 截断必须 `truncated=True`。
- [ ] 测试：一次安装、多 exposure、非激活 exposure、parent 隔离、
      事件容量截断、exposure 不重复计 fault。

### 任务 8：CHAOSFPU F5 永久语义（提交 6）
- [ ] `chaos_fsu_fields.hh` 增加纯函数：
      `applyStuck(value, mask, polarity)`（SA0 强制清零、SA1 强制置一，
      **不是 XOR**）、`stuckActivated(correct, mask, polarity)`。
- [ ] `CHAOSFPU.hh/.cc/.py`：
  - 新参数 `permanentStuck`、`stuckPolarity`、`f5Warmup`、
    `f5SampleLimit`、`f5KeepFirstLastN`；
  - warm-up 后第一个 eligible 安装一次永久 fault（固定 fault_id、
    mask、polarity）；之后每个 eligible 是 exposure，不新建 fault_id；
  - 每次 exposure 都重新施加 SA0/SA1；正确位等于极性 → exposed-not-activated；
    不同 → activated exposure；
  - 首个 exposure、首个 activated exposure、首个真实影响（commit）、
    最终 terminal 保留完整直接 parent 链；其余 exposure 只记计数与
    bounded samples，显式记录 policy/total/dropped；
  - 运行结束发 `chain_end`，含 exposures_total/activated/dropped。
- [ ] 单元测试（host C++ + Python）：SA0/SA1、一次安装、多 exposure、
      非激活 exposure、mask/polarity 全程不变、非目标位不变、
      capacity 不静默丢证据。

### 任务 9：FP06-F5-W3 gate（提交 7；不计 519）
- [ ] 预注册 gate：FP06-a SA0 或 FP06-b SA1，FP32、lane2、固定 1 bit、
      B0-core；`workloads/directed/neon_fp32_lane_kernel`（eligible 16,384）。
- [ ] 验证 10 条：只安装一次；mask/polarity 不变；每次 exposure 强制；
      相同极性不算 activated；不同则结果改变；非目标 lane/bit 不变；
      同 fault 完整链；exposure 总数与独立参考计数一致；EVENT_CAP 无静默
      截断；Markdown 区分 install/exposure/activation/terminal。
- [ ] gate 证据 `runs/fsu-gates/F5-FP06-W3-PERMANENT-GATE/`。

### 任务 10：FP06-F5-W3 正式 seed（高负载解除后）
- [ ] seed1/2/3 分别预注册 SA0/SA1/固定 mantissa（运行前固定）。
- [ ] 完成后：历史 24/519、8/173；活跃 15/240、5/80。
- [ ] 若 W5 未完成：历史 21/519、7/173；活跃 12/240、4/80。

## 3. FR03（不运行正式 seed）

### 任务 11：FR03 写路径与世代（提交 8，代码 + host 单测）
- [ ] `regfile.hh`：VecRegClass 每次写入重新施加 stuck mask（SA0/SA1），
      128-bit 两个 64-bit 字；Vec 不落入 int PRF。
- [ ] permanent key：reg_class + phys_index + generation + lane + bit + polarity。
- [ ] 物理寄存器重新分配后，旧世代故障不传播到新世代（除非显式要求
      cell 跨世代）。
- [ ] CHAOSPhysReg 增加真实 FSU_PROP L0–L5；runner 增加显式
      CHAOSPhysReg 路径。
- [ ] host 单测：连续多次 Vec 写后目标位仍保持 SA0/SA1；squash/重命名/
      释放/重分配语义。全部通过前 FR03-F5 不得正式运行；不得借用 FP06
      结果侧 stuck 证据认证 FR03。

## 4. 测试、Git 与报告

- [ ] 保持 125 项 FSU 测试通过；新增 suite/oracle/F5 测试。
- [ ] 18 个历史正式 seed 继续只读审计通过；不改旧原始事件。
- [ ] 每个稳定阶段小步提交并 `git push origin fsu`；不 force push、
      不重写历史、不覆盖失败 attempt、不手工补写传播事件或 Markdown。
- [ ] 最终报告：负载与恢复时点、W5/oracle 状态、五程序每 seed/component
      状态、F0-W5 3/3、F5 语义真实性、FP06-F5-W3 3/3、FR03 状态、
      双视图计数、测试结果、每个正式 seed Markdown 路径、
      commit SHA / origin 同步 / 工作区状态。

## 5. 文件 owner（并行 subagent，禁止交叉修改）

| owner | 文件 |
|---|---|
| A（suite） | `tools/fsu_suite.py`(新)、`tools/fsu_suite_runner.py`(新)、`tools/fsu_seed_runner.py`、`tools/fsu_seed_audit.py`、`tools/fsu_index.py`、`schemas/fsu_suite.schema.json`、`schemas/fsu_component.schema.json`、`configs/fsu/suites/polybench-fp-v1.json`、`tests/test_fsu_suite.py`、`tests/test_fsu_suite_runner.py`、`tests/test_fsu_index.py`、`tests/test_fsu_seed_runner.py` |
| B（oracle） | `workloads/ooo/polybench/utilities/gem5fi_oracle.h`(新)、五个 `*.c`、`workloads/ooo/Makefile`、`workloads/ooo/polybench/PROVENANCE.md`、`tools/fsu_oracle.py`(新)、`schemas/fsu_oracle.schema.json`、`tests/test_fsu_oracle.py`(新) |
| C（F5） | `CHAOS/gem5/src/cpu/o3/CHAOSFPU/*`、`CHAOS/gem5/src/cpu/o3/CHAOSFPU/chaos_fsu_fields.hh`、`tools/fsu_prop_fields.py`、`tools/fsu_chain_check.py`、`tests/unit/chaos_fsu_f5_test.cc`(新)、`tests/test_chaos_fsu_f5_cpp.py`(新)、`tests/test_fsu_chain_check.py`、`docs/gem5-fi/fsu/F5-PERMANENT-SEMANTICS.md`(新) |
| 主 agent | `configs/fsu/**` 正式 manifest/gate、`tools/fsu_seed_doc.py`、`CHAOS/gem5/src/cpu/o3/regfile.hh`、`CHAOS/gem5/src/cpu/o3/CHAOSPhysReg/*`(FR03)、构建、gem5/gate、正式运行、索引、提交/推送 |

subagent 只写代码 + 跑轻量测试，**不执行 git commit / push**；主 agent 按任务逐单元提交。
