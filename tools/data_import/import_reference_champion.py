"""Migrate one Damage Lab champion into the game's content format (docs/moba/02-data-migration.md).

Read-only with respect to the Damage Lab. Every number keeps its provenance; anything the
Damage Lab does not know is written as `null` with status `unresolved` — never filled in.

Output: game/content/reference-riot/champions/<slug>.champion.json
This is Riot reference data for private validation. It is excluded from player builds
(docs/moba/10-legal-and-ip.md) and must never be listed in a shippable roster.

Usage: python -I tools/data_import/import_reference_champion.py Samira [--check]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sharpwr.champion_skill_data import SAMIRA_ABILITIES  # noqa: E402

OUT_DIR = ROOT / "game" / "content" / "reference-riot" / "champions"
STATS = ROOT / "data" / "marksman_champion_stats.json"
GEOMETRY = ROOT / "data" / "marksman-skill-geometry.json"
PC_REF = ROOT / "docs" / "samira-mechanics-reference.json"

SUPPORTED = {"Samira": SAMIRA_ABILITIES}
# Values the Damage Lab preserves from user-supplied WR evidence (evidence keys D0xx); not
# re-verified by this migration. Only explicit user WR confirmations get "wr_verified_user".
USER_SOURCED = "damage_lab_user_sourced"


def num(value) -> str | None:
    """Decimal text for Fix64.Parse. repr() is the shortest round-trip form of a float."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError(value)
    return repr(float(value)) if isinstance(value, float) else str(value)


def field(value, status, source, note=None):
    out = {"value": num(value), "status": status if value is not None else "unresolved",
           "source": source}
    if note:
        out["note"] = note
    return out


def stat_status(source_entry):
    if source_entry == "existing_user_preserved":
        return "damage_lab_preserved", "data/marksman_champion_stats.json (existing_user_preserved)"
    if isinstance(source_entry, dict) and "url" in source_entry:
        return "wr_wiki", f"{source_entry['url']}#{source_entry.get('parameter', '')}"
    return "unresolved", "data/marksman_champion_stats.json"


def champion_stats(name):
    record = next(c for c in json.loads(STATS.read_text())["champions"] if c["name"] == name)
    stats, sources = record["stats"], record.get("field_sources", {})
    mapping = {
        "base_ad": "base_ad", "ad_per_level": "ad_growth", "base_hp": "base_hp",
        "hp_per_level": "hp_growth", "base_mana": "base_mana", "mana_per_level": "mana_growth",
        "base_armor": "base_armor", "armor_per_level": "armor_growth", "base_mr": "base_mr",
        "mr_per_level": "mr_growth", "hp_regen_per_5s": "base_hp_regen_per_5s",
        "hp_regen_per_5s_per_level": "hp_regen_growth_per_5s",
        "mana_regen_per_5s": "base_mana_regen_per_5s",
        "mana_regen_per_5s_per_level": "mana_regen_growth_per_5s",
        "movement_speed": "movement_speed", "attack_range": "attack_range",
        "base_attack_speed": "base_as", "attack_speed_ratio": "as_ratio",
        "bonus_attack_speed_level1": "base_bonus_as", "bonus_attack_speed_per_level": "as_growth",
        "attack_projectile_speed": "attack_projectile_speed",
        "gameplay_radius": "gameplay_radius",
    }
    out = {}
    for key, src in mapping.items():
        status, source = stat_status(sources.get(src, "existing_user_preserved"))
        out[key] = field(stats.get(src), status, source)
    out["attack_windup_seconds"] = field(
        stats.get("base_attack_windup_seconds"), "pc_reference_provisional",
        "docs/samira-timed-combat.md V5.56 (PC windup/baseAS quotient, user-authorized fallback)")
    out["attack_windup_bonus_as_factor"] = field(
        0.5, "damage_lab_preserved",
        "sharpwr/combat_timing.py attack_windup: base / (1 + 0.5*bonusAS) "
        "(WR Patch 2.2 formula per docs/samira-timed-combat.md V5.56; WR applicability unverified)")
    out["level_growth_curve"] = {
        "value": "damage_lab_quadratic", "status": "damage_lab_preserved",
        "source": "sharpwr/aa_engine.py gu(): n*(0.7025+0.0175n); WR level audit open",
    }
    return out


