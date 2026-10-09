"""Practice Tool numbers: one champion, no items or runes, hitting a training dummy.

The web Practice Tool and the phone app read this (marksman_art.practice_catalogue,
app-data/practice.json). Every number comes from the engine instead of being typed again here:

* level stats: AD and attack speed from the AA engine, movement speed from the champion database,
  attack range and cooldowns, cast times, damaging reach and projectile travel from the kit;
* basic attack windup and projectile speed from combat_timing;
* raw ability damage from marksman_damage_components.damage_component;
* self-buff attack speed, AD and range from the fight engine's own buff() calls, read from its
  source and applied to a Kit, so the kit decides what each buff changes.

What stays outside the engine are the practice rules below: how an ability meets a lone dummy,
and which abilities show no number because their damage needs state the practice dummy does
not track (stacks, missing health, channel ticks). The tool applies the dummy's armor and magic
resistance itself (the Practice Tool's resistance multiplier is the engine's: 100 / (100 + x)).
"""

import ast
import json
import math
from functools import lru_cache
from pathlib import Path

from . import marksman_fight_engine
from .aa_engine import stats
from .app_data import champion_level_stats
from .champion_database import CHAMPION_DATABASE, champion_stat
from .combat_timing import attack_travel, attack_windup
from .marksman_damage_components import damage_component, jhin_attack_damage
from .marksman_kits import CHANNELS, Kit, default_ranks
from .targets import TARGET_PROFILES, target_profile_at_level

LEVELS = range(1, 16)
SLOTS = ("Q", "W", "E", "R")
# Bonus attack speed steps for the windup table (the tool interpolates between them).
WINDUP_STEPS = [round(0.1 * i, 1) for i in range(31)]
# Distances (game units) for the projectile travel table.
TRAVEL_STEPS = list(range(0, 3001, 250))

# How an ability meets one training dummy. Without an entry it is a "hit": its raw damage lands
# when it reaches the dummy, with damage_component's defaults (no stacks, one hit).
HIT_OPTIONS = {
    ("Kai'Sa", "Q"): {"hits": 6},  # an isolated dummy takes all six missiles
    ("Xayah", "Q"): {"hits": 2},  # two daggers, as the fight engine casts it
    ("Varus", "Q"): {"empowered": True},  # cast at full charge, as the fight engine casts it
}
# Damage added to basic attacks instead of landing on the cast: "buff" while the buff lasts,
# "next" on the next basic attack (the fight engine's Spinning Axe and Tumble).
ON_ATTACK = {("Draven", "Q"): "buff", ("Vayne", "Q"): "next"}
# Damage stored on the dummy and released by the next other hit within the window
# (Essence Flux: the fight engine keeps the mark for 4 seconds).
MARKS = {("Ezreal", "W"): 4.0}
# Shown as a hit without a number, with the reason in the tool.
SKIPPED = {
    ("Ashe", "Q"): "Flurry damage is not resolved in the engine.",
    ("Caitlyn", "R"): "Damage depends on the target's missing health.",
    ("Corki", "W"): "Damage over time along the path.",
    ("Corki", "E"): "Damage over time.",
    ("Jhin", "R"): "Jhin's rework is waiting on in-game data.",
    ("Jinx", "R"): "Damage depends on flight distance and missing health.",
    ("Kalista", "W"): "Soul-Marked damage is not resolved in the engine.",
    ("Kalista", "E"): "Damage depends on spear stacks.",
    ("Kog'Maw", "W"): "On-hit damage is a share of the target's maximum health.",
    ("Kog'Maw", "R"): "Damage depends on the target's missing health.",
    ("Lucian", "R"): "Channeled shots.",
    ("Miss Fortune", "E"): "Damage over time.",
    ("Miss Fortune", "R"): "Channeled waves.",
    ("Samira", "W"): "Hits over the spin.",
    ("Samira", "R"): "Channeled shots.",
    ("Smolder", "E"): "Fireballs pick the lowest-health target.",
    ("Tristana", "E"): "Charge detonation and stacks.",
    ("Twitch", "W"): "Venom stacks and pool.",
    ("Twitch", "E"): "Damage depends on venom stacks.",
    ("Vayne", "W"): "Third-hit true damage is not simulated.",
    ("Sivir", "W"): "Bounce damage needs a second target.",
    ("Yunara", "Q"): "On-hit damage is not simulated.",
    ("Varus", "W"): "Blight stacks.",
    ("Xayah", "E"): "Damage depends on recalled feathers.",
    ("Zeri", "E"): "Empowers later attacks.",
}
# Basic attacks deal the champion's AD as physical damage; on-hit passives are not simulated
# (the tool says so for every champion). Extra notes for single champions:
ATTACK_NOTES = {
    "Jhin": "Jhin's rework is waiting on in-game data: the four-shot reload and the fourth-shot crit are not shown.",
}


