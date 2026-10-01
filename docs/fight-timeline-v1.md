# Samira fight timeline V5.47

AA/Q impacts replay in time order; R expands into ten shots with a user-supplied measured channel duration. Illegal attack intervals, cooldowns, unlearned abilities and missing Style reject events without awarding stacks.

Expected critical damage at 50% chance is (normal + critical) / 2. The UI provides a reference and optional replay override. Seeded mode rolls each impact reproducibly. Conqueror, Lethal Tempo, Yun Tal and alternating-action Style progress through accepted events, affecting subsequent hits. Item AA procs reuse the shared kernel; event mode links Spellblade and Fiendhunter to actual skill events.

This is a partial outgoing-damage impact replay, not a complete Wild Rift simulation. Mana, cast/projectile timings, Style expiry, melee passive, Collector execute, skill on-hit procs, movement-based Energized charging and precise R tick timings remain TODO. Expected HP-dependent paths are approximations. Unsupported offensive runes block replay. R spacing uses the supplied duration evenly; this assumption needs measurement.

Validation: 30 unit/UI regression tests passed, including 50% critical averaging, stack progression/expiry, rejected events, R prerequisites, seeded criticals, Yun Tal and Streamlit integration.
