# Ezreal Blender study v2

This is an original stylized character study, not an extracted Wild Rift asset or a claim of final game fidelity. The other 22 champions still use the original procedural rigs.

The study contains a continuous weighted body, 17 deform bones, facial features, swept hair, forehead goggles, jacket panels, trousers, boots and a left-hand arcane gauntlet. Eight authored, baked clips cover Idle, Walk, AA, P and Q/W/E/R. The exported mesh uses 13 material batches. Root movement stays in the fight/replay presentation layer; spell effects follow the gauntlet socket.

Animation Studio selects the study for Ezreal on WebGL when **Ezreal Blender v2** is enabled and quality is High or Balanced. Lightweight and software SVG rendering retain the base rig. The study adapter supports deterministic seeking, looping locomotion and duplicated champions through cloned skeletons.

Download the GLB or editable Blender archive below the Studio. The archive includes the `.blend`, GLB, manifest and reproducible authoring script. Rebuild using Blender 4.5.14 LTS:

```sh
blender --background --threads 4 --python scripts/build_ezreal_study.py
node tests/test_blender_study.cjs
```

The script produces four review renders under `docs/art-review`, exports/reimports eight clips, and records its SHA256 in the study manifest. CI rebuilds the study when this source changes.

Validation covers normalized skin weights, bounded material batches, finite transforms, deterministic seek restoration, forward gauntlet extension and socket attachment. Existing art/fight tests remain in place.

Remaining art work includes facial sculpt refinement, hair/cloth topology, texture painting, hand articulation, foot-contact polish, transition blending and closer champion-specific reference matching. Q/W/E visual studies are baked at 30 fps; their GLB clip length is 28 frames (0.9333s), while the Studio scales their playback to the authored 0.95s demonstration window. Hardware WebGL visual review remains necessary; software browser tests cannot validate GPU skinning or shader appearance.
