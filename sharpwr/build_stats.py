"""Build summary: a champion's stats with items and boots when a fight starts.

The one source for the summary the build search reports (AD, AP, Crit %, AH, Starting AS,
AS over cap, gold) and for the mobile app's build calculator, which is tested against
golden outputs of this module (app-data/golden/build-stats.json).
"""

from .aa_engine import stats
from .catalog import B, F, K, dct
from .champion_database import level_stats
from .marksman_damage_components import jhin_attack_damage

MANA_ITEMS = ("Manamune", "Muramana")


def build_totals(items, boot=None):
    """Every item tuple field (K) summed over the items, then the boots."""
    rows = [dct(F[x]) for x in items] + [dct(B[boot]) if boot else dct(())]
    return {k: sum(q[k] for q in rows) for k in K}


def awe_bonus(items, max_mana):
    """Manamune / Muramana Awe: 2% of maximum mana as bonus AD."""
    return 0.02 * (max_mana or 0) if any(x in items for x in MANA_ITEMS) else 0


def build_stats(
    champion, level, items, boot=None, mist=0, yuntal_stacks=0, base_mana=None, runes=None
):
    """Stats at the start of a fight, before stacks, procs and ability effects.

    Items are summed in sorted order, as the build search does, so results match its saved
    rows exactly. base_mana is used only when the champion has no recorded mana. Health,
    mana, armor and MR are None where the champion's value is unknown. runes is a
    sharpwr.rune_pages.RuneLoadout; its persistent AD, attack speed, ability haste and mana
    are added (without runes the results are unchanged).
    """
    n, l = champion, level
    items = tuple(sorted(items))
    core = level_stats(n, l)
    s = stats(n, l, mist)
    total = build_totals(items, boot)
    base_mana = core["mana"] if core["mana"] is not None else base_mana
    max_mana = None if base_mana is None else base_mana + total["mana"]
    if runes and max_mana is not None:
        max_mana += runes.persistent["mana"]
    yuntal_crit = min(0.25, yuntal_stacks * 0.002) if "Yun Tal Wildarrows" in items else 0.0
    starting_ad = s["ad"] + total["ad"] + awe_bonus(items, max_mana)
    bonus_as = s["bba"] + s["lvbas"] + total["as"]
    if runes:
        starting_ad += runes.persistent["ad"]
        bonus_as += runes.bonus_as
    if n == "Jhin":
        # Whisper converts attack speed and crit into AD; Jhin's attack speed does not grow.
        starting_ad = jhin_attack_damage(
            starting_ad, l, bonus_as, min(1, total["crit"] + yuntal_crit)
        )
        start_raw = s["baseas"] + s["ratio"] * (s["bba"] + s["lvbas"])
    else:
        start_raw = s["baseas"] + s["ratio"] * bonus_as
    cap = 1.5 if n == "Zeri" else 3
    if n == "Zeri":
        # Zeri converts bonus attack speed above her 1.5 cap into AD.
        starting_ad += 0.5 * max(0.0, (bonus_as - max(0.0, (1.5 - s["baseas"]) / s["ratio"])) * 100)
    crit_damage = 2.3 if "Infinity Edge" in items else 2.0
    if n == "Senna":
        crit_damage *= 0.9

    def plus(key, champion_value):
        return None if champion_value is None else champion_value + total[key]

    return {
        "gold": total["gold"],
        "attack_damage": starting_ad,
        "ability_power": total["ap"],
        "attack_speed": min(cap, start_raw),
        "attack_speed_over_cap": max(0, start_raw - cap),
        "attack_speed_cap": cap,
        "crit_chance": min(
            1.0, total["crit"] + (mist // 20 * 0.1 if n == "Senna" else 0.0) + yuntal_crit
        ),
        # Basic attacks; abilities that crit use their own rules.
        "crit_damage": crit_damage,
        "ability_haste": total["ah"] + (runes.persistent["ah"] if runes else 0),
        "armor_pen_pct": total["pctpen"],
        "armor_pen_flat": total["flatpen"],
        "magic_pen_pct": total["pctmpen"],
        "magic_pen_flat": total["flatmpen"],
        "lifesteal": total["ls"],
        "health": plus("hp", core["hp"]),
        "mana": max_mana,
        "armor": plus("armor", core["armor"]),
        "magic_resist": plus("mr", core["mr"]),
        "movement_speed": (core["movement_speed"] or 0) * (1 + sum(dct(F[x])["ms"] for x in items))
        + (dct(B[boot])["ms"] if boot else 0),
    }
