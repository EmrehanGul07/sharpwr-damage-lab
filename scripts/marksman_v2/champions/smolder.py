"""Smolder: an original stylized interpretation (a young four-legged dragon with a big round head,
huge eyes, curved horns, small membranous wings and a long tail that curls up)."""

import math

import bpy
from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, clip, loc, material, metaball_object, rot, size, tube

VIEW_SCALE = 0.72
RIM = (1.0, 0.62, 0.3)
EXPOSURE = -0.3
CLIP_VIEWS = {
    "E": dict(angle_deg=60, distance=3.6, height=1.3, target_z=0.9),
    "R": dict(angle_deg=50, distance=4.2, height=1.5, target_z=1.1),
    "Q": dict(angle_deg=45, distance=3.6, height=1.2, target_z=0.8),
}
LEGS = [("FL", 1, "front"), ("FR", -1, "front"), ("HL", 1, "hind"), ("HR", -1, "hind")]
TROT_A = ("FL", "HR")
TAIL = [Vector(p) for p in ((0, 0.30, 0.40), (0, 0.48, 0.35), (0, 0.66, 0.29), (0, 0.84, 0.24), (0, 1.00, 0.22), (0, 1.14, 0.24))]
TAIL_R = (0.11, 0.085, 0.066, 0.05, 0.036, 0.022)
MOUTH = Vector((0, -0.67, 0.77))
OPEN = 34.0  # jaw rotation (degrees) for a fully open mouth


def leg_points(sx, kind):
    if kind == "front":
        return Vector((0.12 * sx, -0.14, 0.40)), Vector((0.15 * sx, -0.08, 0.22)), Vector((0.14 * sx, -0.16, 0.05))
    return Vector((0.13 * sx, 0.22, 0.38)), Vector((0.17 * sx, 0.10, 0.22)), Vector((0.16 * sx, 0.20, 0.05))


def glow(name, color, strength, alpha=1.0):
    """A self-lit effect material: dark base so the light comes from a saturated emission
    (AgX washes bright emission out to pastel, so fire stays at a modest strength)."""
    m = material(name, color, rough=1.0, emission=strength, alpha=alpha)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.04, 0.015, 0.0, 1)
    return m


def materials():
    M.update(
        skin=material("Scales", "#e07432", rough=0.5),
        back=material("Back scales", "#a8441c", rough=0.45),
        belly=material("Belly plates", "#ffdf92", rough=0.6, sss=0.08),
        membrane=material("Wing membrane", "#e8823a", rough=0.55, sss=0.2),
        horn=material("Horn", "#f4dfb2", rough=0.35),
        claw=material("Claws", "#623d33", rough=0.35),
        sclera=material("Eye white", (0.95, 0.94, 0.9), rough=0.2),
        iris=material("Iris", "#ffbe4a", rough=0.2, emission=0.6),
        pupil=material("Pupil", (0.02, 0.01, 0.01), rough=0.2),
        shine=material("Eye shine", (1, 1, 1), emission=3.0),
        mouth=material("Mouth", (0.28, 0.05, 0.04), rough=0.6),
        tongue=material("Tongue", (0.85, 0.36, 0.36), rough=0.5),
        fire=glow("Fire", (1.0, 0.17, 0.0), 1.1),
        core_fire=glow("Fire core", (1.0, 0.42, 0.04), 1.3),
        flame=glow("Flame", (1.0, 0.1, 0.0), 1.0, alpha=0.8),
        smoke=material("Smoke", (0.32, 0.31, 0.33), rough=0.9, alpha=0.6),
        heal=glow("Mother glow", (1.0, 0.45, 0.06), 1.0, alpha=0.6),
    )


def tail_planes():
    """Per tail segment: (mid point, up normal, mean radius), for clean belly and back stripes."""
    rows = []
    for k in range(len(TAIL) - 1):
        d = TAIL[k + 1] - TAIL[k]
        rows.append((TAIL[k].lerp(TAIL[k + 1], 0.5), Vector((0, -d.z, d.y)).normalized(), (TAIL_R[k] + TAIL_R[k + 1]) / 2))
    return rows


def tail_segment(y):
    return max(0, min(len(TAIL) - 2, max(k for k in range(len(TAIL) - 1) if TAIL[k].y <= y) if y >= TAIL[0].y else 0))