def ability(slot, data, geometry, pc):
    src = data.get("source", "")
    def ranks(values, status, source):
        return [field(v, status, source) for v in values]
    out = {
        "name": data["name"],
        "damage_type": "magic" if slot == "E" else "physical",
        "base_damage_by_rank": ranks(data["base"], USER_SOURCED, f"champion_skill_data.py {src}"),
        "total_ad_ratio": field(data.get("total_ad", 0.0), USER_SOURCED, src),
        "bonus_ad_ratio": field(data.get("bonus_ad", 0.0), USER_SOURCED, src),
        "hits": data["hits"],
        "crit_effectiveness": field(data["crit_effectiveness"], USER_SOURCED, src),
        "cooldown_by_rank": ranks(data["cooldown"], USER_SOURCED, src),
        "mana_cost": field(data["mana"], "wr_verified_user", data.get("mana_source", src)),
        "cast_time_seconds": field(pc.get("cast_time_seconds"), "pc_reference_provisional",
                                   "docs/samira-mechanics-reference.json"),
        "projectile_speed": field(pc.get("projectile_speed"), "pc_reference_provisional",
                                  "docs/samira-mechanics-reference.json"),
        "geometry": {
            "shape": geometry.get("shape"),
            "range": field((geometry.get("range") or [None])[0],
                           "wr_wiki" if geometry.get("status") == "database" else "unresolved",
                           geometry.get("source", "")),
            "width": field((geometry.get("width") or [None])[0],
                           "wr_wiki" if geometry.get("status") == "database" else "unresolved",
                           geometry.get("source", "")),
            "radius": field((geometry.get("radius") or [None])[0],
                            "wr_wiki" if geometry.get("radius") else "unresolved",
                            geometry.get("source", "")),
        },
    }
    if "required_resource" in data:
        out["required_resource"] = data["required_resource"]
    return out


def build(name):
    if name not in SUPPORTED:
        raise SystemExit(f"{name}: no Damage Lab ability table to import yet")
    geometry = json.loads(GEOMETRY.read_text())["champions"][name]["slots"]
    pc = json.loads(PC_REF.read_text())
    abilities = {slot: ability(slot, data, geometry.get(slot, {}), pc.get(slot, {}))
                 for slot, data in SUPPORTED[name].items()}
    return {
        "schema": "sharpwr.champion/1",
        "id": f"ref.{name.lower()}",
        "display_name": name,
        "ip": "riot-reference",
        "shippable": False,
        "stats": champion_stats(name),
        "abilities": abilities,
        "passive": {
            "name": "Daredevil Impulse",
            "status": "unsupported",
            "note": "Style stacks and melee bonus damage use a provisional user-accepted "
                    "interpolation inside fight_engine.replay_samira; not migrated in v1.",
        },
        "unsupported_mechanics": [
            "P: Style grades, melee bonus damage interpolation, immobilized-target assist attack",
            "Q: melee cone variant, E-Q explosives",
            "W: projectile destruction, R-ends-W rule",
            "R: exact WR shot offsets (fixture uses even spacing), ability-haste rule",
            "Collision/gameplay radius (unknown in source data)",
        ],
        "open_questions_source": "docs/ingame-test-todo.md (Samira row)",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("champion")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    out = OUT_DIR / f"{args.champion.lower()}.champion.json"
    text = json.dumps(build(args.champion), indent=1, ensure_ascii=False) + "\n"
    if args.check:
        ok = out.exists() and out.read_text() == text
        print("content up to date" if ok else f"{out} is stale", file=sys.stdout if ok else sys.stderr)
        return 0 if ok else 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
