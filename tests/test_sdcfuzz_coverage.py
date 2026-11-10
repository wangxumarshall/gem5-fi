"""Static completeness tests for the template ACE/IBR coverage contract."""

from sdcfuzz import coverage
from sdcfuzz.evaluate import COUNTERS
from sdcfuzz.templates import TEMPLATE_BY_ID, TEMPLATES


def test_every_template_op_kind_has_a_metric_mapping():
    assert coverage.missing_from_table(TEMPLATES) == []
    for template in TEMPLATES:
        required = coverage.template_metrics(template)
        assert required, template.id
        for kinds in required.values():
            assert kinds, template.id


def test_every_metric_uses_known_evaluate_counters():
    for metric, counters in coverage.METRIC_COUNTERS.items():
        assert counters, metric
        for counter in counters:
            assert counter in COUNTERS, (metric, counter)


def test_fp_templates_require_vector_ace_and_the_matching_fp_ibr():
    add = coverage.template_metrics(TEMPLATE_BY_ID["fp-add"])
    mul = coverage.template_metrics(TEMPLATE_BY_ID["fp-mul"])
    assert "vec" in add and "fpadd" in add
    assert "vec" in mul and "fpmul" in mul
    assert "fadd" in add["fpadd"]
    assert "fmul" in mul["fpmul"]


def test_integer_templates_do_not_depend_on_fp_metrics():
    for template in TEMPLATES:
        if template.target in ("alu", "mult", "div", "l1d", "l1i"):
            required = coverage.template_metrics(template)
            assert "fpadd" not in required and "fpmul" not in required, template.id
