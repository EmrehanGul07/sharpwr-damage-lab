---
paths:
  - "game/packages/com.sharpwr.sim/**"
  - "game/sim/**"
  - "game/server/**"
---
# Simulation core rules

- Pure C#; the asmdef has `noEngineReferences: true`. Never add `using UnityEngine`.
- Numbers: `Fix64` only. Build constants with `Fix64.Ratio(num, den)` or `Fix64.Parse("decimal")`
  at load time; prefer exact integer ratios (single rounding). No `float`/`double` except
  diagnostics accessors marked `// sim-lint: allow(floating-point) <reason>`.
- Time: `SimTime` microseconds. Schedule events with `CombatScheduler`; never compare ticks to
  wall clock. Default 30 Hz fixed step (`SimClock`).
- Ordering: iterate entities by ascending id; events by (µs, phase, sequence). No
  `Dictionary`/`HashSet` enumeration in gameplay paths (lookup-only use needs
  `// sim-lint: allow(unordered-collection) lookup-only`).
- Randomness: `DeterministicRandom` streams derived from the match seed; one stream per purpose.
- No static mutable state; everything lives in the world state so SaveState/LoadState and
  state hashing stay complete.
- No allocations in the per-tick path (pool buffers).
- Validation failures emit one `Rejected` event and change nothing else.
- Every formula has a test first; parity values come from `game/parity/fixtures/` only.
- Operation order in formulas is part of the contract with `tools/parity/fixed_point_model.py`;
  change both together and regenerate vectors.
