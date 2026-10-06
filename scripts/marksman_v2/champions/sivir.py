"""Sivir: an original stylized interpretation (dark hair, gold tiara, teal armour, red sash and a
broad four-point crossblade)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, fk_arm, flash, lathe, loc, material, metaball_object, rot, size, torus

S = 1.04
RIM = (1.0, 0.8, 0.4)
EXPOSURE = -0.15
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55), "Q": dict(angle_deg=28, distance=4.4, height=1.4, target_z=0.9)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#ba8158", rough=0.5, sss=0.1),
        teal=material("Teal armour", "#194f54", rough=0.45, metal=0.3),
        red=material("Red sash", "#973e36", rough=0.6),
        sand=material("Sand cloth", "#f1deaf", rough=0.65),
        gold=material("Gold", "#d3b164", rough=0.28, metal=1.0),
        leather=material("Leather", (0.09, 0.05, 0.03), rough=0.5),
        hair=material("Dark hair", (0.03, 0.015, 0.01), rough=0.45),
        hair_dark=material("Deep hair", (0.015, 0.008, 0.006), rough=0.5),
        blade=material("Blade steel", (0.75, 0.72, 0.62), rough=0.2, metal=1.0),
        glow=material("Golden light", "#ffdb73", emission=7.0),
        shield=material("Spell shield", (1.0, 0.85, 0.45), emission=2.5, alpha=0.3),
    )
    C.face_materials(iris=(0.30, 0.18, 0.08), lash=(0.01, 0.008, 0.006), lip=(0.50, 0.24, 0.20))


def build_body():
    meta = metaball_object("Sivir body")
    C.torso_female(meta, S, bust=0.98, hips=1.0, waist=0.95)
    C.limbs(meta, dict(thigh=(0.064, 0.041), calf=(0.041, 0.047, 0.03), arm=(0.044, 0.032), forearm=(0.034, 0.026), palm=0.033), hands="mitten")
    for side in ("L", "R"):
        toe = C.J[f"toe.{side}"]
        ball(meta, toe + Vector((0, 0.01, 0.004)), 0.033 * S, (0.9, 1.25, 0.7))
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.30, 0.86, 0.95, 1.08, 1.20, 1.36)]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.30, 0.62, 0.82)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            f = C.arm_fraction(c, side)
            return "leather" if f > 0.82 else "gold" if f > 0.62 else "skin" if f > 0.30 else "teal"
        if z < 0.30:
            return "leather"
        if z < 0.86:
            return "skin" if z > 0.62 else "gold"  # bare thighs, gold greaves
        if z < 0.95:
            return "teal"
        if z < 1.08:
            return "skin"  # bare midriff
        if z < 1.36:
            return "teal"
        return "skin"

    return C.body_mesh(meta, "Sivir body", region, ["skin", "teal", "gold", "leather"], cuts)


def build_gear():
    parts = []
    for side, sx in (("L", 1), ("R", -1)):
        pauldron = lathe("Pauldron", "gold", [(0.0, 0.045), (0.045, 0.04), (0.07, 0.015), (0.075, -0.015)], 20, "Z")
        C.place(pauldron, Matrix.Translation(B(0.165 * sx, 0.012, 1.37)) @ Matrix.Rotation(math.radians(-30 * sx), 4, "Y"))
        C.PARTS.append((pauldron, f"shoulder.{side}"))
    gorget = torus("Gorget", "gold", 0.075 * S, 0.012 * S, B(0, 0.012, 1.38), (math.radians(-8), 0, 0), (1.1, 0.95, 0.6), 32)
    C.PARTS.append((gorget, "chest"))
    belt = [
        torus("Belt", "gold", 0.12 * S, 0.012 * S, B(0, 0.01, 0.945), (0, 0, 0), (1.0, 0.8, 1.0), 40),
        ball_mesh("Belt disc", "gold", B(0, -0.095, 0.945), (0.03, 0.01, 0.03), 16, 8),
    ]
    for o in belt:
        C.PARTS.append((o, "hips"))
    # Red sash and loincloth panels on springs.
    panels = C.coat_panels(
        [("front", 0.0, -0.10, 0.12, 0.94, 0.55, 0.0), ("back", 0.0, 0.11, 0.13, 0.94, 0.55, 0.0), ("sash.L", 0.12, 0.0, 0.06, 0.94, 0.62, 0.03)],
        "red",
        S,
    )
    return panels


def build_head():
    C.build_head("Sivir head", jaw=0.98, chin=1.0, nose=1.0)
    C.build_face(eye_size=0.95, lashes="winged", brow_mat="hair", brow_width=0.002, brow_angle=0.1, mouth="smirk", mouth_size=0.002)
    h = C.HEAD
    C.hair_cap("Sivir hair", "hair", front_y=0.045, front_z=0.055)
    meta = metaball_object("Sivir side hair", resolution=0.004)
    for sx in (1, -1):
        C.clump(meta, [h + Vector((0.07 * sx, -0.07, 0.08)), h + Vector((0.095 * sx, -0.06, -0.01)), h + Vector((0.095 * sx, -0.04, -0.12))], 0.02, 0.008, flat=0.6)
    side = C.mesh_from_meta(meta, "Sivir side hair", voxel=0.0035, smooth=3, tris=2500)
    side.data.materials.append(M["hair"])
    C.PARTS.append((side, "head"))
    # Tiara: a gold circlet with a raised crest and a gem.
    tiara = C.torus("Tiara", "gold", 0.105, 0.005, h + Vector((0, 0.005, 0.045)), (math.radians(-14), 0, 0), (1.0, 1.08, 1.0), 40)
    crest = C.plate("Tiara crest", "gold", [(-0.03, 0, 0), (0.0, 0, 0.06), (0.03, 0, 0), (0.0, 0, 0.02)], 0.006, 0.0)
    C.place(crest, Matrix.Translation(h + Vector((0, -0.108, 0.07))) @ Matrix.Rotation(math.radians(-14), 4, "X"))
    gem = ball_mesh("Tiara gem", "red", h + Vector((0, -0.112, 0.077)), (0.009, 0.006, 0.011), 12, 6)
    for o in (tiara, crest, gem):
        C.PARTS.append((o, "head"))
    # Long hair down the back on a chain.
    path = [h + Vector((0, 0.10, -0.06)), B(0, 0.13, 1.36), B(0, 0.14, 1.22), B(0, 0.13, 1.08)]
    sheet = metaball_object("Sivir long hair", resolution=0.005)
    C.clump(sheet, path, 0.07, 0.035, flat=0.5)
    mesh = C.mesh_from_meta(sheet, "Sivir long hair", voxel=0.0045, smooth=3, tris=2500)
    C.paint_regions(mesh, lambda c: "hair" if c.z > 1.3 * S else "hair_dark", ["hair", "hair_dark"])
    return path, mesh


def build_crossblade(name, prefix=""):
    """The crossblade in its own frame: centre grip at the origin, blades in the XZ plane."""
    parts = [torus(f"{prefix}Ring", "gold", 0.06, 0.012, (0, 0, 0), (math.pi / 2, 0, 0), (1, 1, 1), 28), ball_mesh(f"{prefix}Hub", "red", (0, 0, 0), (0.025, 0.02, 0.025), 12, 6)]
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        c, s = math.cos(a), math.sin(a)
        n = Vector((-s, 0, c))
        d = Vector((c, 0, s))
        blade = [d * 0.06 + n * 0.035, d * 0.25 + n * 0.05, d * 0.36, d * 0.25 - n * 0.015, d * 0.06 - n * 0.03]
        parts.append(C.plate(f"{prefix}Blade", "blade", [tuple(p) for p in blade], 0.008, 0.0))
        parts.append(C.plate(f"{prefix}Blade edge", "gold", [tuple(d * 0.06 + n * 0.035), tuple(d * 0.25 + n * 0.05), tuple(d * 0.25 + n * 0.035), tuple(d * 0.06 + n * 0.02)], 0.011, 0.0))
    return C.join(parts, name)


def build():
    C.make_joints(scale=S, shoulder_x=0.178, hip_x=0.094)
    materials()
    body = build_body()
    panels = build_gear()
    hair_path, hair = build_head()
    C.scale_parts("head", 1.06, C.J["head_bone"])

    # The crossblade gripped at its hub in the right hand, flat across the hand.
    wr, hd = C.J["wrist.R"], C.J["hand.R"]
    n = C.hand_normal("R")
    grip = C.frame_along(wr.lerp(hd, 0.55) - n * 0.01, Vector((0, -1, 0)), n)
    blade = build_crossblade("Crossblade")
    C.place(blade, grip @ Matrix.Rotation(math.radians(90), 4, "Y"))
    fx = {
        "fx_blade": (build_crossblade("FX crossblade", "FX "), None, None),
        "fx_spark": (C.fx_flash("ricochet spark", 0.06, "glow", 6), None, None),
        "fx_shield": (C.fx_orb("spell shield", 0.62, "shield", 0), Matrix.Translation(B(0, 0, 0.95)), "hips"),
        "fx_hunt": (C.join([C.torus("FX on the hunt", "glow", 0.5, 0.01, (0, 0, 0.05 * k), (0, 0, 0), (1, 1, 1), 40) for k in range(3)], "FX on the hunt"), Matrix.Translation(B(0, 0, 0.1)), "root"),
        "fx_dust": (C.fx_flash("dash dust", 0.12, "sand", 6), None, None),
        "fx_hand": (C.fx_orb("blade glow", 0.06, "glow", 1), grip, "hand.R"),
        "fx_ring": (C.torus("FX ricochet ring", "glow", 0.3, 0.01, (0, 0, 0), (0, 0, 0), (1, 1, 1), 40), Matrix.Translation(B(0, 0, 0.04)), "root"),
    }
    extra = [C.point_bone("blade_hold", grip, "hand.R", 0.05)]
    extra += C.fx_bones(fx, Matrix.Translation(B(-0.3, -0.4, 1.2)))
    chains = C.coat_chains(panels, stiffness=60, gain=0.9, sway=2.0, limit=(45, 25))
    chains.append(("hair", C.resample(hair_path, 3), "head", dict(skin=True, stiffness=55, gain=1.1, sway=3.0, limit=(45, 30))))
    C.SKINNED.append((hair, ["head", "hair.0", "hair.1", "hair.2"]))
    C.SOCKETS["socket_muzzle"] = ("hand.R", grip)
    C.build_rig("Sivir rig", chains, extra)
    C.bind(body)
    C.attach(blade, "blade_hold")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips(grip, blade)


FX = ["fx_blade", "fx_spark", "fx_shield", "fx_hunt", "fx_dust", "fx_hand", "fx_ring"]


def define_clips(grip, blade):
    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def hand_point(frame):
        return C.carried("hand.R", frame, grip.translation)

    def stance(frame, breath=0.0, sway=0.0):
        """Ready stance: crossblade cocked at the right hip, left hand forward for balance."""
        loc("hips", frame, x=-0.012 * sway, z=-0.04 - 0.004 * breath)
        rot("hips", frame, z=10 - 2 * sway)
        rot("spine", frame, x=4 + breath, z=-4)
        rot("chest", frame, x=1 + 1.5 * breath, z=-6 + sway)
        rot("head", frame, x=-3 + breath, z=-6 + 3 * sway)
        C.feet(frame, (0.06, -0.12, 0, -18), (-0.06, 0.08, 0, 26))
        fk_arm("R", frame, up=18, swing=15, bend=70, out=4, twist=10, hand=-30)
        fk_arm("L", frame, up=20 + 2 * breath, swing=-40, bend=40, out=-10, twist=15, hand=-10)
        size("blade_hold", frame, 1.0)
        loc("root", frame)
        rot("root", frame)

    def throw(frame, distance=3.0, back=True, turns=0.18, out_frames=7, hold_frames=2):
        """Sidearm throw: the held blade vanishes, a spinning copy flies out and returns."""
        size("blade_hold", frame - 1, 1.0)
        size("blade_hold", frame, 0.0)
        size("fx_blade", frame - 1, 0.0)
        size("fx_blade", frame, 1.0)
        far = frame + out_frames
        home = far + hold_frames + out_frames
        keys = [(frame, lambda: hand_point(frame)), (far, lambda: hand_point(frame) + Vector((0.15, -distance, 0.05)))]
        if back:
            keys += [(far + hold_frames, lambda: hand_point(frame) + Vector((0.1, -distance + 0.1, 0.05))), (home, lambda: hand_point(home))]
            size("fx_blade", home, 1.0)
            size("fx_blade", home + 1, 0.0)
            size("blade_hold", home, 0.0)
            size("blade_hold", home + 1, 1.0)
        else:
            size("fx_blade", far, 1.0)
            size("fx_blade", far + 1, 0.0)
        C.fly_path("fx_blade", keys, (0, 0, 1), turns)
        return home if back else far

    def windup(frame, big=False):
        fk_arm("R", frame, up=50 if big else 40, swing=40 if big else 25, bend=80, out=10, twist=-20, hand=-20)
        rot("chest", frame, x=-2, z=24 if big else 16)
        rot("spine", frame, z=8 if big else 4)
        rot("hips", frame, z=16 if big else 12)

    def release(frame):
        fk_arm("R", frame, up=55, swing=-80, bend=10, out=-20, hand=-30)
        rot("chest", frame, x=4, z=-18)
        rot("spine", frame, z=-8)
        rot("hips", frame, z=-6)
        C.feet(frame, (0.07, -0.18, 0, -12), (-0.05, 0.10, 0, 26))

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
            fk_arm("L", frame, up=14, swing=arc, bend=65, out=-4, hand=-5)
            fk_arm("R", frame, up=16, swing=-arc * 0.6 + 10, bend=70, out=4, hand=-30)
            size("blade_hold", frame, 1.0)

        C.run_cycle(upper, scale=S, lean=10, twist=10)
        fx_off(0)

    @clip("AA", 28)
    def attack():
        start()
        windup(4)
        release(7)
        home = throw(7, 3.0, True, 0.15, 6, 1)
        windup(home + 1)
        stance(28)
        size("blade_hold", 28, 1.0)

    @clip("P", 24)
    def fleet_of_foot():
        start()
        # A burst of speed: low lunge forward, dust kicked up behind.
        loc("hips", 4, y=-0.06, z=-0.12)
        rot("spine", 4, x=24)
        rot("head", 4, x=-18)
        C.feet(4, (0.06, -0.30, 0, -10), (-0.06, 0.30, 0.10, -50))
        fk_arm("L", 4, up=20, swing=40, bend=60)
        fk_arm("R", 4, up=20, swing=-30, bend=70, hand=-30)
        size("fx_dust", 3, 0.0)
        C.put("fx_dust", 4, B(0, 0.35, 0.15))
        size("fx_dust", 5, 1.3)
        size("fx_dust", 10, 0.0)
        stance(24)

    @clip("Q", 48)
    def boomerang_blade():
        start()
        windup(6, True)
        size("fx_hand", 5, 0.0)
        size("fx_hand", 9, 0.8)
        size("fx_hand", 10, 0.0)
        release(11)
        throw(11, 4.5, True, 0.12, 12, 3)
        rot("head", 20, x=-2, z=-4)
        windup(37)
        stance(48)
        size("blade_hold", 48, 1.0)

    @clip("W", 44)
    def ricochet():
        start()
        # A buff, not a throw: she lifts the crossblade and it flares with sand-gold light (a ring
        # rises around her); the empowered auto after it ricochets between targets.
        fk_arm("R", 6, up=110, swing=-20, bend=40, out=10, hand=-30)
        rot("head", 6, x=-10, z=10)
        rot("chest", 6, x=-6)
        for f, s_ in ((2, 0.0), (7, 1.8), (12, 1.3), (17, 0.0)):
            size("fx_hand", f, s_)
        for f, s_ in ((5, 0.0), (8, 1.0), (15, 1.2), (18, 0.0)):
            size("fx_ring", f, s_)
        loc("fx_ring", 8)
        loc("fx_ring", 18, z=0.5)
        windup(15)
        release(18)
        home = throw(18, 3.2, True, 0.15, 7, 3)
        for f, co in ((25, B(-0.2, -3.2, 1.2)), (27, B(0.8, -3.6, 1.1))):
            size("fx_spark", f - 1, 0.0)
            C.put("fx_spark", f, co)
            size("fx_spark", f, 1.3)
            size("fx_spark", f + 2, 0.0)
        windup(home + 1)
        stance(44)
        size("blade_hold", 44, 1.0)

    @clip("E", 36)
    def spell_shield():
        start()
        # Blade raised as a guard, a golden shield blooms around her.
        fk_arm("R", 5, up=60, swing=-70, bend=80, out=-20, twist=20, hand=-40)
        fk_arm("L", 5, up=40, swing=-60, bend=80, out=-25)
        loc("hips", 5, z=-0.08)
        rot("spine", 5, x=10)
        size("fx_shield", 4, 0.0)
        size("fx_shield", 7, 1.15)
        size("fx_shield", 9, 1.0)
        size("fx_shield", 26, 1.0)
        size("fx_shield", 30, 0.0)
        stance(36)

    @clip("R", 48)
    def on_the_hunt():
        start()
        # A rallying cry: blade thrust overhead, golden rings rise around her.
        fk_arm("R", 8, up=165, swing=-10, bend=15, out=-5, hand=-20)
        fk_arm("L", 8, up=40, swing=-30, bend=60, out=-10)
        rot("chest", 8, x=-10)
        rot("head", 8, x=-20)
        loc("hips", 8, z=0.0)
        size("fx_hunt", 7, 0.0)
        size("fx_hunt", 10, 1.0)
        size("fx_hunt", 26, 1.4)
        size("fx_hunt", 32, 0.0)
        size("fx_hand", 7, 0.0)
        size("fx_hand", 10, 1.4)
        size("fx_hand", 24, 0.0)
        stance(48)

    @clip("Recall", 48, loop=True)
    def recall():
        # Spins the crossblade on one finger, watching it turn.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.3)
            fk_arm("R", f, up=60, swing=-60, bend=110, out=-20, twist=10, hand=-60)
            rot("head", f, x=10, z=-10)
        pb = C.PB["blade_hold"]
        for f in (0, 48):
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (0, 0, 0 if f == 0 else 4 * math.pi)
            pb.keyframe_insert("rotation_euler", frame=f)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        C.fall_back(0, S)
