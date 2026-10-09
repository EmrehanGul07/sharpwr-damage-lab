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

- [ ] Improve walking/cast transitions and direction alignment for the two pilot champions.
- [ ] Review distinct AA/Q/W/E/R effects, impact readability and range/blink/dash indicators.
- [ ] Improve minion models and motion; inspect lane/tower scale and texture consistency.
- [ ] Tune bot decisions without changing difficulty-dependent stats.
- [ ] Run mobile viewport, sustained-duel and performance checks, then publish a validated update.

Completion means reviewed behavior and passing relevant checks, rather than an unsupported percentage of Wild Rift parity.
