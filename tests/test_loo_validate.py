import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

def test_loo_perfect_library():
    from loo_validate import loo_cross_validate
    # 两个可分单元：lsq 尾数主导 vs prf 高位主导
    masks = {
        "lsq_fwd": [0x00000004, 0x00000100, 0x00000200, 0x00000001, 0x00000800],
        "prf":     [0x8000000000000000, 0x4000000000000000,
                    0x2000000000000000, 0x1000000000000000, 0x0800000000000000],
    }
    r = loo_cross_validate(masks, topk=3)
    assert r["n_events"] == 10
    assert r["top1_hit_rate"] == 1.0     # 完全可分 → 100%

def test_loo_single_unit_trivial():
    from loo_validate import loo_cross_validate
    r = loo_cross_validate({"lsq_fwd": [1, 2, 3, 4]}, topk=3)
    assert r["n_events"] == 4
    assert r["top1_hit_rate"] == 1.0     # 唯一单元平凡命中（诚实标注）

def test_loo_ambiguous_library_below_one():
    from loo_validate import loo_cross_validate
    # 两个相同位谱的单元 → 不可分 → Top-1 命中率 < 1
    masks = {
        "a": [0x00000001, 0x00000002, 0x00000004],
        "b": [0x00000001, 0x00000002, 0x00000004],
    }
    r = loo_cross_validate(masks, topk=1)
    assert r["top1_hit_rate"] < 1.0

def test_render_markdown():
    from loo_validate import render_markdown
    md = render_markdown({"top1_hit_rate": 0.9, "topk_hit_rate": 1.0,
                          "topk": 3, "n_events": 10,
                          "per_unit": {"lsq_fwd": {"n": 5, "top1": 5, "topk": 5}}})
    assert "Top-3" in md and "100.0%" in md
    assert "VALID" in md
