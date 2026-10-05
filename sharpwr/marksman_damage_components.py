"""Known WR raw damage components, independent of timeline/state transitions.

Callers supply stack counts and hit counts explicitly. Unresolved components raise
LookupError; they never fall back to another champion or to PC damage values.
The returned numbers are raw damage before armor/MR, runes and item procs.
"""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class RawDamage:
    physical: float = 0.0
    magic: float = 0.0
    true: float = 0.0

    def instances(self, champion, slot):
        from .damage_classification import annotate_raw

        return annotate_raw(champion, slot, self)


# (damage type, base ranks, total AD ratio, bonus AD ratio, AP ratio)
LINEAR = {
    "Kalista": {"Q": ("physical", (70, 135, 200, 265), 1.1, 0, 0)},
    "Tristana": {
        "W": ("magic", (80, 120, 160, 200), 0, 0.8, 0.5),
        "R": ("magic", (300, 350, 400), 0, 0.7, 1),
    },
    "Twitch": {},
    "Draven": {
        "E": ("physical", (75, 120, 165, 210), 0, 0.5, 0),
        "R": ("physical", (200, 300, 400), 0, 1.5, 0),
    },
    "Kog'Maw": {
        "Q": ("magic", (90, 150, 210, 270), 0, 0, 0.65),
        "E": ("magic", (80, 130, 180, 230), 0, 0, 0.55),
    },
    "Vayne": {"E": ("physical", (50, 80, 110, 140), 0, 0.55, 0)},
    "Ashe": {
        "W": ("physical", (70, 110, 150, 190), 0, 1, 0),
        "R": ("magic", (200, 350, 500), 0, 0, 0.4),
    },
    "Varus": {
        "E": ("physical", (70, 115, 160, 205), 0, 0.9, 0),
        "R": ("magic", (150, 250, 350), 0, 0, 0.8),
    },
    "Xayah": {
        "Q": ("physical", (50, 75, 100, 125), 0, 0.5, 0),
        "R": ("physical", (150, 250, 350), 0, 1, 0),
    },
    "Miss Fortune": {"Q": ("physical", (60, 90, 120, 150), 1.1, 0, 0.35)},
    "Yunara": {"W": ("magic", (60, 110, 160, 210), 0, 0.85, 0.5)},
    "Kai'Sa": {
        "Q": ("physical", (40, 60, 80, 100), 0, 0.5, 0.3),
        "W": ("magic", (30, 60, 90, 120), 1.3, 0, 0.5),
    },
    "Corki": {
        "Q": ("magic", (60, 120, 180, 240), 0, 1.1, 1),
        "W": ("magic", (60, 100, 140, 180), 0, 0.6, 0.6),
        "E": ("physical", (20, 35, 50, 65), 0, 0.55, 0),
    },
    "Lucian": {
        "Q": ("physical", (75, 125, 175, 225), 0, 1, 0),
        "W": ("magic", (75, 125, 175, 225), 0, 0, 0.9),
        "R": ("physical", (20, 25, 30), 0.25, 0, 0.15),
    },
    "Caitlyn": {"E": ("magic", (70, 120, 170, 220), 0, 0, 0.8)},
    "Jinx": {
        "W": ("physical", (10, 80, 150, 220), 1.6, 0, 0),
        "E": ("magic", (70, 140, 210, 280), 0, 0, 1),
    },
    "Ezreal": {
        "Q": ("physical", (25, 55, 85, 115), 1.35, 0, 0.3),
        "E": ("magic", (80, 145, 210, 275), 0, 0.5, 0.75),
        "R": ("magic", (300, 500, 700), 0, 1, 1),
    },
    "Zeri": {
        "W": ("physical", (60, 100, 140, 180), 1, 0, 0.5),
        "R": ("magic", (150, 225, 300), 0, 0.6, 1),
    },
    "Jhin": {
        "W": ("physical", (60, 100, 140, 180), 0.4, 0, 0),
        "E": ("magic", (20, 100, 180, 260), 1.2, 0, 1),
    },
    "Sivir": {"Q": ("physical", (70, 100, 130, 160), 0, 0.7, 0.6)},
    "Senna": {
        "Q": ("physical", (50, 80, 110, 140), 0, 0.6, 0),
        "W": ("physical", (90, 155, 220, 285), 0, 0.7, 0),
        "R": ("physical", (250, 400, 550), 0, 1.2, 0.7),
    },
}


