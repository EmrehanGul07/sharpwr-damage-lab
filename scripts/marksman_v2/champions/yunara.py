"""Yunara: an original stylized interpretation (ivory and teal ceremonial robes, black flowing
hair, golden headdress, orbiting prayer beads; she drifts just above the ground)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, fk_arm, flash, lathe, loc, material, metaball_object, rot, size, torus

S = 1.03
RIM = (0.55, 1.0, 0.85)
EXPOSURE = -0.15
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55), "R": dict(angle_deg=28, distance=3.9, height=1.6, target_z=1.2)}
BEADS = 9


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#d9b9a5", rough=0.5, sss=0.2),
        ivory=material("Ivory robe", "#eee5d0", rough=0.65),
        teal=material("Teal", "#244f51", rough=0.55),
        jade=material("Jade", "#357e76", rough=0.45),
        gold=material("Gold", "#c8a462", rough=0.28, metal=1.0),
        hair=material("Black hair", (0.012, 0.012, 0.014), rough=0.45),
        hair_dark=material("Blue-black hair", (0.008, 0.01, 0.018), rough=0.5),
        bead=material("Prayer bead", (0.35, 0.85, 0.7), rough=0.15, emission=1.5),
        spirit=material("Spirit", "#a2ffe4", emission=7.0),
    )
    C.face_materials(iris=(0.25, 0.55, 0.45), lash=(0.01, 0.01, 0.012), lip=(0.6, 0.3, 0.32))


def build_body():
    meta = metaball_object("Yunara body")
    C.torso_female(meta, S, bust=0.95, hips=0.98, waist=0.92)
    C.limbs(meta, dict(thigh=(0.062, 0.040), calf=(0.040, 0.045, 0.029), arm=(0.042, 0.031), forearm=(0.034, 0.026), palm=0.032), hands="mitten")
    for side in ("L", "R"):
        toe = C.J[f"toe.{side}"]
        ball(meta, toe + Vector((0, 0.01, 0.004)), 0.032 * S, (0.9, 1.25, 0.7))
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.95, 1.02, 1.40)]
    v = Vector((1, 0, -0.35)).normalized()
    cuts += [(B(0.0, 0, 1.02), v), (B(0.0, 0, 1.02), Vector((-v.x, 0, v.z)))]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.78,)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            return "skin" if C.arm_fraction(c, side) > 0.78 else "ivory"
        if 0.95 < z < 1.02:
            return "teal"  # sash
        if z > 1.40 and math.hypot(x, y - 0.01) < 0.065:
            return "skin"
        if y < 0 and z > 1.02 and abs(x) < (z - 1.02) * 0.35:
            return "jade"  # crossed collar
        return "ivory"

    return C.body_mesh(meta, "Yunara body", region, ["skin", "ivory", "teal", "jade"], cuts)


def build_robes():
    # Long robe panels all round (spring chains) and wide sleeves hanging from the forearms.
    panels = C.coat_panels(
        [
            ("front", 0.0, -0.11, 0.16, 0.97, 0.10, 0.0),
            ("back", 0.0, 0.11, 0.17, 0.97, 0.10, 0.0),
            ("side.L", 0.12, 0.0, 0.13, 0.97, 0.12, 0.06),
            ("side.R", -0.12, 0.0, 0.13, 0.97, 0.12, 0.06),
        ],
        "ivory",
        S,
    )
    sleeves = {}
    for side in ("L", "R"):
        el, wr = C.J[f"elbow.{side}"], C.J[f"wrist.{side}"]
        top = el.lerp(wr, 0.2)
        pts = [top, top + Vector((0, 0.03, -0.12)), top + Vector((0, 0.05, -0.24))]
        sleeves[side] = (pts, C.ribbon("Sleeve", pts, 0.12, "jade", (0, 1, 0), 0.006, [1.0, 1.2, 1.3], bone=False))
    sash = C.ribbon("Sash tail", [B(0.05, -0.10, 0.98), B(0.07, -0.12, 0.80), B(0.08, -0.12, 0.62)], 0.05 * S, "teal", (1, 0, 0), 0.004, bone=False)
    belt = [torus("Sash knot", "gold", 0.02, 0.006, B(0.05, -0.105, 0.985), (math.pi / 2, 0, 0), (1, 1, 1), 16)]
    for o in belt:
        C.PARTS.append((o, "hips"))
    return panels, sleeves, sash


def build_head():
    C.build_head("Yunara head", jaw=0.95, chin=0.97, nose=0.92)
    C.build_face(eye_size=0.95, lashes="winged", brow_mat="hair", brow_width=0.0018, brow_angle=0.02, mouth="flat", mouth_size=0.0018)
    h = C.HEAD
    C.hair_cap("Yunara hair", "hair", front_y=0.045, front_z=0.05, scale=1.04)
    meta = metaball_object("Yunara front hair", resolution=0.004)
    for sx in (1, -1):
        C.clump(meta, [h + Vector((0.06 * sx, -0.08, 0.09)), h + Vector((0.095 * sx, -0.07, 0.0)), h + Vector((0.10 * sx, -0.05, -0.12)), h + Vector((0.10 * sx, -0.03, -0.24))], 0.018, 0.006, flat=0.6)
    front = C.mesh_from_meta(meta, "Yunara front hair", voxel=0.0035, smooth=3, tris=2500)
    front.data.materials.append(M["hair"])
    C.PARTS.append((front, "head"))
    backs = {}
    for side, sx in (("L", 1), ("R", -1)):
        path = [h + Vector((0.05 * sx, 0.10, -0.02)), B(0.07 * sx, 0.14, 1.36), B(0.08 * sx, 0.15, 1.14), B(0.085 * sx, 0.14, 0.92)]
        sheet = metaball_object(f"Yunara long hair {side}", resolution=0.005)
        C.clump(sheet, path, 0.05, 0.025, flat=0.55)
        backs[side] = (path, C.mesh_from_meta(sheet, f"Yunara long hair {side}", voxel=0.0045, smooth=3, tris=2200))
        backs[side][1].data.materials.append(M["hair"])
    # Golden headdress: a circlet with tall arches and hanging tassels.
    parts = [C.torus("Headdress band", "gold", 0.105, 0.006, h + Vector((0, 0.005, 0.06)), (math.radians(-12), 0, 0), (1.0, 1.08, 1.0), 40)]
    for k, a in enumerate((-40, -20, 0, 20, 40)):
        r = math.radians(a)
        base = h + Vector((math.sin(r) * 0.1, -math.cos(r) * 0.1 + 0.005, 0.075))
        tall = 0.09 if a == 0 else 0.06 - 0.01 * abs(k - 2)
        parts.append(C.plate("Headdress arch", "gold", [(0, 0, 0), (0.018, 0, tall * 0.6), (0, 0, tall), (-0.018, 0, tall * 0.6)], 0.004, 0.0))
        C.place(parts[-1], Matrix.Translation(base) @ Matrix.Rotation(-r, 4, "Z"))
    parts.append(ball_mesh("Headdress jewel", "spirit", h + Vector((0, -0.108, 0.10)), (0.012, 0.008, 0.016), 12, 6))
    for sx in (1, -1):
        parts.append(C.tube("Tassel", [h + Vector((0.095 * sx, -0.04, 0.05)), h + Vector((0.10 * sx, -0.045, -0.02)), h + Vector((0.098 * sx, -0.04, -0.08))], 0.003, "gold", False))
        parts.append(ball_mesh("Tassel bead", "spirit", h + Vector((0.098 * sx, -0.04, -0.085)), (0.008, 0.008, 0.008), 10, 6))
    for o in parts:
        C.PARTS.append((o, "head"))
    return backs


def build():
    C.make_joints(scale=S, shoulder_x=0.176, hip_x=0.093)
    materials()
    body = build_body()
    panels, sleeves, sash = build_robes()
    backs = build_head()
    C.scale_parts("head", 1.06, C.J["head_bone"])
    # Prayer beads: a ring around her waist that spins; one bead is cast as a spirit orb.
    ring = [ball_mesh(f"Bead {k}", "bead", (math.cos(k * 2 * math.pi / BEADS) * 0.38, math.sin(k * 2 * math.pi / BEADS) * 0.38, 0.0), (0.035, 0.035, 0.035), 16, 8) for k in range(BEADS)]
    ring.append(C.torus("Bead cord", "gold", 0.38, 0.004, (0, 0, 0), (0, 0, 0), (1, 1, 1), 48))
    beads = C.join(ring, "Prayer beads")
    BEAD_RING = Matrix.Translation(B(0, 0, 1.05))
    C.place(beads, BEAD_RING @ Matrix.Rotation(math.radians(8), 4, "X"))
    fx = {
        "fx_orb": (C.fx_orb("spirit orb", 0.05, "spirit", 2), None, None),
        "fx_orb2": (C.fx_orb("spirit orb 2", 0.05, "spirit", 2), None, None),
        "fx_wave": (C.join([C.ribbon("FX spirit wave", [Vector((-0.5, 0, 0)), Vector((0, -0.25, 0.05)), Vector((0.5, 0, 0))], 0.15, "spirit", (0, 0, 1), 0.0, bone=False)], "FX spirit wave"), None, None),
        "fx_halo": (C.join([C.torus("FX transcend", "spirit", 0.5 + 0.12 * k, 0.01, (0, 0, 0.04 * k), (0, 0, 0), (1, 1, 1), 40) for k in range(3)], "FX transcend"), Matrix.Translation(B(0, 0, 1.95)), "root"),
        "fx_blink": (C.fx_flash("spirit step", 0.12, "spirit", 8), None, None),
        "fx_palm": (C.fx_orb("palm light", 0.035, "spirit", 1), None, "hand.R"),
    }
    wr, hd = C.J["wrist.R"], C.J["hand.R"]
    palm = Matrix.Translation(wr.lerp(hd, 0.6) - C.hand_normal("R") * 0.03)
    fx["fx_palm"] = (fx["fx_palm"][0], palm, "hand.R")
    extra = [("beads", BEAD_RING.translation, BEAD_RING.translation + Vector((0, 0.1, 0)), "hips")]
    extra += C.fx_bones(fx, Matrix.Translation(B(-0.2, -0.4, 1.15)))
    chains = C.coat_chains(panels, stiffness=45, gain=1.0, sway=3.0, limit=(40, 25))
    for side, (pts, ribbon) in sleeves.items():
        chains.append((f"sleeve.{side}", C.resample(pts, 2), f"forearm.{side}", dict(skin=True, stiffness=45, gain=1.0, sway=3.0, limit=(45, 30))))
        C.SKINNED.append((ribbon, [f"forearm.{side}", f"sleeve.{side}.0", f"sleeve.{side}.1"]))
    C.SKINNED.append((sash, ["hips"]))
    for side, (path, mesh) in backs.items():
        chains.append((f"hair.{side}", C.resample(path, 3), "head", dict(skin=True, stiffness=45, gain=1.1, sway=3.5, limit=(45, 30))))
        C.SKINNED.append((mesh, ["head"] + [f"hair.{side}.{i}" for i in range(3)]))
    C.SOCKETS["socket_muzzle"] = ("hand.R", palm)
    C.build_rig("Yunara rig", chains, extra)
    C.bind(body)
    C.attach(beads, "beads")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips(palm)


FX = ["fx_orb", "fx_orb2", "fx_wave", "fx_halo", "fx_blink", "fx_palm"]


def define_clips(palm):
    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def palm_at(frame):
        return C.carried("hand.R", frame, palm.translation)

    def spin_beads(f0, f1, degrees_per_frame=6.0):
        for f in range(f0, f1 + 1, 4):
            rot("beads", f, z=degrees_per_frame * (f - f0))

    def stance(frame, breath=0.0, sway=0.0):
        """Serene float: hovering a hand's breadth up, toes pointed, palms open."""
        loc("root", frame, z=0.07 + 0.02 * breath)
        rot("root", frame)
        loc("hips", frame, x=0.005 * sway, z=-0.01)
        rot("spine", frame, x=1 + breath)
        rot("chest", frame, x=-2 + 1.2 * breath, z=sway)
        rot("head", frame, x=-2 + breath, z=-4 + 3 * sway)
        for side in ("L", "R"):
            sx = C.side_x(side)
            loc(f"ik_foot.{side}", frame, x=0.01 * sx, y=0.02 if side == "L" else 0.05, z=0.02)
            rot(f"ik_foot.{side}", frame, x=-35, z=-8 * sx)
            fk_arm(side, frame, up=22 + 2 * breath, swing=-25, bend=55, out=4, twist=25, hand=-25)

    def cast(frame, name, distance=3.6):
        fk_arm("R", frame - 3, up=30, swing=10, bend=100, out=-5, twist=30, hand=10)
        fk_arm("R", frame, up=6, swing=-86, bend=8, out=-6, hand=-60)
        rot("chest", frame - 3, z=10)
        rot("chest", frame, z=-10)
        size("fx_palm", frame - 2, 0.0)
        size("fx_palm", frame, 1.3)
        size("fx_palm", frame + 3, 0.0)
        C.shoot_from(name, frame, frame + 6, lambda: palm_at(frame), (0, -1, 0), distance)

    def start(frame=0):
        stance(frame)
        fx_off(frame)

    @clip("Idle", 72, loop=True)
    def idle():
        for f, breath, sway in ((0, 0, 0), (18, 1, 0.5), (36, 0, 1), (54, 1, 0.5), (72, 0, 0)):
            stance(f, breath, sway)
        fx_off(0)
        spin_beads(0, 72, 5.0)

    @clip("Walk", 24, loop=True)
    def glide():
        # She glides rather than runs: a forward lean, robes trailing, a gentle bob.
        for f, bob in ((0, 0.0), (6, 1.0), (12, 0.0), (18, 1.0), (24, 0.0)):
            stance(f, breath=bob, sway=0.0)
            loc("root", f, z=0.10 + 0.03 * bob)
            rot("spine", f, x=10)
            rot("chest", f, x=4)
            for side in ("L", "R"):
                fk_arm(side, f, up=20, swing=30, bend=30, out=6, twist=10, hand=-10)
                loc(f"ik_foot.{side}", f, x=0.01 * C.side_x(side), y=0.10 if side == "L" else 0.16, z=0.06)
                rot(f"ik_foot.{side}", f, x=-55)
        spin_beads(0, 24, 8.0)
        fx_off(0)

    @clip("AA", 20)
    def attack():
        start()
        cast(6, "fx_orb")
        spin_beads(0, 20, 8.0)
        stance(20)

    @clip("P", 30)
    def transcendent_state():
        start()
        # The beads whirl faster and brighten.
        spin_beads(0, 30, 18.0)
        size("beads", 6, 1.0)
        size("beads", 12, 1.15)
        size("beads", 24, 1.0)
        rot("head", 10, x=-8)
        stance(30)

    @clip("Q", 32)
    def cultivation_of_spirit():
        start()
        # Palms together in prayer, the bead ring swells, then two quick orbs.
        for side in ("L", "R"):
            fk_arm(side, 6, up=30, swing=-60, bend=120, out=-35, twist=30, hand=-10)
        rot("head", 6, x=10)
        size("beads", 4, 1.0)
        size("beads", 10, 1.3)
        size("beads", 24, 1.0)
        spin_beads(0, 32, 14.0)
        cast(16, "fx_orb")
        cast(22, "fx_orb2")
        stance(32)

    @clip("W", 30)
    def spirit_wave():
        start()
        # A sweeping arm sends a crescent of spirit light forward.
        fk_arm("R", 5, up=70, swing=20, bend=40, out=40, hand=-10)
        rot("chest", 5, z=20)
        fk_arm("R", 10, up=50, swing=-80, bend=10, out=-40, hand=-20)
        rot("chest", 10, z=-20)
        C.shoot_from("fx_wave", 10, 18, lambda: C.carried("chest", 10, B(0, -0.4, 1.15)), (0, -1, 0), 3.5)
        spin_beads(0, 30, 8.0)
        stance(30)

    @clip("E", 26)
    def spirit_step():
        start()
        moving = bool(C.OPTIONS.get("root_motion"))
        reach = -1.4 if moving else 0.0
        # She folds into light and reappears ahead.
        size("root", 4, 1.0)
        size("root", 7, 0.0)
        C.put("fx_blink", 5, B(0, 0, 1.0))
        size("fx_blink", 4, 0.0)
        size("fx_blink", 6, 1.2)
        size("fx_blink", 10, 0.0)
        size("root", 10, 0.0)
        size("root", 13, 1.0)
        loc("root", 7, z=0.07)
        loc("root", 10, y=reach, z=0.07)
        stance(26)
        loc("root", 26, y=reach, z=0.07)
        loc("root", 13, y=reach, z=0.07)

    @clip("R", 56)
    def ascension():
        start()
        # She rises, arms opening, a triple halo crowns her; the beads blaze.
        loc("root", 14, z=0.40)
        for side in ("L", "R"):
            fk_arm(side, 14, up=100, swing=-10, bend=20, out=10, hand=10)
        rot("chest", 14, x=-10)
        rot("head", 14, x=-14)
        size("fx_halo", 10, 0.0)
        size("fx_halo", 16, 1.0)
        for f in range(16, 41, 4):
            rot("fx_halo", f, z=20 * (f - 16))
        size("fx_halo", 40, 1.0)
        size("fx_halo", 44, 0.0)
        size("beads", 12, 1.0)
        size("beads", 18, 1.4)
        size("beads", 40, 1.4)
        size("beads", 46, 1.0)
        spin_beads(0, 56, 14.0)
        loc("root", 40, z=0.40)
        stance(56)

    @clip("Recall", 48, loop=True)
    def recall():
        # Meditation: legs folded, palms resting, beads slowly turning.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.0)
            loc("root", f, z=0.25 + 0.02 * abs(s_))
            loc("hips", f, z=-0.18)
            for side in ("L", "R"):
                sx = C.side_x(side)
                loc(f"ik_foot.{side}", f, x=-0.05 * sx, y=-0.10, z=0.22)
                rot(f"ik_foot.{side}", f, x=-20, z=-60 * sx)
                fk_arm(side, f, up=10, swing=-40, bend=80, out=-10, twist=20, hand=-20)
            rot("head", f, x=8)
        spin_beads(0, 48, 7.5)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        loc("root", 4, z=0.07)
        loc("root", 10)
        C.fall_back(0, S)
