# FR01/FR02 生命周期闭合证据（overwrite / free-realloc / squash）

日期：2026-11-05　分支：`fsu`

## 目标

让 FR01/FR02 的 `Masked/contained` 认证建立在可审计的生命周期证据上，
而不是最终 hash 相同或“没有看到后续读”。

## 单元 1：瞬态证据字段（C++）

- [x] `overwrite` 事件记录 `full_before`（安装时翻转值）、`fault_mask`、
      `target_bits_before/after/restored`。
- [x] 覆盖仅在安装世代生效；跨世代写不再冒充 overwrite。
- [x] 新增 `post_overwrite_read` / `write_after_overwrite`（同 fault、
      `activated=0`）与 total/emitted/affected 计数。
- [x] 瞬态 `generation_change` 事件与 `free_realloc` 终局。
- [x] `finalizeVecTransient` 输出 `squashed` 终局。
- [x] 新 key 加入 `CHAOSPropagation::PROP_EVT_EXT_FIELDS` 与
      `tools/fsu_prop_fields.py`（否则会被当作未知字段丢弃）。

## 单元 2：门禁认证规则（Python）

- [x] `CONTAINED_BY_OVERWRITE`：安装世代、目标 bit 全部恢复、
      post-overwrite 读/写 total==emitted 且 affected==0、链尾可追踪。
- [x] `CONTAINED_BY_FREE_REALLOC`：generation old==安装世代、new 不同、
      安装世代之后无 read/commit、链尾可追踪。
- [x] 旧流缺字段 → 保持 BLOCKED + evidence_missing。
- [x] 合成回归：覆盖认证、受影响读拒绝、free/realloc、squash、
      连续写不 stuck。

## 验证

- [x] `scons -j16 build/ARM/gem5.opt` 构建通过（仅既有无关 warning）。
- [x] 真实非正式 gate（v4）：
      `FR01-a/seed2` 与 `FR02-c/seed2` 均 PASS + `CONTAINED_BY_FREE_REALLOC`。
- [x] `pytest tests/test_fsu_fr01_fr02_gate.py tests/test_chaos_physreg_*_cpp.py
      tests/test_chaos_fsu_fields_cpp.py ...` 全通过。
- [ ] 同世代 overwrite、squash、commit 的真实样本（后续 gate）。
