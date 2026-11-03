# FSU 状态一致性 + FP06-F5-W1 + FR03 计划（2026-11-03）

> 基线：`fsu` @ `52fece882d56985bdd32560aaef6cd9fc363482e`，工作区 clean。
> 历史视图 24/519 seed、8/173 RunID；活跃视图 F0/F5 15/240 seed、5/80 RunID。
> 24 个 authoritative audit（21 普通 + 3 W5 suite）全部 ok/certified。
> FSU 测试 216 passed（含 `tests/test_chaos_vec_stuck_cpp.py`）。
> 频率范围：仅 F0/F5；禁止新 F1–F4 正式实验。

## 任务 1：状态文档与矩阵一致性（owner A）

- [ ] 重写 `docs/gem5-fi/fsu/F5-READINESS.md`，区分 FP06-a/b/c（W3 3/3 已认证）、FP06-d（MISSING）、W1/W4/W5/W6（未完成）、FR03（PARTIAL/BLOCKED）。
- [ ] `tools/fsu_implementation_matrix.py`：seed completion 从权威索引/audit 读取（suite seed 计 1）；增加代码能力探测，不再只依赖 2026-11-02 静态快照；输出 `capability_evidence`。
- [ ] 修正 `IMPLEMENTATION_MATRIX.json/csv`、`IMPLEMENTATION_AUDIT.md`、`COVERAGE_STATUS.md`、`ACTIVE_SCOPE.md`、`IMPLEMENTATION-STATUS-2026-11-03.md` 中过期断言；不修改历史实验原始证据。
- [ ] 新增一致性测试：文档/矩阵不得同时声称“未实现”又存在 certified 正式 seed；矩阵 seed 计数必须等于 `fsu_index.scan`。
- 验证：`python3 tools/fsu_implementation_matrix.py && python3 tools/fsu_index.py`；`pytest tests/test_fsu_implementation_matrix.py tests/test_fsu_doc_consistency.py tests/test_fsu_index.py -q`。

## 任务 2：FP06-F5-W1 过滤能力 + gate + 3 正式 seed（owner B，运行由 main）

- [ ] CHAOSFPU 新增 `opClasses`（显式 allowlist）与 `regClass` 过滤；只有 precision/regClass/opClass 全匹配才 eligible/exposure；FCVT/int-convert/不可靠解码 fail closed。
- [ ] census 输出逐 opClass/regClass eligible 计数；F5 事件携带 `op_class`/`reg_class`，链审计可校验。
- [ ] manifest schema + runner + validator 支持 `op_classes`/`reg_class`；未知值 panic/拒绝。
- [ ] 预注册 W1 gate（非正式，不计 519）：FP32 SA0、FP64 SA1、FP32 固定 mantissa、precision mismatch eligible=0、polarity-same 不计 activated、opClass 过滤、守恒、采样不静默丢弃、chain_end 落盘、B0 config、golden/fault oracle。
- [ ] 预注册 seed1 FP06-a FP32 sign SA0；seed2 FP06-b FP64 sign SA1；seed3 FP06-c FP32 mantissa mask。字段/mask/polarity 运行前固定。
- 验证：host 单测 + main 跑 gate 全部 PASS 后才跑正式 seed1→2→3。

## 任务 3：FR03 永久物理 cell 语义 + CHAOSPhysReg 路径（owner C）

- [ ] 按工作簿原文裁决：固定 cell 身份 = reg_class/phys_index/lane/mask/polarity；generation 只标识分配世代/exposure 身份，不是清除条件；free/realloc/squash 后同一 cell 仍卡死。
- [ ] 修改 `regfile.hh`/`CHAOSPhysReg`：同 cell 任意 generation 重施加；其他 cell/reg class 不串扰；新 generation 的 exposure/parent 链重新开始；运行结束清除。
- [ ] host/C++ 测试：同 gen 连续 8 写、free 后新 gen 仍卡死、新 gen 链重启、其他 cell 不受影响、int/float/vec 不串扰、squash 后仍卡死、reset 后消失。
- [ ] CHAOSPhysReg 真实 FSU_PROP 路径尽量实现；未完成部分必须诚实标 BLOCKED，不得认证 FR03-F5。
- 验证：`pytest tests/test_chaos_vec_stuck_cpp.py tests/test_fsu_* -q`；主 agent 构建后跑相关 C++/gem5 gate。

## 任务 4：main 收口

- [ ] 审阅/合并三路修改；处理共享文件 `CHAOSPropagation.hh` 字段 allowlist。
- [ ] 构建 gem5（`-j16`，负载 >16 时暂停）；跑 W1 gate；串行跑 3 正式 seed；逐 seed audit。
- [ ] 重新生成 matrix → index，确认 27/519、9/173 与 18/240、6/80（仅当三 seed 全部 certified）。
- [ ] 完整 FSU 测试；小步提交并推送 `origin/fsu`。