def _round(value):
    return round(value, 3)


def _base_range(name):
    return champion_stat(name, "attack_range")


def _kit(name, ranks, level=1):
    return Kit(name, ranks, level, _base_range(name))


def _max_ranks():
    return {"Q": 4, "W": 4, "E": 4, "R": 3}


def _rank_limit(slot):
    return 3 if slot == "R" else 4


def _levels(name):
    out = {"ad": [], "as": [], "ms": [], "range": [], "hp": [], "armor": [], "mr": []}
    for level in LEVELS:
        row = champion_level_stats(name, level)
        out["ad"].append(_round(row["attack_damage"]))
        out["as"].append(_round(row["attack_speed"]))
        out["ms"].append(row["movement_speed"])
        for field in ("hp", "armor", "mr"):
            out[field].append(_round(row[field]))
        out["range"].append(_round(_kit(name, default_ranks(name, level), level).attack_range(0.0)))
    return out


def _attack(name):
    """Basic attack: raw physical damage by level, windup by bonus attack speed, projectile speed."""
    damage = []
    for level in LEVELS:
        ad = champion_level_stats(name, level)["attack_damage"]
        if name == "Jhin":
            ad = jhin_attack_damage(ad, level, 0.0, 0.0)
        damage.append(_round(ad))
    seconds = attack_travel(name, 1000.0)
    out = {
        "damage": {"physical": damage},
        "windup": [_round(attack_windup(name, bonus)) for bonus in WINDUP_STEPS],
        "speed": _round(1000.0 / seconds) if seconds else None,
    }
    if name in ATTACK_NOTES:
        out["note"] = ATTACK_NOTES[name]
    return out


def _damage_by_rank(name, slot, *, extra_ad=0, extra_ap=0, **options):
    """{damage type: [rank][level] raw damage}, keeping only the types that occur."""
    table = {"physical": [], "magic": [], "true": []}
    for rank in range(1, _rank_limit(slot) + 1):
        rows = {kind: [] for kind in table}
        for level in LEVELS:
            ad = champion_level_stats(name, level)["attack_damage"]
            raw = damage_component(name, slot, rank, ad=ad + extra_ad, ap=extra_ap, base_ad=ad, level=level, **options)
            for kind in table:
                rows[kind].append(_round(getattr(raw, kind)))
        for kind in table:
            table[kind].append(rows[kind])
    return {kind: rows for kind, rows in table.items() if any(v for row in rows for v in row)}


def _damage_model(name, slot):
    key = (name, slot)
    if key in SKIPPED:
        return {"mode": "skip", "reason": SKIPPED[key]}
    try:
        damage = _damage_by_rank(name, slot, **HIT_OPTIONS.get(key, {}))
    except LookupError as error:
        return {"mode": "skip", "reason": f"Not resolved in the engine: {error}"}
    if not damage:
        return {"mode": "none"}
    scaling = {}
    for stat, kwargs in (("ad", {"extra_ad": 100}), ("ap", {"extra_ap": 100})):
        sampled = _damage_by_rank(name, slot, **kwargs, **HIT_OPTIONS.get(key, {}))
        scaling[stat] = {kind: [[_round((row[i] - damage.get(kind, [[0]*15]*len(rows))[r][i])/100) for i in range(15)] for r, row in enumerate(rows)] for kind, rows in sampled.items()}
    if key in ON_ATTACK:
        return {"mode": "attack", "attacks": ON_ATTACK[key], "damage": damage, "scaling": scaling}
    if key in MARKS:
        return {"mode": "mark", "window": MARKS[key], "damage": damage, "scaling": scaling}
    return {"mode": "hit", "damage": damage, "scaling": scaling}


def _finite(value):
    return None if value is None or math.isinf(value) else _round(value)


