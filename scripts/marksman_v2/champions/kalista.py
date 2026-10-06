"""Kalista: an original stylized interpretation (translucent teal armoured revenant, spear, torn
floating hair and an angular spirit crown; she hops between shots)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, fk_arm, flash, lathe, loc, material, metaball_object, rot, size, torus

S = 1.03
RIM = (0.4, 1.0, 0.85)
EXPOSURE = -0.15
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55), "R": dict(angle_deg=28, distance=3.6, height=1.4, target_z=1.0)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Spectral skin", "#77d7c6", rough=0.35, emission=0.4),
        armour=material("Revenant armour", "#193e40", rough=0.35, metal=0.6),
        plate=material("Pale plate", "#32747b", rough=0.3, metal=0.7),
        bone=material("Bone white", "#88bcb5", rough=0.4, metal=0.3),
        steel=material("Spirit steel", "#9cb6a6", rough=0.25, metal=0.9),
        hair=material("Spirit hair", (0.25, 0.85, 0.75), rough=0.4, emission=0.8),
        hair_dark=material("Deep spirit hair", (0.05, 0.35, 0.32), rough=0.45, emission=0.3),
        glow=material("Soul glow", "#67ffe1", emission=7.0),
        cloth=material("Torn cloth", (0.06, 0.14, 0.14), rough=0.7, alpha=0.85),
    )
    C.face_materials(iris=(0.4, 1.0, 0.85), lash=(0.02, 0.06, 0.06), lip=(0.2, 0.45, 0.42))
    M["iris"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 3.0


def build_body():
    meta = metaball_object("Kalista body")
    C.torso_female(meta, S, bust=0.9, hips=0.95, waist=0.88)
    C.limbs(meta, dict(thigh=(0.061, 0.039), calf=(0.039, 0.045, 0.028), arm=(0.042, 0.031), forearm=(0.034, 0.026), palm=0.032), hands="mitten")
    for side in ("L", "R"):
        knee, toe = C.J[f"knee.{side}"], C.J[f"toe.{side}"]
        ball(meta, knee + Vector((0, -0.02, 0.02)), 0.045 * S, (1.0, 0.8, 1.1))
        ball(meta, toe + Vector((0, 0.01, 0.004)), 0.033 * S, (0.9, 1.3, 0.7))
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.55, 0.92, 1.0, 1.40)]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.40, 0.80)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            f = C.arm_fraction(c, side)
            return "plate" if f > 0.80 else "armour" if f > 0.40 else "skin"
        if z < 0.55:
            return "plate"
        if z < 0.92:
            return "armour"
        if z < 1.0:
            return "skin"
        if z > 1.40 and math.hypot(x, y - 0.01) < 0.065:
            return "skin"
        return "armour"

    return C.body_mesh(meta, "Kalista body", region, ["skin", "armour", "plate"], cuts)


def build_gear():
    for side, sx in (("L", 1), ("R", -1)):
        pad = lathe("Pauldron", "plate", [(0.0, 0.05), (0.05, 0.045), (0.075, 0.02), (0.08, -0.02)], 20, "Z")
        C.place(pad, Matrix.Translation(B(0.165 * sx, 0.012, 1.37)) @ Matrix.Rotation(math.radians(-28 * sx), 4, "Y"))
        C.PARTS.append((pad, f"shoulder.{side}"))
        for k in range(2):
            spike = C.cone("Pauldron spike", "bone", 0.014, 0.0, 0.08, B((0.18 + 0.02 * k) * sx, 0.02, 1.42), (0, math.radians(-50 * sx), 0), 5)
            C.PARTS.append((spike, f"shoulder.{side}"))
    belt = [torus("Belt", "steel", 0.115 * S, 0.01 * S, B(0, 0.01, 0.94), (0, 0, 0), (1.0, 0.8, 1.0), 40)]
    for o in belt:
        C.PARTS.append((o, "hips"))
    # Torn cloth panels that float behind her.
    panels = C.coat_panels(
        [
            ("tail.L", 0.06, 0.10, 0.10, 0.95, 0.38, 0.05),
            ("tail.R", -0.06, 0.10, 0.10, 0.95, 0.40, 0.05),
            ("side.L", 0.12, 0.0, 0.08, 0.95, 0.50, 0.08),
            ("side.R", -0.12, 0.0, 0.08, 0.95, 0.48, 0.08),
        ],
        "cloth",
        S,
    )
    for name, (pts, mesh) in panels.items():  # tear notches into the hems
        for v in mesh.data.vertices:
            if v.co.z < pts[-1].z + 0.03:
                v.co.z += 0.03 * math.sin(v.co.x * 160)
    return panels


def build_head():
    C.build_head("Kalista head", jaw=0.92, chin=0.95, nose=0.9)
    C.build_face(eye_size=1.0, lashes="winged", brow_mat="hair_dark", brow_width=0.0018, brow_angle=0.14, mouth="flat", mouth_size=0.0018)
    h = C.HEAD
    C.hair_cap("Kalista hair", "hair", front_y=0.045, front_z=0.055)
    # Torn hair floating up and back as if underwater; it hangs on chains.
    meta = metaball_object("Kalista hair", resolution=0.004)
    for sx in (1, -1):
        C.clump(meta, [h + Vector((0.07 * sx, -0.06, 0.08)), h + Vector((0.10 * sx, -0.04, 0.02)), h + Vector((0.11 * sx, 0.0, -0.08))], 0.016, 0.004, flat=0.6)
    front = C.mesh_from_meta(meta, "Kalista front hair", voxel=0.0035, smooth=3, tris=2000)
    front.data.materials.append(M["hair"])
    C.PARTS.append((front, "head"))
    strands = {}
    for k, (x, lift) in enumerate(((0.05, 0.10), (0.0, 0.16), (-0.05, 0.12))):
        path = [h + Vector((x, 0.09, 0.06)), h + Vector((x * 1.4, 0.18, 0.04 + lift)), h + Vector((x * 1.8, 0.28, 0.0 + lift * 1.3)), h + Vector((x * 2.0, 0.38, -0.04 + lift * 1.2))]
        sheet = metaball_object(f"Spirit strand {k}", resolution=0.0045)
        C.clump(sheet, path, 0.03, 0.006, flat=0.6)
        mesh = C.mesh_from_meta(sheet, f"Spirit strand {k}", voxel=0.004, smooth=3, tris=1200)
        C.paint_regions(mesh, lambda c: "hair" if (c - h).length < 0.2 else "hair_dark", ["hair", "hair_dark"])
        strands[f"strand.{k}"] = (path, mesh)
    # The angular spirit crown.
    crown = []
    for k, a in enumerate((-50, -25, 0, 25, 50)):
        r = math.radians(a)
        tall = 0.12 if a == 0 else 0.08 - 0.012 * abs(k - 2)
        spike = C.plate("Crown spike", "glow" if a == 0 else "steel", [(0, 0, 0), (0.014, 0, tall * 0.5), (0, 0, tall), (-0.014, 0, tall * 0.5)], 0.005, 0.0)
        C.place(spike, Matrix.Translation(h + Vector((math.sin(r) * 0.1, -math.cos(r) * 0.09 + 0.01, 0.085))) @ Matrix.Rotation(-r, 4, "Z") @ Matrix.Rotation(math.radians(-15), 4, "X"))
        crown.append(spike)
    crown.append(C.torus("Crown band", "steel", 0.1, 0.005, h + Vector((0, 0.005, 0.075)), (math.radians(-12), 0, 0), (1.0, 1.08, 1.0), 40))
    for o in crown:
        C.PARTS.append((o, "head"))
    return strands


def build_spear(name, mat="steel", tip="glow"):
    """A long spear: grip at the origin, point toward -Y."""
    parts = [
        C.cyl(f"{name} shaft", "bone", 0.011, 1.3, (0, -0.25, 0), C.X90, 10),
        C.cone(f"{name} head", tip, 0.03, 0.0, 0.20, (0, -1.0, 0), (-math.pi / 2, 0, 0), 4),
        C.plate(f"{name} barb", mat, [(0.0, -0.86, 0.0), (0.06, -0.80, 0.0), (0.0, -0.92, 0.0)], 0.006, 0.0),
        C.plate(f"{name} barb 2", mat, [(0.0, -0.86, 0.0), (-0.06, -0.80, 0.0), (0.0, -0.92, 0.0)], 0.006, 0.0),
        C.cyl(f"{name} butt", mat, 0.016, 0.06, (0, 0.40, 0), C.X90, 10),
    ]
    return C.join(parts, name)


def build():
    C.make_joints(scale=S, shoulder_x=0.176, hip_x=0.093)
    materials()
    body = build_body()
    panels = build_gear()
    strands = build_head()
    C.scale_parts("head", 1.06, C.J["head_bone"])
    # The spear in her right hand, point forward.
    wr, hd = C.J["wrist.R"], C.J["hand.R"]
    n = C.hand_normal("R")
    grip = C.frame_along(wr.lerp(hd, 0.5) - n * 0.012, Vector((0, -1, 0.15)), Vector((0, 0, 1)))
    spear = build_spear("Spear")
    C.place(spear, grip)
    fx = {f"fx_spear.{k}": (build_spear(f"FX spear {k}", "glow", "glow"), None, None) for k in range(3)}
    fx["fx_rend"] = (C.fx_flash("rend", 0.12, "glow", 8), None, None)
    fx["fx_sentinel"] = (C.fx_orb("sentinel", 0.08, "glow", 2), None, None)
    fx["fx_oath"] = (C.join([C.torus("FX fates call", "glow", 0.45 + 0.1 * k, 0.008, (0, 0, 0.1 * k), (0, 0, 0), (1, 1, 1), 40) for k in range(3)], "FX fates call"), Matrix.Translation(B(0, 0, 0.2)), "root")
    extra = [C.point_bone("spear", grip, "hand.R", 0.05)]
    extra += C.fx_bones(fx, Matrix.Translation(B(-0.2, -0.4, 1.2)))
    chains = C.coat_chains(panels, stiffness=40, gain=1.0, sway=4.0, limit=(45, 25))
    for name, (path, mesh) in strands.items():
        chains.append((name, C.resample(path, 3), "head", dict(skin=True, stiffness=35, gain=1.0, sway=5.0, limit=(40, 30))))
        C.SKINNED.append((mesh, ["head"] + [f"{name}.{i}" for i in range(3)]))
    C.SOCKETS["socket_muzzle"] = ("hand.R", grip)
    C.build_rig("Kalista rig", chains, extra)
    C.bind(body)
    C.attach(spear, "spear")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips(grip)


SPEARS = [f"fx_spear.{k}" for k in range(3)]
FX = SPEARS + ["fx_rend", "fx_sentinel", "fx_oath"]


def define_clips(grip):
    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def hand_at(frame):
        return C.carried("hand.R", frame, grip.translation)

    def stance(frame, breath=0.0, sway=0.0):
        """Spectral poise: weight low, spear held back ready to throw, left hand forward."""
        loc("root", frame, z=0.02 * breath)
        rot("root", frame)
        loc("hips", frame, x=0.008 * sway, z=-0.05)
        rot("hips", frame, z=12 - 2 * sway)
        rot("spine", frame, x=6 + breath, z=-6)
        rot("chest", frame, x=2 + 1.5 * breath, z=-8 + sway)
        rot("head", frame, x=-4 + breath, z=-10 + 3 * sway)
        C.feet(frame, (0.07, -0.12, 0, -16), (-0.06, 0.10, 0, 24))
        fk_arm("R", frame, up=40, swing=20, bend=80, out=10, twist=-10, hand=-10)
        fk_arm("L", frame, up=20 + 2 * breath, swing=-45, bend=30, out=-10, twist=15, hand=-10)
        size("spear", frame, 1.0)

    def throw(frame, name, hop=True, distance=4.0):
        """Javelin throw, with her signature backwards hop after the release."""
        fk_arm("R", frame - 4, up=90, swing=50, bend=70, out=10, hand=-20)
        rot("chest", frame - 4, x=-6, z=20)
        fk_arm("R", frame, up=60, swing=-80, bend=10, out=-10, hand=-10)
        rot("chest", frame, x=6, z=-14)
        size("spear", frame - 1, 1.0)
        size("spear", frame, 0.0)
        size("spear", frame + 7, 0.0)
        size("spear", frame + 9, 1.0)
        C.shoot_from(name, frame, frame + 6, lambda: hand_at(frame), (0, -1, 0.02), distance)
        if hop:
            moving = bool(C.OPTIONS.get("root_motion"))
            back = 0.5 if moving else 0.0
            loc("root", frame + 1)
            loc("root", frame + 5, y=back * 0.6, z=0.25)
            loc("root", frame + 9, y=back)
            for side in ("L", "R"):
                loc(f"ik_foot.{side}", frame + 5, x=0.02 * C.side_x(side), y=0.10, z=0.10)
                rot(f"ik_foot.{side}", frame + 5, x=-30)
            return back
        return 0.0

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
            fk_arm("L", frame, up=14, swing=arc, bend=65, out=-4, hand=-10)
            fk_arm("R", frame, up=20, swing=-arc * 0.5 + 10, bend=80, out=6, hand=-10)
            size("spear", frame, 1.0)

        C.run_cycle(upper, scale=S, lean=12, twist=10)
        fx_off(0)

    @clip("AA", 24)
    def attack():
        start()
        back = throw(6, SPEARS[0])
        stance(24)
        loc("root", 24, y=back)

    @clip("P", 26)
    def martial_poise():
        start()
        # A throw and a long evasive hop backwards.
        back = throw(5, SPEARS[1])
        loc("root", 14, y=back * 2.0, z=0.18)
        loc("root", 18, y=back * 2.4)
        stance(26)
        loc("root", 26, y=back * 2.4)

    @clip("Q", 30)
    def pierce():
        start()
        # A heavier wind-up and a piercing spear.
        fk_arm("R", 4, up=100, swing=60, bend=60, out=15, hand=-20)
        rot("chest", 4, x=-8, z=26)
        loc("hips", 4, z=-0.10)
        throw(10, SPEARS[2], hop=False, distance=5.0)
        stance(30)

    @clip("E", 30)
    def rend():
        start()
        # A clenched fist: every lodged spear tears out in a burst of soul light.
        fk_arm("L", 6, up=60, swing=-70, bend=40, out=-10, hand=-40)
        fk_arm("L", 12, up=55, swing=-40, bend=110, out=-10, hand=-60)
        rot("chest", 12, x=-6, z=8)
        rot("head", 12, x=-6)
        size("fx_rend", 11, 0.0)
        C.put("fx_rend", 12, B(0.0, -3.0, 1.1))
        size("fx_rend", 12, 1.6)
        size("fx_rend", 18, 0.0)
        stance(30)

    @clip("W", 30)
    def sentinel():
        start()
        # A soul sentinel sent out on patrol from her open hand.
        fk_arm("L", 6, up=40, swing=-80, bend=20, out=-10, hand=-50)
        size("fx_sentinel", 7, 0.0)
        C.later(lambda: C.put("fx_sentinel", 8, C.carried("hand.L", 8, C.J["hand.L"])))
        size("fx_sentinel", 8, 1.0)
        C.later(lambda: C.put("fx_sentinel", 22, C.carried("hand.L", 8, C.J["hand.L"]) + Vector((0.4, -3.0, 0.2))))
        size("fx_sentinel", 22, 1.0)
        size("fx_sentinel", 23, 0.0)
        stance(30)

    @clip("R", 44)
    def fates_call():
        start()
        # Spear raised to the sky, oath rings rise around her.
        fk_arm("R", 8, up=165, swing=-10, bend=10, out=-5, hand=-20)
        fk_arm("L", 8, up=60, swing=-40, bend=50, out=-10)
        rot("chest", 8, x=-10)
        rot("head", 8, x=-20)
        size("fx_oath", 7, 0.0)
        size("fx_oath", 10, 1.0)
        for f in range(10, 31, 4):
            rot("fx_oath", f, z=25 * (f - 10))
        size("fx_oath", 30, 1.3)
        size("fx_oath", 34, 0.0)
        stance(44)

    @clip("Recall", 48, loop=True)
    def recall():
        # Spear planted, both hands on the shaft, a still vigil.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.2)
            fk_arm("R", f, up=20, swing=-45, bend=60, out=-20, twist=20, hand=-60)
            fk_arm("L", f, up=24, swing=-50, bend=70, out=-25, twist=20, hand=-40)
            rot("head", f, x=14, z=0)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        C.fall_back(0, S)