def build_body():
    meta = metaball_object("Smolder body")
    ball(meta, (0, 0.20, 0.40), 0.15, (1.0, 1.15, 0.95))  # hips
    ball(meta, (0, 0.02, 0.41), 0.17, (1.0, 1.1, 0.92))  # belly
    ball(meta, (0, -0.14, 0.47), 0.16, (1.0, 0.95, 1.05))  # chest
    C.chain(meta, (0, -0.20, 0.55), (0, -0.30, 0.72), 0.105, 0.08)  # neck
    for sx in (1, -1):
        ball(meta, (0.11 * sx, 0.20, 0.36), 0.10)  # haunch
        ball(meta, (0.10 * sx, -0.13, 0.41), 0.08)  # shoulder
        hip, knee, foot = leg_points(sx, "front")
        C.chain(meta, hip, knee, 0.065, 0.05)
        C.chain(meta, knee, foot, 0.05, 0.042)
        ball(meta, foot + Vector((0, -0.03, -0.01)), 0.05, (1.0, 1.35, 0.6))
        hip, knee, foot = leg_points(sx, "hind")
        C.chain(meta, hip, knee, 0.08, 0.06)
        C.chain(meta, knee, foot, 0.055, 0.045)
        ball(meta, foot + Vector((0, -0.03, -0.01)), 0.055, (1.0, 1.4, 0.6))
    for k in range(len(TAIL) - 1):
        C.chain(meta, TAIL[k], TAIL[k + 1], TAIL_R[k], TAIL_R[k + 1])
    body = C.mesh_from_meta(meta, "Smolder body", voxel=0.008, smooth=5, tris=11000)
    planes = tail_planes()
    cuts = [((0, 0, 0.33), (0, 0, 1)), ((0, 0, 0.52), (0, 0, 1)), ((0, -0.21, 0.5), (0, 1, 0.6)), ((0, 1.02, 0), (0, 1, 0))]
    cuts += [((sx * w, 0, 0), (1, 0, 0)) for w in (0.07, 0.10) for sx in (1, -1)]
    for mid, n, r in planes:
        cuts += [(mid - n * 0.55 * r, n), (mid + n * 0.75 * r, n)]
    C.bisect(body, cuts)

    def region(c):
        if c.y > 0.30:  # tail: pale underside, dark stripe on top and a dark tip
            if c.y > 1.02:
                return "back"
            mid, n, r = planes[tail_segment(c.y)]
            s_ = (c - mid).dot(n)
            return "belly" if s_ < -0.55 * r else "back" if s_ > 0.75 * r else "skin"
        if c.z < 0.10:
            return "skin"
        if (c.z < 0.33 and abs(c.x) < 0.10 and c.y > -0.22) or (abs(c.x) < 0.07 and 0.34 < c.z < 0.76 and c.y < -0.21 - 0.6 * (c.z - 0.50)):
            return "belly"
        if abs(c.x) < 0.07 and c.z > 0.52 and c.y > -0.18:
            return "back"
        return "skin"

    C.paint_regions(body, region, ["skin", "back", "belly"])
    return body


def facing(obj, center, normal):
    """Turn a part built around the origin facing -Y so it faces `normal` at `center`."""
    m = Vector((0, -1, 0)).rotation_difference(Vector(normal).normalized()).to_matrix().to_4x4()
    m.translation = Vector(center)
    C.place(obj, m)
    return obj


