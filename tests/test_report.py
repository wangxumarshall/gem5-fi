import csv, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

def _mk_csv(path, unit, sdc, nv):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cell_ordinal","layer","target_arch","semantic_role",
                    "fault_model","f5_substitute_target","n_total","n_valid",
                    "SDC","Crash","Hang","Inactive","Masked","SimulatorError",
                    "P_SDC","P_SDC_lo","P_SDC_hi","P_DUE","P_DUE_lo","P_DUE_hi",
                    "P_escape","Reachability","first_run_id","first_run_class"])
        w.writerow([0,"physical",unit,"", "transient_bit_flip",-1, nv, nv,
                    sdc,0,0,0,nv-sdc,0, sdc/nv,0,1, 0,0,1, sdc/nv, 1.0,
                    "x-r0","SDC" if sdc else "Masked"])

def test_report_merges_and_aggregates():
    from report import merge_campaigns, wilson
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d,"a.csv"), os.path.join(d,"b.csv")
        _mk_csv(a, "prf", 30, 100)
        _mk_csv(b, "rat", 10, 100)
        rows = merge_campaigns([a, b], unit_col="target_arch")
        by_unit = {r["unit"]: r for r in rows}
        assert by_unit["prf"]["sdc"] == 30 and by_unit["prf"]["n_valid"] == 100
        assert by_unit["rat"]["sdc"] == 10
        assert abs(wilson(30, 100)[1] - 0.30) < 1e-9

def test_report_cli_emits_md():
    from report import render_markdown
    rows = [{"unit":"prf","sdc":30,"n_valid":100,"p":0.30,"lo":0.22,"hi":0.40,
             "hang":0,"crash":0,"masked":70,"sources":"a"}]
    md = render_markdown(rows)
    assert "| prf | 30/100 | 0.300 | [0.220,0.400] |" in md
