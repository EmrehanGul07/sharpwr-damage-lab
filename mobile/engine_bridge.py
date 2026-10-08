"""Offline mobile boundary; uses the audited engine without a second fight implementation."""
import json
import math
from sharpwr import engine_namespace
from sharpwr.build_fight_optimizer import BuildFightEvaluator
from sharpwr.rune_pages import DEFAULT_PAGES, rune_loadout
from combat_replay import replay_payload


def mobile_fight(request):
    build = request["build"]
    target = request["target"]
    champion, level = build["champion"], build["level"]
    settings = request.get("settings", {})
    overrides = {}
    rotation = settings.get("rotation", "auto")
    if rotation != "auto":
        if rotation not in ("QWE", "QEW", "WQE", "WEQ", "EQW", "EWQ"):
            raise ValueError("Invalid skill priority")
        overrides["skill_priority"] = tuple(rotation)
    movement = settings.get("movement", "auto")
    if movement != "auto":
        if movement not in ("skill_envelope", "aa_envelope", "close_envelope"):
            raise ValueError("Invalid movement policy")
        overrides["movement_policy"] = movement
    ultimate = settings.get("ultimate", "immediate")
    if ultimate not in ("immediate", "after_basics"):
        raise ValueError("Invalid ultimate timing")
    overrides["ultimate_policy"] = ultimate
    if settings.get("distance") is not None:
        distance = settings["distance"]
        if not isinstance(distance, (int, float)) or not math.isfinite(distance) or not 0 <= distance <= 2500:
            raise ValueError("Starting distance must be between 0 and 2500")
        overrides["distance"] = distance
    runes = rune_loadout(DEFAULT_PAGES[champion], level) if build.get("runes") else None
    evaluator = BuildFightEvaluator(
        engine_namespace(), champion, level, target["health"], target["armor"], target["magicResist"],
        mist=build.get("mist", 0), bonus_hp=target.get("bonusHealth", 0),
        aa_reduction=target.get("attackReduction", 0), energized=True,
        yuntal_stacks=build.get("yuntalStacks", 0), runes=runes, simulation_overrides=overrides,
    )
    row = evaluator.evaluate(build["items"], build.get("boots"))
    # Overrides are applied by the engine after its default policy labels are built.
    # Record the actual requested policy so replay_row reruns exactly that fight.
    row = dict(row)
    if "skill_priority" in overrides:
        row["Rotation"] = " → ".join(overrides["skill_priority"])
    if "movement_policy" in overrides:
        row["Movement"] = overrides["movement_policy"]
    row["Ultimate timing"] = ultimate
    trace = evaluator.replay_row(row)
    payload = replay_payload(trace, champion=champion, level=level, target="Custom target",
                             hp=target["health"], build=row)
    payload["source"] = "build_lab"
    # Surviving targets have infinite ranking TTK, represented as null at the JSON boundary.
    def clean(value):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        if isinstance(value, dict):
            return {key: clean(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [clean(item) for item in value]
        return value
    return json.dumps(clean({"summary": row, "replay": payload}), allow_nan=False)
