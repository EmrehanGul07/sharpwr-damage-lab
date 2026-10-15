---
paths:
  - "game/unity/**"
  - "game/packages/com.sharpwr.acceptance/**"
---
# Unity presentation rules

- Presentation reads simulation snapshots and emits commands. It never decides damage, hits,
  cooldown readiness, deaths or positions; it may *display* predicted values.
- Rendering runs at device frame rate and interpolates between the last two sim states using
  `alpha = accumulator / tickDuration`; never move gameplay objects with physics or animation
  root motion.
- Input layer: touch (joystick, skill buttons with drag-aim and cancel zone) and desktop
  (right-click move/attack, QWER with cursor aim, A-move) map to the same command types.
- Isometric camera: fixed pitch/yaw from config; follow with damping; no gameplay logic in camera.
- Assets: Riot-derived art (existing SharpWR fan models, icons) only under
  `Assets/SharpWR/Reference/` (personal build). Other art: original or licensed, recorded in
  `Assets/SharpWR/Art/LICENSES.md`. The guard hook blocks Riot art elsewhere.
- Use the Input System, URP and Addressables; no `Resources/` for content.
- Zero per-frame allocations in hot paths (health bars, damage numbers pooled).
- PlayMode/EditMode tests for input mapping, camera math and interpolation.
