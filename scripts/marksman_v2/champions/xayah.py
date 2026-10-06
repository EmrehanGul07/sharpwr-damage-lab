"""Xayah: an original stylized interpretation (magenta hair and feathered hood with ears, feather
cape, gold-edged armour, talon boots and twin feather blades)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, fk_arm, flash, lathe, loc, material, metaball_object, rot, size, torus

S = 1.0
RIM = (1.0, 0.5, 0.85)
EXPOSURE = -0.15
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55), "R": dict(angle_deg=28, distance=3.6, height=1.3, target_z=1.0)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#cea4a8", rough=0.5, sss=0.2),
        purple=material("Dark purple", "#352643", rough=0.5),
        magenta=material("Magenta", "#853761", rough=0.5),
        pink=material("Feather pink", "#ba73a0", rough=0.55),
        gold=material("Gold edge", "#cbb079", rough=0.3, metal=1.0),
        hair=material("Magenta hair", (0.55, 0.06, 0.22), rough=0.45),
        hair_dark=material("Deep magenta", (0.28, 0.02, 0.10), rough=0.5),
        talon=material("Talon", (0.12, 0.10, 0.08), rough=0.4),
        blade=material("Feather blade", (0.85, 0.55, 0.75), rough=0.25, metal=0.4),
        glow=material("Feather glow", "#ef9dda", emission=6.0),
    )
    C.face_materials(iris=(0.85, 0.65, 0.2), lash=(0.05, 0.01, 0.03), lip=(0.55, 0.22, 0.32))


def build_body():
    meta = metaball_object("Xayah body")
    C.torso_female(meta, S, bust=0.92, hips=0.96, waist=0.9)
    C.limbs(meta, dict(thigh=(0.061, 0.039), calf=(0.039, 0.044, 0.028), arm=(0.041, 0.030), forearm=(0.032, 0.024), palm=0.031), hands="mitten")
    for side in ("L", "R"):
        toe = C.J[f"toe.{side}"]
        ball(meta, toe + Vector((0, 0.01, 0.004)), 0.032, (0.9, 1.25, 0.7))
    cuts = [((0, 0, z), (0, 0, 1)) for z in (0.50, 0.86, 0.94, 1.08, 1.40)]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.45, 0.80)]

    def region(c):
        x, y, z = c
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            f = C.arm_fraction(c, side)
            return "magenta" if f > 0.80 else "purple" if f > 0.45 else "skin"
        if z < 0.50:
            return "purple"
        if z < 0.86:
            return "magenta"
        if z < 0.94:
            return "gold"
        if z < 1.08:
            return "skin"
        if z > 1.40 and math.hypot(x, y - 0.01) < 0.065:
            return "skin"
        return "purple"

    return C.body_mesh(meta, "Xayah body", region, ["skin", "purple", "magenta", "gold"], cuts)


def feather(name, length, width, mat, edge="gold"):
    """A feather along -Y from the origin: a vane with a gold quill."""
    vane = [(0, 0, 0), (width * 0.5, -length * 0.25, 0), (width * 0.55, -length * 0.65, 0), (0, -length, 0), (-width * 0.4, -length * 0.6, 0), (-width * 0.45, -length * 0.25, 0)]
    parts = [C.plate(name, mat, vane, 0.006, 0.0), C.cyl("Quill", edge, 0.004, length * 0.9, (0, -length * 0.45, 0.003), C.X90, 6)]
    return C.join(parts, name)


def build_gear():
    h = C.HEAD
    # Feathered hood with two long pointed ears.
    meta = metaball_object("Hood", resolution=0.006)
    ball(meta, h + Vector((0, 0.03, 0.035)), 0.12, (1.0, 1.05, 1.05))
    ball(meta, h + Vector((0, 0.07, -0.07)), 0.09, (1.1, 0.9, 1.1))
    hood = C.mesh_from_meta(meta, "Hood", voxel=0.006, smooth=3, tris=3500)
    C.delete_faces(hood, lambda c: (c.y < h.y - 0.0 and c.z < h.z + 0.09) or c.z < h.z - 0.15)
    C.solidify(hood, 0.007)
    hood.data.materials.append(M["purple"])
    C.PARTS.append((hood, "head"))
    for sx in (1, -1):
        ear = C.plate("Hood ear", "magenta", [(0.0, 0.0, 0.0), (0.05 * sx, 0.04, 0.03), (0.14 * sx, 0.10, 0.15), (0.03 * sx, 0.06, 0.07)], 0.012, 0.0)
        C.place(ear, Matrix.Translation(h + Vector((0.06 * sx, 0.03, 0.10))))
        C.PARTS.append((ear, "head"))
    trim = [h + Vector((math.sin(a) * 0.105, -0.0 - math.cos(a) * 0.035, 0.09 * math.cos(a) * 0.9)) for a in (math.radians(d) for d in range(-90, 91, 18))]
    C.PARTS.append((C.tube("Hood trim", trim, 0.006, "gold", False), "head"))
    # Gold-edged armour pieces.
    for sx, side in ((1, "L"), (-1, "R")):
        pad = lathe("Shoulder", "gold", [(0.0, 0.035), (0.045, 0.03), (0.06, 0.005), (0.06, -0.015)], 18, "Z")
        C.place(pad, Matrix.Translation(B(0.16 * sx, 0.012, 1.365)) @ Matrix.Rotation(math.radians(-28 * sx), 4, "Y"))
        C.PARTS.append((pad, f"shoulder.{side}"))
        # Talon tips on the boots.
        toe = C.J[f"toe.{side}"]
        for k in (-1, 0, 1):
            claw = C.cone("Talon", "talon", 0.008, 0.0, 0.05, toe + Vector((0.018 * k, -0.035, -0.005)), (math.radians(-100), 0, math.radians(15 * k)), 6)
            C.PARTS.append((claw, f"foot.{side}"))
    belt = [torus("Belt", "gold", 0.112, 0.01, B(0, 0.01, 0.90), (0, 0, 0), (1.0, 0.8, 1.0), 40)]
    for o in belt:
        C.PARTS.append((o, "hips"))
    # The feather cape: a cape body with rows of feathers, on spring chains.
    capes = {}
    for side, sx in (("L", 1), ("R", -1)):
        pts = [B(0.06 * sx, 0.095, 1.38), B(0.09 * sx, 0.15, 1.12), B(0.11 * sx, 0.17, 0.86), B(0.12 * sx, 0.18, 0.62)]
        cape = C.ribbon("Feather cape", pts, 0.17, "magenta", (1, 0, 0), 0.008, [0.8, 1.0, 1.15, 1.2], bone=False, curl=0.03, across=4)
        capes[side] = (pts, cape, [])
        for row in range(4):
            for k in range(3):
                t = 0.25 + 0.22 * row
                base = Vector(pts[0]).lerp(Vector(pts[-1]), t) + Vector((sx * (0.05 * (k - 1)), 0.015, 0))
                f = feather("Cape feather", 0.16 + 0.03 * row, 0.05, "pink" if (row + k) % 2 else "magenta")
                C.place(f, Matrix.Translation(base) @ Matrix.Rotation(math.radians(-90), 4, "X") @ Matrix.Rotation(math.radians(8 * (k - 1) * sx), 4, "Y"))
                capes[side][2].append(f)
    return capes


def build_head():
    C.build_head("Xayah head", jaw=0.94, chin=0.95, nose=0.9)
    C.build_face(eye_size=1.05, lashes="winged", brow_mat="hair", brow_width=0.0019, brow_angle=0.14, mouth="smirk", mouth_size=0.0019)
    h = C.HEAD
    meta = metaball_object("Xayah hair", resolution=0.004)
    for i, x in enumerate((0.06, 0.03, 0.0, -0.03, -0.06)):
        C.clump(meta, [h + Vector((x * 0.6, -0.06, 0.10)), h + Vector((x, -0.10, 0.06)), h + Vector((x * 1.1, -0.098, 0.015 - 0.004 * (i % 2)))], 0.016, 0.004, flat=0.6)
    for sx in (1, -1):
        C.clump(meta, [h + Vector((0.075 * sx, -0.06, 0.06)), h + Vector((0.095 * sx, -0.065, -0.04)), h + Vector((0.09 * sx, -0.05, -0.15)), h + Vector((0.085 * sx, -0.03, -0.24))], 0.022, 0.006, flat=0.6)
    hair = C.mesh_from_meta(meta, "Xayah hair", voxel=0.0035, smooth=3, tris=3500)
    C.paint_regions(hair, lambda c: "hair" if c.z > h.z - 0.05 else "hair_dark", ["hair", "hair_dark"])
    C.PARTS.append((hair, "head"))
    C.hair_cap("Xayah hair cap", "hair", front_y=0.045, front_z=0.05)


def build():
    C.make_joints(scale=S, shoulder_x=0.172, hip_x=0.092)
    materials()
    body = build_body()
    capes = build_gear()
    build_head()
    C.scale_parts("head", 1.07, C.J["head_bone"])
    # A feather blade held in each hand, pointing forward from the fist.
    holds = {}
    for side in ("L", "R"):
        wr, hd = C.J[f"wrist.{side}"], C.J[f"hand.{side}"]
        n = C.hand_normal(side)
        frame = C.frame_along(wr.lerp(hd, 0.5) - n * 0.01, (hd - wr).normalized() * 0.4 + Vector((0, -1, 0)), n)
        blade = feather(f"Feather blade {side}", 0.36, 0.07, "blade")
        C.place(blade, frame @ Matrix.Rotation(math.radians(90), 4, "Y"))
        holds[side] = frame
    fx = {f"fx_feather.{k}": (C.join([feather(f"FX feather {k}", 0.36, 0.07, "glow")], f"FX feather {k}"), None, None) for k in range(6)}
    fx["fx_glow.L"] = (C.fx_orb("blade glow L", 0.05, "glow", 1), holds["L"], "hand.L")
    fx["fx_glow.R"] = (C.fx_orb("blade glow R", 0.05, "glow", 1), holds["R"], "hand.R")
    fx["fx_storm"] = (C.join([C.torus("FX featherstorm", "glow", 0.6 + 0.1 * k, 0.008, (0, 0, 0.1 * k), (0, 0, 0), (1, 1, 1), 40) for k in range(3)], "FX featherstorm"), Matrix.Translation(B(0, 0, 0.9)), "hips")
    extra = [C.point_bone(f"blade.{side}", holds[side], f"hand.{side}", 0.05) for side in ("L", "R")]
    extra += C.fx_bones(fx, Matrix.Translation(B(0, -0.4, 1.1)))
    chains = []
    for side, (pts, cape, feathers) in capes.items():
        chains.append((f"cape.{side}", C.resample(pts, 3), "chest", dict(skin=True, stiffness=50, gain=1.0, sway=2.5, limit=(50, 25))))
        C.SKINNED.append((cape, ["chest"] + [f"cape.{side}.{i}" for i in range(3)]))
    C.SOCKETS["socket_muzzle"] = ("hand.R", holds["R"])
    C.build_rig("Xayah rig", chains, extra)
    C.bind(body)
    for side, (pts, cape, feathers) in capes.items():
        for f in feathers:
            C.attach_to_chain(f, f"cape.{side}")
    for side in ("L", "R"):
        C.attach(C.bpy.data.objects[f"Feather blade {side}"], f"blade.{side}")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips(holds)


FEATHERS = [f"fx_feather.{k}" for k in range(6)]
FX = FEATHERS + ["fx_glow.L", "fx_glow.R", "fx_storm"]


def define_clips(holds):
    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def hand_at(side, frame):
        return C.carried(f"hand.{side}", frame, holds[side].translation)

    def stance(frame, breath=0.0, sway=0.0):
        """Poised and light: weight forward, both blades low and ready."""
        loc("hips", frame, x=-0.01 * sway, z=-0.035 - 0.004 * breath)
        rot("hips", frame, z=-8 + 3 * sway)
        rot("spine", frame, x=5 + breath, z=4)
        rot("chest", frame, x=1 + 1.5 * breath, z=4 - sway)
        rot("head", frame, x=-4 + breath, y=-4, z=-6 + 3 * sway)
        C.feet(frame, (0.05, -0.10, 0.0, -14), (-0.05, 0.08, 0, 22))
        for side in ("L", "R"):
            fk_arm(side, frame, up=16 + 2 * breath, swing=-30, bend=55, out=4, twist=20, hand=-20)
            size(f"blade.{side}", frame, 1.0)
        loc("root", frame)
        rot("root", frame)

    def throw(side, frame, name, distance=3.5, spread=0.0):
        """Overhand flick: the held blade vanishes, a glowing feather flies."""
        fk_arm(side, frame - 3, up=80, swing=30, bend=110, out=10, hand=-30)
        fk_arm(side, frame, up=50, swing=-85, bend=10, out=-10 * (1 if side == "R" else -1), hand=-10)
        size(f"blade.{side}", frame - 1, 1.0)
        size(f"blade.{side}", frame, 0.0)
        size(f"blade.{side}", frame + 6, 0.0)
        size(f"blade.{side}", frame + 8, 1.0)
        direction = Matrix.Rotation(math.radians(spread), 3, "Z") @ Vector((0, -1, 0))
        C.shoot_from(name, frame, frame + 6, lambda: hand_at(side, frame), direction, distance)

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
            arc = 32 * (1 if lead == "L" else -1) * phase
            fk_arm("L", frame, up=14, swing=arc, bend=70, out=-4, hand=-15)
            fk_arm("R", frame, up=14, swing=-arc, bend=70, out=-4, hand=-15)
            for side in ("L", "R"):
                size(f"blade.{side}", frame, 1.0)

        C.run_cycle(upper, scale=S, lean=12, twist=11)
        fx_off(0)

    @clip("AA", 20)
    def attack():
        start()
        rot("chest", 3, z=16)
        throw("R", 6, FEATHERS[0])
        rot("chest", 6, z=-12)
        stance(20)

    @clip("P", 24)
    def clean_cuts():
        start()
        # A follow-up flick: both blades thrown in a quick one-two.
        throw("R", 5, FEATHERS[0], 3.5, -6)
        throw("L", 9, FEATHERS[1], 3.5, 6)
        rot("chest", 5, z=-14)
        rot("chest", 9, z=14)
        stance(24)

    @clip("Q", 28)
    def double_daggers():
        start()
        # Both arms cocked back, then a scissor throw of two daggers.
        for side in ("L", "R"):
            fk_arm(side, 5, up=70, swing=40, bend=100, out=20, hand=-30)
            size(f"blade.{side}", 7, 1.0)
            size(f"blade.{side}", 8, 0.0)
            size(f"blade.{side}", 16, 0.0)
            size(f"blade.{side}", 18, 1.0)
            fk_arm(side, 8, up=40, swing=-80, bend=10, out=-20, hand=-10)
        loc("hips", 5, z=-0.08)
        rot("spine", 5, x=-6)
        rot("spine", 8, x=14)
        C.shoot_from(FEATHERS[0], 8, 15, lambda: hand_at("L", 8), Matrix.Rotation(math.radians(6), 3, "Z") @ Vector((0, -1, 0)), 4.0)
        C.shoot_from(FEATHERS[1], 8, 15, lambda: hand_at("R", 8), Matrix.Rotation(math.radians(-6), 3, "Z") @ Vector((0, -1, 0)), 4.0)
        stance(28)

    @clip("W", 30)
    def deadly_plumage():
        start()
        # Blades crossed before her face, they flare with light.
        for side in ("L", "R"):
            fk_arm(side, 6, up=40, swing=-70, bend=120, out=-35, twist=20, hand=-30)
            size(f"fx_glow.{side}", 5, 0.0)
            size(f"fx_glow.{side}", 9, 1.4)
            size(f"fx_glow.{side}", 20, 1.0)
            size(f"fx_glow.{side}", 24, 0.0)
        rot("head", 6, x=6, z=0)
        stance(30)

    @clip("E", 34)
    def bladecaller():
        start()
        # Arms flung wide: every feather on the ground snaps back to her.
        for side in ("L", "R"):
            fk_arm(side, 8, up=85, swing=-10, bend=10, out=10, hand=0)
        rot("chest", 8, x=-8)
        rot("head", 8, x=-12)
        for k, name in enumerate(FEATHERS[:5]):
            a = math.radians(-50 + 25 * k)
            far = B(math.sin(a) * 3.0, -math.cos(a) * 3.0, 0.05)
            size(name, 9, 0.0)
            size(name, 10, 1.0)
            size(name, 18, 1.0)
            size(name, 19, 0.0)
            C.fly_path(name, [(10, far), (18, lambda: C.carried("chest", 18, B(0, -0.15, 1.2)))], (0, 0, 1), 0.0)
        stance(34)

    @clip("R", 52)
    def featherstorm():
        start()
        moving = bool(C.OPTIONS.get("root_motion"))
        # A leap up into a spin, a storm of feathers fanned out below, a light landing.
        loc("hips", 5, z=-0.14)
        rot("spine", 5, x=16)
        loc("root", 5)
        loc("root", 14, z=0.55, y=0.3 if moving else 0.0)
        for k, f in enumerate((8, 11, 14, 17, 20)):
            C.spin_about(f, -90 * k, (0, 0, 1), (0, 0, 0), (0, 0.3 if moving else 0.0, 0.55 if 11 <= f <= 17 else 0.25))
        for side in ("L", "R"):
            fk_arm(side, 12, up=90, swing=0, bend=10, out=0, hand=0)
        for side in ("L", "R"):
            loc(f"ik_foot.{side}", 14, x=0.02 * C.side_x(side), y=0.08, z=0.18)
        size("fx_storm", 10, 0.0)
        size("fx_storm", 14, 1.2)
        for f in range(14, 27, 3):
            rot("fx_storm", f, z=-30 * (f - 14))
        size("fx_storm", 26, 0.0)
        for k, name in enumerate(FEATHERS):
            spread = -40 + 16 * k
            C.shoot_from(name, 18, 25, lambda: C.carried("chest", 18, B(0, -0.1, 1.2)), Matrix.Rotation(math.radians(spread), 3, "Z") @ Vector((0, -1, -0.3)), 3.5)
        loc("hips", 24, z=-0.12)
        rot("spine", 24, x=14)
        stance(52)
        C.spin_about(20, -360, (0, 0, 1), (0, 0, 0), (0, 0.3 if moving else 0.0, 0))
        C.spin_about(52, -360, (0, 0, 1), (0, 0, 0), (0, 0.3 if moving else 0.0, 0))

    @clip("Recall", 48, loop=True)
    def recall():
        # Plucking a feather from the cape and twirling it.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.4)
            fk_arm("R", f, up=40, swing=-55, bend=120, out=-25, twist=-10, hand=-40 + 30 * s_)
            rot("head", f, x=10, z=-10 + 4 * s_)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        C.fall_back(0, S)
