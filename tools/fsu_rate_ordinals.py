#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_rate_ordinals.py — F1/F2/F3 确定性 rate ordinal 生成器。

工作簿表 5 语义：
  F1 平均每 1,000,000 个 eligible events 注入 1 次，间隔 ±50% 抖动；
  F2 平均每   100,000 个 eligible events 注入 1 次，间隔 ±50% 抖动；
  F3 平均每    10,000 个 eligible events 注入 1 次，间隔 ±50% 抖动。

实现约定（不是 probability/geometric 近似）：
  - interval 从固定 SplitMix64 PRNG 抽取，范围闭区间
        [ceil(0.5·rate), floor(1.5·rate)]；
  - ordinal = warmup + 依次累加的 interval；严格递增且互不重复；
  - ordinal > N 后停止（N 为 countOnly 实测 eligible 总数）；
  - 同一 (N, rate, jitter_pct, seed, warmup) 逐字节可重放；
  - 不同 seed 产生不同序列（N 足够大时）。

Runner 负责把 ordinals 传给 CHAOSFPU；C++ 端只按 eligible 序号精确命中，
不再做二次概率抽样。manifest 必须记录 generator/version/seed 与完整列表
（或独立文件 + SHA-256）。
"""
from __future__ import annotations

import hashlib
import json
import math

MASK64 = (1 << 64) - 1
SPLITMIX_GAMMA = 0x9E3779B97F4A7C15
SPLITMIX_MUL1 = 0xBF58476D1CE4E5B9
SPLITMIX_MUL2 = 0x94D049BB133111EB

GENERATOR = "splitmix64-mod-uniform-interval"
GENERATOR_VERSION = "1"

# 工作簿表 5 的频率档位 → rate divisor（eligible events / injection）。
FREQ_RATE_DIVISOR = {
    "F1": 1_000_000,
    "F2": 100_000,
    "F3": 10_000,
}


class RateSemanticsError(ValueError):
    """freq 标签与真实 rate 语义不一致（禁止只换标签）。"""


class SplitMix64:
    """确定性 64-bit PRNG；输出与平台/版本无关。"""

    def __init__(self, seed):
        if not isinstance(seed, int) or seed < 0:
            raise ValueError(f"seed must be a non-negative int, got {seed!r}")
        self.state = seed & MASK64

    def next_u64(self):
        self.state = (self.state + SPLITMIX_GAMMA) & MASK64
        z = self.state
        z = ((z ^ (z >> 30)) * SPLITMIX_MUL1) & MASK64
        z = ((z ^ (z >> 27)) * SPLITMIX_MUL2) & MASK64
        z ^= z >> 31
        return z & MASK64


def interval_bounds(rate, jitter_pct):
    """返回闭区间 [ceil((1-j)·rate), floor((1+j)·rate)]。"""
    if not isinstance(rate, int) or rate <= 0:
        raise ValueError(f"rate must be a positive int, got {rate!r}")
    try:
        j = float(jitter_pct)
    except (TypeError, ValueError):
        raise ValueError(f"jitter_pct must be numeric, got {jitter_pct!r}")
    if not math.isfinite(j) or j < 0.0 or j >= 100.0:
        raise ValueError(f"jitter_pct must be in [0, 100), got {jitter_pct!r}")
    lo = max(1, int(math.ceil(rate * (100.0 - j) / 100.0)))
    hi = int(math.floor(rate * (100.0 + j) / 100.0))
    if hi < lo:
        raise ValueError(f"empty interval for rate={rate} jitter={jitter_pct}")
    return lo, hi


def _interval_from_u64(u, lo, hi):
    """把 64-bit 抽样映射到闭区间 [lo, hi]（确定性取模）。"""
    span = hi - lo + 1
    return lo + (int(u) % span)


def build_rate_ordinals(N, rate, jitter_pct, seed, warmup=0,
                        u64_source=None):
    """生成 F1/F2/F3 的注入 ordinal 列表。

    参数:
      N           countOnly 实测 eligible 总数
      rate        平均间隔（F1=1e6, F2=1e5, F3=1e4）
      jitter_pct  抖动百分比（工作簿为 50）
      seed        PRNG seed（同 seed 完全可重放）
      warmup      前 warmup 个 eligible event 不参与注入；ordinal 从 warmup 起累加
      u64_source  仅测试用：返回 64-bit 整数的可调用对象；默认 SplitMix64(seed)

    返回 dict 含完整序列与边界；不含任何概率近似。
    """
    if not isinstance(N, int) or N < 0:
        raise ValueError(f"N must be a non-negative int, got {N!r}")
    if not isinstance(warmup, int) or warmup < 0:
        raise ValueError(f"warmup must be a non-negative int, got {warmup!r}")
    lo, hi = interval_bounds(rate, jitter_pct)

    if u64_source is None:
        rng = SplitMix64(seed)
        def next_u64():
            return rng.next_u64()
    else:
        if not callable(u64_source):
            raise ValueError("u64_source must be callable")
        def next_u64():
            return u64_source()

    ordinals, intervals = [], []
    pos = warmup
    if warmup < N:
        while True:
            interval = _interval_from_u64(next_u64(), lo, hi)
            pos += interval
            if pos > N:
                break
            ordinals.append(pos)
            intervals.append(interval)

    # 严格递增/无重复是函数契约，任何违反都应当场失败。
    for a, b in zip(ordinals, ordinals[1:]):
        if b <= a:
            raise AssertionError(f"ordinals not strictly increasing: {a} -> {b}")
    if len(set(ordinals)) != len(ordinals):
        raise AssertionError("duplicate ordinal generated")

    return {
        "generator": GENERATOR,
        "version": GENERATOR_VERSION,
        "N": N,
        "rate_divisor": rate,
        "jitter_pct": jitter_pct,
        "seed": seed,
        "warmup": warmup,
        "interval_bounds": {"lo": lo, "hi": hi},
        "ordinals": ordinals,
        "intervals": intervals,
        "ordinal_index": list(range(len(ordinals))),
        "injection_count": len(ordinals),
        "first_ordinal": ordinals[0] if ordinals else None,
        "last_ordinal": ordinals[-1] if ordinals else None,
    }


def canonical_bytes(doc):
    """稳定 JSON 字节（键排序、紧凑分隔、单个换行）。"""
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def ordinals_sha256(doc):
    return hashlib.sha256(canonical_bytes(doc)).hexdigest()


def rate_config_from_manifest(manifest):
    """读取 injector.rate；未配置返回 None。"""
    injector = manifest.get("injector") or {}
    cfg = injector.get("rate")
    return cfg if cfg else None


def validate_rate_for_freq(freq, rate_cfg):
    """强制 freq 标签 ↔ rate 语义一致；返回规范化配置或 None。

    - F1/F2/F3 必须提供 rate 配置，且 rate_divisor 必须与档位一致；
    - F0 不得携带 rate 配置（它是一次注入，不是 rate 语义）；
    - 其他档位（F4/F5）本工具不支持，携带 rate 配置直接拒绝。
    """
    if freq in FREQ_RATE_DIVISOR:
        if not isinstance(rate_cfg, dict):
            raise RateSemanticsError(
                f"{freq} requires a real rate config "
                "(injector.rate.rate_divisor/jitter_pct); "
                "changing --fsu_freq alone is not acceptable")
        divisor = rate_cfg.get("rate_divisor")
        expected = FREQ_RATE_DIVISOR[freq]
        if divisor != expected:
            raise RateSemanticsError(
                f"{freq} requires rate_divisor={expected}, got {divisor!r}")
        jitter = rate_cfg.get("jitter_pct", 50)
        interval_bounds(expected, jitter)  # 校验 jitter
        warmup = rate_cfg.get("warmup", 0)
        if not isinstance(warmup, int) or warmup < 0:
            raise RateSemanticsError(f"invalid warmup: {warmup!r}")
        return {"rate_divisor": expected, "jitter_pct": jitter,
                "warmup": warmup}
    if rate_cfg:
        raise RateSemanticsError(
            f"{freq} does not define rate semantics; refusing injector.rate "
            f"config {rate_cfg!r} (only F1/F2/F3 do)")
    return None
