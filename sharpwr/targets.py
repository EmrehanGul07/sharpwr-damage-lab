"""User-tested benchmark target profiles (HP, armor, MR, AA reduction) by level."""

from .aa_engine import gu

# User-tested level benchmark profiles.
SQUISHY_JINX_PROFILE = {
    1: {"hp": 630, "armor": 35, "mr": 30},
    5: {"hp": 1014, "armor": 51, "mr": 35},
    6: {"hp": 1122, "armor": 56, "mr": 36},
    8: {"hp": 1353, "armor": 66, "mr": 39},
    9: {"hp": 1475, "armor": 71, "mr": 40},
    11: {"hp": 1734, "armor": 81, "mr": 43},
    12: {"hp": 1871, "armor": 87, "mr": 45},
    14: {"hp": 2159, "armor": 99, "mr": 48},
    15: {"hp": 2310, "armor": 105, "mr": 50},
}


BRUISER_DARIUS_PROFILE = {
    1: {"hp": 660, "armor": 47, "mr": 40, "aa_reduction": 0},
    5: {"hp": 1617, "armor": 89, "mr": 46, "aa_reduction": 0.10},
    6: {"hp": 1750, "armor": 94, "mr": 48, "aa_reduction": 0.10},
    8: {"hp": 2034, "armor": 151, "mr": 52, "aa_reduction": 0.10},
    9: {"hp": 2185, "armor": 156, "mr": 54, "aa_reduction": 0.10},
    11: {"hp": 2905, "armor": 167, "mr": 59, "aa_reduction": 0.10},
    12: {"hp": 3074, "armor": 173, "mr": 61, "aa_reduction": 0.10},
    14: {"hp": 3729, "armor": 242, "mr": 117, "aa_reduction": 0.10},
    15: {"hp": 4315, "armor": 249, "mr": 182, "aa_reduction": 0.10},
}


TANK_ORNN_PROFILE = {
    1: {"hp": 690, "armor": 48, "mr": 42, "aa_reduction": 0},
    5: {"hp": 2065, "armor": 93, "mr": 48, "aa_reduction": 0.10},
    6: {"hp": 2264, "armor": 98, "mr": 50, "aa_reduction": 0.10},
    8: {"hp": 2989, "armor": 154, "mr": 54, "aa_reduction": 0.10},
    9: {"hp": 3264, "armor": 162, "mr": 56, "aa_reduction": 0.10},
    11: {"hp": 3943, "armor": 264, "mr": 61, "aa_reduction": 0.10},
    12: {"hp": 4173, "armor": 270, "mr": 63, "aa_reduction": 0.10},
    14: {"hp": 5086, "armor": 352, "mr": 131, "aa_reduction": 0.10},
    15: {"hp": 5698, "armor": 415, "mr": 184, "aa_reduction": 0.10},
}


TARGET_PROFILES = {
    "Squishy • Jinx": SQUISHY_JINX_PROFILE,
    "Bruiser • Darius": BRUISER_DARIUS_PROFILE,
    "Tank • Ornn": TANK_ORNN_PROFILE,
}


def target_profile_at_level(profile, lvl):
    """Profile stats at any level, interpolated between recorded levels; boots give 10% AA reduction from level 5."""
    lvl = int(lvl)
    if lvl in profile:
        return dict(profile[lvl])
    levels = sorted(profile)
    lo = max(x for x in levels if x < lvl)
    hi = min(x for x in levels if x > lvl)
    t = (lvl - lo) / (hi - lo)
    out = {k: profile[lo][k] + (profile[hi][k] - profile[lo][k]) * t for k in ("hp", "armor", "mr")}
    # Boots are discrete: Lv1 has none; all benchmark builds from Lv5 onward have Steelcaps/Armored Advance.
    out["aa_reduction"] = (
        0.10
        if lvl >= 5 and (profile[hi].get("aa_reduction", 0) or profile[lo].get("aa_reduction", 0))
        else 0
    )
    return out


def benchmark_target(name, lvl):
    """Named target's profile at a level plus bonus_hp above that champion's natural HP."""
    target = dict(target_profile_at_level(TARGET_PROFILES[name], lvl))
    natural_hp = {
        "Squishy • Jinx": target["hp"],
        "Bruiser • Darius": 660 + 148 * gu(lvl),
        "Tank • Ornn": 690 + 132 * gu(lvl),
    }[name]
    target["bonus_hp"] = max(0.0, target["hp"] - natural_hp)
    return target


def profiles_by_target():
    """Independent copies of the three benchmark profiles, keyed squishy/bruiser/tank."""
    from copy import deepcopy

    return deepcopy(
        {
            "squishy": SQUISHY_JINX_PROFILE,
            "bruiser": BRUISER_DARIUS_PROFILE,
            "tank": TANK_ORNN_PROFILE,
        }
    )
