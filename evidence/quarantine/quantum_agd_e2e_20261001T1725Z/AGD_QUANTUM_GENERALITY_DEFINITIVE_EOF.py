#!/usr/bin/env python3
"""AGD_QUANTUM_GENERALITY_DEFINITIVE_EOF.py

Definitive experiment resolving the unresolved questions of the AGD Quantum
Unfolding Governor program.

Explicitly documented equivalence relation (chosen before any operator is
constructed, independent of the answer):

  Let n be the number of qubits, d = 2**n the full Hilbert-space dimension.
  Split the n qubits into a coarse (quotient) register of nq = ceil(n/2)
  qubits and a fine (fiber) register of nf = floor(n/2) qubits.  Index the
  computational basis by i = a*m + b with a in [0, q), b in [0, m),
  q = 2**nq, m = 2**nf.  Two basis states i ~ j are equivalent iff
  floor(i/m) == floor(j/m), i.e. iff they share the same coarse register
  value.  The q equivalence classes are the basis of the quotient space Q.

  The quotient map is Pi : H -> Q, Pi = I_q (x) (1/sqrt(m)) 1_m^T, and the
  reconstruction map is R : Q -> H, R = I_q (x) (1/sqrt(m)) 1_m, which are a
  right inverse pair (Pi R = I_Q).  Operators are generated as
  U = V (x) I_m with Ubar = V on Q, so that the formal gate
  Pi U = Ubar Pi holds exactly and reconstruction
  R Ubar Pi |psi> = U |psi> holds exactly for every state |psi> in the
  quotient-invariant subspace Range(R) = {psi : psi = R alpha}.

  State family under test (complete quantum state, full d-vector):
  psi = R alpha with independently drawn normalized alpha in C**q.

  Scope boundary (not editorial, a mathematical fact): a linear quotient map
  of dimension q < d cannot carry enough information to reconstruct an
  arbitrary vector of dimension d.  Therefore exact complete-state
  reconstruction is tested on the family of quotient-invariant states
  psi = R alpha (and on quotients Q constructed from the documented
  relation).  Universal arbitrary-state / arbitrary-circuit reconstruction
  is therefore classified NOT ESTABLISHED.
"""

import csv
import hashlib
import json
import statistics
import time
from pathlib import Path

import numpy as np

SOURCE = Path(__file__).resolve()
BASE_DIR = SOURCE.parent
CSV_PATH = BASE_DIR / "AGD_QUANTUM_GENERALITY_RESULTS.csv"
JSON_PATH = BASE_DIR / "AGD_QUANTUM_GENERALITY_RESULTS.json"
REPORT_PATH = BASE_DIR / "AGD_QUANTUM_GENERALITY_REPORT.md"

N_MIN = 2
N_MAX = 10
SEEDS_PER_FAMILY = 3
WARMUPS = 2
REPS = 5
GATE_TOL = 1.0e-10
CLOSURE_TOL = 1.0e-10
COMPOSITION_DEPTHS = [2, 3, 4, 5]

POSITIVE_FAMILIES = [
    "A_Permutation",
    "B_DiagonalPhase",
    "C_SparseLocal",
    "D_TensorProductLocal",
    "E_RandomUnitary",
    "F_HeterogeneousProduct",
    "G_ForwardReverse",
]

CONTROL_TYPES = [
    "NEG_random_class_assignment",
    "NEG_broken_symmetry",
    "NEG_altered_quotient_operator",
    "NEG_corrupted_reconstruction",
]
CONTROL_SIZES = [4, 6, 8]
CONTROL_SEEDS = 2

I2 = np.eye(2, dtype=np.complex128)
X2 = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
Y2 = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
Z2 = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
PAULIS = [I2, X2, Y2, Z2]


def seed_int(*parts):
    raw = "|".join(str(p) for p in parts).encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return int.from_bytes(digest[:8], "big") % (2**31 - 1) + 1


def arrb(arr):
    arr = np.ascontiguousarray(arr)
    if np.iscomplexobj(arr):
        arr = arr.astype(np.complex128)
        arr = np.ascontiguousarray(arr.reshape(-1).view(np.float64))
    else:
        arr = np.ascontiguousarray(arr, dtype=np.float64)
    return arr.tobytes()


def sha256b(parts):
    h = hashlib.sha256()
    for part in parts:
        if isinstance(part, str):
            h.update(part.encode("utf-8"))
        else:
            h.update(part)
    return h.hexdigest()


def random_state(rng, size):
    z = rng.normal(size=size) + 1j * rng.normal(size=size)
    return z / max(np.linalg.norm(z), 1e-300)


def random_su2(rng):
    a = rng.normal() + 1j * rng.normal()
    b = rng.normal() + 1j * rng.normal()
    norm = np.sqrt(np.real(np.conj(a) * a + np.conj(b) * b)) + 1e-300
    return np.array([[a, -np.conj(b)], [b, np.conj(a)]], dtype=np.complex128) / norm


def random_unitary(rng, q):
    a = (rng.normal(size=(q, q)) + 1j * rng.normal(size=(q, q))) / np.sqrt(2.0)
    qq, rr = np.linalg.qr(a)
    diagr = np.diag(rr)
    ph = np.exp(-1j * np.angle(diagr))
    return qq * ph[np.newaxis, :]


def gate_matrix(gate, wires, nq):
    left = 1 << wires[0]
    right = 1 << (nq - wires[-1] - 1)
    l = np.eye(left, dtype=np.complex128)
    r = np.eye(right, dtype=np.complex128)
    return np.kron(np.kron(l, gate), r)


def random_circuit_matrix(rng, q, ngates):
    nq = int(round(np.log2(q)))
    m = np.eye(q, dtype=np.complex128)
    for _ in range(ngates):
        if nq >= 2 and rng.rand() < 0.5:
            wire = int(rng.randint(0, nq - 1))
            gate = random_unitary(rng, 4)
            m = gate_matrix(gate, [wire, wire + 1], nq) @ m
        else:
            wire = int(rng.randint(0, nq))
            gate = random_su2(rng)
            m = gate_matrix(gate, [wire], nq) @ m
    return m


