# ADR-0002 · Q32.32 fixed point, 30 Hz fixed step, microsecond event queue

Status: accepted for M0 (validated by the Python bit-exact model) · Date: 2026-10-15

**Context.** Determinism across ARM/x64, Mono/IL2CPP and a .NET server is required for
server authority, replays and desync detection. The Damage Lab uses continuous float time and
must remain the parity oracle.

**Decision.** `Fix64` signed Q32.32 with exact 128-bit multiply (round half up), exact division
(round half away from zero), checked overflow, decimal-text parsing. `SimTime` int64 µs. 30 Hz
fixed step; events scheduled at exact µs and drained per tick in (µs, phase, sequence) order.
Constants with exact rational forms are written as integer ratios (e.g. growth units
`n(281+7n)/400`) — composing parsed decimals lost 1e-6 HP and failed parity in the spike.

**Evidence.** `tools/parity/test_fixed_point_model.py`: 15 level, 60 resistance, 270 ability,
12 AA-impact cases within tolerance; max errors stat 1.3e-8, damage 2.7e-7 HP, time 1.1 µs.
`test_csharp_algorithm_port.py`: transcribed C# Mul/Div equal the model on 40k fuzz pairs and
exact-tie cases (two rounding mutants are caught).

**Consequences.** No float in sim (lint-enforced); trig needs Fix64 implementations; diagnostics
convert to double only at the edge.
