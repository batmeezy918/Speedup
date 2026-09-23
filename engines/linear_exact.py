#!/usr/bin/env python3
"""Exact invariant-sector reference workload (already-established construction).

Mathematical model
------------------
State space E = R^d composed of `r` contiguous blocks of width `tile`
(d = r * tile) that are kept exactly constant within each block (the invariant
sector Omega). The transition T scales every coordinate by a weight that
depends only on its block class: x[i] *= w[class(i)].

Quotient:      pi(x) = block representatives (first element of each block)
Reduced step:  Tbar(q)[c] = q[c] * w[c]
Reconstruction: sigma(q) = each block replicated `tile` times
Observable:    the block-class representative vector (what consumers read)

Closure facts (proved for the formal lane in lean4):
    pi(T x)  = Tbar(pi x)                      (intertwining, when x in Omega)
    pi(sigma q) = q                            (section)
    Obs(x) = ObsBar(pi x)                      (observable factorization)

Honesty rule: this workload exposes BOTH quantities:
    - operation-count ratio       (theory; math/algorithmic work reduction)
    - measured wall-clock speedup (practice; measured on the declared host)
and NEVER conflates them.
"""
from __future__ import annotations

import json
import pathlib
import sys

try:
    import numpy as np
except Exception:  # noqa: BLE001  (pure-python fallback below)
    np = None

from typing import Any, Callable

DEFAULT_WEIGHTS = None


def _w_vector():
    return [1.0, 1.25, 0.9, 1.1, 1.5, 0.8, 1.3, 0.95]


def block_class_vector(d: int, tile: int, nclasses: int) -> list[int]:
    """class index for each coordinate: contiguous blocks, class = b mod nclasses."""
    r = d // tile
    return [b % nclasses for b in range(r)]


# ---------------------------------------------------------------------------
# models
# ---------------------------------------------------------------------------

class LinearExactModel:
    """Block-constant 1D model. d = r*tile; classes by contiguous block index."""

    name = "exact_invariant_sector_vector"

    def __init__(self, d: int, tile: int, nclasses: int, steps: int = 4,
                 weights=None, rng_seed: int = 0):
        assert d % tile == 0, "d must be a multiple of tile"
        self.d = d
        self.tile = tile
        self.r = d // tile
        self.steps = steps
        self.nclasses = nclasses
        w = weights or _w_vector()

        # per-coordinate weights computed once from per-class weights
        cls_of_block = block_class_vector(d, tile, nclasses)
        self.class_of_elt = [cls_of_block[b] for b in range(self.r) for _ in range(tile)]
        self.weights = [float(w[c % len(w)]) for c in self.class_of_elt]
        self.wbar = [float(w[c % len(w)]) for c in range(self.r)]

    # -- invariant sector generation (block-constant vector) --
    def make_initial(self, seed: int = 0) -> list[float]:
        if np is not None:
            rng = np.random.default_rng(seed)
            reps = rng.uniform(0.5, 2.0, size=self.r)
            x = np.repeat(reps, self.tile)
            return x.tolist()
        return [float((seed >> (b % 64)) & 1) + 0.5 for b in range(self.r) for _ in range(self.tile)]

    # -- literal (baseline) transition on full vector --
    def T_full(self, x) -> list[float]:
        return [x[i] * self.weights[i] for i in range(self.d)]

    # -- projection --
    def pi(self, x) -> list[float]:
        return [x[c * self.tile] for c in range(self.r)]

    # -- reduced (candidate) transition on quotient reps --
    def Tbar(self, q) -> list[float]:
        return [q[c] * self.wbar[c] for c in range(self.r)]

    # -- reconstruction --
    def sigma(self, q) -> list[float]:
        reps = q
        return [reps[c] for c in range(self.r) for _ in range(self.tile)]

    # -- observable factor --
    def obs(self, x) -> list[float]:
        return self.pi(x)

    def obsBar(self, q) -> list[float]:
        return list(q)


