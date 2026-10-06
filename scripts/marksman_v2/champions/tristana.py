"""Tristana: an original stylized interpretation (blue-skinned yordle with oversized ears, a silver
hair crest, pilot goggles, and an oversized brass cannon carried on her shoulder)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, cyl, fk_arm, flash, ik, lathe, loc, material, metaball_object, placement, rot, size, torus, tube, weapon_matrix

S = 0.66
VIEW_SCALE = 0.85
RIM = (1.0, 0.65, 0.35)
EXPOSURE = -0.15
CLIP_VIEWS = {"W": dict(angle_deg=28, distance=4.2, height=1.6, target_z=1.0), "Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Blue skin", "#709dc3", rough=0.5, sss=0.15),
        navy=material("Navy flight suit", "#22334f", rough=0.6),
        red=material("Red scarf", "#9b3243", rough=0.6),
        cream=material("Cream", "#ede1ca", rough=0.6),
        brass=material("Brass", "#bc9658", rough=0.3, metal=1.0),
        iron=material("Cannon iron", (0.08, 0.08, 0.09), rough=0.35, metal=0.9),
        boot=material("Boots", (0.08, 0.045, 0.025), rough=0.45),
        hair=material("Silver hair", (0.62, 0.64, 0.72), rough=0.4),
        hair_dark=material("Grey hair", (0.5, 0.52, 0.6), rough=0.45),
        lens=material("Goggle lens", (0.95, 0.55, 0.15), rough=0.05, emission=0.6),
        fire=material("Cannon fire", "#ffbc68", emission=9.0),
        smoke=material("Smoke", (0.5, 0.5, 0.52), rough=0.9, alpha=0.6),
    )
    C.face_materials(iris=(0.9, 0.55, 0.15), lash=(0.05, 0.05, 0.1), lip=(0.35, 0.3, 0.55), brow=(0.85, 0.85, 0.9))


def build_body():
    meta = metaball_object("Tristana body")
    C.torso_female(meta, S, bust=0.85, hips=1.05, waist=1.0)
    C.limbs(meta, dict(neck=(0.06, 0.055), thigh=(0.095, 0.065), calf=(0.065, 0.07, 0.045), foot=(0.06, 0.05), arm=(0.065, 0.052), forearm=(0.055, 0.045), palm=0.06), hands="mitten")
    for side in ("L", "R"):
        toe = C.J[f"toe.{side}"]
        ball(meta, toe + Vector((0, -0.005, 0.01)), 0.05 * S, (1.0, 1.4, 0.8))  # big boots
        ball(meta, C.J[f"ankle.{side}"] + Vector((0, 0.0, 0.05 * S)), 0.06 * S, (1.0, 1.0, 0.8))
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.40, 0.95, 1.36)]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.75,)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            return "boot" if C.arm_fraction(c, side) > 0.75 else "navy"
        if z < 0.40:
            return "boot"
        if z > 1.36 and math.hypot(x, y - 0.01) < 0.07:
            return "skin"
        return "navy"

    return C.body_mesh(meta, "Tristana body", region, ["skin", "navy", "boot"], cuts)


def build_head():
    def extra(meta, h):
        ball(meta, h + Vector((0, -0.04, -0.05)), 0.05, (1.2, 0.8, 0.7))  # round cheeks

    C.build_head("Tristana head", jaw=0.9, chin=0.85, cheek=1.12, nose=1.25, width=1.05, extra=extra)
    C.build_face(eye_size=1.2, lashes="winged", brow_mat="brow", brow_width=0.0022, brow_angle=0.08, mouth="smile", mouth_size=0.0022)
    h = C.HEAD
    # Oversized pointed ears sweeping out and back.
    for sx in (1, -1):
        meta = metaball_object("Ear", resolution=0.004)
        C.clump(meta, [h + Vector((0.08 * sx, 0.0, 0.0)), h + Vector((0.16 * sx, 0.03, 0.04)), h + Vector((0.26 * sx, 0.06, 0.07))], 0.035, 0.004, flat=0.45)
        ear = C.mesh_from_meta(meta, "Ear", voxel=0.003, smooth=3, tris=1500)
        ear.data.materials.append(M["skin"])
        C.PARTS.append((ear, "head"))
    C.hair_cap("Tristana hair", "hair", front_y=0.04, front_z=0.06)
    meta = metaball_object("Hair crest", resolution=0.004)
    C.clump(meta, [h + Vector((0.0, -0.08, 0.09)), h + Vector((0.0, -0.06, 0.17)), h + Vector((0.0, 0.03, 0.20)), h + Vector((0.0, 0.10, 0.14))], 0.035, 0.012)
    for sx in (1, -1):
        C.clump(meta, [h + Vector((0.04 * sx, -0.085, 0.08)), h + Vector((0.07 * sx, -0.10, 0.03)), h + Vector((0.08 * sx, -0.09, -0.01))], 0.014, 0.004, flat=0.6)
    crest = C.mesh_from_meta(meta, "Hair crest", voxel=0.0035, smooth=3, tris=2500)
    C.paint_regions(crest, lambda c: "hair" if c.z > h.z + 0.08 else "hair_dark", ["hair", "hair_dark"])
    C.PARTS.append((crest, "head"))
    # Pilot goggles on the forehead and a strap.
    C.PARTS.append((torus("Goggle strap", "boot", 0.108, 0.008, h + Vector((0, 0.015, 0.075)), (math.radians(-18), 0, 0), (1.0, 1.06, 1.0), 40), "head"))
    for sx in (1, -1):
        centre = h + Vector((0.042 * sx, -0.088, 0.105))
        tilt = (math.radians(-55), 0, math.radians(-12 * sx))
        C.PARTS.append((cyl("Goggle rim", "brass", 0.029, 0.02, centre, tilt, 24), "head"))
        C.PARTS.append((cyl("Goggle lens", "lens", 0.023, 0.022, centre, tilt, 24), "head"))


def build_gear():
    scarf = metaball_object("Scarf", resolution=0.006)
    for d in range(0, 360, 24):
        a = math.radians(d)
        ball(scarf, B(math.sin(a) * 0.075, 0.012 - math.cos(a) * 0.07, 1.39), 0.03 * S, (1, 1, 0.8))
    wrap = C.mesh_from_meta(scarf, "Scarf", voxel=0.005, smooth=3, tris=2000)
    wrap.data.materials.append(M["red"])
    C.PARTS.append((wrap, "chest"))
    tail_pts = [B(0.04, 0.08, 1.38), B(0.06, 0.16, 1.30), B(0.07, 0.22, 1.18)]
    tail = C.ribbon("Scarf tail", tail_pts, 0.06 * S, "red", (1, 0, 0), 0.006, [1.0, 1.0, 0.8], bone=False)
    belt = [torus("Belt", "boot", 0.135 * S, 0.014 * S, B(0, 0.01, 0.95), (0, 0, 0), (1.0, 0.8, 1.0), 40), box("Buckle", "brass", (0.04 * S, 0.012, 0.03 * S), B(0, -0.10, 0.95), 0.004)]
    for o in belt:
        C.PARTS.append((o, "hips"))
    return tail_pts, tail


def build_cannon():
    """Boomer: grip at the origin, bore toward -Y, a big brass barrel and a back chamber."""
    parts = [
        lathe("Cannon barrel", "brass", [(0.0, 0.30), (0.08, 0.28), (0.10, 0.18), (0.09, 0.0), (0.075, -0.30), (0.09, -0.40), (0.095, -0.45), (0.07, -0.46)], 28),
        lathe("Barrel bands", "iron", [(0.103, 0.12), (0.103, 0.06)], 28),
        lathe("Barrel band 2", "iron", [(0.082, -0.20), (0.082, -0.24)], 28),
        lathe("Bore", "iron", [(0.05, -0.465), (0.05, -0.40)], 28),
        box("Grip", "boot", (0.04, 0.05, 0.12), (0, 0.0, -0.13), 0.01),
        box("Fore grip", "boot", (0.04, 0.04, 0.10), (0, -0.20, -0.12), 0.01),
        cyl("Sight", "brass", 0.015, 0.08, (0, -0.10, 0.11), C.X90, 12),
        ball_mesh("Fuse", "fire", (0.0, 0.25, 0.08), (0.012, 0.012, 0.012), 10, 6),
    ]
    for sx in (1, -1):
        parts.append(C.plate("Fin", "iron", [(0.08 * sx, 0.25, 0.0), (0.16 * sx, 0.32, 0.02), (0.09 * sx, 0.12, 0.0)], 0.012, 0.0))
    return C.join(parts, "Boomer")


def build():
    C.make_joints(scale=S, shoulder_x=0.20, hip_x=0.11, leg_length=0.78, arm_length=0.9)
    materials()
    body = build_body()
    tail_pts, tail = build_gear()
    build_head()
    C.scale_parts("head", 1.95, C.J["head_bone"])
    cannon = build_cannon()
    # Rest: carried on the right shoulder, bore forward, gripped with both hands below.
    sh = C.J["shoulder.R"]
    HOLD = Matrix.Translation(sh + Vector((0.0, -0.05, 0.02))) @ Matrix.Rotation(math.radians(4), 4, "X")
    C.place(cannon, HOLD @ Matrix.Translation((0, 0, 0.13)))
    muzzle = HOLD @ Matrix.Translation((0, -0.48, 0.13))
    fx = {
        "fx_muzzle": (C.fx_flash("muzzle", 0.07, "fire", 6), muzzle, "cannon"),
        "fx_ball": (C.fx_orb("cannonball", 0.06, "iron", 0), None, None),
        "fx_ball2": (C.fx_orb("cannonball 2", 0.06, "iron", 0), None, None),
        "fx_buster": (C.fx_bolt("buster shot", 0.5, 0.12, "fire", rings=2), None, None),
        "fx_smoke": (C.join([ball_mesh(f"FX smoke {k}", "smoke", (0.05 * k, 0.08 * k, 0.03 * k), (0.07, 0.07, 0.07), 12, 6) for k in range(4)], "FX smoke"), muzzle, "cannon"),
        "fx_blast": (C.fx_flash("rocket jump", 0.16, "fire", 8), None, None),
        "fx_bomb": (C.join([C.fx_orb("charge", 0.05, "red", 0), C.fx_flash("charge spark", 0.03, "fire", 4)], "FX charge"), None, None),
        "fx_boom": (C.fx_flash("explosion", 0.2, "fire", 10), None, None),
    }
    grip = HOLD @ Vector((0, 0.0, 0.0))
    fore = HOLD @ Vector((0, -0.20, 0.01))
    extra = [C.weapon_bones("cannon", HOLD, (0, 0, 0), "chest", 0.2), C.grip_bone("grip_cannon.R", grip, "cannon"), C.grip_bone("grip_cannon.L", fore, "cannon")]
    extra += C.fx_bones(fx, Matrix.Translation(B(-0.2, -0.6, 1.2)))
    chains = [("scarf", C.resample(tail_pts, 2), "chest", dict(skin=True, stiffness=45, gain=1.1, sway=3.0, limit=(50, 30)))]
    C.SKINNED.append((tail, ["chest", "scarf.0", "scarf.1"]))
    C.SOCKETS["socket_muzzle"] = ("cannon", muzzle)
    C.build_rig("Tristana rig", chains, extra, [("R", "cannon", "grip_cannon.R"), ("L", "cannon", "grip_cannon.L")])
    C.bind(body)
    C.attach(cannon, "cannon")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips()


FX = ["fx_muzzle", "fx_ball", "fx_ball2", "fx_buster", "fx_smoke", "fx_blast", "fx_bomb", "fx_boom"]


def define_clips():
    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def muzzle_at(frame):
        return C.carried("cannon", frame, C.rig.data.bones["fx_muzzle"].head_local)

    def bore(frame):
        return muzzle_at(frame) - C.carried("cannon", frame, C.rig.data.bones["cannon"].head_local + Vector((0, 0, 0.13)))

    def fire(frame, name, distance=4.0, peak=1.4, kick=0.05):
        flash("fx_muzzle", frame, 3, peak)
        size("fx_smoke", frame, 0.0)
        size("fx_smoke", frame + 2, 1.0)
        size("fx_smoke", frame + 10, 1.4)
        size("fx_smoke", frame + 11, 0.0)
        C.shoot_from(name, frame, frame + 6, lambda: muzzle_at(frame), lambda: bore(frame), distance)
        loc("cannon", frame)
        rot("cannon", frame)
        loc("cannon", frame + 1, y=kick, z=kick * 0.4)
        rot("cannon", frame + 1, x=-8)
        rot("chest", frame + 1, x=-6)
        loc("cannon", frame + 5)
        rot("cannon", frame + 5)

    def stance(frame, breath=0.0, sway=0.0):
        """Plucky, wide stance with Boomer on her shoulder."""
        loc("hips", frame, x=0.006 * sway, z=-0.02 - 0.006 * breath)
        rot("hips", frame, z=-6 + 2 * sway)
        rot("spine", frame, x=2 + breath)
        rot("chest", frame, x=-2 + 1.5 * breath, z=4 - sway)
        rot("head", frame, x=-4 + breath, z=-8 + 4 * sway)
        C.feet(frame, (0.05, -0.04, 0, -18), (-0.05, 0.04, 0, 22))
        loc("cannon", frame)
        rot("cannon", frame)
        ik("R", "cannon", frame, 1.0)
        ik("L", "cannon", frame, 1.0)
        loc("pole_elbow.R", frame, x=-0.1, y=0.1, z=-0.25)
        loc("pole_elbow.L", frame, x=0.1, y=-0.1, z=-0.3)
        loc("root", frame)
        rot("root", frame)

    def start(frame=0):
        stance(frame)
        fx_off(frame)

    @clip("Idle", 72, loop=True)
    def idle():
        for f, breath, sway in ((0, 0, 0), (18, 1, 0.5), (36, 0, 1), (54, 1, 0.5), (72, 0, 0)):
            stance(f, breath, sway)
        fx_off(0)

    @clip("Walk", 16, loop=True)
    def run():
        def upper(frame, lead, phase):
            loc("cannon", frame, z=0.008 * phase)
            rot("cannon", frame)
            ik("R", "cannon", frame, 1.0)
            ik("L", "cannon", frame, 1.0)
            loc("pole_elbow.R", frame, x=-0.1, y=0.1, z=-0.25)
            loc("pole_elbow.L", frame, x=0.1, y=-0.1, z=-0.3)

        C.run_cycle(upper, scale=S, lean=12, twist=10, stride=0.9)
        fx_off(0)

    @clip("AA", 22)
    def attack():
        start()
        rot("chest", 3, x=2, z=0)
        rot("head", 3, x=2, z=-2)
        fire(6, "fx_ball")
        stance(22)

    @clip("P", 30)
    def draw_a_bead():
        start()
        # A squint down the sight: goggles flip down, a glint, a grin.
        rot("head", 6, x=10, z=-14, y=-8)
        rot("chest", 6, x=4)
        size("fx_muzzle", 10, 0.0)
        size("fx_muzzle", 13, 0.5)
        size("fx_muzzle", 15, 0.0)
        rot("head", 18, x=-6, z=-4)
        stance(30)

    @clip("Q", 30)
    def rapid_fire():
        start()
        for k, f in enumerate((4, 9, 14, 19)):
            fire(f, "fx_ball" if k % 2 == 0 else "fx_ball2", 4.0, 1.2, 0.035)
        stance(30)

    @clip("W", 34)
    def rocket_jump():
        start()
        moving = bool(C.OPTIONS.get("root_motion"))
        reach = -1.8 if moving else 0.0
        # Cannon blasts the ground; she rockets up in an arc and lands in a crouch.
        loc("hips", 3, z=-0.06)
        weapon_matrix("cannon", placement("cannon", C.J["shoulder.R"] + Vector((0.0, 0.05, -0.05)), rx=-70, rz=0), 4)
        size("fx_blast", 4, 0.0)
        C.put("fx_blast", 5, B(0, 0.1, 0.05))
        size("fx_blast", 5, 1.4)
        size("fx_blast", 11, 0.0)
        loc("root", 4)
        loc("root", 12, y=reach * 0.5, z=0.65)
        loc("root", 20, y=reach * 0.9, z=0.25)
        loc("root", 23, y=reach)
        for side in ("L", "R"):
            loc(f"ik_foot.{side}", 12, x=0.02 * C.side_x(side), y=0.06, z=0.10)
            rot(f"ik_foot.{side}", 12, x=-30)
        rot("spine", 12, x=-10)
        loc("cannon", 14)
        rot("cannon", 14)
        loc("hips", 24, z=-0.10)
        stance(34)
        for f in (24, 34):
            loc("root", f, y=reach)

    @clip("E", 40)
    def explosive_charge():
        start()
        # A bomb lobbed onto the target; it ticks and blows.
        fk_arm("L", 4, up=40, swing=30, bend=90)
        ik("L", "cannon", 3, 1.0)
        ik("L", "cannon", 5, 0.0)
        fk_arm("L", 8, up=60, swing=-70, bend=20)
        target = B(0.1, -3.0, 0.9)
        C.fly_path("fx_bomb", [(8, lambda: C.carried("hand.L", 8, C.J["hand.L"])), (14, target + Vector((0, 1.0, 0.8))), (18, target)], (0, 0, 1), 0.0)
        size("fx_bomb", 7, 0.0)
        size("fx_bomb", 8, 1.0)
        for k, f in enumerate(range(18, 30, 3)):
            size("fx_bomb", f, 1.0 + 0.15 * (k % 2))
        size("fx_bomb", 30, 0.0)
        size("fx_boom", 29, 0.0)
        C.put("fx_boom", 30, target)
        size("fx_boom", 30, 1.8)
        size("fx_boom", 36, 0.0)
        ik("L", "cannon", 14, 0.0)
        ik("L", "cannon", 18, 1.0)
        stance(40)

    @clip("R", 44)
    def buster_shot():
        start()
        moving = bool(C.OPTIONS.get("root_motion"))
        # Brace, a massive shot; the recoil shoves her back on her heels.
        loc("hips", 6, z=-0.08)
        C.feet(6, (0.07, -0.10, 0, -20), (-0.07, 0.10, 0, 28))
        size("fx_muzzle", 6, 0.0)
        size("fx_muzzle", 12, 0.8)
        fire(14, "fx_buster", 5.0, 2.6, 0.12)
        loc("root", 14)
        loc("root", 20, y=0.35 if moving else 0.08)
        rot("spine", 16, x=-12)
        rot("head", 16, x=-14)
        loc("hips", 20, z=-0.06)
        stance(44)
        loc("root", 44, y=0.35 if moving else 0.0)

    @clip("Recall", 48, loop=True)
    def recall():
        # Boomer set down, she sits on it swinging her legs.
        rest = placement("cannon", B(0.10, 0.05, 0.25), rx=0, rz=90)
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.0)
            weapon_matrix("cannon", rest, f)
            ik("R", "cannon", f, 0.0)
            ik("L", "cannon", f, 0.0)
            loc("hips", f, z=-0.20, y=0.08)
            for side in ("L", "R"):
                sx = C.side_x(side)
                swing = 0.05 * s_ * (1 if side == "L" else -1)
                loc(f"ik_foot.{side}", f, x=0.03 * sx, y=-0.12 + swing, z=0.04)
                fk_arm(side, f, up=10, swing=10, bend=30, out=10)
            rot("head", f, x=-6, z=6 * s_)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        for side in ("L", "R"):
            ik(side, "cannon", 3, 1.0)
            ik(side, "cannon", 6, 0.0)
        loc("cannon", 5)
        rot("cannon", 5)
        weapon_matrix("cannon", placement("cannon", B(-0.4, -0.1, 0.10), rx=0, ry=80, rz=30), 14)
        C.fall_back(0, S)
