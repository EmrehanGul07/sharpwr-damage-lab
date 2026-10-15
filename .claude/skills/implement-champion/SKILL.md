---
name: implement-champion
description: Implement a champion kit in the SharpWR ability framework test-first — data definition, hooks for unique mechanics, gating of unsupported mechanics, parity and scenario tests. Use when adding or changing a champion (champion-implementer agent).
---
# Implement a champion

Prerequisites: content file exists and validates; parity fixtures exist for reference champions;
for original champions, design values with `original_design`/`original_placeholder` statuses.

1. Read `docs/moba/05-ability-framework.md` and the champion's content file. List each ability
   as: targeting / cast / cost / cooldown / delivery / effects / hooks / required fields.
2. Tests first in `game/sim/tests/Champions/<Id>/`:
   - damage per ability and rank vs fixture (reference) or vs design formula (original);
   - gates: cooldown, cost, lockouts, requirements (e.g. resource grade), out of range;
   - every unsupported mechanic: uncastable or effect absent, with the documented reason;
   - one scripted rotation scenario vs dummy, asserting event order and a determinism hash.
3. Express in content first; add hook classes under `Runtime/Champions/<Id>/` only for what
   data cannot express. Hooks never mutate state directly.
4. Run `python -I tools/ci/fast_checks.py` and `dotnet test`. Ownership diff for
   `champion-implementer` must pass.
5. Update the champion's supported/unsupported table (content + milestone report).
