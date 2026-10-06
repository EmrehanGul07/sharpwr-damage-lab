"""Saved build results per champion, computed with the champion's default rune page.

For every matchup (a level in core_items.BUDGETS against each benchmark target):
- cells: the Tier List search on the constrained pool (core_items.EXCLUDED left out); its Top 3
  builds rank the core items (rank_core);
- top: the same search on every item: the Top builds the apps show;
- styles: the full-pool search with each build style's items required and its keystone
  (core_items.build_styles: the editor's core item and data/build-styles.json);
plus a keystone check: the best Top build at KEYSTONE_CHECK_LEVELS replayed with every keystone
the fight engines model. Bounded searches (beam 80, refine 40), not exhaustive.

Searches of one matchup share one evaluator (per keystone), so a build that several searches
reach is fought once; every search still sees its own copies of the rows.

Each champion's results go to a shard in --work, saved after every search, so runs resume.
Several processes can share the work: each claims the next unclaimed champion (a lock file in
--work), most expensive first. --merge then writes data/champion-core-items.json.

Usage: python scripts/build_core_items.py --work DIR [--champion NAME ...]
       python scripts/build_core_items.py --work DIR --merge
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from sharpwr import engine_namespace, profiles_by_target
from sharpwr.build_fight_optimizer import TIER3, search_builds
from sharpwr.core_items import (
    BUDGETS,
    EXCLUDED,
    KEYSTONE_CHECK_LEVELS,
    TARGETS,
    available,
    build_styles,
    cell_evaluator,
    fingerprint,
    matchup,
    rank_core,
    rune_page,
    style_items,
)
from sharpwr.rune_runtime import FIGHT_KEYSTONES

VERSION = "7.1.0"
METHOD = (
    "Tier List search (beam 80, refine 40, every Tier 3 boot) per matchup with the champion's "
    "default rune page: core items from the constrained pool, ranked by Top 3 presence weighted "
    "1, 1/2, 1/3 per eligible matchup; Top builds and build styles from every item. Muramana "
    "from level 11. Bounded search, not exhaustive."
)


class SharedEvaluator:
    """One matchup's evaluator for several searches: cached fights, private row copies."""

    def __init__(self, evaluator):
        self.evaluator = evaluator

    def __getattr__(self, name):
        return getattr(self.evaluator, name)

    def evaluate(self, items, boot=None, refine=False):
        return dict(self.evaluator.evaluate(items, boot, refine=refine))


def search(ns, profiles, evaluator, level, target, pool, required=()):
    boots = [b for b in TIER3 if b in ns["B"]]
    before = evaluator.simulations
    result = search_builds(evaluator, pool, boots, max_items=BUDGETS[level], required=required)
    result["simulations"] = evaluator.simulations - before
    # Keep the finalists with their exact policies; stage lists and marginals are not saved.
    result.pop("stages", None)
    result.pop("marginal", None)
    return {
        "level": level,
        "target": target,
        "budget": BUDGETS[level],
        "yuntal_start_stacks": matchup(ns, profiles, level, target)["yuntal_stacks"],
        "search": result,
    }


def keystone_check(ns, profiles, name, top):
    rows = []
    for level in KEYSTONE_CHECK_LEVELS:
        for target in TARGETS:
            best = top[f"{level}:{target}"]["search"]["full"][0]
            ttk = {}
            for keystone in FIGHT_KEYSTONES:
                if keystone is None:
                    continue
                evaluator = cell_evaluator(ns, profiles, name, level, target, keystone=keystone)
                row = evaluator.evaluate(tuple(best["Items"]), best["Boots"], refine=True)
                ttk[keystone] = row["TTK"]
            rows.append(
                {
                    "level": level,
                    "target": target,
                    "items": list(best["Items"]),
                    "boots": best["Boots"],
                    "ttk": ttk,
                }
            )
    return rows


def matchups():
    return [(level, target) for level in BUDGETS for target in TARGETS]


