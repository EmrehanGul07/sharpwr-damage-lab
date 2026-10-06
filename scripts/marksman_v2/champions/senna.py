"""Senna: an original stylized interpretation (dark skin, white long coat, flowing dark locs,
oversized spectral relic cannon)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, cyl, fk_arm, flash, ik, lathe, loc, material, metaball_object, placement, rot, size, torus, weapon_matrix

S = 1.07
RIM = (0.45, 1.0, 0.75)
EXPOSURE = -0.15
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#6a4636", rough=0.5, sss=0.04),
        coat=material("White coat", "#e3dcd0", rough=0.6),
        green=material("Dark green", "#243932", rough=0.55),
        moss=material("Green trim", "#416856", rough=0.5),
        metal=material("Relic metal", "#a49870", rough=0.3, metal=1.0),
        iron=material("Relic iron", (0.05, 0.06, 0.055), rough=0.35, metal=0.9),
        boot=material("Boots", (0.03, 0.03, 0.028), rough=0.45),
        hair=material("Dark locs", (0.02, 0.014, 0.012), rough=0.55),
        hair_dark=material("Darker locs", (0.01, 0.008, 0.007), rough=0.6),
        mist=material("Mist", "#76ffcd", emission=6.0),
        mist_soft=material("Soft mist", (0.4, 1.0, 0.8), emission=2.0, alpha=0.35),
        dark=material("Dark beam", (0.05, 0.25, 0.18), emission=4.0),
    )
    C.face_materials(iris=(0.30, 0.55, 0.40), lash=(0.01, 0.008, 0.007), lip=(0.32, 0.17, 0.14))


def build_body():
    meta = metaball_object("Senna body")
    C.torso_female(meta, S, bust=1.0, hips=1.0, waist=0.95)
    C.limbs(meta, dict(thigh=(0.064, 0.041), calf=(0.041, 0.047, 0.03), arm=(0.044, 0.032), forearm=(0.035, 0.027), palm=0.034), hands="mitten")
    for side in ("L", "R"):
        knee, toe = C.J[f"knee.{side}"], C.J[f"toe.{side}"]
        ball(meta, knee + Vector((0, -0.012, 0.03 * S)), 0.052 * S, (1.0, 1.0, 0.55))
        ball(meta, toe + Vector((0, 0.012, 0.004)), 0.036 * S, (0.9, 1.25, 0.7))
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.54, 0.88, 1.40)]
    v = Vector((1, 0, -0.09)).normalized()
    cuts += [(B(0.035, 0, 0.95), v), (B(-0.035, 0, 0.95), Vector((-v.x, 0, v.z)))]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.70, 0.80)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            f = C.arm_fraction(c, side)
            return "boot" if f > 0.80 else "moss" if f > 0.70 else "coat"
        if z < 0.54:
            return "boot"
        if z < 0.88:
            return "green"
        if z > 1.40 and math.hypot(x, y - 0.01) < 0.065:
            return "skin"
        if y < 0 and z > 0.95 and abs(x) < 0.035 + (z - 0.95) * 0.09:
            return "green"
        return "coat"

    return C.body_mesh(meta, "Senna body", region, ["skin", "coat", "green", "moss", "boot"], cuts)


def build_clothes():
    panels = C.coat_panels(
        [
            ("back.L", 0.055, 0.105, 0.115, 0.97, 0.30, 0.03),
            ("back.R", -0.055, 0.105, 0.115, 0.97, 0.30, 0.03),
            ("side.L", 0.122, 0.02, 0.12, 0.97, 0.34, 0.08),
            ("side.R", -0.122, 0.02, 0.12, 0.97, 0.34, 0.08),
        ],
        "coat",
        S,
    )
    for sx in (1, -1):
        lapel = C.ribbon("Lapel", [B(0.035 * sx, -0.083, 0.98), B(0.055 * sx, -0.095, 1.18), B(0.085 * sx, -0.084, 1.37)], 0.024 * S, "moss", (1, 0, 0), 0.004, [0.6, 1.0, 1.1], bone=False)
        C.SKINNED.append((lapel, ["spine", "chest"]))
        pad = lathe("Shoulder guard", "metal", [(0.0, 0.035), (0.05, 0.03), (0.07, 0.005), (0.07, -0.02)], 20, "Z")
        C.place(pad, Matrix.Translation(B(0.165 * sx, 0.012, 1.37)) @ Matrix.Rotation(math.radians(-28 * sx), 4, "Y"))
        C.PARTS.append((pad, f"shoulder.{'L' if sx > 0 else 'R'}"))
    collar = [B(math.sin(a) * 0.078, 0.012 + math.cos(a) * 0.064, 1.405 + 0.03 * (1 + math.cos(a)) / 2) for a in (math.radians(d) for d in range(-130, 131, 20))]
    C.PARTS.append((C.ribbon("Collar", collar, 0.06 * S, "coat", (0, 0, 1), 0.008, bone=False), "chest"))
    belt = [torus("Belt", "iron", 0.12 * S, 0.012 * S, B(0, 0.01, 0.94), (0, 0, 0), (1.0, 0.8, 1.0), 40), ball_mesh("Belt relic", "mist", B(0, -0.093, 0.94), (0.016, 0.008, 0.016), 12, 6)]
    for o in belt:
        C.PARTS.append((o, "hips"))
    return panels


def build_head():
    C.build_head("Senna head", jaw=0.98, chin=1.0, nose=1.02)
    C.build_face(eye_size=0.95, lashes="winged", brow_mat="hair", brow_width=0.002, brow_angle=0.06, mouth="flat", mouth_size=0.0021, mouth_y=-0.003)
    h = C.HEAD
    C.hair_cap("Senna hair", "hair", front_y=0.045, front_z=0.06, scale=1.05)
    # Locs: a ring of tapering strands; the long ones down the back hang on chains.
    meta = metaball_object("Senna front locs", resolution=0.004)
    for sx in (1, -1):
        for k in range(3):
            x = (0.06 + 0.015 * k) * sx
            C.clump(meta, [h + Vector((x, -0.06 + 0.03 * k, 0.07)), h + Vector((x * 1.4, -0.05 + 0.03 * k, -0.04)), h + Vector((x * 1.5, -0.04 + 0.03 * k, -0.17))], 0.011, 0.007)
    front = C.mesh_from_meta(meta, "Senna front locs", voxel=0.003, smooth=2, tris=3000)
    front.data.materials.append(M["hair"])
    C.PARTS.append((front, "head"))
    backs = {}
    for side, sx in (("L", 1), ("R", -1)):
        path = [h + Vector((0.05 * sx, 0.10, -0.02)), B(0.07 * sx, 0.14, 1.36), B(0.08 * sx, 0.15, 1.18), B(0.085 * sx, 0.14, 0.98)]
        sheet = metaball_object(f"Senna locs {side}", resolution=0.004)
        for k in range(4):  # separate locs side by side
            off = Vector((0.02 * (k - 1.5), 0.004 * (k % 2), 0))
            C.clump(sheet, [p + off for p in path], 0.013, 0.008)
        mesh = C.mesh_from_meta(sheet, f"Senna locs {side}", voxel=0.0035, smooth=2, tris=3000)
        C.paint_regions(mesh, lambda c: "hair" if c.z > 1.3 * S else "hair_dark", ["hair", "hair_dark"])
        backs[side] = (path, mesh)
    for k in range(5):  # gold cuffs on the locs
        a = math.radians(-60 + 30 * k)
        C.PARTS.append((torus("Loc cuff", "metal", 0.013, 0.003, h + Vector((math.sin(a) * 0.1, 0.06 + 0.04 * math.cos(a), -0.05)), (0, 0, 0), (1, 1, 1), 12), "head"))
    return backs


def build_cannon():
    """The relic cannon: grip at the origin, barrel toward -Y, heavy body above and behind."""
    parts = [
        lathe("Cannon body", "iron", [(0.0, 0.32), (0.07, 0.31), (0.09, 0.22), (0.10, 0.05), (0.085, -0.10), (0.07, -0.20)], 24),
        lathe("Cannon rings", "metal", [(0.104, 0.16), (0.104, 0.12)], 24),
        lathe("Cannon ring 2", "metal", [(0.095, -0.02), (0.095, -0.06)], 24),
        lathe("Barrel", "iron", [(0.06, -0.20), (0.05, -0.55), (0.06, -0.70), (0.075, -0.78), (0.05, -0.80)], 24),
        lathe("Muzzle crown", "metal", [(0.078, -0.74), (0.085, -0.76), (0.08, -0.80)], 24),
        lathe("Mist core", "mist", [(0.065, -0.24), (0.065, -0.30)], 24),
        box("Grip", "boot", (0.035, 0.05, 0.11), (0, 0.02, -0.08), 0.01, (math.radians(-15), 0, 0)),
        box("Fore handle", "boot", (0.03, 0.04, 0.10), (0, -0.30, -0.10), 0.01),
        C.plate("Relic fin", "metal", [(0, 0.25, 0.08), (0, 0.05, 0.10), (0, -0.05, 0.16), (0, 0.10, 0.18)], 0.012, 0.0),
    ]
    for sx in (1, -1):
        parts.append(C.plate("Side wing", "metal", [(0.09 * sx, 0.20, 0.0), (0.16 * sx, 0.12, 0.03), (0.10 * sx, -0.05, 0.02)], 0.01, 0.0))
    for k in range(6):
        a = k * math.pi / 3
        parts.append(ball_mesh("Mist vent", "mist", (math.cos(a) * 0.09, 0.0, math.sin(a) * 0.09), (0.012, 0.012, 0.012), 8, 4))
    cannon = C.join(parts, "Relic cannon")
    C.place(cannon, Matrix.Translation((0, 0, 0.08)))  # bore above the grip
    return cannon


HOLD = None


def build():
    global HOLD
    C.make_joints(scale=S, shoulder_x=0.18, hip_x=0.094)
    materials()
    body = build_body()
    panels = build_clothes()
    backs = build_head()
    C.scale_parts("head", 1.06, C.J["head_bone"])
    cannon = build_cannon()
    # Rest: the cannon braced at the right hip, muzzle forward and slightly down.
    HOLD = Matrix.Translation(B(-0.16, -0.12, 0.98)) @ Matrix.Rotation(math.radians(8), 4, "Z") @ Matrix.Rotation(math.radians(-6), 4, "X")
    C.place(cannon, HOLD)
    muzzle = HOLD @ Matrix.Translation((0, -0.82, 0.08))
    fx = {
        "fx_muzzle": (C.fx_flash("muzzle", 0.06, "mist"), muzzle, "cannon"),
        "fx_shot": (C.fx_bolt("shot", 0.3, 0.025, "mist", "mist_soft"), None, None),
        "fx_beam": (C.fx_beam("piercing darkness", 5.0, 0.07, "dark", "mist"), None, None),
        "fx_dawn": (C.fx_beam("dawning shadow", 7.0, 0.22, "mist_soft", "mist"), None, None),
        "fx_embrace": (C.fx_orb("last embrace", 0.07, "dark", 2), None, None),
        "fx_cloud": (C.join([ball_mesh(f"FX mist {k}", "mist_soft", (math.cos(k * 1.3) * 0.3, math.sin(k * 1.3) * 0.3, 0.2 * (k % 3)), (0.25, 0.25, 0.25), 16, 8) for k in range(6)], "FX mist cloud"), Matrix.Translation(B(0, 0, 0.6)), "root"),
        "fx_souls": (C.join([ball_mesh(f"FX soul {k}", "mist", (math.cos(k * 2.1) * 0.6, math.sin(k * 2.1) * 0.6, 0.3 * (k % 2)), (0.04, 0.04, 0.06), 10, 6) for k in range(5)], "FX souls"), Matrix.Translation(B(0, 0, 1.0)), "root"),
    }
    grip = HOLD @ Vector((0, 0.01, -0.06))
    fore = HOLD @ Vector((0, -0.30, -0.10))
    extra = [C.weapon_bones("cannon", HOLD, (0, 0, 0), "hips", 0.3), C.grip_bone("grip_cannon.R", grip, "cannon"), C.grip_bone("grip_cannon.L", fore, "cannon")]
    extra += C.fx_bones(fx, Matrix.Translation(B(-0.2, -0.5, 1.1)))
    chains = C.coat_chains(panels, stiffness=50, gain=0.9, sway=2.0, limit=(50, 25))
    for side, (path, mesh) in backs.items():
        chains.append((f"locs.{side}", C.resample(path, 3), "head", dict(skin=True, stiffness=55, gain=1.1, sway=2.5, limit=(45, 30))))
        C.SKINNED.append((mesh, ["head"] + [f"locs.{side}.{i}" for i in range(3)]))
    C.SOCKETS["socket_muzzle"] = ("cannon", muzzle)
    C.build_rig("Senna rig", chains, extra, [("R", "cannon", "grip_cannon.R"), ("L", "cannon", "grip_cannon.L")])
    C.bind(body)
    C.attach(cannon, "cannon")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips()


FX = ["fx_muzzle", "fx_shot", "fx_beam", "fx_dawn", "fx_embrace", "fx_cloud", "fx_souls"]


def define_clips():
    aim = placement("cannon", B(-0.13, -0.20, 1.06), rx=3, rz=4)
    high = placement("cannon", B(-0.12, -0.18, 1.10), rx=10, rz=4)

    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def muzzle_point(frame):
        return C.carried("cannon", frame, C.rig.data.bones["fx_muzzle"].head_local)

    def bore(frame):
        return muzzle_point(frame) - C.carried("cannon", frame, C.rig.data.bones["cannon"].head_local + Vector((0, 0, 0.08)))

    def shoot(name, f0, f1, distance=4.5):
        C.shoot_from(name, f0, f1, lambda: muzzle_point(f0), lambda: bore(f0), distance)

    def beam(name, f0, f1):
        size(name, f0 - 1, 0.0)
        size(name, f0, 1.0)
        size(name, f1, 1.0)
        size(name, f1 + 1, 0.0)

        @C.later
        def place():
            r = Vector((0, -1, 0)).rotation_difference(bore(f0)).to_matrix() @ C.rig.data.bones[name].matrix_local.to_3x3()
            C.put(name, f0, muzzle_point(f0), r)
            C.put(name, f1, muzzle_point(f1), r)

    def stance(frame, breath=0.0, sway=0.0):
        """Heavy, grounded stance with the cannon braced at the hip."""
        loc("hips", frame, x=0.006 * sway, z=-0.04 - 0.005 * breath)
        rot("hips", frame, z=-8 + 2 * sway)
        rot("spine", frame, x=3 + breath, z=-4)
        rot("chest", frame, x=-1 + 1.5 * breath, z=-6 + sway)
        rot("head", frame, x=-3 + breath, z=14 - 3 * sway)
        C.feet(frame, (0.07, -0.10, 0, -20), (-0.07, 0.08, 0, 26))
        loc("cannon", frame)
        rot("cannon", frame)
        ik("R", "cannon", frame, 1.0)
        ik("L", "cannon", frame, 1.0)
        loc("pole_elbow.R", frame, x=-0.2, y=0.25, z=-0.2)
        loc("pole_elbow.L", frame, x=0.15, y=-0.05, z=-0.35)
        loc("root", frame)
        rot("root", frame)

    def brace(frame, matrix=None):
        rot("hips", frame, z=-14)
        loc("hips", frame, z=-0.07)
        rot("spine", frame, x=6, z=-8)
        rot("chest", frame, x=4, z=-10)
        rot("head", frame, x=4, z=22)
        C.feet(frame, (0.09, -0.14, 0, -25), (-0.08, 0.12, 0, 30))
        weapon_matrix("cannon", matrix or aim, frame)

    def kick(frame, amount=0.08, pitch=-12, matrix=None):
        rot("chest", frame, x=-6, z=-6)
        loc("hips", frame, y=0.04, z=-0.06)
        weapon_matrix("cannon", Matrix.Translation(B(0, amount, amount * 0.5)) @ (matrix or aim) @ Matrix.Rotation(math.radians(pitch), 4, "X"), frame)

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
            loc("cannon", frame, z=0.01 * phase)
            rot("cannon", frame)
            ik("R", "cannon", frame, 1.0)
            ik("L", "cannon", frame, 1.0)
            loc("pole_elbow.R", frame, x=-0.2, y=0.25, z=-0.2)
            loc("pole_elbow.L", frame, x=0.15, y=-0.05, z=-0.35)

        C.run_cycle(upper, scale=S, lean=8, twist=6, stride=0.9)
        fx_off(0)

    @clip("AA", 26)
    def attack():
        start()
        brace(6)
        flash("fx_muzzle", 9, 3, 1.4)
        shoot("fx_shot", 9, 15, 4.5)
        kick(10)
        brace(16)
        stance(26)

    @clip("P", 36)
    def absolution():
        start()
        # Souls drift in from the mist and are drawn into the relic.
        size("fx_souls", 4, 0.0)
        size("fx_souls", 8, 1.2)
        rot("fx_souls", 8)
        rot("fx_souls", 20, z=90)
        size("fx_souls", 26, 0.15)
        size("fx_souls", 28, 0.0)
        rot("head", 12, x=8, z=4)
        rot("chest", 16, x=-3, z=-4)
        size("fx_muzzle", 20, 0.0)
        size("fx_muzzle", 26, 0.6)
        size("fx_muzzle", 30, 0.0)
        stance(36)

    @clip("Q", 34)
    def piercing_darkness():
        start()
        brace(7)
        size("fx_muzzle", 8, 0.0)
        size("fx_muzzle", 13, 0.8)
        flash("fx_muzzle", 14, 4, 2.0)
        beam("fx_beam", 14, 20)
        kick(15, 0.10, -14)
        brace(21)
        stance(34)

    @clip("W", 30)
    def last_embrace():
        start()
        brace(6)
        flash("fx_muzzle", 10, 3, 1.4)
        shoot("fx_embrace", 10, 20, 4.0)
        kick(11, 0.06, -8)
        brace(17)
        stance(30)

    @clip("E", 40)
    def black_mist():
        start()
        # She sinks into a swirling mist that wreathes her, then rises out of it.
        loc("hips", 6, z=-0.12)
        rot("spine", 6, x=14)
        rot("head", 6, x=14)
        size("fx_cloud", 4, 0.0)
        size("fx_cloud", 9, 1.2)
        for f in range(9, 31, 3):
            rot("fx_cloud", f, z=12 * (f - 9))
        size("fx_cloud", 30, 1.0)
        size("fx_cloud", 34, 0.0)
        stance(40)

    @clip("R", 60)
    def dawning_shadow():
        start()
        # A long charge with the cannon raised, then a massive global beam.
        brace(8, high)
        loc("hips", 10, z=-0.10)
        size("fx_muzzle", 10, 0.0)
        size("fx_muzzle", 34, 1.6)
        for k, f in enumerate(range(14, 35, 4)):
            rot("chest", f, x=4 + (1 if k % 2 else 0), z=-10)
        flash("fx_muzzle", 35, 6, 3.0)
        beam("fx_dawn", 35, 46)
        kick(36, 0.14, -18, high)
        C.feet(37, (0.09, -0.08, 0, -25), (-0.08, 0.22, 0, 30))
        brace(46, high)
        stance(60)

    @clip("Recall", 48, loop=True)
    def recall():
        # The cannon set down, her hand resting on it, mist curling at her feet.
        rest = placement("cannon", B(-0.22, -0.18, 0.55), rx=-80, rz=10)
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.3)
            weapon_matrix("cannon", rest, f)
            ik("L", "cannon", f, 0.0)
            fk_arm("L", f, up=8, swing=-10, bend=20, twist=10, hand=-10)
            rot("head", f, x=-4, z=8 * s_)
        size("fx_cloud", 0, 0.5)
        fx_off(1)
        size("fx_cloud", 1, 0.5)

    @clip("Death", 44)
    def death():
        start()
        for side in ("L", "R"):
            ik(side, "cannon", 3, 1.0)
            ik(side, "cannon", 6, 0.0)
        loc("cannon", 5)
        rot("cannon", 5)
        weapon_matrix("cannon", placement("cannon", B(-0.40, -0.10, 0.10), rx=0, ry=80, rz=30), 14)
        C.fall_back(0, S)
