"""Caitlyn: an original stylized interpretation (tall structured hat, long violet coat with tails,
dark hair with a side braid, copper hextech rifle with a scope)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, cyl, fk_arm, flash, ik, lathe, loc, material, metaball_object, placement, put, rot, size, torus, tube, weapon_matrix

S = 1.07
RIM = (0.65, 0.55, 1.0)
EXPOSURE = -0.2
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55), "R": dict(angle_deg=40, distance=3.6, height=1.2, target_z=0.8)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#edc5a4", rough=0.5, sss=0.2),
        coat=material("Violet coat", "#382d64", rough=0.6),
        panel=material("Purple panel", "#643da2", rough=0.55),
        shirt=material("White shirt", "#edf1f4", rough=0.6),
        trousers=material("Dark trousers", (0.03, 0.025, 0.05), rough=0.6),
        boot=material("Boot leather", (0.025, 0.02, 0.035), rough=0.4),
        glove=material("Violet glove", (0.06, 0.035, 0.11), rough=0.5),
        hair=material("Dark brown hair", (0.06, 0.025, 0.012), rough=0.45),
        hair_dark=material("Deep brown hair", (0.03, 0.012, 0.006), rough=0.5),
        copper=material("Copper", "#b57b49", rough=0.3, metal=1.0),
        gunmetal=material("Gun metal", (0.06, 0.06, 0.07), rough=0.35, metal=0.9),
        stock=material("Stock", (0.10, 0.05, 0.10), rough=0.45),
        lens=material("Scope lens", "#8ae4ff", rough=0.05, emission=1.5),
        glow=material("Hextech blue", "#8ae4ff", emission=7.0),
        flash=material("Muzzle flash", (1.0, 0.75, 0.35), emission=9.0),
        trap=material("Trap steel", (0.25, 0.25, 0.28), rough=0.35, metal=0.9),
        net=material("Net", (0.75, 0.85, 0.95), rough=0.5, emission=1.0),
        laser=material("Laser", (0.3, 0.9, 1.0), emission=12.0),
    )
    C.face_materials(iris=(0.15, 0.35, 0.75), lash=(0.02, 0.012, 0.01), lip=(0.62, 0.28, 0.32))


# ---------------------------------------------------------------- body and clothes


def build_body():
    meta = metaball_object("Caitlyn body")
    C.torso_female(meta, S, bust=0.95, hips=0.97, waist=0.95)
    C.limbs(meta, dict(thigh=(0.062, 0.040), calf=(0.040, 0.046, 0.03), arm=(0.042, 0.031), forearm=(0.033, 0.025), palm=0.033), hands="mitten")
    for side in ("L", "R"):
        knee, ankle, toe = (C.J[f"{n}.{side}"] for n in ("knee", "ankle", "toe"))
        ball(meta, knee + Vector((0, -0.01, 0.03 * S)), 0.052 * S, (1.0, 1.0, 0.5))  # boot top over the knee
        ball(meta, toe + Vector((0, 0.01, 0.004)), 0.034 * S, (0.9, 1.25, 0.7))
    ball(meta, B(0, 0.008, 1.06), 0.105 * S, (1.0, 0.78, 0.55))  # corset
    v = Vector((1, 0, -0.07)).normalized()
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.54, 0.86, 0.99, 1.13, 1.395)]
    cuts += [(B(0.035, 0, 1.0), v), (B(-0.035, 0, 1.0), Vector((-v.x, 0, v.z)))]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.74, 0.79)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            f = C.arm_fraction(c, side)
            return "glove" if f > 0.79 else "shirt" if f > 0.74 else "coat"
        if z < 0.54:
            return "boot"
        if z < 0.86:
            return "trousers"
        if z < 0.99:
            return "coat"
        if z < 1.13:
            return "panel"  # corset
        if z > 1.395 and math.hypot(x, y - 0.01) < 0.065:
            return "skin"
        if y < 0 and abs(x) < 0.035 + (z - 1.0) * 0.07:
            return "shirt"
        return "coat"

    return C.body_mesh(meta, "Caitlyn body", region, ["skin", "coat", "panel", "shirt", "trousers", "boot", "glove"], cuts)


def build_clothes():
    # Coat tails: two long panels at the back and a pair at the sides, on spring chains.
    tails = {}
    for name, x, y, w in (("tail.L", 0.055, 0.105, 0.11), ("tail.R", -0.055, 0.105, 0.11), ("side.L", 0.115, 0.02, 0.07), ("side.R", -0.115, 0.02, 0.07)):
        sx = 1 if x > 0 else -1
        out = 1.0 if name.startswith("side") else 0.0
        pts = [B(x, y, 0.98), B(x + 0.02 * sx * out, y + 0.025, 0.80), B(x + 0.03 * sx * out, y + 0.04, 0.62), B(x + 0.035 * sx * out, y + 0.05, 0.47)]
        side_dir = (1, 0, 0) if not out else (0, 1, 0)
        panel = C.ribbon("Coat tail", pts, w * S, "coat", side_dir, 0.009, [1.0, 1.1, 1.15, 1.1], bone=False)
        tails[name] = (pts, panel)
    # Purple lapels, a white cravat and cuffs.
    for sx in (1, -1):
        lapel = C.ribbon("Lapel", [B(0.04 * sx, -0.083, 1.13), B(0.055 * sx, -0.093, 1.25), B(0.085 * sx, -0.082, 1.37)], 0.03 * S, "panel", (1, 0, 0), 0.005, [0.7, 1.0, 1.2], bone=False)
        C.SKINNED.append((lapel, ["spine", "chest"]))
    cravat = [
        ball_mesh("Cravat knot", "shirt", B(0, -0.06, 1.41), (0.022 * S, 0.016 * S, 0.018 * S)),
        C.ribbon("Cravat", [B(0, -0.065, 1.40), B(0.004, -0.085, 1.34), B(-0.004, -0.093, 1.28)], 0.04 * S, "shirt", (1, 0, 0), 0.005, [0.6, 1.1, 0.8], bone=False),
    ]
    collar = [B(math.sin(a) * 0.072, 0.012 + math.cos(a) * 0.06, 1.405 + 0.025 * (1 + math.cos(a)) / 2) for a in (math.radians(d) for d in range(-140, 141, 20))]
    cravat.append(C.ribbon("Collar", collar, 0.045 * S, "coat", (0, 0, 1), 0.006, bone=False))
    for o in cravat:
        C.PARTS.append((o, "chest"))
    for side in ("L", "R"):
        el, wr = C.J[f"elbow.{side}"], C.J[f"wrist.{side}"]
        frame = C.frame_along(wr, wr - el, C.hand_normal(side))
        cuff = lathe("Coat cuff", "panel", [(0.040, 0.075), (0.043, 0.07), (0.041, 0.03), (0.037, 0.02)], 20)
        C.place(cuff, frame)
        C.PARTS.append((cuff, f"forearm.{side}"))
    # Belt with a copper buckle; boot straps.
    belt = [
        torus("Belt", "boot", 0.118 * S, 0.010 * S, B(0, 0.01, 0.985), (0, 0, 0), (1.0, 0.8, 1.0), 40),
        box("Buckle", "copper", (0.036 * S, 0.012, 0.028 * S), B(0, -0.088, 0.985), 0.004),
    ]
    for o in belt:
        C.PARTS.append((o, "hips"))
    for side in ("L", "R"):
        knee, ankle = C.J[f"knee.{side}"], C.J[f"ankle.{side}"]
        for t in (0.35, 0.7):
            strap = torus("Boot strap", "copper", 0.047 * S, 0.006 * S, knee.lerp(ankle, t), (0, 0, 0), (1, 1, 1), 24)
            C.PARTS.append((strap, f"shin.{side}"))
    return tails


# ---------------------------------------------------------------- head, hair, hat


def build_head():
    C.build_head("Caitlyn head", jaw=0.96, chin=1.0, nose=0.95)
    C.build_face(eye_size=1.0, lashes="winged", brow_mat="hair", brow_width=0.0019, brow_angle=0.04, mouth="flat", mouth_width=1.0, mouth_size=0.0019)


def build_hair():
    h = C.HEAD
    C.hair_cap("Caitlyn hair cap", "hair", front_y=0.04, front_z=0.05)
    meta = metaball_object("Caitlyn hair", resolution=0.004)
    # Straight fringe swept to her right, side curtains framing the face.
    for i, x in enumerate((0.06, 0.035, 0.01, -0.015, -0.04)):
        C.clump(meta, [h + Vector((x * 0.6, -0.07, 0.10)), h + Vector((x - 0.01, -0.10, 0.06)), h + Vector((x - 0.025, -0.098, 0.025 - 0.01 * i))], 0.017, 0.004, flat=0.6)
    for sx in (1, -1):
        C.clump(meta, [h + Vector((0.075 * sx, -0.06, 0.07)), h + Vector((0.095 * sx, -0.065, -0.02)), h + Vector((0.09 * sx, -0.05, -0.11))], 0.02, 0.006, flat=0.6)
    # Back of the head down to the shoulders (the long back hair hangs on chains).
    for x0 in (0.06, 0.0, -0.06):
        C.clump(meta, [h + Vector((x0, 0.05, 0.11)), h + Vector((x0 * 1.3, 0.11, 0.02)), h + Vector((x0 * 1.3, 0.10, -0.10))], 0.035, 0.022)
    hair = C.mesh_from_meta(meta, "Caitlyn hair", voxel=0.0035, smooth=3, tris=6000)
    C.paint_regions(hair, lambda c: "hair" if c.z > h.z - 0.02 else "hair_dark", ["hair", "hair_dark"])
    C.PARTS.append((hair, "head"))
    # Long hair down the back: two tapered sheets (chains), and a side braid over her left shoulder.
    backs = {}
    for side, sx in (("L", 1), ("R", -1)):
        path = [h + Vector((0.045 * sx, 0.10, -0.08)), B(0.06 * sx, 0.135, 1.36), B(0.07 * sx, 0.14, 1.22), B(0.075 * sx, 0.13, 1.08)]
        sheet = metaball_object(f"Back hair {side}", resolution=0.005)
        C.clump(sheet, path, 0.045, 0.02, flat=0.55)
        backs[side] = (path, C.mesh_from_meta(sheet, f"Back hair {side}", voxel=0.0045, smooth=3, tris=2500))
        backs[side][1].data.materials.append(M["hair"])
    braid_path = [h + Vector((0.085, -0.01, -0.06)), h + Vector((0.11, -0.03, -0.13)), B(0.13, -0.05, 1.36), B(0.14, -0.07, 1.24), B(0.14, -0.075, 1.12)]
    lobes = C.braid_lobes(braid_path, radius=0.022, taper=0.4, twist=35)
    tie = ball_mesh("Braid tie", "copper", braid_path[-1] + Vector((0, 0, -0.005)), (0.011, 0.011, 0.008), 12, 6)
    return backs, braid_path, lobes + [tie]


def build_hat():
    """A tall structured hat, tilted to her right: brim, crown, copper band and a hextech gem."""
    h = C.HEAD
    parts = [
        lathe("Hat brim", "coat", [(0.0, -0.004), (0.17, -0.004), (0.178, 0.0), (0.17, 0.006), (0.0, 0.006)], 40, "Z"),
        lathe("Hat crown", "coat", [(0.0, 0.0), (0.098, 0.0), (0.094, 0.10), (0.10, 0.205), (0.0, 0.21)], 40, "Z"),
        lathe("Hat band", "panel", [(0.1, 0.012), (0.1, 0.05)], 40, "Z"),
        torus("Band trim", "copper", 0.1, 0.004, (0, 0, 0.052), (0, 0, 0), (1, 1, 1), 40),
        box("Band buckle", "copper", (0.03, 0.01, 0.036), (0.0, -0.1, 0.032), 0.003),
        ball_mesh("Hat gem", "glow", (0.0, -0.106, 0.032), (0.008, 0.005, 0.008), 12, 6),
    ]
    for sx in (1, -1):  # small goggles resting on the brim
        parts.append(cyl("Hat goggle", "copper", 0.016, 0.014, (0.03 * sx, -0.105, 0.072), (math.radians(-80), 0, 0), 16))
        parts.append(cyl("Hat goggle lens", "lens", 0.012, 0.016, (0.03 * sx, -0.106, 0.072), (math.radians(-80), 0, 0), 16))
    hat = C.join(parts, "Hat")
    C.place(hat, Matrix.Translation(h + Vector((0.0, 0.012, 0.075))) @ Matrix.Rotation(math.radians(-9), 4, "Y") @ Matrix.Rotation(math.radians(-5), 4, "X"))
    C.PARTS.append((hat, "head"))


# ---------------------------------------------------------------- rifle and gear


def build_rifle():
    """The hextech rifle: grip at the origin, barrel toward -Y, stock toward +Y, scope on top."""
    parts = [
        box("Stock", "stock", (0.045, 0.24, 0.07), (0, 0.16, -0.02), 0.012),
        box("Butt plate", "copper", (0.05, 0.02, 0.085), (0, 0.285, -0.025), 0.005),
        box("Receiver", "copper", (0.05, 0.16, 0.06), (0, -0.02, 0.012), 0.008),
        cyl("Grip", "stock", 0.016, 0.10, (0, 0.035, -0.055), (math.radians(25), 0, 0), 12),
        box("Trigger guard", "gunmetal", (0.008, 0.04, 0.03), (0, 0.0, -0.035), 0.003),
        lathe("Barrel shroud", "copper", [(0.026, -0.10), (0.028, -0.14), (0.024, -0.36), (0.02, -0.40)], 20),
        cyl("Barrel", "gunmetal", 0.012, 0.42, (0, -0.52, 0.012), C.X90, 16),
        lathe("Muzzle", "copper", [(0.018, -0.72), (0.024, -0.73), (0.024, -0.78), (0.016, -0.79)], 20),
        box("Foregrip", "stock", (0.036, 0.10, 0.03), (0, -0.22, -0.02), 0.008),
        cyl("Scope", "gunmetal", 0.019, 0.22, (0, -0.06, 0.078), C.X90, 20),
        cyl("Scope ring front", "copper", 0.024, 0.02, (0, -0.16, 0.078), C.X90, 20),
        cyl("Scope ring back", "copper", 0.022, 0.02, (0, 0.04, 0.078), C.X90, 20),
        cyl("Scope lens", "lens", 0.017, 0.006, (0, -0.172, 0.078), C.X90, 20),
        box("Scope mount", "gunmetal", (0.016, 0.10, 0.03), (0, -0.06, 0.05), 0.004),
        lathe("Hextech core", "glow", [(0.03, -0.075), (0.03, -0.095)], 20),
    ]
    for k in range(3):
        parts.append(lathe("Barrel ring", "copper", [(0.027, -0.18 - 0.07 * k), (0.027, -0.19 - 0.07 * k)], 20))
    return C.join(parts, "Rifle")


def build_trap():
    parts = [cyl("Trap base", "trap", 0.07, 0.015, (0, 0, 0.008), (0, 0, 0), 20), ball_mesh("Trap core", "glow", (0, 0, 0.02), (0.018, 0.018, 0.01), 12, 6)]
    for sx in (1, -1):
        jaw = torus("Trap jaw", "trap", 0.06, 0.006, (0.0, 0.0, 0.02), (0, math.radians(70 * sx), 0), (1, 1, 1), 24)
        parts.append(jaw)
        for k in range(5):
            a = math.radians(-60 + k * 30)
            parts.append(C.cone("Trap tooth", "trap", 0.006, 0.0, 0.02, (0.06 * math.cos(a) * 0.3 * sx, 0.06 * math.sin(a), 0.035), (0, 0, 0), 4))
    return C.join(parts, "FX trap")


def build_net():
    parts = [torus("FX net rim", "net", 0.22, 0.008, (0, 0, 0), (math.pi / 2, 0, 0), (1, 1, 1), 32)]
    for k in range(4):
        a = k * math.pi / 4
        parts.append(cyl("FX net strand", "net", 0.003, 0.44, (0, 0, 0), (0, a, 0), 6))
    for r in (0.08, 0.15):
        parts.append(torus("FX net ring", "net", r, 0.003, (0, 0, 0), (math.pi / 2, 0, 0), (1, 1, 1), 24))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        parts.append(ball_mesh("FX net weight", "trap", (math.cos(a) * 0.22, 0, math.sin(a) * 0.22), (0.018, 0.018, 0.018), 10, 6))
    return C.join(parts, "FX net")


def fx_flash(name, radius, mat="flash", spikes=5):
    parts = [ball_mesh(f"FX {name}", mat, (0, 0, 0), (radius, radius * 1.6, radius), 16, 8)]
    for i in range(spikes):
        a = i * 2 * math.pi / spikes
        parts.append(C.cone("FX spike", mat, radius * 0.35, 0.0, radius * 3.2, (math.cos(a) * radius * 0.8, -radius * 1.8, math.sin(a) * radius * 0.8), (math.pi / 2 + 0.35 * math.sin(a), 0.35 * math.cos(a), 0), 4))
    return C.join(parts, f"FX {name}")


def fx_bullet(name, length, radius, mat="flash"):
    parts = [lathe(f"FX {name}", mat, [(0.0, -length * 0.5), (radius, -length * 0.35), (radius * 0.7, 0.0), (radius * 0.2, length * 0.5), (0.0, length)], 12)]
    return C.join(parts, f"FX {name}")


# ---------------------------------------------------------------- assembly

# Rest placement of the rifle: carried on the right shoulder, barrel up and back, scope outward.
CARRY = None


def build():
    global CARRY
    C.make_joints(scale=S, shoulder_x=0.172, hip_x=0.094)
    materials()
    body = build_body()
    tails = build_clothes()
    build_head()
    backs, braid_path, braid = build_hair()
    build_hat()
    C.scale_parts("head", 1.06, C.J["head_bone"])
    rifle = build_rifle()
    trap = build_trap()
    net = build_net()

    # The rifle's rest frame: carried on the right shoulder (barrel up, slightly back, scope out).
    turn = Matrix.Rotation(math.radians(-100), 3, "X") @ Matrix.Rotation(math.radians(-90), 3, "Y")
    CARRY = Matrix.Translation(B(-0.205, -0.085, 1.165)) @ turn.to_4x4()
    C.place(rifle, CARRY)
    muzzle = CARRY @ Matrix.Translation((0, -0.80, 0.012))
    fx = {
        "fx_muzzle": (fx_flash("muzzle flash", 0.035), muzzle, "rifle"),
        "fx_bullet": (fx_bullet("bullet", 0.16, 0.012), None, None),
        "fx_peacemaker": (fx_bullet("peacemaker", 0.5, 0.05, "glow"), None, None),
        "fx_headshot": (fx_bullet("headshot", 0.3, 0.025, "flash"), None, None),
        "fx_net": (net, None, None),
        "fx_laser": (cyl("FX laser", "laser", 0.004, 6.0, (0, -3.0, 0), C.X90, 8), None, None),
        "fx_core": (ball_mesh("FX hextech charge", "glow", (0, 0, 0), (0.05, 0.05, 0.05), 16, 8), CARRY @ Matrix.Translation((0, -0.085, 0.012)), "rifle"),
        "fx_trap": (trap, None, None),
    }
    ahead = Matrix.Translation(B(-0.2, -0.3, 1.2))
    for name, (obj, matrix, _) in list(fx.items()):
        if matrix is None:
            fx[name] = (obj, ahead, None)
        C.place(obj, fx[name][1])

    grip = CARRY @ Vector((0, 0.0, -0.04))
    fore = CARRY @ Vector((0, -0.22, -0.035))
    extra = [
        C.weapon_bones("rifle", CARRY, (0, 0, 0), "chest", 0.3),
        C.grip_bone("grip_rifle.R", grip, "rifle"),
        C.grip_bone("grip_rifle.L", fore, "rifle"),
    ]
    extra += [C.point_bone(name, matrix, parent) for name, (_, matrix, parent) in fx.items()]
    chains = [
        (name, C.resample(pts, 3), "hips", dict(skin=True, stiffness=60 if name.startswith("tail") else 75, gain=0.8, sway=2.0, limit=(40, 20))) for name, (pts, _) in tails.items()
    ]
    for side, (path, _) in backs.items():
        chains.append((f"backhair.{side}", C.resample(path, 3), "head", dict(skin=True, stiffness=65, gain=0.9, sway=2.5, limit=(35, 25))))
    chains.append(("braid", C.resample(braid_path, 5), "head", dict(stiffness=60, gain=1.0, sway=3.0, limit=(40, 30))))
    C.SOCKETS["socket_muzzle"] = ("rifle", muzzle)
    for name, (_, panel) in tails.items():
        C.SKINNED.append((panel, ["hips"] + [f"{name}.{i}" for i in range(3)]))
    for side, (_, sheet) in backs.items():
        C.SKINNED.append((sheet, ["head"] + [f"backhair.{side}.{i}" for i in range(3)]))
    C.build_rig("Caitlyn rig", chains, extra, [("R", "rifle", "grip_rifle.R"), ("L", "rifle", "grip_rifle.L")])
    C.bind(body)
    C.attach(rifle, "rifle")
    for obj in braid:
        C.attach_to_chain(obj, "braid")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips()


# ---------------------------------------------------------------- clips (24 fps)

FX = ("fx_muzzle", "fx_bullet", "fx_peacemaker", "fx_headshot", "fx_net", "fx_laser", "fx_core", "fx_trap")


def define_clips():
    # Rifle placements (armature space): low ready at the hip and shouldered aim, with the torso
    # bladed so the left hand reaches the foregrip.
    hip_aim = placement("rifle", B(-0.10, -0.20, 1.10), rx=2, rz=6)
    shoulder_aim = placement("rifle", B(-0.115, -0.22, 1.40), rx=1, rz=8)
    kneel_aim = placement("rifle", B(-0.10, -0.22, 1.02), rx=2, rz=8)

    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def carry(frame, right=1.0):
        loc("rifle", frame)
        rot("rifle", frame)
        ik("R", "rifle", frame, right)
        ik("L", "rifle", frame, 0.0)

    def stance(frame, breath=0.0, sway=0.0):
        """Poised stance: rifle on the right shoulder, left hand on the hip."""
        loc("hips", frame, x=0.012 + 0.008 * sway, z=-0.015 - 0.004 * breath)
        rot("hips", frame, y=3 + sway, z=-6)
        rot("spine", frame, x=1 + breath, y=-2, z=3)
        rot("chest", frame, x=-3 + 1.5 * breath, z=2 - sway)
        rot("neck", frame, z=-2)
        rot("head", frame, x=-4 + breath, y=3 - 2 * sway, z=-6 + 2 * sway)
        rot("shoulder.L", frame, z=2 + 1.5 * breath)
        C.feet(frame, (0.03, 0.04, 0, -16), (-0.02, -0.06, 0, 10))
        fk_arm("L", frame, up=36, swing=14, bend=105, twist=85, hand=10)
        loc("pole_elbow.R", frame, x=-0.15, y=0.15, z=-0.35)
        carry(frame)
        loc("root", frame)
        rot("root", frame)

    def aim(frame, matrix, lean=0.0):
        """Shouldered or hip aim: torso bladed, both hands on the rifle (body keyed first, so
        the rifle placement is solved against the final chest)."""
        ik("R", "rifle", frame, 1.0)
        ik("L", "rifle", frame, 1.0)
        rot("hips", frame, z=-14)
        loc("hips", frame, z=-0.03)
        rot("spine", frame, x=3 + lean, z=-12)
        rot("chest", frame, x=2 + lean, z=-14)
        rot("head", frame, x=6, y=4, z=22)
        loc("pole_elbow.R", frame, x=-0.25, y=0.2, z=0.05)
        loc("pole_elbow.L", frame, x=0.05, y=-0.1, z=-0.35)
        C.feet(frame, (0.05, -0.10, 0, -25), (-0.05, 0.10, 0, 30))
        weapon_matrix("rifle", matrix, frame)

    def muzzle_point(frame):
        return C.carried("rifle", frame, C.rig.data.bones["fx_muzzle"].head_local)

    def shoot(name, frame_from, frame_to, distance=3.5):
        """A projectile from the muzzle straight ahead (solved after the clip's keys)."""
        size(name, frame_from - 1, 0.0)
        size(name, frame_from, 1.0)
        size(name, frame_to, 1.0)
        size(name, frame_to + 1, 0.0)

        @C.later
        def fly():
            start_co = muzzle_point(frame_from)
            put(name, frame_from, start_co)
            put(name, frame_to, start_co + Vector((0.0, -distance, 0.0)))

    def start(frame=0):
        stance(frame)
        fx_off(frame)

    @clip("Idle", 72, loop=True)
    def idle():
        for f, breath, sway in ((0, 0, 0), (18, 1, 0.5), (36, 0, 1), (54, 1, 0.5), (72, 0, 0)):
            stance(f, breath, sway)
        fx_off(0)

    @clip("Walk", 18, loop=True)
    def run():
        def upper(frame, lead, phase):
            arc = 34 * (1 if lead == "L" else -1) * phase
            fk_arm("L", frame, up=12, swing=arc, bend=60, out=-4, hand=-5)
            carry(frame)
            loc("pole_elbow.R", frame, x=-0.15, y=0.15, z=-0.35)
            rot("shoulder.R", frame, z=-3)

        C.run_cycle(upper, scale=S, lean=9, twist=9)
        fx_off(0)

    @clip("AA", 22)
    def attack():
        start()
        # Swing the rifle down off the shoulder into a hip aim, fire, swing it back up.
        weapon_matrix("rifle", placement("rifle", B(-0.16, -0.18, 1.22), rx=40, rz=-10, roll=-40), 3)
        ik("L", "rifle", 2, 0.0)
        aim(6, hip_aim)
        fx_off(6)
        flash("fx_muzzle", 8, 2, 1.2)
        shoot("fx_bullet", 8, 13, 4.0)
        rot("chest", 9, x=-1, z=-12)
        weapon_matrix("rifle", Matrix.Translation(B(0, 0.04, 0.03)) @ hip_aim @ Matrix.Rotation(math.radians(-8), 4, "X"), 9)
        aim(13, hip_aim)
        ik("L", "rifle", 16, 1.0)
        ik("L", "rifle", 19, 0.0)
        weapon_matrix("rifle", placement("rifle", B(-0.16, -0.18, 1.22), rx=40, rz=-10, roll=-40), 17)
        stance(22)

    def shouldered_shot(frame_aim, frame_fire, bullet, peak=1.6, kick=0.06):
        aim(frame_aim, shoulder_aim)
        fk_arm("L", frame_aim - 2, up=20, swing=-40, bend=60)
        flash("fx_muzzle", frame_fire, 3, peak)
        shoot(bullet, frame_fire, frame_fire + 6, 4.5)
        rot("chest", frame_fire + 1, x=-4, z=-10)
        rot("head", frame_fire + 1, x=0, y=4, z=18)
        weapon_matrix("rifle", Matrix.Translation(B(0, kick, kick * 0.6)) @ shoulder_aim @ Matrix.Rotation(math.radians(-10), 4, "X"), frame_fire + 1)
        loc("hips", frame_fire + 2, y=0.03, z=-0.03)
        aim(frame_fire + 6, shoulder_aim)

    @clip("P", 30)
    def headshot():
        start()
        weapon_matrix("rifle", placement("rifle", B(-0.16, -0.16, 1.30), rx=45, rz=-10, roll=-40), 3)
        ik("L", "rifle", 2, 0.0)
        shouldered_shot(8, 12, "fx_headshot", 2.0, 0.08)
        rot("head", 10, x=10, y=6, z=24)  # cheek on the stock, eye to the scope
        weapon_matrix("rifle", placement("rifle", B(-0.16, -0.16, 1.30), rx=45, rz=-10, roll=-40), 24)
        ik("L", "rifle", 22, 1.0)
        ik("L", "rifle", 25, 0.0)
        stance(30)

    @clip("Q", 34)
    def peacemaker():
        start()
        weapon_matrix("rifle", placement("rifle", B(-0.16, -0.16, 1.30), rx=45, rz=-10, roll=-40), 4)
        ik("L", "rifle", 3, 0.0)
        aim(9, shoulder_aim)
        fk_arm("L", 7, up=20, swing=-40, bend=60)
        # Hextech charge builds in the receiver, then a wide piercing round.
        size("fx_core", 8, 0.0)
        size("fx_core", 16, 1.0)
        size("fx_core", 17, 0.0)
        for k, f in enumerate(range(10, 17, 2)):
            rot("chest", f, x=2 + (0.8 if k % 2 else 0), z=-14)
        flash("fx_muzzle", 17, 4, 2.4)
        shoot("fx_peacemaker", 17, 24, 5.0)
        rot("chest", 18, x=-7, z=-8)
        rot("head", 18, x=-4, y=4, z=16)
        weapon_matrix("rifle", Matrix.Translation(B(0, 0.10, 0.07)) @ shoulder_aim @ Matrix.Rotation(math.radians(-16), 4, "X"), 18)
        loc("hips", 19, y=0.05, z=-0.04)
        C.feet(19, (0.05, -0.08, 0, -25), (-0.05, 0.16, 0, 30))
        aim(25, shoulder_aim)
        weapon_matrix("rifle", placement("rifle", B(-0.16, -0.16, 1.30), rx=45, rz=-10, roll=-40), 29)
        ik("L", "rifle", 27, 1.0)
        ik("L", "rifle", 30, 0.0)
        stance(34)

    @clip("W", 28)
    def snap_trap():
        start()
        # The left hand pulls a trap from the belt and tosses it underhand ahead.
        fk_arm("L", 4, up=10, swing=15, bend=40, twist=20)
        rot("chest", 4, x=4, z=8)
        fk_arm("L", 8, up=8, swing=40, bend=25)
        rot("chest", 8, x=8, z=10)
        loc("hips", 8, z=-0.05)
        fk_arm("L", 12, up=25, swing=-70, bend=15)
        rot("chest", 12, x=2, z=-8)
        fk_arm("L", 15, up=35, swing=-85, bend=25)
        size("fx_trap", 10, 0.0)
        hand = C.carried("hand.L", 11, C.J["hand.L"])
        put("fx_trap", 11, hand)
        size("fx_trap", 11, 1.0)
        put("fx_trap", 15, B(0.15, -0.6, 0.45))
        put("fx_trap", 19, B(0.2, -1.0, 0.0))
        put("fx_trap", 21, B(0.2, -1.02, 0.03))
        put("fx_trap", 23, B(0.2, -1.03, 0.0))
        size("fx_trap", 27, 1.0)
        size("fx_trap", 28, 1.0)
        stance(28)

    @clip("E", 30)
    def caliber_net():
        start()
        moving = bool(C.OPTIONS.get("root_motion"))
        # Fire a net forward from the hip while the recoil throws her back in a hop.
        weapon_matrix("rifle", placement("rifle", B(-0.16, -0.18, 1.22), rx=40, rz=-10, roll=-40), 2)
        ik("L", "rifle", 1, 0.0)
        aim(5, hip_aim)
        flash("fx_muzzle", 7, 3, 1.8)
        size("fx_net", 6, 0.0)
        size("fx_net", 7, 0.3)
        size("fx_net", 14, 1.4)

        @C.later
        def net():
            put("fx_net", 7, muzzle_point(7))
            put("fx_net", 14, muzzle_point(7) + Vector((0, -2.5, 0.1)))

        size("fx_net", 15, 0.0)
        weapon_matrix("rifle", Matrix.Translation(B(0, 0.08, 0.10)) @ hip_aim @ Matrix.Rotation(math.radians(-25), 4, "X"), 9)
        loc("root", 7)
        loc("root", 13, y=0.9 if moving else 0.0, z=0.28)
        loc("root", 18, y=1.2 if moving else 0.0)
        loc("root", 20, y=1.2 if moving else 0.0)
        for side in ("L", "R"):
            loc(f"ik_foot.{side}", 13, x=0.03 * C.side_x(side), y=-0.08, z=0.10)
            rot(f"ik_foot.{side}", 13, x=-25)
        rot("spine", 12, x=-10)
        rot("chest", 12, x=-8, z=-8)
        rot("head", 12, x=-6)
        loc("hips", 18, z=-0.10)
        rot("spine", 18, x=10)
        stance(30)
        loc("root", 30, y=1.2 if moving else 0.0)

    @clip("R", 64)
    def ace_in_the_hole():
        start()
        # Drop to one knee, shoulder the rifle, a long laser-sighted aim, then one huge shot.
        weapon_matrix("rifle", placement("rifle", B(-0.16, -0.16, 1.15), rx=40, rz=-10, roll=-40), 5)
        ik("L", "rifle", 4, 0.0)
        loc("hips", 10, y=0.08, z=-0.36)
        rot("hips", 10, z=-18)
        C.feet(10, (0.06, -0.20, 0, -20), (-0.06, 0.22, 0.02, 30))
        rot("ik_foot.R", 10, x=-60, z=30)
        ik("L", "rifle", 12, 1.0)
        ik("R", "rifle", 12, 1.0)
        rot("spine", 12, x=6, z=-12)
        rot("chest", 12, x=6, z=-14)
        rot("head", 12, x=10, y=6, z=22)
        loc("pole_elbow.R", 12, x=-0.25, y=0.2, z=-0.1)
        loc("pole_elbow.L", 12, x=0.05, y=-0.1, z=-0.45)
        weapon_matrix("rifle", kneel_aim, 12)
        size("fx_laser", 13, 0.0)
        size("fx_laser", 14, 1.0)
        for k, f in enumerate(range(16, 41, 4)):  # held breath: tiny scope sway
            weapon_matrix("rifle", kneel_aim @ Matrix.Rotation(math.radians(0.6 * (-1) ** k), 4, "Z"), f)

        @C.later
        def laser():
            for f in [14] + list(range(16, 41, 4)) + [40]:
                put("fx_laser", f, muzzle_point(f))

        size("fx_laser", 40, 1.0)
        size("fx_laser", 41, 0.0)
        size("fx_core", 30, 0.0)
        size("fx_core", 40, 1.2)
        size("fx_core", 41, 0.0)
        flash("fx_muzzle", 41, 5, 3.0)
        shoot("fx_peacemaker", 41, 47, 6.0)
        rot("chest", 42, x=-6, z=-10)
        rot("head", 42, x=0, z=16)
        weapon_matrix("rifle", Matrix.Translation(B(0, 0.12, 0.08)) @ kneel_aim @ Matrix.Rotation(math.radians(-18), 4, "X"), 42)
        rot("chest", 48, x=6, z=-14)
        weapon_matrix("rifle", kneel_aim, 48)
        loc("hips", 50, y=0.08, z=-0.36)
        weapon_matrix("rifle", placement("rifle", B(-0.16, -0.16, 1.15), rx=40, rz=-10, roll=-40), 56)
        ik("L", "rifle", 54, 1.0)
        ik("L", "rifle", 57, 0.0)
        stance(64)

    @clip("Recall", 48, loop=True)
    def recall():
        # A tip of the hat, rifle resting on the shoulder.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.3)
            fk_arm("L", f, up=70 + 4 * abs(s_), swing=-35, bend=130, out=-5, twist=-10, hand=-20)
            rot("head", f, x=8 + 3 * abs(s_), y=4, z=-8)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        ik("R", "rifle", 3, 1.0)
        ik("R", "rifle", 6, 0.0)
        loc("rifle", 5)
        rot("rifle", 5)
        weapon_matrix("rifle", placement("rifle", B(-0.40, -0.10, 0.05), rx=0, ry=85, rz=40), 16)
        C.fall_back(0, S)