def jhin_attack_damage(unconverted_ad, level, bonus_as, crit_chance):
    """WR 7.3 Whisper: total pre-passive AD × (1 + .30 AS + .40 crit + .03 level).

    All percentages are decimal fractions; conversion is applied once, including
    transient AS and AD. Source: Riot Wild Rift patch 7.3 (2026-09-21).
    """
    if (
        not all(math.isfinite(x) for x in (unconverted_ad, bonus_as, crit_chance))
        or unconverted_ad < 0
        or bonus_as < 0
        or not 0 <= crit_chance <= 1
        or not isinstance(level, int)
        or not 1 <= level <= 15
    ):
        raise ValueError("Invalid Jhin conversion stats")
    return unconverted_ad * (1 + 0.30 * bonus_as + 0.40 * crit_chance + 0.03 * level)


def xayah_feather_multiplier(hits):
    """WR Bladecaller template source: -10 percentage points per preceding feather, floor10%."""
    if not isinstance(hits, int) or isinstance(hits, bool) or hits < 0:
        raise ValueError("Invalid feather count")
    return sum(max(0.1, 1 - 0.1 * i) for i in range(hits))


def damage_component(
    champion,
    slot,
    rank,
    *,
    ad,
    base_ad,
    ap=0.0,
    crit_chance=0.0,
    crit_damage=2.0,
    stacks=0,
    hits=1,
    target_max_hp=0.0,
    target_missing_hp=0.0,
    level=1,
    empowered=False,
    wall=False,
):
    values = (ad, base_ad, ap, crit_chance, crit_damage, target_max_hp, target_missing_hp)
    if (
        not all(math.isfinite(v) for v in values)
        or min(ad, base_ad, ap, target_max_hp, target_missing_hp) < 0
        or target_missing_hp > target_max_hp
        or not 0 <= crit_chance <= 1
        or crit_damage < 1
    ):
        raise ValueError("Invalid damage stats")
    limit = 3 if slot == "R" else 4
    if (
        slot not in ("P", "Q", "W", "E", "R")
        or not isinstance(rank, int)
        or isinstance(rank, bool)
        or not 1 <= rank <= limit
    ):
        raise ValueError("Invalid slot/rank")
    if (
        not isinstance(stacks, int)
        or stacks < 0
        or not isinstance(hits, int)
        or hits < 1
        or not isinstance(level, int)
        or not 1 <= level <= 15
    ):
        raise ValueError("Invalid level/stacks/hits")
    if champion == "Samira" and slot != "P":
        from .champion_skill_data import samira_skill

        v = samira_skill(
            slot, rank, ad, crit_chance, crit_damage, 0, base_ad=base_ad, mr=0, hits=hits
        )
        return RawDamage(v.physical, v.magic, v.true)
    if champion == "Smolder" and slot != "P":
        from .champion_skill_data import smolder_skill

        physical, magic = smolder_skill(
            slot, rank, ad, base_ad, ap, stacks, crit_chance, crit_damage
        )
        return RawDamage(physical * hits, magic * hits)
    no_direct = {
        "Kalista": ("R",),
        "Tristana": ("Q",),
        "Twitch": ("Q", "R"),
        "Draven": ("W",),
        "Vayne": ("R",),
        "Ashe": ("E",),
        "Xayah": ("W",),
        "Miss Fortune": ("W",),
        "Yunara": ("E", "R"),
        "Kai'Sa": ("E", "R"),
        "Lucian": ("E",),
        "Jinx": ("Q",),
        "Sivir": ("E", "R"),
        "Senna": ("E",),
    }
    if slot in no_direct.get(champion, ()):
        return RawDamage()
    b = max(0.0, ad - base_ad)
    i = rank - 1
    c = crit_chance
    d = crit_damage
    kind = "physical"
    value = None
    mult = hits
    if slot in LINEAR.get(champion, {}):
        kind, bases, a_ratio, b_ratio, ap_ratio = LINEAR[champion][slot]
        value = bases[i] + a_ratio * ad + b_ratio * b + ap_ratio * ap
    if champion == "Kalista" and slot == "E":
        value = (
            (30, 45, 60, 75)[i]
            + 0.7 * ad
            + max(0, stacks - 1) * ((12, 22, 32, 42)[i] + (0.36, 0.43, 0.50, 0.57)[i] * ad)
            if stacks
            else 0
        )
    elif champion == "Tristana" and slot == "E":
        if stacks > 4:
            raise ValueError("Explosive Charge has at most four stacks")
        value = (
            ((80, 110, 140, 170)[i] + 1.2 * b + 0.5 * ap)
            * (1 + 0.5 * c * (d - 1))
            * (1 + 0.25 * stacks)
        )
    elif champion == "Twitch" and slot == "P":
        if stacks > 5:
            raise ValueError("Deadly Venom has at most five stacks")
        kind = "true"
        value = (1 + (level - 1) // 3 + 0.03 * ap) * stacks
    elif champion == "Twitch" and slot == "E":
        if stacks > 5:
            raise ValueError("Deadly Venom has at most five stacks")
        return RawDamage(
            ((30, 40, 50, 60)[i] + stacks * ((20, 25, 30, 35)[i] + 0.35 * b)) * hits,
            stacks * 0.35 * ap * hits,
        )
    elif champion == "Draven" and slot == "Q":
        value = (45, 50, 55, 60)[i] + (0.9, 1, 1.1, 1.2)[i] * b
    elif champion == "Kog'Maw" and slot == "W":
        kind = "magic"
        value = target_max_hp * ((0.015, 0.025, 0.035, 0.045)[i] + 0.0001 * ap)
    elif champion == "Vayne" and slot == "Q":
        value = (0.5, 0.6, 0.7, 0.8)[i] * ad
    elif champion == "Vayne" and slot == "W":
        kind = "true"
        value = max((50, 65, 80, 95)[i], target_max_hp * (0.06, 0.07, 0.08, 0.09)[i])
    elif champion == "Vayne" and slot == "E" and wall:
        value += (105, 145, 185, 225)[i] + 0.75 * b
    elif champion == "Varus" and slot == "Q":
        value = (
            ((120, 210, 300, 390)[i] + (1.65, 1.8, 1.95, 2.1)[i] * b)
            if empowered
            else ((80, 140, 200, 260)[i] + (1.1, 1.2, 1.3, 1.4)[i] * b)
        )
    elif champion == "Varus" and slot == "W":
        kind = "magic"
        value = (15, 25, 35, 45)[i] + 0.35 * ap
    elif champion == "Xayah" and slot == "E":
        mult = xayah_feather_multiplier(hits)
        value = ((70, 80, 90, 100)[i] + 0.5 * b) * (1 + 0.5 * c * (d - 1))
    elif champion == "Miss Fortune" and slot == "E":
        kind = "magic"
        value = (15, 20, 25, 30)[i] + (0.10, 0.11, 0.12, 0.13)[i] * ap
    elif champion == "Miss Fortune" and slot == "R":
        value = ((20, 30, 40)[i] + 0.6 * ad + 0.2 * ap) * (1 + c * (0.3 + 0.3 * (d - 2)))
    elif champion == "Yunara" and slot == "Q":
        kind = "magic"
        value = ((10, 15, 20, 25)[i] + 0.2 * ap) * (2 if empowered else 1)
    elif champion == "Yunara" and slot == "W" and empowered:
        raise LookupError("Empowered W requires ultimate rank, not W rank; use yunara_arc_of_ruin")
    elif champion == "Kai'Sa" and slot == "Q":
        if hits not in (1, 6, 12):
            raise ValueError(
                "Supply one missile, six isolated missiles, or twelve evolved missiles"
            )
        mult = 1 + 0.25 * (hits - 1)
    elif champion == "Corki" and slot == "R":
        value = ((140, 210, 280)[i] + 1.3 * b) if empowered else ((70, 140, 210)[i] + 0.65 * b)
    elif champion == "Jhin" and slot == "R":
        if empowered:
            raise LookupError("Fourth R shot crit/item interaction unresolved")
        value = ((75, 150, 225)[i] + 0.25 * ad) * (
            1 + 3 * (target_missing_hp / target_max_hp if target_max_hp else 0)
        )
    elif champion == "Caitlyn" and slot == "Q":
        value = (50, 100, 150, 200)[i] + (1.25, 1.45, 1.65, 1.85)[i] * ad
    elif champion == "Caitlyn" and slot == "W":
        value = (40, 90, 140, 190)[i] + 0.3 * b
    elif champion == "Ezreal" and slot == "W":
        kind = "magic"
        value = (80, 155, 230, 305)[i] + 0.6 * b + (0.75, 0.80, 0.85, 0.90)[i] * ap
    elif champion == "Zeri" and slot == "Q":
        kind = "magic"
        value = (70, 100, 130, 160)[i] + 0.8 * b + (0.3, 0.35, 0.4, 0.45)[i] * ap
    elif champion == "Zeri" and slot == "E":
        kind = "magic"
        value = ((20, 23, 26, 29)[i] + 0.1 * b + 0.2 * ap) * (1 + c)
    elif champion == "Jhin" and slot == "Q":
        value = (45, 80, 115, 150)[i] + (0.35, 0.45, 0.55, 0.65)[i] * ad + 0.6 * ap
    elif champion == "Sivir" and slot == "Q":
        value *= 1 + 0.4 * c * (d - 1)
    elif champion == "Sivir" and slot == "W":
        value = (0.3, 0.35, 0.4, 0.45)[i] * ad
    if value is None:
        raise LookupError(f"{champion} {slot}: no resolved raw damage component")
    if champion == "Zeri" and slot == "W" and wall:
        raise LookupError("Wall critical modifier requires verified WR interaction")
    return RawDamage(**{kind: value * mult})


def yunara_arc_of_ruin(ultimate_rank, *, bonus_ad, ap=0.0):
    if (
        ultimate_rank not in (1, 2, 3)
        or min(bonus_ad, ap) < 0
        or not all(math.isfinite(v) for v in (bonus_ad, ap))
    ):
        raise ValueError("Invalid ultimate stats")
    return RawDamage(magic=(160, 320, 480)[ultimate_rank - 1] + 1.2 * bonus_ad + 0.75 * ap)


def varus_blight(rank, stacks, *, target_max_hp, ap=0.0):
    if (
        rank not in (1, 2, 3, 4)
        or stacks not in (0, 1, 2, 3)
        or min(target_max_hp, ap) < 0
        or not all(math.isfinite(v) for v in (target_max_hp, ap))
    ):
        raise ValueError("Invalid blight stats")
    return RawDamage(
        magic=stacks * target_max_hp * ((0.03, 0.035, 0.04, 0.045)[rank - 1] + 0.00012 * ap)
    )


def yunara_linger_tick(rank, *, bonus_ad, ap=0.0):
    """User WR screenshot: one normal W tick, excluding its initial hit."""
    if (
        rank not in (1, 2, 3, 4)
        or min(bonus_ad, ap) < 0
        or not all(math.isfinite(v) for v in (bonus_ad, ap))
    ):
        raise ValueError("Invalid Yunara W tick stats")
    return RawDamage(magic=(8, 14, 20, 26)[rank - 1] + 0.12 * bonus_ad + 0.075 * ap)