def _slot(name, slot):
    limit = _rank_limit(slot)
    ranks = [dict(_max_ranks(), **{slot: rank}) for rank in range(1, limit + 1)]
    kits = [_kit(name, r) for r in ranks]
    travel = [kits[-1].travel(slot, float(d)) or 0.0 for d in TRAVEL_STEPS]
    out = {
        "cooldown": [_finite(kit.cd(slot)) for kit in kits],
        "cast": _round(kits[-1].cast_time(slot, 0.0, 0.0)),
        "reach": [_finite(kit.range(slot, 0.0)) for kit in kits],
        "travel": [_round(t) for t in travel] if any(travel) else None,
        **_damage_model(name, slot),
    }
    channel = CHANNELS.get(name)
    if channel and channel[0] == slot:
        out["channel"] = {"seconds": channel[1], "mobile": channel[2]}
    buff = _buffs(name).get(slot)
    if buff:
        out["buff"] = buff
    if name == "Jinx" and slot == "W":
        out["cast_by_as"] = [_round(kits[-1].cast_time(slot, 0, bonus)) for bonus in WINDUP_STEPS]
    return out


# ---------------------------------------------------------------- self-buffs from the fight engine


def _context(tests):
    """Champion and slots named by the enclosing `if` tests of a buff() call."""
    champion, slots = None, set("QWER")
    for test in tests:
        for node in ast.walk(test):
            if not isinstance(node, ast.Compare) or len(node.ops) != 1:
                continue
            left, op, right = node.left, node.ops[0], node.comparators[0]
            if not isinstance(left, ast.Name):
                continue
            if left.id in ("c", "name") and isinstance(op, ast.Eq) and isinstance(right, ast.Constant):
                champion = right.value
            elif left.id == "slot" and isinstance(op, ast.Eq) and isinstance(right, ast.Constant):
                slots &= {right.value}
            elif left.id == "slot" and isinstance(op, ast.In):
                values = (
                    {e.value for e in right.elts}
                    if isinstance(right, ast.Tuple)
                    else set(right.value)
                    if isinstance(right, ast.Constant)
                    else set("QWER")
                )
                slots &= values
    return champion, slots


@lru_cache(maxsize=1)
def engine_buff_calls():
    """Every buff the fight engine starts: (champion, slots, key, duration, value) expressions."""
    tree = ast.parse(Path(marksman_fight_engine.__file__).read_text())
    found = []

    def visit(node, tests):
        if isinstance(node, ast.If):
            for child in node.body:
                visit(child, tests + [node.test])
            for child in node.orelse:
                visit(child, tests)
            return
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "buff" and len(node.args) == 3:
                found.append((*_context(tests), *node.args))
            elif (
                node.func.id == "queue"
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value == "buff"
            ):
                keywords = {k.arg: k.value for k in node.keywords}
                found.append((*_context(tests), keywords["key"], keywords["duration"], keywords["value"]))
        for child in ast.iter_child_nodes(node):
            visit(child, tests)

    visit(tree, [])
    return [call for call in found if call[0] is not None]


def _evaluate(expression, rank, slot, ranks):
    code = compile(ast.Expression(body=expression), "<fight engine>", "eval")
    return eval(code, {"__builtins__": {}}, {"r": rank, "slot": slot, "ranks": ranks, "s": {"axes": 1}})


def _depends_on(expression):
    """The other slot whose rank an expression reads (Yunara R reads Q's rank), if any."""
    for node in ast.walk(expression):
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == "ranks"
            and isinstance(node.slice, ast.Constant)
        ):
            return node.slice.value
    return None


@lru_cache(maxsize=None)
def _buffs(name):
    """{slot: {"by": slot whose rank indexes the lists, "duration", "as", "ad", "range": per rank}}

    Only buffs that change attack speed, attack damage or attack range, as the kit reads them.
    """
    out = {}
    for slot in SLOTS:
        calls = [c for c in engine_buff_calls() if c[0] == name and slot in c[1]]
        if not calls:
            continue
        by = next((d for c in calls for d in [_depends_on(c[4])] if d), slot)
        rows = {"duration": [], "as": [], "ad": [], "range": []}
        for rank in range(1, _rank_limit(by) + 1):
            ranks = dict(_max_ranks(), **{by: rank})
            kit = _kit(name, ranks)
            before = (kit.bonus_as(0.0), kit.bonus_ad(0.0), kit.attack_range(0.0))
            duration = 0.0
            for _, _, key, length, value in calls:
                seconds = _evaluate(length, ranks[slot], slot, ranks)
                kit.buff(_evaluate(key, ranks[slot], slot, ranks), seconds, _evaluate(value, ranks[slot], slot, ranks))
                duration = max(duration, seconds)
            after = (kit.bonus_as(0.0), kit.bonus_ad(0.0), kit.attack_range(0.0))
            rows["duration"].append(_round(duration))
            for field, a, b in zip(("as", "ad", "range"), before, after):
                rows[field].append(_round(b - a))
        if any(v for field in ("as", "ad", "range") for v in rows[field]):
            out[slot] = {"by": by, **{k: v for k, v in rows.items() if k == "duration" or any(rows[k])}}
    return out


