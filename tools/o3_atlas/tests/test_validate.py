# tools/o3_atlas/tests/test_validate.py
from tools.o3_atlas.validate import check_anchor


def test_anchor_ok(tmp_path):
    f = tmp_path / "a.cc"
    f.write_text("line1\nint x;\n")
    assert check_anchor("a.cc:2", tmp_path) is None


def test_anchor_missing_file(tmp_path):
    assert "missing" in check_anchor("nope.cc:1", tmp_path)


def test_anchor_line_out_of_range(tmp_path):
    f = tmp_path / "a.cc"
    f.write_text("line1\n")
    assert "out of range" in check_anchor("a.cc:9", tmp_path)


def test_anchor_blank_line(tmp_path):
    f = tmp_path / "a.cc"
    f.write_text("line1\n   \n")
    assert "blank" in check_anchor("a.cc:2", tmp_path)
