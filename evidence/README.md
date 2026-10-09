# AGD PCSS Elevation Evidence Bundle

Run: `AGD_PCSS_ELEVATION_20261009T060000Z`

The full reproducible run bundle is encoded as ordered base64 text parts in `archive_parts/`. To reconstruct the exact tarball on Linux/macOS:

```sh
cat evidence/archive_parts/part-*.b64 | base64 -d > AGD_PCSS_ELEVATION_20261009T060000Z.tar.gz
sha256sum AGD_PCSS_ELEVATION_20261009T060000Z.tar.gz
```

Expected tarball SHA-256:

`acbec74fa8597811e03809e764dc8389267db70a4dc540dfda5d88be7f16943d`

The archive includes source, binaries, Lean proof files, gate receipts, the PCSS closure receipt, the overhead sweep source and raw CSV, and the extended artifact manifest. The standalone evidence files in this directory make the main report and receipt reviewable without reconstructing the archive.

**Scope:** PCSS 8/8 closure is limited to the declared tensor-separable family (U = ar U otimes I_m) and its block-constant invariant sector. The sweep measures setup, quotient steps, and reconstruction separately through 1,024 steps. It does not establish universal transformer speedup, arbitrary invariant discovery, or independent-hardware replication.
