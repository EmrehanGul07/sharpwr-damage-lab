"""Twitch: an original stylized interpretation (hunched rat marksman with a long snout, pink ears,
an articulated tail, a ragged hood and a chem crossbow)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, cyl, fk_arm, flash, ik, lathe, loc, material, metaball_object, placement, rot, size, torus, tube, weapon_matrix

S = 0.98
RIM = (0.7, 1.0, 0.3)
EXPOSURE = -0.1
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Grey fur", "#9f9a79", rough=0.8),
        fur_dark=material("Dark fur", (0.20, 0.19, 0.14), rough=0.85),
        pink=material("Pink skin", (0.75, 0.35, 0.38), rough=0.5, sss=0.2),
        cloth=material("Rags", "#28312b", rough=0.8),
        olive=material("Olive", "#687339", rough=0.7),
        tan=material("Tan", "#a28f68", rough=0.7),
        metal=material("Rusty metal", "#625a49", rough=0.45, metal=0.7),
        wood=material("Crossbow wood", (0.12, 0.07, 0.035), rough=0.55),
        tooth=material("Teeth", (0.85, 0.75, 0.45), rough=0.4),
        toxic=material("Toxic", "#baff4e", emission=6.0),
        cloud=material("Venom cloud", (0.5, 0.9, 0.2), emission=1.5, alpha=0.5),
    )
    C.face_materials(iris=(0.9, 0.85, 0.1), lash=(0.01, 0.01, 0.01), lip=(0.3, 0.2, 0.2))
    M["iris"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.5


def build_body():
    meta = metaball_object("Twitch body")
    C.torso_male(meta, S, chest=0.92, waist=0.85, shoulders=0.9)
    C.limbs(meta, dict(neck=(0.045, 0.04), thigh=(0.06, 0.04), calf=(0.04, 0.045, 0.026), foot=(0.042, 0.03), arm=(0.04, 0.03), forearm=(0.032, 0.024), palm=0.03), hands="mitten")
    for side in ("L", "R"):
        toe = C.J[f"toe.{side}"]
        for k in (-1, 0, 1):  # clawed toes
            ball(meta, toe + Vector((0.018 * k, -0.03, -0.005)), 0.014 * S, (0.8, 1.6, 0.6))
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.30, 0.86, 1.30)]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.55, 0.80)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            f = C.arm_fraction(c, side)
            return "pink" if f > 0.80 else "skin" if f > 0.55 else "cloth"
        if z < 0.30:
            return "pink" if z < 0.06 else "skin"
        if z < 0.86:
            return "olive"
        if z > 1.30:
            return "skin"
        return "cloth"

    return C.body_mesh(meta, "Twitch body", region, ["skin", "pink", "cloth", "olive"], cuts)


def build_head():
    def snout(meta, h):
        C.chain(meta, h + Vector((0, -0.04, -0.03)), h + Vector((0, -0.16, -0.06)), 0.055, 0.022)  # long snout
        ball(meta, h + Vector((0, 0.02, 0.03)), 0.085, (0.95, 1.15, 0.95))  # elongated skull

    head = C.build_head("Twitch head", jaw=0.85, chin=0.7, cheek=0.9, nose=0.5, ears=0.0, extra=snout)
    h = C.HEAD
    C.build_face(eye_size=0.75, lashes="none", brow_mat="fur_dark", brow_width=0.002, brow_angle=0.2, mouth="flat", mouth_size=0.0015, eye_gap=1.05)
    C.PARTS.append((ball_mesh("Rat nose", "pink", h + Vector((0, -0.185, -0.055)), (0.018, 0.014, 0.014), 12, 6), "head"))
    for sx in (1, -1):
        ear = lathe("Ear", "pink", [(0.0, 0.0), (0.05, 0.004), (0.055, 0.012), (0.05, 0.02), (0.0, 0.012)], 20, "Z")
        rim = C.torus("Ear rim", "skin", 0.053, 0.008, (0, 0, 0.01), (0, 0, 0), (1, 1, 1), 20)
        both = C.join([ear, rim], "Rat ear")
        C.place(both, Matrix.Translation(h + Vector((0.075 * sx, 0.03, 0.10))) @ Matrix.Rotation(math.radians(70), 4, "X") @ Matrix.Rotation(math.radians(-30 * sx), 4, "Y"))
        C.PARTS.append((both, "head"))
        for k in range(3):  # whiskers
            w = tube("Whisker", [h + Vector((0.02 * sx, -0.17, -0.06)), h + Vector((0.08 * sx, -0.16 + 0.01 * k, -0.06 + 0.01 * (k - 1))), h + Vector((0.13 * sx, -0.14 + 0.02 * k, -0.07 + 0.02 * (k - 1)))], 0.0012, "tan", False)
            C.PARTS.append((w, "head"))
    for sx in (1, -1):
        C.PARTS.append((box("Tooth", "tooth", (0.008, 0.004, 0.016), h + Vector((0.005 * sx, -0.17, -0.085)), 0.001), "head"))
    # Ragged hood over the skull, the snout poking out.
    meta = metaball_object("Hood", resolution=0.006)
    ball(meta, h + Vector((0, 0.04, 0.04)), 0.12, (1.0, 1.1, 1.0))
    ball(meta, h + Vector((0, 0.09, -0.08)), 0.10, (1.2, 0.9, 1.2))
    hood = C.mesh_from_meta(meta, "Hood", voxel=0.006, smooth=3, tris=3000)
    C.delete_faces(hood, lambda c: (c.y < h.y - 0.0 and c.z < h.z + 0.08) or c.z < h.z - 0.17 or (abs(c.x) > 0.06 and abs(c.x) < 0.11 and c.z > h.z + 0.06))
    C.solidify(hood, 0.007)
    hood.data.materials.append(M["cloth"])
    C.PARTS.append((hood, "head"))
    return head


def build_crossbow():
    """The chem crossbow: grip at the origin, bolt toward -Y, limbs across X, vials on the stock."""
    parts = [
        box("Stock", "wood", (0.04, 0.42, 0.05), (0, 0.02, 0.0), 0.01),
        box("Grip", "wood", (0.03, 0.04, 0.10), (0, 0.06, -0.06), 0.008, (math.radians(-15), 0, 0)),
        box("Rail", "metal", (0.016, 0.30, 0.012), (0, -0.10, 0.03), 0.003),
        tube("Limbs", [Vector((0.28, -0.12, 0.0)), Vector((0.14, -0.20, 0.02)), Vector((0.0, -0.22, 0.03)), Vector((-0.14, -0.20, 0.02)), Vector((-0.28, -0.12, 0.0))], 0.012, "metal", False, taper=[0.5, 0.9, 1.2, 0.9, 0.5]),
        tube("String", [Vector((0.275, -0.12, 0.0)), Vector((0.0, -0.02, 0.03)), Vector((-0.275, -0.12, 0.0))], 0.002, "tan", False),
        box("Bolt", "toxic", (0.008, 0.28, 0.008), (0, -0.14, 0.045), 0.002),
        cyl("Vial", "toxic", 0.022, 0.08, (0.04, 0.08, 0.04), (0, 0, 0), 12),
        cyl("Vial 2", "toxic", 0.018, 0.06, (-0.04, 0.12, 0.035), (0, 0, 0), 12),
        cyl("Tube", "metal", 0.006, 0.16, (0.03, -0.02, 0.04), C.X90, 8),
    ]
    return C.join(parts, "Chem crossbow")


def build():
    C.make_joints(scale=S, shoulder_x=0.18, hip_x=0.09)
    materials()
    body = build_body()
    build_head()
    C.scale_parts("head", 1.15, C.J["head_bone"])
    # Tail: a long tapering tube on a spring chain from the base of the spine.
    tail_pts = [B(0, 0.10, 0.92), B(0, 0.22, 0.80), B(0, 0.32, 0.55), B(0, 0.40, 0.30), B(0, 0.52, 0.12), B(0, 0.70, 0.06)]
    tail = tube("Tail", tail_pts, 0.03 * S, "pink", False, taper=[1.0, 0.8, 0.6, 0.45, 0.3, 0.12], resolution=6, bevel=3)
    # Rags: a tattered cloak tail and belt pouches.
    panels = C.coat_panels([("rag.L", 0.06, 0.10, 0.10, 1.30, 0.75, 0.04), ("rag.R", -0.06, 0.10, 0.10, 1.30, 0.80, 0.04)], "cloth", S)
    for name, (pts, mesh) in panels.items():
        for v in mesh.data.vertices:
            if v.co.z < pts[-1].z + 0.05:
                v.co.z += 0.04 * math.sin(v.co.x * 140)
    belt = [torus("Belt", "metal", 0.115 * S, 0.01 * S, B(0, 0.01, 0.92), (0, 0.1, 0), (1.0, 0.8, 1.0), 40), box("Pouch", "tan", (0.05 * S, 0.035 * S, 0.06 * S), B(0.11, -0.04, 0.88), 0.01), cyl("Cask", "olive", 0.04 * S, 0.08 * S, B(-0.12, 0.02, 0.86), (0, 0, 0), 12)]
    for o in belt:
        C.PARTS.append((o, "hips"))
    bow = build_crossbow()
    HOLD = Matrix.Translation(B(-0.16, -0.18, 1.02)) @ Matrix.Rotation(math.radians(-4), 4, "X") @ Matrix.Rotation(math.radians(8), 4, "Z")
    C.place(bow, HOLD)
    muzzle = HOLD @ Matrix.Translation((0, -0.30, 0.045))
    fx = {
        "fx_flash": (C.fx_flash("toxic flash", 0.03, "toxic"), muzzle, "crossbow"),
        "fx_bolt": (C.fx_bolt("bolt", 0.24, 0.012, "toxic"), None, None),
        "fx_bolt2": (C.fx_bolt("bolt 2", 0.24, 0.012, "toxic"), None, None),
        "fx_bolt3": (C.fx_bolt("bolt 3", 0.24, 0.012, "toxic"), None, None),
        "fx_cask": (C.join([C.cyl("FX cask", "olive", 0.04, 0.08, (0, 0, 0), (0.4, 0, 0), 12), ball_mesh("FX cask glow", "toxic", (0, 0, 0.045), (0.02, 0.02, 0.01), 10, 6)], "FX cask"), None, None),
        "fx_cloud": (C.join([ball_mesh(f"FX venom {k}", "cloud", (math.cos(k * 1.4) * 0.25, math.sin(k * 1.4) * 0.25, 0.1 * (k % 2)), (0.22, 0.22, 0.16), 14, 7) for k in range(6)], "FX venom cloud"), None, None),
        "fx_mist": (C.join([ball_mesh(f"FX ambush {k}", "cloud", (math.cos(k * 1.1) * 0.25, math.sin(k * 1.1) * 0.25, 0.25 * (k % 3)), (0.25, 0.25, 0.25), 14, 7) for k in range(6)], "FX ambush mist"), Matrix.Translation(B(0, 0, 0.4)), "root"),
        # Spray and Pray is a buff: the crossbow takes on a toxic glow and its bolts grow long and pierce.
        "fx_charged": (C.fx_orb("charged crossbow", 0.06, "cloud", 2), HOLD @ Matrix.Translation((0, -0.12, 0.03)), "crossbow"),
        "fx_ring": (C.torus("FX spray ring", "toxic", 0.32, 0.012, (0, 0, 0), (0, 0, 0), (1, 1, 1), 40), Matrix.Translation(B(0, 0, 0.04)), "root"),
        "fx_pierce": (C.fx_bolt("piercing bolt", 0.6, 0.022, "toxic", "cloud", 1), None, None),
        "fx_pierce2": (C.fx_bolt("piercing bolt 2", 0.6, 0.022, "toxic", "cloud", 1), None, None),
    }
    grip = HOLD @ Vector((0, 0.06, -0.05))
    fore = HOLD @ Vector((0, -0.16, -0.02))
    extra = [C.weapon_bones("crossbow", HOLD, (0, 0, 0), "hips", 0.25), C.grip_bone("grip_bow.R", grip, "crossbow"), C.grip_bone("grip_bow.L", fore, "crossbow")]
    extra += C.fx_bones(fx, Matrix.Translation(B(-0.2, -0.5, 1.1)))
    chains = [("tail", C.resample(tail_pts, 5), "hips", dict(skin=True, stiffness=40, gain=1.2, sway=6.0, limit=(40, 40)))]
    chains += C.coat_chains(panels, stiffness=50, gain=0.9, sway=2.5, limit=(40, 20))
    C.SKINNED.append((tail, ["hips"] + [f"tail.{i}" for i in range(5)]))
    C.SOCKETS["socket_muzzle"] = ("crossbow", muzzle)
    C.build_rig("Twitch rig", chains, extra, [("R", "bow", "grip_bow.R"), ("L", "bow", "grip_bow.L")])
    C.bind(body)
    C.attach(bow, "crossbow")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips()


FX = ["fx_flash", "fx_bolt", "fx_bolt2", "fx_bolt3", "fx_cask", "fx_cloud", "fx_mist", "fx_charged", "fx_ring", "fx_pierce", "fx_pierce2"]


def define_clips():
    aim = placement("crossbow", B(-0.12, -0.24, 1.12), rx=2, rz=4)

    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def muzzle_at(frame):
        return C.carried("crossbow", frame, C.rig.data.bones["fx_flash"].head_local)

    def bore(frame):
        return muzzle_at(frame) - C.carried("crossbow", frame, C.rig.data.bones["crossbow"].head_local)

    def fire(frame, name, distance=4.0, peak=1.0):
        flash("fx_flash", frame, 2, peak)
        C.shoot_from(name, frame, frame + 5, lambda: muzzle_at(frame), lambda: bore(frame), distance)

    def stance(frame, breath=0.0, sway=0.0):
        """Hunched and twitchy: knees bent, back curled, snout forward."""
        loc("hips", frame, x=0.008 * sway, z=-0.10 - 0.008 * breath)
        rot("hips", frame, x=10, z=-6 + 3 * sway)
        rot("spine", frame, x=20 + breath, z=3)
        rot("chest", frame, x=12 + 1.5 * breath, z=3 - sway)
        rot("neck", frame, x=-14)
        rot("head", frame, x=-18 + 2 * breath, z=-8 + 8 * sway)
        C.feet(frame, (0.08, -0.06, 0, -24), (-0.08, 0.10, 0, 26))
        loc("crossbow", frame)
        rot("crossbow", frame)
        ik("R", "bow", frame, 1.0)
        ik("L", "bow", frame, 1.0)
        loc("pole_elbow.R", frame, x=-0.2, y=0.2, z=-0.2)
        loc("pole_elbow.L", frame, x=0.1, y=-0.1, z=-0.35)
        loc("root", frame)
        rot("root", frame)

    def brace(frame):
        rot("chest", frame, x=10, z=-8)
        rot("head", frame, x=-14, z=10)
        weapon_matrix("crossbow", aim, frame)

    def start(frame=0):
        stance(frame)
        fx_off(frame)

    @clip("Idle", 48, loop=True)
    def idle():
        for f, breath, sway in ((0, 0, 0), (12, 1, 0.5), (24, 0, 1), (36, 1, 0.5), (48, 0, 0)):
            stance(f, breath, sway)
        for f in (8, 9, 30, 31):  # nervous sniffs
            rot("head", f, x=-22 if f % 2 == 0 else -16, z=-4)
        fx_off(0)

    @clip("Walk", 16, loop=True)
    def scurry():
        def upper(frame, lead, phase):
            loc("crossbow", frame, z=0.01 * phase)
            rot("crossbow", frame)
            ik("R", "bow", frame, 1.0)
            ik("L", "bow", frame, 1.0)
            loc("pole_elbow.R", frame, x=-0.2, y=0.2, z=-0.2)
            loc("pole_elbow.L", frame, x=0.1, y=-0.1, z=-0.35)

        C.run_cycle(upper, scale=S, lean=26, twist=8, stride=0.85)
        fx_off(0)

    @clip("AA", 20)
    def attack():
        start()
        brace(4)
        fire(7, "fx_bolt")
        weapon_matrix("crossbow", Matrix.Translation(B(0, 0.03, 0.02)) @ aim, 8)
        brace(12)
        stance(20)

    @clip("P", 30)
    def deadly_venom():
        start()
        brace(4)
        fire(6, "fx_bolt")
        size("fx_cloud", 10, 0.0)
        C.put("fx_cloud", 11, B(-0.1, -4.0, 1.0))
        size("fx_cloud", 12, 1.0)
        size("fx_cloud", 24, 1.2)
        size("fx_cloud", 26, 0.0)
        rot("head", 14, x=-10, z=16)  # a delighted snicker
        stance(30)

    @clip("Q", 36)
    def ambush():
        start()
        # He hunches lower, rubs his paws, and vanishes into a toxic haze.
        loc("hips", 6, z=-0.18)
        rot("spine", 6, x=30)
        rot("head", 10, x=-10, z=20)
        size("fx_mist", 8, 0.0)
        size("fx_mist", 14, 1.3)
        size("fx_mist", 28, 1.0)
        size("fx_mist", 32, 0.0)
        size("root", 14, 1.0)
        size("root", 18, 0.0)
        size("root", 28, 0.0)
        size("root", 32, 1.0)
        stance(36)

    @clip("W", 30)
    def venom_cask():
        start()
        # The left paw lets go, grabs a cask from the belt and lobs it.
        ik("L", "bow", 2, 1.0)
        ik("L", "bow", 4, 0.0)
        fk_arm("L", 6, up=40, swing=40, bend=90)
        fk_arm("L", 11, up=90, swing=-60, bend=20)
        C.fly_path("fx_cask", [(11, lambda: C.carried("hand.L", 11, C.J["hand.L"])), (16, B(0.2, -1.6, 1.6)), (21, B(0.3, -3.0, 0.1))], (1, 0, 0), 0.15)
        size("fx_cask", 10, 0.0)
        size("fx_cask", 11, 1.0)
        size("fx_cask", 21, 1.0)
        size("fx_cask", 22, 0.0)
        size("fx_cloud", 21, 0.0)
        C.put("fx_cloud", 22, B(0.3, -3.0, 0.1))
        size("fx_cloud", 23, 1.2)
        size("fx_cloud", 29, 0.0)
        ik("L", "bow", 20, 0.0)
        ik("L", "bow", 24, 1.0)
        stance(30)

    @clip("E", 28)
    def contaminate():
        start()
        # A vicious squeeze of the vial on the crossbow; the venom bursts on every target.
        rot("chest", 6, x=20, z=-6)
        rot("head", 6, x=-6, z=10)
        flash("fx_flash", 8, 4, 1.6)
        size("fx_cloud", 9, 0.0)
        C.put("fx_cloud", 10, B(0.0, -3.5, 0.9))
        size("fx_cloud", 10, 1.5)
        size("fx_cloud", 16, 0.0)
        stance(28)

    @clip("R", 48)
    def spray_and_pray():
        start()
        # A buff, not a volley: he throws his head back cackling and hugs the crossbow up to his
        # chest while it charges with venom (a toxic ring rises around him). Then the empowered
        # autos: two long glowing bolts that pierce straight through.
        rot("chest", 5, x=-4, z=-4)
        rot("neck", 5, x=-26)
        rot("head", 5, x=-34, z=-6)
        weapon_matrix("crossbow", placement("crossbow", B(-0.06, -0.16, 1.18), rx=55, rz=12), 6)
        for k, f in enumerate(range(7, 18, 2)):  # shoulders shaking with laughter
            rot("chest", f, x=-4 + (3 if k % 2 else -1), z=-4 + (2 if k % 2 else -2))
            rot("head", f, x=-34 + (5 if k % 2 else 0), z=-6)
        size("fx_charged", 6, 0.0)
        size("fx_charged", 10, 1.3)
        size("fx_charged", 18, 1.0)
        size("fx_charged", 46, 1.0)
        size("fx_charged", 48, 0.0)
        for f, s_ in ((6, 0.0), (9, 0.8), (16, 1.2), (20, 0.0)):
            size("fx_ring", f, s_)
        loc("fx_ring", 9)
        loc("fx_ring", 20, z=0.6)
        rot("neck", 18, x=-14)
        brace(20)
        fire(24, "fx_pierce", 8.0, 1.5)
        weapon_matrix("crossbow", Matrix.Translation(B(0, 0.04, 0.02)) @ aim, 25)
        brace(29)
        fire(33, "fx_pierce2", 8.0, 1.5)
        weapon_matrix("crossbow", Matrix.Translation(B(0, 0.04, 0.02)) @ aim, 34)
        brace(38)
        rot("head", 36, x=-12, z=14)  # a snicker
        stance(48)

    @clip("Recall", 48, loop=True)
    def recall():
        # Crossbow cradled, he scratches behind an ear and sniffs the air.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.5)
            ik("L", "bow", f, 0.0)
            fk_arm("L", f, up=70 + 8 * abs(s_), swing=-20, bend=140, out=10, hand=-20)
            rot("head", f, x=-10, z=-14 + 4 * s_, y=8 * s_)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        for side in ("L", "R"):
            ik(side, "bow", 3, 1.0)
            ik(side, "bow", 6, 0.0)
        loc("crossbow", 5)
        rot("crossbow", 5)
        weapon_matrix("crossbow", placement("crossbow", B(-0.40, -0.10, 0.06), rx=0, ry=80, rz=30), 14)
        C.fall_back(0, S)