def build_head():
    meta = metaball_object("Smolder head")
    ball(meta, (0, -0.37, 0.87), 0.16, (1.05, 1.0, 0.92))  # cranium
    ball(meta, (0, -0.27, 0.86), 0.11)  # back of the skull
    ball(meta, (0, -0.52, 0.81), 0.10, (0.85, 1.25, 0.72))  # snout
    ball(meta, (0, -0.60, 0.81), 0.07, (0.9, 1.0, 0.7))  # snout tip
    for sx in (1, -1):
        ball(meta, (0.07 * sx, -0.44, 0.80), 0.09)  # cheeks
        ball(meta, (0.075 * sx, -0.46, 0.94), 0.05, (1.25, 0.8, 0.55))  # brow ridge
    head = C.mesh_from_meta(meta, "Smolder head", voxel=0.006, smooth=4, tris=7000)
    C.paint_regions(head, lambda c: "back" if c.z > 0.99 and c.y > -0.42 else "belly" if c.z < 0.76 and c.y < -0.40 else "skin", ["skin", "back", "belly"])
    C.PARTS.append((head, "head"))
    C.PARTS.append((ball_mesh("Mouth", "mouth", (0, -0.50, 0.755), (0.06, 0.10, 0.025), 16, 8), "head"))
    for sx in (1, -1):
        eye = Vector((0.085 * sx, -0.475, 0.885))
        look = Vector((0.35 * sx, -1.0, 0.05)).normalized()
        C.PARTS.append((ball_mesh("Eye", "sclera", eye, (0.055, 0.05, 0.058), 20, 10), "head"))
        C.PARTS.append((facing(ball_mesh("Iris", "iris", (0, 0, 0), (0.034, 0.012, 0.038), 18, 8), eye + look * 0.042, look), "head"))
        C.PARTS.append((facing(ball_mesh("Pupil", "pupil", (0, 0, 0), (0.01, 0.01, 0.027), 12, 6), eye + look * 0.051, look), "head"))
        C.PARTS.append((ball_mesh("Eye shine", "shine", eye + look * 0.052 + Vector((0.012 * sx, 0, 0.016)), (0.008, 0.005, 0.008), 8, 4), "head"))
        tube("Horn", [Vector((0.075 * sx, -0.31, 0.98)), Vector((0.11 * sx, -0.22, 1.07)), Vector((0.13 * sx, -0.10, 1.11)), Vector((0.13 * sx, 0.0, 1.07))], 0.032, "horn", "head", taper=[1.0, 0.75, 0.45, 0.08])
        fin = C.plate("Ear fin", "back", [(0.12 * sx, -0.36, 0.94), (0.25 * sx, -0.31, 0.98), (0.21 * sx, -0.28, 0.93), (0.31 * sx, -0.21, 0.92), (0.22 * sx, -0.24, 0.89), (0.12 * sx, -0.27, 0.86)], 0.014, 0.0)
        C.PARTS.append((fin, "head"))
        C.PARTS.append((C.cone("Cheek spike", "back", 0.018, 0.0, 0.05, (0.13 * sx, -0.42, 0.79), (0, sx * 1.2, 0), 5), "head"))
        C.PARTS.append((ball_mesh("Nostril", "mouth", (0.028 * sx, -0.645, 0.838), (0.012, 0.008, 0.008), 8, 4), "head"))
        C.PARTS.append((C.cone("Fang", "horn", 0.011, 0.0, 0.03, (0.04 * sx, -0.60, 0.742), (math.pi, 0, 0), 5), "head"))
    # Lower jaw (rigid on the jaw bone) with a tongue.
    meta = metaball_object("Smolder jaw")
    ball(meta, (0, -0.50, 0.725), 0.085, (0.9, 1.45, 0.42))
    ball(meta, (0, -0.60, 0.73), 0.05, (0.9, 0.9, 0.5))
    jaw = C.mesh_from_meta(meta, "Smolder jaw", voxel=0.006, smooth=4, tris=1500)
    jaw.data.materials.append(M["belly"])
    C.PARTS.append((jaw, "jaw"))
    C.PARTS.append((ball_mesh("Tongue", "tongue", (0, -0.52, 0.745), (0.045, 0.08, 0.015), 12, 6), "jaw"))


def membrane(name, root, edge, rings=4):
    """A wing membrane: a fan from the shoulder to the edge points, in rings so it can bend."""
    root = Vector(root)
    verts = [tuple(root)]
    for k in range(1, rings + 1):
        for p in edge:
            verts.append(tuple(root.lerp(Vector(p), k / rings)))
    n = len(edge)
    faces = []
    for i in range(n - 1):
        faces.append((0, 1 + i, 2 + i))
        for k in range(rings - 1):
            a, b = 1 + k * n + i, 1 + (k + 1) * n + i
            faces.append((a, b, b + 1, a + 1))
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    obj = bpy.data.objects.new(name, data)
    C.scene.collection.objects.link(obj)
    obj.data.materials.append(M["membrane"])
    C.smooth_shade(obj)
    return obj


WING = dict(
    root=(0.09, -0.07, 0.58),
    elbow=(0.25, -0.01, 0.76),
    tip=(0.42, 0.10, 0.74),
    edge=((0.25, -0.01, 0.76), (0.34, 0.04, 0.77), (0.42, 0.10, 0.74), (0.37, 0.11, 0.68), (0.36, 0.15, 0.62), (0.30, 0.13, 0.60), (0.27, 0.16, 0.55), (0.21, 0.12, 0.56), (0.17, 0.11, 0.53), (0.10, 0.03, 0.55)),
)


def mirror(p, sx):
    return Vector((p[0] * sx, p[1], p[2]))


