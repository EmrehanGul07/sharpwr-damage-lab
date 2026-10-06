"""Draven: an original stylized interpretation (broad bare arms, angular moustache, high black crest,
fur collar and two spinning crescent axes)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, fk_arm, flash, lathe, loc, material, metaball_object, rot, size, torus

S = 1.06
RIM = (1.0, 0.4, 0.3)
EXPOSURE = -0.1
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55), "AA": dict(angle_deg=28, distance=3.8, height=1.5, target_z=1.1)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#cfa386", rough=0.5, sss=0.15),
        vest=material("Dark vest", "#36232a", rough=0.55),
        red=material("Blood red", "#a83933", rough=0.5),
        black=material("Black leather", "#211e24", rough=0.45),
        gold=material("Gold", "#d6ae67", rough=0.28, metal=1.0),
        fur=material("Fur", (0.12, 0.09, 0.07), rough=0.95),
        hair=material("Black hair", (0.01, 0.008, 0.008), rough=0.4),
        steel=material("Axe steel", (0.7, 0.68, 0.66), rough=0.2, metal=1.0),
        glow=material("Blood glow", "#ff7259", emission=7.0),
    )
    C.face_materials(iris=(0.30, 0.18, 0.08), lash=(0.01, 0.008, 0.008), lip=(0.45, 0.22, 0.20), brow=(0.01, 0.008, 0.008))


def build_body():
    meta = metaball_object("Draven body")
    C.torso_male(meta, S, chest=1.12, waist=1.0, shoulders=1.18)
    ball(meta, B(0, 0.01, 0.885), 0.13 * S, (1.05, 0.8, 0.35))
    C.limbs(meta, dict(neck=(0.062, 0.055), thigh=(0.074, 0.05), calf=(0.05, 0.056, 0.035), foot=(0.043, 0.037), arm=(0.062, 0.044), forearm=(0.048, 0.034), palm=0.040), hands="mitten")
    for side in ("L", "R"):
        sh, el = C.J[f"shoulder.{side}"], C.J[f"elbow.{side}"]
        ball(meta, sh.lerp(el, 0.45), 0.058 * S, (1.0, 1.0, 1.0))  # biceps
        el2, wr = C.J[f"elbow.{side}"], C.J[f"wrist.{side}"]
        ball(meta, el2.lerp(wr, 0.25), 0.047 * S)  # forearm muscle
        knee, toe = C.J[f"knee.{side}"], C.J[f"toe.{side}"]
        ball(meta, knee.lerp(C.J[f"ankle.{side}"], 0.4), 0.058 * S, (1.0, 1.0, 0.5))
        ball(meta, toe + Vector((0, 0.012, 0.006)), 0.042 * S, (0.95, 1.2, 0.75))
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.38, 0.885, 0.93, 1.0, 1.385)]
    cuts += [((0.05 * S * sx, 0, 0), (1, 0, 0)) for sx in (1, -1)]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.12, 0.62, 0.80)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.22 and z > 0.88:
            f = C.arm_fraction(c, side)
            return "black" if f > 0.80 else "gold" if f > 0.62 else "skin" if f > 0.12 else "vest"
        if z < 0.38:
            return "black"
        if z < 0.885:
            return "black"
        if z < 0.93:
            return "red"
        if z > 1.385 and math.hypot(x, y - 0.01) < 0.08:
            return "skin"
        if y < 0 and abs(x) < 0.05 and z > 1.0:
            return "skin"  # open vest
        return "vest"

    return C.body_mesh(meta, "Draven body", region, ["skin", "vest", "red", "black", "gold"], cuts)


def build_gear():
    # Fur collar over the shoulders.
    meta = metaball_object("Fur collar", resolution=0.006)
    for d in range(-150, 151, 15):
        a = math.radians(d)
        ball(meta, B(math.sin(a) * 0.13, 0.02 + math.cos(a) * 0.09, 1.39 + 0.01 * math.cos(3 * a)), 0.045 * S, (1.0, 1.0, 0.8))
    fur = C.mesh_from_meta(meta, "Fur collar", voxel=0.006, smooth=2, tris=3500)
    fur.data.materials.append(M["fur"])
    C.PARTS.append((fur, "chest"))
    belt = [
        torus("Belt", "black", 0.135 * S, 0.014 * S, B(0, 0.012, 0.91), (0, 0, 0), (1.0, 0.8, 1.0), 40),
        box("Buckle", "gold", (0.05 * S, 0.012, 0.04 * S), B(0, -0.10, 0.91), 0.005),
    ]
    for sx in (1, -1):
        belt.append(box("Axe holster", "black", (0.04 * S, 0.07 * S, 0.12 * S), B(0.15 * sx, 0.02, 0.84), 0.01))
    for o in belt:
        C.PARTS.append((o, "hips"))
    panels = C.coat_panels([("tail.L", 0.06, 0.10, 0.11, 0.93, 0.55, 0.02), ("tail.R", -0.06, 0.10, 0.11, 0.93, 0.55, 0.02)], "red", S)
    return panels


def build_head():
    head = C.build_head("Draven head", jaw=1.12, chin=1.15, cheek=1.02, nose=1.15, width=1.02)
    C.build_face(eye_size=0.85, lashes="soft", brow_mat="brow", brow_width=0.0034, brow_angle=0.2, mouth="smirk", mouth_size=0.0024, mouth_width=1.2, mouth_y=-0.005)
    h = C.HEAD
    # High black crest: sides shaved short, a tall slicked ridge swept back.
    C.hair_cap("Draven hair", "hair", front_y=0.03, front_z=0.08, scale=0.99, thickness=0.004)
    meta = metaball_object("Crest", resolution=0.004)
    for x in (-0.028, 0.0, 0.028):
        w = 1.0 - abs(x) * 8
        C.clump(meta, [h + Vector((x, -0.085, 0.10)), h + Vector((x * 0.8, -0.07, 0.10 + 0.09 * w)), h + Vector((x * 0.6, 0.0, 0.10 + 0.13 * w)), h + Vector((x * 0.7, 0.08, 0.08 + 0.09 * w)), h + Vector((x, 0.11, 0.04))], 0.032, 0.02)
    crest = C.mesh_from_meta(meta, "Crest", voxel=0.0035, smooth=3, tris=3000)
    crest.data.materials.append(M["hair"])
    C.PARTS.append((crest, "head"))
    # The angular moustache sweeping out and down.
    for sx in (1, -1):
        stache = [h + Vector((0.005 * sx, -0.098, -0.04)), h + Vector((0.03 * sx, -0.095, -0.045)), h + Vector((0.06 * sx, -0.08, -0.07)), h + Vector((0.07 * sx, -0.07, -0.11))]
        C.tube("Moustache", stache, 0.007, "hair", taper=[0.8, 1.2, 0.8, 0.2])
        C.tube("Sideburn", [h + Vector((0.085 * sx, -0.03, 0.03)), h + Vector((0.09 * sx, -0.04, -0.02)), h + Vector((0.085 * sx, -0.05, -0.06))], 0.008, "hair", taper=[1.0, 0.9, 0.3], flat=0.5)
    return head


def build_axe(name, mat="steel", glow=None):
    """A crescent axe: grip at the origin, haft toward -Y, three-bladed crescent at the head."""
    parts = [C.cyl(f"{name} haft", "black", 0.012, 0.30, (0, -0.10, 0), C.X90, 10), ball_mesh(f"{name} pommel", "gold", (0, 0.06, 0), (0.018, 0.018, 0.018), 10, 6)]
    for k in range(3):
        a = k * 2 * math.pi / 3
        c, s = math.cos(a), math.sin(a)
        n = Vector((-s, 0, c))
        d = Vector((c, 0, s))
        centre = Vector((0, -0.24, 0))
        blade = [centre + d * 0.03 + n * 0.03, centre + d * 0.16 + n * 0.08, centre + d * 0.22 - n * 0.02, centre + d * 0.12 - n * 0.03, centre + d * 0.03 - n * 0.02]
        parts.append(C.plate(f"{name} blade", mat, [tuple(p) for p in blade], 0.01, 0.0))
        parts.append(C.plate(f"{name} edge", "red", [tuple(centre + d * 0.16 + n * 0.08), tuple(centre + d * 0.22 - n * 0.02), tuple(centre + d * 0.2 - n * 0.0), tuple(centre + d * 0.15 + n * 0.06)], 0.013, 0.0))
    parts.append(ball_mesh(f"{name} hub", glow or "gold", (0, -0.24, 0), (0.03, 0.02, 0.03), 12, 6))
    return C.join(parts, name)


def build():
    C.make_joints(scale=S, shoulder_x=0.22, hip_x=0.098)
    materials()
    body = build_body()
    panels = build_gear()
    build_head()
    C.scale_parts("head", 1.04, C.J["head_bone"])
    holds = {}
    for side in ("L", "R"):
        wr, hd = C.J[f"wrist.{side}"], C.J[f"hand.{side}"]
        n = C.hand_normal(side)
        frame = C.frame_along(wr.lerp(hd, 0.5) - n * 0.012, (hd - wr).normalized() * 0.2 + Vector((0, -1, 0)), n)
        axe = build_axe(f"Axe {side}")
        C.place(axe, frame)
        holds[side] = (frame, axe)
    fx = {f"fx_axe.{k}": (build_axe(f"FX axe {k}", "steel", "glow"), None, None) for k in range(2)}
    fx["fx_rush"] = (C.join([C.torus("FX blood rush", "glow", 0.45, 0.01, (0, 0, 0.12 * k), (0, 0, 0), (1, 1, 1), 36) for k in range(3)], "FX blood rush"), Matrix.Translation(B(0, 0, 0.3)), "root")
    fx["fx_wave"] = (C.join([C.ribbon(f"FX edge {k}", [Vector((-0.6, -0.3 * k, 0)), Vector((0, -0.2 - 0.3 * k, 0.05)), Vector((0.6, -0.3 * k, 0))], 0.12, "glow", (0, 0, 1), 0.0, bone=False) for k in range(2)], "FX double edged"), None, None)
    fx["fx_catch"] = (C.fx_flash("catch", 0.06, "glow", 6), None, None)
    extra = [C.point_bone(f"axe.{side}", m, f"hand.{side}", 0.05) for side, (m, _) in holds.items()]
    extra += C.fx_bones(fx, Matrix.Translation(B(0, -0.4, 1.2)))
    chains = C.coat_chains(panels, stiffness=65, gain=0.8, sway=1.5, limit=(40, 20))
    C.SOCKETS["socket_muzzle"] = ("hand.R", holds["R"][0])
    C.build_rig("Draven rig", chains, extra)
    C.bind(body)
    for side, (m, axe) in holds.items():
        C.attach(axe, f"axe.{side}")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips({side: m for side, (m, _) in holds.items()})


FX = ["fx_axe.0", "fx_axe.1", "fx_rush", "fx_wave", "fx_catch"]


def define_clips(holds):
    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def hand_at(side, frame):
        return C.carried(f"hand.{side}", frame, holds[side].translation)

    def twirl(side, f0, f1, turns_per_frame=0.25):
        """Spin the held axe on its haft between two frames."""
        pb = C.PB[f"axe.{side}"]
        pb.rotation_mode = "XYZ"
        for f in range(f0, f1 + 1, 2):
            pb.rotation_euler = (2 * math.pi * turns_per_frame * (f - f0), 0, 0)
            pb.keyframe_insert("rotation_euler", frame=f)
        pb.rotation_euler = (0, 0, 0)
        pb.keyframe_insert("rotation_euler", frame=f1 + 1)

    def stance(frame, breath=0.0, sway=0.0):
        """Showman's stance: chest out, axes spinning lazily at his sides."""
        loc("hips", frame, x=0.008 * sway, z=-0.03 - 0.005 * breath)
        rot("hips", frame, z=4 - 2 * sway)
        rot("spine", frame, x=-2 + breath)
        rot("chest", frame, x=-6 + 1.5 * breath, z=2 - sway)
        rot("head", frame, x=-6 + breath, z=-6 + 4 * sway)
        C.feet(frame, (0.08, -0.04, 0, -18), (-0.08, 0.04, 0, 18))
        for side in ("L", "R"):
            fk_arm(side, frame, up=22 + 2 * breath, swing=-25, bend=70, out=6, twist=-10, hand=-20)
            size(f"axe.{side}", frame, 1.0)
        loc("root", frame)
        rot("root", frame)

    def throw(side, frame, name, home, peak=1.5, distance=2.2):
        """Overhand throw: the axe spins up in an arc and lands back near him to be caught."""
        fk_arm(side, frame - 4, up=150, swing=40, bend=100, out=10, hand=-20)
        rot("chest", frame - 4, x=-8, z=12 if side == "R" else -12)
        fk_arm(side, frame, up=60, swing=-80, bend=10, out=-10, hand=-10)
        rot("chest", frame, x=6, z=-10 if side == "R" else 10)
        size(f"axe.{side}", frame - 1, 1.0)
        size(f"axe.{side}", frame, 0.0)
        size(f"axe.{side}", home, 0.0)
        size(f"axe.{side}", home + 1, 1.0)
        size(name, frame - 1, 0.0)
        size(name, frame, 1.0)
        size(name, home, 1.0)
        size(name, home + 1, 0.0)
        mid = (frame + home) // 2
        C.fly_path(name, [(frame, lambda: hand_at(side, frame)), (mid - 3, lambda: hand_at(side, frame) + Vector((0, -distance, peak))), (mid + 2, lambda: hand_at(side, frame) + Vector((0, -distance * 0.8, peak * 0.9))), (home, lambda: hand_at(side, home))], (1, 0, 0), -0.12)
        fk_arm(side, home - 2, up=80, swing=-60, bend=60, out=0, hand=-10)
        size("fx_catch", home - 1, 0.0)
        C.later(lambda: C.put("fx_catch", home, hand_at(side, home)))
        size("fx_catch", home, 1.0)
        size("fx_catch", home + 3, 0.0)

    def start(frame=0):
        stance(frame)
        fx_off(frame)
        for side in ("L", "R"):
            loc(f"axe.{side}", frame)
            rot(f"axe.{side}", frame)

    @clip("Idle", 72, loop=True)
    def idle():
        for f, breath, sway in ((0, 0, 0), (18, 1, 0.5), (36, 0, 1), (54, 1, 0.5), (72, 0, 0)):
            stance(f, breath, sway)
        fx_off(0)
        twirl("R", 6, 30, 0.08)

    @clip("Walk", 18, loop=True)
    def run():
        def upper(frame, lead, phase):
            arc = 30 * (1 if lead == "L" else -1) * phase
            fk_arm("L", frame, up=18, swing=arc, bend=70, out=4, hand=-20)
            fk_arm("R", frame, up=18, swing=-arc, bend=70, out=4, hand=-20)
            for side in ("L", "R"):
                size(f"axe.{side}", frame, 1.0)

        C.run_cycle(upper, scale=S, lean=8, twist=12)
        fx_off(0)

    @clip("AA", 36)
    def attack():
        start()
        throw("R", 6, "fx_axe.0", 28)
        stance(36)

    @clip("Q", 30)
    def spinning_axe():
        start()
        # The axe spins up in his raised hand, blades blazing.
        fk_arm("R", 6, up=80, swing=-50, bend=80, out=10, hand=-20)
        twirl("R", 6, 24, 0.3)
        rot("head", 8, x=-4, z=20)
        stance(30)

    @clip("W", 26)
    def blood_rush():
        start()
        # A roaring burst of speed: fists out, crouch, red rings at his feet.
        for side in ("L", "R"):
            fk_arm(side, 5, up=60, swing=-10, bend=90, out=20, hand=-10)
        rot("chest", 5, x=-10)
        rot("head", 5, x=-14)
        loc("hips", 5, z=-0.06)
        size("fx_rush", 4, 0.0)
        size("fx_rush", 7, 1.2)
        for f in range(7, 20, 3):
            rot("fx_rush", f, z=40 * (f - 7))
        size("fx_rush", 19, 0.0)
        stance(26)

    @clip("E", 30)
    def double_edged():
        start()
        # Both axes swung together, a crossing blade wave rolls ahead.
        for side in ("L", "R"):
            fk_arm(side, 5, up=120, swing=40, bend=90, out=20, hand=-20)
            fk_arm(side, 10, up=40, swing=-85, bend=10, out=-20, hand=-10)
        rot("chest", 5, x=-10)
        rot("chest", 10, x=10)
        loc("hips", 10, z=-0.08)
        C.shoot_from("fx_wave", 10, 18, lambda: C.carried("chest", 10, B(0, -0.4, 1.0)), (0, -1, 0), 3.5)
        stance(30)

    @clip("R", 52)
    def whirling_death():
        start()
        # Both axes hurled forward together, glowing; they return in an arc.
        throw("L", 10, "fx_axe.0", 40, 0.6, 3.5)
        throw("R", 11, "fx_axe.1", 41, 0.6, 3.5)
        loc("hips", 10, z=-0.08)
        stance(52)

    @clip("P", 44)
    def league_of_draven():
        start()
        # "Welcome to the League": arms flung wide, chest out, a slow turn to the crowd.
        for side in ("L", "R"):
            fk_arm(side, 10, up=95, swing=-5, bend=40, out=20, hand=10)
        rot("chest", 10, x=-12)
        rot("head", 10, x=-14, z=10)
        rot("head", 24, x=-10, z=-10)
        rot("chest", 24, x=-12, z=-4)
        stance(44)

    @clip("Recall", 48, loop=True)
    def recall():
        # Juggling an axe from hand to hand.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.3)
            fk_arm("R", f, up=40 + 20 * max(0, s_), swing=-50, bend=100, out=0, hand=-10)
            fk_arm("L", f, up=40 + 20 * max(0, -s_), swing=-50, bend=100, out=0, hand=-10)
            rot("head", f, x=-8, z=8 * s_)
        twirl("R", 0, 46, 0.1)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        C.fall_back(0, S)
