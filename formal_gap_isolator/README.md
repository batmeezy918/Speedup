# PCSS Formal Gap Isolator

Executable first-class gap extraction layer for the recursive proof-carrying speedup workflow.

## Operational loop

`Evidence -> Gate State -> Formal Gap -> Dependency Resolution -> Closure Plan -> Targeted Evidence -> Reassessment`

A gap is represented as a typed object with parent run/scenario identity, status, failed obligation, dependencies, candidate derivations, required experiment/telemetry, and a closure predicate.

## Safety invariant

This component **never promotes evidence** and cannot produce a VERIFIED primitive. It only converts unmet evidence obligations into explicit machine-readable work items.

## Run

```bash
python3 formal_gap_isolator/gap_isolator.py CERTIFICATE.json OUT_DIR
```

## Tests

```bash
python3 -m pytest -q formal_gap_isolator/tests
```
