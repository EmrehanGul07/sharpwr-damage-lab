# Marksman implementation queue — 2026-10-01

**Current active follow-up:** [ingame-test-todo.md](ingame-test-todo.md). This queue records adapter integration and earlier research notes; V5.65 offline coverage is in [offline-engine-review-v565.md](offline-engine-review-v565.md).

All 23 champions are connected to Skill Lab. All adapters are provisional: integration completion does not imply verified Wild Rift parity.

Each champion has an executable event timeline, automatic ranks, item callbacks, resource handling and movement. Unknown timings and source conflicts remain explicit in runtime assumptions and the in-game TODO.

| Order | Champion | Catalogue | Fight engine | Missing mana slots |
|---|---|---|---|---|
| 1 | Samira | 5 slots | Provisional | — |
| 2 | Smolder | 5 slots | Provisional | — |
| 3 | Twitch | 5 slots | Provisional | — |
| 4 | Yunara | 5 slots | Provisional | — |
| 5 | Lucian | 5 slots | Provisional | — |
| 6 | Varus | 5 slots | Provisional | W |
| 7 | Ezreal | 5 slots | Provisional | — |
| 8 | Vayne | 5 slots | Provisional | — |
| 9 | Tristana | 5 slots | Provisional | — |
| 10 | Ashe | 5 slots | Provisional | E |
| 11 | Kalista | 5 slots | Provisional | W |
| 12 | Draven | 5 slots | Provisional | — |
| 13 | Caitlyn | 5 slots | Provisional | — |
| 14 | Jinx | 5 slots | Provisional | — |
| 15 | Kai'Sa | 5 slots | Provisional | — |
| 16 | Kog'Maw | 5 slots | Provisional | R |
| 17 | Miss Fortune | 5 slots | Provisional | — |
| 18 | Xayah | 5 slots | Provisional | — |
| 19 | Sivir | 5 slots | Provisional | E |
| 20 | Corki | 5 slots | Provisional | — |
| 21 | Senna | 5 slots | Provisional | — |
| 22 | Zeri | 5 slots | Provisional | — |
| 23 | Jhin | 5 slots | Provisional | — |

## Remaining work by champion

### 1. Samira

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: See docs/ingame-test-todo.md T01–T16. Mana and S Style are user-confirmed; they are not missing.
Unresolved mana: none.

### 2. Smolder

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: See docs/ingame-test-todo.md T17–T23. Mana is user-confirmed; it is not missing.
Unresolved mana: none.

### 3. Twitch

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Poison refresh/AP tick order, first spread tick, E spread radius and R item-proc falloff.
Unresolved mana: none.

### 4. Yunara

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: User mana Q30/W60/E40/R100 and empowered W160/320/480 are recorded. Base HP/mana/MS/core stats remain manual pending. Burn/linger/crit interaction timing needs WR validation.
Unresolved mana: none.

### 5. Lucian

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Lightslinger second-shot level progression; R bullet rounding/cap; W mark and passive proc order.
Unresolved mana: none.

### 6. Varus

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Q rank 2–4 bonus AD ratios and charge curve; W active missing-health scaling; blight application/detonation order.
Unresolved mana: W.

### 7. Ezreal

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: W detonation relative to Q on-hit/item effects; launch snapshot and projectile hit order.
Unresolved mana: none.

### 8. Vayne

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Q crit/on-hit eligibility; Silver Bolts proc classification and stack expiry; dash endpoint and wall detection.
Unresolved mana: none.

### 9. Tristana

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Level-one range offset; Explosive Charge crit/stack/proc order; jump endpoint and timed expiry explosion.
Unresolved mana: none.

### 10. Ashe

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Frost first-hit/crit calculation; Q flurry on-hit count; target distance stun scaling.
Unresolved mana: E.

### 11. Kalista

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Boot-dependent hop distance/speed; Rend proc order; allied Oathsworn damage excluded from solo simulation.
Unresolved mana: W.

### 12. Draven

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Q bonus critical eligibility; axe landing/catch timing and movement; R return/falloff/execute order.
Unresolved mana: none.

### 13. Caitlyn

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Headshot level/crit progression; trap arming and headshot/net/trap item-proc order; R crit calculation.
Unresolved mana: none.

### 14. Jinx

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Rocket flight damage curve; trap arming and overlap; minigun AS stack distribution; rocket mana consumption.
Unresolved mana: none.

### 15. Kai'Sa

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Plasma level progression and AP detonation coefficient; evolve conditions; E charge duration versus AS; W multi-stack ordering.
Unresolved mana: none.

### 16. Kog'Maw

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: R mana ramp and source conflict; missing-health interpolation and exact 40% boundary; W attack-proc order.
Unresolved mana: R.

### 17. Miss Fortune

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Love Tap crit modifier, level amp and expiry; Q bounce geometry; R shot/item eligibility.
Unresolved mana: none.

### 18. Xayah

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Feather lifetime, lateral recall collision detection and Q/R placement. WR per-feather 10 percentage-point falloff with 10% floor implemented; stationary aligned benchmark counts recalled feathers.
Unresolved mana: none.

### 19. Sivir

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Morale cap/expiry and R cooldown reduction order; Q cast scaling/return overlap; W bounce-only versus primary-target effects.
Unresolved mana: E.

### 20. Corki

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Passive true-damage base and proc order; W/E tick cadence/shred order; R charge reload ranks and critical-AA refund units.
Unresolved mana: none.

### 21. Senna

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Mist state and level passive damage; Q cast scaling; passive two-hit/target lockout/crit item-proc order.
Unresolved mana: none.

### 22. Zeri

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: Burst Fire level base; wall crit item interaction; R AS-cap exception/extension; E cooldown-refund crit handling.
Unresolved mana: none.

### 23. Jhin

- [x] P/Q/W/E/R observations and provenance catalogued.
- [x] Available WR template metadata researched; user damage/CD values preserved.
- [x] Timeline adapter, item/rune interaction, kit movement and rotation search.
- [ ] WR parity checks for unresolved details.
Remaining mechanics: R fourth-shot item interaction and channel cadence; in-game conversion cross-check. WR AD conversion, 2.5s reload and fourth-AA 11%-25% missing-HP level progression implemented.
Unresolved mana: none.

## Important source limits

Blank cost fields were not interpreted as zero. Explicit `none` was interpreted as zero with its source retained.
Kog’Maw R template has five ranks and a 40–400 conditional cost; the user WR record has three ranks and a different mana ramp. This conflict is retained and not applied.
PC base windup is authorized for Samira only. No PC timing fallback was added for other champions.
See docs/all-marksman-fight-engine.md for executable mechanics, conservative exclusions and outstanding parity checks.
