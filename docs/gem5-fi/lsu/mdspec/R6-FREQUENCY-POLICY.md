# R6 Frequency Policy (generated — do not hand-edit)

- schema_version: `r6-frequency-policy/1`
- decision_date: 2026-10-25
- decision_source: user-ruling-2026-10-25:R6-frequency-policy-overlay
- counts: {"total": 329, "normal": 261, "stress_only": 39, "stress_redundant": 29}

## Representative F6 groups

| model | representative | runids |
|---|---|---|
| A04 | A04-F6-W0 | A04-F6-W0, A04-F6-W3 |
| A05 | A05-F6-W3 | A05-F6-W3 |
| A06 | A06-F6-W3 | A06-F6-W3, A06-F6-W5 |
| A07 | A07-F6-W3 | A07-F6-W3, A07-F6-W5 |
| A08 | A08-F6-W3 | A08-F6-W3, A08-F6-W5 |
| C05 | C05-F6-W6 | C05-F6-W6 |
| C07 | C07-F6-W6 | C07-F6-W6 |
| C08 | C08-F6-W6 | C08-F6-W6, C08-F6-W7 |
| C09 | C09-F6-W10 | C09-F6-W10, C09-F6-W6 |
| C11 | C11-F6-W10 | C11-F6-W10, C11-F6-W6 |
| C12 | C12-F6-W10 | C12-F6-W10, C12-F6-W6 |
| C15 | C15-F6-W10 | C15-F6-W10, C15-F6-W11, C15-F6-W6 |
| L02 | L02-F6-W12 | L02-F6-W12, L02-F6-W5 |
| L03 | L03-F6-W12 | L03-F6-W12, L03-F6-W5 |
| L04 | L04-F6-W11 | L04-F6-W11, L04-F6-W12, L04-F6-W5 |
| O01 | O01-F6-W7 | O01-F6-W7 |
| O02 | O02-F6-W7 | O02-F6-W7 |
| O03 | O03-F6-W7 | O03-F6-W7 |
| O04 | O04-F6-W7 | O04-F6-W7 |
| O05 | O05-F6-W7 | O05-F6-W7 |
| O06 | O06-F6-W7 | O06-F6-W7 |
| O07 | O07-F6-W7 | O07-F6-W7 |
| P03 | P03-F6-W8 | P03-F6-W8, P03-F6-W9 |
| P05 | P05-F6-W10 | P05-F6-W10, P05-F6-W8 |
| P06 | P06-F6-W6 | P06-F6-W6, P06-F6-W8 |
| P07 | P07-F6-W6 | P07-F6-W6, P07-F6-W8 |
| P09 | P09-F6-W13 | P09-F6-W13, P09-F6-W6, P09-F6-W8 |
| S04 | S04-F6-W0 | S04-F6-W0, S04-F6-W5 |
| S05 | S05-F6-W3 | S05-F6-W3, S05-F6-W5 |
| S06 | S06-F6-W5 | S06-F6-W5, S06-F6-W6 |
| S07 | S07-F6-W5 | S07-F6-W5 |
| S08 | S08-F6-W5 | S08-F6-W5 |
| S09 | S09-F6-W5 | S09-F6-W5 |
| S11 | S11-F6-W5 | S11-F6-W5, S11-F6-W6 |
| T04 | T04-F6-W4 | T04-F6-W4 |
| T05 | T05-F6-W4 | T05-F6-W4 |
| T06 | T06-F6-W4 | T06-F6-W4 |
| T07 | T07-F6-W4 | T07-F6-W4 |
| T08 | T08-F6-W4 | T08-F6-W4, T08-F6-W9 |

## F6 per-RunID policy table

