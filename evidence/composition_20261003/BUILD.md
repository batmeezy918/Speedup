# PCSS composition witness — 2026-10-03

This directory records a fresh synthetic end-to-end composition witness combining:
- shared-prefix elimination
- 64-branch -> 8-class quotient/reconstruction
- AArch64 NEON FMA

## Reproduce on AArch64

```sh
clang -O3 -march=armv8-a+simd composition.c -o composition
sha256sum composition.c composition
./composition
```

Expected source SHA-256:
`fabc306109e6a216f8b5a3de44134b4c9e95a912e99922097d8c9e793a6a64e3`

The recorded binary SHA-256 is:
`d4eece0407a79063736650125c2478e8833d268fe1b99e84caa9e3439f000b43`

The witness is **STRONG_LOCAL_COMPOSITION_WITNESS**, not a PCSS `VERIFIED` publication. Lean binding and an independently certified reverse reconstruction remain open gates.
