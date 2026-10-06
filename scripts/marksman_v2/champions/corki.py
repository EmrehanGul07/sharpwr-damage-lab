"""Corki: an original stylized interpretation (yordle aviator with a big moustache, cap and goggles,
flying a twin-wing hextech aircraft with a front rotor, nose guns and missile pods)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, cyl, fk_arm, flash, lathe, loc, material, metaball_object, rot, size, torus, tube

S = 0.62
RIM = (0.6, 0.85, 1.0)
EXPOSURE = -0.15
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55), "Q": dict(angle_deg=28, distance=4.0, height=1.5, target_z=0.9)}
PLANE = Vector((0, 0.05, 0.62))  # aircraft centre, hovering


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#edc5a4", rough=0.5, sss=0.2),
        violet=material("Hull violet", "#382d64", rough=0.4, metal=0.3),
        purple=material("Hull purple", "#643da2", rough=0.4, metal=0.3),
        white=material("Hull white", "#edf1f4", rough=0.4),
        copper=material("Copper", "#b57b49", rough=0.3, metal=1.0),
        dark=material("Dark metal", (0.05, 0.05, 0.06), rough=0.35, metal=0.9),
        leather=material("Flight leather", (0.06, 0.03, 0.018), rough=0.5),
        scarf=material("Scarf", (0.75, 0.15, 0.12), rough=0.6),
        hair=material("Moustache", (0.82, 0.78, 0.7), rough=0.6),
        lens=material("Goggle lens", (0.3, 0.8, 1.0), rough=0.05, emission=0.8),
        glow=material("Hextech", "#8ae4ff", emission=7.0),
        fire=material("Fire", (1.0, 0.55, 0.15), emission=8.0),
        smoke=material("Smoke", (0.4, 0.4, 0.42), rough=0.9, alpha=0.6),
    )
    C.face_materials(iris=(0.25, 0.45, 0.75), lash=(0.05, 0.04, 0.03), lip=(0.55, 0.3, 0.28), brow=(0.82, 0.78, 0.7))


def build_body():
    meta = metaball_object("Corki body")
    C.torso_male(meta, S, chest=1.1, waist=1.15, shoulders=0.95)
    C.limbs(meta, dict(neck=(0.06, 0.055), thigh=(0.09, 0.065), calf=(0.06, 0.065, 0.045), foot=(0.06, 0.05), arm=(0.065, 0.052), forearm=(0.055, 0.045), palm=0.06), hands="mitten")
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (1.36,)]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.78,)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.2 and z > 0.85:
            return "leather" if C.arm_fraction(c, side) > 0.78 else "leather"
        if z > 1.36 and math.hypot(x, y - 0.01) < 0.07:
            return "skin"
        return "leather"

    return C.body_mesh(meta, "Corki body", region, ["skin", "leather"], cuts, tris=12000)


def build_head():
    def extra(meta, h):
        ball(meta, h + Vector((0, -0.05, -0.04)), 0.05, (1.2, 0.8, 0.8))

    C.build_head("Corki head", jaw=0.95, chin=0.9, cheek=1.1, nose=1.6, width=1.05, extra=extra)
    C.build_face(eye_size=1.0, lashes="none", brow_mat="brow", brow_width=0.004, brow_angle=0.05, mouth="flat", mouth_size=0.002)
    h = C.HEAD
    # The grand moustache, ears and an aviator cap with goggles.
    for sx in (1, -1):
        C.tube("Moustache", [h + Vector((0.005 * sx, -0.105, -0.035)), h + Vector((0.05 * sx, -0.10, -0.04)), h + Vector((0.11 * sx, -0.07, -0.02)), h + Vector((0.15 * sx, -0.05, 0.01))], 0.013, "hair", taper=[1.0, 1.3, 0.9, 0.3])
        meta = metaball_object("Ear", resolution=0.004)
        C.clump(meta, [h + Vector((0.08 * sx, 0.0, 0.0)), h + Vector((0.14 * sx, 0.02, 0.03)), h + Vector((0.20 * sx, 0.04, 0.05))], 0.03, 0.004, flat=0.45)
        ear = C.mesh_from_meta(meta, "Ear", voxel=0.003, smooth=3, tris=1200)
        ear.data.materials.append(M["skin"])
        C.PARTS.append((ear, "head"))
    cap = metaball_object("Cap", resolution=0.005)
    ball(cap, h + Vector((0, 0.015, 0.03)), 0.108, (1.0, 1.05, 0.95))
    capm = C.mesh_from_meta(cap, "Aviator cap", voxel=0.005, smooth=3, tris=2500)
    C.delete_faces(capm, lambda c: c.z < h.z + 0.02 and c.y < h.y + 0.02)
    C.solidify(capm, 0.006)
    capm.data.materials.append(M["leather"])
    C.PARTS.append((capm, "head"))
    for sx in (1, -1):
        centre = h + Vector((0.042 * sx, -0.09, 0.08))
        tilt = (math.radians(-55), 0, math.radians(-12 * sx))
        C.PARTS.append((cyl("Goggle rim", "copper", 0.03, 0.02, centre, tilt, 24), "head"))
        C.PARTS.append((cyl("Goggle lens", "lens", 0.024, 0.022, centre, tilt, 24), "head"))


def build_plane():
    """The aircraft, built around PLANE: fuselage along Y (nose toward -Y), wings, tail, guns,
    missile pods and a cockpit ring; the rotor is separate (it spins)."""
    c = PLANE
    parts = [
        lathe("Fuselage", "violet", [(0.0, -0.62), (0.08, -0.6), (0.17, -0.45), (0.21, -0.2), (0.21, 0.15), (0.16, 0.42), (0.08, 0.6), (0.0, 0.64)], 28, "Y", tuple(c)),
        lathe("Hull stripe", "white", [(0.214, -0.12), (0.214, -0.04)], 28, "Y", tuple(c)),
        lathe("Nose cone", "copper", [(0.0, -0.66), (0.07, -0.62), (0.09, -0.58)], 20, "Y", tuple(c)),
        C.torus("Cockpit rim", "copper", 0.16, 0.02, c + Vector((0, 0.05, 0.17)), (0, 0, 0), (1.0, 1.2, 1.0), 32),
        lathe("Exhaust", "dark", [(0.09, 0.58), (0.11, 0.66), (0.10, 0.70)], 20, "Y", tuple(c)),
    ]
    for sx in (1, -1):
        parts.append(C.plate("Wing", "purple", [(0.18 * sx, -0.25, 0.0), (0.75 * sx, -0.05, 0.04), (0.78 * sx, 0.12, 0.04), (0.18 * sx, 0.18, 0.0)], 0.03, 0.0))
        C.place(parts[-1], Matrix.Translation(c))
        parts.append(C.plate("Wing tip", "white", [(0.72 * sx, -0.06, 0.04), (0.82 * sx, -0.02, 0.05), (0.82 * sx, 0.13, 0.05), (0.74 * sx, 0.12, 0.04)], 0.034, 0.0))
        C.place(parts[-1], Matrix.Translation(c))
        parts.append(C.plate("Tail fin", "purple", [(0.06 * sx, 0.40, 0.08), (0.30 * sx, 0.62, 0.22), (0.26 * sx, 0.72, 0.22), (0.05 * sx, 0.58, 0.10)], 0.02, 0.0))
        C.place(parts[-1], Matrix.Translation(c))
        parts.append(cyl("Nose gun", "dark", 0.022, 0.30, c + Vector((0.13 * sx, -0.55, -0.06)), C.X90, 14))
        parts.append(lathe("Missile pod", "copper", [(0.0, -0.25), (0.05, -0.22), (0.06, 0.0), (0.05, 0.18), (0.0, 0.2)], 18, "Y", tuple(c + Vector((0.48 * sx, -0.04, -0.06)))))
        parts.append(ball_mesh("Pod light", "glow", c + Vector((0.48 * sx, -0.29, -0.06)), (0.025, 0.012, 0.025), 12, 6))
    parts.append(ball_mesh("Hextech core", "glow", c + Vector((0, 0.48, 0.10)), (0.06, 0.06, 0.06), 16, 8))
    hull = C.join(parts, "Aircraft")
    blades = [box("Rotor blade", "white", (0.05, 0.012, 0.42), c + Vector((0, -0.70, 0.0)), 0.006, (0, k * math.pi / 3, 0)) for k in range(3)]
    blades.append(ball_mesh("Rotor hub", "copper", c + Vector((0, -0.70, 0.0)), (0.05, 0.04, 0.05), 14, 7))
    rotor = C.join(blades, "Rotor")
    return hull, rotor


def build():
    C.make_joints(scale=S, shoulder_x=0.21, hip_x=0.11, leg_length=0.78, arm_length=0.9)
    materials()
    body = build_body()
    build_head()
    C.scale_parts("head", 1.85, C.J["head_bone"])
    scarf_pts = [B(0.0, 0.08, 1.38), B(0.03, 0.20, 1.34), B(0.05, 0.34, 1.30), B(0.06, 0.48, 1.28)]
    scarf = C.ribbon("Scarf tail", scarf_pts, 0.07 * S, "scarf", (1, 0, 0), 0.006, [1.0, 1.0, 0.9, 0.7], bone=False)
    wrap = C.torus("Scarf wrap", "scarf", 0.07 * S, 0.03 * S, B(0, 0.012, 1.39), (0, 0, 0), (1.0, 0.95, 0.8), 24)
    C.PARTS.append((wrap, "chest"))
    hull, rotor = build_plane()
    c = PLANE
    fx = {
        "fx_flash.L": (C.fx_flash("gun flash L", 0.04, "fire"), Matrix.Translation(c + Vector((0.13, -0.72, -0.06))), "plane"),
        "fx_flash.R": (C.fx_flash("gun flash R", 0.04, "fire"), Matrix.Translation(c + Vector((-0.13, -0.72, -0.06))), "plane"),
        "fx_shell": (C.fx_bolt("shell", 0.16, 0.014, "fire"), None, None),
        "fx_shell2": (C.fx_bolt("shell 2", 0.16, 0.014, "fire"), None, None),
        "fx_hex": (C.fx_bolt("hextech shell", 0.22, 0.02, "glow"), None, None),
        "fx_bomb": (C.fx_orb("phosphorus bomb", 0.06, "fire", 1), None, None),
        "fx_boom": (C.fx_flash("explosion", 0.22, "fire", 10), None, None),
        "fx_missile": (C.join([C.fx_bolt("missile", 0.30, 0.03, "copper"), C.fx_flash("missile flame", 0.03, "fire", 4)], "FX missile"), None, None),
        "fx_trail": (C.join([C.fx_flash(f"valkyrie {k}", 0.12, "fire", 6) for k in range(3)], "FX valkyrie"), None, None),
        "fx_exhaust": (C.fx_flash("exhaust", 0.06, "fire", 5), Matrix.Translation(c + Vector((0, 0.72, 0))) @ Matrix.Rotation(math.pi, 4, "Z"), "plane"),
        "fx_smoke": (C.join([ball_mesh(f"FX smoke {k}", "smoke", (0.04 * k, 0.12 * k, 0.05 * k), (0.08, 0.08, 0.08), 12, 6) for k in range(4)], "FX smoke"), Matrix.Translation(c + Vector((0, 0.6, 0.1))), "plane"),
    }
    extra = [("plane", c, c + Vector((0, -0.3, 0)), "root"), ("rotor", c + Vector((0, -0.70, 0)), c + Vector((0, -0.80, 0)), "plane")]
    extra += C.fx_bones(fx, Matrix.Translation(c + Vector((0, -0.8, 0))))
    chains = [("scarf", C.resample(scarf_pts, 3), "chest", dict(skin=True, stiffness=40, gain=1.2, sway=5.0, limit=(55, 35)))]
    C.SKINNED.append((scarf, ["chest", "scarf.0", "scarf.1", "scarf.2"]))
    C.SOCKETS["socket_muzzle"] = ("plane", Matrix.Translation(c + Vector((0, -0.72, -0.06))))
    C.build_rig("Corki rig", chains, extra)
    # The pilot sits in the plane: hips follow the plane bone.
    C.activate(C.rig)
    C.bpy.ops.object.mode_set(mode="EDIT")
    C.rig.data.edit_bones["hips"].parent = C.rig.data.edit_bones["plane"]
    for side in ("L", "R"):
        C.rig.data.edit_bones[f"ik_foot.{side}"].parent = C.rig.data.edit_bones["plane"]
    C.bpy.ops.object.mode_set(mode="OBJECT")
    C.bind(body)
    C.attach(hull, "plane")
    C.attach(rotor, "rotor")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips()


FX = ["fx_flash.L", "fx_flash.R", "fx_shell", "fx_shell2", "fx_hex", "fx_bomb", "fx_boom", "fx_missile", "fx_trail", "fx_exhaust", "fx_smoke"]


def define_clips():
    c = PLANE
    seat = c + Vector((0, 0.05, 0.12))  # where the pilot's hips sit

    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def spin_rotor(f0, f1, turns_per_frame=0.2):
        pb = C.PB["rotor"]
        pb.rotation_mode = "XYZ"
        for f in range(f0, f1 + 1, 1):
            pb.rotation_euler = (0, 2 * math.pi * turns_per_frame * (f - f0), 0)
            pb.keyframe_insert("rotation_euler", frame=f)

    def seated(frame, bob=0.0, bank=0.0, pitch=0.0, look=0.0):
        """Pilot in the cockpit, hands on the controls; the aircraft hovers, banks and pitches."""
        hips_rest = C.rig.data.bones["hips"].head_local
        loc("hips", frame, *(seat - hips_rest))
        rot("hips", frame)
        rot("spine", frame, x=8)
        rot("chest", frame, x=2, z=-look * 0.3)
        rot("head", frame, x=-6, z=look)
        for side in ("L", "R"):
            sx = C.side_x(side)
            ankle = C.rig.data.bones[f"ik_foot.{side}"].head_local
            loc(f"ik_foot.{side}", frame, *((seat + Vector((0.07 * sx, -0.25, -0.12))) - ankle))
            rot(f"ik_foot.{side}", frame, x=-20)
            fk_arm(side, frame, up=18, swing=-55, bend=60, out=-12, twist=20, hand=-20)
        loc("plane", frame, z=0.03 * bob)
        rot("plane", frame, x=pitch, y=bank)
        loc("root", frame)
        rot("root", frame)

    def start(frame=0):
        seated(frame)
        fx_off(frame)

    def guns(frame, shell, distance=4.0):
        for side in ("L", "R"):
            flash(f"fx_flash.{side}", frame, 2, 1.0)
        C.shoot_from(shell, frame, frame + 5, lambda: C.carried("plane", frame, c + Vector((0.13, -0.75, -0.06))), lambda: C.carried("plane", frame, c + Vector((0, -1.75, -0.06))) - C.carried("plane", frame, c + Vector((0, -0.75, -0.06))), distance)

    @clip("Idle", 48, loop=True)
    def idle():
        for f, bob, look in ((0, 0, 0), (12, 1, 10), (24, 0, 0), (36, -1, -10), (48, 0, 0)):
            seated(f, bob=bob, bank=3 * bob, look=look)
        spin_rotor(0, 48, 0.25)
        fx_off(0)
        size("fx_exhaust", 0, 0.5)
        size("fx_exhaust", 48, 0.5)

    @clip("Walk", 24, loop=True)
    def fly():
        for f, bob in ((0, 0), (6, 1), (12, 0), (18, -1), (24, 0)):
            seated(f, bob=bob, bank=4 * bob, pitch=-8)
        spin_rotor(0, 24, 0.375)
        fx_off(0)
        size("fx_exhaust", 0, 1.2)
        size("fx_exhaust", 24, 1.2)

    @clip("AA", 18)
    def attack():
        start()
        seated(3, pitch=-3)
        guns(5, "fx_shell")
        seated(6, pitch=2)
        seated(9, pitch=-1)
        seated(18)
        spin_rotor(0, 18, 0.25)

    @clip("P", 22)
    def hextech_munitions():
        start()
        seated(3, pitch=-4)
        guns(6, "fx_hex", 4.5)
        seated(7, pitch=3)
        seated(22)
        spin_rotor(0, 22, 0.25)

    @clip("Q", 34)
    def phosphorus_bomb():
        start()
        # A bomb lobbed from the hull in an arc; it bursts in a flash of fire.
        seated(4, pitch=6, look=-6)
        C.fly_path("fx_bomb", [(6, c + Vector((0.0, -0.4, -0.15))), (12, c + Vector((0.0, -1.6, 0.9))), (20, Vector((0.0, -3.0, 0.1)))], (1, 0, 0), 0.1)
        size("fx_bomb", 5, 0.0)
        size("fx_bomb", 6, 1.0)
        size("fx_bomb", 20, 1.0)
        size("fx_bomb", 21, 0.0)
        size("fx_boom", 20, 0.0)
        C.put("fx_boom", 21, Vector((0.0, -3.0, 0.1)))
        size("fx_boom", 21, 1.6)
        size("fx_boom", 28, 0.0)
        seated(10)
        seated(34)
        spin_rotor(0, 34, 0.25)

    @clip("W", 28)
    def valkyrie():
        start()
        moving = bool(C.OPTIONS.get("root_motion"))
        reach = -2.2 if moving else 0.0
        # Nose down, full throttle: a dash leaving a burning trail.
        seated(4, pitch=-14, bank=-6)
        loc("root", 4)
        loc("root", 14, y=reach)
        seated(14, pitch=-16, bank=6)
        size("fx_exhaust", 4, 0.5)
        size("fx_exhaust", 6, 2.0)
        size("fx_exhaust", 14, 2.0)
        size("fx_exhaust", 18, 0.5)
        size("fx_trail", 5, 0.0)
        C.put("fx_trail", 6, Vector((0, 0.2, 0.05)))
        size("fx_trail", 7, 1.2)
        size("fx_trail", 22, 1.0)
        size("fx_trail", 24, 0.0)
        seated(20)
        seated(28)
        for f in (14, 20, 28):
            loc("root", f, y=reach)
        spin_rotor(0, 28, 0.45)

    @clip("E", 44)
    def gatling_gun():
        start()
        # A sustained spray from the nose guns while the pilot leans into it.
        seated(4, pitch=-5)
        k = 0
        for f in range(6, 36, 2):
            guns(f, ("fx_shell", "fx_shell2")[k % 2], 3.0)
            rot("plane", f, x=-5 + (1 if k % 2 else 0), y=2 * math.sin(k))
            k += 1
        seated(38)
        seated(44)
        spin_rotor(0, 44, 0.3)

    @clip("R", 30)
    def missile_barrage():
        start()
        seated(3, pitch=-2, bank=4)
        C.shoot_from("fx_missile", 6, 16, lambda: C.carried("plane", 6, c + Vector((0.48, -0.32, -0.06))), lambda: C.carried("plane", 6, c + Vector((0.48, -1.32, -0.06))) - C.carried("plane", 6, c + Vector((0.48, -0.32, -0.06))), 4.5)
        seated(7, pitch=3, bank=-4)
        size("fx_boom", 16, 0.0)
        C.later(lambda: C.put("fx_boom", 17, C.carried("plane", 6, c + Vector((0.48, -4.8, -0.06)))))
        size("fx_boom", 17, 1.4)
        size("fx_boom", 23, 0.0)
        seated(30)
        spin_rotor(0, 30, 0.25)

    @clip("Recall", 48, loop=True)
    def recall():
        # Settled low, the pilot tips his cap and twirls his moustache.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            seated(f, bob=0.5 * s_)
            loc("plane", f, z=-0.25 + 0.01 * s_)
            fk_arm("R", f, up=60, swing=-70, bend=130, out=-10, twist=20, hand=-30 + 20 * s_)
            rot("head", f, x=-4, z=6 * s_)
        spin_rotor(0, 48, 0.1)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        # Hit: smoke pours out, the engine sputters, the aircraft spirals down and crashes.
        size("fx_smoke", 3, 0.0)
        size("fx_smoke", 6, 1.0)
        size("fx_smoke", 30, 1.6)
        size("fx_smoke", 44, 1.6)
        seated(8, pitch=10, bank=-15, look=20)
        for k, f in enumerate((14, 20, 26, 32)):
            C.spin_about(f, 25 * (k + 1), (0, 0, 1), (0, 0, 0))
            rot("plane", f, x=-10 - 6 * k, y=20 + 8 * k)
            loc("plane", f, z=-0.12 * (k + 1))
        rot("plane", 36, x=-30, y=40)
        loc("plane", 36, z=-0.52)
        C.spin_about(44, 100, (0, 0, 1), (0, 0, 0))
        rot("plane", 44, x=-28, y=42)
        loc("plane", 44, z=-0.52)
        spin_rotor(0, 30, 0.15)
