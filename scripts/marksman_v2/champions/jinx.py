"""Jinx: an original stylized interpretation (twin braids, Pow-Pow, Fishbones, Zapper, Chompers)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import (
    J,
    M,
    X90,
    ball,
    ball_mesh,
    box,
    chain,
    clip,
    cone,
    cyl,
    fk_arm,
    flash,
    ik,
    join,
    loc,
    material,
    metaball_object,
    mesh_from_meta,
    place,
    placement,
    plate,
    rest_matrix,
    rot,
    size,
    sphere,
    striped,
    tube,
    unpart,
    weapon_matrix,
)

RIM = (1.0, 0.45, 0.85)
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.4, height=1.5, target_z=0.55)}


def materials():
    M.update(
        skin=material("Pale skin", (0.62, 0.43, 0.38), rough=0.5, sss=0.25),
        top=material("Black crop top", (0.018, 0.018, 0.024), rough=0.55),
        shorts=material("Plum shorts", (0.16, 0.035, 0.12), rough=0.6),
        stocking=striped("Pink and black stocking", (0.9, 0.12, 0.42), (0.02, 0.02, 0.025)),
        boot=material("Dark boot leather", (0.035, 0.03, 0.04), rough=0.42),
        glove=material("Fingerless glove", (0.03, 0.03, 0.035), rough=0.5),
        hair=material("Electric blue hair", (0.03, 0.30, 0.85), rough=0.4),
        hair_dark=material("Deep blue hair", (0.015, 0.12, 0.45), rough=0.45),
        pink=material("Hot pink", (0.95, 0.10, 0.45), rough=0.4),
        metal=material("Gun metal", (0.18, 0.19, 0.22), rough=0.3, metal=0.9),
        brass=material("Brass", (0.75, 0.52, 0.18), rough=0.3, metal=1.0),
        rocket=material("Fishbones teal", (0.10, 0.36, 0.42), rough=0.45),
        rocket_dark=material("Fishbones shadow", (0.04, 0.12, 0.15), rough=0.5),
        mouth=material("Shark mouth", (0.45, 0.04, 0.06), rough=0.5),
        tooth=material("Shark teeth", (0.93, 0.92, 0.86), rough=0.35),
        gun_pink=material("Pow-Pow pink", (0.85, 0.18, 0.50), rough=0.38, metal=0.2),
        gun_purple=material("Pow-Pow purple", (0.22, 0.08, 0.35), rough=0.4, metal=0.2),
        glow=material("Spark cyan", (0.2, 0.85, 1.0), emission=6.0),
    )
    C.face_materials(iris=(0.95, 0.15, 0.55), lash=(0.01, 0.01, 0.015))


def build_body():
    meta = metaball_object("Jinx body")
    # Torso: hips, buttocks, waist, ribcage, chest, bust, shoulder line.
    ball(meta, (0, 0.004, 0.95), 0.13, (1.0, 0.70, 0.62))
    for sx in (1, -1):
        ball(meta, (0.058 * sx, 0.045, 0.915), 0.07, (1.0, 0.95, 1.05))
    ball(meta, (0, 0.006, 1.05), 0.10, (1.0, 0.76, 0.8))
    ball(meta, (0, 0.006, 1.12), 0.093, (1.0, 0.78, 0.8))
    ball(meta, (0, 0.004, 1.21), 0.118, (1.0, 0.76, 0.9))
    ball(meta, (0, 0.010, 1.30), 0.13, (1.0, 0.66, 0.6))
    for sx in (1, -1):
        ball(meta, (0.052 * sx, -0.045, 1.255), 0.05, (1.0, 0.95, 0.92))
        ball(meta, (0.11 * sx, 0.012, 1.345), 0.05, (1.25, 0.8, 0.6))
    C.limbs(meta)
    cuts = [((0, 0, z), (0, 0, 1)) for z in (0.215, 0.80, 1.035, 1.165, 1.335)]
    cuts += [((0.19 * sx, 0, 0), (1, 0, 0)) for sx in (1, -1)]
    cuts += [C.arm_cut(side, 0.80) for side in ("L", "R")]

    def region(c):
        x, y, z = c
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            return "glove" if C.arm_fraction(c, side) > 0.80 else "skin"
        if z < 0.215:
            return "boot"
        if 1.165 < z < 1.335 and abs(x) < 0.19:
            return "top"
        if 0.80 < z < 1.035:
            return "shorts"
        if x > 0.02 and z < 0.80:
            return "stocking"
        return "skin"

    return C.body_mesh(meta, "Jinx body", region, ["skin", "top", "shorts", "stocking", "boot", "glove"], cuts)


def braid(sx):
    """A long braid: alternating twisted lobes along a falling path, with a pink tie."""
    H = C.HEAD
    path = [
        H + Vector((0.062 * sx, 0.055, 0.085)),
        H + Vector((0.135 * sx, 0.11, 0.07)),
        H + Vector((0.18 * sx, 0.15, -0.10)),
        Vector((0.20 * sx, 0.17, 1.18)),
        Vector((0.21 * sx, 0.19, 0.86)),
        Vector((0.21 * sx, 0.20, 0.55)),
    ]
    pts = C.catmull(path)
    lobes = []
    for i in range(2, len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        mid = (a + b) / 2
        frac = i / len(pts)
        r = 0.034 * (1 - 0.55 * frac)
        quat = (b - a).normalized().to_track_quat("Z", "Y")
        obj = sphere("Braid lobe", mid, (r * 0.85, r * 0.65, (b - a).length * 1.25), "hair" if i % 2 else "hair_dark", False, segments=12, rings=8)
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = quat @ Matrix.Rotation(math.radians(38 if i % 2 else -38), 4, "Y").to_quaternion()
        lobes.append(obj)
    sphere("Hair tie", path[1] + Vector((-0.01 * sx, 0.0, 0.0)), (0.03, 0.03, 0.022), "pink")
    lobes.append(sphere("Braid tip", path[-1] + Vector((0, 0, -0.04)), (0.016, 0.016, 0.05), "hair", False))
    return path, lobes


def build_hair():
    h = C.HEAD
    C.hair_cap("Jinx hair cap", "hair")
    # Bangs: side-swept tapered strands over the forehead.
    for i, x in enumerate((-0.07, -0.045, -0.02, 0.005, 0.03, 0.055, 0.075)):
        root = h + Vector((x * 0.6, -0.045, 0.098))
        tip = h + Vector((x + 0.018, -0.098, 0.018 - abs(x) * 0.25))
        mid = root.lerp(tip, 0.5) + Vector((0, -0.03, 0.01))
        tube(f"Bang {i}", [root, mid, tip], 0.011, "hair" if i % 2 else "hair_dark", taper=[1.0, 0.9, 0.12])
    for i in range(14):
        a = math.radians(-150 + i * (300 / 13))
        root = h + Vector((0.0, 0.03, 0.118))
        side = Vector((math.sin(a) * 0.112, math.cos(a) * 0.105 + 0.03, 0.02))
        tip = h + Vector((math.sin(a) * 0.104, math.cos(a) * 0.098 + 0.03, -0.075 if abs(math.sin(a)) > 0.6 else -0.035))
        tube(f"Strand {i}", [root, h + side + Vector((0, 0, 0.055)), tip], 0.014, "hair" if i % 2 else "hair_dark", taper=[0.7, 1.0, 0.2])
    for sx in (1, -1):
        root = h + Vector((0.075 * sx, -0.045, 0.06))
        tube("Side lock", [root, h + Vector((0.09 * sx, -0.06, -0.02)), h + Vector((0.085 * sx, -0.055, -0.11))], 0.012, "hair", taper=[1.0, 0.8, 0.15])
    return [braid(1), braid(-1)]


def build_powpow():
    """Pow-Pow, the minigun: grip at the origin, barrels toward -Y."""
    parts = [
        box("Housing", "gun_pink", (0.11, 0.30, 0.12), (0, -0.06, 0.03), 0.02),
        box("Housing stripe", "gun_purple", (0.114, 0.10, 0.124), (0, -0.04, 0.03), 0.015),
        cyl("Drum", "gun_purple", 0.075, 0.06, (0.0, 0.0, -0.06), (0, math.pi / 2, 0)),
        cyl("Drum rim", "gun_pink", 0.078, 0.02, (0.0, 0.0, -0.06), (0, math.pi / 2, 0)),
        cyl("Grip", "dark", 0.016, 0.11, (0, 0.06, -0.02), (0.35, 0, 0)),
        cyl("Front ring", "metal", 0.048, 0.03, (0, -0.24, 0.03), X90),
        cyl("Back ring", "gun_purple", 0.05, 0.025, (0, -0.205, 0.03), X90),
        tube("Carry handle", [Vector((0, 0.02, 0.09)), Vector((0, -0.06, 0.15)), Vector((0, -0.14, 0.09))], 0.009, "metal", False),
    ]
    for i in range(7):  # painted teeth on the housing's front
        parts.append(cone("Tooth", "tooth", 0.007, 0.0, 0.016, (-0.042 + i * 0.014, -0.208, -0.0), (math.pi, 0, 0), 3))
    for sx in (1, -1):
        parts.append(ball_mesh("Gun eye", "white", (0.057 * sx, -0.15, 0.06), (0.004, 0.018, 0.018)))
        parts.append(ball_mesh("Gun pupil", "dark", (0.06 * sx, -0.152, 0.06), (0.003, 0.009, 0.009)))
    housing = join(parts, "Pow-Pow")
    barrels = [cyl("Barrel", "metal", 0.011, 0.34, (math.cos(a) * 0.03, -0.38, 0.03 + math.sin(a) * 0.03), X90, 12) for a in (i * math.pi / 3 for i in range(6))]
    barrels.append(cyl("Muzzle ring", "metal", 0.046, 0.02, (0, -0.535, 0.03), X90))
    barrels.append(cyl("Spindle", "dark", 0.012, 0.36, (0, -0.38, 0.03), X90, 12))
    return housing, join(barrels, "Pow-Pow barrels")


def build_fishbones():
    """Fishbones, the shark rocket launcher: grip at the origin, mouth toward -Y."""
    meta = metaball_object("Fishbones body", resolution=0.01)
    ball(meta, (0, -0.15, 0.10), 0.13, (1.0, 3.6, 1.05))
    ball(meta, (0, -0.42, 0.10), 0.12, (1.05, 1.4, 1.0))
    ball(meta, (0, 0.22, 0.10), 0.07, (1.0, 1.6, 1.0))
    body = mesh_from_meta(meta, "Fishbones", voxel=0.008, smooth=3, tris=5000)
    body.data.materials.append(M["rocket"])
    body.data.materials.append(M["rocket_dark"])
    for poly in body.data.polygons:
        poly.material_index = 1 if poly.center.z > 0.155 else 0
    parts = [body, ball_mesh("Shark mouth", "mouth", (0, -0.60, 0.09), (0.085, 0.05, 0.075))]
    for i in range(12):  # two rows of teeth around the mouth
        a = math.pi * (0.1 + 0.8 * (i % 6) / 5)
        upper = i < 6
        z = 0.09 + (0.035 if upper else -0.04) + (math.sin(a) - 0.6) * 0.012 * (1 if upper else -1)
        parts.append(cone("Fang", "tooth", 0.011, 0.0, 0.03, (math.cos(a) * 0.07, -0.625, z), (0 if upper else math.pi, 0, 0), 4))
    for sx in (1, -1):
        parts.append(ball_mesh("Shark eye", "white", (0.088 * sx, -0.47, 0.15), (0.014, 0.024, 0.024)))
        parts.append(ball_mesh("Shark pupil", "dark", (0.098 * sx, -0.475, 0.15), (0.006, 0.012, 0.014)))
    parts.append(plate("Dorsal fin", "rocket_dark", [(0, -0.12, 0.2), (0, 0.10, 0.2), (0, 0.06, 0.34)], 0.02, 0.0))
    for sx in (1, -1):
        parts.append(plate("Side fin", "rocket_dark", [(0.10 * sx, -0.30, 0.05), (0.10 * sx, -0.14, 0.05), (0.22 * sx, -0.10, -0.02)], 0.016, 0.0))
        parts.append(plate("Tail fin", "rocket_dark", [(0, 0.30, 0.10), (0, 0.42, 0.10), (0.13 * sx, 0.50, 0.10 + 0.10 * sx)], 0.016, 0.0))
    parts.append(cyl("Exhaust", "metal", 0.05, 0.08, (0, 0.33, 0.10), X90))
    parts.append(cyl("Exhaust glow", "glow", 0.032, 0.085, (0, 0.335, 0.10), X90))
    parts.append(cyl("Grip", "dark", 0.016, 0.12, (0, 0.0, -0.03), (0.3, 0, 0)))
    parts.append(box("Shoulder pad", "pink", (0.09, 0.16, 0.03), (0, 0.06, -0.025), 0.01))
    return join(parts, "Fishbones")


def build_zapper():
    parts = [
        box("Zapper body", "gun_purple", (0.04, 0.14, 0.05), (0, -0.05, 0.03), 0.008),
        cyl("Zapper barrel", "metal", 0.012, 0.08, (0, -0.15, 0.035), X90, 12),
        cyl("Zapper grip", "dark", 0.013, 0.08, (0, 0.0, -0.02), (0.3, 0, 0), 12),
        ball_mesh("Zapper coil", "glow", (0, -0.20, 0.035), (0.016, 0.016, 0.016)),
    ]
    return join(parts, "Zapper")


def build_chomper():
    parts = [
        ball_mesh("Chomper top", "gun_purple", (0, 0, 0.035), (0.055, 0.05, 0.03)),
        ball_mesh("Chomper base", "gun_pink", (0, 0, 0.012), (0.06, 0.055, 0.02)),
        ball_mesh("Chomper eye", "glow", (0, -0.045, 0.045), (0.012, 0.008, 0.008)),
    ]
    for i in range(8):
        a = i / 8 * 2 * math.pi
        parts.append(cone("Chomper tooth", "tooth", 0.008, 0.0, 0.02, (math.cos(a) * 0.05, math.sin(a) * 0.045, 0.028), (0, 0, 0), 4))
    return join(parts, "Flame Chomper")


def build_flash(name, radius, mat="glow"):
    parts = [ball_mesh(name, mat, (0, 0, 0), (radius, radius * 1.8, radius))]
    for i in range(4):
        parts.append(cone("Spike", mat, radius * 0.35, 0.0, radius * 3.2, (0, -radius * 1.4, 0), (math.pi / 2, i * math.pi / 4, 0), 4))
    return join(parts, name)


def build_belts():
    parts = []
    for tilt, z in ((0.20, 0.965), (-0.20, 0.945)):
        parts.append(C.torus("Belt", "boot", 0.165, 0.011, (0, 0.004, z), (0, tilt, 0), (1.0, 0.70, 1.0)))
        for i in range(16):
            a = i / 16 * 2 * math.pi
            x, y = math.cos(a) * 0.168, math.sin(a) * 0.168 * 0.70 + 0.004
            parts.append(cyl("Cartridge", "brass", 0.006, 0.03, (x, y, z + math.sin(tilt) * -x), (0, 0, 0), 8))
    return join(parts, "Ammo belts")


# Rest placements: Pow-Pow held at the right hip, Fishbones strapped across the back, Zapper
# holstered on the left hip. Animations move the weapon bones from here.
HOLD_POWPOW = Matrix.Translation((-0.24, -0.10, 0.97)) @ Matrix.Rotation(math.radians(-8), 4, "X")
BACK_FISHBONES = Matrix.Translation((0.03, 0.21, 0.98)) @ Matrix.Rotation(math.radians(-28), 4, "Y") @ Matrix.Rotation(math.radians(-48), 4, "X")
HOLSTER_ZAPPER = Matrix.Translation((0.16, 0.02, 0.88)) @ Matrix.Rotation(math.radians(80), 4, "X")
FLASHES = {
    "flash_powpow": (HOLD_POWPOW @ Matrix.Translation((0, -0.58, 0.03)), "powpow_barrels"),
    "flash_fishbones": (BACK_FISHBONES @ Matrix.Translation((0, -0.68, 0.09)), "fishbones"),
    "flash_exhaust": (BACK_FISHBONES @ Matrix.Translation((0, 0.42, 0.10)), "fishbones"),
    "flash_zap": (HOLSTER_ZAPPER @ Matrix.Translation((0, -0.23, 0.035)), "zapper"),
}


def build():
    C.make_joints()
    materials()
    body = build_body()
    C.build_head("Jinx head")
    C.build_face(brow_mat="hair_dark")
    braids = build_hair()
    powpow, barrels = build_powpow()
    fishbones = build_fishbones()
    zapper = build_zapper()
    belts = build_belts()
    chompers = [build_chomper() for _ in range(3)]
    for i, c in enumerate(chompers):
        place(c, Matrix.Translation((-0.25 + 0.25 * i, -0.9, 0.0)))
    flashes = {
        "flash_powpow": build_flash("Pow-Pow flash", 0.04),
        "flash_fishbones": build_flash("Fishbones flash", 0.09),
        "flash_exhaust": build_flash("Fishbones exhaust", 0.07),
        "flash_zap": build_flash("Zap flash", 0.03),
    }
    for obj in (powpow, barrels):
        place(obj, HOLD_POWPOW)
    place(fishbones, BACK_FISHBONES)
    place(zapper, HOLSTER_ZAPPER)
    for name, obj in flashes.items():
        m = FLASHES[name][0] @ (Matrix.Rotation(math.pi, 4, "Z") if name == "flash_exhaust" else Matrix())
        place(obj, m)

    grip_powpow = HOLD_POWPOW @ Vector((0, 0.06, -0.02))
    support_powpow = HOLD_POWPOW @ Vector((0, -0.215, -0.02))
    barrel_axis = HOLD_POWPOW @ Vector((0, -0.38, 0.03))
    grip_fishbones = BACK_FISHBONES @ Vector((0, 0.0, -0.03))
    support_fishbones = BACK_FISHBONES @ Vector((0, -0.30, -0.01))
    fwd = Vector((0, -1, 0))
    zap = HOLSTER_ZAPPER.to_translation()
    extra = [
        C.weapon_bones("powpow", HOLD_POWPOW, (0, 0.06, -0.02), "hips", 0.2),
        ("powpow_barrels", barrel_axis, barrel_axis + (HOLD_POWPOW.to_3x3() @ fwd) * 0.15, "powpow"),
        C.weapon_bones("fishbones", BACK_FISHBONES, (0, 0.0, -0.03), "chest", 0.25),
        C.weapon_bones("zapper", HOLSTER_ZAPPER, (0, 0, 0), "hips", 0.1),
        C.grip_bone("grip_zapper.L", zap, "zapper"),
    ]
    for i in range(3):
        co = Vector((-0.25 + 0.25 * i, -0.9, 0.0))
        extra.append((f"chomper.{i}", co, co + Vector((0, 0.08, 0)), "root"))
    for name, (m, parent) in FLASHES.items():
        extra.append(C.point_bone(name, m, parent))
    for name, co, parent in (
        ("grip_powpow.R", grip_powpow, "powpow"),
        ("grip_powpow.L", support_powpow, "powpow"),
        ("grip_fishbones.R", grip_fishbones, "fishbones"),
        ("grip_fishbones.L", support_fishbones, "fishbones"),
    ):
        extra.append(C.grip_bone(name, co, parent))
    chains = [(f"braid.{side}", C.resample(path[1:], 8), "head", {}) for side, (path, _) in zip(("L", "R"), braids)]
    arm_iks = []
    for side in ("L", "R"):
        arm_iks += [(side, "powpow", f"grip_powpow.{side}"), (side, "fishbones", f"grip_fishbones.{side}")]
    arm_iks.append(("L", "zapper", "grip_zapper.L"))
    C.SOCKETS["socket_muzzle"] = ("powpow_barrels", FLASHES["flash_powpow"][0])
    C.build_rig("Jinx rig", chains, extra, arm_iks)
    C.bind(body)
    for side, (_, lobes) in zip(("L", "R"), braids):
        for obj in lobes:
            C.attach_to_chain(obj, f"braid.{side}")
    for obj, bone in ((powpow, "powpow"), (barrels, "powpow_barrels"), (fishbones, "fishbones"), (zapper, "zapper"), (belts, "hips")):
        C.attach(obj, bone)
    for i, c in enumerate(chompers):
        C.attach(c, f"chomper.{i}")
    for name, obj in flashes.items():
        C.attach(obj, name)
    define_clips()


# ---------------------------------------------------------------- clips (24 fps)
# Anticipation before every action, overshoot and settle after it, arcs for hands and weapons,
# offset timing (hips lead, chest and head follow); the braids follow through (core springs).


def define_clips():
    shoulder_fishbones = placement("fishbones", (-0.20, -0.02, 1.29), rx=4, rz=-4)
    shoulder_fishbones_up = placement("fishbones", (-0.20, 0.0, 1.31), rx=16, rz=-4)
    stowed_powpow = placement("powpow", (0.05, 0.19, 1.03), rx=62, ry=20, rz=180)
    aim_zapper = placement("zapper", (0.20, -0.42, 1.27), rx=0, rz=8)

    def flashes_off(frame):
        for f in FLASHES:
            size(f, frame, 0.0)

    def chompers_hidden(frame):
        for i in range(3):
            size(f"chomper.{i}", frame, 0.0)

    def spin(frame_from, frame_to, turns):
        """Spin Pow-Pow's barrels around their own axis: spin up, full speed, spin down."""
        pb = C.PB["powpow_barrels"]
        pb.rotation_mode = "XYZ"
        for f, share in ((frame_from, 0.0), (frame_from + 3, 0.08), (frame_to - 3, 0.88), (frame_to, 1.0)):
            pb.rotation_euler = (0, turns * 2 * math.pi * share, 0)
            pb.keyframe_insert("rotation_euler", frame=f)

    def barrels_still(frame):
        pb = C.PB["powpow_barrels"]
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0, 0, 0)
        pb.keyframe_insert("rotation_euler", frame=frame)

    def hold_weapons(frame, mode="powpow"):
        """Keys every weapon bone at its placement for a mode: powpow (rest) or fishbones."""
        if mode == "powpow":
            for b in ("powpow", "fishbones"):
                loc(b, frame)
                rot(b, frame)
        else:
            weapon_matrix("powpow", stowed_powpow, frame)
            weapon_matrix("fishbones", shoulder_fishbones, frame)
        loc("zapper", frame)
        rot("zapper", frame)
        if frame == 0:
            barrels_still(0)
        for side in ("L", "R"):
            ik(side, "powpow", frame, 1.0 if mode == "powpow" else 0.0)
            ik(side, "fishbones", frame, 1.0 if mode == "fishbones" else 0.0)
        ik("L", "zapper", frame, 0.0)

    def body_hold(frame, breath=0.0, sway=0.0):
        """The Pow-Pow stance with a breathing/sway amount in -1..1."""
        loc("hips", frame, x=0.01 - 0.012 * sway, z=-0.035 - 0.006 * breath)
        rot("hips", frame, z=8 - 3 * sway)
        rot("spine", frame, x=4 + 1.2 * breath, z=-6 + sway)
        rot("chest", frame, x=3 + 1.5 * breath, z=-4 + sway)
        rot("neck", frame, z=3 - sway)
        rot("head", frame, x=-2 + 1.5 * breath, z=8 - 4 * sway, y=-4 + 2 * sway)
        rot("shoulder.R", frame, z=-4 - 2 * breath)
        rot("shoulder.L", frame, z=6 + 2 * breath)
        loc("ik_foot.L", frame, x=0.05, y=-0.10)
        rot("ik_foot.L", frame, z=-12)
        loc("ik_foot.R", frame, x=-0.04, y=0.08)
        rot("ik_foot.R", frame, z=18)
        loc("pole_elbow.R", frame, x=-0.1, y=0.1, z=-0.2)
        loc("pole_elbow.L", frame, x=-0.15, y=-0.3, z=-0.25)
        loc("root", frame)
        rot("root", frame)

    def start(frame=0, mode="powpow"):
        body_hold(frame)
        hold_weapons(frame, mode)
        flashes_off(frame)
        chompers_hidden(frame)

    @clip("Idle", 72, loop=True)
    def idle():
        for f, breath, sway in ((0, 0, 0), (18, 1, 0.5), (36, 0, 1), (54, 1, 0.5), (72, 0, 0)):
            body_hold(f, breath, sway)
            hold_weapons(f)
        flashes_off(0)
        chompers_hidden(0)

    @clip("Walk", 18, loop=True)
    def run():
        # Contact, down, passing, up, then the mirrored half (frames 9-18).
        legs = [
            (0, (-0.30, 0.02, 10), (0.32, 0.16, -55)),
            (2, (-0.12, 0.0, 0), (0.24, 0.32, -40)),
            (4, (0.06, 0.0, -5), (-0.02, 0.30, -10)),
            (6, (0.24, 0.07, -35), (-0.24, 0.18, 15)),
        ]
        for half, (lead, trail) in enumerate((("L", "R"), ("R", "L"))):
            for f, a, b in legs:
                frame = f + 9 * half
                for side, (y, z, toe) in ((lead, a), (trail, b)):
                    loc(f"ik_foot.{side}", frame, x=0.02 * C.side_x(side), y=y, z=z)
                    rot(f"ik_foot.{side}", frame, x=toe)
                twist = 9 if lead == "L" else -9
                bob = {0: -0.05, 2: -0.085, 4: -0.03, 6: 0.0}[f]
                loc("hips", frame, z=bob, y=-0.02)
                rot("hips", frame, z=twist, y=(3 if lead == "L" else -3))
                rot("spine", frame, x=12, z=-twist * 0.6)
                rot("chest", frame, x=6, z=-twist * 0.5)
                rot("head", frame, x=-10 + (2 if f == 2 else 0), z=twist * 0.3)
                # Left arm swings opposite to the left leg; the right hand keeps Pow-Pow.
                fk_arm("L", frame, up=18, swing=(34 if lead == "L" else -38), bend=55)
                loc("powpow", frame, z=0.012 if f == 2 else 0.0)
                rot("powpow", frame, x=(4 if f == 2 else -2))
        for frame in (0, 18):
            loc("ik_foot.L", frame, x=0.02, y=-0.30, z=0.02)
            rot("ik_foot.L", frame, x=10)
            loc("ik_foot.R", frame, x=-0.02, y=0.32, z=0.16)
            rot("ik_foot.R", frame, x=-55)
            loc("hips", frame, z=-0.05, y=-0.02)
            rot("hips", frame, z=9, y=3)
            rot("spine", frame, x=12, z=-5.4)
            rot("chest", frame, x=6, z=-4.5)
            rot("head", frame, x=-10, z=2.7)
            fk_arm("L", frame, up=18, swing=34, bend=55)
        barrels_still(0)
        ik("L", "powpow", 0, 0.0)
        ik("R", "powpow", 0, 1.0)
        ik("L", "fishbones", 0, 0.0)
        ik("R", "fishbones", 0, 0.0)
        ik("L", "zapper", 0, 0.0)
        for b in ("fishbones", "zapper"):
            loc(b, 0)
            rot(b, 0)
        flashes_off(0)
        chompers_hidden(0)

    @clip("AA", 22)
    def attack_powpow():
        start()
        # Anticipation: brace low and lean in.
        loc("hips", 3, x=0.01, z=-0.055, y=-0.01)
        rot("spine", 3, x=8, z=-8)
        rot("chest", 3, x=6, z=-6)
        rot("head", 3, x=2, z=10, y=-6)
        loc("powpow", 3, y=-0.02)
        spin(2, 19, 5)
        for k, f in enumerate(range(5, 17, 2)):
            loc("powpow", f, y=0.016 if k % 2 == 0 else 0.004, z=0.004 * (k % 2))
            rot("chest", f, x=4 + (k % 2), z=-6)
            flash("flash_powpow", f, 1, 0.8 + 0.4 * (k % 2))
        body_hold(22)
        loc("powpow", 22)

    @clip("AA rocket", 24)
    def attack_rocket():
        start(0, "fishbones")
        loc("pole_elbow.R", 0, x=-0.2, y=0.2, z=0.1)
        loc("pole_elbow.L", 0, x=0.05, y=0.1, z=-0.1)
        # Anticipation: sink and aim.
        loc("hips", 6, x=0.01, z=-0.07)
        rot("spine", 6, x=9, z=-4)
        rot("head", 6, x=4, z=4)
        # Fire: recoil kicks the launcher up and back, the body rocks back, one foot slides.
        flash("flash_fishbones", 8, 3, 1.3)
        flash("flash_exhaust", 8, 3, 1.0)
        weapon_matrix("fishbones", shoulder_fishbones, 7)
        weapon_matrix("fishbones", Matrix.Translation((0, 0.07, 0.03)) @ shoulder_fishbones_up, 9)
        rot("chest", 9, x=-6, z=-2)
        rot("head", 9, x=-8, z=6)
        loc("hips", 10, x=0.01, y=0.03, z=-0.05)
        loc("ik_foot.R", 11, x=-0.04, y=0.14)
        weapon_matrix("fishbones", shoulder_fishbones, 16)
        rot("chest", 16, x=3, z=-4)
        body_hold(24)
        weapon_matrix("fishbones", shoulder_fishbones, 24)

    @clip("Q", 26)
    def switcheroo():
        start()
        # Pow-Pow is lifted, spun and slung on the back; the left hand reaches back for Fishbones.
        weapon_matrix("powpow", Matrix.Translation((0.02, -0.05, 0.12)) @ rest_matrix("powpow"), 4)
        for side in ("L", "R"):
            ik(side, "powpow", 4, 1.0)
            ik(side, "powpow", 7, 0.0)
        fk_arm("L", 4, up=10, swing=-20, bend=40)
        fk_arm("L", 9, up=-70, swing=60, bend=95, out=20)
        fk_arm("R", 9, up=0, swing=-30, bend=70)
        rot("chest", 9, x=-4, z=12)
        rot("head", 9, x=-6, z=-14)
        weapon_matrix("powpow", placement("powpow", (-0.05, -0.10, 1.35), rx=80, rz=200), 8)
        weapon_matrix("powpow", stowed_powpow, 13)
        # Fishbones swings over the right shoulder in an arc and lands aimed.
        loc("fishbones", 9)
        rot("fishbones", 9)
        weapon_matrix("fishbones", placement("fishbones", (-0.10, 0.12, 1.55), rx=55, rz=-10), 13)
        weapon_matrix("fishbones", Matrix.Translation((0, 0, 0.03)) @ shoulder_fishbones_up, 17)
        weapon_matrix("fishbones", shoulder_fishbones, 21)
        for side in ("L", "R"):
            ik(side, "fishbones", 13, 0.0)
            ik(side, "fishbones", 17, 1.0)
        loc("pole_elbow.R", 17, x=-0.2, y=0.2, z=0.1)
        loc("pole_elbow.L", 17, x=0.05, y=0.1, z=-0.1)
        rot("chest", 17, x=4, z=-8)
        rot("head", 19, x=-4, z=14, y=8)  # cocky head tilt
        body_hold(26)
        hold_weapons(26, "fishbones")
        loc("pole_elbow.R", 26, x=-0.2, y=0.2, z=0.1)
        loc("pole_elbow.L", 26, x=0.05, y=0.1, z=-0.1)

    @clip("W", 26)
    def zap():
        start()
        # The left hand lets go of Pow-Pow, draws the Zapper and fires it at arm's length.
        ik("L", "powpow", 0, 1.0)
        ik("L", "powpow", 3, 0.0)
        ik("L", "zapper", 3, 0.0)
        ik("L", "zapper", 5, 1.0)
        loc("zapper", 5)
        rot("zapper", 5)
        weapon_matrix("zapper", placement("zapper", (0.24, -0.25, 1.12), rx=-10, rz=20), 8)
        weapon_matrix("zapper", aim_zapper, 11)
        rot("chest", 11, x=2, z=12)
        rot("head", 11, x=2, z=12)
        loc("pole_elbow.L", 11, x=0.1, y=0.2, z=-0.2)
        flash("flash_zap", 13, 2, 1.5)
        weapon_matrix("zapper", Matrix.Translation((0, 0.05, 0.05)) @ aim_zapper @ Matrix.Rotation(math.radians(-14), 4, "X"), 14)
        weapon_matrix("zapper", aim_zapper, 18)
        loc("zapper", 23)
        rot("zapper", 23)
        ik("L", "zapper", 22, 1.0)
        ik("L", "zapper", 24, 0.0)
        ik("L", "powpow", 24, 0.0)
        ik("L", "powpow", 26, 1.0)
        body_hold(26)
        loc("pole_elbow.L", 26, x=-0.15, y=-0.3, z=-0.25)

    @clip("E", 30)
    def chompers_toss():
        start()
        # Underhand toss with the left arm: wind back, swing through, follow through high.
        ik("L", "powpow", 0, 1.0)
        ik("L", "powpow", 3, 0.0)
        fk_arm("L", 4, up=5, swing=40, bend=20)
        rot("chest", 6, x=6, z=14)
        fk_arm("L", 7, up=10, swing=55, bend=15)
        rot("chest", 11, x=2, z=-10)
        fk_arm("L", 11, up=30, swing=-70, bend=10)
        fk_arm("L", 15, up=45, swing=-95, bend=20)
        for i in range(3):
            size(f"chomper.{i}", 9, 0.0)
            size(f"chomper.{i}", 10, 1.0)
            loc(f"chomper.{i}", 10, x=0.30 - (-0.25 + 0.25 * i), y=0.55, z=0.95)
            loc(f"chomper.{i}", 14 + i, x=(0.10 - 0.08 * i), y=0.20, z=0.55)
            loc(f"chomper.{i}", 18 + i)
            loc(f"chomper.{i}", 20 + i, y=-0.02, z=0.05)
            loc(f"chomper.{i}", 22 + i, y=-0.03)
            size(f"chomper.{i}", 22 + i, 1.0)
            size(f"chomper.{i}", 24 + i, 1.25)
            size(f"chomper.{i}", 26 + i, 1.0)
        ik("L", "powpow", 24, 0.0)
        ik("L", "powpow", 28, 1.0)
        body_hold(30)

    @clip("R", 52)
    def mega_rocket():
        start()
        # Swap to Fishbones (fast), plant a wide stance, aim high, fire, get thrown back, laugh.
        weapon_matrix("powpow", stowed_powpow, 8)
        weapon_matrix("fishbones", placement("fishbones", (-0.10, 0.12, 1.55), rx=55, rz=-10), 5)
        weapon_matrix("fishbones", shoulder_fishbones_up, 10)
        for side in ("L", "R"):
            ik(side, "powpow", 3, 1.0)
            ik(side, "powpow", 5, 0.0)
            ik(side, "fishbones", 7, 0.0)
            ik(side, "fishbones", 10, 1.0)
        loc("pole_elbow.R", 10, x=-0.2, y=0.2, z=0.1)
        loc("pole_elbow.L", 10, x=0.05, y=0.1, z=-0.1)
        loc("ik_foot.L", 14, x=0.12, y=-0.18)
        loc("ik_foot.R", 14, x=-0.10, y=0.16)
        loc("hips", 14, z=-0.09)
        rot("spine", 18, x=6, z=-8)
        rot("head", 18, x=6, z=6)
        weapon_matrix("fishbones", Matrix.Translation((0, 0.0, 0.02)) @ shoulder_fishbones_up @ Matrix.Rotation(math.radians(8), 4, "X"), 22)
        flash("flash_fishbones", 24, 5, 2.2)
        flash("flash_exhaust", 24, 5, 1.8)
        loc("root", 23)
        loc("root", 27, y=0.16)
        rot("chest", 27, x=-12, z=-2)
        rot("head", 27, x=-22, z=4)  # head thrown back in laughter
        weapon_matrix("fishbones", Matrix.Translation((0, 0.10, 0.08)) @ shoulder_fishbones_up @ Matrix.Rotation(math.radians(24), 4, "X"), 26)
        loc("hips", 28, y=0.04, z=-0.06)
        for k, f in enumerate(range(32, 46, 4)):  # shoulders bounce with laughter
            rot("chest", f, x=-6 + (3 if k % 2 else 0), z=-2)
            rot("head", f, x=-16 + (5 if k % 2 else 0), z=4)
            rot("shoulder.L", f, z=6 + (5 if k % 2 else 0))
            rot("shoulder.R", f, z=-4 - (5 if k % 2 else 0))
        weapon_matrix("fishbones", shoulder_fishbones, 38)
        loc("root", 50, y=0.16)
        body_hold(52)
        loc("root", 52, y=0.16)
        hold_weapons(52, "fishbones")

    @clip("Death", 44)
    def death():
        start()
        # Hit: chest snaps back, Pow-Pow is dropped, a stagger, knees give way, fall backwards.
        rot("chest", 3, x=-14, z=6)
        rot("head", 3, x=-18, z=-6)
        for side in ("L", "R"):
            ik(side, "powpow", 3, 1.0)
            ik(side, "powpow", 6, 0.0)
        fk_arm("L", 6, up=-25, swing=20, bend=40, out=10)
        fk_arm("R", 6, up=-20, swing=25, bend=50)
        loc("powpow", 5)
        rot("powpow", 5)
        weapon_matrix("powpow", placement("powpow", (-0.35, -0.25, 0.06), rx=0, ry=85, rz=30), 14)
        loc("ik_foot.R", 9, x=-0.04, y=0.22)
        loc("hips", 9, y=0.05, z=-0.06)
        loc("hips", 16, y=0.08, z=-0.30)
        rot("spine", 16, x=14)
        rot("chest", 16, x=8)
        rot("head", 16, x=12, z=-10)
        rot("root", 16)
        rot("root", 30, x=-88)
        loc("root", 30, y=0.25, z=0.12)
        loc("hips", 30, z=-0.20)
        rot("spine", 30, x=-4)
        rot("chest", 30, x=-6)
        rot("head", 33, x=-6, z=-25)
        fk_arm("L", 30, up=-60, swing=-30, bend=10, out=30)
        fk_arm("R", 30, up=-50, swing=-20, bend=15, out=-20)
        rot("root", 34, x=-92)
        rot("root", 44, x=-90)
        loc("root", 44, y=0.25, z=0.12)

    @clip("Recall", 48, loop=True)
    def recall():
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            body_hold(f, breath=abs(s_), sway=0.5 + 0.5 * s_)
            hold_weapons(f, "fishbones")
            loc("pole_elbow.R", f, x=-0.2, y=0.2, z=0.1)
            loc("pole_elbow.L", f, x=0.05, y=0.1, z=-0.1)
            # Fishbones resting across the shoulders, bobbing to a hummed tune.
            weapon_matrix("fishbones", placement("fishbones", (-0.05, 0.10, 1.40 + 0.012 * abs(s_)), rx=0, ry=8 * s_, rz=90), f)
            rot("head", f, x=-6, z=10 * s_, y=8 * s_)
            rot("hips", f, z=6 * s_)
        flashes_off(0)
        chompers_hidden(0)

    @clip("P", 36)
    def get_excited():
        start()
        # Crouch, jump with a fist pump, land, bounce.
        loc("hips", 5, z=-0.14, y=0.02)
        rot("spine", 5, x=16)
        rot("head", 5, x=10)
        ik("L", "powpow", 4, 1.0)
        ik("L", "powpow", 6, 0.0)
        fk_arm("L", 6, up=10, swing=20, bend=60)
        loc("root", 6)
        loc("root", 13, z=0.38)
        loc("root", 20)
        rot("spine", 11, x=-6)
        rot("head", 12, x=-14, z=8)
        fk_arm("L", 11, up=135, swing=-30, bend=40, out=10)
        for side in ("L", "R"):
            loc(f"ik_foot.{side}", 13, y=0.02, z=0.06)
            rot(f"ik_foot.{side}", 13, x=-30)
        loc("hips", 21, z=-0.10)
        rot("spine", 21, x=10)
        fk_arm("L", 22, up=110, swing=-20, bend=70)
        ik("L", "powpow", 30, 0.0)
        ik("L", "powpow", 34, 1.0)
        body_hold(36)
        loc("root", 36)
