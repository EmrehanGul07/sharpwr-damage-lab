# Marksman fight adapters — V5.87.1

All 23 champions are connected to Skill Lab and have executable fight adapters. Integration is complete; Wild Rift parity is unresolved. This file describes the current engine. Older dated reports remain historical evidence.

Shared behavior: automatic ranks, expected crit, mana/cooldowns, cast/channel/AA locks, impact queues, item callbacks and movement. Authorized PC timing proxies are used with recorded WR stats. User-confirmed coefficients and exceptions take precedence over older imported metadata.

The target is stationary and does not attack back. Incoming damage, own death, lifesteal survival, allies and turret simulation are excluded. Unsupported offensive rune loadouts block replay. First Strike covers an initially ready engagement only; adaptive rune procs keep the existing ADC physical model.

## Current validation

The no-rune integrity matrix contains 3312 cases and 6912 fights with 0 failures. A separate baseline comparison replays all 1,242 saved finalists. These checks establish model consistency, not gameplay parity.

## Runtime assumptions by champion

Generated from the current integrity matrix and saved-finalist replays. The full structured record is `data/marksman-runtime-assumptions.json`. Additional evidence gaps live in [ingame-test-todo.md](ingame-test-todo.md).

### Twitch

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Twitch W range unresolved: conservative AA-range targeting

### Yunara

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Yunara Phantom on-hit: WR damage tags unresolved
- Yunara W hit: WR damage tags unresolved
- Yunara W: WR damage tags unresolved
- Yunara uses rounded WR stats at all 15 levels; HP regeneration units and AD/AS observation reconciliation remain pending

### Lucian

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Lucian Q cast time unresolved: instant cast mode
- Lucian R bullet rounding/cap uses floor of tooltip candidate
- Lucian R range unresolved: conservative AA-range targeting
- Lucian second-shot level progression unresolved: confirmed 40% baseline
- Movement skill path uses provisional distance/end-point proxy; Ezreal E calibrated to observed 16 Energized charges

### Varus

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Varus E range unresolved: conservative AA-range targeting
- Varus Phantom on-hit: WR damage tags unresolved
- Varus Q range unresolved: conservative AA-range targeting
- Varus Q rank 2–4 ratios sourced from WR wiki, retaining user bonus-AD basis; wiki total-AD wording conflicts
- Varus R range unresolved: conservative AA-range targeting
- Varus W cost absent in WR wiki: provisional free activation; verify in-game

### Ezreal

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Ezreal Q Rageblade attack-speed stack gain is not independently verified
- Movement skill path uses provisional distance/end-point proxy; Ezreal E calibrated to observed 16 Energized charges

### Vayne

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Movement skill path uses provisional distance/end-point proxy; Ezreal E calibrated to observed 16 Energized charges
- Vayne E range unresolved: conservative AA-range targeting
- Vayne Phantom on-hit: WR damage tags unresolved
- Vayne Q dash speed/end-point unresolved: instant lateral tumble

### Tristana

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Movement skill path uses provisional distance/end-point proxy; Ezreal E calibrated to observed 16 Energized charges
- Tristana E range unresolved: conservative AA-range targeting
- Tristana R range unresolved: conservative AA-range targeting
- Tristana R: WR damage tags unresolved
- Tristana W range unresolved: conservative AA-range targeting

### Ashe

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Ashe Q subsequent arrows: WR says default/proc; Hexoptics only first arrow, exact component split pending WR test
- Ashe first-hit/Frost base modifier and Q flurry item-on-hit count need WR validation

### Kalista

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Kalista E projectile timing unresolved: instant impact after cast
- Kalista E range unresolved: conservative AA-range targeting
- Kalista Q range unresolved: conservative AA-range targeting
- Kalista boot hop speed/distance unresolved: max-range walking kite

### Draven

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Draven axe crit scope/catch timing provisional; explicit catch event after 1s

