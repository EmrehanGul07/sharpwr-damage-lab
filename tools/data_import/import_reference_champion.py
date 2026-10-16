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
from sharpwr.fight_engine import SAMIRA_SKILL_ORDER  # noqa: E402

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


PC = "docs/samira-mechanics-reference.json (PC reference; user-authorized provisional for WR)"
ENGINE = "sharpwr/fight_engine.py replay_samira timed_combat"


def samira_kit():
    """Mechanics the Damage Lab timed model uses, each with provenance. Read from the reference
    JSON where present; values that exist only as Damage Lab code constants cite that code."""
    pc = json.loads(PC_REF.read_text())
    lab = "damage_lab_preserved"
    prov = "pc_reference_provisional"
    return {
        "hook": "samira",
        "style": {
            "max_stacks": field(6, lab, ENGINE + ": style = min(6, style + 1)"),
            "expiry_seconds": field(pc["P"]["style_duration_seconds"], prov, PC),
            "gain": "AA/Q/W/E hit whose action differs from the previous Style action "
                    "(Damage Lab rule); R hits never grant Style",
            "reset": "at R channel end (Damage Lab WR engine; PC says end of effect)",
        },
        "passive_melee_bonus": {
            "formula": "(level + 5 + (0.05 + 0.008*level) * AD) * (1 + missing_hp / max_hp), magic",
            "level_flat": field(5, lab, ENGINE + " passive (user-accepted provisional interpolation)"),
            "ad_ratio_base": field(0.05, lab, ENGINE + " passive (user-accepted provisional interpolation)"),
            "ad_ratio_per_level": field(0.008, lab, ENGINE + " passive (user-accepted provisional interpolation)"),
            "applies_to": "W hits, E hit, melee AA (target within melee_attack_range), Q slash; never R",
        },
        "melee_attack_range": field(pc["P"]["blade_attack_edge_range"], prov, PC + " blade AA edge range"),
        "q": {
            "cast_seconds": field(pc["Q"]["cast_time_seconds"], prov, PC),
            "projectile_speed": field(pc["Q"]["projectile_speed"], prov, PC),
            "slash_range": field(pc["Q"]["target_edge_range"], prov, PC + " melee cone trigger"),
        },
        "w": {
            "cast_seconds": field(pc["W"]["cast_time_seconds"], prov, PC),
            "hit_offsets_seconds": [field(v, prov, PC) for v in pc["W"]["hit_times_relative_seconds"]],
            "radius": field(pc["W"]["edge_effect_radius"], prov, PC),
            "blocks": ["AA", "Q"],
        },
        "e": {
            "target_range": field(pc["E"]["center_target_range"], prov, PC),
            "dash_distance": field(650, "wr_wiki", "data/marksman-skill-geometry.json Samira E movement_range"),
            "dash_speed": field(pc["E"]["dash_speed"], prov, PC),
            "hit_width": field(pc["E"]["edge_width"], prov,
                               PC + " edge width; Damage Lab E impact limit 250 (fight_engine.py)"),
            "attack_speed_by_rank": [field(v, lab, ENGINE + " attack_stats E bonus") for v in (0.25, 0.30, 0.35, 0.40)],
            "attack_speed_seconds": field(pc["E"]["WR_AS_buff_duration_preserved_seconds"], "wr_verified_user",
                                          PC + " WR 3 s duration preserved by user"),
        },
        "r": {
            "required_style": field(6, "wr_verified_user", "sharpwr/champion_skill_data.py R required_resource"),
            "radius": field(pc["R"]["center_effect_radius"], prov, PC),
            "channel_seconds": field(pc["R"]["channel_duration_seconds"], prov, PC),
            "shot_window_seconds": field(pc["R"]["shot_window_seconds"], prov, PC),
            "shots": field(pc["R"]["max_shots_per_target"], prov, PC),
            "shot_spacing": "even across the window (Damage Lab assumption; exact WR offsets unknown)",
            "projectile_speed": field(2800, lab, ENGINE + " R tick travel gap/2800"),
            "blocks": ["AA", "Q", "W"],
            "ends_w": True,
        },
    }


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
            "note": "Style and melee bonus in kit.style / kit.passive_melee_bonus (provisional).",
        },
        "skill_order": {
            "order": "".join(SAMIRA_SKILL_ORDER),
            "source": "sharpwr/fight_engine.py SAMIRA_SKILL_ORDER (Damage Lab default leveling)",
        },
        "kit": samira_kit(),
        "unsupported_mechanics": [
            "P: Style movement speed bonus; immobilized-target assist attack",
            "P: melee bonus damage uses a provisional interpolation (labelled, see kit)",
            "Q: melee cone geometry (slash hits the nearest enemy in slash_range); E-Q explosives",
            "W: projectile destruction",
            "AA: attack timer under mid-cycle attack-speed changes (timer fixed at attack start)",
            "W cast during E dash: rejected (Damage Lab buffers it to dash end)",
            "Q collision is evaluated at release against current positions (no swept dodge)",
            "Walking positions update at tick end; mid-tick events see tick-start positions (dashes exact)",
            "Crits: no crit chance without items (M3); crit rolls not implemented",
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
