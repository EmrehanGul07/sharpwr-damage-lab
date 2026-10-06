"""Zeri: an original stylized interpretation (bright green twin hair knots, oversized yellow jacket,
teal shirt, articulated electric rifle with a battery pack on her back)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, cyl, fk_arm, flash, ik, lathe, loc, material, metaball_object, placement, rot, size, torus, tube, weapon_matrix

S = 0.98
RIM = (0.75, 1.0, 0.35)
EXPOSURE = -0.15
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55), "E": dict(angle_deg=28, distance=3.9, height=1.2, target_z=0.85)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#b98862", rough=0.5, sss=0.12),
        teal=material("Teal shirt", "#19635b", rough=0.6),
        yellow=material("Yellow jacket", "#d0ae3c", rough=0.6),
        green=material("Lime", "#91c450", rough=0.5),
        metal=material("Olive metal", "#796938", rough=0.35, metal=0.8),
        dark=material("Dark", (0.03, 0.035, 0.03), rough=0.5),
        shoe=material("Sneakers", (0.85, 0.85, 0.8), rough=0.5),
        hair=material("Green hair", (0.25, 0.75, 0.08), rough=0.45),
        hair_dark=material("Deep green hair", (0.08, 0.35, 0.03), rough=0.5),
        spark=material("Spark", "#c8ff58", emission=8.0),
    )
    C.face_materials(iris=(0.4, 0.75, 0.2), lash=(0.02, 0.02, 0.01), lip=(0.5, 0.25, 0.22))


def build_body():
    meta = metaball_object("Zeri body")
    C.torso_female(meta, S, bust=0.9, hips=0.95, waist=0.92)
    # The oversized jacket: puffed shoulders and sleeves.
    for sx in (1, -1):
        ball(meta, B(0.15 * sx, 0.012, 1.34), 0.07 * S, (1.2, 1.1, 0.8))
    C.limbs(meta, dict(thigh=(0.062, 0.040), calf=(0.040, 0.045, 0.03), arm=(0.052, 0.042), forearm=(0.042, 0.03), palm=0.032), hands="mitten")
    for side in ("L", "R"):
        toe = C.J[f"toe.{side}"]
        ball(meta, toe + Vector((0, 0.005, 0.01)), 0.042 * S, (1.0, 1.3, 0.75))  # chunky sneakers
        ball(meta, C.J[f"ankle.{side}"] + Vector((0, 0.0, 0.01)), 0.04 * S)
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.12, 0.62, 0.92, 1.04, 1.40)]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.68, 0.80)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            f = C.arm_fraction(c, side)
            return "dark" if f > 0.80 else "green" if f > 0.68 else "yellow"
        if z < 0.12:
            return "shoe"
        if z < 0.62:
            return "skin"
        if z < 0.92:
            return "dark"  # shorts
        if z < 1.04:
            return "teal"
        if z > 1.40 and math.hypot(x, y - 0.01) < 0.065:
            return "skin"
        if y < -0.04 and abs(x) < 0.07:
            return "teal"  # shirt in the open jacket
        return "yellow"

    return C.body_mesh(meta, "Zeri body", region, ["skin", "teal", "yellow", "green", "dark", "shoe"], cuts)


def build_head():
    C.build_head("Zeri head", jaw=0.94, chin=0.95, nose=0.9)
    C.build_face(eye_size=1.08, lashes="winged", brow_mat="hair_dark", brow_width=0.002, brow_angle=0.05, mouth="smile", mouth_size=0.002)
    h = C.HEAD
    C.hair_cap("Zeri hair", "hair", front_y=0.045, front_z=0.055)
    meta = metaball_object("Zeri hair", resolution=0.004)
    # Two big knots on top with jagged, lightning-like spikes and a choppy fringe.
    for sx in (1, -1):
        knot = h + Vector((0.065 * sx, 0.02, 0.13))
        ball(meta, knot, 0.045, (1.0, 1.0, 0.9))
        for k in range(4):
            a = math.radians(30 + 40 * k) * sx
            tip = knot + Vector((math.sin(a) * 0.09, 0.02 * k - 0.03, 0.03 + 0.03 * (k % 2)))
            C.clump(meta, [knot, knot.lerp(tip, 0.5) + Vector((0, 0, 0.015)), tip], 0.016, 0.003)
    for i, x in enumerate((0.05, 0.02, -0.01, -0.04)):
        C.clump(meta, [h + Vector((x * 0.6, -0.07, 0.10)), h + Vector((x + 0.01, -0.10, 0.06)), h + Vector((x + 0.015 * (-1) ** i, -0.098, 0.025))], 0.015, 0.004, flat=0.6)
    hair = C.mesh_from_meta(meta, "Zeri hair", voxel=0.0035, smooth=3, tris=4500)
    C.paint_regions(hair, lambda c: "hair" if c.z > h.z + 0.09 or c.y < h.y - 0.08 else "hair_dark", ["hair", "hair_dark"])
    C.PARTS.append((hair, "head"))
    for sx in (1, -1):
        C.PARTS.append((torus("Knot band", "spark", 0.035, 0.005, h + Vector((0.065 * sx, 0.02, 0.10)), (0, 0, 0), (1, 1, 1), 18), "head"))


def build_rifle():
    """The electric rifle: grip at the origin, barrel toward -Y, coils and a cable port."""
    parts = [
        box("Rifle body", "metal", (0.06, 0.30, 0.08), (0, -0.06, 0.03), 0.015),
        box("Rifle shell", "yellow", (0.065, 0.16, 0.05), (0, -0.04, 0.07), 0.012),
        cyl("Rifle barrel", "dark", 0.016, 0.30, (0, -0.32, 0.04), C.X90, 14),
        box("Grip", "dark", (0.028, 0.04, 0.10), (0, 0.04, -0.03), 0.008, (math.radians(-15), 0, 0)),
        box("Stock", "metal", (0.045, 0.12, 0.06), (0, 0.15, 0.02), 0.012),
        box("Fore grip", "dark", (0.03, 0.05, 0.07), (0, -0.20, -0.02), 0.008),
    ]
    for k in range(4):
        parts.append(torus("Coil", "spark", 0.028, 0.005, (0, -0.24 - 0.06 * k, 0.04), (math.pi / 2, 0, 0), (1, 1, 1), 16))
    parts.append(ball_mesh("Core", "spark", (0.034, -0.05, 0.04), (0.012, 0.03, 0.012), 10, 6))
    return C.join(parts, "Electric rifle")


def build():
    C.make_joints(scale=S, shoulder_x=0.182, hip_x=0.093)
    materials()
    body = build_body()
    build_head()
    C.scale_parts("head", 1.09, C.J["head_bone"])
    # Battery pack on her back, cable to the rifle.
    pack = C.join([box("Battery", "metal", (0.16 * S, 0.08 * S, 0.20 * S), B(0, 0.14, 1.18), 0.02), box("Battery cell", "spark", (0.10 * S, 0.084 * S, 0.03 * S), B(0, 0.142, 1.22), 0.005), box("Battery cell 2", "spark", (0.10 * S, 0.084 * S, 0.03 * S), B(0, 0.142, 1.15), 0.005)], "Battery pack")
    C.PARTS.append((pack, "chest"))
    rifle = build_rifle()
    HOLD = Matrix.Translation(B(-0.20, -0.14, 1.0)) @ Matrix.Rotation(math.radians(-6), 4, "X") @ Matrix.Rotation(math.radians(6), 4, "Z")
    C.place(rifle, HOLD)
    cable = tube("Cable", [B(-0.06, 0.18, 1.10), B(-0.16, 0.14, 0.98), HOLD @ Vector((0, 0.18, 0.02))], 0.008, "dark", False)
    C.SKINNED.append((cable, ["chest", "hips", "rifle"]))
    muzzle = HOLD @ Matrix.Translation((0, -0.48, 0.04))
    fx = {
        "fx_flash": (C.fx_flash("spark flash", 0.035, "spark"), muzzle, "rifle"),
        "fx_laser": (C.fx_beam("ultrashock laser", 5.0, 0.035, "spark"), None, None),
        "fx_ring": (C.join([C.torus("FX lightning crash", "spark", 0.6 + 0.25 * k, 0.012, (0, 0, 0.0), (0, 0, 0), (1, 1, 1), 40) for k in range(3)], "FX lightning crash"), Matrix.Translation(B(0, 0, 0.6)), "root"),
        "fx_trail": (C.fx_flash("spark trail", 0.10, "spark", 6), None, None),
        "fx_charge": (C.fx_orb("living battery", 0.12, "spark", 2), Matrix.Translation(B(0, 0.15, 1.18)), "chest"),
    }
    for k in range(7):
        fx[f"fx_shot.{k}"] = (C.fx_bolt(f"spark {k}", 0.14, 0.012, "spark"), None, None)
    grip = HOLD @ Vector((0, 0.04, -0.03))
    fore = HOLD @ Vector((0, -0.20, -0.03))
    extra = [C.weapon_bones("rifle", HOLD, (0, 0, 0), "hips", 0.25), C.grip_bone("grip_rifle.R", grip, "rifle"), C.grip_bone("grip_rifle.L", fore, "rifle")]
    C.DEFORM_LATER.append("rifle")
    extra += C.fx_bones(fx, Matrix.Translation(B(-0.2, -0.5, 1.1)))
    C.SOCKETS["socket_muzzle"] = ("rifle", muzzle)
    C.build_rig("Zeri rig", [], extra, [("R", "rifle", "grip_rifle.R"), ("L", "rifle", "grip_rifle.L")])
    C.bind(body)
    C.attach(rifle, "rifle")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips(HOLD)


SHOTS = [f"fx_shot.{k}" for k in range(7)]
FX = ["fx_flash", "fx_laser", "fx_ring", "fx_trail", "fx_charge"] + SHOTS


def define_clips(HOLD):
    aim = placement("rifle", B(-0.14, -0.22, 1.08), rx=2, rz=4)

    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def muzzle_at(frame):
        return C.carried("rifle", frame, C.rig.data.bones["fx_flash"].head_local)

    def bore(frame):
        return muzzle_at(frame) - C.carried("rifle", frame, C.rig.data.bones["rifle"].head_local)

    def fire(frame, name, distance=4.0, peak=1.0):
        flash("fx_flash", frame, 1, peak)
        C.shoot_from(name, frame, frame + 5, lambda: muzzle_at(frame), lambda: bore(frame), distance)

    def stance(frame, breath=0.0, sway=0.0):
        """Bouncy, eager stance with the rifle at the hip."""
        loc("hips", frame, x=0.01 * sway, z=-0.03 - 0.012 * breath)
        rot("hips", frame, z=-6 + 3 * sway)
        rot("spine", frame, x=3 + breath, z=4)
        rot("chest", frame, x=1 + 1.5 * breath, z=4 - sway)
        rot("head", frame, x=-6 + 2 * breath, y=4 * sway, z=-6 + 3 * sway)
        C.feet(frame, (0.06, -0.08, 0, -16), (-0.06, 0.08, 0, 20))
        loc("rifle", frame)
        rot("rifle", frame)
        ik("R", "rifle", frame, 1.0)
        ik("L", "rifle", frame, 1.0)
        loc("pole_elbow.R", frame, x=-0.15, y=0.2, z=-0.2)
        loc("pole_elbow.L", frame, x=0.05, y=-0.1, z=-0.35)
        loc("root", frame)
        rot("root", frame)

    def brace(frame):
        rot("hips", frame, z=-12)
        loc("hips", frame, z=-0.05)
        rot("spine", frame, x=5, z=-6)
        rot("chest", frame, x=3, z=-8)
        rot("head", frame, x=2, z=16)
        C.feet(frame, (0.07, -0.12, 0, -22), (-0.06, 0.10, 0, 28))
        weapon_matrix("rifle", aim, frame)

    def start(frame=0):
        stance(frame)
        fx_off(frame)

    @clip("Idle", 48, loop=True)
    def idle():
        for f, breath, sway in ((0, 0, 0), (12, 1, 0.5), (24, 0, 1), (36, 1, 0.5), (48, 0, 0)):
            stance(f, breath, sway)
        fx_off(0)
        for f in (10, 34):  # crackling sparks
            size("fx_flash", f - 1, 0.0)
            size("fx_flash", f, 0.4)
            size("fx_flash", f + 2, 0.0)

    @clip("Walk", 18, loop=True)
    def run():
        def upper(frame, lead, phase):
            loc("rifle", frame, z=0.01 * phase)
            rot("rifle", frame)
            ik("R", "rifle", frame, 1.0)
            ik("L", "rifle", frame, 1.0)
            loc("pole_elbow.R", frame, x=-0.15, y=0.2, z=-0.2)
            loc("pole_elbow.L", frame, x=0.05, y=-0.1, z=-0.35)

        C.run_cycle(upper, scale=S, lean=13, twist=9)
        fx_off(0)

    @clip("AA", 22)
    def attack():
        start()
        brace(4)
        for k, f in enumerate((6, 8, 10)):
            fire(f, SHOTS[k], 4.0, 0.9)
            weapon_matrix("rifle", Matrix.Translation(B(0, 0.02, 0.01)) @ aim, f + 1)
        brace(13)
        stance(22)

    @clip("Q", 28)
    def burst_fire():
        start()
        brace(4)
        for k, f in enumerate(range(6, 20, 2)):
            fire(f, SHOTS[k], 4.0, 1.1)
            weapon_matrix("rifle", Matrix.Translation(B(0, 0.025, 0.012)) @ aim, f + 1)
        brace(21)
        stance(28)

    @clip("P", 30)
    def living_battery():
        start()
        # Sparks race over her as the battery charges; a little hop of excitement.
        size("fx_charge", 4, 0.0)
        size("fx_charge", 10, 1.4)
        size("fx_charge", 20, 0.6)
        size("fx_charge", 24, 0.0)
        loc("root", 8)
        loc("root", 13, z=0.12)
        loc("root", 18)
        rot("head", 12, x=-10, z=10)
        stance(30)

    @clip("W", 36)
    def ultrashock_laser():
        start()
        brace(6)
        size("fx_flash", 6, 0.0)
        size("fx_flash", 14, 1.2)
        flash("fx_flash", 15, 4, 2.0)
        size("fx_laser", 14, 0.0)
        size("fx_laser", 15, 1.0)
        size("fx_laser", 22, 1.0)
        size("fx_laser", 23, 0.0)

        @C.later
        def laser():
            r = Vector((0, -1, 0)).rotation_difference(bore(15)).to_matrix() @ C.rig.data.bones["fx_laser"].matrix_local.to_3x3()
            C.put("fx_laser", 15, muzzle_at(15), r)
            C.put("fx_laser", 22, muzzle_at(22), r)

        weapon_matrix("rifle", Matrix.Translation(B(0, 0.05, 0.03)) @ aim @ Matrix.Rotation(math.radians(-10), 4, "X"), 16)
        brace(22)
        stance(36)

    @clip("E", 24)
    def spark_surge():
        start()
        moving = bool(C.OPTIONS.get("root_motion"))
        reach = -1.5 if moving else 0.0
        # A low electric dash with a spark trail, then a quick burst.
        loc("hips", 3, z=-0.10)
        rot("spine", 3, x=22)
        loc("root", 3)
        loc("root", 9, y=reach, z=0.05)
        C.feet(7, (0.05, 0.20, 0.12, -40), (-0.05, 0.26, 0.18, -50))
        rot("spine", 7, x=28)
        size("fx_trail", 3, 0.0)
        C.put("fx_trail", 4, B(0, -0.2, 0.5))
        size("fx_trail", 4, 1.3)
        size("fx_trail", 9, 0.0)
        brace(11)
        for k, f in enumerate((13, 15, 17)):
            fire(f, SHOTS[k], 3.5, 0.9)
        stance(24)
        for f in (11, 24):
            loc("root", f, y=reach)

    @clip("R", 44)
    def lightning_crash():
        start()
        # Crouch and charge, then a burst of lightning rings out around her.
        loc("hips", 6, z=-0.14)
        rot("spine", 6, x=16)
        rot("head", 6, x=10)
        loc("hips", 12, z=0.0)
        rot("spine", 12, x=-10)
        rot("chest", 12, x=-10)
        rot("head", 12, x=-16)
        size("fx_ring", 11, 0.0)
        size("fx_ring", 12, 0.3)
        size("fx_ring", 18, 1.6)
        size("fx_ring", 22, 0.0)
        size("fx_charge", 6, 0.0)
        size("fx_charge", 11, 1.6)
        size("fx_charge", 13, 0.0)
        stance(44)

    @clip("Recall", 48, loop=True)
    def recall():
        # Rifle on her shoulder, bopping her head to music in her ears.
        rest = placement("rifle", B(-0.14, 0.05, 1.42), rx=55, rz=180, roll=0)
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.5 + 0.5 * s_)
            weapon_matrix("rifle", rest, f)
            ik("L", "rifle", f, 0.0)
            fk_arm("L", f, up=8, swing=-10, bend=30, twist=10, hand=-10)
            rot("head", f, x=-4 + 6 * abs(s_), z=10 * s_)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        for side in ("L", "R"):
            ik(side, "rifle", 3, 1.0)
            ik(side, "rifle", 6, 0.0)
        loc("rifle", 5)
        rot("rifle", 5)
        weapon_matrix("rifle", placement("rifle", B(-0.40, -0.10, 0.06), rx=0, ry=80, rz=30), 14)
        C.fall_back(0, S)