def _rank_attack_speed(name):
    """Bonus attack speed a skill gives just by being ranked (Kog'Maw R), per rank."""
    out = {}
    for slot in SLOTS:
        values = [
            _round(_kit(name, {slot: rank}).bonus_as(0.0)) for rank in range(1, _rank_limit(slot) + 1)
        ]
        if any(values):
            out[slot] = values
    return out


# ---------------------------------------------------------------- catalogue


def champion(name):
    record = {
        "levels": _levels(name),
        "as_ratio": stats(name, 1)["ratio"],
        "ranks": [default_ranks(name, level) for level in LEVELS],
        "attack": _attack(name),
        "slots": {slot: _slot(name, slot) for slot in SLOTS},
    }
    rank_as = _rank_attack_speed(name)
    if rank_as:
        record["rank_as"] = rank_as
    record["duel"] = _duel_mechanics(name)
    return record


def _duel_mechanics(name):
    """Pilot mechanics from repository observations and the reference Kit, not difficulty knobs."""
    kit = _kit(name, _max_ranks(), 15)
    resources = {k: [_round(champion_level_stats(name, level)[k] or 0) for level in LEVELS]
                 for k in ("mana", "hp_regen_per_5s", "mana_regen_per_5s")}
    costs = {s: [_kit(name, dict(_max_ranks(), **{s: r})).cost(s, 0)
                 for r in range(1, _rank_limit(s) + 1)] for s in SLOTS}
    common = {"resources": resources, "costs": costs,
              "source": "data/marksman-ability-catalogue.json; sharpwr/marksman_kits.py"}
    if name == "Ezreal":
        values = []
        for stack in range(5):
            kit.state["rising_spell_force"] = stack
            values.append(_round(kit.bonus_as(0)))
        return {**common, "passive_as": values, "passive_duration": 8,
                "q_refund": 1.5, "flux_refund": [60, 70, 80, 90],
                "bolt_speed": _round(1000 / kit.travel("E", 1000))}
    if name != "Jinx":
        return common
    rows = []
    for rank in range(1, 5):
        k = _kit(name, dict(_max_ranks(), Q=rank))
        values = []
        for stack in range(4):
            k.state["minigun"] = stack
            values.append(_round(k.bonus_as(0)))
        k.weapon = "rockets"
        rows.append({"as": values, "range": k.attack_range(0) - k.base_range})
    return {**common, "minigun": rows, "stack_duration": 2.5, "stack_decay": 2,
            "rocket_multiplier": 1.12,
            "rocket_speed": _round(1000 / attack_travel(name, 1000, weapon="rockets")),
            "minigun_speed": _round(1000 / attack_travel(name, 1000, weapon="minigun")),
            "slow": [0.3, 0.4, 0.5, 0.6], "slow_duration": 2,
            "root": [1.45, 1.55, 1.65, 1.75], "trap_duration": 5,
            "trap_arm": 1, "trap_status": "three discrete traps; provisional 1s arming, 50u spacing and 20u radius",
            "execute_base": [25, 35, 45], "execute_missing": [0.25, 0.30, 0.35],
            "execute_bonus_ad": 0.12,
            "execute_status": "reference endpoints over first flight second; linear interpolation provisional",
            "excited_duration": 6, "excited_as": 0.25, "excited_ms": 1.4,
            "excited_mana": 0.1}


def targets():
    """Benchmark dummies by level (index 0 = level 1)."""
    return {
        label: [
            {k: _round(v) for k, v in target_profile_at_level(profile, level).items()}
            for level in LEVELS
        ]
        for label, profile in TARGET_PROFILES.items()
    }


@lru_cache(maxsize=1)
def practice_data():
    return {"targets": targets(), "champions": {name: champion(name) for name in CHAMPION_DATABASE}}


def render_practice_json(catalogue):
    return json.dumps(catalogue, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n"
