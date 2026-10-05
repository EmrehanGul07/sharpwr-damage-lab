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
FIGHT_KEYSTONES = (
    None,
    "Conqueror",
    "Lethal Tempo",
    "First Strike",
    "Dark Harvest",
    "Empowerment",
    "Phase Rush",
    "Fleet Footwork",
)
# No effect on damage against the benchmark: a stationary target that deals no damage, with no
# allies, turrets, plants or summoner spells in the fight. Pages may hold them; fights ignore them.
NO_FIGHT_EFFECT = frozenset(
    {
        "Guardian",
        "Triumph",
        "Relentless Hunter",
        "Bone Plating",
        "Second Wind",
        "Perseverance",
        "Revitalize",
        "Nullifying Orb",
        "Courage of the Colossus",
        "Font of Life",
        "Demolish",
        "Nimbus Cloak",
        "Hexflash",
        "Ixtali Seedjar",
        "Botanist",
    }
)
FIGHT_RUNES = STAT_RUNES | {
    "Brutal",
    "Cut Down",
    "Coup de Grace",
    "Battle Zeal",
    "Last Stand",
    "Tyrant",
    "Empowered Attack",
    "Sudden Impact",
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
        if "alacrity_progress" in s:
            # Share of the 18% takedown attack speed, on top of the base 3%.
            out["bonus_as"] = 0.03 + 0.18 * number("alacrity_progress", 0, 0, 1)
        else:
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
    """Recorded ADC physical-adaptive proc model; no new flight times inferred.

    Empowerment: every damaging attack or ability hit counts; three hits with no gap over 4s
    deal its adaptive damage (cooldown 4s) and from then on amplify all damage by 8% for the
    rest of the fight. Sudden Impact: the first attack or ability hit within 4s after a dash
    ends deals true damage (cooldown 15s); engines report dashes through dashed().
    """

    def __init__(self, level, keystone, runes, souls=0):
        if isinstance(souls, bool) or not isinstance(souls, int) or souls < 0:
            raise ValueError("Invalid Dark Harvest souls")
        self.level = level
        self.keystone = keystone
        self.runes = set(runes)
        self.souls = souls
        self.ready = {
            name: 0.0
            for name in (
                "Dark Harvest",
                "Tyrant",
                "Empowered Attack",
                "Empowerment",
                "Sudden Impact",
            )
        }
        self.hits = 0
        self.last_hit = None
        self.empowered = False
        self.dash_end = None

    def dashed(self, end_time):
        """A dash, leap or blink of the attacker ended at end_time."""
        self.dash_end = end_time

    def amplification(self):
        """Damage multiplier from Empowerment once it has fired."""
        return 1.08 if self.empowered else 1.0

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
        amplification = self.amplification()
        if self.keystone == "Empowerment":
            if self.last_hit is not None and time - self.last_hit > 4.0:
                self.hits = 0
            self.last_hit = time
            self.hits += 1
            if self.hits >= 3 and time >= self.ready["Empowerment"]:
                candidates.append(("Empowerment", scale(40, 165), 4.0))
                self.hits = 0
                self.empowered = True
        if (
            "Sudden Impact" in self.runes
            and self.dash_end is not None
            and self.dash_end <= time <= self.dash_end + 4.0
            and time >= self.ready["Sudden Impact"]
        ):
            candidates.append(("Sudden Impact", scale(10, 65), 15.0, "true"))
            self.dash_end = None
        parts = []
        notes = []
        damage = 0.0
        for name, raw, cooldown, *kind in candidates:
            kind = kind[0] if kind else "physical"
            resist = 1.0 if kind == "true" else resistance_multiplier(physical_multiplier)
            amount = raw * resist * damage_multiplier * amplification
            damage += amount
            self.ready[name] = time + cooldown
            parts.append(
                {
                    "damage_type": kind,
                    "raw_amount": raw,
                    "tags": [],
                    "status": "unknown_WR",
                    "component": name + " rune proc",
                    "origin": "Rune",
                }
            )
            label = "true" if kind == "true" else "physical (ADC adaptive model)"
            notes.append(f"{name} +{amount:.3f} {label}")
        return damage, notes, parts


class PhaseRush:
    """Phase Rush: 3 champion hits within 4s grant +10 basic ability haste for 3s and cut the
    remaining basic ability cooldowns by 20% (cooldown 21-7s by level). Its movement speed has
    no effect on the stationary benchmark."""

    def __init__(self, enabled, level):
        self.enabled = enabled
        self.cooldown = 21 + (7 - 21) * (level - 1) / 14
        self.hits = []
        self.ready = 0.0
        self.active_until = -1.0

    def hit(self, time):
        """Record a damaging hit; True when Phase Rush fires on it."""
        if not self.enabled:
            return False
        self.hits = [h for h in self.hits if time - h <= 4.0] + [time]
        if len(self.hits) >= 3 and time >= self.ready:
            self.hits = []
            self.ready = time + self.cooldown
            self.active_until = time + 3.0
            return True
        return False

    def haste(self, time):
        """Extra basic ability haste at a time."""
        return 10.0 if self.enabled and time < self.active_until else 0.0


class FleetFootwork:
    """Fleet Footwork: at 100 energy the next attack gains 40% attack speed for its attack
    cycle. Energy follows the engine's Energized item rule (9 per attack, 26 per 700 units
    moved): WR's own charge rate is not recorded. Its heal and movement speed have no effect
    on the stationary benchmark."""

    def __init__(self, enabled, ready=False):
        self.enabled = enabled
        self.energy = 100.0 if ready else 0.0
        self.distance = 0.0
        self.empowered = False

    def bonus_as(self):
        return 0.40 if self.empowered else 0.0

    def start_attack(self, movement_distance):
        """Call when an attack starts, before its timing is read."""
        if not self.enabled:
            return
        self.energy = min(100.0, self.energy + (movement_distance - self.distance) * 26.0 / 700.0)
        self.distance = movement_distance
        if self.energy >= 100.0 - 1e-9:
            self.empowered = True
            self.energy = 0.0
        else:
            self.empowered = False
            self.energy = min(100.0, self.energy + 9.0)
