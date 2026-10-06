"""Jhin: an original stylized interpretation (porcelain mask, asymmetrical gold shoulder shell,
white tailcoat, ornate four-shot rifle with a rose)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, cyl, fk_arm, flash, ik, lathe, loc, material, metaball_object, placement, rot, size, torus, weapon_matrix

S = 1.07
RIM = (1.0, 0.45, 0.6)
EXPOSURE = -0.15
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55), "R": dict(angle_deg=40, distance=3.8, height=1.2, target_z=0.8), "Q": dict(angle_deg=28, distance=3.9, height=1.3, target_z=0.85)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#d4bda6", rough=0.5, sss=0.15),
        plum=material("Plum vest", "#372639", rough=0.55),
        rose=material("Rose crimson", "#97294d", rough=0.5),
        ivory=material("Ivory coat", "#eae3d6", rough=0.55),
        porcelain=material("Porcelain", (0.88, 0.86, 0.82), rough=0.18),
        gold=material("Gold", "#d6ba76", rough=0.28, metal=1.0),
        dark=material("Dark leather", (0.03, 0.022, 0.03), rough=0.45),
        trousers=material("Trousers", (0.04, 0.03, 0.045), rough=0.6),
        hair=material("Dark hair", (0.04, 0.025, 0.02), rough=0.5),
        stock=material("Rifle white", (0.85, 0.82, 0.76), rough=0.3),
        glow=material("Rose light", "#f26491", emission=7.0),
        flash=material("Muzzle flash", (1.0, 0.55, 0.65), emission=9.0),
    )
    C.face_materials(iris=(0.15, 0.10, 0.08), lash=(0.01, 0.008, 0.01), lip=(0.5, 0.3, 0.3))


def build_body():
    meta = metaball_object("Jhin body")
    C.torso_male(meta, S, chest=0.98, waist=0.95)
    ball(meta, B(0, 0.01, 0.885), 0.12 * S, (1.05, 0.8, 0.35))
    C.limbs(meta, dict(neck=(0.05, 0.044), thigh=(0.065, 0.044), calf=(0.044, 0.049, 0.031), foot=(0.04, 0.034), arm=(0.048, 0.035), forearm=(0.037, 0.028), palm=0.035), hands="mitten")
    for side in ("L", "R"):
        knee, toe = C.J[f"knee.{side}"], C.J[f"toe.{side}"]
        ball(meta, knee + Vector((0, -0.012, 0.03 * S)), 0.053 * S, (1.0, 1.0, 0.5))
        ball(meta, toe + Vector((0, 0.012, 0.006)), 0.038 * S, (0.95, 1.2, 0.75))
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.54, 0.885, 1.385)]
    v = Vector((1, 0, -0.1)).normalized()
    cuts += [(B(0.04, 0, 0.95), v), (B(-0.04, 0, 0.95), Vector((-v.x, 0, v.z)))]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.66, 0.78)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.21 and z > 0.88:
            f = C.arm_fraction(c, side)
            return "dark" if f > 0.78 else "gold" if f > 0.66 and f < 0.69 else "ivory"
        if z < 0.54:
            return "dark"
        if z < 0.885:
            return "trousers"
        if z > 1.385 and math.hypot(x, y - 0.01) < 0.075:
            return "skin"
        if y < 0 and z > 0.95 and abs(x) < 0.04 + (z - 0.95) * 0.1:
            return "plum"
        return "ivory"

    return C.body_mesh(meta, "Jhin body", region, ["skin", "ivory", "plum", "gold", "trousers", "dark"], cuts)


def build_clothes():
    panels = C.coat_panels(
        [
            ("back.L", 0.055, 0.105, 0.11, 0.97, 0.36, 0.02),
            ("back.R", -0.055, 0.105, 0.11, 0.97, 0.36, 0.02),
            ("side.L", 0.122, 0.02, 0.11, 0.97, 0.45, 0.06),
            ("side.R", -0.122, 0.02, 0.11, 0.97, 0.45, 0.06),
        ],
        "ivory",
        S,
    )
    # The asymmetrical gold shoulder shell on his left, a small plate on the right.
    shell = lathe("Shoulder shell", "gold", [(0.0, 0.08), (0.05, 0.075), (0.09, 0.05), (0.11, 0.0), (0.105, -0.04), (0.09, -0.06)], 24, "Z")
    for v in shell.data.vertices:  # flare a ridge outward
        v.co.x *= 1.15
    C.place(shell, Matrix.Translation(B(0.17, 0.012, 1.36)) @ Matrix.Rotation(math.radians(-30), 4, "Y"))
    C.PARTS.append((shell, "shoulder.L"))
    for k in range(3):
        fin = C.plate("Shell fin", "gold", [(0, 0, 0), (0.05, 0.0, 0.05), (0.02, 0.0, 0.0)], 0.01, 0.0)
        C.place(fin, Matrix.Translation(B(0.20 + 0.025 * k, 0.03 - 0.03 * k, 1.42 - 0.01 * k)) @ Matrix.Rotation(math.radians(-20), 4, "Y"))
        C.PARTS.append((fin, "shoulder.L"))
    plate = lathe("Shoulder plate", "gold", [(0.0, 0.03), (0.05, 0.025), (0.07, 0.0), (0.065, -0.02)], 20, "Z")
    C.place(plate, Matrix.Translation(B(-0.17, 0.012, 1.37)) @ Matrix.Rotation(math.radians(28), 4, "Y"))
    C.PARTS.append((plate, "shoulder.R"))
    for sx in (1, -1):
        lapel = C.ribbon("Lapel", [B(0.04 * sx, -0.083, 0.98), B(0.06 * sx, -0.095, 1.18), B(0.085 * sx, -0.084, 1.37)], 0.02 * S, "gold", (1, 0, 0), 0.004, [0.6, 1.0, 1.1], bone=False)
        C.SKINNED.append((lapel, ["spine", "chest"]))
    collar = [B(math.sin(a) * 0.08, 0.012 + math.cos(a) * 0.066, 1.40 + 0.04 * (1 + math.cos(a)) / 2) for a in (math.radians(d) for d in range(-130, 131, 20))]
    C.PARTS.append((C.ribbon("Collar", collar, 0.07 * S, "ivory", (0, 0, 1), 0.008, bone=False), "chest"))
    sash = C.ribbon("Sash", [B(0.12, -0.05, 1.30), B(0.0, -0.10, 1.12), B(-0.12, -0.05, 0.96)], 0.05 * S, "rose", (0, 0, 1), 0.005, bone=False)
    C.SKINNED.append((sash, ["spine", "chest"]))
    belt = [torus("Belt", "dark", 0.125 * S, 0.011 * S, B(0, 0.012, 0.915), (0, 0, 0), (1.0, 0.78, 1.0), 40), box("Buckle", "gold", (0.04 * S, 0.01, 0.03 * S), B(0, -0.096, 0.913), 0.004)]
    for o in belt:
        C.PARTS.append((o, "hips"))
    return panels


def build_head():
    head = C.build_head("Jhin head", jaw=1.0, chin=1.05, nose=1.0)
    h = C.HEAD
    # Dark hair swept back into a short tail.
    C.hair_cap("Jhin hair", "hair", front_y=0.04, front_z=0.075, scale=1.02)
    meta = metaball_object("Jhin hair tail", resolution=0.004)
    C.clump(meta, [h + Vector((0, 0.07, 0.04)), h + Vector((0, 0.11, -0.03)), h + Vector((0, 0.10, -0.12))], 0.025, 0.008)
    tail = C.mesh_from_meta(meta, "Jhin hair tail", voxel=0.0035, smooth=3, tris=2500)
    tail.data.materials.append(M["hair"])
    C.PARTS.append((tail, "head"))
    # The porcelain mask: a shell just proud of the face, eye slits, a gilded smile and crest.
    meta = metaball_object("Mask", resolution=0.004)
    ball(meta, h + Vector((0, -0.04, -0.005)), 0.085, (0.95, 0.75, 1.15))
    mask = C.mesh_from_meta(meta, "Mask", voxel=0.0035, smooth=3, tris=3000)
    C.delete_faces(mask, lambda c: c.y > h.y - 0.045)
    C.solidify(mask, 0.004)
    mask.data.materials.append(M["porcelain"])
    C.PARTS.append((mask, "head"))
    for sx in (1, -1):
        eye = h + Vector((0.036 * sx, -0.113, 0.004))
        C.PARTS.append((ball_mesh("Mask eye", "dark", eye, (0.02, 0.006, 0.008), 16, 8), "head"))
        C.PARTS.append((C.tube("Mask brow", [eye + Vector((-0.02 * sx, -0.002, 0.016)), eye + Vector((0.0, -0.004, 0.024)), eye + Vector((0.026 * sx, 0.0, 0.03))], 0.003, "gold", False), "head"))
    smile = [h + Vector((x, -0.118 + abs(x) * 0.5, -0.06 + (x / 0.035) ** 2 * 0.014)) for x in (-0.035, -0.018, 0.0, 0.018, 0.035)]
    C.PARTS.append((C.tube("Mask smile", smile, 0.0025, "gold", False), "head"))
    C.PARTS.append((C.tube("Mask crest", [h + Vector((0, -0.118, 0.03)), h + Vector((0, -0.112, 0.075)), h + Vector((0, -0.09, 0.11))], 0.004, "gold", False, taper=[0.5, 1.0, 0.4]), "head"))
    C.PARTS.append((ball_mesh("Mask rose", "rose", h + Vector((0.05, -0.105, 0.05)), (0.012, 0.008, 0.012), 12, 6), "head"))
    return head


def build_rifle():
    """Whisper: grip at the origin, long barrel toward -Y, stock toward +Y, ornaments on top."""
    parts = [
        box("Stock", "stock", (0.045, 0.24, 0.075), (0, 0.16, -0.02), 0.014),
        box("Stock inlay", "gold", (0.048, 0.18, 0.012), (0, 0.15, 0.01), 0.004),
        box("Receiver", "gold", (0.05, 0.16, 0.065), (0, -0.02, 0.012), 0.01),
        cyl("Grip", "dark", 0.016, 0.10, (0, 0.035, -0.055), (math.radians(25), 0, 0), 12),
        lathe("Barrel housing", "stock", [(0.03, -0.10), (0.033, -0.14), (0.028, -0.50), (0.022, -0.56)], 20),
        cyl("Barrel", "gold", 0.013, 0.30, (0, -0.70, 0.012), C.X90, 16),
        lathe("Muzzle bell", "gold", [(0.016, -0.84), (0.03, -0.88), (0.028, -0.90), (0.018, -0.90)], 20),
        box("Foregrip", "dark", (0.036, 0.10, 0.03), (0, -0.26, -0.025), 0.008),
        cyl("Scope", "dark", 0.018, 0.20, (0, -0.10, 0.08), C.X90, 16),
        cyl("Scope ring", "gold", 0.022, 0.02, (0, -0.19, 0.08), C.X90, 16),
        ball_mesh("Rose", "rose", (0.035, -0.32, 0.02), (0.022, 0.022, 0.022), 12, 8),
        ball_mesh("Chamber gem", "glow", (0, -0.05, 0.046), (0.012, 0.012, 0.008), 12, 6),
    ]
    for k in range(4):  # the four chambers
        parts.append(cyl("Chamber", "gold", 0.009, 0.03, (0.03, -0.02 - 0.03 * k, 0.012), C.X90, 10))
    for k in range(3):
        parts.append(lathe("Barrel ring", "gold", [(0.031, -0.18 - 0.11 * k), (0.031, -0.195 - 0.11 * k)], 20))
    return C.join(parts, "Whisper")


def build_grenade():
    parts = [ball_mesh("FX grenade", "gold", (0, 0, 0), (0.04, 0.04, 0.04), 16, 8)]
    for k in range(6):
        a = k * math.pi / 3
        parts.append(C.plate("FX petal", "rose", [(0, 0, 0.02), (math.cos(a) * 0.06, math.sin(a) * 0.06, 0.03), (math.cos(a + 0.4) * 0.05, math.sin(a + 0.4) * 0.05, 0.0)], 0.006, 0.0))
    return C.join(parts, "FX grenade")


def build_lotus():
    parts = [ball_mesh("FX lotus", "glow", (0, 0, 0.02), (0.03, 0.03, 0.02), 12, 6)]
    for k in range(8):
        a = k * math.pi / 4
        parts.append(C.plate("FX lotus petal", "rose", [(0, 0, 0.0), (math.cos(a) * 0.12, math.sin(a) * 0.12, 0.05), (math.cos(a + 0.35) * 0.09, math.sin(a + 0.35) * 0.09, 0.02)], 0.006, 0.0))
    return C.join(parts, "FX lotus")


CARRY = None


def build():
    global CARRY
    C.make_joints(scale=S, shoulder_x=0.195, hip_x=0.092)
    materials()
    body = build_body()
    panels = build_clothes()
    build_head()
    C.scale_parts("head", 1.05, C.J["head_bone"])
    rifle = build_rifle()
    # Rest: Whisper held across the body, grip at the right hip, barrel up past the left shoulder.
    CARRY = Matrix.Translation(B(-0.12, -0.13, 1.02)) @ (Matrix.Rotation(math.radians(55), 3, "Y") @ Matrix.Rotation(math.radians(-72), 3, "X") @ Matrix.Rotation(math.radians(-90), 3, "Y")).to_4x4()
    C.place(rifle, CARRY)
    muzzle = CARRY @ Matrix.Translation((0, -0.90, 0.012))
    fx = {
        "fx_muzzle": (C.fx_flash("muzzle", 0.04, "flash"), muzzle, "rifle"),
        "fx_shot": (C.fx_bolt("shot", 0.2, 0.014, "flash"), None, None),
        "fx_fourth": (C.fx_bolt("fourth shot", 0.4, 0.03, "glow", "flash", rings=2), None, None),
        "fx_beam": (C.fx_beam("deadly flourish", 6.0, 0.03, "glow", "flash"), None, None),
        "fx_grenade": (build_grenade(), None, None),
        "fx_lotus": (build_lotus(), None, None),
        "fx_curtain": (C.fx_bolt("curtain call", 0.6, 0.06, "glow", "flash", rings=3), None, None),
        "fx_bloom": (C.fx_flash("bloom", 0.12, "glow", 8), None, None),
    }
    grip = CARRY @ Vector((0, 0.0, -0.04))
    fore = CARRY @ Vector((0, -0.26, -0.035))
    extra = [C.weapon_bones("rifle", CARRY, (0, 0, 0), "chest", 0.3), C.grip_bone("grip_rifle.R", grip, "rifle"), C.grip_bone("grip_rifle.L", fore, "rifle")]
    extra += C.fx_bones(fx, Matrix.Translation(B(-0.2, -0.4, 1.3)))
    chains = C.coat_chains(panels, stiffness=50, gain=0.9, sway=2.0, limit=(50, 25))
    C.SOCKETS["socket_muzzle"] = ("rifle", muzzle)
    C.build_rig("Jhin rig", chains, extra, [("R", "rifle", "grip_rifle.R"), ("L", "rifle", "grip_rifle.L")])
    C.bind(body)
    C.attach(rifle, "rifle")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips()


FX = ["fx_muzzle", "fx_shot", "fx_fourth", "fx_beam", "fx_grenade", "fx_lotus", "fx_curtain", "fx_bloom"]


def define_clips():
    shoulder_aim = placement("rifle", B(-0.12, -0.22, 1.40), rx=1, rz=8)
    kneel_aim = placement("rifle", B(-0.10, -0.24, 1.03), rx=3, rz=8)

    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def muzzle_point(frame):
        return C.carried("rifle", frame, C.rig.data.bones["fx_muzzle"].head_local)

    def muzzle_dir(frame):
        return muzzle_point(frame) - C.carried("rifle", frame, C.rig.data.bones["rifle"].head_local)

    def shoot(name, frame_from, frame_to, distance=4.5):
        C.shoot_from(name, frame_from, frame_to, lambda: muzzle_point(frame_from), lambda: muzzle_dir(frame_from), distance)

    def stance(frame, breath=0.0, sway=0.0):
        """A performer's poise: upright, chin raised, Whisper held across the body."""
        loc("hips", frame, x=0.008 * sway, z=-0.01 - 0.004 * breath)
        rot("hips", frame, z=6 - 2 * sway)
        rot("spine", frame, x=-1 + breath, z=-3)
        rot("chest", frame, x=-4 + 1.5 * breath, z=-3 + sway)
        rot("head", frame, x=-8 + breath, y=-4 + 3 * sway, z=4)
        C.feet(frame, (0.02, -0.08, 0, -6), (-0.04, 0.04, 0, 28))
        loc("rifle", frame)
        rot("rifle", frame)
        ik("R", "rifle", frame, 1.0)
        ik("L", "rifle", frame, 1.0)
        loc("pole_elbow.R", frame, x=-0.2, y=0.2, z=-0.25)
        loc("pole_elbow.L", frame, x=0.1, y=0.1, z=-0.35)
        loc("root", frame)
        rot("root", frame)

    def aim(frame, matrix=None):
        rot("hips", frame, z=-14)
        loc("hips", frame, z=-0.03)
        rot("spine", frame, x=3, z=-12)
        rot("chest", frame, x=2, z=-14)
        rot("head", frame, x=8, y=4, z=22)
        loc("pole_elbow.R", frame, x=-0.25, y=0.2, z=0.05)
        loc("pole_elbow.L", frame, x=0.05, y=-0.1, z=-0.35)
        C.feet(frame, (0.05, -0.10, 0, -25), (-0.05, 0.10, 0, 30))
        ik("R", "rifle", frame, 1.0)
        ik("L", "rifle", frame, 1.0)
        weapon_matrix("rifle", matrix or shoulder_aim, frame)

    def recoil(frame, kick=0.06, pitch=-10, matrix=None):
        rot("chest", frame, x=-4, z=-10)
        rot("head", frame, x=2, y=4, z=18)
        weapon_matrix("rifle", Matrix.Translation(B(0, kick, kick * 0.6)) @ (matrix or shoulder_aim) @ Matrix.Rotation(math.radians(pitch), 4, "X"), frame)

    def start(frame=0):
        stance(frame)
        fx_off(frame)
        C.leg_ik(frame, 1.0)

    @clip("Idle", 72, loop=True)
    def idle():
        for f, breath, sway in ((0, 0, 0), (18, 1, 0.5), (36, 0, 1), (54, 1, 0.5), (72, 0, 0)):
            stance(f, breath, sway)
        fx_off(0)

    @clip("Walk", 18, loop=True)
    def run():
        def upper(frame, lead, phase):
            loc("rifle", frame)
            rot("rifle", frame)
            ik("R", "rifle", frame, 1.0)
            ik("L", "rifle", frame, 1.0)
            loc("pole_elbow.R", frame, x=-0.2, y=0.2, z=-0.25)
            loc("pole_elbow.L", frame, x=0.1, y=0.1, z=-0.35)

        C.run_cycle(upper, scale=S, lean=8, twist=7)
        fx_off(0)

    @clip("AA", 22)
    def attack():
        start()
        aim(6)
        flash("fx_muzzle", 9, 2, 1.2)
        shoot("fx_shot", 9, 14)
        recoil(10)
        aim(14)
        stance(22)

    @clip("P", 34)
    def whisper():
        start()
        # The fourth shot: a held breath, a flourish of the barrel, a blooming crit.
        aim(6)
        rot("head", 10, x=12, y=8, z=24)
        flash("fx_muzzle", 14, 4, 2.2)
        shoot("fx_fourth", 14, 20, 5.0)
        recoil(15, 0.09, -16)
        size("fx_bloom", 19, 0.0)
        C.put("fx_bloom", 20, B(-0.2, -5.0, 1.5))
        size("fx_bloom", 20, 1.6)
        size("fx_bloom", 25, 0.0)
        aim(20)
        stance(34)

    @clip("Q", 34)
    def dancing_grenade():
        start()
        # A theatrical overhand toss of the grenade with the left hand; it bounces ahead.
        ik("L", "rifle", 2, 1.0)
        ik("L", "rifle", 4, 0.0)
        fk_arm("L", 6, up=120, swing=40, bend=100, out=0, hand=20)
        rot("chest", 6, x=-8, z=14)
        fk_arm("L", 10, up=110, swing=-60, bend=20, out=-10, hand=-20)
        rot("chest", 10, x=6, z=-10)
        fk_arm("L", 14, up=40, swing=-70, bend=20, hand=-30)
        size("fx_grenade", 8, 0.0)
        C.later(lambda: C.put("fx_grenade", 9, C.carried("hand.L", 9, C.J["hand.L"])))
        size("fx_grenade", 9, 1.0)
        for f, co in ((14, B(0.2, -1.2, 1.4)), (18, B(0.2, -1.9, 0.1)), (21, B(0.0, -2.4, 0.6)), (24, B(-0.2, -2.9, 0.1)), (27, B(-0.3, -3.3, 0.4))):
            C.put("fx_grenade", f, co)
        size("fx_grenade", 27, 1.0)
        size("fx_grenade", 28, 0.0)
        size("fx_bloom", 27, 0.0)
        C.put("fx_bloom", 28, B(-0.3, -3.3, 0.4))
        size("fx_bloom", 28, 1.3)
        size("fx_bloom", 32, 0.0)
        ik("L", "rifle", 24, 0.0)
        ik("L", "rifle", 28, 1.0)
        stance(34)

    @clip("W", 36)
    def deadly_flourish():
        start()
        aim(6)
        rot("head", 10, x=10, y=6, z=24)
        flash("fx_muzzle", 16, 5, 2.4)
        size("fx_beam", 15, 0.0)
        C.later(lambda: C.put("fx_beam", 16, muzzle_point(16), (Vector((0, -1, 0)).rotation_difference(muzzle_dir(16)).to_matrix() @ C.rig.data.bones["fx_beam"].matrix_local.to_3x3())))
        size("fx_beam", 16, 1.0)
        size("fx_beam", 22, 1.0)
        size("fx_beam", 23, 0.0)
        recoil(17, 0.08, -14)
        aim(23)
        stance(36)

    @clip("E", 30)
    def captive_audience():
        start()
        # A bow to the audience: one knee bends, the left hand places a lotus trap.
        ik("L", "rifle", 2, 1.0)
        ik("L", "rifle", 5, 0.0)
        loc("hips", 9, z=-0.22, y=0.04)
        rot("spine", 9, x=30)
        rot("head", 9, x=20)
        C.feet(9, (0.06, -0.22, 0, -10), (-0.06, 0.12, 0, 25))
        fk_arm("L", 9, up=20, swing=-70, bend=20, out=-10, hand=-40)
        size("fx_lotus", 10, 0.0)
        C.put("fx_lotus", 11, B(0.15, -0.65, 0.0))
        size("fx_lotus", 11, 0.3)
        size("fx_lotus", 16, 1.0)
        size("fx_lotus", 30, 1.0)
        ik("L", "rifle", 18, 0.0)
        ik("L", "rifle", 22, 1.0)
        stance(30)

    @clip("R", 72)
    def curtain_call():
        start()
        # Kneel, Whisper levelled as a cannon: four heavy shots, the last a crescendo.
        loc("hips", 10, y=0.08, z=-0.36)
        rot("hips", 10, z=-18)
        C.feet(10, (0.06, -0.20, 0, -20), (-0.06, 0.22, 0.02, 30))
        rot("ik_foot.R", 10, x=-60, z=30)
        rot("spine", 12, x=6, z=-12)
        rot("chest", 12, x=6, z=-14)
        rot("head", 12, x=10, y=6, z=22)
        loc("pole_elbow.R", 12, x=-0.25, y=0.2, z=-0.1)
        loc("pole_elbow.L", 12, x=0.05, y=-0.1, z=-0.45)
        weapon_matrix("rifle", kneel_aim, 12)
        for k, f in enumerate((20, 32, 44, 56)):
            last = k == 3
            flash("fx_muzzle", f, 3, 3.0 if last else 2.0)
            shoot("fx_curtain", f, f + 7, 6.0)
            recoil(f + 1, 0.12 if last else 0.08, -20 if last else -12, kneel_aim)
            weapon_matrix("rifle", kneel_aim, f + 6)
        loc("hips", 62, y=0.08, z=-0.36)
        stance(72)

    @clip("Recall", 48, loop=True)
    def recall():
        # A conductor's flourish with the free hand, Whisper held at rest.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.3)
            ik("L", "rifle", f, 0.0)
            fk_arm("L", f, up=70 + 15 * s_, swing=-30, bend=60 - 20 * s_, out=10, hand=-20 + 30 * s_)
            rot("head", f, x=-14, z=6 * s_)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        ik("R", "rifle", 3, 1.0)
        ik("R", "rifle", 6, 0.0)
        ik("L", "rifle", 3, 1.0)
        ik("L", "rifle", 6, 0.0)
        loc("rifle", 5)
        rot("rifle", 5)
        weapon_matrix("rifle", placement("rifle", B(-0.40, -0.10, 0.05), rx=0, ry=85, rz=40), 16)
        C.fall_back(0, S)
