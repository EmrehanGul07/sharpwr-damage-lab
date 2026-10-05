"""Refresh the local engine dependency graph once per deployed app revision."""
import importlib
import sys
import threading

_lock = threading.RLock()
_loaded_revision = None
_MODULES = (
    'sharpwr.combat_validation', 'sharpwr.champion_database', 'sharpwr.rune_database', 'sharpwr.rune_runtime',
    'sharpwr.champion_skill_data', 'sharpwr.marksman_ability_database', 'sharpwr.damage_classification',
    'sharpwr.combat_timing', 'sharpwr.marksman_state', 'sharpwr.marksman_damage_components', 'sharpwr.marksman_kits',
    'sharpwr.marksman_fight_engine', 'sharpwr.fight_engine',
    'sharpwr.catalog', 'sharpwr.aa_engine', 'sharpwr.targets', 'sharpwr',
    'sharpwr.build_fight_optimizer',
    'marksman_art', 'combat_replay', 'sharpwr.core_items', 'sharpwr.item_consensus',
)

def ensure_engine_revision(revision):
    global _loaded_revision
    with _lock:
        if _loaded_revision == revision:
            return
        importlib.invalidate_caches()
        for name in _MODULES:
            if name in sys.modules:
                importlib.reload(sys.modules[name])
            else:
                importlib.import_module(name)
        _loaded_revision = revision
