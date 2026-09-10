#!/usr/bin/env python3
"""Silicon Speedup next-elevation EOF.

Adversarial claim-salvage certificate generator.
Rule: CLAIM STRENGTH <= EVIDENCE STRENGTH.
It preserves structural/runtime/formal boundaries and never upgrades
an unsupported universal claim.
"""
import argparse, hashlib, json, platform, time
from pathlib import Path

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def check(ok, reason):
    return {'status': 'PASS' if ok else 'FAIL', 'reason': reason}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, required=True)
    ap.add_argument('--sim2xr', type=Path)
    ap.add_argument('--emit', type=Path, default=Path('EOF_NEXT_ELEVATION_CERTIFICATE.json'))
    args = ap.parse_args()

    root = args.results
    cert = {
        'schema': 'SILICON_SPEEDUP_NEXT_ELEVATION_EOF_V1',
        'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'host': {'platform': platform.platform(), 'machine': platform.machine(), 'python': platform.python_version()},
        'claim_discipline': 'CLAIM STRENGTH <= EVIDENCE STRENGTH',
        'checks': {}, 'claims': []
    }
    if not root.exists():
        cert['checks']['results_root'] = check(False, f'missing results root: {root}')
        cert['status'] = 'BLOCKED'
        args.emit.write_text(json.dumps(cert, indent=2))
        print(json.dumps(cert, indent=2)); return 2

    files = sorted(p for p in root.rglob('*') if p.is_file())
    cert['inventory'] = [{'path': str(p.relative_to(root)), 'sha256': sha256_file(p), 'bytes': p.stat().st_size} for p in files]
    cert['checks']['results_root'] = check(True, f'{len(files)} evidence files inventoried')

    blobs = []
    for p in files:
        if p.suffix.lower() in {'.json','.txt','.log','.md','.csv'}:
            try: blobs.append(p.read_text(errors='replace'))
            except Exception: pass
    joined = '\n'.join(blobs)
    facts = {
        'omega_only_falsified': 'OMEGA-ONLY: FALSIFIED' in joined,
        'universal_intertwining_not_established': 'UNIVERSAL INTERTWINING: NOT_ESTABLISHED' in joined,
        'canonical_exact': 'CANONICAL EXACT: True' in joined,
        'python_reference_only': 'RUNTIME REFERENCE_PYTHON_ONLY' in joined,
        'lean_not_bound': 'LEAN NOT_BOUND' in joined,
        'pcss_not_closed': 'PCSS NOT_CLOSED' in joined,
    }
    cert['checks']['adversarial_boundaries'] = {
        'status': 'PASS' if facts['omega_only_falsified'] else 'FAIL',
        'facts': facts,
        'reason': 'Retain the Omega-only falsification and do not promote universal intertwining.'
    }
    if facts['canonical_exact']:
        cert['claims'].append({'claim':'canonical execution equality','class':'STRONG_LOCAL','status':'SALVAGED','scope':'exact inventoried scenario'})
    if facts['omega_only_falsified']:
        cert['claims'].append({'claim':'Omega-only quotient is insufficient for general GEMM equivalence','class':'FAILED_AS_UNIVERSAL_CRITERION','status':'BOUNDARY_CONFIRMED'})
    if facts['universal_intertwining_not_established']:
        cert['claims'].append({'claim':'universal concrete GEMM operator intertwining','class':'OPEN','status':'BLOCKED'})
    if facts['python_reference_only']:
        cert['claims'].append({'claim':'native runtime speedup from V3','class':'OPEN_FROM_V3','status':'BLOCKED','reason':'V3 labels runtime evidence Python-reference-only'})
    if facts['lean_not_bound']:
        cert['claims'].append({'claim':'Lean-to-runtime binding','class':'OPEN','status':'BLOCKED'})
    if facts['pcss_not_closed']:
        cert['claims'].append({'claim':'publication gate','class':'QUARANTINED','status':'BLOCKED','reason':'PCSS not closed'})

    if args.sim2xr:
        if args.sim2xr.exists():
            cert['sim2xr_certificate_sha256'] = sha256_file(args.sim2xr)
            cert['checks']['sim2xr_certificate'] = check(True, 'certificate loaded')
        else:
            cert['checks']['sim2xr_certificate'] = check(False, f'missing: {args.sim2xr}')

    cert['required_next_closure'] = [
        'concrete GEMM Respects/operator intertwining',
        'arbitrary-fibre reconstruction',
        'executable cost binding',
        'fair frozen baseline',
        'independent rerun',
        'Lean scenario binding',
        'PCSS I ∧ R ∧ Q ∧ Q^-1 ∧ Ω ∧ X ∧ L'
    ]
    cert['status'] = 'SALVAGE_COMPLETE_PENDING_CLOSURE'
    args.emit.write_text(json.dumps(cert, indent=2))
    print(json.dumps(cert, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
