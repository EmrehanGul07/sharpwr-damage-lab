"""Varus: an original stylized interpretation (pale archer, flowing white hair, black-violet
corrupted lower body and arm, sculptural living bow)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, fk_arm, flash, ik, lathe, loc, material, metaball_object, placement, rot, size, torus, tube, weapon_matrix

S = 1.06
RIM = (0.9, 0.45, 1.0)
EXPOSURE = -0.15
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Pale skin", "#d2c4c6", rough=0.5, sss=0.15),
        dark=material("Corruption", "#211d3f", rough=0.35, metal=0.3),
        violet=material("Corrupted violet", "#663558", rough=0.35, metal=0.3),
        silver=material("Silver", "#c1c5cd", rough=0.3, metal=0.9),
        mauve=material("Mauve", "#aa8394", rough=0.35, metal=0.6),
        cloth=material("Cloth", (0.06, 0.05, 0.09), rough=0.6),
        hair=material("White hair", (0.85, 0.84, 0.88), rough=0.45),
        hair_dark=material("Grey hair", (0.55, 0.54, 0.6), rough=0.5),
        bow=material("Living bow", (0.12, 0.05, 0.14), rough=0.3, metal=0.2),
        glow=material("Corruption glow", "#e678ea", emission=7.0),
        string=material("Bow string", (0.95, 0.6, 1.0), emission=3.0),
    )
    C.face_materials(iris=(0.85, 0.3, 0.9), lash=(0.05, 0.04, 0.06), lip=(0.5, 0.35, 0.4), brow=(0.7, 0.7, 0.75))


def build_body():
    meta = metaball_object("Varus body")
    C.torso_male(meta, S, chest=1.05, waist=0.95, shoulders=1.05)
    ball(meta, B(0, 0.01, 0.885), 0.125 * S, (1.05, 0.8, 0.35))
    C.limbs(meta, dict(neck=(0.054, 0.047), thigh=(0.07, 0.047), calf=(0.048, 0.054, 0.034), foot=(0.042, 0.035), arm=(0.052, 0.038), forearm=(0.04, 0.03), palm=0.036), hands="mitten")
    for side in ("L", "R"):
        knee, toe = C.J[f"knee.{side}"], C.J[f"toe.{side}"]
        ball(meta, knee + Vector((0, -0.02, 0.0)), 0.05 * S, (1.0, 0.8, 1.1))
        ball(meta, toe + Vector((0, 0.01, 0.004)), 0.042 * S, (0.95, 1.3, 0.7))
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.95, 1.12, 1.385)]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.35, 0.55)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.21 and z > 0.88:
            f = C.arm_fraction(c, side)
            if side == "L":  # the corrupted bow arm
                return "dark" if f > 0.35 else "violet"
            return "skin" if f > 0.55 else "cloth"
        if z < 0.95:
            return "dark"  # corrupted lower body
        if z < 1.12:
            return "violet"
        if z > 1.385 and math.hypot(x, y - 0.01) < 0.075:
            return "skin"
        return "cloth"

    return C.body_mesh(meta, "Varus body", region, ["skin", "dark", "violet", "cloth"], cuts)


def build_gear():
    # Corruption growths: spines along the legs and the bow arm, glowing veins.
    for side, sx in (("L", 1), ("R", -1)):
        hip, knee, ankle = (C.J[f"{n}.{side}"] for n in ("hip", "knee", "ankle"))
        for k, t in enumerate((0.3, 0.6, 0.9)):
            base = hip.lerp(knee, t) + Vector((0.05 * sx, 0.03, 0))
            spine = C.cone("Corruption spine", "violet", 0.018, 0.0, 0.08, base + Vector((0.02 * sx, 0.02, 0)), (math.radians(-60), math.radians(40 * sx), 0), 5)
            C.PARTS.append((spine, f"thigh.{side}"))
        vein = tube("Vein", [hip + Vector((0.03 * sx, -0.06, -0.05)), hip.lerp(knee, 0.5) + Vector((0.01 * sx, -0.065, 0)), knee + Vector((0, -0.05, -0.02))], 0.006, "glow", False)
        C.SKINNED.append((vein, [f"thigh.{side}", "hips"]))
        pad = lathe("Pauldron", "mauve" if side == "L" else "silver", [(0.0, 0.05), (0.05, 0.045), (0.075, 0.02), (0.08, -0.02)], 20, "Z")
        C.place(pad, Matrix.Translation(B(0.17 * sx, 0.012, 1.375)) @ Matrix.Rotation(math.radians(-30 * sx), 4, "Y"))
        C.PARTS.append((pad, f"shoulder.{side}"))
    sh, el = C.J["shoulder.L"], C.J["elbow.L"]
    for k in range(3):
        spike = C.cone("Arm spike", "violet", 0.015, 0.0, 0.07, sh.lerp(el, 0.4 + 0.2 * k) + Vector((0.03, 0.02, 0.02)), (math.radians(-40), math.radians(60), 0), 5)
        C.PARTS.append((spike, "upper_arm.L"))
    belt = [torus("Belt", "silver", 0.128 * S, 0.012 * S, B(0, 0.012, 0.95), (0, 0, 0), (1.0, 0.8, 1.0), 40), ball_mesh("Belt gem", "glow", B(0, -0.098, 0.95), (0.014, 0.008, 0.014), 12, 6)]
    for o in belt:
        C.PARTS.append((o, "hips"))
    panels = C.coat_panels(
        [("front", 0.0, -0.105, 0.14, 0.95, 0.50, 0.0), ("back", 0.0, 0.11, 0.15, 0.95, 0.48, 0.0)],
        "cloth",
        S,
    )
    return panels


def build_head():
    C.build_head("Varus head", jaw=1.04, chin=1.05, nose=1.05)
    C.build_face(eye_size=0.88, lashes="soft", brow_mat="brow", brow_width=0.0028, brow_angle=0.16, mouth="flat", mouth_size=0.0021, mouth_width=1.1)
    h = C.HEAD
    C.hair_cap("Varus hair", "hair", front_y=0.04, front_z=0.07, scale=1.03)
    meta = metaball_object("Varus hair", resolution=0.0045)
    for sx in (1, -1):
        C.clump(meta, [h + Vector((0.06 * sx, -0.075, 0.09)), h + Vector((0.095 * sx, -0.06, 0.01)), h + Vector((0.10 * sx, -0.04, -0.10)), h + Vector((0.11 * sx, -0.02, -0.20))], 0.02, 0.007, flat=0.6)
    front = C.mesh_from_meta(meta, "Varus hair", voxel=0.004, smooth=3, tris=2500)
    front.data.materials.append(M["hair"])
    C.PARTS.append((front, "head"))
    backs = {}
    for side, sx in (("L", 1), ("R", -1)):
        path = [h + Vector((0.05 * sx, 0.10, -0.03)), B(0.07 * sx, 0.14, 1.38), B(0.08 * sx, 0.15, 1.22), B(0.085 * sx, 0.14, 1.06)]
        sheet = metaball_object(f"Varus long hair {side}", resolution=0.005)
        C.clump(sheet, path, 0.05, 0.024, flat=0.55)
        mesh = C.mesh_from_meta(sheet, f"Varus long hair {side}", voxel=0.0045, smooth=3, tris=2200)
        C.paint_regions(mesh, lambda c: "hair" if c.z > 1.30 * S else "hair_dark", ["hair", "hair_dark"])
        backs[side] = (path, mesh)
    return backs


def build_bow():
    """The living bow: grip at the origin, aim -Y, limbs along Z, string at +Y; organic horns."""
    arc = [Vector((0, 0.17 * (abs(z) / 0.72) ** 1.5, z)) for z in (-0.72, -0.55, -0.35, -0.15, 0.0, 0.15, 0.35, 0.55, 0.72)]
    parts = [tube("Bow limbs", arc, 0.022, "bow", False, taper=[0.3, 0.75, 1.0, 1.2, 1.35, 1.2, 1.0, 0.75, 0.3], resolution=8)]
    parts.append(lathe("Bow grip", "mauve", [(0.026, -0.08), (0.03, -0.06), (0.03, 0.06), (0.026, 0.08)], 16, "Z"))
    parts.append(ball_mesh("Bow eye", "glow", (0, -0.03, 0.0), (0.016, 0.01, 0.022), 12, 6))
    for sz in (1, -1):
        for k in range(3):
            z = (0.22 + 0.17 * k) * sz
            y = 0.17 * (abs(z) / 0.72) ** 1.5
            parts.append(C.cone("Bow horn", "violet", 0.016, 0.0, 0.10, (0, y - 0.05, z), (math.radians(-70 if sz > 0 else -110), 0, 0), 5))
        parts.append(tube("Bow vein", [Vector((0.012, 0.0, 0.05 * sz)), Vector((0.016, 0.04, 0.35 * sz)), Vector((0.014, 0.15, 0.62 * sz))], 0.004, "glow", False))
    return C.join(parts, "Living bow")


def build_arrow(name, length=0.8, mat="glow", radius=0.007):
    parts = [C.cyl(name, "violet", radius, length * 0.9, (0, -length * 0.45, 0), C.X90, 8), C.cone("Arrow head", mat, radius * 3.5, 0.0, 0.09, (0, -length * 0.93, 0), (-math.pi / 2, 0, 0), 5)]
    return C.join(parts, name)


REST_BOW = Matrix.Translation(Vector((0.215, -0.10, 0.95)) * S) @ Matrix.Rotation(math.radians(35), 4, "X")
BRACE = 0.17
DRAW = 0.42


def build():
    C.make_joints(scale=S, shoulder_x=0.205, hip_x=0.094)
    materials()
    body = build_body()
    panels = build_gear()
    backs = build_head()
    C.scale_parts("head", 1.05, C.J["head_bone"])
    bow = build_bow()
    C.place(bow, REST_BOW)
    nock_rest = REST_BOW @ Matrix.Translation((0, BRACE, 0))
    string = tube("Bow string", [REST_BOW @ Vector((0, BRACE, 0.72)), nock_rest.translation, REST_BOW @ Vector((0, BRACE, -0.72))], 0.003, "string", False, resolution=12, bevel=1)
    arrow = build_arrow("Nocked arrow")
    C.place(arrow, nock_rest)
    fx = {f"fx_arrow.{k}": (build_arrow(f"FX arrow {k}"), None, None) for k in range(3)}
    fx["fx_charge"] = (C.fx_orb("charge", 0.06, "glow", 2), REST_BOW @ Matrix.Translation((0, -0.05, 0)), "bow")
    fx["fx_blight"] = (C.fx_flash("blight burst", 0.10, "glow", 7), None, None)
    fx["fx_rain"] = (C.join([C.fx_orb(f"hail {k}", 0.4 - 0.1 * k, "glow", 1) for k in range(2)], "FX hail"), None, None)
    fx["fx_chain"] = (C.fx_bolt("chain of corruption", 0.9, 0.06, "glow", "violet", rings=3), None, None)
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
        w = max(0.0, 1.0 - abs(local.z) / 0.72)
        return {"nock": w, "bow": 1.0 - w} if w > 0 else {"bow": 1.0}

    C.SKINNED.append((string, string_weights))
    chains = C.coat_chains(panels, stiffness=65, gain=0.8, sway=1.5, limit=(35, 15))
    for side, (path, mesh) in backs.items():
        chains.append((f"hair.{side}", C.resample(path, 3), "head", dict(skin=True, stiffness=55, gain=1.1, sway=3.0, limit=(45, 30))))
        C.SKINNED.append((mesh, ["head"] + [f"hair.{side}.{i}" for i in range(3)]))
    C.SOCKETS["socket_muzzle"] = ("bow", REST_BOW @ Matrix.Translation((0, -0.05, 0)))
    C.build_rig("Varus rig", chains, extra, [("L", "bow", "grip_bow.L"), ("R", "draw", "nock")])
    C.bind(body)
    C.attach(bow, "bow")
    C.attach(arrow, "arrow")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips()


ARROWS = [f"fx_arrow.{k}" for k in range(3)]
FX = ARROWS + ["fx_charge", "fx_blight", "fx_rain", "fx_chain"]


def define_clips():
    aim_bow = placement("bow", B(0.05, -0.55, 1.48), rx=0, rz=0, roll=-8)
    sky_bow = placement("bow", B(0.07, -0.42, 1.60), rx=45, rz=0)

    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def stance(frame, breath=0.0, sway=0.0):
        """Brooding stance: bow low in the corrupted left hand, shoulders hunched."""
        loc("hips", frame, x=0.008 * sway, z=-0.03 - 0.004 * breath)
        rot("hips", frame, z=6)
        rot("spine", frame, x=6 + breath, z=-3)
        rot("chest", frame, x=4 + 1.5 * breath, z=-3 + sway)
        rot("head", frame, x=4 + breath, z=8 - 3 * sway)
        C.feet(frame, (0.05, -0.06, 0, -14), (-0.05, 0.06, 0, 20))
        loc("bow", frame)
        rot("bow", frame)
        loc("nock", frame)
        ik("L", "bow", frame, 1.0)
        ik("R", "draw", frame, 0.0)
        loc("pole_elbow.L", frame, x=0.1, y=0.1, z=-0.3)
        fk_arm("R", frame, up=6 + 2 * breath, swing=-8, bend=30, out=-2, twist=10, hand=-10)
        size("arrow", frame, 0.0)
        loc("root", frame)
        rot("root", frame)

    def full_draw(frame, matrix=None, amount=1.0):
        rot("hips", frame, z=-16)
        loc("hips", frame, z=-0.04)
        rot("spine", frame, x=2, z=-12)
        rot("chest", frame, x=-2, z=-16)
        rot("head", frame, x=2, y=-4, z=40)
        C.feet(frame, (0.08, -0.12, 0, -30), (-0.06, 0.10, 0, 35))
        ik("L", "bow", frame, 1.0)
        ik("R", "draw", frame, 1.0)
        loc("pole_elbow.L", frame, x=0.3, y=0.1, z=-0.2)
        loc("pole_elbow.R", frame, x=-0.4, y=0.5, z=0.25)
        weapon_matrix("bow", matrix or aim_bow, frame)
        C.weapon_offset("bow", "nock", frame, (0, DRAW * amount, 0))
        size("arrow", frame, 1.0)

    def nock_arrow(frame, matrix=None):
        rot("chest", frame, x=-1, z=-10)
        rot("hips", frame, z=-8)
        weapon_matrix("bow", matrix or aim_bow, frame)
        ik("L", "bow", frame, 1.0)
        ik("R", "draw", frame, 1.0)
        loc("pole_elbow.R", frame, x=-0.3, y=0.3, z=0.1)
        C.weapon_offset("bow", "nock", frame, (0, 0, 0))
        size("arrow", frame - 1, 0.0)
        size("arrow", frame, 1.0)

    def loose(frame, shot, distance=4.5, matrix=None):
        size("arrow", frame, 0.0)
        C.weapon_offset("bow", "nock", frame, (0, -0.02, 0))
        C.weapon_offset("bow", "nock", frame + 2, (0, 0.01, 0))
        C.weapon_offset("bow", "nock", frame + 4, (0, 0, 0))
        ik("R", "draw", frame, 0.0)
        fk_arm("R", frame + 1, up=70, swing=-10, bend=120, out=-40, twist=-20, hand=10)
        frame_m = C.weapon_frame("bow", matrix or aim_bow)
        C.shoot_from(shot, frame, frame + 6, lambda: frame_m @ Vector((0, -0.2, 0)), lambda: frame_m.to_3x3() @ Vector((0, -1, 0)), distance)
        return frame_m

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

    @clip("P", 30)
    def living_vengeance():
        start()
        # Corruption surges: the bow's eye flares, veins pulse, a snarl.
        size("fx_charge", 4, 0.0)
        size("fx_charge", 10, 1.4)
        size("fx_charge", 20, 1.0)
        size("fx_charge", 24, 0.0)
        rot("chest", 10, x=10, z=-6)
        rot("head", 10, x=12, z=10)
        fk_arm("R", 10, up=30, swing=-20, bend=90, out=10, hand=-30)
        stance(30)

    @clip("Q", 56)
    def piercing_arrow():
        start()
        # A long, trembling charge to full draw, then a piercing shot.
        nock_arrow(5)
        full_draw(12, amount=0.6)
        size("fx_charge", 10, 0.0)
        size("fx_charge", 34, 1.8)
        for k, f in enumerate(range(14, 35, 3)):
            C.weapon_offset("bow", "nock", f, (0, DRAW * (0.65 + 0.05 * k), 0))
            rot("chest", f, x=-2 - (0.8 if k % 2 else 0), z=-16)
        size("fx_charge", 35, 0.0)
        loose(35, ARROWS[0], 6.0)
        flash("fx_blight", 36, 4, 1.2)
        rot("chest", 36, x=-8, z=-14)
        stance(56)

    @clip("W", 28)
    def blighted_quiver():
        start()
        nock_arrow(4)
        full_draw(9)
        loose(11, ARROWS[1])
        size("fx_blight", 16, 0.0)
        C.put("fx_blight", 17, B(0.1, -4.5, 1.4))
        size("fx_blight", 17, 1.6)
        size("fx_blight", 22, 0.0)
        stance(28)

    @clip("E", 34)
    def hail_of_arrows():
        start()
        # An arrow arced into the sky; a corrupted hail bursts ahead.
        nock_arrow(5, sky_bow)
        full_draw(11, sky_bow)
        rot("head", 11, x=-16, y=-4, z=36)
        loose(14, ARROWS[2], 3.0, sky_bow)
        size("fx_rain", 19, 0.0)
        C.put("fx_rain", 20, B(0.0, -3.0, 0.1))
        size("fx_rain", 20, 0.6)
        size("fx_rain", 24, 1.3)
        size("fx_rain", 30, 0.0)
        stance(34)

    @clip("R", 40)
    def chain_of_corruption():
        start()
        nock_arrow(5)
        full_draw(12)
        size("fx_charge", 10, 0.0)
        size("fx_charge", 18, 1.6)
        size("fx_charge", 19, 0.0)
        frame_m = C.weapon_frame("bow", aim_bow)
        size("arrow", 19, 0.0)
        C.weapon_offset("bow", "nock", 19, (0, -0.02, 0))
        ik("R", "draw", 19, 0.0)
        fk_arm("R", 20, up=70, swing=-10, bend=120, out=-40, twist=-20, hand=10)
        C.shoot_from("fx_chain", 19, 28, lambda: frame_m @ Vector((0, -0.3, 0)), lambda: frame_m.to_3x3() @ Vector((0, -1, 0)), 5.0)
        rot("chest", 20, x=-8, z=-14)
        stance(40)

    @clip("Recall", 48, loop=True)
    def recall():
        # The corruption flexes through his arm; he clenches the fist and stares at it.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.3)
            rot("head", f, x=14, z=-6)
        size("fx_charge", 0, 0.3)
        fx_off(1)
        size("fx_charge", 12, 0.0)
        size("fx_charge", 18, 0.8)
        size("fx_charge", 26, 0.0)

    @clip("Death", 44)
    def death():
        start()
        ik("L", "bow", 3, 1.0)
        ik("L", "bow", 6, 0.0)
        weapon_matrix("bow", placement("bow", B(0.40, -0.25, 0.04), rx=-90, rz=60), 16)
        C.fall_back(0, S)