def build_wings():
    for side, sx in (("L", 1), ("R", -1)):
        root, elbow, tip = (mirror(WING[k], sx) for k in ("root", "elbow", "tip"))
        skin = membrane(f"Wing {side}", root, [mirror(p, sx) for p in WING["edge"]])
        arm = (elbow - root).normalized()
        span = (elbow - root).length

        def weights(co, root=root, arm=arm, span=span, side=side):
            t = max(0.0, min(1.0, ((co - root).dot(arm) / span - 0.85) / 0.3))
            return {f"wing.{side}": 1.0 - t, f"wingtip.{side}": t} if t > 0 else {f"wing.{side}": 1.0}

        C.SKINNED.append((skin, weights))
        tube("Wing arm", [root, elbow], 0.022, "skin", f"wing.{side}", taper=[1.0, 0.8])
        tube("Wing finger", [elbow, mirror((0.34, 0.04, 0.775), sx), tip], 0.018, "skin", f"wingtip.{side}", taper=[1.0, 0.7, 0.25])
        tube("Wing finger", [elbow, mirror((0.36, 0.15, 0.62), sx)], 0.012, "back", f"wingtip.{side}", taper=[1.0, 0.35])
        tube("Wing finger", [elbow, mirror((0.27, 0.16, 0.55), sx)], 0.011, "back", f"wing.{side}", taper=[1.0, 0.35])
        tube("Wing finger", [elbow, mirror((0.17, 0.11, 0.53), sx)], 0.01, "back", f"wing.{side}", taper=[1.0, 0.35])
        C.PARTS.append((C.cone("Wing claw", "claw", 0.014, 0.0, 0.04, tuple(elbow + Vector((0, 0, 0.02))), (0, 0, 0), 5), f"wing.{side}"))


def build_spikes(body):
    def spike(name, y, bone, r, depth, tilt):
        top = C.surface(body, (0, y, 1.4), (0, y, 0.0))
        co = top + Vector((0, 0.01, depth * 0.35))
        C.PARTS.append((C.cone(name, "back", r, 0.0, depth, tuple(co), (math.radians(tilt), 0, 0), 6), bone))

    for y, bone in ((-0.27, "neck"), (-0.21, "neck"), (-0.13, "chest"), (-0.02, "spine"), (0.10, "hips"), (0.22, "hips")):
        spike("Back spike", y, bone, 0.034, 0.09, -30)
    for k in range(len(TAIL) - 1):
        mid = TAIL[k].lerp(TAIL[k + 1], 0.5)
        spike("Tail spike", mid.y, f"tail.{k}", 0.03 * (1 - 0.13 * k), 0.085 * (1 - 0.12 * k), -40)
    tip = TAIL[-1]
    C.PARTS.append((C.cone("Tail tip", "back", 0.028, 0.0, 0.11, (0, tip.y + 0.04, tip.z), (-math.pi / 2, 0, 0), 6), "tail.4"))
    for sz in (0.6, -0.6):
        C.PARTS.append((C.cone("Tail tip spike", "back", 0.02, 0.0, 0.075, (-0.02 * (1 if sz > 0 else -1), tip.y + 0.0, tip.z + 0.01), (-math.pi / 2 + 0.25, 0, sz), 6), "tail.4"))
    for prefix, sx, kind in LEGS:
        foot = leg_points(sx, kind)[2]
        for dx in (-0.025, 0.0, 0.025):
            co = (foot.x + dx, foot.y - 0.085 if kind == "front" else foot.y - 0.105, 0.03)
            C.PARTS.append((C.cone("Claw", "claw", 0.011, 0.0, 0.035, co, (math.pi / 2 + 0.3, 0, 0), 5), f"lower.{prefix}"))


