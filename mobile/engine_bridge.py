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
    runes = rune_loadout(DEFAULT_PAGES[champion], level) if build.get("runes") else None
    evaluator = BuildFightEvaluator(
        engine_namespace(), champion, level, target["health"], target["armor"], target["magicResist"],
        mist=build.get("mist", 0), bonus_hp=target.get("bonusHealth", 0),
        aa_reduction=target.get("attackReduction", 0), energized=True,
        yuntal_stacks=build.get("yuntalStacks", 0), runes=runes,
    )
    row = evaluator.evaluate(build["items"], build.get("boots"))
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
