# LSU 传播终态判定 v3

10种终态：NO_ELIGIBLE_EVENT、INJECTION_NOT_ACTIVATED、ACTIVATED_MASKED、SQUASHED、DETECTED_CONTAINED、ARCH_STATE_CORRUPTION、SDC、CRASH、HANG/TIMEOUT、TRACE_INCOMPLETE。

- **TraceCompleteness** 独立字段：COMPLETE/INCOMPLETE/MISSING；INCOMPLETE不得判Masked。
- **ACTIVATED_MASKED** 必须有L1/L2/L3覆盖/纠正证据；不能因软件无错误直接判Masked。
- **ARCH_STATE_CORRUPTION ≠ SDC**；SDC需oracle差异+传播链证据。
- **SQUASHED** 不等于更早消除。
- **DETECTED_CONTAINED** 无真实RAS/ECC证据时=NOT_IMPLEMENTED。
- **CRASH** 区分guest crash与SimulatorError。
- **HANG/TIMEOUT** 需绝对超时与最后可证事件。
- **NO_ELIGIBLE_EVENT/INJECTION_NOT_ACTIVATED** 不是成功传播。
- **正常程序退出** 不能自动判为无错误；必须检查oracle与Trace。


## v3.1 四维组织

见 `LSU_Trace_Hook_Design_v3.1.md`：RunStatus、FaultActivationStatus、TerminalState、TraceCompleteness 分开。
- 未激活 = FaultActivationStatus=NOT_TRIGGERED。
- Masked = 已激活/传播但架构可见结果无差异且有覆盖/纠正证据。
- Squashed = 推测指令被撤销。
- ARCH_STATE_CORRUPTION = 错误进入架构状态但未证明软件可见错误。
- SDC = 架构状态错误+软件oracle差异+未被检测。
- CRASH = guest/系统异常退出；HANG = Timeout。
- Trace INCOMPLETE 不得判 Masked。

