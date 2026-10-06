"""Export the v2 marksman studies for the web Animation Studio.

Driver (plain Python):
  python scripts/marksman_v2/export_studio.py [--jobs N] [--blender PATH] [--only id,id]
  Runs one Blender process per champion (this interpreter with the pip `bpy` module, or a
  Blender binary with --blender), then writes static/marksman-3d/manifest.json and the
  download package build/release/sharpwr-skinned-roster-v8.zip.
Worker (inside bpy / Blender):
  export_studio.py --one CHAMPION_ID
  Builds the study with every clip, saves the editable .blend, keeps the eight studio clips
  (Idle, Walk, AA, P, Q, W, E, R; no root travel, the app owns movement), drops the preview
  effects and exports character.glb (full) and preview.glb (CPU skinning budget), a review
  render and the champion manifest.
"""

import json
import subprocess
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_art_sources import roster_digest  # noqa: E402

OUT = ROOT / "static/marksman-3d"  # runtime GLBs + manifests, served by the app
SOURCES = ROOT / "build/roster"  # editable .blend files, published as a release asset
RELEASE = ROOT / "build/release"
LOGS = ROOT / "build/roster-logs"
REVIEW = ROOT / "docs/art-review/roster-v8"
CATALOGUE = ROOT / "data/marksman-art-direction.json"
STUDIO_CLIPS = ["Idle", "Walk", "AA", "P", "Q", "W", "E", "R"]
STUDIO_SCALE = 1.34  # v2 studies are authored at real proportions (Jinx 1.72 m); the studio stage expects the v1 size (2.3)
FULL_BUDGET = 30000
PREVIEW_BUDGET = 8000
EMISSION_CAP = 1.0
STATUS = "original authored stylized asset; not extracted Wild Rift game art"


def catalogue():
    return json.loads(CATALOGUE.read_text())["champions"]


def studio_durations(p):
    """Playback lengths the studio uses (the GLB clips are mapped onto them by progress)."""
    return {"Idle": 3, "Walk": 1.2, "AA": p["attack"]["study_duration"], "P": p["passive"]["study_duration"], **{s: a["study_duration"] for s, a in p["skills"].items()}}


# ---------------------------------------------------------------- worker