def compute(ns, profiles, name, path):
    sig = fingerprint()
    shard = json.loads(path.read_text()) if path.exists() else {}
    if shard.get("fingerprint") != sig or shard.get("rune_page") != rune_page(name):
        shard = {
            "fingerprint": sig,
            "rune_page": rune_page(name),
            "cells": {},
            "top": {},
            "styles": {},
        }

    def save():
        path.write_text(json.dumps(shard, separators=(",", ":")))

    def run(section, key, label, evaluator, **kwargs):
        if key in section:
            return
        start = time.time()
        level, target = key.split(":")
        section[key] = search(ns, profiles, evaluator, int(level), target, **kwargs)
        save()
        best = section[key]["search"]["full"][0]
        print(name, label, key, best["Items"], f"{time.time() - start:.0f}s", flush=True)

    styles = build_styles(name)
    for style in styles:
        shard["styles"].setdefault(
            style["key"],
            {
                "name": style["name"],
                "items": style["items"],
                "keystone": style["keystone"],
                "cells": {},
            },
        )
    for level, target in matchups():
        key = f"{level}:{target}"
        evaluators = {}

        def evaluator(keystone):
            if keystone not in evaluators:
                evaluators[keystone] = SharedEvaluator(
                    cell_evaluator(ns, profiles, name, level, target, keystone=keystone)
                )
            return evaluators[keystone]

        full = [i for i in ns["F"] if i != "Muramana" or level >= 11]
        core = [i for i in ns["F"] if available(i, level)]
        run(shard["cells"], key, "core", evaluator(None), pool=core)
        run(shard["top"], key, "top", evaluator(None), pool=full)
        for style in styles:
            run(
                shard["styles"][style["key"]]["cells"],
                key,
                f"style {style['key']}",
                evaluator(style["keystone"]),
                pool=full,
                required=style_items(style, level, BUDGETS[level]),
            )
    if "keystone_check" not in shard:
        shard["keystone_check"] = keystone_check(ns, profiles, name, shard["top"])
        save()
    print("COMPLETE", name, flush=True)


def claim(work, name):
    """Take a champion for this process; a lock left by a dead process is taken over."""
    lock = work / f"{name}.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            os.kill(int(lock.read_text() or 0), 0)
            return False
        except (ProcessLookupError, ValueError):
            lock.write_text(str(os.getpid()))
            return True
    with os.fdopen(fd, "w") as handle:
        handle.write(str(os.getpid()))
    return True


def cost(name):
    """Rough search cost: sections to compute; Jinx's weapon policies take about twice as long."""
    return (2 + len(build_styles(name))) * (2.5 if name == "Jinx" else 1)


def merge(ns, work, output):
    sig = fingerprint()
    data = {
        "version": VERSION,
        "fingerprint": sig,
        "excluded": sorted(EXCLUDED),
        "budgets": BUDGETS,
        "method": METHOD,
        "champions": {},
    }
    for name in ns["C"]:
        path = work / f"{name}.json"
        shard = json.loads(path.read_text()) if path.exists() else {}
        if shard.get("fingerprint") != sig or shard.get("rune_page") != rune_page(name):
            print("missing or stale:", name)
            continue
        styles = {style["key"]: style for style in build_styles(name)}
        complete = len(shard["cells"]) == len(matchups())
        data["champions"][name] = {
            "complete": complete
            and len(shard["top"]) == len(matchups())
            and "keystone_check" in shard,
            "rune_page": shard["rune_page"],
            "cells": shard["cells"],
            "ranking": rank_core(shard["cells"], ns["F"]) if complete else [],
            "top": shard["top"],
            "styles": [
                {"key": key, **record}
                for key, record in shard["styles"].items()
                if key in styles and len(record["cells"]) == len(matchups())
            ],
            "keystone_check": shard.get("keystone_check", []),
        }
    output.write_text(json.dumps(data, separators=(",", ":")))
    print("wrote", output, len(data["champions"]), "champions")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--champion", action="append")
    parser.add_argument("--merge", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "champion-core-items.json")
    args = parser.parse_args()
    ns = engine_namespace()
    if args.merge:
        return merge(ns, args.work, args.output)
    args.work.mkdir(parents=True, exist_ok=True)
    profiles = profiles_by_target()
    names = args.champion or sorted(ns["C"], key=lambda n: -cost(n))
    for name in names:
        if claim(args.work, name):
            compute(ns, profiles, name, args.work / f"{name}.json")


if __name__ == "__main__":
    main()
