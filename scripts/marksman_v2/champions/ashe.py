"""Ashe: an original stylized interpretation (ivory hood, layered navy mantle and cape, pale
braided hair, frost crystal longbow)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, fk_arm, flash, ik, lathe, loc, material, metaball_object, placement, rot, size, torus, tube, weapon_matrix

S = 1.04
RIM = (0.55, 0.85, 1.0)
EXPOSURE = -0.2
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#e3c8b6", rough=0.5, sss=0.2),
        navy=material("Navy mantle", "#152d59", rough=0.6),
        blue=material("Frost blue", "#719ecb", rough=0.55),
        ivory=material("Ivory", "#d8e9ef", rough=0.6),
        fur=material("White fur", (0.85, 0.86, 0.88), rough=0.9),
        gold=material("Gold", "#b8a275", rough=0.3, metal=1.0),
        leggings=material("Leggings", (0.02, 0.03, 0.06), rough=0.6),
        hair=material("Pale hair", (0.80, 0.80, 0.82), rough=0.45),
        hair_dark=material("Pale hair shadow", (0.55, 0.58, 0.65), rough=0.5),
        ice=material("Frost crystal", "#82efff", rough=0.08, metal=0.1, emission=1.2),
        glow=material("Frost glow", "#82efff", emission=7.0),
        string=material("Bow string", (0.9, 0.95, 1.0), emission=2.0),
    )
    C.face_materials(iris=(0.25, 0.55, 0.85), lash=(0.05, 0.05, 0.07), lip=(0.62, 0.36, 0.38))


def build_body():
    meta = metaball_object("Ashe body")
    C.torso_female(meta, S, bust=0.95, hips=0.98, waist=0.95)
    C.limbs(meta, dict(thigh=(0.062, 0.040), calf=(0.040, 0.046, 0.03), arm=(0.042, 0.031), forearm=(0.034, 0.026), palm=0.033), hands="mitten")
    for side in ("L", "R"):
        knee, ankle, toe = (C.J[f"{n}.{side}"] for n in ("knee", "ankle", "toe"))
        ball(meta, knee + Vector((0, -0.012, 0.02 * S)), 0.05 * S, (1.0, 1.0, 0.55))  # boot top
        ball(meta, toe + Vector((0, 0.01, 0.004)), 0.034 * S, (0.9, 1.25, 0.7))
        el, wr = C.J[f"elbow.{side}"], C.J[f"wrist.{side}"]
        ball(meta, el.lerp(wr, 0.6), 0.037 * S, (1.0, 1.0, 1.0))  # bracer volume
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.52, 0.86, 0.95, 1.40)]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.42, 0.55, 0.80)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            f = C.arm_fraction(c, side)
            return "ivory" if f > 0.80 else "gold" if 0.55 < f < 0.58 else "blue" if f > 0.42 else "navy"
        if z < 0.52:
            return "ivory"
        if z < 0.86:
            return "leggings"
        if z < 0.95:
            return "gold"
        if z > 1.40 and math.hypot(x, y - 0.01) < 0.065:
            return "skin"
        return "navy"

    return C.body_mesh(meta, "Ashe body", region, ["skin", "navy", "blue", "ivory", "gold", "leggings"], cuts)


def build_clothes():
    h = C.HEAD
    # The hood: a shell around the head with the face open, draping onto the shoulders.
    meta = metaball_object("Hood", resolution=0.006)
    ball(meta, h + Vector((0, 0.025, 0.035)), 0.125, (1.0, 1.05, 1.08))
    ball(meta, h + Vector((0, 0.07, -0.06)), 0.10, (1.1, 0.9, 1.2))
    for sx in (1, -1):
        ball(meta, h + Vector((0.085 * sx, 0.0, -0.08)), 0.065, (0.8, 1.2, 1.4))
        ball(meta, B(0.13 * sx, 0.03, 1.40), 0.07, (1.3, 1.1, 0.6))
    ball(meta, B(0, 0.08, 1.42), 0.09, (1.4, 0.9, 0.7))
    hood = C.mesh_from_meta(meta, "Hood", voxel=0.006, smooth=3, tris=5000)
    C.delete_faces(hood, lambda c: (c.y < h.y - 0.02 and abs(c.x) < 0.085 and h.z - 0.16 < c.z < h.z + 0.10) or c.z < 1.36 * S)
    C.solidify(hood, 0.008)
    hood.data.materials.append(M["ivory"])
    C.SKINNED.append((hood, ["head", "neck", "chest"]))
    trim = [h + Vector((math.sin(a) * 0.09, -0.035 - math.cos(a) * 0.01, 0.0 + math.cos(a) * 0.105)) for a in (math.radians(d) for d in range(-100, 101, 20))]
    C.PARTS.append((tube("Hood trim", trim, 0.008, "gold", False), "head"))
    # Mantle: layered navy capelet over the shoulders with a fur collar.
    meta = metaball_object("Mantle", resolution=0.007)
    for sx in (1, -1):
        ball(meta, B(0.15 * sx, 0.012, 1.35), 0.085, (1.2, 1.15, 0.7))
    ball(meta, B(0, 0.05, 1.32), 0.12, (1.3, 0.9, 0.8))
    ball(meta, B(0, -0.045, 1.30), 0.10, (1.25, 0.8, 0.75))
    mantle = C.mesh_from_meta(meta, "Mantle", voxel=0.007, smooth=3, tris=4000)
    C.delete_faces(mantle, lambda c: c.z < 1.21 * S or c.z > 1.43 * S)
    C.solidify(mantle, 0.008)
    mantle.data.materials.append(M["navy"])
    C.SKINNED.append((mantle, ["chest", "shoulder.L", "shoulder.R"]))
    fur = C.torus("Fur collar", "fur", 0.085 * S, 0.028 * S, B(0, 0.015, 1.415), (math.radians(-6), 0, 0), (1.05, 0.95, 0.6), 28)
    C.PARTS.append((fur, "chest"))
    # Long cape down the back on a spring chain, and tunic tails over the leggings.
    cape_pts = [B(0, 0.10, 1.40), B(0, 0.15, 1.10), B(0, 0.17, 0.80), B(0, 0.18, 0.50), B(0, 0.18, 0.30)]
    cape = C.ribbon("Cape", cape_pts, 0.36 * S, "navy", (1, 0, 0), 0.008, [0.75, 1.0, 1.1, 1.2, 1.25], bone=False)
    panels = C.coat_panels(
        [
            ("tail.F", 0.0, -0.105, 0.13, 0.94, 0.58, 0.0),
            ("tail.L", 0.115, 0.02, 0.10, 0.94, 0.60, 0.04),
            ("tail.R", -0.115, 0.02, 0.10, 0.94, 0.60, 0.04),
        ],
        "blue",
        S,
    )
    belt = [
        C.torus("Belt", "gold", 0.12 * S, 0.010 * S, B(0, 0.01, 0.95), (0, 0, 0), (1.0, 0.78, 1.0), 40),
        ball_mesh("Belt gem", "glow", B(0, -0.093, 0.95), (0.012, 0.006, 0.012), 12, 6),
    ]
    for o in belt:
        C.PARTS.append((o, "hips"))
    return cape_pts, cape, panels


def build_head():
    C.build_head("Ashe head", jaw=0.95, chin=0.95, nose=0.92)
    C.build_face(eye_size=1.0, lashes="winged", brow_mat="hair_dark", brow_width=0.0018, brow_angle=0.06, mouth="flat", mouth_size=0.0018)
    h = C.HEAD
    C.hair_cap("Ashe hair", "hair", front_y=0.04, front_z=0.05)
    meta = metaball_object("Ashe fringe", resolution=0.004)
    for i, x in enumerate((0.05, 0.02, -0.01, -0.04)):
        C.clump(meta, [h + Vector((x * 0.5, -0.07, 0.10)), h + Vector((x, -0.10, 0.06)), h + Vector((x * 1.2, -0.097, 0.02 - 0.005 * i))], 0.016, 0.004, flat=0.6)
    for sx in (1, -1):
        C.clump(meta, [h + Vector((0.075 * sx, -0.06, 0.06)), h + Vector((0.092 * sx, -0.06, -0.03)), h + Vector((0.088 * sx, -0.045, -0.10))], 0.018, 0.005, flat=0.6)
    fringe = C.mesh_from_meta(meta, "Ashe fringe", voxel=0.0035, smooth=3, tris=3000)
    fringe.data.materials.append(M["hair"])
    C.PARTS.append((fringe, "head"))
    # A long braid falling over her left shoulder, out of the hood.
    path = [h + Vector((0.07, -0.02, -0.07)), h + Vector((0.10, -0.05, -0.15)), B(0.12, -0.075, 1.34), B(0.13, -0.09, 1.22), B(0.13, -0.095, 1.08)]
    lobes = C.braid_lobes(path, radius=0.024, taper=0.35, twist=36)
    tie = ball_mesh("Braid tie", "gold", path[-1] + Vector((0, 0, -0.008)), (0.012, 0.012, 0.01), 12, 6)
    return path, lobes + [tie]


def build_bow():
    """Frost crystal longbow: grip at the origin, aim toward -Y, limbs along Z, string at +Y."""
    arc = [Vector((0, 0.16 * (abs(z) / 0.7) ** 1.6, z)) for z in (-0.70, -0.55, -0.35, -0.15, 0.0, 0.15, 0.35, 0.55, 0.70)]
    parts = [tube("Bow limbs", arc, 0.016, "ice", False, taper=[0.35, 0.7, 0.95, 1.1, 1.2, 1.1, 0.95, 0.7, 0.35], resolution=8)]
    parts.append(lathe("Bow grip", "gold", [(0.021, -0.07), (0.024, -0.06), (0.024, 0.06), (0.021, 0.07)], 16, "Z"))
    parts.append(ball_mesh("Bow gem", "glow", (0, -0.022, 0.0), (0.012, 0.008, 0.016), 12, 6))
    for sz in (1, -1):
        tip = Vector((0, 0.16, 0.70 * sz))
        parts.append(C.cone("Crystal tip", "ice", 0.02, 0.0, 0.10, tip + Vector((0, -0.01, 0.04 * sz)), (0 if sz > 0 else math.pi, 0, 0), 5))
        for k in range(3):
            z = (0.25 + 0.15 * k) * sz
            y = 0.16 * (abs(z) / 0.7) ** 1.6
            parts.append(C.cone("Crystal shard", "ice", 0.012, 0.0, 0.07, (0.0, y - 0.03, z), (math.radians(-60 if sz > 0 else -120), 0, 0), 4))
    return C.join(parts, "Frost bow")


def build_arrow(name, length=0.78, mat="ice", radius=0.006):
    """An arrow along -Y with its nock at the origin."""
    parts = [
        C.cyl(name, "gold", radius, length * 0.9, (0, -length * 0.45, 0), C.X90, 8),
        C.cone("Arrow head", mat, radius * 3.2, 0.0, 0.07, (0, -length * 0.93, 0), (-math.pi / 2, 0, 0), 6),
    ]
    for k in range(3):
        a = k * 2 * math.pi / 3
        parts.append(C.plate("Fletching", "ivory", [(0, -0.015, 0), (math.cos(a) * 0.022, -0.03, math.sin(a) * 0.022), (math.cos(a) * 0.02, -0.11, math.sin(a) * 0.02), (0, -0.12, 0)], 0.002, 0.0))
    return C.join(parts, name)


def build_hawk():
    parts = [ball_mesh("FX hawk", "glow", (0, 0, 0), (0.04, 0.10, 0.035), 12, 6), C.cone("FX beak", "glow", 0.015, 0.0, 0.05, (0, -0.12, 0.005), (-math.pi / 2, 0, 0), 4)]
    for sx in (1, -1):
        parts.append(C.plate("FX wing", "glow", [(0.03 * sx, -0.03, 0.01), (0.30 * sx, 0.02, 0.06), (0.26 * sx, 0.08, 0.04), (0.03 * sx, 0.05, 0.01)], 0.006, 0.0))
    parts.append(C.plate("FX tail", "glow", [(0, 0.08, 0.0), (0.05, 0.20, 0.0), (-0.05, 0.20, 0.0)], 0.006, 0.0))
    return C.join(parts, "FX hawk")


# ---------------------------------------------------------------- assembly

REST_BOW = Matrix.Translation(Vector((0.205, -0.10, 0.93)) * S) @ Matrix.Rotation(math.radians(35), 4, "X")
BRACE = 0.16  # string distance behind the grip
DRAW = 0.42  # extra draw at full pull


def build():
    C.make_joints(scale=S, shoulder_x=0.176, hip_x=0.094)
    materials()
    body = build_body()
    cape_pts, cape, panels = build_clothes()
    braid_path, braid = build_head()
    C.scale_parts("head", 1.06, C.J["head_bone"])
    bow = build_bow()
    C.place(bow, REST_BOW)
    nock_rest = REST_BOW @ Matrix.Translation((0, BRACE, 0))
    string_pts = [REST_BOW @ Vector((0, BRACE, 0.70)), nock_rest.translation, REST_BOW @ Vector((0, BRACE, -0.70))]
    string = tube("Bow string", string_pts, 0.0025, "string", False, resolution=12, bevel=1)
    arrow = build_arrow("Nocked arrow")
    C.place(arrow, nock_rest)

    fx = {f"fx_arrow.{k}": (build_arrow(f"FX arrow {k}", mat="glow"), None, None) for k in range(7)}
    fx["fx_crystal"] = (C.join([build_arrow("FX crystal arrow", 1.2, "glow", 0.012), ball_mesh("FX crystal head", "glow", (0, -1.1, 0), (0.06, 0.16, 0.06), 12, 6)], "FX crystal arrow"), None, None)
    fx["fx_hawk"] = (build_hawk(), None, None)
    fx["fx_frost"] = (C.fx_flash("frost burst", 0.05, "glow", 6), REST_BOW @ Matrix.Translation((0, -0.06, 0)), "bow")
    fx["fx_bowglow"] = (C.fx_orb("bow glow", 0.05, "glow", 1), REST_BOW, "bow")
    extra = [
        C.weapon_bones("bow", REST_BOW, (0, 0, 0), "hips", 0.2),
        C.grip_bone("grip_bow.L", REST_BOW.translation, "bow"),
        C.point_bone("nock", nock_rest, "bow", 0.05),
        C.point_bone("arrow", nock_rest, "nock", 0.1),
    ]
    extra += C.fx_bones(fx, Matrix.Translation(B(0.1, -0.4, 1.4)))
    C.DEFORM_LATER += ["bow", "nock"]

    def string_weights(co):
        local = REST_BOW.inverted() @ co
        w = max(0.0, 1.0 - abs(local.z) / 0.70)
        return {"nock": w, "bow": 1.0 - w} if w > 0 else {"bow": 1.0}

    C.SKINNED.append((string, string_weights))
    C.SKINNED.append((cape, ["chest"] + [f"cape.{i}" for i in range(4)]))
    chains = [("cape", C.resample(cape_pts, 4), "chest", dict(skin=True, stiffness=50, gain=1.0, sway=2.5, limit=(50, 20)))]
    chains += C.coat_chains(panels, stiffness=70, gain=0.7, sway=1.5, limit=(35, 15))
    chains.append(("braid", C.resample(braid_path, 5), "head", dict(stiffness=60, gain=1.0, sway=2.5, limit=(40, 30))))
    C.SOCKETS["socket_muzzle"] = ("bow", REST_BOW @ Matrix.Translation((0, -0.05, 0)))
    C.build_rig("Ashe rig", chains, extra, [("L", "bow", "grip_bow.L"), ("R", "draw", "nock")])
    C.bind(body)
    C.attach(bow, "bow")
    C.attach(arrow, "arrow")
    for obj in braid:
        C.attach_to_chain(obj, "braid")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips()


ARROWS = [f"fx_arrow.{k}" for k in range(7)]
FX = ARROWS + ["fx_crystal", "fx_hawk", "fx_frost", "fx_bowglow"]


def define_clips():
    aim_bow = placement("bow", B(0.05, -0.55, 1.48), rx=0, rz=0, roll=-8)
    sky_bow = placement("bow", B(0.08, -0.40, 1.62), rx=40, rz=0)

    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def stance(frame, breath=0.0, sway=0.0):
        """Poised archer: bow low in the left hand, right hand relaxed, weight on the back leg."""
        loc("hips", frame, x=-0.01 - 0.006 * sway, z=-0.02 - 0.004 * breath)
        rot("hips", frame, y=-2 - sway, z=4)
        rot("spine", frame, x=2 + breath, z=-2)
        rot("chest", frame, x=-2 + 1.5 * breath, z=-2 + sway)
        rot("head", frame, x=-3 + breath, y=-3 + sway, z=6 - 2 * sway)
        C.feet(frame, (0.03, -0.05, 0, -10), (-0.02, 0.05, 0, 16))
        loc("bow", frame)
        rot("bow", frame)
        loc("nock", frame)
        ik("L", "bow", frame, 1.0)
        ik("R", "draw", frame, 0.0)
        loc("pole_elbow.L", frame, x=0.1, y=0.1, z=-0.3)
        fk_arm("R", frame, up=6 + 2 * breath, swing=-6, bend=25, out=-2, twist=10, hand=-10)
        size("arrow", frame, 0.0)
        loc("root", frame)
        rot("root", frame)

    def full_draw(frame, matrix=None, amount=1.0):
        """Bladed stance, bow raised to the target, string drawn to the jaw."""
        rot("hips", frame, z=-16)
        loc("hips", frame, z=-0.03)
        rot("spine", frame, x=2, z=-12)
        rot("chest", frame, x=-2, z=-16)
        rot("head", frame, x=2, y=-4, z=40)
        C.feet(frame, (0.07, -0.12, 0, -30), (-0.05, 0.10, 0, 35))
        ik("L", "bow", frame, 1.0)
        ik("R", "draw", frame, 1.0)
        loc("pole_elbow.L", frame, x=0.3, y=0.1, z=-0.2)
        loc("pole_elbow.R", frame, x=-0.4, y=0.5, z=0.25)
        weapon_matrix("bow", matrix or aim_bow, frame)
        C.weapon_offset("bow", "nock", frame, (0, DRAW * amount, 0))
        size("arrow", frame, 1.0)

    def nock_arrow(frame):
        """Raise the bow, set an arrow (string at brace)."""
        rot("chest", frame, x=-1, z=-10)
        rot("hips", frame, z=-8)
        weapon_matrix("bow", aim_bow, frame)
        ik("L", "bow", frame, 1.0)
        ik("R", "draw", frame, 1.0)
        loc("pole_elbow.R", frame, x=-0.3, y=0.3, z=0.1)
        C.weapon_offset("bow", "nock", frame, (0, 0, 0))
        size("arrow", frame - 1, 0.0)
        size("arrow", frame, 1.0)

    def loose(frame, shot, distance=4.5, matrix=None):
        """Release: the arrow leaves, the string snaps forward, the draw hand flicks back."""
        size("arrow", frame, 0.0)
        C.weapon_offset("bow", "nock", frame, (0, -0.02, 0))
        C.weapon_offset("bow", "nock", frame + 2, (0, 0.01, 0))
        C.weapon_offset("bow", "nock", frame + 4, (0, 0, 0))
        ik("R", "draw", frame, 0.0)
        fk_arm("R", frame + 1, up=70, swing=-10, bend=120, out=-40, twist=-20, hand=10)
        m = matrix or aim_bow
        frame_m = C.weapon_frame("bow", m)
        C.shoot_from(shot, frame, frame + 6, lambda: frame_m @ Vector((0, -0.2, 0)), lambda: frame_m.to_3x3() @ Vector((0, -1, 0)), distance)

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
            arc = 30 * (1 if lead == "L" else -1) * phase
            fk_arm("R", frame, up=12, swing=-arc, bend=60, out=-4, hand=-5)
            loc("bow", frame)
            rot("bow", frame)
            ik("L", "bow", frame, 1.0)
            ik("R", "draw", frame, 0.0)
            size("arrow", frame, 0.0)

        C.run_cycle(upper, scale=S, lean=9, twist=9)
        fx_off(0)

    @clip("AA", 24)
    def attack():
        start()
        nock_arrow(4)
        full_draw(10)
        loose(13, ARROWS[0])
        stance(24)

    @clip("P", 28)
    def frost_shot():
        start()
        nock_arrow(4)
        full_draw(11)
        size("fx_bowglow", 8, 0.0)
        size("fx_bowglow", 13, 1.2)
        loose(14, ARROWS[0])
        flash("fx_frost", 14, 5, 1.6)
        size("fx_bowglow", 16, 0.0)
        stance(28)

    @clip("Q", 40)
    def rangers_focus():
        start()
        # The bow ices over, then three quick shots.
        size("fx_bowglow", 2, 0.0)
        size("fx_bowglow", 8, 1.5)
        size("fx_bowglow", 34, 1.2)
        size("fx_bowglow", 38, 0.0)
        for k, f in enumerate((6, 16, 26)):
            nock_arrow(f)
            full_draw(f + 4)
            loose(f + 6, ARROWS[k], 4.5)
        stance(40)

    @clip("W", 34)
    def volley():
        start()
        nock_arrow(5)
        full_draw(14)
        rot("chest", 14, x=-4, z=-18)
        size("arrow", 17, 0.0)
        C.weapon_offset("bow", "nock", 17, (0, -0.02, 0))
        ik("R", "draw", 17, 0.0)
        fk_arm("R", 18, up=70, swing=-10, bend=120, out=-40, twist=-20, hand=10)
        frame_m = C.weapon_frame("bow", aim_bow)
        for k, name in enumerate(ARROWS):
            spread = math.radians(-36 + 12 * k)
            direction = Matrix.Rotation(spread, 3, "Z") @ (frame_m.to_3x3() @ Vector((0, -1, 0)))
            C.shoot_from(name, 17, 24, lambda: frame_m @ Vector((0, -0.2, 0)), direction, 3.5)
        flash("fx_frost", 17, 4, 1.4)
        stance(34)

    @clip("E", 30)
    def hawkshot():
        start()
        # Bow raised high, a spirit hawk loosed into the sky ahead.
        nock_arrow(5)
        full_draw(12, sky_bow)
        rot("head", 12, x=-14, y=-4, z=36)
        size("arrow", 15, 0.0)
        ik("R", "draw", 15, 0.0)
        fk_arm("R", 16, up=80, swing=-20, bend=110, out=-40, hand=10)
        frame_m = C.weapon_frame("bow", sky_bow)
        C.shoot_from("fx_hawk", 15, 26, lambda: frame_m @ Vector((0, -0.2, 0)), frame_m.to_3x3() @ Vector((0, -1, 0)), 4.0)
        stance(30)

    @clip("R", 52)
    def crystal_arrow():
        start()
        # A long, deep draw while the crystal arrow forms, then a heavy release.
        nock_arrow(6)
        full_draw(14, amount=0.7)
        size("fx_bowglow", 10, 0.0)
        size("fx_bowglow", 30, 2.2)
        for k, f in enumerate(range(16, 31, 3)):
            C.weapon_offset("bow", "nock", f, (0, DRAW * (0.8 + 0.04 * k), 0))
            rot("chest", f, x=-2 - (0.8 if k % 2 else 0), z=-16)
        loc("hips", 30, z=-0.06)
        size("fx_bowglow", 31, 0.0)
        loose(31, "fx_crystal", 6.0)
        flash("fx_frost", 31, 6, 2.5)
        rot("chest", 32, x=-8, z=-14)
        loc("hips", 33, y=0.04, z=-0.05)
        stance(52)

    @clip("Recall", 48, loop=True)
    def recall():
        # Bow planted, both hands resting on it, a calm look into the distance.
        planted = placement("bow", B(0.06, -0.30, 0.85), rx=-88, rz=0, roll=0)
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.3)
            weapon_matrix("bow", planted, f)
            fk_arm("R", f, up=10, swing=-40, bend=60, out=-30, twist=30, hand=-10)
            rot("head", f, x=-2, z=6 * s_)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        ik("L", "bow", 3, 1.0)
        ik("L", "bow", 6, 0.0)
        weapon_matrix("bow", placement("bow", B(0.40, -0.25, 0.04), rx=-90, rz=60), 16)
        C.fall_back(0, S)
