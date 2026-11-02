# 开发构建记录（非权威证据）

> 记录时间：2026-11-02（API 中断恢复后补记）。
> 结论：**该次构建是开发构建，不是权威 -j4 构建证据**；未保留完整 stdout/stderr。

## 1. 事实

- 工作目录：`/home/sdc/gem5-fi-fsu/CHAOS/gem5`
- 命令：`PYTHON_CONFIG=/opt/python3.11/bin/python3.11-config scons -j16 build/ARM/gem5.opt`
- 输出处理：仅 `| tail`，**未保存完整日志**。
- 第一次执行：编译失败（CHAOSFPU.cc 构造函数 rate 校验块被误放在命名空间作用域，
  以及 `fsu_rate_divisor` 成员名笔误），退出码非 0；失败输出只保留了 tail。
- 修复后第二次执行：成功，退出码 0；输出只保留了 tail。
- 构建后二进制：`CHAOS/gem5/build/ARM/gem5.opt`
- 构建后 SHA-256：`b9f7e1f57a4a938dab237664f4f4848a2e3c37902233b42fc834ab5ecb15bd55`
- 二进制 size / mtime：`1246087008` / `2026-11-02 19:42:46 +0800`
- 源码 HEAD（构建时）：`67b4dfd1616be47cb8b3f31b94d049a04d1a72a2`
- 工作树状态：dirty（rate ordinal 实现未提交）

## 2. 诚实边界

- 本记录**不**声称使用 `-j4`，**不**声称有完整权威日志。
- 本记录不替代随后由 `tools/fsu_build_gem5.sh`（flock + Python 3.11 + `scons -j4`）
  生成的权威增量构建证据。
- 上一轮二进制/日志未被删除；权威构建会在同一路径上增量重建，届时记录
  构建前后 SHA-256。
