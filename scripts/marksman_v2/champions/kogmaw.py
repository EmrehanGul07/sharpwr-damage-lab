"""Kog'Maw: an original stylized interpretation (a low six-legged void creature with a huge glowing
mouth, ridged carapace, tusks and bulbous acid sacs)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, clip, flash, loc, material, metaball_object, rot, size, tube

RIM = (0.7, 1.0, 0.3)
EXPOSURE = -0.1
CLIP_VIEWS = {"R": dict(angle_deg=30, distance=4.4, height=1.6, target_z=0.6), "E": dict(angle_deg=30, distance=4.0, height=1.4, target_z=0.5), "Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.4)}
LEGS = [("L0", 1, -0.24), ("R0", -1, -0.24), ("L1", 1, 0.02), ("R1", -1, 0.02), ("L2", 1, 0.28), ("R2", -1, 0.28)]
GAIT_A = ("L0", "R1", "L2")


def materials():
    M.update(
        skin=material("Void hide", "#acb581", rough=0.6, sss=0.1),
        shell=material("Carapace", "#334329", rough=0.35, metal=0.2),
        olive=material("Olive plates", "#788352", rough=0.4),
        belly=material("Belly", "#aaba77", rough=0.7),
        dark=material("Dark chitin", "#4d4c2b", rough=0.4),
        tusk=material("Tusk", (0.85, 0.82, 0.65), rough=0.4),
        mouth=material("Maw", (0.08, 0.02, 0.05), rough=0.6),
        acid=material("Acid", "#afff57", emission=7.0),
        sac=material("Acid sac", (0.6, 0.95, 0.2), emission=2.5, alpha=0.8),
        eye=material("Eyes", (1.0, 0.9, 0.2), emission=4.0),
        puddle=material("Ooze", (0.5, 0.95, 0.2), emission=2.0, alpha=0.7),
    )


def build_body():
    meta = metaball_object("Kog body")
    ball(meta, (0, 0.26, 0.4), 0.28, (1.0, 1.15, 0.73))  # abdomen
    ball(meta, (0, -0.02, 0.43), 0.25, (1.05, 1.0, 0.73))
    ball(meta, (0, -0.28, 0.48), 0.22, (1.0, 0.9, 0.78))
    for prefix, sx, y in LEGS:
        hip, knee, foot = Vector((0.20 * sx, y, 0.36)), Vector((0.40 * sx, y, 0.42)), Vector((0.50 * sx, y, 0.03))
        C.chain(meta, hip, knee, 0.09, 0.07)
        C.chain(meta, knee, foot + Vector((0, 0, 0.04)), 0.07, 0.045)
    body = C.mesh_from_meta(meta, "Kog body", voxel=0.008, smooth=5, tris=14000)
    C.paint_regions(body, lambda c: "belly" if c.z < 0.30 and abs(c.x) < 0.22 else "skin" if abs(c.x) > 0.26 else "shell", ["skin", "shell", "belly"])
    return body


def build_head():
    meta = metaball_object("Kog head")
    ball(meta, (0, -0.55, 0.54), 0.26, (1.1, 1.0, 0.78))
    ball(meta, (0, -0.70, 0.54), 0.16, (1.2, 0.8, 0.58))
    head = C.mesh_from_meta(meta, "Kog head", voxel=0.007, smooth=4, tris=5000)
    C.delete_faces(head, lambda c: c.y < -0.70 and c.z < 0.52)  # the maw opening
    C.solidify(head, 0.012)
    C.paint_regions(head, lambda c: "shell" if c.z > 0.62 else "skin", ["shell", "skin"])
    C.PARTS.append((head, "head"))
    C.PARTS.append((ball_mesh("Maw", "mouth", (0, -0.66, 0.48), (0.17, 0.12, 0.1), 20, 10), "head"))
    C.PARTS.append((ball_mesh("Maw glow", "acid", (0, -0.70, 0.48), (0.09, 0.05, 0.05), 16, 8), "head"))
    for k in range(4):  # small yellow eyes on top
        sx = 1 if k % 2 else -1
        C.PARTS.append((ball_mesh("Eye", "eye", (0.06 * sx * (1 + k // 2), -0.62 + 0.04 * (k // 2), 0.74 - 0.02 * (k // 2)), (0.022, 0.022, 0.018), 12, 6), "head"))
    for k in range(7):  # upper teeth
        x = -0.15 + 0.05 * k
        C.PARTS.append((C.cone("Tooth", "tusk", 0.014, 0.0, 0.05, (x, -0.76, 0.51), (math.pi, 0, 0), 5), "head"))
    for k in range(5):  # crest ridges
        C.PARTS.append((C.cone("Crest", "dark", 0.03, 0.0, 0.09, (0, -0.68 + 0.08 * k, 0.76 - 0.015 * k), (math.radians(-20), 0, 0), 5), "head"))
    # Lower jaw (rigid on the jaw bone) with teeth and tusks.
    meta = metaball_object("Kog jaw")
    ball(meta, (0, -0.62, 0.34), 0.18, (1.15, 1.1, 0.43))
    jaw = C.mesh_from_meta(meta, "Kog jaw", voxel=0.007, smooth=4, tris=2500)
    jaw.data.materials.append(M["belly"])
    C.PARTS.append((jaw, "jaw"))
    for k in range(6):
        x = -0.125 + 0.05 * k
        C.PARTS.append((C.cone("Lower tooth", "tusk", 0.013, 0.0, 0.045, (x, -0.76, 0.4), (0, 0, 0), 5), "jaw"))
    for sx in (1, -1):
        tusk = tube("Tusk", [Vector((0.15 * sx, -0.66, 0.36)), Vector((0.22 * sx, -0.80, 0.4)), Vector((0.20 * sx, -0.90, 0.54))], 0.03, "tusk", False, taper=[1.0, 0.7, 0.1])
        C.PARTS.append((tusk, "jaw"))


def build_back():
    parts = []
    for k, (y, z, r) in enumerate(((0.32, 0.64, 0.17), (0.08, 0.66, 0.18), (-0.18, 0.66, 0.15))):
        bone = ("body", "spine", "chest")[k]
        plate = ball_mesh("Carapace plate", "olive", (0, y, z), (r * 1.3, r, 0.05), 20, 10)
        C.PARTS.append((plate, bone))
        for sx in (1, -1):
            C.PARTS.append((ball_mesh("Acid sac", "sac", (0.16 * sx, y + 0.04, z - 0.02), (0.07, 0.07, 0.08), 16, 8), bone))
        C.PARTS.append((C.cone("Spine", "dark", 0.035, 0.0, 0.12, (0, y, z + 0.06), (math.radians(-25), 0, 0), 5), bone))
    for prefix, sx, y in LEGS:
        claw = C.cone("Claw", "dark", 0.04, 0.0, 0.08, (0.50 * sx, y, 0.03), (math.pi, 0, 0), 5)
        C.PARTS.append((claw, f"lower.{prefix}"))


def build():
    materials()
    C.HEAD = Vector((0, -0.55, 0.54))
    body = build_body()
    build_head()
    build_back()
    bones = [
        ("body", (0, 0.38, 0.4), (0, 0.04, 0.43), None, True),
        ("spine", (0, 0.04, 0.43), (0, -0.26, 0.48), "body", True),
        ("chest", (0, -0.26, 0.48), (0, -0.42, 0.51), "spine", True),
        ("head", (0, -0.42, 0.51), (0, -0.78, 0.54), "chest", False),
        ("jaw", (0, -0.48, 0.43), (0, -0.80, 0.36), "head", False),
    ]
    legs = []
    parent_of = {-0.24: "chest", 0.02: "spine", 0.28: "body"}
    for prefix, sx, y in LEGS:
        hip, knee, foot = Vector((0.20 * sx, y, 0.36)), Vector((0.40 * sx, y, 0.42)), Vector((0.50 * sx, y, 0.03))
        bones.append((f"upper.{prefix}", hip, knee, parent_of[y], True))
        bones.append((f"lower.{prefix}", knee, foot, f"upper.{prefix}", True))
        legs.append((prefix, f"upper.{prefix}", f"lower.{prefix}", foot, Vector((0.9 * sx, y, 1.1))))
    mouth = Matrix.Translation((0, -0.82, 0.46))
    fx = {
        "fx_glow": (C.fx_orb("maw glow", 0.08, "acid", 1), Matrix.Translation((0, -0.70, 0.48)), "head"),
        "fx_spit": (C.fx_orb("spit", 0.06, "acid", 1), None, None),
        "fx_spit2": (C.fx_orb("spit 2", 0.06, "acid", 1), None, None),
        "fx_big": (C.fx_orb("caustic spittle", 0.10, "acid", 2), None, None),
        "fx_shell": (C.fx_orb("living artillery", 0.16, "acid", 2), None, None),
        "fx_splash": (C.fx_flash("splash", 0.20, "acid", 9), None, None),
        "fx_ooze": (ball_mesh("FX void ooze", "puddle", (0, -1.6, 0.01), (0.35, 1.5, 0.02), 24, 8), Matrix(), "root"),
        "fx_burst": (C.fx_flash("icathian surprise", 0.35, "acid", 10), Matrix.Translation((0, 0, 0.48)), "root"),
    }
    extra = C.fx_bones(fx, mouth)
    chains = [("tail", [Vector((0, 0.50, 0.38)), Vector((0, 0.62, 0.3)), Vector((0, 0.70, 0.2))], "body", dict(stiffness=60, gain=0.8, sway=2.0))]
    C.SOCKETS["socket_muzzle"] = ("head", mouth)
    C.build_creature_rig("Kog rig", bones, legs, chains, extra)
    stub = tube("Tail stub", [Vector((0, 0.48, 0.4)), Vector((0, 0.62, 0.3)), Vector((0, 0.70, 0.18))], 0.06, "shell", False, taper=[1.0, 0.7, 0.2])
    C.bind(body)
    C.attach(stub, "tail.0")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips(mouth)


FX = ["fx_glow", "fx_spit", "fx_spit2", "fx_big", "fx_shell", "fx_splash", "fx_ooze", "fx_burst"]


def define_clips(mouth):
    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def mouth_at(frame):
        return C.carried("head", frame, mouth.translation)

    def stance(frame, breath=0.0, sway=0.0):
        """Low and wide, breathing heavily through the open maw."""
        loc("body", frame, z=-0.01 * breath, x=0.01 * sway)
        rot("body", frame, z=2 * sway)
        rot("spine", frame, x=1.5 * breath)
        rot("chest", frame, x=-2 * breath, z=-2 * sway)
        rot("head", frame, x=3 * breath, z=6 * sway)
        rot("jaw", frame, x=-6 - 6 * breath)
        for prefix, sx, y in LEGS:
            loc(f"ik_{prefix}", frame)
            rot(f"ik_{prefix}", frame)
        loc("root", frame)
        rot("root", frame)

    def spit(frame, name, distance=3.5, lob=0.0):
        rot("head", frame - 4, x=-18)
        rot("jaw", frame - 4, x=-10)
        rot("chest", frame - 4, x=-8)
        rot("head", frame, x=12)
        rot("jaw", frame, x=-40)
        rot("chest", frame, x=6)
        size("fx_glow", frame - 3, 0.0)
        size("fx_glow", frame - 1, 1.3)
        size("fx_glow", frame + 2, 0.0)
        if lob:
            size(name, frame - 1, 0.0)
            size(name, frame, 1.0)
            size(name, frame + 14, 1.0)
            size(name, frame + 15, 0.0)
            C.fly_path(name, [(frame, lambda: mouth_at(frame)), (frame + 7, lambda: mouth_at(frame) + Vector((0, -distance * 0.5, lob))), (frame + 14, lambda: Vector((0, mouth_at(frame).y - distance, 0.1)))], (1, 0, 0), 0.05)
        else:
            C.shoot_from(name, frame, frame + 6, lambda: mouth_at(frame), (0, -1, -0.05), distance)
        rot("jaw", frame + 4, x=-12)

    def start(frame=0):
        stance(frame)
        fx_off(frame)
        C.leg_ik(frame, 1.0)

    @clip("Idle", 48, loop=True)
    def idle():
        for f, breath, sway in ((0, 0, 0), (12, 1, 0.5), (24, 0, 1), (36, 1, 0.5), (48, 0, 0)):
            stance(f, breath, sway)
        fx_off(0)
        size("fx_glow", 0, 0.4)
        size("fx_glow", 24, 0.7)
        size("fx_glow", 48, 0.4)

    @clip("Walk", 16, loop=True)
    def scuttle():
        # Tripod gait: one set of three legs swings while the other pushes.
        for f in range(0, 17, 2):
            phase = 2 * math.pi * f / 16
            stance(f, breath=0.3 * math.sin(phase), sway=0.3 * math.sin(phase))
            loc("body", f, z=0.02 * abs(math.sin(phase)))
            for prefix, sx, y in LEGS:
                p = phase + (0 if prefix in GAIT_A else math.pi)
                swing = math.sin(p)
                lift = max(0.0, math.cos(p)) * 0.10
                loc(f"ik_{prefix}", f, y=-0.14 * swing, z=lift)
        fx_off(0)

    @clip("AA", 22)
    def attack():
        start()
        spit(8, "fx_spit")
        stance(22)

    @clip("P", 30)
    def icathian_surprise():
        start()
        # He swells and glows as if about to burst, then settles with a burp.
        for f, s_ in ((6, 1.08), (12, 1.15), (18, 1.08), (24, 1.0)):
            size("body", f, s_)
            size("spine", f, 1.0)
        size("fx_glow", 4, 0.0)
        size("fx_glow", 12, 1.6)
        size("fx_glow", 20, 0.0)
        rot("jaw", 20, x=-35)
        rot("head", 20, x=-10)
        stance(30)

    @clip("Q", 28)
    def caustic_spittle():
        start()
        spit(10, "fx_big", 4.0)
        size("fx_splash", 15, 0.0)
        C.later(lambda: C.put("fx_splash", 16, mouth_at(10) + Vector((0, -4.0, -0.2))))
        size("fx_splash", 16, 1.0)
        size("fx_splash", 21, 0.0)
        stance(28)

    @clip("W", 44)
    def bio_arcane_barrage():
        start()
        # The maw blazes and he rattles off spit after spit.
        size("fx_glow", 2, 0.0)
        size("fx_glow", 6, 1.8)
        size("fx_glow", 38, 1.4)
        size("fx_glow", 42, 0.0)
        for k, f in enumerate((10, 18, 26, 34)):
            spit(f, ("fx_spit", "fx_spit2")[k % 2], 4.5)
        stance(44)

    @clip("E", 36)
    def void_ooze():
        start()
        # He retches a long trail of ooze along the ground ahead.
        rot("head", 6, x=-12)
        rot("jaw", 6, x=-10)
        rot("head", 10, x=22)
        rot("jaw", 10, x=-45)
        rot("chest", 10, x=10)
        loc("body", 10, z=-0.06)
        size("fx_ooze", 9, 0.0)
        size("fx_ooze", 11, 0.4)
        size("fx_ooze", 18, 1.0)
        size("fx_ooze", 30, 1.0)
        size("fx_ooze", 34, 0.0)
        rot("jaw", 20, x=-12)
        stance(36)

    @clip("R", 44)
    def living_artillery():
        start()
        # He rears up on the back legs and lobs a huge glob high into the air.
        rot("body", 8, x=-20)
        loc("body", 8, z=0.10)
        rot("spine", 8, x=-14)
        rot("head", 8, x=-20)
        for prefix in ("L0", "R0"):
            loc(f"ik_{prefix}", 8, y=-0.05, z=0.35)
        spit(12, "fx_shell", 5.0, lob=2.2)
        size("fx_splash", 25, 0.0)
        C.later(lambda: C.put("fx_splash", 26, Vector((0, mouth_at(12).y - 5.0, 0.1))))
        size("fx_splash", 26, 1.8)
        size("fx_splash", 33, 0.0)
        stance(44)

    @clip("Recall", 48, loop=True)
    def recall():
        # Settles down and scratches with a middle leg, maw lolling.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=0.5, sway=0.0)
            loc("body", f, z=-0.12)
            loc("ik_L1", f, y=-0.15, z=0.30 + 0.05 * s_, x=-0.15)
            rot("head", f, x=-4, z=10 * s_)
            rot("jaw", f, x=-20)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        # The legs give way, he swells and bursts in a cloud of acid.
        for prefix, sx, y in LEGS:
            loc(f"ik_{prefix}", 10, x=0.12 * sx)
        loc("body", 10, z=-0.22)
        rot("head", 10, x=10)
        rot("jaw", 10, x=-40)
        for f, s_ in ((14, 1.1), (20, 1.25), (26, 1.35)):
            size("body", f, s_)
        size("fx_burst", 27, 0.0)
        size("fx_burst", 28, 1.5)
        size("fx_burst", 36, 0.0)
        size("body", 28, 0.8)
        size("body", 44, 0.8)
        loc("body", 44, z=-0.25)
