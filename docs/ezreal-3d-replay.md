# Ezreal 3D combat replay — V5.83.0

Three.js 0.169.0 presents the same immutable replay payload as the original 2D renderer. Procedural models, tiled arena, lighting, shadows, range ring, gait, cast poses and Q/W/E/R/AA effects are illustrative. Camera drag/zoom does not affect engine geometry. Recorded radial distance and kite arc project into world space; no damage, cooldown or movement decisions are computed by the renderer.

The existing play, pause, speed, seek and event-step controls drive both renderers. Projectile launch/arrival come from recorded command timestamps. Ezreal W records its scheduled non-damaging mark arrival separately from W detonation, and its gold marker lasts until recorded detonation or the engine's four-second expiry. E portals follow recorded positions; current movement endpoint proxies remain engine assumptions rather than independently measured WR endpoints.

The level-15 preview is a recorded 6,000 HP / 100 armor / 100 MR training fight using Muramana, Trinity Force, Botrk, Navori, LDR and Armorcrusher Boots. It is explicitly labeled as an example, not a ranking winner. Actual search winners continue to generate their own traces. Other champions retain the original renderer. If WebGL is unavailable, SVGRenderer presents the same 3D geometry with simpler lighting and no shadows. If CDN loading or both renderers fail, the original 2D replay stays available. Three.js runs entirely in the component iframe.

Engine change is metadata only: Ezreal command `impact_time` equals the unchanged event queue arrival. Existing core item fingerprints are migrated to reflect that source change without altering numerical results. Tests verify W mark timing differs from detonation and total damage/TTK match the evaluator.
