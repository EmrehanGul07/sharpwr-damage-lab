# 05 · Champion ability framework

The Damage Lab encodes each champion as one long function. The game splits a champion into
**data** (what most abilities are) and **small, named hooks** (what makes a kit unique), so
most champions need no code and every piece of code is individually testable.

## Building blocks

```
ChampionDefinition (JSON)
  stats{…}  basic_attack{range, windup, projectile|melee}  passive{…}  abilities{Q,W,E,R}

AbilityDefinition
  targeting   : Self | Unit(range, filter) | Direction(range) | Point(range) | Vector
  cast        : cast_time, lockouts{move, attack, cast}, queue_window, interruptible_by
  cost        : mana | energy | none, plus requirements (e.g. "style_grade >= S")
  cooldown    : by_rank, haste_applies (bool, may be unresolved), charges{max, recharge}
  delivery    : Instant | Projectile{speed, width, range, pierce, collides_with}
              | Area{shape: circle|cone|rect, delay} | Dash{speed, distance, path_hits}
              | Channel{duration, tick_offsets[]} | Composite[...]
  effects[]   : Damage{formula, type, flags, hits} | Heal | Shield | ApplyStatus{id, duration}
              | Displace | ResetAttack | ModifyCooldown | GrantStacks{resource, amount}
  hooks[]     : named script hooks for anything not expressible above
```

`formula` uses the same small expression set the Damage Lab uses:
`base_by_rank + total_ad × r1 + bonus_ad × r2 + ap × r3 + missing_hp% …`, evaluated in Fix64.

## Hooks (script escape hatch)

Hooks are C# classes in `Runtime/Champions/<Id>/` implementing narrow interfaces, registered by
string id from content:

| Interface | Called at | Example |
|---|---|---|
| `IOnHitHook` | Damage phase, after a hit lands | Samira Style stack on a *different* action |
| `ICastGateHook` | command validation | Samira R requires Style S |
| `IDamageModifierHook` | pipeline step 3 | passive melee bonus (when verified) |
| `IStatusHook` | status apply/expire | Style decay after 6 s |
| `IAttackModifierHook` | attack start | blade AA within 200 edge range is melee |

Hooks receive a read-only view + an `EffectSink` to schedule events; they cannot mutate state
directly, which keeps ordering inside the pipeline and makes them unit-testable without a world.

## Unsupported mechanics are first-class

Each ability and hook declares the content fields it requires. At load:

* all required fields resolved → ability enabled;
* any required field `unresolved` → ability **disabled** with `UnsupportedReason`, shown in
  the HUD tooltip and the practice "What this simulates" panel, logged as `Rejected` if cast.

This reproduces the Damage Lab policy ("Unsupported offensive loadouts block replay instead of
silently dropping their effects") in the game.

## Samira as the framework's first stress test

| Piece | Expressed as | Data status |
|---|---|---|
| AA (ranged 525 / blade ≤200) | basic_attack + `IAttackModifierHook` | range wr_wiki; windup PC-provisional; blade range PC-provisional |
| Style (E→S, 6 s) | resource `style` + `IOnHitHook` + `IStatusHook` | duration/stacking: PC + user rules; refresh details **open** |
| Passive melee bonus | `IDamageModifierHook` | **unsupported** (provisional interpolation) |
| Q Flair | Direction → Projectile(2600, w120) / melee cone | damage/CD user-sourced; geometry wr_wiki; cone **unsupported v1** |
| W Blade Whirl | Self → Channel(0.75 s, hits at 0, 0.75) + lockouts | damage user-sourced; projectile destruction **unsupported v1** |
| E Wild Rush | Unit → Dash(1600, 650) + Damage | user-sourced; E-Q explosives **unsupported v1** |
| R Inferno Trigger | Self → Channel(2.277 s, 10 ticks, even offsets) + `ICastGateHook` | damage user-sourced; offsets PC + even-spacing assumption, labelled |

For an **original** first champion the same framework is used with `original_design` values.

## Champion implementation procedure (agent: champion-implementer)

1. data-verification produces/updates the content file and its parity fixtures.
2. Write failing tests: per-ability damage vs fixtures, gates (cooldown, cost, lockouts),
   unsupported paths.
3. Express in data; add hooks only for what data cannot express.
4. Scenario test: scripted rotation against a dummy vs Python event log (where a reference exists).
5. Update the champion's "supported / unsupported" table in content; QA signs acceptance.
