"""Build one SharpWR v2 marksman study in Blender (bpy): model, rig, clips, renders and GLB.

Usage: python build.py CHAMPION_ID OUT_DIR [options]
  --render front,side,...   still views (core.VIEWS)
  --clips all|Idle,AA,...   author clips
  --video all|Idle,...      render clip frames to OUT_DIR/frames/<clip>/
  --sheet Clip:frame,...    stills of clip frames (OUT_DIR/sheet_<i>.png)
  --export NAME.glb         export rig, meshes and clips (parts merged, --budget triangles)
  --preview NAME.glb        lighter export after --export (--preview_budget triangles)
  --stats                   print triangle counts
  --root_motion             let clips move the root (preview videos; the app owns root motion)
  --samples N --width W --height H --threads T --fast
Runs with Blender's Python module (pip bpy 4.5).
"""

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core  # noqa: E402


def parse(argv):
    champion, out = argv[0], Path(argv[1])
    opts = {}
    rest = argv[2:]
    i = 0
    while i < len(rest):
        key = rest[i].lstrip("-")
        if i + 1 < len(rest) and not rest[i + 1].startswith("--"):
            opts[key] = rest[i + 1]
            i += 2
        else:
            opts[key] = True
            i += 1
    return champion, out, opts


def main():
    champion, out, opts = parse(sys.argv[1:])
    out.mkdir(parents=True, exist_ok=True)
    spec = importlib.import_module(f"champions.{champion.replace('-', '_')}")
    core.new_scene()
    core.OPTIONS.update(opts)
    spec.build()
    scale = getattr(spec, "VIEW_SCALE", 1.0)
    camera = core.stage(rim=getattr(spec, "RIM", (1.0, 0.45, 0.85)), height=scale)
    core.configure_render(opts, getattr(spec, "EXPOSURE", 0.0))
    actions = {}
    if opts.get("clips"):
        wanted = None if opts["clips"] == "all" else opts["clips"].split(",")
        actions = core.build_clips(wanted)
    if "Idle" in actions:  # stills in the idle stance
        core.rig.animation_data.action = actions["Idle"]
        core.scene.frame_set(0)
    for view in (opts.get("render") or "").split(","):
        if view:
            core.shoot(camera, out / f"{view}.png", core.VIEWS[view], scale)
    if opts.get("video"):
        names = list(actions) if opts["video"] == "all" else opts["video"].split(",")
        views = getattr(spec, "CLIP_VIEWS", {})
        for name in names:
            core.render_clip(camera, actions, name, out, views.get(name, core.CLIP_VIEW), scale=scale)
    if opts.get("sheet"):
        for i, item in enumerate(opts["sheet"].split(",")):
            name, frame = item.split(":")
            core.rig.animation_data.action = actions[name]
            core.scene.frame_set(int(frame))
            core.shoot(camera, out / f"sheet_{i:02d}.png", core.CLIP_VIEW, scale)
    if opts.get("stats"):
        core.stats("built")
    if opts.get("export") or opts.get("preview"):
        core.drop_fx()
    if opts.get("export"):
        core.merge_parts()
        core.reduce_to(int(opts.get("budget", 36000)))
        core.stats("export")
        core.export_glb(out / opts["export"], actions)
    if opts.get("preview"):
        core.reduce_to(int(opts.get("preview_budget", 9000)), keep=())
        core.stats("preview")
        core.export_glb(out / opts["preview"], actions)


if __name__ == "__main__":
    main()
