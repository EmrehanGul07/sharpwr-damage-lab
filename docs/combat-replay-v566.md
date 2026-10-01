# Combat replay — v5.66.0

The item tier list now records its #1 full build and embeds an interactive replay directly below the Top 3. A new search is needed for a previously cached result.

## Controls and recorded data

Play/pause, 0.25×–2× speed, timeline seeking, previous/next event, and clickable event markers support inspecting the fight. The inspector exposes event IDs, commands versus impacts, damage, target HP, mana snapshots, stacks, cooldowns, and item effects. The trace can be downloaded as JSON.

Motion capture runs only for the winning replay, not every candidate. It records distance, kite arc, attack range and action locks. AA projectiles use recorded launch/impact times. Q projectile visuals represent recorded cast-to-impact intervals. W and R lock states appear in the arena. All damage and resource numbers come from the engine trace; the renderer does not simulate damage.

The replay is matched against the selected winner's damage and TTK before display. A mismatch reports an error while retaining the build rankings.

## Scope

This is a representative 2D debug replay, not Wild Rift footage. Lateral kite coordinates are projected from recorded distance and kite arc. Unit sizes and visual effects are illustrative. The engine's existing proxy data, unknown mechanics and in-game TODOs still apply. First release supports the #1 build; video export and arbitrary build selection are not implemented.

## Validation

All 23 marksmen reproduce the ranked damage and TTK with motion capture. Refined Samira, Xayah and Jinx winners also reproduce their selected policy results. Automated tests check event ordering, trace agreement and safe HTML embedding. 178 automated tests passed. JavaScript controls were exercised with DOM/canvas stubs: playback, pause, event stepping, seek, final HP and reset passed. Visual browser QA remains pending: this workspace has no browser binary and its browser download returned a truncated archive.
