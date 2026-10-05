# Skinned roster V7

All 23 database marksmen have original stylized skinned models, editable Blender sources, full GLBs and lightweight previews. Each has Idle, Walk, AA, P, Q, W, E and R clips (184 clips total). These are original preview assets, not Riot assets or a claim of final Wild Rift visual fidelity.

Practice indicators use a dedicated geometry catalogue derived from the existing Wild Rift database, at 100 game units per world unit. Range and movement distance are separate. Blink/dash indicators show the landing point and respect arena boundaries. Champion level and ability rank can be selected. Hold or focus a skill button to inspect its indicator.

Missing or ambiguous distances are marked unverified instead of substituting PC League values. Examples include Vayne Q, Tristana W, Caitlyn recoil distance and Kai’Sa R maximum cast range. Global abilities display a finite visible guide labeled GLOBAL. Recorded fights retain their presentation choreography; Practice uses geometry-aware movement. Build Lab and combat calculations are unchanged.

Rebuild with scripts/build_marksman_roster.py using Blender. Runtime GLBs are written to static/marksman-3d; editable .blend sources and the download package go to build/ and are published by CI to the art-sources GitHub release, after model/animation validation.
