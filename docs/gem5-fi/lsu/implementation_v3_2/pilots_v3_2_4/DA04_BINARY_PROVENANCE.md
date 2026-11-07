# DA04 binary provenance (v3.2.5 correction)

The v3.2.4 report header carried a SHA-256 that did not match the committed
pilot manifests. The manifests are the authoritative record for what actually
ran. All five agree:

| Pilot | Manifest | binary_sha256 |
|---|---|---|
| R01 | `DA04-R01/manifest.json` | `3e9148fc380c84917ddad84603e540b2e40e217918f392eb5659d32a56668297` |
| R02 | `DA04-R02/manifest.json` | `3e9148fc380c84917ddad84603e540b2e40e217918f392eb5659d32a56668297` |
| R03 | `DA04-R03/manifest.json` | `3e9148fc380c84917ddad84603e540b2e40e217918f392eb5659d32a56668297` |
| R04 | `DA04-R04/manifest.json` | `3e9148fc380c84917ddad84603e540b2e40e217918f392eb5659d32a56668297` |
| R05 | `DA04-R05/manifest.json` | `3e9148fc380c84917ddad84603e540b2e40e217918f392eb5659d32a56668297` |

The v3.2.5 R04/R05 rerun (request-time causality) used a different binary:
`69a1ca9c5b1cbfb160d0502a8cad8acf7d17101625228978ec79ede588b2287d`
(`baselines_v3_2_5/binary_v325.sha256`). Its manifests are under
`pilots_v3_2_5/DA04-R04` and `pilots_v3_2_5/DA04-R05`.

The v3.2.4 directories were not modified; this file only corrects the
documentation and records both binaries explicitly.
