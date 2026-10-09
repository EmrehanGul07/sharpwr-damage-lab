# ADC simulator: two-day implementation plan

Scope: bring Ezreal–Jinx lane practice to a consistent standard before expanding the ADC roster. Build Lab stays outside this work. Time blocks are estimates, not a promise of continuous background execution.

## Day 1 — controls and combat

- [x] Inspect pointer ownership, manual movement and selected-target routing. Preserve the rule that human attacks and aiming never command movement.
- [x] Fix Jinx traps: only the opposing champion can trigger them, independently of the selected minion or tower.
- [x] Fix Ezreal E: acquire a living enemy within bolt radius, prioritize an active W mark, otherwise choose the nearest enemy. Freeze acquired identity so changing selection cannot redirect damage.
- [x] Add regression cases for champion-only traps, marked-target priority, selection changes and dead bolt victims.
- [x] Audit AA windup, moving-target projectile visuals and locomotion/cast transitions; fix actual victim impact positions and stopped-session animation locks.
- [x] Complete Ezreal/Jinx kit matrix covering mana, cooldowns, marks, weapons, crowd control and impact-time damage. See `ezreal-jinx-day1-audit.md` for explicit limits.
- [x] Verify simultaneous touch controls, skill cancellation, blur cleanup and late releases in browser at 390x844, 844x390 and 1280x800. Verify death/finish cleanup with engine regressions.

The E priority and champion-only trap rules are documented in `data/ability-descriptions.json`. Existing numerical configuration remains unchanged. Timing and radius values still need a source-confidence audit; they must not be described as exact Wild Rift values without evidence.

## Day 2 — presentation and practice quality

- [x] Improve walking/cast transitions and direction alignment for the two pilot champions: shortest-arc walk turns, immediate cast facing, existing skeletal blends verified.
- [x] Review distinct AA/Q/W/E/R effects, impact readability and range/blink/dash indicators: pilot projectile silhouettes, Ezreal blink bolt and actual opponent impact positions improved.
- [x] Improve minion models and motion; inspect lane/tower scale and texture consistency: articulated melee/caster actors, distance-based gait, attack telemetry, shared resources and stone/rock detail.
- [x] Tune bot decisions without changing difficulty-dependent stats: visible tower-aggro retreat, safer firing-angle sidesteps and expiring observation records.
- [x] Run mobile viewport, sustained-duel and performance checks. Eight three-minute pilot/difficulty runs and mobile tests pass; release 0.8.18 includes browser resource ceilings and CI publication validation.

Implementation details and remaining simulator limitations: `adc-simulator-day2-results.md`. These completed milestones do not imply full Wild Rift parity.

Completion means reviewed behavior and passing relevant checks, rather than an unsupported percentage of Wild Rift parity.
