"""Vayne: an original stylized interpretation (dark ponytail, red-lensed glasses, navy armour with
silver plates, crimson cape, wrist-mounted crossbows)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, cyl, fk_arm, flash, lathe, loc, material, metaball_object, rot, size, torus

S = 1.03
RIM = (1.0, 0.35, 0.45)
EXPOSURE = -0.15
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55), "Q": dict(angle_deg=20, distance=3.8, height=1.2, target_z=0.8)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#dfb198", rough=0.5, sss=0.2),
        navy=material("Navy armour", "#202e4c", rough=0.5),
        crimson=material("Crimson", "#a43448", rough=0.55),
        silver=material("Silver", "#c7d6db", rough=0.4, metal=0.8),
        steel=material("Dark steel", "#766a74", rough=0.35, metal=0.9),
        leather=material("Black leather", (0.02, 0.018, 0.022), rough=0.45),
        hair=material("Dark hair", (0.015, 0.012, 0.018), rough=0.45),
        hair_dark=material("Darker hair", (0.006, 0.005, 0.008), rough=0.5),
        lens=material("Red lens", (0.85, 0.04, 0.06), rough=0.05, emission=0.8),
        glow=material("Silver light", "#aeccff", emission=7.0),
    )
    C.face_materials(iris=(0.35, 0.18, 0.12), lash=(0.01, 0.008, 0.01), lip=(0.55, 0.22, 0.26))


def build_body():
    meta = metaball_object("Vayne body")
    C.torso_female(meta, S, bust=0.92, hips=0.95, waist=0.92)
    C.limbs(meta, dict(thigh=(0.061, 0.040), calf=(0.040, 0.045, 0.029), arm=(0.042, 0.031), forearm=(0.033, 0.025), palm=0.032), hands="mitten")
    for side in ("L", "R"):
        knee, ankle, toe = (C.J[f"{n}.{side}"] for n in ("knee", "ankle", "toe"))
        ball(meta, knee + Vector((0, -0.015, 0.035 * S)), 0.05 * S, (1.0, 1.0, 0.6))
        ball(meta, toe + Vector((0, 0.01, 0.004)), 0.033 * S, (0.9, 1.25, 0.7))
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.56, 0.90, 0.95, 1.40)]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.55, 0.80)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            f = C.arm_fraction(c, side)
            return "leather" if f > 0.80 else "steel" if f > 0.55 else "navy"
        if z < 0.56:
            return "leather"
        if 0.90 < z < 0.95:
            return "crimson"
        if z > 1.40 and math.hypot(x, y - 0.01) < 0.065:
            return "skin"
        return "navy"

    return C.body_mesh(meta, "Vayne body", region, ["skin", "navy", "crimson", "steel", "leather"], cuts)


def build_armour():
    parts = []
    for sx, side in ((1, "L"), (-1, "R")):
        pauldron = lathe("Pauldron", "silver", [(0.0, 0.05), (0.04, 0.048), (0.065, 0.03), (0.075, 0.0), (0.07, -0.02)], 20, "Z")
        C.place(pauldron, Matrix.Translation(B(0.165 * sx, 0.012, 1.365)) @ Matrix.Rotation(math.radians(-28 * sx), 4, "Y"))
        C.PARTS.append((pauldron, f"shoulder.{side}"))
        knee = C.J[f"knee.{side}"]
        guard = ball_mesh("Knee guard", "silver", knee + Vector((0, -0.045, 0.01)), (0.038, 0.02, 0.045), 16, 8)
        C.PARTS.append((guard, f"shin.{side}"))
    chest = ball_mesh("Chest plate", "silver", B(0, -0.075, 1.24), (0.085 * S, 0.02, 0.06 * S), 20, 10)
    C.PARTS.append((chest, "chest"))
    belt = [
        torus("Belt", "leather", 0.115 * S, 0.012 * S, B(0, 0.01, 0.95), (0, 0.1, 0), (1.0, 0.78, 1.0), 40),
        box("Buckle", "silver", (0.03 * S, 0.01, 0.026 * S), B(0, -0.09, 0.95), 0.004),
        box("Bolt quiver", "leather", (0.03 * S, 0.05 * S, 0.12 * S), B(-0.12, 0.05, 0.86), 0.008, (0, math.radians(-10), 0)),
    ]
    for o in belt:
        C.PARTS.append((o, "hips"))
    # Crimson cape from the shoulders down the back, on a spring chain; short coat tails.
    cape_pts = [B(0, 0.095, 1.39), B(0, 0.15, 1.10), B(0, 0.17, 0.80), B(0, 0.18, 0.52), B(0, 0.18, 0.36)]
    cape = C.ribbon("Cape", cape_pts, 0.34 * S, "crimson", (1, 0, 0), 0.008, [0.8, 1.0, 1.1, 1.2, 1.25], bone=False, curl=0.06, across=6)
    clasp = [ball_mesh("Cape clasp", "silver", B(0.12 * sx, -0.02, 1.37), (0.02, 0.012, 0.02), 12, 6) for sx in (1, -1)]
    for o in clasp:
        C.PARTS.append((o, "chest"))
    panels = C.coat_panels([("tail.L", 0.06, 0.10, 0.10, 0.95, 0.66, 0.02), ("tail.R", -0.06, 0.10, 0.10, 0.95, 0.66, 0.02)], "navy", S)
    return cape_pts, cape, panels


def build_head():
    C.build_head("Vayne head", jaw=0.95, chin=0.98, nose=0.95)
    C.build_face(eye_size=0.95, lashes="winged", brow_mat="hair", brow_width=0.0019, brow_angle=0.1, mouth="flat", mouth_size=0.0018)
    h = C.HEAD
    C.hair_cap("Vayne hair", "hair", front_y=0.045, front_z=0.055)
    meta = metaball_object("Vayne fringe", resolution=0.004)
    for i, x in enumerate((0.055, 0.025, -0.005, -0.035)):
        C.clump(meta, [h + Vector((x * 0.6, -0.065, 0.10)), h + Vector((x + 0.01, -0.098, 0.065)), h + Vector((x + 0.025, -0.097, 0.035 - 0.004 * i))], 0.015, 0.004, flat=0.6)
    for sx in (1, -1):
        C.clump(meta, [h + Vector((0.078 * sx, -0.055, 0.06)), h + Vector((0.09 * sx, -0.06, -0.02)), h + Vector((0.085 * sx, -0.05, -0.07))], 0.014, 0.004, flat=0.6)
    fringe = C.mesh_from_meta(meta, "Vayne fringe", voxel=0.0035, smooth=3, tris=2500)
    fringe.data.materials.append(M["hair"])
    C.PARTS.append((fringe, "head"))
    # Red-lensed glasses over the eyes.
    for sx in (1, -1):
        centre = h + Vector((0.037 * sx, -0.093, 0.004))
        C.PARTS.append((cyl("Glasses rim", "steel", 0.019, 0.006, centre, (math.radians(90), 0, math.radians(8 * sx)), 20), "head"))
        C.PARTS.append((cyl("Glasses lens", "lens", 0.016, 0.008, centre, (math.radians(90), 0, math.radians(8 * sx)), 20), "head"))
        C.PARTS.append((C.tube("Glasses arm", [centre + Vector((0.018 * sx, 0.0, 0.002)), h + Vector((0.08 * sx, -0.05, 0.008)), h + Vector((0.093 * sx, 0.0, 0.005))], 0.0025, "steel", False), "head"))
    C.tube("Glasses bridge", [h + Vector((0.019, -0.097, 0.008)), h + Vector((0, -0.1, 0.012)), h + Vector((-0.019, -0.097, 0.008))], 0.0025, "steel")
    # High ponytail on a spring chain.
    tie = h + Vector((0, 0.085, 0.07))
    path = [tie, tie + Vector((0, 0.05, -0.02)), tie + Vector((0, 0.07, -0.12)), tie + Vector((0, 0.06, -0.26)), tie + Vector((0, 0.05, -0.38))]
    tail = metaball_object("Ponytail", resolution=0.0045)
    C.clump(tail, path, 0.03, 0.008)
    pony = C.mesh_from_meta(tail, "Ponytail", voxel=0.004, smooth=3, tris=2500)
    C.paint_regions(pony, lambda c: "hair" if c.y > tie.y + 0.06 else "hair_dark", ["hair", "hair_dark"])
    C.PARTS.append((torus("Hair tie", "crimson", 0.02, 0.006, tie + Vector((0, 0.012, 0.0)), (math.radians(70), 0, 0), (1, 1, 1), 16), "head"))
    return path, pony


def build_crossbow(name, size_=1.0):
    """A wrist crossbow along -Y (mounted on the forearm), limbs across X."""
    k = size_
    parts = [
        box("Stock", "steel", (0.028 * k, 0.17 * k, 0.026 * k), (0, -0.03 * k, 0.0), 0.006),
        box("Rail", "silver", (0.012 * k, 0.16 * k, 0.01 * k), (0, -0.05 * k, 0.018 * k), 0.003),
        C.tube("Limbs", [Vector((0.13 * k, -0.08 * k, 0.0)), Vector((0.0, -0.13 * k, 0.012 * k)), Vector((-0.13 * k, -0.08 * k, 0.0))], 0.007 * k, "silver", False, taper=[0.5, 1.2, 0.5]),
        C.tube("String", [Vector((0.128 * k, -0.08 * k, 0.0)), Vector((0.0, -0.045 * k, 0.012 * k)), Vector((-0.128 * k, -0.08 * k, 0.0))], 0.0018 * k, "leather", False),
        box("Bolt", "glow", (0.006 * k, 0.12 * k, 0.006 * k), (0, -0.09 * k, 0.026 * k), 0.002),
        ball_mesh("Crossbow gem", "crimson", (0, 0.03 * k, 0.016 * k), (0.012 * k, 0.012 * k, 0.008 * k), 12, 6),
    ]
    return C.join(parts, name)


def build_back_crossbow():
    parts = [build_crossbow("Back crossbow", 2.2)]
    return C.join(parts, "Back crossbow")


def build():
    C.make_joints(scale=S, shoulder_x=0.176, hip_x=0.093)
    materials()
    body = build_body()
    cape_pts, cape, panels = build_armour()
    pony_path, pony = build_head()
    C.scale_parts("head", 1.06, C.J["head_bone"])

    # Wrist crossbows ride on the outside of each forearm, pointing along the hand.
    muzzles = {}
    for side, scale in (("R", 1.0), ("L", 0.8)):
        el, wr = C.J[f"elbow.{side}"], C.J[f"wrist.{side}"]
        n = C.hand_normal(side)
        frame = C.frame_along(el.lerp(wr, 0.7) + n * 0.035, wr - el, n)
        bow = build_crossbow(f"Wrist crossbow {side}", scale)
        C.place(bow, frame)
        C.PARTS.append((bow, f"forearm.{side}"))
        muzzles[side] = frame @ Matrix.Translation((0, -0.16 * scale, 0.026 * scale))
    back = build_back_crossbow()
    C.place(back, Matrix.Translation(B(0.0, 0.16, 1.15)) @ Matrix.Rotation(math.radians(-90), 4, "X") @ Matrix.Rotation(math.radians(20), 4, "Y"))
    C.PARTS.append((back, "chest"))

    fx = {
        "fx_flash.R": (C.fx_flash("flash R", 0.025, "glow"), muzzles["R"], "forearm.R"),
        "fx_flash.L": (C.fx_flash("flash L", 0.02, "glow"), muzzles["L"], "forearm.L"),
        "fx_bolt.0": (C.fx_bolt("bolt 0", 0.22, 0.012, "glow"), None, None),
        "fx_bolt.1": (C.fx_bolt("bolt 1", 0.22, 0.012, "glow"), None, None),
        "fx_condemn": (C.fx_bolt("condemn", 0.5, 0.03, "glow", "crimson", rings=2), None, None),
        "fx_silver": (C.fx_orb("silver bolts", 0.12, "glow", 3), None, None),
        "fx_aura": (C.join([C.torus("FX final hour", "glow", 0.42, 0.008, (0, 0, 0), (math.pi / 2 - 0.3 * k, 0.5 * k, 0.4 * k), (1, 1, 1), 40) for k in range(3)], "FX final hour"), Matrix.Translation(B(0, 0, 1.0)), "hips"),
        "fx_tumble": (C.fx_flash("tumble trail", 0.12, "glow", 6), None, None),
    }
    extra = C.fx_bones(fx, Matrix.Translation(B(-0.3, -0.4, 1.2)))
    chains = [("cape", C.resample(cape_pts, 4), "chest", dict(skin=True, stiffness=50, gain=1.0, sway=2.5, limit=(55, 25)))]
    chains += C.coat_chains(panels, stiffness=70, gain=0.8, sway=1.5, limit=(35, 15))
    chains.append(("pony", C.resample(pony_path, 4), "head", dict(skin=True, stiffness=55, gain=1.1, sway=3.0, limit=(45, 35))))
    C.SKINNED.append((cape, ["chest"] + [f"cape.{i}" for i in range(4)]))
    C.SKINNED.append((pony, ["head"] + [f"pony.{i}" for i in range(4)]))
    C.SOCKETS["socket_muzzle"] = ("forearm.R", muzzles["R"])
    C.build_rig("Vayne rig", chains, extra)
    C.bind(body)
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips(muzzles)


FX = ["fx_flash.R", "fx_flash.L", "fx_bolt.0", "fx_bolt.1", "fx_condemn", "fx_silver", "fx_aura", "fx_tumble"]


def define_clips(muzzles):
    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def muzzle(side, frame):
        return C.carried(f"forearm.{side}", frame, muzzles[side].translation)

    def heading(side, frame):
        m = muzzles[side]
        return muzzle(side, frame) - C.carried(f"forearm.{side}", frame, (m @ Matrix.Translation((0, 0.1, 0))).translation)

    def fire(side, frame, shot, distance=4.0, peak=1.2):
        flash(f"fx_flash.{side}", frame, 2, peak)
        C.shoot_from(shot, frame, frame + 5, lambda: muzzle(side, frame), lambda: heading(side, frame), distance)

    def stance(frame, breath=0.0, sway=0.0):
        """Hunter's crouch-ready stance: low centre, right crossbow arm half raised."""
        loc("hips", frame, z=-0.05 - 0.005 * breath, x=0.008 * sway)
        rot("hips", frame, z=-8 + 2 * sway)
        rot("spine", frame, x=6 + breath, z=4)
        rot("chest", frame, x=1 + 1.5 * breath, z=6 - 2 * sway)
        rot("head", frame, x=-4 + breath, z=-4 + 4 * sway)
        C.feet(frame, (0.06, -0.10, 0, -20), (-0.06, 0.08, 0, 24))
        fk_arm("R", frame, up=8, swing=-40, bend=70, out=-6, twist=20, hand=-10)
        fk_arm("L", frame, up=10 + 2 * breath, swing=10, bend=30, out=0, twist=10, hand=-10)
        loc("root", frame)
        rot("root", frame)

    def aim(side, frame, up=0.0, out=-4.0, bend=8):
        fk_arm(side, frame, up=up, swing=-88, bend=bend, out=out, twist=80, hand=-5)  # crossbow on top

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
            arc = 32 * (1 if lead == "L" else -1) * phase
            fk_arm("L", frame, up=14, swing=arc, bend=65, out=-4, hand=-5)
            fk_arm("R", frame, up=14, swing=-arc, bend=65, out=-4, hand=-5)

        C.run_cycle(upper, scale=S, lean=12, twist=10)
        fx_off(0)

    @clip("AA", 18)
    def attack():
        start()
        aim("R", 4)
        rot("chest", 4, z=14)
        rot("head", 4, z=-10)
        fire("R", 6, "fx_bolt.0")
        aim("R", 7, up=8, bend=16)
        aim("R", 9)
        stance(18)

    @clip("P", 30)
    def night_hunter():
        start()
        # A predator's lean: sink low, scan left, scan right, glasses glint.
        loc("hips", 6, z=-0.10)
        rot("spine", 6, x=14)
        rot("head", 8, x=4, z=24)
        rot("head", 16, x=4, z=-24)
        stance(30)

    @clip("Q", 22)
    def tumble():
        start()
        moving = bool(C.OPTIONS.get("root_motion"))
        side_x = 0.9 if moving else 0.0
        # A low, fast dive to her left: crouch, body tilted into the dodge with legs tucked,
        # a silver blur, land low and fire from the crouch.
        loc("hips", 3, z=-0.13)
        rot("spine", 3, x=16, y=12)
        rot("hips", 3, y=10)
        C.feet(3, (0.10, -0.08, 0, -20), (-0.04, 0.06, 0, 20))
        loc("root", 3)
        rot("root", 3)
        rot("root", 7, y=38)
        loc("root", 7, x=side_x * 0.5, z=0.16)
        loc("hips", 7, z=-0.05)
        for side in ("L", "R"):
            loc(f"ik_foot.{side}", 7, x=0.02 * C.side_x(side), y=0.05, z=0.28)
            rot(f"ik_foot.{side}", 7, x=-30)
            fk_arm(side, 7, up=30, swing=-40, bend=100, out=-20, hand=-20)
        rot("spine", 7, x=26, y=20)
        rot("head", 7, x=12, y=-10)
        size("fx_tumble", 3, 0.0)
        C.put("fx_tumble", 5, B(0, 0, 0.6))
        size("fx_tumble", 5, 1.3)
        size("fx_tumble", 10, 0.0)
        rot("root", 11, y=8)
        loc("root", 11, x=side_x)
        loc("hips", 11, z=-0.14)
        C.feet(11, (0.10, -0.08, 0, -20), (-0.07, 0.10, 0, 24))
        rot("spine", 11, x=14, y=4)
        aim("R", 13, out=-4)
        fire("R", 14, "fx_bolt.1")
        aim("R", 15, up=8, bend=16)
        stance(22)
        rot("root", 13)
        loc("root", 13, x=side_x)
        loc("root", 22, x=side_x)

    @clip("W", 26)
    def silver_bolts():
        start()
        # Three quick wrist shots; the third bursts in silver.
        for k, f in enumerate((4, 9, 14)):
            aim("R", f - 1)
            fire("R", f, f"fx_bolt.{k % 2}" if k < 2 else "fx_condemn", 4.0, 1.0 + 0.4 * k)
            aim("R", f + 1, up=8, bend=16)
        size("fx_silver", 18, 0.0)
        C.put("fx_silver", 19, B(-0.1, -4.0, 1.3))
        size("fx_silver", 19, 1.5)
        size("fx_silver", 24, 0.0)
        stance(26)

    @clip("E", 28)
    def condemn():
        start()
        # Plant, brace the crossbow arm with the left hand, a heavy bolt with recoil.
        aim("R", 6, out=-2)
        fk_arm("L", 6, up=10, swing=-70, bend=80, out=-35, twist=20, hand=-10)
        C.feet(6, (0.09, -0.16, 0, -25), (-0.08, 0.14, 0, 30))
        loc("hips", 6, z=-0.09)
        rot("chest", 6, z=10)
        size("fx_flash.R", 7, 0.0)
        size("fx_flash.R", 10, 0.6)
        fire("R", 11, "fx_condemn", 4.5, 2.0)
        aim("R", 12, up=16, bend=26)
        rot("chest", 12, x=-6, z=8)
        loc("hips", 13, y=0.05, z=-0.08)
        aim("R", 16)
        stance(28)

    @clip("R", 44)
    def final_hour():
        start()
        # Crouch, rise and spread the arms as a silver aura flares and the cape lifts.
        loc("hips", 6, z=-0.14)
        rot("spine", 6, x=18)
        rot("head", 6, x=14)
        for side in ("L", "R"):
            fk_arm(side, 6, up=10, swing=-20, bend=90, out=-20, hand=-20)
        loc("hips", 14, z=0.04)
        rot("spine", 14, x=-12)
        rot("chest", 14, x=-10)
        rot("head", 14, x=-16)
        for side in ("L", "R"):
            fk_arm(side, 14, up=85, swing=10, bend=20, out=0, hand=10)
        size("fx_aura", 12, 0.0)
        size("fx_aura", 16, 1.4)
        size("fx_aura", 30, 1.0)
        size("fx_aura", 36, 0.0)
        aim("R", 26)
        rot("chest", 26, z=12)
        stance(44)

    @clip("Recall", 48, loop=True)
    def recall():
        # Adjusting her glasses, then a slow look over the shoulder.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.5)
            fk_arm("L", f, up=40 + 4 * abs(s_), swing=-60, bend=140, out=-25, twist=30, hand=-10)
            rot("head", f, x=-2, z=10 * s_)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        C.fall_back(0, S)
