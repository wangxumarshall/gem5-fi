MD04-R01 trace_v31.jsonl 928e3e3011f7fee5f003e748d6064ea3f50f9432d4f54064b21b8aa790c62f2d
MD04-R01 prop_trace.csv.gz 49d88eff3d503bb26ba5e39fd90d41e381f9fabf2c08796d89cabf95dac39920
MD04-R02 trace_v31.jsonl ee7ce8268d7cc7087d833a7d939189458e8e4f97383b9a11edfcba02bec54d7f
MD04-R02 prop_trace.csv.gz 6735c8b51def4604bc1f81811887e6b7d83779b5af1eb7d25dc46efefb6a556a
MD04-R03 trace_v31.jsonl 622fa84c87fa44931629618ec4f45f4fa06f45dfef1256cd870eb0be18c45895
MD04-R03 prop_trace.csv.gz 2767c69a66ee3a97ca1fb914d91e10f84b38d700d4d77091bdfbf2cac24cd3c4
MD04-R04 trace_v31.jsonl af98933b1ccd1d39bec1c8aacecc9c706a081fc8ede0fd3b9a764e6117d3bd3e
MD04-R04 prop_trace.csv.gz 11dec44a4a84d479dcb9bced5f6d1d71a74f7fa4c2aec1faf23b755dd7019b96
MD04-R05 trace_v31.jsonl 66b60040b6d350e97866891e5bbdaa708efd754dbbba484aee035f9d6c01de2d
MD04-R05 prop_trace.csv.gz 0ec4cbec9ce69f05a8e9267f221bb876a8049b55e42c7496e0b47493cfbe8fe0

# Trace storage

Each `trace_v31.jsonl` is ~26–27 MB. Per repo policy (GitHub 100 MB file
limit; v3.2.3 precedent) the JSONL and gzip CSV stay on disk and in the
v3.2.7 delivery zip; Git keeps this checksum stub plus every metadata,
manifest, config, oracle and stats file. Re-generate with run_pilot.py from
the recorded command.txt.
