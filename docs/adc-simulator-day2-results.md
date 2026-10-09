# Day 2 implementation

## Presentation

- Original melee/caster minions replace capsule proxies: faction armor, visor, shield/blade or staff/orb, articulated legs and arms. Animation uses distance-based gait and the actual lane attack timestamp; idle units do not cycle their feet.
- Five shared geometries and nine shared materials serve successive waves. Removed units leave the actor pool; leaving lane mode releases actor references.
- Champion locomotion turns use the shortest angular arc and a 55 ms smoothing constant. Casts snap to the requested direction rather than inherit a delayed walk turn. Existing skeletal entry/exit blends remain intact.
- Jinx minigun, rocket AA, W and R have separate silhouettes. Ezreal E displays its landing-origin bolt in addition to blink bursts. Projectile bodies stay on their frozen, flat launch line.
- Enemy effects honor actual impact positions, including selected minions. AA range lines, full skillshot range and movement endpoints preserve the previous control rules.
- Stone/rock use subtle bump detail from existing terrain maps; tint reduces the washed-out look. High-quality anisotropy is eight; lightweight modes use two.

## Decision and runtime quality

- Tower aggro on the bot forces retreat even when friendly minions are inside tower range.
- Skillshot-angle sidesteps check delayed visible tower positions before choosing a direction.
- Cast/hit observation keys expire after their visible lifetime; learned cooldown knowledge remains. Stats, reaction delays and human movement mechanics are unchanged.
- New regression coverage includes articulated actor poses and shared resources, angle-wrap continuity, distinct gravity-free pilot VFX, tower aggro under cover and eight full three-minute lane runs across both champions and four difficulties.
- Browser regression budgets: at most 64 lane actors, five shared actor geometries, ten actor materials, fewer than 1500 renderer calls and 800 resident geometries. These are regression ceilings, not measured hardware FPS promises.

## Limits

This completes the planned two-day improvement milestone, not the complete Wild Rift simulator. Minions are original procedural articulated meshes, not imported Riot characters. Existing Jinx trap envelope/arming proxies, ultimate flight-damage curve, assist passive rules and full item interactions remain explicitly unresolved in the Day 1 audit. No build or champion statistics were changed to make visuals or bot difficulty appear stronger.