def build():
    materials()
    C.HEAD = Vector((0, -0.37, 0.87))
    body = build_body()
    build_head()
    build_wings()
    bones = [
        ("hips", (0, 0.32, 0.40), (0, 0.06, 0.42), None, True),
        ("spine", (0, 0.06, 0.42), (0, -0.12, 0.47), "hips", True),
        ("chest", (0, -0.12, 0.47), (0, -0.20, 0.55), "spine", True),
        ("neck", (0, -0.20, 0.55), (0, -0.30, 0.72), "chest", True),
        ("head", (0, -0.30, 0.72), (0, -0.52, 0.84), "neck", False),
        ("jaw", (0, -0.40, 0.76), (0, -0.60, 0.72), "head", False),
    ]
    for k in range(len(TAIL) - 1):
        bones.append((f"tail.{k}", TAIL[k], TAIL[k + 1], "hips" if k == 0 else f"tail.{k - 1}", True))
    for side, sx in (("L", 1), ("R", -1)):
        root, elbow, tip = (mirror(WING[k], sx) for k in ("root", "elbow", "tip"))
        bones.append((f"wing.{side}", root, elbow, "chest", False))
        bones.append((f"wingtip.{side}", elbow, tip, f"wing.{side}", False))
        C.DEFORM_LATER += [f"wing.{side}", f"wingtip.{side}"]
    legs = []
    for prefix, sx, kind in LEGS:
        hip, knee, foot = leg_points(sx, kind)
        bones.append((f"upper.{prefix}", hip, knee, "chest" if kind == "front" else "hips", True))
        bones.append((f"lower.{prefix}", knee, foot, f"upper.{prefix}", True))
        pole = Vector((knee.x, 0.45 if kind == "front" else -0.35, knee.z))
        legs.append((prefix, f"upper.{prefix}", f"lower.{prefix}", foot, pole))
    build_spikes(body)
    mouth = Matrix.Translation(MOUTH)
    ring = C.torus("FX aura ring", "fire", 0.44, 0.008, (0, 0, 0), (0, 0, 0), (1, 1, 1), 48)
    embers = [ring] + [ball_mesh("FX ember", "core_fire", (0.44 * math.cos(a), 0.44 * math.sin(a), 0.03 * math.sin(3 * a)), (0.025, 0.025, 0.025), 8, 4) for a in (i * math.pi / 4 for i in range(8))]
    shout = C.join([C.torus("FX shout", "flame", 0.12, 0.012, (0, 0, 0), (math.pi / 2, 0, 0)), C.torus("FX shout 2", "flame", 0.2, 0.01, (0, -0.06, 0), (math.pi / 2, 0, 0))], "FX shout")
    sneeze = C.join([C.cone("FX sneeze", "flame", 0.02, 0.26, 0.7, (0, -0.35, 0), (math.pi / 2, 0, 0), 20), C.cone("FX sneeze core", "core_fire", 0.01, 0.1, 0.5, (0, -0.25, 0), (math.pi / 2, 0, 0), 12)], "FX sneeze")
    fx = {
        "fx_glow": (C.fx_orb("ember glow", 0.035, "fire", 0), Matrix.Translation(MOUTH + Vector((0, 0.10, -0.02))), "head"),
        "fx_flash": (C.fx_flash("breath flash", 0.06, "fire", 6), mouth, "head"),
        "fx_ball": (C.fx_bolt("fireball", 0.30, 0.07, "fire", "core_fire"), None, None),
        "fx_ball2": (C.fx_bolt("sneeze ball", 0.2, 0.05, "fire", "core_fire"), None, None),
        "fx_ball3": (C.fx_bolt("sneeze ball 2", 0.2, 0.05, "fire", "core_fire"), None, None),
        "fx_big": (C.fx_bolt("super scorcher", 0.5, 0.13, "fire", "core_fire", 1), None, None),
        "fx_boom": (C.fx_flash("blast", 0.25, "fire", 8), None, None),
        "fx_cone": (sneeze, mouth, "head"),
        "fx_shout": (shout, mouth, "head"),
        "fx_aura": (C.join(embers, "FX dragon practice"), Matrix.Translation((0, 0.05, 0.22)), "root"),
        "fx_mom": (C.fx_bolt("mother flame", 2.4, 0.45, "flame", "core_fire"), None, None),
        "fx_heal": (C.torus("FX mother glow", "heal", 0.42, 0.03, (0, 0, 0), (0, 0, 0), (1, 1, 1), 40), Matrix.Translation((0, 0.05, 0.1)), "root"),
        "fx_puff": (C.fx_orb("puff", 0.04, "fire", 1), None, None),
        "fx_smoke": (C.fx_orb("smoke", 0.05, "smoke", 0), Matrix.Translation((0, -0.64, 0.86)), "head"),
    }
    extra = C.fx_bones(fx, mouth)
    C.SOCKETS["socket_muzzle"] = ("head", mouth)
    C.build_creature_rig("Smolder rig", bones, legs, (), extra)
    C.bind(body)
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips()


FX = ["fx_glow", "fx_flash", "fx_ball", "fx_ball2", "fx_ball3", "fx_big", "fx_boom", "fx_cone", "fx_shout", "fx_aura", "fx_mom", "fx_heal", "fx_puff", "fx_smoke"]


