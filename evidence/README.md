# AGD PCSS Elevation Evidence Bundle

Run: `AGD_PCSS_ELEVATION_20261009T060000Z`

The complete reproducible run archive is encoded as ordered base64 text parts in `archive_parts/`. Reconstruct it on Linux/macOS:

```sh
cat evidence/archive_parts/part-*.b64 | base64 -d > AGD_PCSS_ELEVATION_20261009T060000Z.tar.gz
sha256sum AGD_PCSS_ELEVATION_20261009T060000Z.tar.gz
```

Expected tarball SHA-256: `79f7985b40da7b0bbfb3bd33a402bb52f3b48ea3031084a42ec8f34a2a7a0871`.

The archive includes source, binaries, Lean proof files, receipts, formal and source-set manifests, and the final overhead sweep v3 source/raw CSV. Standalone files expose the report, receipt, manifest, and sweep for review.

**Scope:** PCSS 8/8 applies only to `U = Ubar ⊗ I_m` on the declared block-constant invariant sector. The final overhead sweep measures setup, quotient steps, reconstruction, and plan destruction through 1,024 steps. No universal transformer speedup, arbitrary invariant discovery, or independent-hardware replication is claimed.
