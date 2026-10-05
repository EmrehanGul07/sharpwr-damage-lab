"""SharpWR damage engine, independent of any user interface.

- catalog: champion AA stats (C), completed items (F), components (P), boots (B)
- aa_engine: level formulas and the shared multi-item AA hit kernel (combat_hits)
- targets: user-tested benchmark target profiles

engine_namespace() returns the name -> object mapping that the build optimizer
(BuildFightEvaluator) and the tests take as their engine.
"""

from .catalog import B, C, F, K, P, dct
from .aa_engine import (
    combat_hits,
    effective_resistance,
    gu,
    lvl_scale,
    rm,
    sim,
    sim_build,
    stats,
    validate_build,
)
from .targets import (
    BRUISER_DARIUS_PROFILE,
    SQUISHY_JINX_PROFILE,
    TANK_ORNN_PROFILE,
    TARGET_PROFILES,
    benchmark_target,
    profiles_by_target,
    target_profile_at_level,
)

ENGINE_NAMES = (
    "B",
    "C",
    "F",
    "K",
    "P",
    "dct",
    "combat_hits",
    "effective_resistance",
    "gu",
    "lvl_scale",
    "rm",
    "sim",
    "sim_build",
    "stats",
    "validate_build",
    "BRUISER_DARIUS_PROFILE",
    "SQUISHY_JINX_PROFILE",
    "TANK_ORNN_PROFILE",
    "TARGET_PROFILES",
    "benchmark_target",
    "target_profile_at_level",
)


def engine_namespace():
    """A fresh dict of every engine name, for code that takes an engine namespace."""
    return {name: globals()[name] for name in ENGINE_NAMES}
