# Skinned roster V8

All 23 database marksmen have original stylized models built in Blender from the v2 studies in `scripts/marksman_v2` (one script per champion in `champions/`, on the shared toolkit `core.py`). Each study sculpts its model (metaball bodies, hair clumps, cloth panels, weapons), rigs it (a human skeleton with leg IK, or a free-form creature rig for Kog'Maw and Smolder), and hand-keys its clips: Idle, Walk, AA, P, Q, W, E, R, plus Recall and Death in the editable source. Spring chains add follow-through to hair, capes, scarves and tails. These are original preview assets, not Riot assets or a claim of final Wild Rift visual fidelity.

The Animation Studio loads `static/marksman-3d/<id>/character.glb` (full model, about 30k triangles) or `preview.glb` (about 8k triangles, for software rendering). For the app each model is one skinned mesh (rigid parts are weighted to their bone), helper bones are removed, the preview effect meshes are dropped (the app draws its own effects), dashes stay in place (the app owns movement) and the eight studio clips are kept. `socket_muzzle` marks where projectiles start. The studio plays each clip over its authored demonstration duration from `data/marksman-art-direction.json`.

Practice indicators use a dedicated geometry catalogue derived from the existing Wild Rift database, at 100 game units per world unit. Range and movement distance are separate. Blink/dash indicators show the landing point and respect arena boundaries. Champion level and ability rank can be selected. Hold or focus a skill button to inspect its indicator.

Missing or ambiguous distances are marked unverified instead of substituting PC League values. Examples include Vayne Q, Tristana W, Caitlyn recoil distance and Kai’Sa R maximum cast range. Global abilities display a finite visible guide labeled GLOBAL. Recorded fights retain their presentation choreography; Practice uses geometry-aware movement. Build Lab and combat calculations are unchanged.

## Rebuilding

```
python scripts/marksman_v2/export_studio.py --jobs 2                     # with the pip bpy module
python scripts/marksman_v2/export_studio.py --blender /path/to/blender --jobs 4
```

This writes the GLBs and manifests to `static/marksman-3d`, review renders to `docs/art-review/roster-v8`, and the editable `.blend` files and download package (`sharpwr-skinned-roster-v8.zip`) to `build/`. The roster manifest records a signature of the v2 sources; when they change, the art workflow rebuilds the roster with Blender, validates every model and clip, publishes the package to the `art-sources` release and commits the regenerated assets.

Preview videos of every clip (with root motion and effects) come from `scripts/marksman_v2/make_video.sh`.
