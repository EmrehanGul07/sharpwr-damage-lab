"""Lucian: an original stylized interpretation (close-cropped hair and beard, long dark split coat,
ivory-and-gold relic pistols in both hands, radiant light shots)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, cyl, fk_arm, flash, lathe, loc, material, metaball_object, rot, size, torus, tube

S = 1.05
RIM = (1.0, 0.9, 0.6)
EXPOSURE = -0.1
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#6a4636", rough=0.5, sss=0.04),
        coat=material("Black coat", "#20232a", rough=0.6),
        vest=material("Grey vest", "#34383b", rough=0.6),
        ivory=material("Ivory", "#e5e2ca", rough=0.35),
        gold=material("Relic gold", "#ad9566", rough=0.3, metal=1.0),
        trousers=material("Trousers", (0.018, 0.019, 0.022), rough=0.65),
        boot=material("Boot", (0.02, 0.016, 0.014), rough=0.4),
        glove=material("Glove", (0.025, 0.025, 0.028), rough=0.5),
        hair=material("Black hair", (0.010, 0.008, 0.007), rough=0.6),
        leather=material("Holster leather", (0.06, 0.035, 0.02), rough=0.5),
        light=material("Holy light", "#f2e6a2", emission=8.0),
        light_soft=material("Soft light", (1.0, 0.95, 0.75), emission=3.0),
    )
    C.face_materials(iris=(0.25, 0.16, 0.08), lash=(0.01, 0.008, 0.007), lip=(0.30, 0.17, 0.13), brow=(0.012, 0.01, 0.009))


def build_body():
    meta = metaball_object("Lucian body")
    C.torso_male(meta, S, chest=1.05, shoulders=1.06)
    ball(meta, B(0, 0.01, 0.885), 0.125 * S, (1.05, 0.8, 0.35))
    C.limbs(meta, dict(neck=(0.056, 0.049), thigh=(0.07, 0.047), calf=(0.047, 0.052, 0.033), foot=(0.041, 0.035), arm=(0.054, 0.039), forearm=(0.041, 0.031), palm=0.037), hands="mitten")
    for side in ("L", "R"):
        knee, ankle, toe = (C.J[f"{n}.{side}"] for n in ("knee", "ankle", "toe"))
        ball(meta, knee.lerp(ankle, 0.45), 0.054 * S, (1.0, 1.0, 0.45))
        ball(meta, toe + Vector((0, 0.012, 0.006)), 0.039 * S, (0.95, 1.2, 0.75))
    v = Vector((1, 0, -0.08)).normalized()
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.40, 0.885, 1.385)]
    cuts += [(B(0.025, 0, 0.95), v), (B(-0.025, 0, 0.95), Vector((-v.x, 0, v.z)))]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.78,)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.21 and z > 0.88:
            return "glove" if C.arm_fraction(c, side) > 0.78 else "coat"
        if z < 0.40:
            return "boot"
        if z < 0.885:
            return "trousers"
        if z > 1.385 and math.hypot(x, y - 0.01) < 0.075:
            return "skin"
        if y < 0 and z > 0.95 and abs(x) < 0.025 + (z - 0.95) * 0.08:
            return "vest"
        return "coat"

    return C.body_mesh(meta, "Lucian body", region, ["skin", "coat", "vest", "trousers", "boot", "glove"], cuts)


def build_clothes():
    panels = C.coat_panels(
        [
            ("back.L", 0.055, 0.105, 0.11, 0.98, 0.40, 0.02),
            ("back.R", -0.055, 0.105, 0.11, 0.98, 0.40, 0.02),
            ("side.L", 0.122, 0.02, 0.12, 0.98, 0.42, 0.06),
            ("side.R", -0.122, 0.02, 0.12, 0.98, 0.42, 0.06),
        ],
        "coat",
        S,
    )
    for sx in (1, -1):
        lapel = C.ribbon("Lapel", [B(0.028 * sx, -0.083, 0.97), B(0.045 * sx, -0.095, 1.17), B(0.075 * sx, -0.086, 1.37)], 0.011 * S, "gold", (1, 0, 0), 0.004, [0.6, 1.0, 1.1], bone=False)
        C.SKINNED.append((lapel, ["spine", "chest"]))
        C.PARTS.append((box("Shoulder plate", "ivory", (0.075 * S, 0.11 * S, 0.012 * S), B(0.17 * sx, 0.012, 1.39), 0.006, (0, math.radians(-14 * sx), 0)), f"shoulder.{'L' if sx > 0 else 'R'}"))
    collar = [B(math.sin(a) * 0.08, 0.012 + math.cos(a) * 0.066, 1.40 + 0.03 * (1 + math.cos(a)) / 2) for a in (math.radians(d) for d in range(-130, 131, 20))]
    C.PARTS.append((C.ribbon("Collar", collar, 0.06 * S, "coat", (0, 0, 1), 0.008, bone=False), "chest"))
    belt = [
        torus("Belt", "leather", 0.13 * S, 0.011 * S, B(0, 0.012, 0.915), (0, 0.05, 0), (1.0, 0.78, 1.0), 40),
        box("Buckle", "gold", (0.032 * S, 0.01, 0.026 * S), B(0, -0.097, 0.913), 0.004),
    ]
    for sx in (1, -1):
        belt.append(box("Holster", "leather", (0.035 * S, 0.06 * S, 0.11 * S), B(0.135 * sx, -0.01, 0.84), 0.01, (0, math.radians(8 * sx), 0)))
    for o in belt:
        C.PARTS.append((o, "hips"))
    return panels


def build_head():
    def extra(meta, h):
        ball(meta, h + Vector((0, -0.03, -0.06)), 0.052, (1.15, 0.8, 0.6))

    head = C.build_head("Lucian head", jaw=1.08, chin=1.1, cheek=1.0, nose=1.05, width=1.0, extra=extra)
    C.build_face(eye_size=0.85, lashes="soft", brow_mat="brow", brow_width=0.003, brow_angle=0.12, mouth="flat", mouth_width=1.15, mouth_size=0.0022, mouth_y=-0.004)
    h = C.HEAD
    # A short boxed beard painted on the lower face, and a moustache snapped onto the lip.
    head.data.materials.append(M["hair"])

    def bearded(c):
        d = c - h
        return d.y < 0.035 and d.z < -0.071 + 0.28 * max(0.0, abs(d.x) - 0.03)

    for poly in head.data.polygons:
        if bearded(Vector(poly.center)):
            poly.material_index = 1
    lip = [C.surface(head, h + Vector((x, -0.25, -0.043 + abs(x) * 0.15)), h + Vector((x * 0.5, 0, -0.043)), 0.002) for x in (0.022, 0.0, -0.022)]
    tube("Moustache", [p for p in lip if p is not None], 0.0026, "hair", taper=[0.4, 1, 0.4])
    C.hair_cap("Lucian hair", "hair", front_y=0.03, front_z=0.075, scale=0.99, back=0.98, thickness=0.004)


def build_pistol(name):
    """A relic pistol: grip at the origin (inside the fist), barrel toward -Y, top toward +Z."""
    parts = [
        box("Pistol body", "ivory", (0.032, 0.17, 0.05), (0, -0.06, 0.035), 0.008),
        box("Pistol rib", "gold", (0.036, 0.13, 0.012), (0, -0.07, 0.062), 0.003),
        cyl("Pistol barrel", "gold", 0.012, 0.08, (0, -0.18, 0.04), C.X90, 16),
        lathe("Pistol muzzle", "gold", [(0.014, -0.215), (0.018, -0.22), (0.018, -0.235), (0.012, -0.24)], 16),
        C.plate("Pistol fin", "ivory", [(0, -0.07, 0.01), (0, -0.22, 0.012), (0, -0.25, -0.025), (0, -0.16, -0.02)], 0.02, 0.0),
        C.plate("Pistol fin trim", "gold", [(0, -0.22, 0.012), (0, -0.25, -0.025), (0, -0.235, -0.03), (0, -0.21, 0.0)], 0.024, 0.0),
        box("Pistol grip", "leather", (0.026, 0.036, 0.085), (0, 0.012, -0.03), 0.008, (math.radians(-12), 0, 0)),
        torus("Trigger guard", "gold", 0.016, 0.003, (0, -0.02, -0.005), (0, math.pi / 2, 0), (1, 1, 1), 16),
        ball_mesh("Relic core", "light", (0, -0.05, 0.035), (0.018, 0.012, 0.012), 12, 6),
        cyl("Light line", "light_soft", 0.003, 0.11, (0.017, -0.08, 0.035), C.X90, 6),
    ]
    return C.join(parts, name)


def build():
    C.make_joints(scale=S, shoulder_x=0.205, hip_x=0.092)
    materials()
    body = build_body()
    panels = build_clothes()
    build_head()
    C.scale_parts("head", 1.06, C.J["head_bone"])

    pistols, muzzles, grips = {}, {}, {}
    for side in ("L", "R"):
        wr, hd = C.J[f"wrist.{side}"], C.J[f"hand.{side}"]
        n = C.hand_normal(side)
        origin = wr.lerp(hd, 0.55) - n * 0.012
        frame = C.frame_along(origin, hd - wr, Vector((0, -1, 0)))
        pistol = build_pistol(f"Pistol {side}")
        C.place(pistol, frame)
        C.PARTS.append((pistol, f"hand.{side}"))
        pistols[side] = frame
        muzzles[side] = frame @ Matrix.Translation((0, -0.25, 0.04))
        grips[side] = frame @ Matrix.Translation((0, -0.10, 0.04))

    fx = {}
    for side in ("L", "R"):
        fx[f"fx_flash.{side}"] = (C.fx_flash(f"flash {side}", 0.03, "light"), muzzles[side], f"hand.{side}")
    for k in range(6):
        fx[f"fx_shot.{k}"] = (C.fx_bolt(f"shot {k}", 0.20, 0.016, "light", "light_soft"), None, None)
    fx["fx_beam"] = (C.fx_beam("piercing light", 5.0, 0.05, "light", "light_soft"), None, None)
    fx["fx_star"] = (C.fx_flash("ardent star", 0.06, "light", spikes=4), None, None)
    fx["fx_dash"] = (C.fx_flash("dash trail", 0.10, "light_soft", spikes=6), None, None)
    extra = C.fx_bones(fx, Matrix.Translation(B(0, -0.3, 1.2)))
    chains = C.coat_chains(panels, stiffness=55, gain=0.9, sway=2.0, limit=(50, 25))
    C.SOCKETS["socket_muzzle"] = ("hand.R", muzzles["R"])
    C.build_rig("Lucian rig", chains, extra)
    C.bind(body)
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips(muzzles, grips)


FX_SHOTS = [f"fx_shot.{k}" for k in range(6)]
FX = ["fx_flash.L", "fx_flash.R", "fx_beam", "fx_star", "fx_dash"] + FX_SHOTS


def define_clips(muzzles, grips):
    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def muzzle(side, frame):
        return C.carried(f"hand.{side}", frame, muzzles[side].translation)

    def barrel(side, frame):
        return muzzle(side, frame) - C.carried(f"hand.{side}", frame, grips[side].translation)

    def fire(side, frame, shot, distance=4.0, peak=1.2):
        flash(f"fx_flash.{side}", frame, 2, peak)
        C.shoot_from(shot, frame, frame + 5, lambda: muzzle(side, frame), lambda: barrel(side, frame), distance)

    def stance(frame, breath=0.0, sway=0.0):
        """Grounded gunslinger stance: feet apart, knees soft, both pistols low and ready."""
        loc("hips", frame, z=-0.03 - 0.005 * breath, x=0.006 * sway)
        rot("hips", frame, z=4 * sway)
        rot("spine", frame, x=3 + breath)
        rot("chest", frame, x=-1 + 1.5 * breath, z=-3 * sway)
        rot("head", frame, x=-2 + breath, z=-4 + 6 * sway)
        C.feet(frame, (0.05, -0.04, 0, -12), (-0.05, 0.04, 0, 14))
        for side in ("L", "R"):
            fk_arm(side, frame, up=4 + 2 * breath, swing=-16, bend=30, out=-2, twist=18, hand=-30)
        loc("root", frame)
        rot("root", frame)

    def aim(side, frame, up=0.0, out=0.0, bend=6):
        fk_arm(side, frame, up=up, swing=-88, bend=bend, out=out, hand=-4)

    def start(frame=0):
        stance(frame)
        fx_off(frame)

    @clip("Idle", 72, loop=True)
    def idle():
        for f, breath, sway in ((0, 0, 0), (18, 1, 0.4), (36, 0, 1), (54, 1, 0.4), (72, 0, 0)):
            stance(f, breath, sway)
        fx_off(0)

    @clip("Walk", 18, loop=True)
    def run():
        def upper(frame, lead, phase):
            arc = 30 * (1 if lead == "L" else -1) * phase
            fk_arm("L", frame, up=12, swing=arc - 10, bend=65, out=2, hand=-25)
            fk_arm("R", frame, up=12, swing=-arc - 10, bend=65, out=2, hand=-25)

        C.run_cycle(upper, scale=S, lean=11, twist=10)
        fx_off(0)

    @clip("AA", 18)
    def attack():
        start()
        rot("chest", 3, z=8)
        aim("R", 4, out=-6)
        rot("chest", 5, x=0, z=12)
        rot("head", 5, z=-8)
        fire("R", 5, "fx_shot.0")
        aim("R", 6, up=10, out=-6, bend=18)  # recoil
        aim("R", 8, out=-6)
        stance(18)

    @clip("P", 24)
    def lightslinger():
        start()
        # Two quick shots: right, then left.
        aim("R", 3, out=-6)
        rot("chest", 3, z=10)
        fire("R", 4, "fx_shot.0")
        aim("R", 5, up=10, out=-6, bend=18)
        aim("L", 7, out=-6)
        rot("chest", 8, z=-10)
        fire("L", 9, "fx_shot.1")
        aim("L", 10, up=10, out=-6, bend=18)
        fk_arm("R", 12, up=10, swing=-40, bend=30, out=4, hand=-20)
        aim("L", 12, out=-6)
        stance(24)

    @clip("Q", 26)
    def piercing_light():
        start()
        aim("R", 4, out=-4)
        rot("chest", 4, z=16)
        rot("spine", 4, z=6)
        rot("head", 4, z=-10)
        C.feet(6, (0.06, -0.10, 0, -20), (-0.06, 0.08, 0, 25))
        loc("hips", 6, z=-0.05)
        size("fx_flash.R", 5, 0.0)
        size("fx_flash.R", 9, 0.6)  # gathering light
        flash("fx_flash.R", 10, 6, 2.0)
        C.shoot_from("fx_beam", 10, 16, lambda: muzzle("R", 10), lambda: barrel("R", 10), 0.02)
        aim("R", 11, up=6, out=-4, bend=12)
        rot("chest", 11, x=-3, z=14)
        aim("R", 16, out=-4)
        stance(26)

    @clip("W", 24)
    def ardent_blaze():
        start()
        aim("L", 4, up=4, out=-4)
        rot("chest", 4, z=-14)
        rot("head", 4, z=8)
        fire("L", 6, "fx_star", 4.0, 1.6)
        aim("L", 7, up=16, out=-4, bend=24)
        rot("chest", 7, x=-3, z=-10)
        aim("L", 11, up=4, out=-4)
        stance(24)

    @clip("E", 22)
    def relentless_pursuit():
        start()
        moving = bool(C.OPTIONS.get("root_motion"))
        # Crouch, burst forward low, land with both pistols up.
        loc("hips", 3, z=-0.09)
        rot("spine", 3, x=14)
        for side in ("L", "R"):
            fk_arm(side, 3, up=20, swing=30, bend=60, hand=-20)
        loc("root", 3)
        loc("root", 9, y=-1.6 if moving else 0.0, z=0.05)
        rot("spine", 7, x=24)
        rot("head", 7, x=-18)
        for side in ("L", "R"):
            fk_arm(side, 7, up=30, swing=45, bend=40, hand=-20)
        C.feet(7, (0.04, 0.18, 0.12, -40), (-0.04, 0.24, 0.16, -50))
        size("fx_dash", 3, 0.0)
        C.put("fx_dash", 4, B(0, -0.2, 0.9))
        size("fx_dash", 4, 1.4)
        size("fx_dash", 9, 0.0)
        loc("hips", 11, z=-0.10)
        rot("spine", 11, x=8)
        for side in ("L", "R"):
            aim(side, 12, up=4, out=-8)
        stance(22)
        if moving:
            loc("root", 22, y=-1.6)
            loc("root", 11, y=-1.6)

    @clip("R", 60)
    def the_culling():
        start()
        moving = bool(C.OPTIONS.get("root_motion"))
        # Both pistols raised, alternating rapid fire while strafing to his left.
        for side in ("L", "R"):
            aim(side, 6, out=-6)
        loc("hips", 6, z=-0.05)
        rot("spine", 6, x=4)
        k = 0
        for f in range(8, 50, 3):
            side = "R" if k % 2 == 0 else "L"
            fire(side, f, FX_SHOTS[k % 6], 4.5, 1.0)
            aim(side, f + 1, up=6, out=-6, bend=12)
            aim(side, f + 2, out=-6)
            k += 1
        for i, f in enumerate(range(8, 51, 6)):  # strafe: small side steps
            step = 0.06 * (1 if i % 2 else -1)
            C.feet(f, (0.05 + step, -0.04, 0.03 if i % 2 else 0, -12), (-0.05 + step, 0.04, 0 if i % 2 else 0.03, 14))
            loc("hips", f, x=step * 0.5, z=-0.05)
            if moving:
                loc("root", f, x=0.04 * i)
        stance(60)
        if moving:
            loc("root", 60, x=0.32)

    @clip("Recall", 48, loop=True)
    def recall():
        # A quiet moment: the left pistol raised, a look at it, a slow breath.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.2)
            fk_arm("L", f, up=30 + 3 * abs(s_), swing=-55, bend=110, out=-20, twist=20, hand=-30)
            rot("head", f, x=14 + 2 * abs(s_), z=8)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        C.fall_back(0, S)
