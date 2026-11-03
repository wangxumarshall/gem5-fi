# FSU D3：F0/F5 活跃范围与正式运行门禁

## 任务 A：活跃范围配置 ✅
- `configs/fsu/ACTIVE_SCOPE.json`：F0/F5，80 RunID/240 seed，
  源注册表 173/519 不变；F1–F4 = DEFERRED_BY_USER；
  历史完成 = HISTORICAL_COMPLETE_OUT_OF_ACTIVE_SCOPE。
- `tools/fsu_scope.py`：频率解析、主动范围校验、scope_status、
  源注册表 SHA/count/唯一性校验、正式 out-root 保护。

## 任务 B：双视图索引 ✅
- `fsu_index` 输出历史 173/519 与活跃 80/240；每行 frequency/
  scope_class/completion_state；已完成 18/519、6 个 3/3；
  活跃 9/240、3 个 3/3；DEFERRED 90；历史范围外完成 3/9。

## 任务 C：运行门禁 ✅
- `fsu_seed_runner` 在创建 attempt/gem5 前拒绝 F1–F4；
  `runner.py` 对显式 freq 拒绝；`campaign.py` 在 runs/ 创建前拒绝，
  测试模式重定向输出到临时目录。
- 显式测试模式只验证旧频率解析，不写正式 runs/fsu。

## 任务 D：W5/W6 artifact 审计 ✅
- W5：4/5 程序真实，2mm 缺失、suite/program_id/oracle 未定义 → BLOCKED；
  不运行正式 F0-W5。
- W6：仅 SVD 真实，FFT/稀疏缺失 → PARTIAL；不运行正式 F0-W6。

## 任务 E：F5 readiness ✅
- 8 个 F5 RunID 0 READY；FP06 5 个 PARTIAL，FR03 3 个 BLOCKED。
- F5 定义清晰（永久 stuck，非 rate），但调度/SA0/SA1/FR03 Vec 持久化/
  FSU_PROP/runner 路径/事件上限未闭合 → 不运行 F5。

## 任务 F：测试 ✅
- 全量 FSU 测试 125 passed；历史 18 seed 离线审计保持通过。
