"""Refresh the local engine dependency graph once per deployed app revision."""
import importlib
import sys
import threading

_lock = threading.RLock()
_loaded_revision = None
_MODULES = (
    'combat_validation', 'champion_database', 'rune_database', 'rune_runtime', 'champion_skill_data',
    'marksman_ability_database', 'damage_classification', 'combat_timing',
    'marksman_state', 'marksman_damage_components', 'marksman_kits',
    'marksman_fight_engine', 'fight_engine', 'build_fight_optimizer',
    'marksman_art', 'combat_replay', 'core_items', 'item_consensus',
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
