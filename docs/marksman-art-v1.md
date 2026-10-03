# SharpWR marksman character art — 1.0

The Animation Studio contains 23 original stylized character interpretations, 184 animation clips and 92 authored active-ability effects. Build Lab controls, gameplay calculations and the published tier list are unchanged.

## Included

- Distinct silhouettes, clothing, hairstyles and equipment for the 23 database marksmen.
- Human, yordle, creature, dragon and aircraft rigs; articulated limbs, fingers, jaws, wings, cloth, hair and tails where applicable.
- Eight clips per champion: Idle, Walk, AA, passive demonstration, Q, W, E and R. Walk is an in-place locomotion cycle; Corki uses aircraft locomotion.
- PBR materials, dramatic three-light stage, shadows, orbit/zoom, three camera views, quality settings and a training target.
- Deterministic pooled spell geometry and billboard particles. Effects are separate runtime code because glTF does not carry this particle system.
- All 23 binary glTF assets, independently reimported after export. Human assets include a weighted deforming cloth panel; much of the stylized geometry is rigidly attached to the joint hierarchy.

## Timing and scope

These are original procedural art studies, not extracted Riot meshes, production Wild Rift animation files or AAA sculpted assets. Animation Studio uses authored demonstration durations. The recorded-replay adapter uses captured windup, cast and channel windows plus launch/impact timestamps; it does not infer damage, collision, cooldowns, persistent status durations or unrecorded interactions. Geometry and lateral movement remain illustrative.

Passive demonstrations visualize identity rather than reproducing every stack-dependent gameplay state. A complete gameplay presentation still needs dedicated transitions for death, hit reaction, reload, sustained buffs, skin variants and adversarial combat interruptions. Those are outside the eight-clip package and must not be represented as completed.

## Source and export

`data/marksman-art-direction.json` is the authored visual catalogue. `assets/marksman-3d/rig.js`, `effects.js` and `scene.js` are the shared runtime. `studio.html` is the review interface, and `replay.js` adapts engine traces without changing simulation.

Run `npm ci`, `npm run test:art`, and `npm run export:art`. The exporter generates `assets/marksman-3d/models/*.glb` and `data/marksman-3d-assets.json`, reimports each GLB and verifies eight clips. Assets can be imported into Blender, Godot or other glTF-capable tools. They need further sculpting, retopology, texture authoring and animation polish before a claim of game-production or AAA readiness.

## Verification

Automated checks cover all 23 rigs, 184 clips, 1,288 finite/repeatable bone poses, 828 effect frames, idle/walk loop closure and export/reimport. Python checks require an exact match with the marksman database, intact exported file sizes and channel timestamps sourced from captured traces. Combat tests protect damage/TTK and Ezreal's W arrival/detonation separation. Visual review is recorded separately; mathematical tests do not establish visual quality.
