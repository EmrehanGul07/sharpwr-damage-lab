# 03 · Combat event model

The simulation advances in fixed 30 Hz ticks. Within a tick, everything that happens is an
**event** with an exact microsecond timestamp, resolved in a total order. Resolved events are
appended to the `EventLog`, which is the audit trail, the replay format, the parity surface and
the desync detector.

## 1. Tick pipeline

```
Tick k  (window (T(k-1), T(k)],  T(k) = floor(k * 1e6 / 30) µs)
 1. Commands     apply validated player/bot commands stamped for tick k (Input phase)
 2. Movement     integrate walking for the full step (paths, collision) — dashes are events
 3. Drain queue  pop scheduled events with time <= T(k) in (time, phase, sequence) order;
                 handlers may schedule new events (same time allowed, later phase or sequence)
 4. Regen/decay  per-tick resource regen, stack decay, aura ticks
 5. Visibility   fog-of-war recompute (every 2nd tick, see 07-performance)
 6. Snapshot     state hash; snapshot ring buffer (networking/rollback)
```

## 2. Event kinds and payloads

| Kind | Produced by | Payload | Consumers |
|---|---|---|---|
| `AttackStart` | attack controller | source, target, attack id | windup, animation |
| `AttackImpact` | scheduler (start + windup + travel) | projectile/melee hit | damage pipeline |
| `AbilityCast` | ability system after validation & cost | slot, rank, aim | ability hooks, CD start |
| `AbilityImpact` | delivery (projectile, area, dash end, channel tick) | hit list | damage, status |
| `DamageApplied` | damage pipeline | type, raw, mitigated, flags, crit | HP, on-damage triggers, UI |
| `ShieldAbsorbed` / `Heal` | shields / healing | amount | HP, UI |
| `StatusApplied` / `StatusExpired` | status system | status id, stacks, duration | movement/cast gates |
| `Death` / `Respawn` | death check / respawn timer | killer, assists | scoring, AI |
| `Rejected` | validation | reason (cooldown, mana, range, lock, unsupported) | UI feedback, tests |

## 3. Deterministic ordering contract

Ordering key: **(time µs, phase, sequence)**, never ties.

| Phase | Value | Contents |
|---|---|---|
| Input | 0 | commands for this tick |
| CastStart | 10 | casts begin; cost paid; cooldown starts; attack timer starts |
| Movement | 20 | dash/blink resolution, displacement |
| Impact | 30 | hits computed against the post-movement state |
| Damage | 40 | shields → HP; on-hit and on-damage triggers enqueue (later sequence) |
| Death | 50 | units at HP ≤ 0 die **after** all same-µs damage (simultaneous trades) |
| StatusExpiry | 60 | buffs/CC end after everything else at that µs |

`sequence` is a global insertion counter, so two impacts at the same µs resolve in scheduling
order. Entity iteration (movement, regen) is by ascending entity id.

## 4. Damage pipeline

```
DamageRequest(source, target, type, base components, flags)
  1. scale       base + ratios × stats (CombatMath.ScaledAbility)
  2. crit        rolled per hit from source crit stream (or forced in tests); crit_effectiveness
  3. amplify     source damage modifiers (runes, items), ordered by modifier priority then id
  4. mitigate    resistances after percent then flat pen (CombatMath.Mitigate); true ignores
  5. reduce      target damage reduction (percent, then flat)
  6. shields     typed shields first (magic/physical), then generic, oldest first
  7. apply       HP -= remainder; record DamageApplied (raw, mitigated, absorbed, flags)
  8. triggers    on-hit (only if flags.TriggerOnHit), lifesteal/omnivamp, on-damage, kill credit
```

Flags mirror the Damage Lab classification (`BasicAttack`, `ActiveSpell`, `Proc`,
`TriggerOnHitEvents`, `ApplyLifesteal`, …) so item rules port without reinterpretation.

## 5. Resources, cooldowns, gates

* A command is validated in this order: alive → not disabled for that action (stun, silence,
  disarm, cast lock, channel) → cooldown ready → resource affordable → range/target legal →
  content supported. The first failure produces one `Rejected` event and **no state change**
  (Damage Lab rule: "invalid casts spend neither mana nor cooldown").
* Cooldowns store the ready time in µs; ability haste converts with `CD × 100/(100+AH)`.
* Attack timer: `period = 1/AS` rounded to µs at attack start; windup =
  `base_windup / (1 + bonusAS × windup_modifier)` (Damage Lab formula, WR applicability
  still open).

## 6. Example: Samira AA at level 1 vs dummy (fixture `level1_ranged_525`)

| µs | Phase | Event |
|---|---|---|
| 0 | CastStart | `AttackStart` (period 1,519,757 µs, windup 227,964 µs) |
| 415,464 | Impact | `AttackImpact` (windup + 525/2800 s travel = 187,500 µs) |
| 415,464 | Damage | `DamageApplied` 60 physical (armor 0) |
| 1,519,757 | CastStart | next `AttackStart` |

Python reference impact times: 0.415464, 1.935220, 3.454977, 4.974734 s. The fixed-point
model reproduces them within 1.1 µs (`tools/parity/test_fixed_point_model.py`).
