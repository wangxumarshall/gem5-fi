"""conftest.py — pytest 适配层（[LSU][MDSPEC][R4-8-PYTEST]）。

本仓库的 LSU 测试有两类：
  1. **脚本式**（绝大多数，`python3 tests/test_xxx.py` → 退出码 0=全 PASS）：
     模块内自带 `main()`，用局部回调 `check(name, cond, detail)` 记录失败，**不依赖 pytest**。
     pytest 收集不到它们（无 `test_*` 顶层函数契约），这是**设计如此**，不是缺口。
  2. **函数式**（`tests/test_claim_concurrency.py`）：把 `test_a_*`…`test_e_*` 定义为顶层函数、
     由 `main()` 传入 `check` 回调调用。该文件**两种跑法都成立**，但 pytest 会把 `check`
     当 fixture 请求 → 5 项 `fixture 'check' not found` 的 **collection/setup ERROR**。

R4-7 门禁（`tools/lsu_ready_contract.py --gate`）跑 `pytest tests/ -q`，把这 5 项 ERROR 计成 rc=1。
如实判定：这是**测试入口错误，不是功能错误**（同一文件 `python3 tests/…` 自跑 rc=0）。

本适配层**不降标准、不静默**：
  - `check` fixture = 真实断言记录器：条件不成立立即 FAIL（**绝不**静默通过或 skip）。
  - 子测试 (c)(d)(e) 的环境前置（`env_precheck`：MemAvailable≥11GiB 且 SwapFree≥4GiB）
    以 autouse fixture 复现原脚本语义：环境不可验收 = **响亮失败**（原文件自述：
    "拒绝静默跳过：环境不可验收=失败"）。
  - 模块结束清理 `TMP_ROOT`（复现 `main()` 的 `finally: shutil.rmtree`）。
"""
import shutil

import pytest

_GATED = ("test_c_slot_race", "test_d_run_concurrency_cap", "test_e_heartbeat")


def _is_claim_concurrency(request):
    mod = getattr(request, "module", None)
    return mod is not None and getattr(mod, "__name__", "").endswith(
        "test_claim_concurrency")


@pytest.fixture
def check():
    """脚本式测试的 `check(name, cond, detail)` 回调 —— pytest 版本：不成立即断言失败。"""
    def _check(name, cond, detail=""):
        assert cond, f"{name}  <- {detail}"
    return _check


@pytest.fixture(autouse=True)
def _claim_concurrency_env_gate(request):
    """复现原脚本 `env_precheck` 语义：环境不足则 (c)(d)(e) 响亮失败，不静默跳过。"""
    if not _is_claim_concurrency(request) or request.node.name not in _GATED:
        return
    mod = request.module
    missing = []

    def _record(name, cond, detail=""):
        if not cond:
            missing.append(f"{name}({detail})")

    ok = mod.env_precheck(_record)
    assert ok, ("ENV-FAIL（拒绝静默跳过：环境不可验收=失败）: "
                + "; ".join(missing))


@pytest.fixture(autouse=True, scope="module")
def _claim_concurrency_tmp_cleanup(request):
    """复现 `main()` 的 finally：模块测试结束后删除隔离临时目录。"""
    yield
    if _is_claim_concurrency(request):
        shutil.rmtree(getattr(request.module, "TMP_ROOT", None), ignore_errors=True)
