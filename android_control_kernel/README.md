# Android Control Kernel

Native control/observation substrate for the Speedup Android fabric.

## Layers
1. **Capability** — filesystem, packages, UI/events, sensors, network, telemetry.
2. **Quotient** — equivalence/invariant representation and admissible descent.
3. **Operator registry** — executable speedup transformations with evidence class.
4. **Planner** — selects compatible operator chains.
5. **Runtime witness** — baseline/transformed execution and correctness measurement.
6. **Receipt** — immutable JSON evidence with SHA-256 digest.
7. **Linux/voice bridge** — callable command surface.

No Tasker or Shizuku dependency is part of the core architecture.
Third-party providers, if ever used, are adapters only.
