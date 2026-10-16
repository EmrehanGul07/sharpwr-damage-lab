# M1 · Damage comparison report (Python Damage Lab vs C# simulation)

Fixture `samira-reference-v1` · Damage Lab 7.1.23 · exported at 9313ad3
C# CI run: run 38967987454 @ e02746e (ubuntu x64, ubuntu ARM64, windows, macOS: identical results)

## Formula cases

C# values are computed by the bit-exact Q32.32 model, which CI proves identical to `Fix64`
(`fix64-vectors-v1.json`). Every case: `M1-parity-cases.csv`.

| Group | Cases | Max abs delta | Tolerance | Result | Data status of inputs |
|---|---|---|---|---|---|
| level_stat | 60 | 1.31e-08 | 1e-06 | pass | damage_lab_preserved, wr_wiki |
| resistance | 60 | 1.27e-10 | 1e-09 | pass | formula |
| ability | 270 | 2.66e-07 | 0.001 | pass | damage_lab_user_sourced |

## Simulation scenarios (C# `Match` vs Python `replay_samira`)

- AA loop L1, 1500 HP / 50 armor at 525: 38 hits, kill at 49.725990 s, max |dt| 1.28e-6 s, max |d dmg| 1.72e-7 HP
- AA loop L9, 2000 HP / 50 armor at 400 (acceptance #3, limit 10 us): 36 hits, kill at 39.967595 s, max |dt| 3.25e-6 s, max |d dmg| 2.33e-7 HP
- AA loop L15, 2500 HP / 120 armor at 520: 52 hits, kill at 50.762079 s, max |dt| 2.48e-5 s (us-grid period rounding over 52 attacks; loop tolerance 1e-4 s), max |d dmg| 2.30e-7 HP
- Scripted Q/W/E/R rotation at L9 (AA, Q, AA, Q, E, W, R, Q-during-R): 17 hits incl. E/W melee passive and 10 R shots, max |dt| 5.24e-7 s, max |d dmg| 4.92e-8 HP; rejected Q during R matches

## Data status legend

`wr_wiki` Wild Rift wiki template · `damage_lab_preserved` existing Damage Lab value · `damage_lab_user_sourced` user-supplied WR evidence kept by the Damage Lab · `pc_reference_provisional` PC value used as a stand-in (AA windup, cast times, speeds) · `formula` no data input. Parity proves the C# engine reproduces the Damage Lab; it does not prove Wild Rift parity (see `docs/ingame-test-todo.md`).