def define_clips():
    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def mouth_at(frame):
        return C.carried("head", frame, MOUTH)

    def jaw(frame, amount):
        rot("jaw", frame, x=OPEN * amount)

    def wings(frame, up=0.0, fold=0.0, sweep=0.0):
        """Raise (up), fold the tips down (fold) and sweep back both wings."""
        for side, sx in (("L", 1), ("R", -1)):
            rot(f"wing.{side}", frame, y=-sx * up, z=sx * sweep)
            rot(f"wingtip.{side}", frame, y=sx * fold)

    def tail(frame, amp=0.0, phase=0.0, lift=6.0, base=0.0):
        """Sway the tail (a wave travelling to the tip) and curl it up."""
        for k in range(len(TAIL) - 1):
            rot(f"tail.{k}", frame, x=lift + (base if k == 0 else 0.0), z=amp * math.sin(phase - 0.8 * k) * (0.6 + 0.2 * k))

    def stance(frame, breath=0.0, look=0.0, sway=0.0):
        loc("root", frame)
        rot("root", frame)
        loc("hips", frame, z=-0.008 * breath)
        rot("hips", frame, z=2 * sway)
        rot("spine", frame, x=-1.0 * breath)
        rot("chest", frame, x=-1.5 * breath, z=-2 * sway)
        rot("neck", frame, x=-3 * breath, z=4 * look)
        rot("head", frame, x=2 * breath, y=-4 * look, z=10 * look)
        jaw(frame, 0.05)
        for prefix, sx, kind in LEGS:
            loc(f"ik_{prefix}", frame)
            rot(f"ik_{prefix}", frame)
        wings(frame, up=4 * breath)
        tail(frame, 6 * sway)

    def sit(frame, breath=0.0, look=0.0):
        """Settled back on the haunches like a cat, chest up."""
        stance(frame, breath, look)
        loc("hips", frame, y=0.03, z=-0.10)
        rot("hips", frame, x=-18)
        rot("chest", frame, x=-8 - 1.5 * breath)
        rot("neck", frame, x=-6 - 3 * breath, z=4 * look)

    def start(frame=0):
        stance(frame)
        fx_off(frame)
        C.leg_ik(frame, 1.0)

    def pulse(name, keys):
        for f, s_ in keys:
            size(name, f, s_)

    @clip("Idle", 48, loop=True)
    def idle():
        for f in range(0, 49, 6):
            p = 2 * math.pi * f / 48
            stance(f, breath=0.5 - 0.5 * math.cos(2 * p), look=0.6 * math.sin(p), sway=0.5 * math.sin(p))
            tail(f, 10, 2 * p)
        fx_off(0)

    @clip("Walk", 20, loop=True)
    def trot():
        # Trot: diagonal pairs (front left with hind right) swing together.
        for f in range(0, 21, 2):
            p = 2 * math.pi * f / 20
            stance(f, breath=0.2 * math.sin(2 * p), sway=0.4 * math.sin(p))
            loc("hips", f, z=0.015 * math.cos(2 * p))
            rot("neck", f, x=3 * math.sin(2 * p + 0.6))
            wings(f, up=-6 + 3 * math.sin(2 * p), sweep=6)
            tail(f, 12, p)
            for prefix, sx, kind in LEGS:
                q = p + (0 if prefix in TROT_A else math.pi)
                loc(f"ik_{prefix}", f, y=-0.10 * math.sin(q), z=max(0.0, math.cos(q)) * 0.07)
        fx_off(0)

    @clip("AA", 22)
    def attack():
        start()
        rot("neck", 6, x=-14)
        rot("head", 6, x=-12)
        rot("chest", 6, x=-5)
        jaw(6, 0.4)
        pulse("fx_glow", ((4, 0.0), (7, 1.2), (10, 0.0)))
        rot("neck", 10, x=10)
        rot("head", 10, x=8)
        rot("chest", 10, x=4)
        jaw(10, 1.0)
        pulse("fx_flash", ((9, 0.0), (10, 1.2), (13, 0.0)))
        C.shoot_from("fx_ball", 10, 17, lambda: mouth_at(10), (0, -1, -0.04), 3.5)
        jaw(15, 0.2)
        tail(12, 14, 1.5, lift=9)
        stance(22)

    @clip("P", 40)
    def dragon_practice():
        start()
        # A proud stack: he gathers himself, then puffs up in an aura of embers.
        loc("hips", 8, z=-0.04)
        rot("neck", 8, x=8)
        rot("head", 8, x=6)
        wings(8, up=-10)
        size("chest", 16, 1.08)
        size("chest", 30, 1.08)
        size("chest", 34, 1.0)
        loc("hips", 16, z=0.01)
        rot("neck", 16, x=-22)
        rot("head", 16, x=-10)
        jaw(16, 0.35)
        wings(16, up=38, sweep=-10)
        wings(30, up=30, sweep=-8)
        tail(16, 8, 0.0, lift=12)
        pulse("fx_glow", ((14, 0.0), (17, 1.0), (24, 0.0)))
        pulse("fx_aura", ((12, 0.0), (16, 1.0), (34, 1.0), (38, 0.0)))
        for f in range(12, 39, 2):
            rot("fx_aura", f, z=8 * (f - 12))
        stance(40)

    @clip("Q", 30)
    def super_scorcher_breath():
        start()
        # A deep breath (chest swells, fire gathers in the maw), then a big fireball.
        size("chest", 8, 1.07)
        size("chest", 12, 1.0)
        loc("hips", 8, z=-0.03)
        rot("neck", 8, x=-20)
        rot("head", 8, x=-15)
        jaw(8, 0.3)
        wings(8, up=22)
        tail(8, 0, 0, lift=11)
        pulse("fx_glow", ((2, 0.0), (9, 1.2), (12, 0.0)))
        rot("neck", 11, x=12)
        rot("head", 11, x=10)
        jaw(11, 1.2)
        loc("hips", 11, y=0.04)
        wings(11, up=-15, sweep=10)
        pulse("fx_flash", ((10, 0.0), (11, 1.6), (15, 0.0)))
        C.shoot_from("fx_big", 11, 19, lambda: mouth_at(11), (0, -1, -0.03), 4.5)
        C.later(lambda: C.put("fx_boom", 20, mouth_at(11) + Vector((0, -4.5, -0.25))))
        pulse("fx_boom", ((19, 0.0), (20, 1.2), (24, 1.6), (27, 0.0)))
        jaw(18, 0.3)
        rot("neck", 18, x=2)
        stance(30)

    @clip("W", 32)
    def achoo():
        start()
        # "Ah... ah..." (head rears, nostrils glow) then a sneeze of fire that jolts him back.
        rot("neck", 6, x=-12)
        rot("head", 6, x=-14)
        jaw(6, 0.3)
        rot("neck", 9, x=-6)
        rot("head", 9, x=-6)
        jaw(9, 0.15)
        rot("neck", 14, x=-24)
        rot("head", 14, x=-22)
        rot("chest", 14, x=-6)
        jaw(14, 0.6)
        wings(14, up=15)
        pulse("fx_glow", ((4, 0.0), (6, 0.6), (9, 0.3), (14, 1.0), (16, 0.0)))
        rot("neck", 17, x=8)
        rot("head", 17, x=4)
        rot("chest", 17, x=6)
        jaw(17, 0.9)
        loc("hips", 17, y=0.07)
        wings(17, up=40, sweep=-15)
        tail(17, 0, 0, lift=12)
        pulse("fx_flash", ((16, 0.0), (17, 1.4), (20, 0.0)))
        pulse("fx_cone", ((16, 0.0), (17, 1.0), (20, 1.25), (23, 0.0)))
        for name, d in (("fx_ball", (0, -1, -0.05)), ("fx_ball2", (0.35, -1, -0.05)), ("fx_ball3", (-0.35, -1, -0.05))):
            C.shoot_from(name, 17, 24, lambda: mouth_at(17), d, 2.8)
        jaw(21, 0.2)
        for f, z in ((22, 12), (25, -12), (28, 6)):
            rot("head", f, z=z)
            rot("neck", f, x=2)
        stance(32)

    @clip("E", 48)
    def flap_flap_flap():
        start()
        # Hops up and flies forward on frantic little wingbeats, then lands.
        loc("hips", 5, z=-0.08)
        rot("neck", 5, x=8)
        wings(5, up=30)
        for prefix, sx, kind in LEGS:
            loc(f"ik_{prefix}", 5)
        loc("root", 5)
        moving = bool(C.OPTIONS.get("root_motion"))
        reach = -1.6 if moving else 0.0
        for f in range(9, 39):
            t = (f - 9) / 29
            rise = math.sin(0.5 * math.pi * min(1.0, t / 0.3))
            fall = min(1.0, (1 - t) / 0.25)
            loc("root", f, y=(-0.15 + (reach + 0.15) * t) if moving else 0.0, z=(0.5 + 0.04 * math.sin(2 * math.pi * (f - 9) / 5)) * rise * fall)
        for k, f in enumerate(range(9, 39, 5)):
            wings(f, up=-38, fold=-10, sweep=-5)
            wings(f + 2, up=46, fold=15, sweep=5)
            tail(f, 10, k * 1.4, lift=3)
            rot("hips", f, x=12)
            rot("neck", f, x=-12)
            rot("head", f, x=-4)
            loc("hips", f, z=0.0)
            for prefix, sx, kind in LEGS:
                tuck = (0.0, 0.08, 0.12) if kind == "front" else (0.0, 0.12, 0.08)
                loc(f"ik_{prefix}", f, *tuck)
        for prefix, sx, kind in LEGS:
            loc(f"ik_{prefix}", 38)
        wings(39, up=30, sweep=-5)
        loc("hips", 41, z=-0.07)
        rot("hips", 41, x=-3)
        rot("neck", 41, x=6)
        wings(44, up=8)
        stance(48)
        loc("root", 48, y=reach)

    @clip("R", 60)
    def mmooommmm():
        start()
        # He sits up and calls for his mother; her flame sweeps in over his head.
        sit(8)
        rot("neck", 8, x=-26)
        rot("head", 8, x=-24)
        jaw(8, 1.1)
        wings(8, up=25, sweep=-10)
        pulse("fx_shout", ((8, 0.0), (10, 0.6), (17, 1.8), (19, 0.0), (20, 0.0), (22, 0.6), (28, 1.8), (30, 0.0)))
        sit(24)
        rot("neck", 24, x=-30)
        rot("head", 24, x=-32, z=8)
        jaw(24, 0.6)
        wings(24, up=30, sweep=-10)
        pulse("fx_mom", ((23, 0.0), (24, 1.0), (40, 1.0), (41, 0.0)))
        C.fly_path("fx_mom", [(24, (0, 3.5, 3.0)), (32, (0, -0.5, 1.9)), (40, (0, -5.0, 0.9))])
        C.later(lambda: C.put("fx_boom", 41, Vector((0, -5.0, 0.3))))
        pulse("fx_boom", ((40, 0.0), (41, 2.0), (45, 2.6), (48, 0.0)))
        for k, f in enumerate(range(30, 48, 4)):
            sit(f, look=0.4 * (-1) ** k)
            rot("neck", f, x=-12)
            jaw(f, 0.7)
            wings(f, up=45 if k % 2 == 0 else -5, sweep=-8)
            tail(f, 16, k * 1.6, lift=10, base=18)
        pulse("fx_heal", ((34, 0.0), (36, 1.0), (48, 1.15), (52, 0.0)))
        loc("fx_heal", 36)
        loc("fx_heal", 52, z=0.5)
        sit(52)
        tail(52, 0, 0, lift=8, base=18)
        stance(60)

    @clip("Recall", 48, loop=True)
    def recall():
        # Sits happily, wagging, and blows little smoke rings of flame up into the air.
        for f in range(0, 49, 6):
            p = 2 * math.pi * f / 48
            sit(f, breath=0.5 - 0.5 * math.cos(2 * p), look=0.5 * math.sin(p))
            rot("head", f, x=-8, y=-6 * math.sin(p), z=6 * math.sin(p))
            tail(f, 14, 2 * p, lift=8, base=18)
            wings(f, up=6 + 6 * math.sin(2 * p))
        for f0 in (10, 34):
            jaw(f0 - 2, 0.05)
            jaw(f0, 0.5)
            jaw(f0 + 4, 0.05)
            pulse("fx_puff", ((f0 - 1, 0.0), (f0, 0.8), (f0 + 10, 1.4), (f0 + 12, 0.0)))
            C.fly_path("fx_puff", [(f0, lambda f0=f0: mouth_at(f0)), (f0 + 12, lambda f0=f0: mouth_at(f0) + Vector((0, -0.1, 0.6)))], (0, 0, 1), 0.04)
        fx_off(0)
        fx_off(48)

    @clip("Death", 44)
    def death():
        start()
        # Staggers, wobbles and flops onto his belly; a last puff of smoke.
        loc("hips", 6, y=0.05)
        rot("neck", 6, x=-15)
        rot("head", 6, x=-10, z=10)
        jaw(6, 0.5)
        wings(6, up=30)
        loc("hips", 12, z=-0.05)
        rot("hips", 12, z=8)
        rot("head", 12, z=-15)

        def dead(frame, bounce=0.0):
            loc("hips", frame, z=-0.22 + bounce)
            rot("hips", frame, x=4)
            rot("chest", frame, x=6)
            rot("neck", frame, x=22 - 40 * bounce)
            rot("head", frame, x=16, z=5)
            jaw(frame, 0.3)
            wings(frame, up=-28, sweep=10)
            tail(frame, 0, 0, lift=-2)
            for prefix, sx, kind in LEGS:
                loc(f"ik_{prefix}", frame, x=0.10 * sx, y=-0.10 if kind == "front" else 0.12)

        dead(20)
        dead(24, 0.03)
        dead(27)
        pulse("fx_smoke", ((31, 0.0), (33, 1.0), (42, 1.6), (44, 0.0)))
        loc("fx_smoke", 33)
        loc("fx_smoke", 44, z=0.25)
        dead(44)
