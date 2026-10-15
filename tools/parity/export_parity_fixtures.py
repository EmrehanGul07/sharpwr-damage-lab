"""Export Python Damage Lab results as parity fixtures for the C# simulation core.

Read-only with respect to the Damage Lab: imports `sharpwr` and reads `data/`, never writes
there. Output: game/parity/fixtures/<champion>-reference-v<N>.json

Every expected value is produced by calling the existing engine, never re-derived here, so the
C# port is compared against the reference implementation itself. Each case carries the engine
function it came from and the data status of its inputs, so a failing case can be traced.

Usage:
    python -I tools/parity/export_parity_fixtures.py            # write fixtures
    python -I tools/parity/export_parity_fixtures.py --check    # exit 1 if committed file is stale
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sharpwr import aa_engine  # noqa: E402
from sharpwr.champion_database import level_stats  # noqa: E402
from sharpwr.champion_skill_data import SAMIRA_ABILITIES, samira_skill  # noqa: E402
from sharpwr.fight_engine import replay_samira  # noqa: E402

FIXTURE_VERSION = 1
OUT = ROOT / "game" / "parity" / "fixtures" / f"samira-reference-v{FIXTURE_VERSION}.json"
SOURCE_FILES = (
    "VERSION",
    "data/marksman_champion_stats.json",
    "sharpwr/aa_engine.py",
    "sharpwr/catalog.py",
    "sharpwr/champion_database.py",
    "sharpwr/champion_skill_data.py",
    "sharpwr/fight_engine.py",
)

# Tolerances the C# port must meet. Absolute HP for damage, absolute units for stats,
# absolute seconds for event times. The C# sim schedules on an integer-microsecond grid and
# rounds each attack period to it, so drift grows by <= 0.5 us per attack; 10 us over a
# six-second fight is far below one 33,333 us simulation tick.
# Long attack loops round each attack period to the microsecond grid, so drift grows with
# the attack count (measured up to 25 us over 52 attacks); 0.1 ms is ~0.3% of one tick.
TOLERANCE = {"stat": 1e-6, "multiplier": 1e-9, "damage": 1e-3, "time_seconds": 1e-5,
             "loop_time_seconds": 1e-4}


def fingerprint():
    def sha(rel):
        return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()

    try:
        head = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        head = None
    return {
        "damage_lab_version": (ROOT / "VERSION").read_text().strip(),
        "git_head_at_export": head,
        "source_sha256": {rel: sha(rel) for rel in SOURCE_FILES},
    }


def level_cases():
    cases = []
    for level in range(1, 16):
        ad = aa_engine.stats("Samira", level)
        core = level_stats("Samira", level)
        cases.append(
            {
                "level": level,
                "growth_units": aa_engine.gu(level),
                "base_ad": ad["basead"],
                "ad": ad["ad"],
                "as_ratio": ad["ratio"],
                "base_as": ad["baseas"],
                "base_bonus_as": ad["bba"],
                "level_bonus_as": ad["lvbas"],
                "hp": core["hp"],
                "mana": core["mana"],
                "armor": core["armor"],
                "mr": core["mr"],
                "movement_speed": core["movement_speed"],
                "attack_range": core["attack_range"],
            }
        )
    return {
        "engine_functions": ["sharpwr.aa_engine.stats", "sharpwr.champion_database.level_stats"],
        "data_status": "growth curve n*(0.7025+0.0175n) is the app curve; WR level audit open "
        "(docs/ingame-test-todo.md)",
        "cases": cases,
    }


def resistance_cases():
    values = (-60.0, -25.0, -1.0, 0.0, 1.0, 35.0, 50.5, 101.325, 250.0, 1000.0)
    pens = ((0.0, 0.0), (0.3, 0.0), (0.0, 18.0), (0.3, 18.0), (1.0, 0.0), (0.45, 200.0))
    cases = []
    for value in values:
        for pct, flat in pens:
            eff = aa_engine.effective_resistance(value, pct, flat)
            cases.append(
                {
                    "resistance": value,
                    "pct_pen": pct,
                    "flat_pen": flat,
                    "effective": eff,
                    "multiplier": aa_engine.rm(eff),
                }
            )
    return {
        "engine_functions": ["sharpwr.aa_engine.effective_resistance", "sharpwr.aa_engine.rm"],
        "cases": cases,
    }


def skill_cases():
    cases = []
    for slot, data in SAMIRA_ABILITIES.items():
        for rank in range(1, len(data["base"]) + 1):
            for base_ad, ad in ((60.0, 60.0), (88.0, 140.0), (109.0, 320.0)):
                for armor, mr in ((0.0, 0.0), (35.0, 30.0), (101.325, 48.571)):
                    for outcome, crit_chance in (("Normal", 0.0), ("Critical", 0.5)):
                        result = samira_skill(
                            slot,
                            rank,
                            ad,
                            crit_chance,
                            1.75,
                            armor,
                            outcome=outcome,
                            base_ad=base_ad,
                            mr=mr,
                        )
                        cases.append(
                            {
                                "slot": slot,
                                "rank": rank,
                                "base_ad": base_ad,
                                "ad": ad,
                                "armor": armor,
                                "mr": mr,
                                "outcome": outcome,
                                "crit_chance": crit_chance,
                                "crit_damage": 1.75,
                                "hits": result.hits,
                                "raw_per_hit": result.physical_per_hit
                                if slot != "E"
                                else result.magic / result.hits,
                                "dealt_physical": result.dealt_physical,
                                "dealt_magic": result.dealt_magic,
                                "dealt_total": result.total,
                            }
                        )
    return {
        "engine_functions": ["sharpwr.champion_skill_data.samira_skill"],
        "data_status": {
            slot: data.get("source", "") for slot, data in SAMIRA_ABILITIES.items()
        },
        "excluded": [
            "Passive melee bonus: interpolation is a user-accepted provisional model inside "
            "fight_engine.replay_samira; not exported as a standalone formula (v1).",
            "Expected-value crit outcome: the C# sim rolls crits with a seeded RNG; parity "
            "runs use Normal/Critical outcomes only.",
        ],
        "cases": cases,
    }


def timeline_cases():
    """Stationary-dummy AA cadence. Covers windup + ranged projectile travel + attack timer."""
    base = level_stats("Samira", 1)
    windup = 0.2279635167173252
    scenarios = []
    for name, level, attack_speed, distance in (
        ("level1_ranged_525", 1, 0.658, 525.0),
        ("level1_ranged_300", 1, 0.658, 300.0),
        ("level9_bonus_as", 9, 0.658 * (1 + 0.14 + 0.03 * aa_engine.gu(9)), 525.0),
    ):
        ad = aa_engine.stats("Samira", level)["ad"]
        result = replay_samira(
            [],
            level=level,
            ad=ad,
            attack_speed=attack_speed,
            crit_chance=0.0,
            crit_damage=1.75,
            hp=10_000.0,
            armor=0.0,
            q_rank=0,
            w_rank=0,
            e_rank=0,
            r_rank=0,
            use_e=False,
            automatic_until=6.0,
            timed_combat=True,
            aa_windup=windup,
            movement_speed=0.0,
            distance=distance,
            attack_range=float(base["attack_range"]),
        )
        scenarios.append(
            {
                "name": name,
                "inputs": {
                    "level": level,
                    "ad": ad,
                    "attack_speed": attack_speed,
                    "aa_windup_seconds": windup,
                    "starting_bonus_as": 0.0,
                    "distance": distance,
                    "projectile_speed": 2800.0,
                    "target_armor": 0.0,
                    "until_seconds": 6.0,
                },
                "impacts": [
                    {
                        "order": e["order"],
                        "time": e["time"],
                        "action": e["action"],
                        "damage": e["damage"],
                    }
                    for e in result.log
                ],
            }
        )
    return {
        "engine_functions": ["sharpwr.fight_engine.replay_samira(timed_combat=True)"],
        "data_status": "AA windup is the PC-derived provisional value "
        "(docs/samira-timed-combat.md V5.56); projectile speed PC reference",
        "scenarios": scenarios,
    }


def champion_loop_cases():
    """Level-derived AA loop until a dummy dies: stats, bonus-AS windup scaling, travel, armor.

    Mirrors how the game builds a champion from content: AS = base + ratio * (level bonus),
    windup = base_windup / (1 + 0.5 * bonus AS) (Damage Lab V5.56 formula).
    """
    stats = json.loads((ROOT / "data" / "marksman_champion_stats.json").read_text())
    samira = next(c for c in stats["champions"] if c["name"] == "Samira")["stats"]
    base_windup = samira["base_attack_windup_seconds"]
    scenarios = []
    for level, distance, hp, armor in ((1, 525.0, 1500.0, 50.0), (9, 400.0, 2000.0, 50.0),
                                       (15, 520.0, 2500.0, 120.0)):
        s = aa_engine.stats("Samira", level)
        bonus = s["bba"] + s["lvbas"]
        result = replay_samira(
            [], level=level, ad=s["ad"], attack_speed=s["baseas"], crit_chance=0.0,
            crit_damage=1.75, hp=hp, armor=armor, q_rank=0, w_rank=0, e_rank=0, r_rank=0,
            use_e=False, automatic_until=60.0, until_death=True, timed_combat=True,
            base_windup=base_windup, starting_bonus_as=bonus, movement_speed=0.0,
            distance=distance, attack_range=float(samira["attack_range"]),
        )
        scenarios.append({
            "name": f"samira_l{level}_d{int(distance)}",
            "inputs": {"level": level, "distance": distance, "dummy_hp": hp, "dummy_armor": armor,
                       "base_windup_seconds": base_windup, "windup_bonus_as_factor": 0.5},
            "derived": {"ad": s["ad"], "bonus_as": bonus,
                        "attack_speed": s["baseas"] + s["ratio"] * bonus},
            "killed_at": result.killed_at,
            "impacts": [{"time": e["time"], "action": e["action"], "damage": e["damage"],
                         "hp_after": e["hp_after"]} for e in result.log],
        })
    return {
        "engine_functions": ["sharpwr.fight_engine.replay_samira(timed_combat, until_death, "
                             "base_windup, starting_bonus_as)"],
        "data_status": "windup PC-provisional; growth curve app curve; AS formula "
                       "base + ratio*(bba+lvbas) from sharpwr/aa_engine.py",
        "scenarios": scenarios,
    }


def build():
    return {
        "schema": "sharpwr.parity-fixture/1",
        "fixture_version": FIXTURE_VERSION,
        "champion": "Samira",
        "ip_notice": "Riot Games reference data for private engine validation only; "
        "not shippable game content (docs/moba/10-legal-and-ip.md).",
        "fingerprint": fingerprint(),
        "tolerance": TOLERANCE,
        "level_stats": level_cases(),
        "resistance": resistance_cases(),
        "skills": skill_cases(),
        "timeline": timeline_cases(),
        "champion_loop": champion_loop_cases(),
    }


def serialize(data):
    return json.dumps(data, indent=1, sort_keys=True) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the committed file differs")
    args = parser.parse_args(argv)
    text = serialize(build())
    if args.check:
        current = OUT.read_text() if OUT.exists() else ""
        # git_head changes on every commit; compare everything else.
        a, b = json.loads(text), json.loads(current) if current else {}
        for d in (a, b):
            d.get("fingerprint", {}).pop("git_head_at_export", None)
        if a != b:
            print(f"{OUT.relative_to(ROOT)} is stale; re-run the exporter", file=sys.stderr)
            return 1
        print("parity fixtures up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    counts = {
        "level": len(json.loads(text)["level_stats"]["cases"]),
        "resistance": len(json.loads(text)["resistance"]["cases"]),
        "skills": len(json.loads(text)["skills"]["cases"]),
        "timeline_scenarios": len(json.loads(text)["timeline"]["scenarios"]),
        "champion_loops": len(json.loads(text)["champion_loop"]["scenarios"]),
    }
    print(f"wrote {OUT.relative_to(ROOT)} {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
