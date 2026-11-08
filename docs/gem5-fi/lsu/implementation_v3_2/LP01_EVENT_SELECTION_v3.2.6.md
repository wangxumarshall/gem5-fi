# LP01 event selection — historical fact and freeze requirement

- R01: Excel ordinal 1, clinical 1.
- R02: Excel ordinal 2, clinical 2.
- R03: Excel ordinal 3, clinical 3.
- R04: Excel ordinal 4, clinical 4.
- R05: Excel ordinal **5**, clinical **14**.

The R05 substitution is retained as a historical fact: the Excel ordinal 5
event in the W5 eligible stream had no consumer, so ordinal 14 was used. It
is recorded as `excel_identity.event_ordinal=5` and
`event_ordinal_used=14` in every v3.2.5/v3.2.6 manifest and pilot_meta. It
is **not** relabelled as Excel ordinal 5 in the clinical field.

Before the formal experiment, the ROI/warm-up window and the eligible-event
selection rule must be frozen separately. The post-hoc rule "advance until a
consumer exists" is a temporary pilot selection and must not be used for
formal samples without the researcher's explicit approval.
