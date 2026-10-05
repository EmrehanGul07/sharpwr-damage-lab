"""Shared, user-sourced persistent rune stats and first-contact damage.

No incoming damage, healing, ally or turret simulation is implied. First Strike
models the explicitly ready initial engagement only; rearming is unresolved.
"""

import math

STAT_RUNES = frozenset(
    {
        "Zombie Ward",
        "Eyeball Collection",
        "Hubris",
        "Absolute Focus",
        "Gathering Storm",
        "Manaflow Band",
        "Legend: Alacrity",
        "Legend: Haste",
        "Legend: Bloodline",
        "Transcendence",
        "Overgrowth",
        "Unshakeable",
    }
)
FIGHT_KEYSTONES = (None, "Conqueror", "Lethal Tempo", "First Strike", "Dark Harvest")
FIGHT_RUNES = STAT_RUNES | {
    "Brutal",
    "Cut Down",
    "Coup de Grace",
    "Battle Zeal",
    "Last Stand",
    "Tyrant",
    "Empowered Attack",
}


def persistent_stats(level, selected, settings=None):
    if isinstance(level, bool) or not isinstance(level, int) or not 1 <= level <= 15:
        raise ValueError("Invalid rune level")
    runes = set(selected) - {None, "None"}
    s = settings or {}

    def number(key, default, low, high):
        value = s.get(key, default)
        if (
            not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not low <= value <= high
        ):
            raise ValueError(f"Invalid rune setting: {key}")
        return value

    out = dict(
        ad=0.0,
        mana=0.0,
        bonus_as=0.0,
        ah=0.0,
        flat_hp=0.0,
        hp_multiplier=1.0,
        resistance_multiplier=1.0,
        omnivamp=0.0,
    )
    if "Zombie Ward" in runes:
        out["ad"] += 15
    if "Eyeball Collection" in runes:
        out["ad"] += 1.5 * number("eyeball_stacks", 8, 0, 8)
    if "Hubris" in runes and s.get("hubris_active", False):
        out["ad"] += 5 + number("hubris_kills", 0, 0, 100)
    if "Absolute Focus" in runes and s.get("absolute_focus_active", True):
        out["ad"] += 2 + 18 * (level - 1) / 14
    if "Gathering Storm" in runes:
        minute = number("game_minute", 0, 0, 21)
        out["ad"] += max(
            (v for m, v in ((6, 2), (9, 5), (12, 9), (15, 14), (18, 20), (21, 27)) if minute >= m),
            default=0,
        )
    if "Manaflow Band" in runes:
        out["mana"] = 300.0
    if "Legend: Alacrity" in runes:
        out["bonus_as"] = 0.21 if s.get("alacrity_full", False) else 0.03
    if "Legend: Haste" in runes and s.get("haste_full", False):
        out["ah"] += 15
    if "Transcendence" in runes:
        out["ah"] += 5 if level < 5 else 10
    if "Legend: Bloodline" in runes:
        out["omnivamp"] = 0.08 if s.get("bloodline_full", False) else 0.01
    if "Overgrowth" in runes:
        stacks = number("overgrowth_stacks", 60, 0, 999)
        out["flat_hp"] = 3 * stacks
        out["hp_multiplier"] = 1.03 if stacks >= 30 else 1.0
    if "Unshakeable" in runes:
        out["resistance_multiplier"] = 1.03 + 0.02 * number("nearby_enemies", 3, 0, 3)
    return out


def own_stats(core, item_stats, rune_stats):
    """Keep unknown base stats unknown; apply Overgrowth to full champion HP."""

    def total(field, item):
        return None if core[field] is None else core[field] + item_stats.get(item, 0.0)

    hp = total("hp", "hp")
    return {
        "hp": None if hp is None else (hp + rune_stats["flat_hp"]) * rune_stats["hp_multiplier"],
        "armor": (
            None
            if core["armor"] is None
            else total("armor", "armor") * rune_stats["resistance_multiplier"]
        ),
        "mr": (
            None if core["mr"] is None else total("mr", "mr") * rune_stats["resistance_multiplier"]
        ),
    }


def last_stand_multiplier(own_hp_pct):
    if not math.isfinite(own_hp_pct) or not 0 <= own_hp_pct <= 100:
        raise ValueError("Invalid own health")
    missing = 100 - own_hp_pct
    return 1.0 if missing < 30 else 1.0 + min(0.11, 0.05 + ((missing - 30) // 5) * 0.01)


class FirstContact:
    def __init__(self, enabled=False, ready=True):
        self.enabled = enabled and ready
        self.start = None

    def apply(self, time, damage):
        if not self.enabled or damage <= 0:
            return damage, []
        if self.start is None:
            self.start = time
        if time < self.start + 3.0 - 1e-9:
            return damage * 1.07, ["First Strike: +7% true damage (initial 3s engagement)"]
        return damage, []


class DamageProcs:
    """Recorded ADC physical-adaptive proc model; no new flight times inferred."""

    def __init__(self, level, keystone, runes, souls=0):
        if isinstance(souls, bool) or not isinstance(souls, int) or souls < 0:
            raise ValueError("Invalid Dark Harvest souls")
        self.level = level
        self.keystone = keystone
        self.runes = set(runes)
        self.souls = souls
        self.ready = {name: 0.0 for name in ("Dark Harvest", "Tyrant", "Empowered Attack")}

    def apply(
        self, time, action, hp_fraction, bonus_ad, ap, physical_multiplier, damage_multiplier=1.0
    ):
        from .champion_skill_data import resistance_multiplier

        candidates = []
        scale = lambda low, high: low + (high - low) * (self.level - 1) / 14
        if (
            self.keystone == "Dark Harvest"
            and hp_fraction < 0.5
            and time >= self.ready["Dark Harvest"]
        ):
            candidates.append(
                ("Dark Harvest", 35 + 11 * self.souls + 0.1 * bonus_ad + 0.05 * ap, 20.0)
            )
            self.souls += 1
        if "Tyrant" in self.runes and hp_fraction < 0.5 and time >= self.ready["Tyrant"]:
            candidates.append(("Tyrant", scale(20, 70) + 0.06 * bonus_ad + 0.03 * ap, 10.0))
        if (
            "Empowered Attack" in self.runes
            and action.startswith("AA")
            and time >= self.ready["Empowered Attack"]
        ):
            candidates.append(("Empowered Attack", scale(20, 60) * 0.8, 8.0))
        parts = []
        notes = []
        damage = 0.0
        for name, raw, cooldown in candidates:
            amount = raw * resistance_multiplier(physical_multiplier) * damage_multiplier
            damage += amount
            self.ready[name] = time + cooldown
            parts.append(
                {
                    "damage_type": "physical",
                    "raw_amount": raw,
                    "tags": [],
                    "status": "unknown_WR",
                    "component": name + " rune proc",
                    "origin": "Rune",
                }
            )
            notes.append(f"{name} +{amount:.3f} physical (ADC adaptive model)")
        return damage, notes, parts