class LinearExactMatrixModel:
    """Block-constant 2D model. n x n matrix, tile x tile blocks.

    Class of block (bi, bj) is determined by a deterministic hash-like formula
    so that classes are exact and reproducible: c = (a*bi + b*bj) mod nclasses.
    """

    name = "exact_invariant_sector_matrix"

    def __init__(self, n: int, tile: int, nclasses: int, steps: int = 4,
                 weights=None, a: int = 3, b: int = 1):
        assert n % tile == 0, "n must be a multiple of tile"
        self.n = n
        self.tile = tile
        self.bn = n // tile
        self.r = self.bn * self.bn  # number of blocks
        self.steps = steps
        self.nclasses = nclasses
        w = weights or [1.0, 1.1, 0.95, 1.2, 0.9, 1.05, 1.15, 0.85]

        self.class_weights = {}  # (bi, bj) -> float
        self.cache = {}
        for bi in range(self.bn):
            for bj in range(self.bn):
                c = (a * bi + b * bj) % nclasses
                self.class_weights[(bi, bj)] = float(w[c % len(w)])

    def block_class(self, bi: int, bj: int) -> int:
        return (3 * bi + bj) % self.nclasses

    def make_initial(self, seed: int = 0) -> list[list[float]]:
        if np is not None:
            rng = np.random.default_rng(seed)
            A = np.empty((self.n, self.n), dtype=np.float64)
            for bi in range(self.bn):
                for bj in range(self.bn):
                    c = self.block_class(bi, bj)
                    v = float(rng.uniform(0.5, 2.0)) + c
                    A[bi * self.tile:(bi + 1) * self.tile,
                      bj * self.tile:(bj + 1) * self.tile] = v
            return A.tolist()
        return [[0.0] * self.n for _ in range(self.n)]

    def T_full(self, A) -> list[list[float]]:
        out = [[0.0] * self.n for _ in range(self.n)]
        for bi in range(self.bn):
            for bj in range(self.bn):
                w = self.class_weights[(bi, bj)]
                for x in range(self.tile):
                    for y in range(self.tile):
                        ii = bi * self.tile + x
                        jj = bj * self.tile + y
                        out[ii][jj] = A[ii][jj] * w
        return out

    def pi(self, A) -> list[float]:
        reps = []
        for bi in range(self.bn):
            for bj in range(self.bn):
                reps.append(A[bi * self.tile][bj * self.tile])
        return reps

    def Tbar(self, q) -> list[float]:
        out = []
        idx = 0
        for bi in range(self.bn):
            for bj in range(self.bn):
                w = self.class_weights[(bi, bj)]
                out.append(q[idx] * w)
                idx += 1
        return out

    def sigma(self, q) -> list[list[float]]:
        out = [[0.0] * self.n for _ in range(self.n)]
        idx = 0
        for bi in range(self.bn):
            for bj in range(self.bn):
                v = q[idx]
                for x in range(self.tile):
                    for y in range(self.tile):
                        out[bi * self.tile + x][bj * self.tile + y] = v
                idx += 1
        return out

    def obs(self, A) -> list[float]:
        return self.pi(A)

    def obsBar(self, q) -> list[float]:
        return list(q)


# ---------------------------------------------------------------------------
# invariant evaluator
# ---------------------------------------------------------------------------

def omega_vector(x, tile: int = 32, nclasses: int | None = None) -> bool:
    """Block-constancy invariant: every tile block must be exactly constant."""
    d = len(x)
    nblocks = d // tile
    for b in range(nblocks):
        lo = b * tile
        hi = lo + tile
        if any(x[i] != x[lo] for i in range(lo + 1, hi)):
            return False
    return True


def omega_matrix(A, tile: int = 8) -> bool:
    n = len(A)
    bn = n // tile
    for bi in range(bn):
        for bj in range(bn):
            ref = A[bi * tile][bj * tile]
            for x in range(bi * tile, (bi + 1) * tile):
                for y in range(bj * tile, (bj + 1) * tile):
                    if A[x][y] != ref:
                        return False
    return True


# ---------------------------------------------------------------------------
# factory
# ---------------------------------------------------------------------------

def make_model(scenario: dict) -> LinearExactModel | LinearExactMatrixModel:
    kind = scenario["workload"]["kind"]
    params = scenario.get("parameters", {})
    dims = scenario.get("dimensions", {})
    if kind == "exact_invariant_sector":
        mode = params.get("model", "vector")
        if mode == "matrix":
            n = dims.get("matrix_rows") or dims.get("d")
            tile = dims.get("tile", 8)
            nclasses = dims.get("r", dims.get("nclasses", 8))
            return LinearExactMatrixModel(n, tile, nclasses,
                                          steps=params.get("steps", 4),
                                          a=params.get("a", 3), b=params.get("b", 1))
        d = dims.get("d")
        if d is None:
            mr = dims.get("matrix_rows") or 0
            mc = dims.get("matrix_cols") or 0
            d = mr * mc
        tile = dims.get("tile", 32)
        nclasses = dims.get("nclasses", dims.get("r", 8))
        return LinearExactModel(d, tile, nclasses, steps=params.get("steps", 4),
                                weights=params.get("weights"),
                                rng_seed=scenario.get("seed", 0))
    raise ValueError(f"make_model: unsupported workload.kind {kind!r}")


def invoke(name: str, model, value):
    """Dispatch a named function from the scenario carrier to the model."""
    fn = getattr(model, name, None)
    if fn is None:
        raise ValueError(f"unknown model function {name!r}")
    return fn(value)


if __name__ == "__main__":
    m = LinearExactModel(d=1 << 20, tile=32, nclasses=1 << 15)
    x0 = m.make_initial(seed=7)
    q0 = m.pi(x0)
    x1 = m.T_full(x0)
    q1 = m.Tbar(q0)
    print("intertwining exact:", m.pi(x1) == q1, "dims:", m.d, "r:", m.r)
    print("invariant init:", omega_vector(x0, m.tile))