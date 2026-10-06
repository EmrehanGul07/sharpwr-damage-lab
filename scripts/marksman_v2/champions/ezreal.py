"""Ezreal: an original stylized interpretation (swept blond hair, goggles, explorer jacket, scarf,
belts and a glowing arcane gauntlet on the left hand)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, cyl, fk_arm, lathe, loc, material, metaball_object, put, rot, size, sphere, torus, tube  # noqa: F401

S = 1.04  # height scale against the base skeleton
RIM = (0.45, 0.85, 1.0)
EXPOSURE = -0.3
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.5, height=1.5, target_z=0.55)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#e6b58f", rough=0.5, sss=0.2),
        jacket=material("Explorer blue", "#1c657e", rough=0.6),
        jacket_dark=material("Jacket lining", "#103d4d", rough=0.7),
        trim=material("Gold trim", "#bb8c45", rough=0.35, metal=0.7),
        cuff=material("Rolled cuff", "#174f63", rough=0.65),
        shirt=material("Shirt", (0.30, 0.26, 0.20), rough=0.7),
        trousers=material("Trousers", "#353947", rough=0.7),
        boot=material("Boot leather", (0.085, 0.045, 0.025), rough=0.45),
        leather=material("Belt leather", (0.16, 0.075, 0.03), rough=0.5),
        glove=material("Glove", (0.06, 0.035, 0.02), rough=0.55),
        hair=material("Blond hair", (0.80, 0.55, 0.20), rough=0.45),
        hair_dark=material("Deep blond", (0.50, 0.30, 0.09), rough=0.5),
        scarf=material("Scarf", (0.55, 0.33, 0.12), rough=0.75),
        brass=material("Brass", "#bb8c45", rough=0.28, metal=1.0),
        lens=material("Goggle lens", (0.85, 0.42, 0.08), rough=0.08, emission=0.35),
        glow=material("Arcane cyan", "#60edff", emission=7.0),
        gold_glow=material("Essence gold", (1.0, 0.72, 0.25), emission=7.0),
    )
    C.face_materials(iris=(0.10, 0.38, 0.85), lash=(0.03, 0.02, 0.015), lip=(0.60, 0.36, 0.30))


# ---------------------------------------------------------------- body


def build_body():
    meta = metaball_object("Ezreal body")
    ball(meta, B(0, 0.004, 0.95), 0.118 * S, (1.0, 0.74, 0.62))  # pelvis
    for sx in (1, -1):
        ball(meta, B(0.05 * sx, 0.04, 0.915), 0.06 * S)  # glutes
    ball(meta, B(0, 0.006, 1.04), 0.105 * S, (1.0, 0.76, 0.8))  # waist
    ball(meta, B(0, 0.004, 1.12), 0.108 * S, (1.0, 0.76, 0.85))  # abdomen
    ball(meta, B(0, 0.006, 1.21), 0.128 * S, (1.0, 0.74, 0.9))  # ribcage
    ball(meta, B(0, 0.012, 1.30), 0.142 * S, (1.05, 0.68, 0.6))  # upper chest
    for sx in (1, -1):
        ball(meta, B(0.058 * sx, -0.035, 1.265), 0.058 * S, (1.15, 0.7, 0.75))  # pecs
        ball(meta, B(0.155 * sx, 0.012, 1.345), 0.058 * S, (1.2, 0.9, 0.75))  # deltoids
        ball(meta, B(0.07 * sx, 0.03, 1.375), 0.045 * S, (1.3, 0.9, 0.7))  # trapezius
    ball(meta, B(0, 0.01, 0.885), 0.125 * S, (1.05, 0.8, 0.35))  # jacket hem
    C.limbs(
        meta,
        dict(neck=(0.054, 0.047), thigh=(0.068, 0.046), calf=(0.046, 0.05, 0.032), foot=(0.040, 0.034), arm=(0.050, 0.037), forearm=(0.038, 0.029), palm=0.036),
        hands="mitten",
    )
    for side in ("L", "R"):
        knee, ankle, toe = (C.J[f"{n}.{side}"] for n in ("knee", "ankle", "toe"))
        ball(meta, knee.lerp(ankle, 0.33), 0.055 * S, (1.0, 1.0, 0.45))  # boot cuff
        ball(meta, toe + Vector((0, 0.012, 0.006)), 0.038 * S, (0.95, 1.2, 0.75))  # boot toe
    v = Vector((1, 0, -0.10)).normalized()
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.355, 0.885, 1.385)]
    cuts += [(B(0.02, 0, 0.95), v), (B(-0.02, 0, 0.95), Vector((-v.x, 0, v.z)))]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.60, 0.66, 0.80)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.21 and z > 0.88:
            f = C.arm_fraction(c, side)
            return "glove" if f > 0.80 else "skin" if f > 0.66 else "cuff" if f > 0.60 else "jacket"
        if z < 0.355:
            return "boot"
        if z < 0.885:
            return "trousers"
        if z > 1.385 and math.hypot(x, y - 0.01) < 0.072:
            return "skin"
        if y < 0 and z > 0.97 and abs(x) < 0.02 + (z - 0.95) * 0.10:
            return "shirt"
        return "jacket"

    return C.body_mesh(meta, "Ezreal body", region, ["skin", "jacket", "cuff", "shirt", "trousers", "boot", "glove"], cuts, tris=20000)


def build_clothes():
    # Lapels along the open front, skinned to the spine and chest.
    for sx in (1, -1):
        lapel = C.ribbon("Lapel", [B(0.024 * sx, -0.080, 0.99), B(0.042 * sx, -0.093, 1.17), B(0.07 * sx, -0.085, 1.36)], 0.014 * S, "trim", (1, 0, 0.0), 0.004, [0.6, 1.0, 1.1], bone=False)
        C.SKINNED.append((lapel, ["spine", "chest"]))
    # Scarf: a soft, bunched wrap (metaball folds) with a knot; its loose end flows down the
    # back on a spring chain.
    meta = metaball_object("Scarf", resolution=0.006)
    for k, (z, r, lean) in enumerate(((1.418, 0.068, -0.012), (1.385, 0.074, 0.008))):
        ring = []
        for d in range(0, 360, 20):
            a = math.radians(d)
            ring.append(B(math.sin(a) * r, 0.012 - math.cos(a) * r * 0.92, z + lean * math.cos(a)))
        for i, co in enumerate(ring):
            ball(meta, co, (0.024 + 0.006 * math.sin(i * 1.9 + k)) * S, (1.0, 1.0, 0.75))
    ball(meta, B(0.045, 0.075, 1.385), 0.032 * S)  # knot
    scarf_wrap = C.mesh_from_meta(meta, "Scarf wrap", voxel=0.005, smooth=3, tris=3000)
    scarf_wrap.data.materials.append(M["scarf"])
    C.PARTS.append((scarf_wrap, "chest"))
    tail = [B(0.045, 0.085, 1.38), B(0.06, 0.125, 1.30), B(0.07, 0.15, 1.19), B(0.075, 0.16, 1.07)]
    scarf = C.ribbon("Scarf tail", tail, 0.055 * S, "scarf", (1, 0, 0), 0.008, [1.0, 1.0, 0.9, 0.8], bone=False)
    # Jacket tails at the back, on spring chains from the hips.
    coats = {}
    for side, sx in (("L", 1), ("R", -1)):
        pts = [B(0.06 * sx, 0.11, 0.95), B(0.068 * sx, 0.125, 0.81), B(0.072 * sx, 0.132, 0.69)]
        coats[side] = (pts, C.ribbon("Jacket tail", pts, 0.11 * S, "jacket", (1, 0, 0), 0.009, [1.0, 1.05, 0.95], bone=False))
    # Belts with a brass buckle and pouches.
    belts = [
        torus("Belt", "leather", 0.13 * S, 0.012 * S, B(0, 0.012, 0.915), (0, 0.06, 0), (1.0, 0.78, 1.0), 40),
        torus("Hip belt", "leather", 0.135 * S, 0.010 * S, B(0, 0.014, 0.885), (0, -0.22, 0), (1.0, 0.8, 1.0), 40),
        box("Buckle", "brass", (0.034 * S, 0.012, 0.026 * S), B(0.0, -0.097, 0.913), 0.004),
        box("Pouch", "leather", (0.045 * S, 0.035 * S, 0.05 * S), B(-0.115, -0.045, 0.87), 0.008, (0, 0, math.radians(-25))),
        box("Pouch flap", "brass", (0.02 * S, 0.006, 0.012 * S), B(-0.124, -0.067, 0.885), 0.002, (0, 0, math.radians(-25))),
        box("Back pouch", "leather", (0.06 * S, 0.035 * S, 0.045 * S), B(0.06, 0.112, 0.905), 0.008),
    ]
    for o in belts:
        C.PARTS.append((o, "hips"))
    # Boot cuffs and a leather bracer on the right forearm.
    for side in ("L", "R"):
        knee, ankle = C.J[f"knee.{side}"], C.J[f"ankle.{side}"]
        t = (knee.z - 0.36 * S) / (knee.z - ankle.z)
        C.PARTS.append((torus("Boot cuff", "boot", 0.054 * S, 0.011 * S, knee.lerp(ankle, t), (0, 0, 0), (1.0, 1.0, 1.0), 24), f"shin.{side}"))
    el, wr = C.J["elbow.R"], C.J["wrist.R"]
    frame = C.frame_along(wr, wr - el, C.hand_normal("R"))
    bracer = lathe("Bracer", "leather", [(0.036, 0.11), (0.040, 0.10), (0.037, 0.03), (0.034, 0.015)], 20)
    C.place(bracer, frame)
    C.PARTS.append((bracer, "forearm.R"))
    return scarf, tail, coats


def build_gauntlet():
    """The arcane gauntlet on the left forearm and hand, built in the forearm's frame
    (-Y toward the hand, +Z on the back of the hand)."""
    el, wr = C.J["elbow.L"], C.J["wrist.L"]
    G = C.frame_along(wr, wr - el, C.hand_normal("L"))
    fore = [
        lathe("Gauntlet bracer", "brass", [(0.041, 0.19), (0.048, 0.18), (0.047, 0.11), (0.044, 0.03), (0.046, 0.012), (0.041, 0.0)], 28),
        lathe("Gauntlet glow band", "glow", [(0.0485, 0.072), (0.0485, 0.058)], 28),
        lathe("Gauntlet teal band", "jacket", [(0.049, 0.15), (0.049, 0.13)], 28),
        box("Bracer ridge", "brass", (0.016, 0.15, 0.012), (0, 0.10, 0.047), 0.004),
    ]
    hand = [
        box("Hand plate", "brass", (0.058, 0.075, 0.016), (0, -0.045, 0.022), 0.006),
        torus("Gem ring", "brass", 0.019, 0.0045, (0, -0.045, 0.031), (0, 0, 0), (1, 1, 1), 20),
        ball_mesh("Gauntlet gem", "glow", (0, -0.045, 0.033), (0.015, 0.015, 0.010), 16, 8),
        box("Knuckle guard", "brass", (0.06, 0.02, 0.018), (0, -0.092, 0.014), 0.005),
        box("Finger guard", "brass", (0.055, 0.03, 0.012), (0, -0.118, 0.010), 0.004),
        ball_mesh("Palm crystal", "glow", (0, -0.05, -0.018), (0.013, 0.013, 0.004), 12, 6),
    ]
    for o in fore:
        C.place(o, G)
        C.PARTS.append((o, "forearm.L"))
    for o in hand:
        C.place(o, G)
        C.PARTS.append((o, "hand.L"))
    return G


# ---------------------------------------------------------------- head, hair, goggles


def build_head():
    def extra(meta, h):
        ball(meta, h + Vector((0, -0.03, -0.06)), 0.05, (1.15, 0.8, 0.6))  # jaw line
        for sx in (1, -1):
            ball(meta, h + Vector((0.05 * sx, -0.05, -0.035)), 0.026, (0.9, 0.8, 0.8))  # cheekbones

    C.build_head("Ezreal head", jaw=1.06, chin=1.15, cheek=0.98, nose=1.12, width=0.98, extra=extra)
    C.build_face(eye_size=0.9, lashes="soft", brow_mat="hair_dark", brow_width=0.0026, brow_lift=0.002, brow_angle=0.05, mouth="smirk", mouth_width=1.15, mouth_size=0.0023)


def build_hair():
    """Sculpted clumps (metaballs) merged into one hair mass: a big swoop rising off the
    forehead and sweeping back toward his right, short sides and a tapered nape."""
    h = C.HEAD

    def volume(meta, h):
        ball(meta, h + Vector((0, -0.005, 0.10)), 0.075, (1.1, 1.0, 0.8))

    C.hair_cap("Ezreal hair cap", "hair_dark", front_y=0.04, front_z=0.06, scale=1.03, extra=volume)
    meta = metaball_object("Ezreal hair", resolution=0.004)
    # The quiff: one big wave off the forehead, rolling up and back toward his right.
    C.clump(meta, [h + Vector((0.035, -0.082, 0.07)), h + Vector((0.01, -0.112, 0.125)), h + Vector((-0.03, -0.095, 0.172)), h + Vector((-0.075, -0.045, 0.185))], 0.038, 0.014)
    C.clump(meta, [h + Vector((0.07, -0.07, 0.075)), h + Vector((0.055, -0.095, 0.13)), h + Vector((0.02, -0.075, 0.175))], 0.026, 0.01)
    # Spikes along its crest and over the crown, tips swept back and to his right.
    for k, (x, y, z) in enumerate(((0.045, -0.085, 0.16), (0.012, -0.10, 0.17), (-0.025, -0.085, 0.185), (-0.06, -0.05, 0.19), (0.04, -0.02, 0.17), (-0.01, 0.0, 0.175))):
        root = h + Vector((x, y, z))
        tip = root + Vector((-0.05 - 0.01 * (k % 2), 0.035 + 0.02 * (k > 3), 0.025 - 0.012 * (k % 3)))
        C.clump(meta, [root, root.lerp(tip, 0.5) + Vector((0, 0, 0.012)), tip], 0.017, 0.003)
    # Short sides swept back, a tapered nape and a loose lock over the right brow.
    for sx in (1, -1):
        C.clump(meta, [h + Vector((0.083 * sx, -0.045, 0.065)), h + Vector((0.10 * sx, 0.0, 0.03)), h + Vector((0.097 * sx, 0.05, -0.03))], 0.02, 0.006)
        C.clump(meta, [h + Vector((0.08 * sx, -0.06, 0.03)), h + Vector((0.087 * sx, -0.055, -0.02)), h + Vector((0.085 * sx, -0.05, -0.05))], 0.011, 0.004)
    for x0 in (0.05, 0.0, -0.05):
        C.clump(meta, [h + Vector((x0, 0.07, 0.10)), h + Vector((x0, 0.108, 0.0)), h + Vector((x0 * 0.8, 0.09, -0.085))], 0.028, 0.008)
    C.clump(meta, [h + Vector((-0.012, -0.096, 0.088)), h + Vector((-0.036, -0.113, 0.052)), h + Vector((-0.052, -0.104, 0.018))], 0.013, 0.003)
    hair = C.mesh_from_meta(meta, "Ezreal hair", voxel=0.0035, smooth=3, tris=7000)
    C.paint_regions(hair, lambda c: "hair" if c.z > h.z + 0.03 or c.y < h.y - 0.07 else "hair_dark", ["hair", "hair_dark"])
    C.PARTS.append((hair, "head"))
    # Goggles pushed up on the hair, behind the swoop: strap around the head, brass-rimmed lenses.
    C.PARTS.append((torus("Goggle strap", "leather", 0.113, 0.008, h + Vector((0, 0.025, 0.09)), (math.radians(-26), 0, 0), (1.0, 1.06, 1.0), 40), "head"))
    for sx in (1, -1):
        centre = h + Vector((0.045 * sx, -0.055, 0.162))
        tilt = (math.radians(-30), math.radians(10 * sx), math.radians(-12 * sx))
        C.PARTS.append((cyl("Goggle rim", "brass", 0.028, 0.02, centre, tilt, 24), "head"))
        C.PARTS.append((cyl("Goggle lens", "lens", 0.022, 0.022, centre, tilt, 24), "head"))
    tube("Goggle bridge", [h + Vector((0.019, -0.065, 0.164)), h + Vector((0, -0.067, 0.167)), h + Vector((-0.019, -0.065, 0.164))], 0.004, "brass")


# ---------------------------------------------------------------- effects (preview videos only)


def fx_flash(name, radius, mat="glow", spikes=6):
    parts = [ball_mesh(f"FX {name}", mat, (0, 0, 0), (radius, radius, radius), 16, 8)]
    for i in range(spikes):
        a = i * 2 * math.pi / spikes
        parts.append(C.cone("FX spike", mat, radius * 0.3, 0.0, radius * 3.0, (math.cos(a) * radius * 1.3, -radius * 0.4, math.sin(a) * radius * 1.3), (math.pi / 2 - 0.5 * math.sin(a), 0.5 * math.cos(a), 0), 4))
    return C.join(parts, f"FX {name}")


def fx_bolt(name, length, radius, mat="glow", core_mat=None):
    """A projectile along -Y: glowing spindle with a tapering trail behind it."""
    body = lathe(f"FX {name}", mat, [(0.0, -length * 0.5), (radius, -length * 0.3), (radius * 0.8, 0.0), (radius * 0.35, length * 0.5), (0.0, length * 0.9)], 16)
    parts = [body]
    if core_mat:
        parts.append(ball_mesh("FX core", core_mat, (0, -length * 0.25, 0), (radius * 0.6, length * 0.25, radius * 0.6), 12, 6))
    for k in (0.15, 0.4):
        parts.append(torus("FX ring", mat, radius * 1.4, radius * 0.12, (0, length * k, 0), (math.pi / 2, 0, 0), (1, 1, 1), 16))
    return C.join(parts, f"FX {name}")


def fx_beam(name, length, radius):
    parts = [
        cyl(f"FX {name}", "gold_glow", radius, length, (0, -length / 2, 0), C.X90, 20),
        cyl("FX beam core", "glow", radius * 0.45, length * 1.02, (0, -length / 2, 0), C.X90, 12),
        lathe("FX beam head", "gold_glow", [(0.0, -length - radius * 2.5), (radius * 1.5, -length), (radius, -length + radius)], 20),
    ]
    for k in range(5):
        parts.append(torus("FX beam ring", "gold_glow", radius * 1.6, radius * 0.1, (0, -length * (0.15 + 0.17 * k), 0), (math.pi / 2, 0, 0), (1, 1, 1), 20))
    return C.join(parts, f"FX {name}")


def fx_orb(name, radius, mat):
    parts = [ball_mesh(f"FX {name}", mat, (0, 0, 0), (radius, radius, radius), 20, 10)]
    parts.append(torus("FX orb ring", mat, radius * 1.6, radius * 0.08, (0, 0, 0), (math.pi / 2, 0.4, 0), (1, 1, 1), 24))
    parts.append(torus("FX orb ring", mat, radius * 1.5, radius * 0.08, (0, 0, 0), (0.3, 1.2, 0), (1, 1, 1), 24))
    return C.join(parts, f"FX {name}")


# ---------------------------------------------------------------- assembly


def build():
    C.make_joints(scale=S, shoulder_x=0.20, hip_x=0.090)
    materials()
    body = build_body()
    scarf, scarf_path, coats = build_clothes()
    G = build_gauntlet()
    build_head()
    build_hair()
    C.scale_parts("head", 1.08, C.J["head_bone"])  # stylized: a slightly larger head

    palm = G @ Matrix.Translation((0, -0.05, -0.03))  # cast point, in front of the palm
    ahead = Matrix.Translation(palm.translation)  # projectiles travel along -Y (forward)
    fx = {
        "fx_palm": (fx_flash("palm flare", 0.035), palm, "hand.L"),
        "fx_bolt": (fx_bolt("bolt", 0.22, 0.028), ahead, None),
        "fx_mystic": (fx_bolt("mystic shot", 0.42, 0.045, "glow", "gold_glow"), ahead, None),
        "fx_flux": (fx_orb("essence flux", 0.06, "gold_glow"), ahead, None),
        "fx_beam": (fx_beam("trueshot beam", 1.8, 0.075), ahead, None),
        "fx_charge": (fx_orb("charge", 0.05, "glow"), ahead, None),
        "fx_blink_a": (fx_flash("blink out", 0.12, "glow", 8), Matrix.Translation(B(0, 0, 0.9)), None),
        "fx_blink_b": (fx_flash("blink in", 0.12, "glow", 8), Matrix.Translation(B(0, 0, 0.9)), None),
    }
    ring = torus("FX power ring", "glow", 0.07, 0.006, (0, 0.05, 0), (math.pi / 2, 0, 0), (1, 1, 1), 28)
    ring2 = torus("FX power ring", "glow", 0.06, 0.005, (0, 0.12, 0), (math.pi / 2, 0, 0), (1, 1, 1), 28)
    fx["fx_ring"] = (C.join([ring, ring2], "FX power rings"), G, "forearm.L")
    for name, (obj, matrix, _) in fx.items():
        C.place(obj, matrix @ (Matrix.Rotation(math.pi, 4, "X") if name == "fx_palm" else Matrix()))

    chains = [
        ("scarf", C.resample(scarf_path, 4), "chest", dict(skin=True, stiffness=55, gain=1.1, sway=4.0, limit=(45, 30), scale=0.6)),
        ("coat.L", C.resample(coats["L"][0], 3), "hips", dict(skin=True, stiffness=80, gain=0.7, sway=1.5, limit=(30, 15))),
        ("coat.R", C.resample(coats["R"][0], 3), "hips", dict(skin=True, stiffness=80, gain=0.7, sway=1.5, limit=(30, 15))),
    ]
    extra = [C.point_bone(name, matrix, parent) for name, (_, matrix, parent) in fx.items()]
    C.SOCKETS["socket_muzzle"] = ("hand.L", palm)
    C.SKINNED.append((scarf, ["chest", "scarf.0", "scarf.1", "scarf.2", "scarf.3"]))
    for side in ("L", "R"):
        C.SKINNED.append((coats[side][1], ["hips"] + [f"coat.{side}.{i}" for i in range(3)]))
    C.build_rig("Ezreal rig", chains, extra)
    C.bind(body)
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips()


# ---------------------------------------------------------------- clips (24 fps)


FX = ("fx_palm", "fx_bolt", "fx_mystic", "fx_flux", "fx_beam", "fx_charge", "fx_blink_a", "fx_blink_b", "fx_ring")


def define_clips():
    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def stance(frame, breath=0.0, sway=0.0):
        """Relaxed, cocky stance: weight on the right leg, gauntlet hand loose in front."""
        loc("hips", frame, x=-0.015 - 0.008 * sway, z=-0.018 - 0.004 * breath)
        rot("hips", frame, y=-3 - sway, z=6)
        rot("spine", frame, x=1 + breath, y=2, z=-3)
        rot("chest", frame, x=-2 + 1.5 * breath, y=1, z=-3 + sway)
        rot("neck", frame, z=2)
        rot("head", frame, x=-3 + breath, y=-4 + 2 * sway, z=8 - 2 * sway)
        rot("shoulder.L", frame, z=3 + 1.5 * breath)
        rot("shoulder.R", frame, z=-3 - 1.5 * breath)
        C.feet(frame, (0.035, -0.07, 0, -14), (-0.015, 0.05, 0, 18))
        fk_arm("L", frame, up=6 + 2 * breath, swing=-14, bend=50, out=-4, twist=30, hand=-10)
        fk_arm("R", frame, up=36, swing=12, bend=105, twist=85, hand=10)
        loc("root", frame)
        rot("root", frame)

    def start(frame=0):
        stance(frame)
        fx_off(frame)

    def aim_left(frame, up=0.0, out=0.0, bend=8, hand=-55):
        """Left arm thrust forward, palm out."""
        fk_arm("L", frame, up=up, swing=-88, bend=bend, out=out, hand=hand)

    def shoot(name, frame_from, frame_to, start, distance=3.0, lift=0.0):
        """A projectile from start() straight ahead (-Y), shown between two frames; solved
        after the clip's other keys so it leaves the final pose."""
        size(name, frame_from - 1, 0.0)
        size(name, frame_from, 1.0)
        size(name, frame_to, 1.0)
        size(name, frame_to + 1, 0.0)

        @C.later
        def fly():
            start_co = start()
            put(name, frame_from, start_co)
            put(name, frame_to, start_co + Vector((0, -distance, lift)))

    def palm_point(frame):
        return C.carried("hand.L", frame, C.rig.data.bones["fx_palm"].head_local)

    @clip("Idle", 72, loop=True)
    def idle():
        for f, breath, sway in ((0, 0, 0), (18, 1, 0.5), (36, 0, 1), (54, 1, 0.5), (72, 0, 0)):
            stance(f, breath, sway)
        # The gauntlet hums: the palm flares softly twice per loop.
        fx_off(0)
        for f in (20, 56):
            size("fx_palm", f - 6, 0.0)
            size("fx_palm", f, 0.35)
            size("fx_palm", f + 6, 0.0)

    @clip("Walk", 18, loop=True)
    def run():
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
                    loc(f"ik_foot.{side}", frame, x=0.02 * C.side_x(side), y=y * S, z=z * S)
                    rot(f"ik_foot.{side}", frame, x=toe)
                twist = 10 if lead == "L" else -10
                bob = {0: -0.05, 2: -0.085, 4: -0.03, 6: 0.0}[f]
                loc("hips", frame, z=bob * S, y=-0.02)
                rot("hips", frame, z=twist, y=(3 if lead == "L" else -3))
                rot("spine", frame, x=10, z=-twist * 0.6)
                rot("chest", frame, x=4, z=-twist * 0.6)
                rot("head", frame, x=-8 + (2 if f == 2 else 0), z=twist * 0.35)
                # Arms swing opposite to the legs: the left arm is back while the left leg leads.
                arc = 36 * (1 if lead == "L" else -1) * {0: 1.0, 2: 0.8, 4: 0.1, 6: -0.55}[f]
                fk_arm("L", frame, up=14, swing=arc, bend=70, out=-4, hand=-5)
                fk_arm("R", frame, up=14, swing=-arc, bend=70, out=-4, hand=5)
        for frame in (0, 18):
            loc("ik_foot.L", frame, x=0.02, y=-0.30 * S, z=0.02 * S)
            rot("ik_foot.L", frame, x=10)
            loc("ik_foot.R", frame, x=-0.02, y=0.32 * S, z=0.16 * S)
            rot("ik_foot.R", frame, x=-55)
            loc("hips", frame, z=-0.05 * S, y=-0.02)
            rot("hips", frame, z=10, y=3)
            rot("spine", frame, x=10, z=-6)
            rot("chest", frame, x=4, z=-6)
            rot("head", frame, x=-8, z=3.5)
            fk_arm("L", frame, up=14, swing=36, bend=70, out=-4, hand=-5)
            fk_arm("R", frame, up=14, swing=-36, bend=70, out=-4, hand=5)
        fx_off(0)

    @clip("AA", 20)
    def attack():
        start()
        # Anticipation: draw the gauntlet back to the hip, turn the shoulders.
        fk_arm("L", 4, up=12, swing=10, bend=95, out=-10, hand=-30)
        rot("chest", 4, x=-1, z=10)
        rot("spine", 4, z=4)
        # Thrust: the arm snaps forward, palm out; bolt leaves the palm.
        aim_left(8, up=2, out=-6)
        rot("chest", 8, x=2, z=-14)
        rot("spine", 8, z=-6)
        rot("head", 8, x=-1, z=-6, y=-2)
        C.feet(8, (0.035, -0.10, 0, -14), (-0.015, 0.05, 0, 18))
        size("fx_palm", 7, 0.0)
        size("fx_palm", 8, 1.0)
        size("fx_palm", 11, 0.0)
        shoot("fx_bolt", 8, 13, lambda: palm_point(8), 2.6)
        # Recoil and settle.
        aim_left(11, up=8, out=-6, bend=20, hand=-40)
        rot("chest", 11, x=-1, z=-10)
        stance(20)

    @clip("Q", 24)
    def mystic_shot():
        start()
        # A bigger wind-up: step in, cock the gauntlet behind, then a full-body thrust.
        fk_arm("L", 5, up=20, swing=30, bend=110, out=-14, hand=-40)
        rot("chest", 5, x=-3, z=18)
        rot("spine", 5, z=6)
        rot("hips", 5, z=12)
        loc("hips", 5, x=-0.01, z=-0.04)
        size("fx_palm", 3, 0.0)
        size("fx_palm", 6, 0.5)  # charging glow
        aim_left(9, up=4, out=-4, bend=4)
        rot("chest", 9, x=4, z=-18)
        rot("spine", 9, x=4, z=-8)
        rot("hips", 9, z=-4)
        loc("hips", 9, y=-0.03, z=-0.05)
        C.feet(9, (0.04, -0.20, 0, -6), (-0.02, 0.10, 0, 22))
        fk_arm("R", 9, up=20, swing=30, bend=60, out=10, hand=10)
        size("fx_palm", 9, 1.4)
        size("fx_palm", 13, 0.0)
        shoot("fx_mystic", 9, 15, lambda: palm_point(9), 3.4)
        rot("head", 9, x=0, z=-10, y=-4)
        aim_left(13, up=10, out=-4, bend=18, hand=-40)
        rot("chest", 13, x=0, z=-12)
        stance(24)

    @clip("W", 26)
    def essence_flux():
        start()
        # Both hands gather energy at the chest, then push it forward.
        fk_arm("L", 6, up=6, swing=-48, bend=88, out=-22, twist=25, hand=-20)
        fk_arm("R", 6, up=6, swing=-48, bend=88, out=-22, twist=25, hand=-20)
        rot("chest", 6, x=-4, z=4)
        loc("hips", 6, z=-0.04)
        C.later(lambda: put("fx_flux", 6, C.carried("chest", 6, B(0, -0.24, 1.17))))
        size("fx_flux", 5, 0.0)
        size("fx_flux", 7, 0.5)
        C.later(lambda: put("fx_flux", 11, C.carried("chest", 11, B(0, -0.27, 1.18))))
        size("fx_flux", 11, 0.8)
        aim_left(14, up=8, out=-18, bend=10)
        fk_arm("R", 14, up=8, swing=-86, bend=10, out=-18, hand=-55)
        rot("chest", 14, x=5, z=-2)
        rot("spine", 14, x=4)
        loc("hips", 14, y=-0.03, z=-0.05)
        C.feet(14, (0.04, -0.14, 0, -8), (-0.03, 0.09, 0, 15))
        shoot("fx_flux", 14, 21, lambda: C.carried("chest", 14, B(0, -0.55, 1.25)), 3.0)
        size("fx_flux", 14, 1.2)
        fk_arm("L", 18, up=12, swing=-75, bend=25, out=-14, hand=-40)
        fk_arm("R", 18, up=12, swing=-75, bend=25, out=-14, hand=-40)
        stance(26)

    @clip("E", 30)
    def arcane_shift():
        start()
        moving = bool(C.OPTIONS.get("root_motion"))
        # Crouch, vanish in a flash, reappear (further ahead in preview videos) and fire a bolt.
        loc("hips", 4, z=-0.07)
        rot("spine", 4, x=10)
        fk_arm("L", 4, up=25, swing=-20, bend=80, out=-10, hand=-20)
        size("root", 5, 1.0)
        size("root", 8, 0.0)
        put("fx_blink_a", 6, B(0, 0, 0.9))
        size("fx_blink_a", 5, 0.0)
        size("fx_blink_a", 7, 1.2)
        size("fx_blink_a", 11, 0.0)
        if moving:
            loc("root", 8)
            loc("root", 12, y=-1.2)
        size("root", 12, 0.0)
        put("fx_blink_b", 13, B(0, -1.2 if moving else 0, 0.9))
        size("fx_blink_b", 12, 0.0)
        size("fx_blink_b", 14, 1.2)
        size("fx_blink_b", 18, 0.0)
        size("root", 15, 1.0)
        loc("hips", 15, z=-0.06)
        rot("spine", 15, x=6)
        aim_left(18, up=6, out=-8)
        rot("chest", 18, z=-12)
        size("fx_palm", 17, 0.0)
        size("fx_palm", 18, 1.0)
        size("fx_palm", 21, 0.0)
        shoot("fx_bolt", 18, 23, lambda: palm_point(18), 2.4)
        stance(30)
        if moving:
            loc("root", 30, y=-1.2)

    @clip("R", 52)
    def trueshot_barrage():
        start()
        # Wide stance, both hands drawn back to the hip charging a growing orb, a lean back,
        # then a two-handed release that throws him back a step.
        C.feet(8, (0.10, -0.14, 0, -20), (-0.08, 0.16, 0, 30))
        loc("hips", 8, x=0.0, z=-0.10)
        rot("hips", 8, z=24)
        rot("spine", 8, x=4, z=10)
        rot("chest", 8, x=-6, z=16)
        fk_arm("L", 8, up=15, swing=20, bend=110, out=-20, hand=-30)
        fk_arm("R", 8, up=15, swing=15, bend=115, out=-25, hand=-30)
        size("fx_charge", 6, 0.0)
        C.later(lambda: put("fx_charge", 8, C.carried("hips", 8, B(-0.05, -0.20, 1.0))))
        size("fx_charge", 8, 0.4)
        C.later(lambda: put("fx_charge", 26, C.carried("hips", 26, B(-0.05, -0.22, 1.02))))
        size("fx_charge", 26, 1.6)
        for k, f in enumerate(range(12, 27, 3)):  # trembling charge
            rot("chest", f, x=-6 + (1 if k % 2 else 0), z=16 + (1.5 if k % 2 else 0))
        rot("head", 24, x=6, z=10)
        # Release.
        aim_left(29, up=6, out=-14, bend=6)
        fk_arm("R", 29, up=6, swing=-88, bend=6, out=-14, hand=-55)
        rot("hips", 29, z=0)
        rot("spine", 29, x=6, z=-4)
        rot("chest", 29, x=6, z=-6)
        rot("head", 29, x=0, z=-4)
        loc("hips", 29, y=-0.04, z=-0.09)
        size("fx_charge", 28, 1.6)
        size("fx_charge", 29, 0.0)
        size("fx_beam", 28, 0.0)
        C.later(lambda: put("fx_beam", 29, C.carried("chest", 29, B(0, -0.65, 1.22))))
        size("fx_beam", 29, 1.0)
        C.later(lambda: put("fx_beam", 40, C.carried("chest", 29, B(0, -4.5, 1.22))))
        size("fx_beam", 40, 1.0)
        size("fx_beam", 41, 0.0)
        size("fx_palm", 28, 0.0)
        size("fx_palm", 29, 2.0)
        size("fx_palm", 35, 0.0)
        # Kickback.
        loc("hips", 33, y=0.06, z=-0.08)
        rot("chest", 33, x=-8, z=-4)
        rot("head", 33, x=-8)
        aim_left(33, up=22, out=-14, bend=25, hand=-30)
        fk_arm("R", 33, up=22, swing=-70, bend=25, out=-14, hand=-30)
        C.feet(34, (0.10, -0.08, 0, -20), (-0.08, 0.22, 0, 30))
        stance(52)

    @clip("P", 36)
    def rising_spell_force():
        start()
        # A cocky power-up: raise the gauntlet, clench, rings of energy run up the arm.
        fk_arm("L", 8, up=55, swing=-60, bend=120, out=-10, hand=-10)
        rot("chest", 8, x=-4, z=8)
        rot("head", 10, x=2, z=18, y=-6)
        size("fx_ring", 7, 0.0)
        for k, f in enumerate((10, 16, 22)):
            size("fx_ring", f, 1.0 + 0.3 * k)
            size("fx_ring", f + 3, 0.6)
        size("fx_ring", 27, 0.0)
        size("fx_palm", 9, 0.0)
        size("fx_palm", 12, 0.9)
        size("fx_palm", 24, 0.9)
        size("fx_palm", 28, 0.0)
        fk_arm("L", 14, up=60, swing=-62, bend=128, out=-12, hand=-25)
        rot("head", 24, x=-2, z=14, y=-10)
        stance(36)

    @clip("Recall", 48, loop=True)
    def recall():
        # Polishing the gauntlet: left arm raised, right hand rubbing it, a glance and a grin.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.5)
            fk_arm("L", f, up=12, swing=-58, bend=100, out=-30, twist=40, hand=-15)
            fk_arm("R", f, up=14 + 2 * s_, swing=-52, bend=104 + 5 * s_, out=-36, twist=40 + 4 * s_, hand=0)
            rot("chest", f, x=4, z=8)
            rot("head", f, x=16, z=10 + 3 * s_, y=-4)
        fx_off(0)
        size("fx_palm", 18, 0.0)
        size("fx_palm", 24, 0.5)
        size("fx_palm", 30, 0.0)

    @clip("Death", 44)
    def death():
        start()
        rot("chest", 3, x=-14, z=8)
        rot("head", 3, x=-18, z=-6)
        fk_arm("L", 6, up=-20, swing=25, bend=40, out=10)
        fk_arm("R", 6, up=-15, swing=25, bend=50)
        loc("ik_foot.R", 9, x=-0.04, y=0.22)
        loc("hips", 9, y=0.05, z=-0.06)
        loc("hips", 16, y=0.08, z=-0.30)
        rot("spine", 16, x=14)
        rot("chest", 16, x=8)
        rot("head", 16, x=12, z=-10)
        rot("root", 16)
        rot("root", 30, x=-88)
        loc("root", 30, y=0.26, z=0.12)
        loc("hips", 30, z=-0.20)
        rot("spine", 30, x=-4)
        rot("chest", 30, x=-6)
        rot("head", 33, x=-6, z=-25)
        fk_arm("L", 30, up=-60, swing=-30, bend=10, out=30)
        fk_arm("R", 30, up=-50, swing=-20, bend=15, out=-20)
        rot("root", 34, x=-92)
        rot("root", 44, x=-90)
        loc("root", 44, y=0.26, z=0.12)
