# Pilot evidence archive

`pilot_evidence.tar.gz` is split into `part00`, `part01`, ... because GitHub
limits individual files to 100 MB.

Reassemble and verify:

```bash
cat pilot_evidence.tar.gz.part* > /tmp/pilot_evidence.tar.gz
sha256sum -c pilot_evidence.tar.gz.sha256   # expects the archive name to match
tar -tzf /tmp/pilot_evidence.tar.gz | wc -l # 3890 files
```

The archive preserves every non-`disk.img` file from the 150 non-authoritative
`TEST-*` pilot directories. It is the backup that authorizes their deletion.
