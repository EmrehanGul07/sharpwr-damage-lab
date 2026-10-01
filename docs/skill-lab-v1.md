# Skill Lab v1 — Samira Q and R

Build Lab now offers standalone skill damage estimates for Samira. Q has ranks 0–4 and R 0–3; rank 0 means unlearned. W/E are visibly pending. R requires six Style stacks (S) and accepts 1–10 landed shots per target.

Damage rows separate normal, expected and critical outcomes. Critical is shown only when the build has nonzero crit chance. Physical, magic and true components appear before and after resistance; Q/R are physical. Target basic-attack reduction is excluded from these skill estimates.

Formulas:

- Q: `(15/20/25/30 + 1.25 × total AD) × (1 + 0.5 × (crit damage − 1) × crit probability)`.
- R per shot: `(20/40/60 + 0.5 × total AD) × (1 + (crit damage − 1) × crit probability)`; multiply by landed shots per target.
- Crit probability is 0 for normal, 1 for critical, and build crit chance for expected damage.

Sources: uploaded game screenshots D001–D002 and D007–D008; user practice Q normal/crit 76/114 and 123/203, R crit ratio 69/158, and the 112-per-shot tooltip at 184 AD. These observations support crit coefficients; absolute rune-affected indicator values are not asserted to equal the isolated model.

Stats use the current champion level, equipped items, boots, selected Yun Tal permanent crit and mana-derived Awe AD. Rune stats/damage, item damage amplification/procs, Samira melee passive, mana costs and channel timing remain outside this first estimate. No combo or ability DPS is inferred. Q/R base cooldowns and item Ability Haste cooldowns are shown; unknown mana remains Unknown.

Validation: unit tests for all ranks, unlearned skills, expected crit weighting, Q/R crit ratios, 1–10 R shots, armor penetration and invalid inputs. UI tests cover support gating, disabled pending abilities, S-style requirement, rank 0, partial R and state retention across item removal. Existing shared-AA tests remain required.
