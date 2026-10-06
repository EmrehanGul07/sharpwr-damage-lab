"""Samira: an original stylized interpretation (dark swept hair, eyepatch, red scarf, armoured
leather suit, a curved blade in the right hand and a compact pistol in the left)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, cyl, fk_arm, flash, lathe, loc, material, metaball_object, rot, size, torus

S = 1.03
RIM = (1.0, 0.45, 0.35)
EXPOSURE = -0.1
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55), "E": dict(angle_deg=28, distance=3.9, height=1.2, target_z=0.85)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#a76f54", rough=0.5, sss=0.08),
        suit=material("Leather suit", "#24272c", rough=0.45),
        red=material("Red scarf", "#a0353b", rough=0.6),
        plate=material("Steel plate", "#b9c4c3", rough=0.3, metal=0.9),
        brass=material("Brass", "#ac8a59", rough=0.3, metal=1.0),
        belt=material("Belt leather", (0.035, 0.016, 0.012), rough=0.45),
        hair=material("Black hair", (0.012, 0.01, 0.012), rough=0.45),
        hair_dark=material("Blue-black hair", (0.01, 0.012, 0.025), rough=0.5),
        steel=material("Blade steel", (0.8, 0.8, 0.82), rough=0.15, metal=1.0),
        fire=material("Gunfire", "#ff7050", emission=8.0),
        slash=material("Slash arc", (1.0, 0.45, 0.35), emission=5.0, alpha=0.75),
    )
    C.face_materials(iris=(0.35, 0.20, 0.10), lash=(0.01, 0.008, 0.008), lip=(0.42, 0.18, 0.16))


def build_body():
    meta = metaball_object("Samira body")
    C.torso_female(meta, S, bust=1.0, hips=1.0, waist=0.92)
    C.limbs(meta, dict(thigh=(0.064, 0.041), calf=(0.041, 0.046, 0.03), arm=(0.043, 0.032), forearm=(0.034, 0.026), palm=0.033), hands="mitten")
    for side in ("L", "R"):
        knee, toe = C.J[f"knee.{side}"], C.J[f"toe.{side}"]
        ball(meta, knee + Vector((0, -0.012, 0.03 * S)), 0.05 * S, (1.0, 1.0, 0.55))
        ball(meta, toe + Vector((0, 0.01, 0.004)), 0.034 * S, (0.9, 1.25, 0.7))
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.55, 0.92, 0.97, 1.40)]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.55, 0.80)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            f = C.arm_fraction(c, side)
            return "belt" if f > 0.80 else "plate" if f > 0.55 else "suit"
        if z < 0.55:
            return "belt"
        if 0.92 < z < 0.97:
            return "red"
        if z > 1.40 and math.hypot(x, y - 0.01) < 0.065:
            return "skin"
        return "suit"

    return C.body_mesh(meta, "Samira body", region, ["skin", "suit", "red", "plate", "belt"], cuts)


def build_gear():
    for side, sx in (("L", 1), ("R", -1)):
        pad = lathe("Shoulder plate", "plate", [(0.0, 0.04), (0.05, 0.035), (0.07, 0.01), (0.072, -0.02)], 20, "Z")
        C.place(pad, Matrix.Translation(B(0.165 * sx, 0.012, 1.37)) @ Matrix.Rotation(math.radians(-28 * sx), 4, "Y"))
        C.PARTS.append((pad, f"shoulder.{side}"))
    # Scarf wrapped at the throat with two tails flowing back.
    meta = metaball_object("Scarf", resolution=0.006)
    for d in range(0, 360, 24):
        a = math.radians(d)
        ball(meta, B(math.sin(a) * 0.07, 0.012 - math.cos(a) * 0.065, 1.405), 0.025 * S, (1, 1, 0.8))
    wrap = C.mesh_from_meta(meta, "Scarf wrap", voxel=0.005, smooth=3, tris=2500)
    wrap.data.materials.append(M["red"])
    C.PARTS.append((wrap, "chest"))
    tails = {}
    for name, x in (("scarf.L", 0.03), ("scarf.R", -0.03)):
        pts = [B(x, 0.08, 1.40), B(x * 2, 0.14, 1.32), B(x * 2.5, 0.18, 1.18), B(x * 3, 0.20, 1.04)]
        tails[name] = (pts, C.ribbon("Scarf tail", pts, 0.05 * S, "red", (1, 0, 0), 0.006, [1.0, 1.0, 0.9, 0.7], bone=False))
    belt = [
        torus("Belt", "belt", 0.12 * S, 0.012 * S, B(0, 0.01, 0.945), (0, 0.1, 0), (1.0, 0.8, 1.0), 40),
        torus("Bandolier", "belt", 0.125 * S, 0.010 * S, B(0, 0.012, 0.91), (0, -0.25, 0), (1.0, 0.8, 1.0), 40),
        box("Buckle", "brass", (0.034 * S, 0.01, 0.026 * S), B(0, -0.095, 0.945), 0.004),
    ]
    for k in range(9):
        a = math.radians(-60 + 15 * k)
        belt.append(cyl("Cartridge", "brass", 0.006, 0.03, B(math.sin(a) * 0.13, -math.cos(a) * 0.10 + 0.012, 0.91 - 0.25 * math.sin(a) * 0.13), (0, 0, 0), 8))
    for o in belt:
        C.PARTS.append((o, "hips"))
    panels = C.coat_panels([("tail.L", 0.06, 0.10, 0.10, 0.95, 0.62, 0.02), ("tail.R", -0.06, 0.10, 0.10, 0.95, 0.62, 0.02)], "suit", S)
    return tails, panels


def build_head():
    head = C.build_head("Samira head", jaw=0.98, chin=1.0, nose=1.0)
    C.build_face(eye_size=0.95, lashes="winged", brow_mat="hair", brow_width=0.0022, brow_angle=0.12, mouth="smirk", mouth_size=0.0021)
    h = C.HEAD
    # Eyepatch over her right eye with a strap around the head.
    patch = ball_mesh("Eyepatch", "suit", h + Vector((-0.037, -0.094, 0.004)), (0.024, 0.008, 0.02), 16, 8)
    C.PARTS.append((patch, "head"))
    strap = C.tube("Patch strap", [h + Vector((-0.06, -0.085, 0.02)), h + Vector((-0.095, -0.02, 0.03)), h + Vector((-0.06, 0.09, 0.04)), h + Vector((0.05, 0.09, 0.04)), h + Vector((0.095, -0.02, 0.03)), h + Vector((0.06, -0.08, 0.02)), h + Vector((-0.015, -0.098, 0.022))], 0.003, "suit", False)
    C.PARTS.append((strap, "head"))
    C.hair_cap("Samira hair cap", "hair", front_y=0.045, front_z=0.06)
    meta = metaball_object("Samira hair", resolution=0.004)
    # Swept to her left, long at the back.
    for i, x in enumerate((-0.05, -0.02, 0.01, 0.04)):
        C.clump(meta, [h + Vector((x, -0.08, 0.08)), h + Vector((x + 0.03, -0.088, 0.105)), h + Vector((x + 0.08, -0.04, 0.105)), h + Vector((x + 0.11, 0.02, 0.05))], 0.015, 0.005, flat=0.5)
    C.clump(meta, [h + Vector((0.08, -0.06, 0.06)), h + Vector((0.10, -0.06, -0.02)), h + Vector((0.10, -0.04, -0.10))], 0.02, 0.006, flat=0.6)
    hair = C.mesh_from_meta(meta, "Samira hair", voxel=0.0035, smooth=3, tris=3500)
    C.paint_regions(hair, lambda c: "hair" if c.z > h.z + 0.06 else "hair_dark", ["hair", "hair_dark"])
    C.PARTS.append((hair, "head"))
    path = [h + Vector((0.0, 0.10, -0.03)), B(0.0, 0.13, 1.40), B(0.0, 0.14, 1.28), B(0.0, 0.13, 1.16)]
    sheet = metaball_object("Samira long hair", resolution=0.005)
    C.clump(sheet, path, 0.06, 0.03, flat=0.5)
    back = C.mesh_from_meta(sheet, "Samira long hair", voxel=0.0045, smooth=3, tris=2200)
    back.data.materials.append(M["hair"])
    return path, back


def build_sword():
    """A curved blade: hilt at the origin, blade toward -Y, edge down (-Z)."""
    curve = [Vector((0, -0.06 - 0.6 * t, -0.07 * t * t)) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
    parts = [C.ribbon("Blade", curve, 0.05, "steel", (0, 0, 1), 0.006, [1.0, 1.05, 1.0, 0.8, 0.1], bone=False)]
    parts += [
        cyl("Hilt", "belt", 0.014, 0.10, (0, 0.03, 0), C.X90, 12),
        box("Guard", "brass", (0.02, 0.02, 0.08), (0, -0.03, -0.005), 0.004),
        ball_mesh("Pommel", "brass", (0, 0.085, 0), (0.018, 0.018, 0.018), 12, 6),
    ]
    return C.join(parts, "Curved blade")


def build_pistol():
    parts = [
        box("Pistol body", "suit", (0.03, 0.12, 0.045), (0, -0.04, 0.03), 0.007),
        cyl("Pistol barrel", "brass", 0.011, 0.08, (0, -0.13, 0.036), C.X90, 14),
        box("Pistol grip", "belt", (0.026, 0.035, 0.08), (0, 0.012, -0.028), 0.008, (math.radians(-14), 0, 0)),
        cyl("Pistol drum", "plate", 0.018, 0.035, (0, -0.02, 0.03), C.X90, 12),
    ]
    return C.join(parts, "Pistol")


def build_arc(name, radius=0.75, sweep=150):
    pts = [Vector((math.sin(math.radians(a)) * radius, -math.cos(math.radians(a)) * radius, 0)) for a in range(-sweep // 2, sweep // 2 + 1, 15)]
    n = len(pts)
    arc = C.ribbon(f"FX {name}", pts, 0.10, "slash", (0, 0, 1), 0.0, [0.1] + [1.0] * (n - 2) + [0.1], bone=False)
    return arc


def build():
    C.make_joints(scale=S, shoulder_x=0.178, hip_x=0.094)
    materials()
    body = build_body()
    tails, panels = build_gear()
    hair_path, back = build_head()
    C.scale_parts("head", 1.06, C.J["head_bone"])

    holds, muzzle = {}, None
    for side, maker in (("R", build_sword), ("L", build_pistol)):
        wr, hd = C.J[f"wrist.{side}"], C.J[f"hand.{side}"]
        n = C.hand_normal(side)
        along = (hd - wr).normalized()
        forward = (along * 0.3 + Vector((0, -1, 0))).normalized() if side == "R" else along
        frame = C.frame_along(wr.lerp(hd, 0.55) - n * 0.012, forward, Vector((0, -1, 0)) if side == "L" else -along)
        weapon = maker()
        C.place(weapon, frame)
        C.PARTS.append((weapon, f"hand.{side}"))
        holds[side] = frame
    muzzle = holds["L"] @ Matrix.Translation((0, -0.17, 0.036))
    pistol_back = holds["L"] @ Matrix.Translation((0, -0.05, 0.036))
    fx = {
        "fx_flash": (C.fx_flash("flash", 0.03, "fire"), muzzle, "hand.L"),
        "fx_arc": (build_arc("slash"), Matrix.Translation(B(0, 0, 1.30)), "chest"),
        "fx_whirl": (C.join([build_arc(f"whirl {k}", 0.9, 300) for k in range(2)], "FX whirl"), Matrix.Translation(B(0, 0, 1.0)), "hips"),
    }
    for k in range(8):
        fx[f"fx_shot.{k}"] = (C.fx_bolt(f"shot {k}", 0.16, 0.012, "fire"), None, None)
    extra = C.fx_bones(fx, Matrix.Translation(B(0.2, -0.4, 1.2)))
    chains = C.coat_chains(panels, stiffness=65, gain=0.8, sway=1.5, limit=(35, 15))
    for name, (pts, ribbon) in tails.items():
        chains.append((name, C.resample(pts, 3), "chest", dict(skin=True, stiffness=50, gain=1.1, sway=3.0, limit=(50, 30))))
        C.SKINNED.append((ribbon, ["chest"] + [f"{name}.{i}" for i in range(3)]))
    chains.append(("hair", C.resample(hair_path, 3), "head", dict(skin=True, stiffness=55, gain=1.1, sway=2.5, limit=(45, 30))))
    C.SKINNED.append((back, ["head", "hair.0", "hair.1", "hair.2"]))
    C.SOCKETS["socket_muzzle"] = ("hand.L", muzzle)
    C.build_rig("Samira rig", chains, extra)
    C.bind(body)
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips(muzzle, pistol_back)


SHOTS = [f"fx_shot.{k}" for k in range(8)]
FX = ["fx_flash", "fx_arc", "fx_whirl"] + SHOTS


def define_clips(muzzle, pistol_back):
    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def muzzle_at(frame):
        return C.carried("hand.L", frame, muzzle.translation)

    def barrel(frame):
        return muzzle_at(frame) - C.carried("hand.L", frame, pistol_back.translation)

    def fire(frame, shot, distance=4.0, peak=1.2):
        flash("fx_flash", frame, 2, peak)
        C.shoot_from(shot, frame, frame + 5, lambda: muzzle_at(frame), lambda: barrel(frame), distance)

    def slash(frame, length=4, turn=0.0, tilt=0.0):
        size("fx_arc", frame - 1, 0.0)
        rot("fx_arc", frame, y=tilt, z=turn)
        size("fx_arc", frame, 1.0)
        rot("fx_arc", frame + length, y=tilt, z=turn - 70)
        size("fx_arc", frame + length, 1.1)
        size("fx_arc", frame + length + 1, 0.0)

    def stance(frame, breath=0.0, sway=0.0):
        """Duelist's stance: blade forward low, pistol cocked at the hip."""
        loc("hips", frame, x=0.008 * sway, z=-0.05 - 0.004 * breath)
        rot("hips", frame, z=14 - 2 * sway)
        rot("spine", frame, x=6 + breath, z=-6)
        rot("chest", frame, x=1 + 1.5 * breath, z=-6 + sway)
        rot("head", frame, x=-4 + breath, z=-8 + 3 * sway)
        C.feet(frame, (0.07, 0.06, 0, -10), (-0.06, -0.12, 0, 22))
        fk_arm("R", frame, up=14, swing=-40, bend=40, out=-4, twist=20, hand=-10)
        fk_arm("L", frame, up=16 + 2 * breath, swing=10, bend=80, out=4, twist=20, hand=-30)
        loc("root", frame)
        rot("root", frame)

    def aim_pistol(frame, up=0.0, out=-4.0, bend=6):
        fk_arm("L", frame, up=up, swing=-88, bend=bend, out=out, hand=-4)

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
            fk_arm("L", frame, up=14, swing=arc, bend=70, out=-4, hand=-20)
            fk_arm("R", frame, up=14, swing=-arc, bend=60, out=-4, hand=-10)

        C.run_cycle(upper, scale=S, lean=12, twist=10)
        fx_off(0)

    @clip("AA", 18)
    def attack():
        start()
        aim_pistol(4)
        rot("chest", 4, z=-12)
        rot("head", 4, z=8)
        fire(6, SHOTS[0])
        aim_pistol(7, up=14, bend=20)
        aim_pistol(9)
        stance(18)

    @clip("P", 30)
    def daredevil():
        start()
        # Style combo: a blade slash, then a pistol shot.
        fk_arm("R", 4, up=70, swing=-10, bend=60, out=40, hand=-10)
        rot("chest", 4, z=25)
        fk_arm("R", 8, up=40, swing=-80, bend=10, out=-50, hand=-10)
        rot("chest", 8, z=-20)
        slash(6, 3, 30)
        aim_pistol(14)
        rot("chest", 14, z=-8)
        fire(16, SHOTS[1])
        aim_pistol(17, up=14, bend=20)
        stance(30)

    @clip("Q", 24)
    def flair():
        start()
        fk_arm("R", 4, up=80, swing=-20, bend=70, out=40, hand=-20)
        rot("chest", 4, z=28)
        loc("hips", 4, z=-0.08)
        fk_arm("R", 9, up=50, swing=-85, bend=8, out=-55, hand=-10)
        rot("chest", 9, z=-26)
        C.feet(9, (0.08, -0.06, 0, -10), (-0.06, 0.12, 0, 26))
        slash(7, 4, 40)
        stance(24)

    @clip("W", 34)
    def blade_whirl():
        start()
        # Blade held out, two fast turns in place; a ring of slashes spins around her.
        fk_arm("R", 4, up=80, swing=-30, bend=10, out=10, hand=0)
        fk_arm("L", 4, up=70, swing=-10, bend=30, out=10, hand=0)
        loc("hips", 4, z=-0.06)
        for k, f in enumerate((4, 8, 12, 16, 20, 24)):
            C.spin_about(f, -120 * k, (0, 0, 1), (0, 0, 0))
        size("fx_whirl", 5, 0.0)
        size("fx_whirl", 7, 1.0)
        for f in range(7, 25, 2):
            rot("fx_whirl", f, z=-720 * (f - 7) / 17)
        size("fx_whirl", 24, 1.0)
        size("fx_whirl", 25, 0.0)
        stance(34)
        C.spin_about(24, -600, (0, 0, 1), (0, 0, 0))
        C.spin_about(34, -720, (0, 0, 1), (0, 0, 0))

    @clip("E", 22)
    def wild_rush():
        start()
        moving = bool(C.OPTIONS.get("root_motion"))
        reach = -1.4 if moving else 0.0
        loc("hips", 3, z=-0.10)
        rot("spine", 3, x=20)
        fk_arm("R", 3, up=60, swing=40, bend=60, out=30, hand=-20)
        loc("root", 3)
        loc("root", 8, y=reach)
        rot("spine", 8, x=26)
        C.feet(8, (0.06, -0.25, 0.05, -10), (-0.06, 0.25, 0.10, -40))
        fk_arm("R", 9, up=40, swing=-85, bend=10, out=-50, hand=-10)
        rot("chest", 9, z=-26)
        slash(9, 4, 30)
        stance(22)
        loc("root", 22, y=reach)
        loc("root", 12, y=reach)

    @clip("R", 60)
    def inferno_trigger():
        start()
        # Pistol out, spinning in place firing all around; the blade raised for balance.
        aim_pistol(4, out=0)
        fk_arm("R", 4, up=60, swing=10, bend=40, out=20, hand=-10)
        loc("hips", 4, z=-0.05)
        k = 0
        for f in range(6, 52, 3):
            C.spin_about(f, -40 * k, (0, 0, 1), (0, 0, 0))
            fire(f, SHOTS[k % 8], 3.5, 1.0)
            k += 1
        C.spin_about(52, -40 * k, (0, 0, 1), (0, 0, 0))
        stance(60)
        C.spin_about(60, -720, (0, 0, 1), (0, 0, 0))

    @clip("Recall", 48, loop=True)
    def recall():
        # Pistol raised, a lazy twirl, smoke blown off the barrel.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.3)
            fk_arm("L", f, up=40, swing=-55, bend=120, out=-30, twist=-20, hand=-40 + 20 * s_)
            rot("head", f, x=4, z=12 + 3 * s_)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        C.fall_back(0, S)
