# FINAL regression report

* Working-tree suite and independent extracted-package suite: 0 failed, 0 errors; the only skip is the explicitly documented SERVER_EVIDENCE_REQUIRED test, which is executed separately on the server and passes. The executed summary is written by the freeze builder into `verification/FINAL_PYTEST.txt` and `verification/FINAL_SERVER_EVIDENCE_TEST.txt`.
* 180/180 chain graphs validated; 0 gaps.
* 60/60 control evidence rows present, hashed and COMPLETED.
* 57 masking endpoints have strong in/out edges; 20 IVD runs have a connected terminal.
* 15/15 RP01 canonical gzip traces independently readable, with WATCHDOG terminal and >=287 post-injection probes.
* 6/6 historical squash rows audited, excluded from the denominator.
* 6812/6812 pre-repair semantic records reconciled; 0 unresolved.
* JSON/CSV/report edge totals: 712998 = 712998 = 712998.
* SHA256 of every packaged file and every present server trace recorded in `FINAL_EVIDENCE_MANIFEST.csv`.
