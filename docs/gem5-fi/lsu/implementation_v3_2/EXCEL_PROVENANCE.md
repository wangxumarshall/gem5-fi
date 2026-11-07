# Authoritative experiment Excel files in this package

Three workbooks are included because they have distinct roles:

| File | Role |
|---|---|
| `excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.1.xlsx` | **Latest experiment plan** (v3.2.1) — the newest workbook in the tree. |
| `excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.xlsx` | v3.2 plan, retained for provenance. |
| `excel/final_paper_audit_v3_1/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.1.xlsx` | **The frozen source that `platform/config_parser.py` actually reads** (`SAMPLE_SHEET = "5.60个样本执行矩阵"`); the DA04 SampleRunID/Seed/EventOrdinal values in this package come from this file. |

The v3.2.4 pilots did not modify any workbook. The DA04 clinical ordinals are
recorded in `pilots_v3_2_4/DA04-R0*/pilot_meta.json →
excel_identity.event_ordinal_used`; the Excel ordinal column remains 1–5.