def worker(cid):
    import importlib

    import bpy

    sys.path.insert(0, str(HERE))
    import core

    name, p = next((n, p) for n, p in catalogue().items() if p["id"] == cid)
    spec = importlib.import_module(f"champions.{cid.replace('-', '_')}")
    core.new_scene()
    spec.build()
    actions = core.build_clips()
    missing = [c for c in STUDIO_CLIPS if c not in actions]
    if missing:
        raise SystemExit(f"{cid}: missing studio clips {missing}")

    # Review still (idle, three-quarter view) before anything is trimmed.
    scale = getattr(spec, "VIEW_SCALE", 1.0)
    camera = core.stage(rim=getattr(spec, "RIM", (1.0, 0.45, 0.85)), height=scale)
    core.configure_render({"samples": 12, "width": 420, "height": 500, "threads": 2}, getattr(spec, "EXPOSURE", 0.0))
    core.rig.animation_data.action = actions["Idle"]
    core.scene.frame_set(0)
    REVIEW.mkdir(parents=True, exist_ok=True)
    core.shoot(camera, REVIEW / f"{cid}.png", core.VIEWS["three_quarter"], scale)

    # The editable source keeps every clip and the preview effects.
    (SOURCES / cid).mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCES / cid / "source.blend"), compress=True)

    for clip_name in list(actions):
        if clip_name not in STUDIO_CLIPS:
            bpy.data.actions.remove(actions.pop(clip_name))
    for o in list(bpy.data.objects):  # stage objects are not part of the character
        if o != core.rig and o.parent is None:
            bpy.data.objects.remove(o, do_unlink=True)
    core.drop_fx()
    for material in bpy.data.materials:  # the studio adds bloom: keep glows (eyes, acid sacs) from blowing out
        bsdf = material.node_tree.nodes.get("Principled BSDF") if material.use_nodes else None
        if bsdf and bsdf.inputs["Emission Strength"].default_value > EMISSION_CAP:
            bsdf.inputs["Emission Strength"].default_value = EMISSION_CAP
    core.reduce_to(FULL_BUDGET)
    core.skin_parts()
    core.prune_bones()
    core.rig.scale = (STUDIO_SCALE,) * 3
    directory = OUT / cid
    directory.mkdir(parents=True, exist_ok=True)
    full = core.stats("export")
    core.export_glb(directory / "character.glb", actions)
    core.reduce_to(PREVIEW_BUDGET, keep=())
    preview = core.stats("preview")
    core.export_glb(directory / "preview.glb", actions)
    meshes = [o for o in core.rig.children_recursive if o.type == "MESH"]
    record = {
        "champion": name,
        "id": cid,
        "bones": len(core.rig.data.bones),
        "animations": studio_durations(p),
        "full_triangles": full,
        "preview_triangles": preview,
        "materials": len({m.name for o in meshes for m in o.data.materials if m}),
        "silhouette": p["art_brief"],
        "weapon": p.get("weapon"),
        "source": f"scripts/marksman_v2/champions/{cid.replace('-', '_')}.py",
        "source_sha256": roster_digest(),
        "status": STATUS,
    }
    (directory / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    print("ROSTER_READY", cid, flush=True)


# ---------------------------------------------------------------- driver


def run_one(cid, blender):
    script = str(Path(__file__).resolve())
    if blender:
        cmd = [blender, "--background", "--python", script, "--", "--one", cid]
    else:
        cmd = [sys.executable, script, "--one", cid]
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / f"{cid}.log"
    with log.open("w") as handle:
        code = subprocess.run(cmd, stdout=handle, stderr=subprocess.STDOUT).returncode
    ok = code == 0 and "ROSTER_READY" in log.read_text()
    print(("OK   " if ok else "FAIL ") + cid, flush=True)
    return cid, ok


def package(records):
    RELEASE.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(RELEASE / "sharpwr-skinned-roster-v8.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for source in sorted(HERE.rglob("*")):
            if source.suffix in (".py", ".sh") and "__pycache__" not in source.parts:
                archive.write(source, "scripts/" + str(source.relative_to(HERE)))
        for cid in sorted(r["id"] for r in records.values()):
            for file in [*sorted((OUT / cid).iterdir()), SOURCES / cid / "source.blend"]:
                if file.suffix in (".glb", ".blend", ".json") and file.exists():
                    archive.write(file, cid + "/" + file.name)


def main(args):
    jobs, blender, only = 2, None, None
    i = 0
    while i < len(args):
        if args[i] == "--jobs":
            jobs = int(args[i + 1])
        elif args[i] == "--blender":
            blender = args[i + 1]
        elif args[i] == "--only":
            only = args[i + 1].split(",")
        i += 2
    cat = catalogue()
    ids = [p["id"] for p in cat.values()]
    selected = [cid for cid in ids if not only or cid in only]
    with ThreadPoolExecutor(jobs) as pool:
        results = list(pool.map(lambda cid: run_one(cid, blender), selected))
    failed = [cid for cid, ok in results if not ok]
    if failed:
        raise SystemExit(f"export failed for {failed}; see {LOGS}")
    if set(selected) == set(ids):
        records = {name: json.loads((OUT / p["id"] / "manifest.json").read_text()) for name, p in cat.items()}
        (OUT / "manifest.json").write_text(json.dumps({"schema": 2, "source_sha256": roster_digest(), "champions": records}, indent=2) + "\n")
        package(records)
        print("SKINNED_ROSTER_COMPLETE", len(records), flush=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if argv[:1] == ["--one"]:
        worker(argv[1])
    else:
        main(argv)
