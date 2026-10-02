# Ezreal arcane replay — 5.85.0

Original procedural effects with separate silhouettes for AA bolts, Q arrows, orbiting gold W rings and persistent target sigils, E portal shards and homing bolts, and a filled R crescent. Cast charge appears on the articulated gauntlet. Impact flashes and radial shards use recorded damage events. R visually continues past the target without extra damage.

Simulation values, launch/impact times, item calculations and ranking are unchanged. SVG fallback uses the same pooled geometry. Software playback throttle now uses wall-clock time, preserving smooth slow-motion playback.

Validation: JavaScript syntax, replay event ordering tests and 14 replay/core/UI Python tests passed.
