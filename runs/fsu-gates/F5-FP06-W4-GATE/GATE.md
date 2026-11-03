# FP06-F5-W4 gate (non-formal, never 519/240)

- generated: 2026-11-04T01:24:01
- conclusion: **PASS**
- evidence: `runs/fsu-gates/F5-FP06-W4-GATE`

| item | value |
|---|---|
| full exposures_total | 32643 |
| full activated | 4077 |
| full sampled / dropped | 32643 / 0 |
| full oracle | SDC |
| full audit.ok | True |
| sampled exposures_total | 32643 |
| sampled activated | 4077 |
| sampled sampled / dropped | 514 / 32129 |
| sampled oracle | SDC |
| sampled audit.ok | True |
| formal exposures_total | 1309699 |
| formal activated | 130814 |
| formal sampled / dropped | 513 / 1309186 |
| formal oracle | SDC |
| formal audit.ok | True |

## Checks

| check | result | detail |
|---|---|---|
| full: runner status | PASS | `{"status": "admitted", "attempt": "runs/fsu-gates/F5-FP06-W4-GATE/full/FSU-FP06-F5-W4-FULL-GATE/seed1/attempt-1", "chain_terminal": "full", "oracle": "SDC", "md": "runs/fsu-gates/F5-FP06-W4-GATE/full/COMPLETE_PROPAGATION_PATHS/FSU-FP06-F5-W` |
| sampled: runner status | PASS | `{"status": "admitted", "attempt": "runs/fsu-gates/F5-FP06-W4-GATE/sampled/FSU-FP06-F5-W4-SAMPLED-GATE/seed1/attempt-1", "chain_terminal": "full", "oracle": "SDC", "md": "runs/fsu-gates/F5-FP06-W4-GATE/sampled/COMPLETE_PROPAGATION_PATHS/FSU-` |
| formal: runner status | PASS | `{"status": "admitted", "attempt": "runs/fsu-gates/F5-FP06-W4-GATE/formal/FSU-FP06-F5-W4-FORMAL-BOUNDED-GATE/seed1/attempt-1", "chain_terminal": "full", "oracle": "SDC", "md": "runs/fsu-gates/F5-FP06-W4-GATE/formal/COMPLETE_PROPAGATION_PATHS` |
| early: run not admitted | PASS | `{"status": "failed", "attempt": "runs/fsu-gates/F5-FP06-W4-GATE/early/FSU-FP06-F5-W4-SAMPLED-GATE/seed1/attempt-1", "oracle": "Hang", "reason": "exceeded Hang timeout with no program checksum (control-flow corruption: never completed)", "fa` |
| full: audit.ok | PASS | `[]` |
| full: chain_end terminal present | PASS | `"committed"` |
| full: total=sampled+dropped | PASS | `{"root_event_id": "0", "exposure_events": 32643, "unique_exposure_ids": 32643, "activated_events": 4077, "exposures_total": 32643, "exposures_sampled": 32643, "exposures_dropped": 0, "activated_exposure_count": 4077, "first_activated_sn": 1` |
| full: sampled == unique ids | PASS | `{"root_event_id": "0", "exposure_events": 32643, "unique_exposure_ids": 32643, "activated_events": 4077, "exposures_total": 32643, "exposures_sampled": 32643, "exposures_dropped": 0, "activated_exposure_count": 4077, "first_activated_sn": 1` |
| sampled: audit.ok | PASS | `[]` |
| sampled: chain_end terminal present | PASS | `"committed"` |
| sampled: total=sampled+dropped | PASS | `{"root_event_id": "0", "exposure_events": 514, "unique_exposure_ids": 514, "activated_events": 40, "exposures_total": 32643, "exposures_sampled": 514, "exposures_dropped": 32129, "activated_exposure_count": 4077, "first_activated_sn": 10879` |
| sampled: sampled == unique ids | PASS | `{"root_event_id": "0", "exposure_events": 514, "unique_exposure_ids": 514, "activated_events": 40, "exposures_total": 32643, "exposures_sampled": 514, "exposures_dropped": 32129, "activated_exposure_count": 4077, "first_activated_sn": 10879` |
| formal: audit.ok | PASS | `[]` |
| formal: chain_end terminal present | PASS | `"committed"` |
| full == sampled: exposures_total | PASS | `{"full": 32643, "sampled": 32643}` |
| full == sampled: activated_exposure_count | PASS | `{"full": 4077, "sampled": 4077}` |
| full == sampled: faults_injected | PASS | `{"full": 1, "sampled": 1}` |
| full == sampled: oracle | PASS | `{"full": "SDC", "sampled": "SDC"}` |
| formal: prop_evt bounded (< 200000 events) | PASS | `{"event_count": 521, "truncated": false, "prop_evt_bytes": 73084, "injection_log_bytes": 381988508}` |
| formal: evidence files bounded | PASS | `{"event_count": 521, "truncated": false, "prop_evt_bytes": 73084, "injection_log_bytes": 381988508}` |
| early: audit is NOT ok (fail-closed) | PASS | `["prop_evt 未截断（reason=EOFError:Compressed file ended before the end-of-stream marker was reached）", "所有 fault 均 admitted", "所有 fault 均 certified", "链 admitted=True", "链 certified=True", "链 violations=[]", "存在 admitted fault", "stats.txt 非空"` |
| early: no AUTHORITATIVE | PASS | `"runs/fsu-gates/F5-FP06-W4-GATE/early/FSU-FP06-F5-W4-SAMPLED-GATE/seed1/AUTHORITATIVE"` |
| early: no injector chain_end | PASS | `{"has_end": false}` |
