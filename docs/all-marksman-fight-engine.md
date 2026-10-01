# All marksman fight adapters — V5.59

All 23 database champions are exposed in Skill Lab. Samira and Smolder retain their existing adapters; the remaining 21 now dispatch to an event-driven kit adapter. Integration is complete; exact Wild Rift parity is not verified.

## Implemented shared behavior

- Automatic skill ranks at levels 1–15, build attack speed / haste / crit / penetration and expected critical damage.
- Mana spending and regeneration, cooldown timers, buff and stack expiry, delayed impacts and channels.
- Shared item callbacks for basic attacks; eligible skill on-hit callbacks for Ezreal Q, Senna Q and Miss Fortune Q.
- Passive damage, reloads, ammo, multi-hit channels, resource prerequisites and ability-specific basic-attack locks.
- Ranged max-AA-range movement with approaches for shorter skills and return to range. Samira keeps her existing melee approach.
- Six basic-skill permutations with E enabled/disabled (12 candidates); Jinx additionally compares two weapons (24). The best tested result is selected; this is not a mathematical global optimum.
- Target never deals damage. Defensive-only/allied abilities cannot increase solo target DPS and are omitted.

## Limits that remain explicit

Unknown casts and projectiles use instant impact; unknown ranges use the supplied AA envelope. These are reported as assumptions, not researched values. General AA windups remain unknown except the authorized Samira PC base fallback and sourced Senna WR level-one base. Expected damage is deterministic; threshold-dependent state follows expected HP rather than enumerating random fights. Movement is integrated at 50 ms steps while scheduled impacts retain their event time. Only the existing supported offensive rune set is available.

Xayah recall currently includes the known first-feather damage only; uncertain subsequent-feather falloff/path is excluded. Missing Jhin AS/crit-to-AD coefficients are not invented. Senna uses supplied initial mist; further mist generation is pending. Corki package pickup, wall collisions, dash endpoints and exact return paths remain unverified. These limitations can change DPS materially.

User WR values take priority over conflicting current wiki values, including Twitch Q/P, Xayah E, Corki recharge, Senna mist crit and Kai’Sa passive. Kog’Maw R mana ramp and Varus W blank mana cost remain provisional. Yunara lacks verified core mana/MS/range statistics; a result without supplied maximum mana cannot verify resource affordability.

## Remaining runtime assumptions by champion

### Twitch

- Twitch E projectile timing unresolved: instant impact after cast
- Twitch E range unresolved: conservative AA-range targeting
- Twitch Q projectile timing unresolved: instant impact after cast
- Twitch Q range unresolved: conservative AA-range targeting
- Twitch R projectile timing unresolved: instant impact after cast
- Twitch R range unresolved: conservative AA-range targeting
- Twitch W cast time unresolved: instant cast mode
- Twitch W projectile timing unresolved: instant impact after cast
- Twitch W range unresolved: conservative AA-range targeting
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Yunara

- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback
- Yunara Q cast time unresolved: instant cast mode
- Yunara Q projectile timing unresolved: instant impact after cast
- Yunara R cast time unresolved: instant cast mode
- Yunara R projectile timing unresolved: instant impact after cast
- Yunara W cast time unresolved: instant cast mode
- Yunara W linger contact/total ticks unresolved: initial hit only
- Yunara W projectile timing unresolved: instant impact after cast
- Yunara core mana/MS/range await manual WR data; resource and spatial timing remain unresolved

### Lucian

- Lucian Q cast time unresolved: instant cast mode
- Lucian Q projectile timing unresolved: instant impact after cast
- Lucian R bullet rounding/cap uses floor of tooltip candidate
- Lucian R projectile timing unresolved: instant impact after cast
- Lucian R range unresolved: conservative AA-range targeting
- Lucian W range unresolved: conservative AA-range targeting
- Lucian second-shot level progression unresolved: confirmed 40% baseline
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Varus

- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback
- Varus E projectile timing unresolved: instant impact after cast
- Varus E range unresolved: conservative AA-range targeting
- Varus Q projectile timing unresolved: instant impact after cast
- Varus Q range unresolved: conservative AA-range targeting
- Varus Q rank 2–4 ratios sourced from WR wiki, retaining user bonus-AD basis; wiki total-AD wording conflicts
- Varus R projectile timing unresolved: instant impact after cast
- Varus R range unresolved: conservative AA-range targeting
- Varus W cost absent in WR wiki: provisional free activation; verify in-game
- Varus W projectile timing unresolved: instant impact after cast
- Varus W range unresolved: conservative AA-range targeting

### Ezreal

- Ezreal R projectile timing unresolved: instant impact after cast
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Vayne

- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback
- Vayne E projectile timing unresolved: instant impact after cast
- Vayne E range unresolved: conservative AA-range targeting
- Vayne Q dash speed/end-point unresolved: instant lateral tumble
- Vayne Q projectile timing unresolved: instant impact after cast
- Vayne Q range unresolved: conservative AA-range targeting
- Vayne R projectile timing unresolved: instant impact after cast
- Vayne R range unresolved: conservative AA-range targeting
- Vayne W projectile timing unresolved: instant impact after cast
- Vayne W range unresolved: conservative AA-range targeting

### Tristana

- Tristana E cast time unresolved: instant cast mode
- Tristana E projectile timing unresolved: instant impact after cast
- Tristana E range unresolved: conservative AA-range targeting
- Tristana Q projectile timing unresolved: instant impact after cast
- Tristana Q range unresolved: conservative AA-range targeting
- Tristana R projectile timing unresolved: instant impact after cast
- Tristana R range unresolved: conservative AA-range targeting
- Tristana W projectile timing unresolved: instant impact after cast
- Tristana W range unresolved: conservative AA-range targeting
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Ashe

- Ashe Q projectile timing unresolved: instant impact after cast
- Ashe Q range unresolved: conservative AA-range targeting
- Ashe R cast time unresolved: instant cast mode
- Ashe R projectile timing unresolved: instant impact after cast
- Ashe R range unresolved: conservative AA-range targeting
- Ashe W cast time unresolved: instant cast mode
- Ashe first-hit/Frost base modifier and Q flurry item-on-hit count need WR validation
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Kalista

- Kalista E projectile timing unresolved: instant impact after cast
- Kalista E range unresolved: conservative AA-range targeting
- Kalista Q projectile timing unresolved: instant impact after cast
- Kalista Q range unresolved: conservative AA-range targeting
- Kalista boot hop speed/distance unresolved: max-range walking kite
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Draven

- Draven Q projectile timing unresolved: instant impact after cast
- Draven Q range unresolved: conservative AA-range targeting
- Draven W projectile timing unresolved: instant impact after cast
- Draven W range unresolved: conservative AA-range targeting
- Draven axe crit scope/catch timing provisional; explicit catch event after 1s
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Caitlyn

- Caitlyn E range unresolved: conservative AA-range targeting
- Caitlyn Q range unresolved: conservative AA-range targeting
- Caitlyn R crit modifier unresolved: confirmed non-crit component only
- Caitlyn W projectile timing unresolved: instant impact after cast
- Caitlyn headshot level/crit progression unresolved: confirmed 60% baseline
- Caitlyn trap ammo/recharge pool provisional: one charge per recharge
- Caitlyn trap arming provisional 1s
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Jinx

- Jinx E projectile timing unresolved: instant impact after cast
- Jinx R distance/flight curve unresolved: minimum flight-damage component
- Jinx R projectile timing unresolved: instant impact after cast
- Jinx W range unresolved: conservative AA-range targeting
- Jinx trap arming provisional 1s
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Kai'Sa

- Kai'Sa E cast time unresolved: instant cast mode
- Kai'Sa E projectile timing unresolved: instant impact after cast
- Kai'Sa E range unresolved: conservative AA-range targeting
- Kai'Sa Q projectile timing unresolved: instant impact after cast
- Kai'Sa W cast time unresolved: instant cast mode
- Kai’Sa E AS-dependent charge duration unresolved: provisional 1s charge
- Kai’Sa passive level progression unresolved: level-one known base only
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Kog'Maw