### Caitlyn

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Caitlyn R crit modifier unresolved: confirmed non-crit component only
- Caitlyn W projectile timing unresolved: instant impact after cast
- Caitlyn headshot level/crit progression unresolved: confirmed 60% baseline
- Caitlyn trap ammo/recharge pool provisional: one charge per recharge
- Caitlyn trap arming provisional 1s
- Movement skill path uses provisional distance/end-point proxy; Ezreal E calibrated to observed 16 Energized charges

### Jinx

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Jinx E projectile timing unresolved: instant impact after cast
- Jinx R distance/flight curve unresolved: minimum flight-damage component
- Jinx trap arming provisional 1s

### Kai'Sa

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Kai'Sa Phantom on-hit: WR damage tags unresolved
- Kai’Sa E charge uses user-authorized PC AS-dependent timing
- Kai’Sa passive level progression unresolved: level-one known base only

### Kog'Maw

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Kog'Maw Phantom on-hit: WR damage tags unresolved
- Kog'Maw R projectile timing unresolved: instant impact after cast
- Kog'Maw R range unresolved: conservative AA-range targeting
- Kog’Maw R initial mana/ramp source conflict: provisional 40 + 50 per cast, capped at user 500
- Kog’Maw R missing-health interpolation unresolved: non-amplified component above 40%

### Miss Fortune

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Miss Fortune E projectile timing unresolved: instant impact after cast
- Miss Fortune Love Tap crit/level modifier unresolved: confirmed 60% base component only
- Skill on-hit item stack eligibility/Phantom Hit interactions remain provisional

### Xayah

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Xayah Q projectile timing unresolved: instant impact after cast
- Xayah R 1.5s untargetable lock provisional WR timing
- Xayah benchmark uses aligned radial movement against a stationary target; lateral feather collision geometry unverified

### Sivir

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Sivir Morale cap/expiry unresolved

### Corki

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Corki E/W tick cadence uses provisional 0.25s integration
- Corki R range unresolved: conservative AA-range targeting
- Corki passive Spellblade/crit interaction order needs validation
- Corki recharge retains user 16s baseline; wiki 20s conflicts; AA refund candidate 2 + 3×crit
- Movement skill path uses provisional distance/end-point proxy; Ezreal E calibrated to observed 16 Energized charges

### Senna

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Senna Q range unresolved: conservative AA-range targeting
- Senna WR base windup 0.5s with 60% AS scaling; level-dependent modifier unresolved
- Senna mist generation from champion siphon unresolved: initial supplied mist retained
- Senna passive bonus AA and two-hit level progression unresolved: confirmed base extra 10 physical
- Skill on-hit item stack eligibility/Phantom Hit interactions remain provisional

### Zeri

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Movement skill path uses provisional distance/end-point proxy; Ezreal E calibrated to observed 16 Energized charges
- Zeri Burst Fire flat level progression unresolved: confirmed 20 baseline
- Zeri E range unresolved: conservative AA-range targeting
- Zeri Q cast time unresolved: instant cast mode
- Zeri W range unresolved: conservative AA-range targeting

### Jhin

- AA windup/projectile use user-authorized PC timing proxies with WR AS scaling
- Jhin E range unresolved: conservative AA-range targeting
- Jhin Q range unresolved: conservative AA-range targeting
- Jhin R hit: WR damage tags unresolved
- Jhin R range unresolved: conservative AA-range targeting
- Jhin R: WR damage tags unresolved
- Jhin W projectile timing unresolved: instant impact after cast
- Jhin W range unresolved: conservative AA-range targeting
- Jhin W: WR damage tags unresolved

### Samira


### Smolder


## Provenance

Preserved user observations: `data/marksman-ability-evidence.json`, later user-test JSON records and the active evidence TODO. WR metadata: `data/marksman-wr-ability-metadata.json` and `data/marksman-ability-catalogue.json`. Authorized timing proxies: `data/pc-combat-timing.json`. Unknown WR classifications remain unknown in `data/damage-classification.json`.
