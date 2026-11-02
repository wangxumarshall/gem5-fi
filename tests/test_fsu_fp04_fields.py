"""tests/test_fsu_fp04_fields.py — FP04 字段/lane 语义的特征测试与缺口测试。

特征测试只读取 runs/fsu 的 AUTHORITATIVE 原始 PROP-EVT，不运行 gem5；
它们锁定当前正式证据的真实字段语义（FP64 bit 坐标、64-bit lane、FP04-c）。

缺口测试使用 strict xfail 记录尚未实现的能力（FP32 精度参数、lane 选择、
128-bit lane 写入/lane_mask 发射）。实现完成后 strict xfail 会转为
XPASS 失败，提醒更新测试与覆盖文档。
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_prop_fields as P  # noqa: E402

# FP64 结果位的合法区间（与 CHAOSFPU.cc:276-283 的字段定义一致）。
FP64_FIELDS = {
    "sign": (63, 63),
    "exp_hi": (58, 62),
    "exp_lo": (52, 57),
    "mant_hi": (35, 51),
    "mant_mid": (18, 34),
    "mant_lo": (0, 17),
}

# 已完成的正式频率批次（F0/F1/F2/F3-W4）；值是该 seed 的 scheduled fault 数。
OFFICIAL_SEEDS = {
    ("FSU-FP04-F0-W4", 1): 1, ("FSU-FP04-F0-W4", 2): 1,
    ("FSU-FP04-F0-W4", 3): 1,
    ("FSU-FP04-F1-W4", 1): 1, ("FSU-FP04-F1-W4", 2): 2,
    ("FSU-FP04-F1-W4", 3): 1,
    ("FSU-FP04-F2-W4", 1): 21, ("FSU-FP04-F2-W4", 2): 22,
    ("FSU-FP04-F2-W4", 3): 19,
    ("FSU-FP04-F3-W4", 1): 206, ("FSU-FP04-F3-W4", 2): 202,
    ("FSU-FP04-F3-W4", 3): 210,
}


def _attempt(runid: str, seed: int) -> Path:
    auth = ROOT / "runs/fsu" / runid / f"seed{seed}" / "AUTHORITATIVE"
    att = Path(auth.read_text(encoding="utf-8").strip())
    return att if att.is_absolute() else ROOT / att


def _roots(runid: str, seed: int):
    att = _attempt(runid, seed)
    events, truncated, _ = P.read_stream(att / "inject/prop_evt.txt.gz")
    assert not truncated, f"{runid} seed{seed} prop_evt truncated"
    return [e for e in events if str(e.get("kind")) == "fault_applied"]


@pytest.mark.parametrize("runid,seed", sorted(OFFICIAL_SEEDS))
def test_official_seed_roots_have_legal_fp64_field(runid, seed):
    roots = _roots(runid, seed)
    assert len(roots) == OFFICIAL_SEEDS[(runid, seed)]
    for root in roots:
        field = str(root.get("field"))
        assert field in FP64_FIELDS, (runid, seed, field)
        lo, hi = FP64_FIELDS[field]
        bit = int(str(root.get("bit_indices")))
        assert lo <= bit <= hi, (runid, seed, field, bit)
        mask = int(str(root.get("fault_mask")), 16)
        assert mask == 1 << bit, (runid, seed, field, bit, hex(mask))
        # 当前试点契约：FP64 结果寄存器，单 64-bit lane。
        assert str(root.get("lane_width")) == "64"
        assert str(root.get("lane_offset")) == "0"
        assert str(root.get("submodel")) == "FP04-c"


def test_official_coverage_is_mant_lo_only():
    """锁定当前正式证据的真实字段覆盖；扩展字段后必须同步更新覆盖文档。"""
    fields = set()
    for runid, seed in OFFICIAL_SEEDS:
        fields |= {str(r.get("field")) for r in _roots(runid, seed)}
    assert fields == {"mant_lo"}


@pytest.mark.xfail(
    strict=True,
    reason="FP32 字段映射未实现：CHAOSFPU 无 precision 参数/FP32 位表"
           "（见 FP04-W4-FREQUENCY-CLOSEOUT.md 第 8 节）",
)
def test_fp32_precision_parameter_present():
    text = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.py").read_text(
        encoding="utf-8")
    assert "precision" in text or "fp32" in text.lower()


@pytest.mark.xfail(
    strict=True,
    reason="FP04-d lane 选择未实现：CHAOSFPU 无 laneWidth/laneOffset 参数",
)
def test_lane_selection_parameter_present():
    text = (ROOT / "CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.py").read_text(
        encoding="utf-8")
    assert "laneWidth" in text or "laneOffset" in text


@pytest.mark.xfail(
    strict=True,
    reason="FP04-d 128-bit lane/lane_mask 未实现：事件 lane_mask 恒为空",
)
def test_lane_mask_event_field_is_emitted():
    for runid, seed in OFFICIAL_SEEDS:
        for root in _roots(runid, seed):
            assert str(root.get("lane_mask")).strip()