| RunID | policy | req_seeds | sched | in_stats | representative | reason |
|---|---|---|---|---|---|---|
| A04-F6-W3 | STRESS_REDUNDANT | 0 | False | False | A04-F6-W0 | covered_by_representative_F6 |
| A04-F6-W0 | STRESS_ONLY | 1 | True | False | A04-F6-W0 |  |
| A05-F6-W3 | STRESS_ONLY | 1 | True | False | A05-F6-W3 |  |
| A06-F6-W3 | STRESS_ONLY | 1 | True | False | A06-F6-W3 |  |
| A06-F6-W5 | STRESS_REDUNDANT | 0 | False | False | A06-F6-W3 | covered_by_representative_F6 |
| A07-F6-W3 | STRESS_ONLY | 1 | True | False | A07-F6-W3 |  |
| A07-F6-W5 | STRESS_REDUNDANT | 0 | False | False | A07-F6-W3 | covered_by_representative_F6 |
| A08-F6-W3 | STRESS_ONLY | 1 | True | False | A08-F6-W3 |  |
| A08-F6-W5 | STRESS_REDUNDANT | 0 | False | False | A08-F6-W3 | covered_by_representative_F6 |
| T04-F6-W4 | STRESS_ONLY | 1 | True | False | T04-F6-W4 |  |
| T05-F6-W4 | STRESS_ONLY | 1 | True | False | T05-F6-W4 |  |
| T06-F6-W4 | STRESS_ONLY | 1 | True | False | T06-F6-W4 |  |
| T07-F6-W4 | STRESS_ONLY | 1 | True | False | T07-F6-W4 |  |
| T08-F6-W4 | STRESS_ONLY | 1 | True | False | T08-F6-W4 |  |
| T08-F6-W9 | STRESS_REDUNDANT | 0 | False | False | T08-F6-W4 | covered_by_representative_F6 |
| S04-F6-W5 | STRESS_REDUNDANT | 0 | False | False | S04-F6-W0 | covered_by_representative_F6 |
| S04-F6-W0 | STRESS_ONLY | 1 | True | False | S04-F6-W0 |  |
| S05-F6-W5 | STRESS_REDUNDANT | 0 | False | False | S05-F6-W3 | covered_by_representative_F6 |
| S05-F6-W3 | STRESS_ONLY | 1 | True | False | S05-F6-W3 |  |
| S06-F6-W5 | STRESS_ONLY | 1 | True | False | S06-F6-W5 |  |
| S06-F6-W6 | STRESS_REDUNDANT | 0 | False | False | S06-F6-W5 | covered_by_representative_F6 |
| S07-F6-W5 | STRESS_ONLY | 1 | True | False | S07-F6-W5 |  |
| S08-F6-W5 | STRESS_ONLY | 1 | True | False | S08-F6-W5 |  |
| S09-F6-W5 | STRESS_ONLY | 1 | True | False | S09-F6-W5 |  |
| S11-F6-W5 | STRESS_ONLY | 1 | True | False | S11-F6-W5 |  |
| S11-F6-W6 | STRESS_REDUNDANT | 0 | False | False | S11-F6-W5 | covered_by_representative_F6 |
| C05-F6-W6 | STRESS_ONLY | 1 | True | False | C05-F6-W6 |  |
| C07-F6-W6 | STRESS_ONLY | 1 | True | False | C07-F6-W6 |  |
| C08-F6-W6 | STRESS_ONLY | 1 | True | False | C08-F6-W6 |  |
| C08-F6-W7 | STRESS_REDUNDANT | 0 | False | False | C08-F6-W6 | covered_by_representative_F6 |
| C09-F6-W6 | STRESS_REDUNDANT | 0 | False | False | C09-F6-W10 | covered_by_representative_F6 |
| C09-F6-W10 | STRESS_ONLY | 1 | True | False | C09-F6-W10 |  |
| C11-F6-W6 | STRESS_REDUNDANT | 0 | False | False | C11-F6-W10 | covered_by_representative_F6 |
| C11-F6-W10 | STRESS_ONLY | 1 | True | False | C11-F6-W10 |  |
| C12-F6-W6 | STRESS_REDUNDANT | 0 | False | False | C12-F6-W10 | covered_by_representative_F6 |
| C12-F6-W10 | STRESS_ONLY | 1 | True | False | C12-F6-W10 |  |
| O01-F6-W7 | STRESS_ONLY | 1 | True | False | O01-F6-W7 |  |
| O02-F6-W7 | STRESS_ONLY | 1 | True | False | O02-F6-W7 |  |
| O03-F6-W7 | STRESS_ONLY | 1 | True | False | O03-F6-W7 |  |
| O04-F6-W7 | STRESS_ONLY | 1 | True | False | O04-F6-W7 |  |
| O05-F6-W7 | STRESS_ONLY | 1 | True | False | O05-F6-W7 |  |
| O06-F6-W7 | STRESS_ONLY | 1 | True | False | O06-F6-W7 |  |
| O07-F6-W7 | STRESS_ONLY | 1 | True | False | O07-F6-W7 |  |
| P03-F6-W8 | STRESS_ONLY | 1 | True | False | P03-F6-W8 |  |
| P03-F6-W9 | STRESS_REDUNDANT | 0 | False | False | P03-F6-W8 | covered_by_representative_F6 |
| P05-F6-W8 | STRESS_REDUNDANT | 0 | False | False | P05-F6-W10 | covered_by_representative_F6 |
| P05-F6-W10 | STRESS_ONLY | 1 | True | False | P05-F6-W10 |  |
| P06-F6-W6 | STRESS_ONLY | 1 | True | False | P06-F6-W6 |  |
| P06-F6-W8 | STRESS_REDUNDANT | 0 | False | False | P06-F6-W6 | covered_by_representative_F6 |
| P07-F6-W6 | STRESS_ONLY | 1 | True | False | P07-F6-W6 |  |
| P07-F6-W8 | STRESS_REDUNDANT | 0 | False | False | P07-F6-W6 | covered_by_representative_F6 |
| L02-F6-W5 | STRESS_REDUNDANT | 0 | False | False | L02-F6-W12 | covered_by_representative_F6 |
| L02-F6-W12 | STRESS_ONLY | 1 | True | False | L02-F6-W12 |  |
| L03-F6-W5 | STRESS_REDUNDANT | 0 | False | False | L03-F6-W12 | covered_by_representative_F6 |
| L03-F6-W12 | STRESS_ONLY | 1 | True | False | L03-F6-W12 |  |
| L04-F6-W5 | STRESS_REDUNDANT | 0 | False | False | L04-F6-W11 | covered_by_representative_F6 |
| L04-F6-W11 | STRESS_ONLY | 1 | True | False | L04-F6-W11 |  |
| L04-F6-W12 | STRESS_REDUNDANT | 0 | False | False | L04-F6-W11 | covered_by_representative_F6 |
| C15-F6-W6 | STRESS_REDUNDANT | 0 | False | False | C15-F6-W10 | covered_by_representative_F6 |
| C15-F6-W10 | STRESS_ONLY | 1 | True | False | C15-F6-W10 |  |
| C15-F6-W11 | STRESS_REDUNDANT | 0 | False | False | C15-F6-W10 | covered_by_representative_F6 |
| P09-F6-W6 | STRESS_REDUNDANT | 0 | False | False | P09-F6-W13 | covered_by_representative_F6 |
| P09-F6-W8 | STRESS_REDUNDANT | 0 | False | False | P09-F6-W13 | covered_by_representative_F6 |
| P09-F6-W13 | STRESS_ONLY | 1 | True | False | P09-F6-W13 |  |
| C13-F6-W6 | STRESS_REDUNDANT | 0 | False | False |  | covered_by_representative_F6 |
| O08-F6-W7 | STRESS_REDUNDANT | 0 | False | False |  | covered_by_representative_F6 |
| S12-F6-W5 | STRESS_REDUNDANT | 0 | False | False |  | covered_by_representative_F6 |
| T09-F6-W4 | STRESS_REDUNDANT | 0 | False | False |  | covered_by_representative_F6 |
