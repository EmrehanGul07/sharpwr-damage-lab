---
name: parity-check
description: Compare the C# simulation against the Python Damage Lab reference — regenerate parity fixtures and Fix64 vectors, run the bit-exact model and C# parity tests, and produce a damage comparison report. Use after any change to combat formulas, numerics, content values or the Python reference, and for milestone damage reports.
---
# Parity check

1. Regenerate generated inputs (never edit them by hand):
   ```sh
   python -I tools/parity/export_parity_fixtures.py
   python -I tools/parity/emit_fix64_vectors.py
   git diff --stat game/parity   # any change must be explained (formula change? reference change?)
   ```
2. Model-level parity (no .NET needed):
   ```sh
   python -I -m unittest discover -s tools/parity -p "test_*.py" -v
   ```
   It prints `max |fixed - reference|` per kind; record it.
3. C# parity (needs .NET 8 SDK):
   ```sh
   dotnet test game/sim/tests/SharpWR.Sim.Tests.csproj --nologo --logger "trx;LogFileName=parity.trx"
   ```
   If .NET is unavailable, say so explicitly in the report — do not claim C# parity.
4. Damage comparison report → `docs/moba/milestones/<milestone>-parity.md`:
   one row per case group (level stats, resistance, abilities per slot/rank, timeline scenario)
   with: cases, max |Δ|, tolerance, pass/fail, data status of inputs (from the fixture and
   content provenance), and the fixture fingerprint (Damage Lab version + git head).
5. Failures: never loosen a tolerance or edit a fixture to pass. Find whether the C# formula
   order, the content value, or the reference changed; route to the owner.