- Kog'Maw E range unresolved: conservative AA-range targeting
- Kog'Maw Q cast time unresolved: instant cast mode
- Kog'Maw Q range unresolved: conservative AA-range targeting
- Kog'Maw R projectile timing unresolved: instant impact after cast
- Kog'Maw R range unresolved: conservative AA-range targeting
- Kog'Maw W projectile timing unresolved: instant impact after cast
- Kog'Maw W range unresolved: conservative AA-range targeting
- Kog’Maw R initial mana/ramp source conflict: provisional 40 + 50 per cast, capped at user 500
- Kog’Maw R missing-health interpolation unresolved: non-amplified component above 40%
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Miss Fortune

- Miss Fortune E projectile timing unresolved: instant impact after cast
- Miss Fortune Love Tap crit/level modifier unresolved: confirmed 60% base component only
- Miss Fortune Q cast time unresolved: instant cast mode
- Miss Fortune Q range unresolved: conservative AA-range targeting
- Miss Fortune W projectile timing unresolved: instant impact after cast
- Miss Fortune W range unresolved: conservative AA-range targeting
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Xayah

- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback
- Xayah E projectile timing unresolved: instant impact after cast
- Xayah E range unresolved: conservative AA-range targeting
- Xayah Q projectile timing unresolved: instant impact after cast
- Xayah Q range unresolved: conservative AA-range targeting
- Xayah R 1.5s untargetable lock provisional WR timing
- Xayah R projectile timing unresolved: instant impact after cast
- Xayah R range unresolved: conservative AA-range targeting
- Xayah W projectile timing unresolved: instant impact after cast
- Xayah W range unresolved: conservative AA-range targeting
- Xayah feather falloff unresolved: only first confirmed feather contributes damage; full count retained in trace

### Sivir

- Sivir Morale cap/expiry unresolved
- Sivir Q cast time unresolved: instant cast mode
- Sivir Q projectile timing unresolved: instant impact after cast
- Sivir Q return travel unresolved: provisional 0.25s return delay
- Sivir R projectile timing unresolved: instant impact after cast
- Sivir R range unresolved: conservative AA-range targeting
- Sivir W projectile timing unresolved: instant impact after cast
- Sivir W range unresolved: conservative AA-range targeting
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Corki

- Corki E projectile timing unresolved: instant impact after cast
- Corki E/W tick cadence uses provisional 0.25s integration
- Corki R range unresolved: conservative AA-range targeting
- Corki W projectile timing unresolved: instant impact after cast
- Corki passive Spellblade/crit interaction order needs validation
- Corki recharge retains user 16s baseline; wiki 20s conflicts; AA refund candidate 2 + 3×crit
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Senna

- Senna Q level modifier unresolved: 80% of sourced WR base AA windup
- Senna Q projectile timing unresolved: instant impact after cast
- Senna Q range unresolved: conservative AA-range targeting
- Senna WR base windup 0.5s with 60% AS scaling; level-dependent modifier unresolved
- Senna mist generation from champion siphon unresolved: initial supplied mist retained
- Senna passive bonus AA and two-hit level progression unresolved: confirmed base extra 10 physical
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

### Zeri

- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback
- Zeri Burst Fire flat level progression unresolved: confirmed 20 baseline
- Zeri E range unresolved: conservative AA-range targeting
- Zeri Q cast time unresolved: instant cast mode
- Zeri Q projectile timing unresolved: instant impact after cast
- Zeri Q range unresolved: conservative AA-range targeting
- Zeri R projectile timing unresolved: instant impact after cast
- Zeri W cast time unresolved: instant cast mode
- Zeri W range unresolved: conservative AA-range targeting

### Jhin

- Jhin E projectile timing unresolved: instant impact after cast
- Jhin E range unresolved: conservative AA-range targeting
- Jhin Q projectile timing unresolved: instant impact after cast
- Jhin Q range unresolved: conservative AA-range targeting
- Jhin R cast time unresolved: instant cast mode
- Jhin R projectile timing unresolved: instant impact after cast
- Jhin R range unresolved: conservative AA-range targeting
- Jhin W projectile timing unresolved: instant impact after cast
- Jhin W range unresolved: conservative AA-range targeting
- Jhin bonus-AS/crit-to-AD conversion coefficients missing: supplied AD used without invented conversion
- Jhin fourth-AA missing-health level progression unresolved: confirmed 11% baseline
- Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback

## Validation

Automated coverage checks all 23 champions in the Streamlit UI at levels 1 and 15, full builds against Tank Ornn, valid HP ledgers and resource bounds, deterministic replay, expected 50% crit, reload/channel blocks, poison ticks, bomb expiration, Vayne third hit, Lucian double-shot, Yunara free ultimate skills, Kai’Sa evolution, Ezreal mark consumption and Zeri AS conversion. Validation passed: full suite 117/117 (92.321 s), plus 2/2 new item integration tests. The item matrix runs 21 adapters across crit, mana/on-hit and stacking-AS builds (63 scenarios), plus eligible skill-on-hit regressions.

## Source provenance

Existing user screenshot/practice evidence remains in data/marksman-ability-evidence.json. Imported WR metadata remains in data/marksman-wr-ability-metadata.json. Supplemental timing/state sources use wiki.leagueoflegends.com WR templates only; no additional PC timing fallback was introduced.

- Jhin P: https://wiki.leagueoflegends.com/en-us/WR:Jhin (WR data template; fetched 2026-10-01).
- Jhin R: https://wiki.leagueoflegends.com/en-us/WR:Jhin (WR data template; fetched 2026-10-01).
- Varus Q: https://wiki.leagueoflegends.com/en-us/WR:Varus (WR data template; fetched 2026-10-01).
- Varus W: https://wiki.leagueoflegends.com/en-us/WR:Varus (WR data template; fetched 2026-10-01).
- Kai'Sa P: https://wiki.leagueoflegends.com/en-us/WR:Kai'Sa (WR data template; fetched 2026-10-01).
- Kai'Sa E: https://wiki.leagueoflegends.com/en-us/WR:Kai'Sa (WR data template; fetched 2026-10-01).
- Caitlyn P: https://wiki.leagueoflegends.com/en-us/WR:Caitlyn (WR data template; fetched 2026-10-01).
- Zeri P: https://wiki.leagueoflegends.com/en-us/WR:Zeri (WR data template; fetched 2026-10-01).
- Zeri R: https://wiki.leagueoflegends.com/en-us/WR:Zeri (WR data template; fetched 2026-10-01).
- Zeri E: https://wiki.leagueoflegends.com/en-us/WR:Zeri (WR data template; fetched 2026-10-01).
- Xayah P: https://wiki.leagueoflegends.com/en-us/WR:Xayah (WR data template; fetched 2026-10-01).
- Xayah E: https://wiki.leagueoflegends.com/en-us/WR:Xayah (WR data template; fetched 2026-10-01).
- Ashe P: https://wiki.leagueoflegends.com/en-us/WR:Ashe (WR data template; fetched 2026-10-01).
- Corki P: https://wiki.leagueoflegends.com/en-us/WR:Corki (WR data template; fetched 2026-10-01).
- Corki R: https://wiki.leagueoflegends.com/en-us/WR:Corki (WR data template; fetched 2026-10-01).
- Senna P: https://wiki.leagueoflegends.com/en-us/WR:Senna (WR data template; fetched 2026-10-01).
- Senna Q: https://wiki.leagueoflegends.com/en-us/WR:Senna (WR data template; fetched 2026-10-01).
- Kalista P: https://wiki.leagueoflegends.com/en-us/WR:Kalista (WR data template; fetched 2026-10-01).
- Miss Fortune P: https://wiki.leagueoflegends.com/en-us/WR:Miss_Fortune (WR data template; fetched 2026-10-01).
- Twitch Q: https://wiki.leagueoflegends.com/en-us/WR:Twitch (WR data template; fetched 2026-10-01).
- Twitch P: https://wiki.leagueoflegends.com/en-us/WR:Twitch (WR data template; fetched 2026-10-01).
- Jinx Q: https://wiki.leagueoflegends.com/en-us/WR:Jinx (WR data template; fetched 2026-10-01).
- Jinx R: https://wiki.leagueoflegends.com/en-us/WR:Jinx (WR data template; fetched 2026-10-01).