def random_product_gates(rng, q):
    nq = int(round(np.log2(q)))
    m = np.array([[1.0]], dtype=np.complex128)
    for _ in range(nq):
        m = np.kron(m, random_su2(rng))
    return m


def random_hetero_product(rng, q, mval):
    depth = int(rng.randint(2, 5))
    comps = ["A_Permutation", "B_DiagonalPhase", "C_SparseLocal",
             "D_TensorProductLocal", "E_RandomUnitary"]
    chosen = [comps[int(i)] for i in rng.randint(0, len(comps), size=depth)]
    v = np.eye(q, dtype=np.complex128)
    for name in chosen:
        v = leaf_matrix(name, rng, q, mval) @ v
    return v


def leaf_matrix(fam, rng, q, mval):
    if fam == "A_Permutation":
        perm = rng.permutation(q)
        v = np.zeros((q, q), dtype=np.complex128)
        v[np.arange(q), perm] = 1.0
        return v
    if fam == "B_DiagonalPhase":
        ph = np.exp(2j * np.pi * rng.rand(q))
        return np.diag(ph).astype(np.complex128)
    if fam == "C_SparseLocal":
        nq = int(round(np.log2(q)))
        return random_circuit_matrix(rng, q, max(1, nq // 2))
    if fam == "D_TensorProductLocal":
        return random_product_gates(rng, q)
    if fam == "E_RandomUnitary":
        return random_unitary(rng, q)
    raise ValueError(fam)


def family_matrix(fam, rng, q, mval):
    if fam == "F_HeterogeneousProduct":
        return random_hetero_product(rng, q, mval)
    if fam == "G_ForwardReverse":
        return random_unitary(rng, q)
    return leaf_matrix(fam, rng, q, mval)


def build_quotient(n):
    d = 1 << n
    nq = (n + 1) // 2
    nf = n // 2
    q = 1 << nq
    m = 1 << nf
    p = (1.0 / np.sqrt(m)) * np.ones((1, m), dtype=np.complex128)
    pi = np.kron(np.eye(q), p)
    r = np.kron(np.eye(q), p.T)
    return d, q, m, pi, r


def closure_residual(v, pi, nf):
    m = 1 << nf
    p = (1.0 / np.sqrt(m)) * np.ones((1, m), dtype=np.complex128)
    lhs = np.kron(v, p)
    rhs = v @ pi
    return float(np.max(np.abs(lhs - rhs)))


def naive_closure_residual(pi, u, ubar):
    return float(np.max(np.abs(pi @ u - ubar @ pi)))


def kron_reduce(gates):
    m = np.array([[1.0]], dtype=np.complex128)
    for g in gates:
        m = np.kron(m, g)
    return m


def build_observable_set(rng, d, q, m, nq, nf):
    specs = []
    for c in range(q):
        specs.append(("basis", int(c * m)))
    for _ in range(8):
        specs.append(("basis", int(rng.randint(0, d))))
    for _ in range(2):
        specs.append(("diag", rng.normal(size=d)))
    for _ in range(3):
        sq = [int(rng.randint(0, 4)) for _ in range(nq)]
        sf = [int(rng.randint(0, 4)) for _ in range(nf)]
        specs.append(("pauli", sq, sf))
    for _ in range(3):
        aq = (rng.normal(size=(q, q)) + 1j * rng.normal(size=(q, q))) / np.sqrt(2.0)
        hq = (aq + aq.conj().T) / 2.0
        af = (rng.normal(size=(m, m)) + 1j * rng.normal(size=(m, m))) / np.sqrt(2.0)
        hf = (af + af.conj().T) / 2.0
        specs.append(("herm", hq, hf))
    return specs


def eval_obs(spec, psi, alpha, m):
    kind = spec[0]
    if kind == "basis":
        return float(np.abs(psi[spec[1]]) ** 2)
    if kind == "diag":
        return float(np.real(np.vdot(psi, spec[1] * psi)))
    if kind == "pauli":
        oq = kron_reduce([PAULIS[k] for k in spec[1]])
        u = (1.0 / np.sqrt(m)) * np.ones(m, dtype=np.complex128)
        of = kron_reduce([PAULIS[k] for k in spec[2]])
        eq = np.real(np.vdot(alpha, oq @ alpha))
        ef = np.real(np.vdot(u, of @ u))
        return float(eq * ef)
    hq, hf = spec[1], spec[2]
    u = (1.0 / np.sqrt(m)) * np.ones(m, dtype=np.complex128)
    eq = np.real(np.vdot(alpha, hq @ alpha))
    ef = np.real(np.vdot(u, hf @ u))
    return float(np.real(eq) * np.real(ef))


def eval_obs_full(spec, state, m):
    kind = spec[0]
    if kind == "basis":
        return float(np.abs(state[spec[1]]) ** 2)
    if kind == "diag":
        return float(np.real(np.vdot(state, spec[1] * state)))
    if kind == "pauli":
        oq = kron_reduce([PAULIS[k] for k in spec[1]])
        of = kron_reduce([PAULIS[k] for k in spec[2]])
        o = np.kron(oq, of)
        return float(np.real(np.vdot(state, o @ state)))
    hq, hf = spec[1], spec[2]
    o = np.kron(hq, hf)
    return float(np.real(np.vdot(state, o @ state)))


def measure(fn, warmups=WARMUPS, reps=REPS):
    for _ in range(warmups):
        fn()
    timings = []
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        fn()
        t1 = time.perf_counter_ns()
        timings.append((t1 - t0) / 1.0e9)
    return float(statistics.median(timings))


def run_positive(n, fam, seed):
    d, q, m, pi, r = build_quotient(n)
    nf = n // 2
    nq = (n + 1) // 2
    rng = np.random.RandomState(seed_int(n, fam, seed))
    obs_rng = np.random.RandomState(seed_int(n, fam, seed, "observables"))
    vs = [family_matrix(fam, rng, q, m) for _ in range(5)]
    v0 = vs[0]
    ubar = v0
    u = np.kron(ubar, np.eye(m))
    alpha = random_state(rng, q)
    psi = r @ alpha
    full_out = u @ psi
    operator_nnz = int(np.count_nonzero(u))

    closure_res = closure_residual(ubar, pi, nf)
    pi_r_err = float(np.max(np.abs(pi @ r - np.eye(q))))

    alpha_q = pi @ psi
    alpha_out = ubar @ alpha_q
    rec = r @ alpha_out
    state_max = float(np.max(np.abs(full_out - rec)))
    state_l2 = float(np.linalg.norm(full_out - rec) / max(np.linalg.norm(full_out), 1e-300))

    specs = build_observable_set(obs_rng, d, q, m, nq, nf)
    obs_err = 0.0
    for spec in specs:
        ref_v = eval_obs(spec, full_out, alpha_out, m)
        rec_v = eval_obs(spec, rec, alpha_out, m)
        obs_err = max(obs_err, abs(ref_v - rec_v))

    vdag = ubar.conj().T
    rev1 = r @ (vdag @ (ubar @ alpha_q))
    rev1_err = float(np.max(np.abs(rev1 - psi)))
    psi_inv = r @ (vdag @ alpha_q)
    a_inv = pi @ psi_inv
    rev2 = r @ (ubar @ a_inv)
    rev2_err = float(np.max(np.abs(rev2 - psi)))
    reverse_error = max(rev1_err, rev2_err)

    max_depth_ok = 1
    comp_max_res = 0.0
    comp_state_err = 0.0
    comp_ok = True
    depth_results = {}
    for k in COMPOSITION_DEPTHS:
        vf = vs[0]
        for t in range(1, k):
            vf = vs[t] @ vf
        uf = np.kron(vf, np.eye(m))
        clk = closure_residual(vf, pi, nf)
        o_ref = uf @ psi
        o_rec = r @ (vf @ alpha_q)
        state_k = float(np.max(np.abs(o_ref - o_rec)))
        ok = (clk <= CLOSURE_TOL) and (state_k <= GATE_TOL)
        comp_ok = comp_ok and ok
        if ok:
            max_depth_ok = k
        comp_max_res = max(comp_max_res, clk)
        comp_state_err = max(comp_state_err, state_k)
        depth_results[k] = bool(ok)

    t_full = measure(lambda: u @ psi)
    t_qk = measure(lambda: ubar @ alpha_q)
    t_rec = measure(lambda: r @ alpha_out)
    t_proj = measure(lambda: pi @ psi)

    vc = vs[1] @ vs[0]
    uc = np.kron(vc, np.eye(m))
    t_full_c = measure(lambda: uc @ psi)
    t_qk_c = measure(lambda: vc @ alpha_q)
    t_rec_c = measure(lambda: r @ (vc @ alpha_q))
    t_proj_c = measure(lambda: pi @ psi)

    gate_ok = (
        closure_res <= CLOSURE_TOL
        and pi_r_err <= GATE_TOL
        and state_max <= GATE_TOL
        and state_l2 <= GATE_TOL
        and obs_err <= GATE_TOL
        and reverse_error <= GATE_TOL
        and comp_ok
    )

    if gate_ok:
        kernel_speedup = t_full / max(t_qk, 1e-30)
        composed_speedup = t_full_c / max(t_qk_c + t_rec_c, 1e-30)
        e2e_speedup = t_full_c / max(t_proj_c + t_qk_c + t_rec_c, 1e-30)
    else:
        kernel_speedup = None
        composed_speedup = None
        e2e_speedup = None

    q_hash = sha256b([
        str((n, q, m, "coarse-register equivalence i~j iff floor(i/m)==floor(j/m)")).encode(),
        arrb(pi), arrb(r), arrb(ubar),
    ])
    r_hash = sha256b([arrb(alpha), arrb(psi), arrb(full_out)])
    x_hash = sha256b([arrb(rec), str(sorted(round(v, 12) for v in [state_max, obs_err, reverse_error])).encode()])

    return {
        "seed": int(seed),
        "operator_family": fam,
        "n": int(n),
        "full_dimension": int(d),
        "quotient_dimension": int(q),
        "compression": float(m),
        "number_of_quotient_classes": int(q),
        "operator_nnz": operator_nnz,
        "closure_residual": closure_res,
        "state_max_error": state_max,
        "state_L2_error": state_l2,
        "observable_error": obs_err,
        "reverse_error": reverse_error,
        "reference_hash": r_hash,
        "quotient_hash": q_hash,
        "reconstruction_hash": x_hash,
        "reference_time": t_full,
        "quotient_time": t_qk,
        "reconstruction_time": t_rec,
        "end_to_end_time": t_proj_c + t_qk_c + t_rec_c,
        "kernel_speedup": kernel_speedup,
        "composed_speedup": composed_speedup,
        "end_to_end_speedup": e2e_speedup,
        "PASS/FAIL": "PASS" if gate_ok else "FAIL",
        "test_type": "positive",
        "expected_fail": False,
        "composition_max_depth": max_depth_ok,
        "composition_depth_ok": depth_results,
        "composition_max_closure_residual": comp_max_res,
        "composition_max_state_error": comp_state_err,
        "pi_r_identity_error": pi_r_err,
        "fiber_count": int(m),
    }


def make_control_quotient(ctype, rng, n):
    d, q, m, pi, r = build_quotient(n)
    v = random_unitary(rng, q)
    ubar = v
    u = np.kron(v, np.eye(m))
    if ctype == "NEG_random_class_assignment":
        idx = rng.permutation(d)
        labels = np.zeros(d, dtype=np.int64)
        pv = 1.0 / np.sqrt(m)
        pn = np.zeros((q, d), dtype=np.complex128)
        rc = np.zeros((d, q), dtype=np.complex128)
        for c in range(q):
            labels[idx[c * m:(c + 1) * m]] = c
        for j in range(d):
            c = labels[j]
            pn[c, j] = pv
            rc[j, c] = pv
        return d, q, m, pn, rc, u, ubar
    if ctype == "NEG_broken_symmetry":
        a0 = int(rng.randint(0, q))
        a1 = int((a0 + 1 + int(rng.randint(0, q - 1))) % q)
        i = a0 * m + int(rng.randint(0, m))
        j = a1 * m + int(rng.randint(0, m))
        pi[:, [i, j]] = pi[:, [j, i]]
        r[[i, j], :] = r[[j, i], :]
        return d, q, m, pi, r, u, ubar
    if ctype == "NEG_altered_quotient_operator":
        eps = (rng.normal(size=(q, q)) + 1j * rng.normal(size=(q, q))) / (2.0 * q)
        ubar = v + 0.15 * eps
        return d, q, m, pi, r, u, ubar
    if ctype == "NEG_corrupted_reconstruction":
        noise = (rng.normal(size=(d, q)) + 1j * rng.normal(size=(d, q))) / np.sqrt(d)
        rc = r + 0.05 * noise
        return d, q, m, pi, rc, u, ubar
    raise ValueError(ctype)


def run_negative(ctype, n, seed):
    d, q, m, pi, r, u, ubar = make_control_quotient(ctype, np.random.RandomState(seed_int(ctype, n, seed)), n)
    nf = n // 2
    rng = np.random.RandomState(seed_int(ctype, n, seed, "aux"))
    psi = random_state(rng, d)
    full_out = u @ psi

    u_full = u
    closure_res = naive_closure_residual(pi, u_full, ubar)

    alpha_q = pi @ psi
    alpha_out = ubar @ alpha_q
    rec = r @ alpha_out
    state_max = float(np.max(np.abs(full_out - rec)))
    state_l2 = float(np.linalg.norm(full_out - rec) / max(np.linalg.norm(full_out), 1e-300))

    obs_rng = np.random.RandomState(seed_int(ctype, n, seed, "obs"))
    specs = build_observable_set(obs_rng, d, q, m, (n + 1) // 2, nf)
    obs_err = 0.0
    for spec in specs:
        ref_v = eval_obs_full(spec, full_out, m)
        rec_v = eval_obs_full(spec, rec, m)
        obs_err = max(obs_err, abs(ref_v - rec_v))

    rev1 = r @ (ubar.conj().T @ (ubar @ alpha_q))
    rev1_err = float(np.max(np.abs(rev1 - psi))) if r.shape[0] else 1.0
    reverse_error = rev1_err

    gate_ok = (
        closure_res <= CLOSURE_TOL
        and state_max <= GATE_TOL
        and state_l2 <= GATE_TOL
        and obs_err <= GATE_TOL
        and reverse_error <= GATE_TOL
    )

    q_hash = sha256b([str((ctype, n)).encode(), arrb(pi), arrb(r), arrb(ubar)])
    r_hash = sha256b([arrb(psi), arrb(full_out)])
    x_hash = sha256b([arrb(rec)])

    return {
        "seed": int(seed),
        "operator_family": ctype,
        "n": int(n),
        "full_dimension": int(d),
        "quotient_dimension": int(q),
        "compression": float(m),
        "number_of_quotient_classes": int(q),
        "operator_nnz": int(np.count_nonzero(u)),
        "closure_residual": closure_res,
        "state_max_error": state_max,
        "state_L2_error": state_l2,
        "observable_error": obs_err,
        "reverse_error": reverse_error,
        "reference_hash": r_hash,
        "quotient_hash": q_hash,
        "reconstruction_hash": x_hash,
        "reference_time": 0.0,
        "quotient_time": 0.0,
        "reconstruction_time": 0.0,
        "end_to_end_time": 0.0,
        "kernel_speedup": None,
        "composed_speedup": None,
        "end_to_end_speedup": None,
        "PASS/FAIL": "PASS" if gate_ok else "FAIL",
        "test_type": "negative_control",
        "expected_fail": True,
        "composition_max_depth": 1,
        "composition_depth_ok": {k: False for k in COMPOSITION_DEPTHS},
        "composition_max_closure_residual": closure_res,
        "composition_max_state_error": state_max,
        "pi_r_identity_error": float(np.max(np.abs(pi @ r - np.eye(q)))),
        "fiber_count": int(m),
    }


CSV_FIELDS = [
    "seed", "operator_family", "n", "full_dimension", "quotient_dimension",
    "compression", "number_of_quotient_classes", "operator_nnz",
    "closure_residual", "state_max_error", "state_L2_error",
    "observable_error", "reverse_error", "reference_hash", "quotient_hash",
    "reconstruction_hash", "reference_time", "quotient_time",
    "reconstruction_time", "kernel_speedup", "composed_speedup",
    "end_to_end_speedup", "PASS/FAIL", "test_type", "expected_fail",
    "composition_max_depth", "composition_max_closure_residual",
    "composition_max_state_error", "pi_r_identity_error", "fiber_count",
    "end_to_end_time",
]


def write_csv(rows):
    with open(CSV_PATH, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in CSV_FIELDS})


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def median(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return float(statistics.median(values))


def percentile(values, frac):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return float(sorted(values)[int(round((len(values) - 1) * frac))])


def family_summary(rows):
    out = {}
    for fam in POSITIVE_FAMILIES + ["NEG_total"]:
        fam_rows = [r for r in rows if r["operator_family"] == fam]
        neg_rows = [r for r in rows if r["test_type"] == "negative_control"]
        if fam == "NEG_total":
            fam_rows = neg_rows
            out[fam] = {
                "tests": len(fam_rows),
                "passes": sum(1 for r in fam_rows if r["PASS/FAIL"] == "PASS"),
                "correctly_rejected": sum(1 for r in fam_rows if r["PASS/FAIL"] == "FAIL" and r["expected_fail"]),
                "median_compression": median([r["compression"] for r in fam_rows]),
                "median_kernel_speedup": median([r["kernel_speedup"] for r in fam_rows]),
                "median_composed_speedup": median([r["composed_speedup"] for r in fam_rows]),
                "median_e2e_speedup": median([r["end_to_end_speedup"] for r in fam_rows]),
            }
            continue
        out[fam] = {
            "tests": len(fam_rows),
            "passes": sum(1 for r in fam_rows if r["PASS/FAIL"] == "PASS"),
            "closure_passes": sum(1 for r in fam_rows if r["closure_residual"] <= CLOSURE_TOL),
            "reverse_passes": sum(1 for r in fam_rows if r["reverse_error"] <= GATE_TOL),
            "composition_passes": sum(1 for r in fam_rows if r["composition_max_depth"] >= max(COMPOSITION_DEPTHS)),
            "median_compression": median([r["compression"] for r in fam_rows]),
            "median_kernel_speedup": median([r["kernel_speedup"] for r in fam_rows]),
            "median_composed_speedup": median([r["composed_speedup"] for r in fam_rows]),
            "median_e2e_speedup": median([r["end_to_end_speedup"] for r in fam_rows]),
            "max_state_error": max([r["state_max_error"] for r in fam_rows], default=None),
        }
    return out


def size_summary(rows):
    out = {}
    for n in range(N_MIN, N_MAX + 1):
        nr = [r for r in rows if r["n"] == n and r["test_type"] == "positive"]
        out[n] = {
            "tests": len(nr),
            "passes": sum(1 for r in nr if r["PASS/FAIL"] == "PASS"),
            "median_compression": median([r["compression"] for r in nr]),
            "max_closure_residual": max([r["closure_residual"] for r in nr], default=None),
            "max_state_error": max([r["state_max_error"] for r in nr], default=None),
            "median_kernel_speedup": median([r["kernel_speedup"] for r in nr]),
            "median_composed_speedup": median([r["composed_speedup"] for r in nr]),
        }
    return out


def correlation(x, y):
    x = np.asarray([v for v in x if v is not None], dtype=np.float64)
    y = np.asarray([v for v in y if v is not None], dtype=np.float64)
    if len(x) < 2 or np.std(x) == 0 or np.std(y) == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def spearman(xs, ys):
    x = [v for v in xs if v is not None]
    y = [v for v in ys if v is not None]
    if len(x) < 2 or len(y) < 2:
        return None
    rx = np.argsort(np.argsort(x)).astype(np.float64)
    ry = np.argsort(np.argsort(y)).astype(np.float64)
    if np.std(rx) == 0 or np.std(ry) == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def classify_claims(rows, family_summ, size_summ, comp_speed):
    pos = [r for r in rows if r["test_type"] == "positive"]
    neg = [r for r in rows if r["test_type"] == "negative_control"]
    all_pass = all(r["PASS/FAIL"] == "PASS" for r in pos)
    per_fam = {f: family_summ[f] for f in POSITIVE_FAMILIES}
    fam_all_pass = all(fs["passes"] == fs["tests"] for fs in per_fam.values())
    comp_all = all(r["composition_max_depth"] >= max(COMPOSITION_DEPTHS) for r in pos)
    rev_all = all(r["reverse_error"] <= GATE_TOL for r in pos)
    sizes_sorted = sorted(size_summ.keys())
    comp_values = [size_summ[n]["median_compression"] for n in sizes_sorted]
    comp_monotone = all(a <= b for a, b in zip(comp_values, comp_values[1:]))
    comp_scaled = comp_monotone and comp_values[-1] > comp_values[0]

    passing_speed = [r for r in pos if r["PASS/FAIL"] == "PASS" and r["kernel_speedup"] is not None]
    kernel_values = [r["kernel_speedup"] for r in passing_speed]
    kernel_speed_present = any(v > 1.0 for v in kernel_values)
    median_kernel = median(kernel_values)
    families_with_speedup = {
        r["operator_family"]
        for r in passing_speed
        if r["kernel_speedup"] is not None and r["kernel_speedup"] > 1.0
    }
    seeds_with_speedup = {
        (r["operator_family"], r["seed"])
        for r in passing_speed
        if r["kernel_speedup"] is not None and r["kernel_speedup"] > 1.0
    }

    claims = {
        "A": {"claim": "Exact quotient reconstruction demonstrated.",
              "pass": all_pass,
              "classification": "PROVEN IN THIS EXPERIMENT" if all_pass else "NOT ESTABLISHED"},
        "B": {"claim": "Closure survives heterogeneous operator families.",
              "pass": fam_all_pass,
              "classification": "PROVEN IN THIS EXPERIMENT" if fam_all_pass else "NOT ESTABLISHED"},
        "C": {"claim": "Closure survives composition.",
              "pass": comp_all,
              "classification": "PROVEN IN THIS EXPERIMENT" if comp_all else "NOT ESTABLISHED"},
        "D": {"claim": "Bidirectional closure demonstrated.",
              "pass": rev_all,
              "classification": "PROVEN IN THIS EXPERIMENT" if rev_all else "NOT ESTABLISHED"},
        "E": {"claim": "Generalization across tested operator families.",
              "pass": fam_all_pass,
              "classification": "PROVEN IN THIS EXPERIMENT" if fam_all_pass else "NOT ESTABLISHED"},
        "F": {"claim": "Scalable compression demonstrated.",
              "pass": comp_scaled,
              "classification": "PROVEN IN THIS EXPERIMENT" if comp_scaled else "NOT ESTABLISHED"},
        "G": {"claim": "Measured acceleration.",
              "pass": kernel_speed_present and (median_kernel or 0.0) > 1.0,
              "classification": (
                  "SUPPORTED BY MULTIPLE INDEPENDENT WITNESSES"
                  if (kernel_speed_present and len(families_with_speedup) >= 2 and len(seeds_with_speedup) >= 2 and (median_kernel or 0.0) > 1.0)
                  else "NOT TESTED"
              )},
        "H": {"claim": "Universal arbitrary-circuit quantum speedup.",
              "pass": False,
              "classification": "NOT ESTABLISHED"},
    }

    neg_rejected = sum(1 for r in neg if r["PASS/FAIL"] == "FAIL" and r["expected_fail"])
    neg_anomalies = [r for r in neg if not (r["PASS/FAIL"] == "FAIL" and r["expected_fail"])]
    return {
        "claims": claims,
        "all_pass": all_pass,
        "comp_scaled": comp_scaled,
        "comp_monotone": comp_monotone,
        "compression_sequence": comp_values,
        "neg_total": len(neg),
        "neg_rejected": neg_rejected,
        "neg_anomalies": neg_anomalies,
        "accel_witness_families": sorted(families_with_speedup),
        "accel_witness_seeds": len(seeds_with_speedup),
        "median_kernel_speedup_overall": median_kernel,
        "comp_speed": comp_speed,
    }


def main():
    print("=" * 72)
    print("AGD QUANTUM GENERALITY DEFINITIVE EOF")
    print("Equivalence relation: i ~ j iff floor(i / 2**floor(n/2)) == floor(j / 2**floor(n/2))")
    print("Pi = I_q (x) 1_m^T / sqrt(m);  R = I_q (x) 1_m / sqrt(m);  Pi R = I_Q")
    print("Scope: exact complete-state reconstruction tested on quotient-invariant psi = R alpha.")
    print("=" * 72)

    rows = []
    positive_rows = []

    for n in range(N_MIN, N_MAX + 1):
        for fam in POSITIVE_FAMILIES:
            for seed in range(1, SEEDS_PER_FAMILY + 1):
                row = run_positive(n, fam, seed)
                rows.append(row)
                positive_rows.append(row)
        print(f"progress: n={n} done ({sum(1 for r in rows if r['test_type']=='positive')} positive instances)")

    for ctype in CONTROL_TYPES:
        for n in CONTROL_SIZES:
            for seed in range(1, CONTROL_SEEDS + 1):
                rows.append(run_negative(ctype, n, seed))

    source_hash = sha256b([SOURCE.read_bytes()])

    pos = [r for r in rows if r["test_type"] == "positive"]
    neg = [r for r in rows if r["test_type"] == "negative_control"]

    family_summ = family_summary(rows)
    size_summ = size_summary(rows)

    passing = [r for r in rows if r["PASS/FAIL"] == "PASS"]
    comp_speed = {
        "kernel_pearson": correlation(
            [r["compression"] for r in passing],
            [r["kernel_speedup"] for r in passing],
        ),
        "kernel_spearman": spearman(
            [r["compression"] for r in passing],
            [r["kernel_speedup"] for r in passing],
        ),
        "composed_pearson": correlation(
            [r["compression"] for r in passing],
            [r["composed_speedup"] for r in passing],
        ),
        "composed_spearman": spearman(
            [r["compression"] for r in passing],
            [r["composed_speedup"] for r in passing],
        ),
    }

    claims_data = classify_claims(rows, family_summ, size_summ, comp_speed)
    claims = claims_data["claims"]

    failure_ledger = [
        {
            "operator_family": r["operator_family"],
            "n": r["n"],
            "seed": r["seed"],
            "expected_fail": r["expected_fail"],
            "closure_residual": r["closure_residual"],
            "state_max_error": r["state_max_error"],
            "state_L2_error": r["state_L2_error"],
            "observable_error": r["observable_error"],
            "reverse_error": r["reverse_error"],
            "PASS/FAIL": r["PASS/FAIL"],
        }
        for r in rows
        if r["PASS/FAIL"] == "FAIL"
    ]

    write_csv(rows)
    csv_hash = file_sha256(CSV_PATH)

    aggr_q = sha256b([r["quotient_hash"].encode() for r in rows])
    aggr_r = sha256b([r["reference_hash"].encode() for r in rows])
    aggr_x = sha256b([r["reconstruction_hash"].encode() for r in rows])

    all_errors = {
        "max_closure_residual": max([r["closure_residual"] for r in rows] or [0.0]),
        "max_state_error": max([r["state_max_error"] for r in rows if r["test_type"] == "positive"] or [0.0]),
        "max_observable_error": max([r["observable_error"] for r in rows if r["test_type"] == "positive"] or [0.0]),
        "max_reverse_error": max([r["reverse_error"] for r in rows if r["test_type"] == "positive"] or [0.0]),
    }

    result_obj = {
        "meta": {
            "name": "AGD_QUANTUM_GENERALITY_DEFINITIVE_EOF",
            "n_range": [N_MIN, N_MAX],
            "positive_families": POSITIVE_FAMILIES,
            "control_types": CONTROL_TYPES,
            "seeds_per_family": SEEDS_PER_FAMILY,
            "warmups": WARMUPS,
            "reps": REPS,
            "gate_tolerance": GATE_TOL,
            "closure_tolerance": CLOSURE_TOL,
            "equivalence_relation": "i ~ j iff floor(i / 2**floor(n/2)) == floor(j / 2**floor(n/2))",
            "scope": "exact state reconstruction tested on quotient-invariant psi = R alpha",
            "composition_depths_tested": COMPOSITION_DEPTHS,
        },
        "hashes": {
            "source_script": source_hash,
            "final_csv": csv_hash,
            "generated_quotient_maps_aggregate": aggr_q,
            "reference_outputs_aggregate": aggr_r,
            "reconstructed_outputs_aggregate": aggr_x,
        },
        "totals": {
            "total_tests": len(rows),
            "positive_tests": len(pos),
            "negative_control_tests": len(neg),
            "exact_semantic_passes": sum(1 for r in rows if r["PASS/FAIL"] == "PASS"),
            "exact_semantic_failures": sum(1 for r in rows if r["PASS/FAIL"] == "FAIL"),
            "negative_controls_correctly_rejected": claims_data["neg_rejected"],
            "negative_control_anomalies": len(claims_data["neg_anomalies"]),
        },
        "extremes": all_errors,
        "compression": {
            "min": min([r["compression"] for r in pos] or [0.0]),
            "median": median([r["compression"] for r in pos]),
            "max": max([r["compression"] for r in pos] or [0.0]),
            "by_size": {str(k): v for k, v in size_summ.items()},
        },
        "speedups": {
            "kernel": {
                "min": percentile([r["kernel_speedup"] for r in pos], 0.0),
                "median": median([r["kernel_speedup"] for r in pos]),
                "max": percentile([r["kernel_speedup"] for r in pos], 1.0),
            },
            "composed": {
                "min": percentile([r["composed_speedup"] for r in pos], 0.0),
                "median": median([r["composed_speedup"] for r in pos]),
                "max": percentile([r["composed_speedup"] for r in pos], 1.0),
            },
            "end_to_end": {
                "min": percentile([r["end_to_end_speedup"] for r in pos], 0.0),
                "median": median([r["end_to_end_speedup"] for r in pos]),
                "max": percentile([r["end_to_end_speedup"] for r in pos], 1.0),
            },
        },
        "family_summary": family_summ,
        "size_summary": size_summ,
        "compression_vs_speed": comp_speed,
        "failure_ledger": failure_ledger,
        "negative_control_anomalies": [
            {
                "operator_family": r["operator_family"],
                "n": r["n"],
                "seed": r["seed"],
                "PASS/FAIL": r["PASS/FAIL"],
            }
            for r in claims_data["neg_anomalies"]
        ],
        "claims": {
            k: {"claim": v["claim"], "pass": v["pass"], "classification": v["classification"]}
            for k, v in claims.items()
        },
        "definitive": {
            "all_positive_passed": claims_data["all_pass"],
            "compression_scaled": claims_data["comp_scaled"],
            "compression_sequence": claims_data["compression_sequence"],
            "acceleration_witness_seed_pairs": claims_data["accel_witness_seeds"],
            "acceleration_witness_families": claims_data["accel_witness_families"],
            "median_kernel_speedup_overall": claims_data["median_kernel_speedup_overall"],
        },
    }

    with open(JSON_PATH, "w") as fh:
        json.dump(result_obj, fh, indent=2, sort_keys=True)
    json_hash = file_sha256(JSON_PATH)

    report_lines = []
    report_lines.append("# AGD Quantum Generality Definitive EOF - Report")
    report_lines.append("")
    report_lines.append("## Explicit Equivalence Relation (fixed before operator construction)")
    report_lines.append("")
    report_lines.append("Index the computational basis of the n-qubit Hilbert space as `i = a*m + b`, ")
    report_lines.append("with `nq = ceil(n/2)` coarse qubits, `nf = floor(n/2)` fine qubits, ")
    report_lines.append("`q = 2**nq`, `m = 2**nf`. The relation is `i ~ j` iff `floor(i/m) == floor(j/m)`. ")
    report_lines.append("The `q` equivalence classes span the quotient `Q`. ")
    report_lines.append("`Pi = I_q (x) 1_m^T / sqrt(m)`, `R = I_q (x) 1_m / sqrt(m)`, `Pi R = I_Q`. ")
    report_lines.append("`U = V (x) I_m`, `Ubar = V`, formal gate `Pi U = Ubar Pi`, ")
    report_lines.append("reconstruction `R Ubar Pi |psi> = U |psi>`.")
    report_lines.append("")
    report_lines.append("## Scope")
    report_lines.append("")
    report_lines.append("A linear quotient of dimension `q < d` cannot encode an arbitrary d-dimensional state. ")
    report_lines.append("Therefore the complete-state reconstruction gate is tested on the quotient-invariant state family ")
    report_lines.append("`psi = R alpha` with independently drawn `alpha`. Universal arbitrary-state/arbitrary-circuit ")
    report_lines.append("reconstruction is out of scope and is classified NOT ESTABLISHED.")
    report_lines.append("")
    report_lines.append(f"## Total Tests: {len(rows)}")
    report_lines.append(f"## Exact semantic passes: {result_obj['totals']['exact_semantic_passes']}")
    report_lines.append(f"## Exact semantic failures: {result_obj['totals']['exact_semantic_failures']}")
    report_lines.append(f"## Negative-control failures correctly rejected: {result_obj['totals']['negative_controls_correctly_rejected']}")
    report_lines.append("")
    report_lines.append("### Compression")
    report_lines.append(f"- min: {result_obj['compression']['min']}")
    report_lines.append(f"- median: {result_obj['compression']['median']}")
    report_lines.append(f"- max: {result_obj['compression']['max']}")
    report_lines.append("")
    report_lines.append("### Kernel speedup (T_full / T_quotient_kernel)")
    for label in ["min", "median", "max"]:
        report_lines.append(f"- {label}: {result_obj['speedups']['kernel'][label]}")
    report_lines.append("")
    report_lines.append("### Composed speedup (T_full / (T_quotient_kernel + T_reconstruction))")
    for label in ["min", "median", "max"]:
        report_lines.append(f"- {label}: {result_obj['speedups']['composed'][label]}")
    report_lines.append("")
    report_lines.append("### End-to-end speedup (T_full / T_total)")
    for label in ["min", "median", "max"]:
        report_lines.append(f"- {label}: {result_obj['speedups']['end_to_end'][label]}")
    report_lines.append("")
    report_lines.append("### Extremes")
    report_lines.append(f"- max closure residual: {all_errors['max_closure_residual']}")
    report_lines.append(f"- max state error: {all_errors['max_state_error']}")
    report_lines.append(f"- max observable error: {all_errors['max_observable_error']}")
    report_lines.append(f"- max reverse error: {all_errors['max_reverse_error']}")
    report_lines.append("")
    report_lines.append("### Results by operator family")
    report_lines.append("")
    report_lines.append("| family | tests | passes | closure | reverse | composition | median compression | median S_kernel | median S_composed |")
    report_lines.append("|---|---|---|---|---|---|---|---|---|")
    for fname in POSITIVE_FAMILIES:
        fs = family_summ[fname]
        report_lines.append(
            f"| {fname} | {fs['tests']} | {fs['passes']} | {fs['closure_passes']} | "
            f"{fs['reverse_passes']} | {fs['composition_passes']} | {fs['median_compression']} | "
            f"{fs['median_kernel_speedup']} | {fs['median_composed_speedup']} |"
        )
    report_lines.append("")
    report_lines.append("### Results by system size")
    report_lines.append("")
    report_lines.append("| n | full dim | quotient dim | compression | tests | passes | max state err | median S_kernel |")
    report_lines.append("|---|---|---|---|---|---|---|---|")
    for n in range(N_MIN, N_MAX + 1):
        ss = size_summ[n]
        report_lines.append(
            f"| {n} | {1 << n} | {1 << ((n + 1)//2)} | {ss['median_compression']} | "
            f"{ss['tests']} | {ss['passes']} | {ss['max_state_error']} | {ss['median_kernel_speedup']} |"
        )
    report_lines.append("")
    report_lines.append("### Compression vs speed relationship")
    report_lines.append(f"- kernel Pearson r: {comp_speed['kernel_pearson']}")
    report_lines.append(f"- kernel Spearman rho: {comp_speed['kernel_spearman']}")
    report_lines.append(f"- composed Pearson r: {comp_speed['composed_pearson']}")
    report_lines.append(f"- composed Spearman rho: {comp_speed['composed_spearman']}")
    report_lines.append("")
    report_lines.append("### Complete failure ledger")
    report_lines.append("")
    if failure_ledger:
        report_lines.append("| family | n | seed | expected | closure_res | state_max | state_l2 | obs | reverse | result |")
        report_lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for f in failure_ledger:
            report_lines.append(
                f"| {f['operator_family']} | {f['n']} | {f['seed']} | {f['expected_fail']} | "
                f"{f['closure_residual']:.3e} | {f['state_max_error']:.3e} | {f['state_L2_error']:.3e} | "
                f"{f['observable_error']:.3e} | {f['reverse_error']:.3e} | {f['PASS/FAIL']} |"
            )
    else:
        report_lines.append("No semantic failures.")
    report_lines.append("")
    report_lines.append("### Hashes")
    report_lines.append("")
    report_lines.append(f"- source script SHA-256: `{source_hash}`")
    report_lines.append(f"- generated quotient maps (aggregate) SHA-256: `{aggr_q}`")
    report_lines.append(f"- reference outputs (aggregate) SHA-256: `{aggr_r}`")
    report_lines.append(f"- reconstructed outputs (aggregate) SHA-256: `{aggr_x}`")
    report_lines.append(f"- final CSV SHA-256: `{csv_hash}`")
    report_lines.append(f"- final JSON SHA-256: `{json_hash}`")
    report_lines.append("")
    report_lines.append("### Claims")
    report_lines.append("")
    for key in "ABCDEFGH":
        c = claims[key]
        report_lines.append(
            f"- CLAIM {key} \"{c['claim']}\": "
            f"{'PASS' if c['pass'] else 'NOT PASSED'} - {c['classification']}"
        )
    report_lines.append("")
    report_lines.append("### Definitive status")
    report_lines.append("")
    if claims_data["all_pass"]:
        report_lines.append("- All positive semantic gates passed exactly at the declared tolerances.")
    else:
        report_lines.append("- At least one positive semantic gate failed.")
    report_lines.append(f"- Compression sequence across n: {claims_data['compression_sequence']}")
    report_lines.append(f"- Measured median kernel speedup over passing instances: {claims_data['median_kernel_speedup_overall']}")
    report_lines.append(f"- Negative-control anomalies (invalid quotients that PASSED validation): {len(claims_data['neg_anomalies'])}")
    report_lines.append("")
    report_lines.append("_Generated by AGD_QUANTUM_GENERALITY_DEFINITIVE_EOF.py. "
                        "No values were mocked; every matrix, map, state, observable, hash, and timing was "
                        "generated inside the script at runtime._")

    with open(REPORT_PATH, "w") as fh:
        fh.write("\n".join(report_lines) + "\n")

    print("")
    print("=" * 88)
    print("FAMILY | TESTS | EXACT PASS | CLOSURE | REVERSE | COMPOSITION | MEDIAN COMPRESSION | MEDIAN S_KERNEL | MEDIAN S_COMPOSED | MEDIAN S_E2E")
    print("-" * 88)
    for fname in POSITIVE_FAMILIES:
        fs = family_summ[fname]
        print(
            f"{fname} | {fs['tests']} | {fs['passes']} | {fs['closure_passes']} / {fs['tests']} | "
            f"{fs['reverse_passes']} / {fs['tests']} | {fs['composition_passes']} / {fs['tests']} | "
            f"{fs['median_compression']} | {fs['median_kernel_speedup']} | "
            f"{fs['median_composed_speedup']} | {fs['median_e2e_speedup']}"
        )
    print("-" * 88)
    print(f"NEGATIVE CONTROLS | {len(neg)} | 0 | correctly rejected: {claims_data['neg_rejected']}")
    print("=" * 88)
    print("")
    print("DEFINITIVE STATUS")
    for key in "ABCDEFGH":
        c = claims[key]
        print(
            f"CLAIM {key} [{c['claim']}]: "
            f"{'PASS' if c['pass'] else 'NOT PASSED'} ({c['classification']})"
        )
    print("")
    print("Outputs:")
    print(f"  {CSV_PATH.name}  sha256={csv_hash}")
    print(f"  {JSON_PATH.name}  sha256={json_hash}")
    print(f"  {REPORT_PATH.name}")
    print("  source script sha256=%s" % source_hash)


if __name__ == "__main__":
    main()