"""Rune pages: SharpWR's default page per champion and how a page enters a fight.

`rune_loadout` is the one place that turns a rune page into fight inputs: the keystone and
runes the fight engines model, the persistent stats they grant and the stack settings they
assume. Stack-based runes fill with level, as Yun Tal stacks do in the build search: empty up
to level 5, full from level 9, in between in proportion (editor decision, 2026-10-05).
"""

import json
from pathlib import Path
from typing import NamedTuple

from .rune_database import RUNE_DATABASE, RUNE_SLOTS
from .rune_runtime import FIGHT_KEYSTONES, FIGHT_RUNES, NO_FIGHT_EFFECT, persistent_stats

PAGES_PATH = Path(__file__).resolve().parents[1] / "data" / "default-rune-pages.json"
DEFAULT_PAGES = json.loads(PAGES_PATH.read_text())["pages"]


def stack_progress(level):
    """Share of full stacks at a level: 0 up to level 5, 1 from level 9."""
    return 0.0 if level <= 5 else 1.0 if level >= 9 else (level - 5) / 4


def level_settings(level):
    """persistent_stats settings for stacking runes at a level."""
    progress = stack_progress(level)
    return {
        "alacrity_progress": progress,
        "eyeball_stacks": round(8 * progress),
        "haste_full": progress >= 1,
        "bloodline_full": progress >= 1,
        # Gathering Storm grows with game time; full here means its minute-21 value.
        "game_minute": 21 * progress,
    }


def page_runes(page):
    """Keystone, the three primary runes and the secondary rune, skipping missing ones."""
    runes = [page.get("keystone"), *page.get("primary", ()), page.get("secondary")]
    return [rune for rune in runes if rune]


def page_problems(page):
    """Why a page is not a legal Wild Rift rune page; empty when it is."""
    problems = []
    keystone = page.get("keystone")
    if keystone is None:
        problems.append("Keystone missing")
    elif RUNE_DATABASE.get(keystone, {}).get("tree") != "Key Rune":
        problems.append(f"Not a keystone: {keystone}")
    tree = page.get("primary_tree")
    primary = list(page.get("primary") or [None, None, None])
    if tree not in RUNE_SLOTS:
        problems.append("Primary tree missing")
    else:
        for row, rune in enumerate(primary, start=1):
            if rune is None:
                problems.append(f"Primary row {row} missing")
            elif rune not in RUNE_SLOTS[tree][row]:
                problems.append(f"{rune} is not in {tree} row {row}")
    secondary_tree = page.get("secondary_tree")
    secondary = page.get("secondary")
    if secondary_tree is None or secondary is None:
        problems.append("Secondary rune missing")
    elif secondary_tree == tree or secondary_tree not in RUNE_SLOTS:
        problems.append("The secondary rune must come from another tree")
    elif not any(secondary in runes for runes in RUNE_SLOTS[secondary_tree].values()):
        problems.append(f"{secondary} is not in {secondary_tree}")
    return problems


class RuneLoadout(NamedTuple):
    """Fight inputs from a rune page at one level."""

    keystone: object
    runes: tuple
    persistent: dict
    bonus_as: float
    transcendence: bool
    dark_harvest_souls: int
    unmodeled: tuple


def rune_loadout(page, level):
    """Fight inputs for a page. `unmodeled` lists runes whose damage effect no engine has yet."""
    keystone = page.get("keystone")
    subs = [rune for rune in page_runes(page) if rune != keystone]
    unmodeled = []
    if keystone is not None and keystone not in FIGHT_KEYSTONES:
        unmodeled.append(keystone)
    fight_runes = tuple(rune for rune in subs if rune in FIGHT_RUNES)
    unmodeled += [rune for rune in subs if rune not in FIGHT_RUNES and rune not in NO_FIGHT_EFFECT]
    persistent = persistent_stats(level, fight_runes, level_settings(level))
    return RuneLoadout(
        keystone=keystone if keystone in FIGHT_KEYSTONES else None,
        runes=fight_runes,
        persistent=persistent,
        bonus_as=persistent["bonus_as"],
        transcendence="Transcendence" in fight_runes,
        dark_harvest_souls=level if keystone == "Dark Harvest" else 0,
        unmodeled=tuple(unmodeled),
    )


def default_loadout(champion, level):
    return rune_loadout(DEFAULT_PAGES[champion], level)
