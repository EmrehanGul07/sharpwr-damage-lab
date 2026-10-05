"""Damage type and source tags are orthogonal. Unknown WR tags stay unknown.

This registry describes interactions, not replacement damage coefficients.
PC taxonomy supplies vocabulary; only WR evidence may mark a spell BasicAttack.
"""

import json
from functools import lru_cache
from pathlib import Path

TAGS = frozenset(
    (
        "BasicAttack",
        "ActiveSpell",
        "AOE",
        "Periodic",
        "Proc",
        "Indirect",
        "Pet",
        "Item",
        "NonRedirectable",
        "DoesNotAggroJungle",
        "OnHit",
        "Augment",
    )
)
PROPERTIES = frozenset(
    (
        "ApplyAttackRatio",
        "ApplyCritical",
        "ApplyDamageModifier",
        "ApplyLifesteal",
        "ApplyOmnivamp",
        "ApplyPhysicalVamp",
        "ApplySpellvamp",
        "EnableCallForHelp",
        "EnableKill",
        "RespectDodge",
        "RespectImmunity",
        "TriggerDamageEvents",
        "TriggerOnHitEvents",
    )
)


@lru_cache(maxsize=1)
def registry():
    return json.loads(
        (Path(__file__).resolve().parents[1] / "data/damage-classification.json").read_text()
    )


def ability_profile(champion, slot):
    return registry()["abilities"][champion][slot]


def event_profile(champion, action):
    if action == "Galeforce active":
        return {"tags": ["Item", "ActiveSpell"], "status": "item_active_origin", "properties": {}}
    if action == "Phantom on-hit":
        return {"tags": ["OnHit"], "status": "unknown_WR", "properties": {}}
    if action == "Plasma detonation" and champion == "Kai'Sa":
        return ability_profile(champion, "P")
    if action.startswith("AA"):
        return {
            "tags": ["BasicAttack"],
            "status": "fundamental_basic_attack",
            "properties": {"TriggerOnHitEvents": True, "ApplyLifesteal": True},
            "component": "attack base; additions require their own classification",
        }
    if action == "Burn tick" and champion == "Smolder":
        return (
            ability_profile(champion, "Q")
            .get("variants", {})
            .get("burn", {"tags": [], "status": "unknown_WR"})
        )
    if action in ("Poison tick", "Venom tick") and champion == "Twitch":
        return ability_profile(champion, "P")
    if action and action[0] in "QWER":
        return ability_profile(champion, action[0])
    return {"tags": [], "status": "unknown_WR", "properties": {}}


def magnification(distance, tags):
    """User-confirmed distance model; eligibility requires explicit basic damage."""
    if "BasicAttack" not in tags:
        return 1.0
    d = max(0.0, float(distance or 0.0))
    return 1.0 + (0.0 if d < 100 else min(0.10, (int((d - 100) // 50) + 1) * 0.01))


def ability_magnification(champion, action, distance, enabled=True):
    return magnification(distance, event_profile(champion, action)["tags"]) if enabled else 1.0


def component_profile(champion, slot, variant=None):
    profile = ability_profile(champion, slot)
    return profile.get("variants", {}).get(variant, profile) if variant else profile


def annotate_raw(champion, slot, damage):
    """Separate simultaneous physical/magic/true damage instances for audit."""
    p = ability_profile(champion, slot)
    result = []
    for kind, value in (
        ("physical", damage.physical),
        ("magic", damage.magic),
        ("true", damage.true),
    ):
        if value == 0:
            continue
        component = p
        result.append(
            dict(
                damage_type=kind,
                raw_amount=value,
                tags=list(component["tags"]),
                classification_status=component["status"],
                source=component.get("source"),
                properties=dict(component.get("properties", {})),
            )
        )
    return result
