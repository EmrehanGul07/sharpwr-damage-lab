# Ezreal 3D replay V2 — V5.84.0

V2 improves presentation only. Numerical combat rules, build rankings and saved core results are unchanged.

- Procedural articulated model: jacket/scarf, goggles/hair, shoulder plates, gauntlet, segmented legs and elbows. Walking is driven by recorded displacement. AA windup and Q/W/E/R cast poses use recorded command/lock windows.
- Cyan Q trail, gold W mark/shatter, violet E portals and segmented crescent R wave. Effect dimensions remain illustrative.
- Duel and Follow frame recorded positions; Tactical uses a steeper fixed angle. Orbit, wheel zoom and Reset camera remain available.
- Optional movement trail samples the recorded path over 1.6 seconds. Range remains the recorded AA range.
- Hero mana snapshot, target HP, action banner, skill cooldowns, labeled damage numbers and item/passive stacks.
- Focus view hides event panels/timeline without changing playback. Loop restarts the same trace. Space toggles playback; arrow keys step events, while inputs keep their normal keyboard behavior.
- Equal-time event stepping respects the selected order for HP, mana, cooldowns, W marker and damage effects. A W detonation after an AA at the same timestamp does not appear before that event is selected.
- Effect geometry is shared and pooled; paused scenes skip redundant rendering. SVG fallback draws at up to 24 playback frames per second without changing simulation time. WebGL uses the existing lighting/shadow renderer.

Validation: Python replay/UI/cache tests; Node pure trace-reader tests for same-time ordering, W arrival, consumption, expiry and reapplication; live preview/controls inspection. 3D models and projected lateral movement remain representations, not captured WR footage.
