"""Miss Fortune: an original stylized interpretation (copper-red flowing hair, broad pirate hat
with a plume, navy coat over a red corset, two brass flintlock pistols)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, cyl, fk_arm, flash, lathe, loc, material, metaball_object, rot, size, torus

S = 1.04
RIM = (1.0, 0.6, 0.35)
EXPOSURE = -0.15
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55), "E": dict(angle_deg=28, distance=4.2, height=1.4, target_z=0.9)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#dab298", rough=0.5, sss=0.2),
        navy=material("Navy coat", "#22334f", rough=0.6),
        red=material("Red corset", "#9b3243", rough=0.5),
        cream=material("Cream shirt", "#ede1ca", rough=0.6),
        brass=material("Brass", "#bc9658", rough=0.3, metal=1.0),
        wood=material("Pistol wood", (0.16, 0.07, 0.03), rough=0.45),
        boot=material("Brown boots", (0.10, 0.05, 0.025), rough=0.45),
        trousers=material("Dark trousers", (0.02, 0.02, 0.03), rough=0.6),
        hat=material("Hat felt", (0.03, 0.035, 0.06), rough=0.7),
        hair=material("Copper hair", (0.62, 0.12, 0.04), rough=0.45),
        hair_dark=material("Deep copper", (0.32, 0.05, 0.02), rough=0.5),
        plume=material("Plume", (0.85, 0.82, 0.75), rough=0.8),
        fire=material("Gunfire", "#ffbc68", emission=8.0),
        love=material("Love tap", (1.0, 0.35, 0.55), emission=6.0),
    )
    C.face_materials(iris=(0.20, 0.45, 0.30), lash=(0.02, 0.01, 0.01), lip=(0.70, 0.18, 0.22))


def build_body():
    meta = metaball_object("MF body")
    C.torso_female(meta, S, bust=1.12, hips=1.05, waist=0.9)
    C.limbs(meta, dict(thigh=(0.066, 0.041), calf=(0.041, 0.047, 0.03), arm=(0.042, 0.031), forearm=(0.033, 0.025), palm=0.033), hands="mitten")
    for side in ("L", "R"):
        knee, toe = C.J[f"knee.{side}"], C.J[f"toe.{side}"]
        ball(meta, knee + Vector((0, -0.012, 0.05 * S)), 0.054 * S, (1.0, 1.0, 0.5))  # boot cuff over the knee
        ball(meta, toe + Vector((0, 0.01, 0.004)), 0.034 * S, (0.9, 1.25, 0.7))
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in (0.58, 0.88, 0.97, 1.17, 1.40)]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.70, 0.76)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            f = C.arm_fraction(c, side)
            return "skin" if f > 0.76 else "cream" if f > 0.70 else "navy"
        if z < 0.58:
            return "boot"
        if z < 0.88:
            return "trousers"
        if z < 0.97:
            return "navy"
        if z < 1.17:
            return "red"  # corset
        if z > 1.40 and math.hypot(x, y - 0.01) < 0.065:
            return "skin"
        if y < -0.02 and abs(x) < 0.09:
            return "cream"  # shirt neckline
        return "navy"

    return C.body_mesh(meta, "MF body", region, ["skin", "navy", "red", "cream", "trousers", "boot"], cuts)


def build_clothes():
    panels = C.coat_panels(
        [
            ("back.L", 0.06, 0.105, 0.11, 0.97, 0.50, 0.03),
            ("back.R", -0.06, 0.105, 0.11, 0.97, 0.50, 0.03),
            ("side.L", 0.125, 0.025, 0.11, 0.97, 0.55, 0.07),
            ("side.R", -0.125, 0.025, 0.11, 0.97, 0.55, 0.07),
        ],
        "navy",
        S,
    )
    for sx in (1, -1):
        lapel = C.ribbon("Coat lapel", [B(0.07 * sx, -0.07, 1.17), B(0.10 * sx, -0.075, 1.29), B(0.12 * sx, -0.05, 1.38)], 0.035 * S, "red", (1, 0, 0), 0.005, [1.0, 1.1, 0.9], bone=False)
        C.SKINNED.append((lapel, ["spine", "chest"]))
    # Corset lacing, brass buttons, sash and belt.
    lacing = [box("Lacing", "cream", (0.06 * S, 0.004, 0.005), B(0, -0.093 + 0.0, 1.0 + 0.04 * k), 0.001) for k in range(4)]
    for o in lacing:
        C.PARTS.append((o, "spine"))
    belt = [
        torus("Belt", "boot", 0.122 * S, 0.010 * S, B(0, 0.01, 0.93), (0, 0.12, 0), (1.0, 0.8, 1.0), 40),
        box("Buckle", "brass", (0.034 * S, 0.01, 0.026 * S), B(0.01, -0.096, 0.925), 0.004),
        C.ribbon("Sash", [B(-0.10, -0.06, 0.94), B(-0.13, -0.02, 0.86), B(-0.14, 0.0, 0.74)], 0.05 * S, "red", (0, 1, 0), 0.004, [1.0, 0.9, 0.7], bone=False),
    ]
    for sx in (1, -1):
        belt.append(box("Holster", "boot", (0.035 * S, 0.06 * S, 0.12 * S), B(0.14 * sx, -0.005, 0.85), 0.01, (0, math.radians(8 * sx), 0)))
    for o in belt:
        C.PARTS.append((o, "hips"))
    return panels


def build_head():
    C.build_head("MF head", jaw=0.96, chin=0.98, nose=0.95)
    C.build_face(eye_size=1.0, lashes="winged", brow_mat="hair_dark", brow_width=0.002, brow_angle=0.05, mouth="smirk", mouth_size=0.0022, mouth_width=1.05)
    h = C.HEAD
    C.hair_cap("MF hair cap", "hair", front_y=0.045, front_z=0.05, scale=1.04)
    meta = metaball_object("MF hair", resolution=0.0045)
    # Side-parted waves framing the face and big volume at the sides and back.
    for i, x in enumerate((0.06, 0.03, 0.0)):
        C.clump(meta, [h + Vector((x - 0.02, -0.075, 0.10)), h + Vector((x + 0.02, -0.10, 0.07)), h + Vector((x + 0.05, -0.09, 0.02))], 0.02, 0.006, flat=0.6)
    for sx in (1, -1):
        C.clump(meta, [h + Vector((0.08 * sx, -0.06, 0.07)), h + Vector((0.11 * sx, -0.05, -0.02)), h + Vector((0.12 * sx, -0.03, -0.12)), h + Vector((0.12 * sx, -0.01, -0.20))], 0.032, 0.014)
    for x0 in (0.06, 0.0, -0.06):
        C.clump(meta, [h + Vector((x0, 0.06, 0.11)), h + Vector((x0 * 1.4, 0.12, 0.0)), h + Vector((x0 * 1.5, 0.12, -0.12))], 0.042, 0.03)
    hair = C.mesh_from_meta(meta, "MF hair", voxel=0.004, smooth=3, tris=6000)
    C.paint_regions(hair, lambda c: "hair" if c.z > h.z - 0.04 else "hair_dark", ["hair", "hair_dark"])
    C.PARTS.append((hair, "head"))
    backs = {}
    for side, sx in (("L", 1), ("R", -1)):
        path = [h + Vector((0.06 * sx, 0.11, -0.10)), B(0.08 * sx, 0.14, 1.36), B(0.10 * sx, 0.15, 1.20), B(0.11 * sx, 0.14, 1.04)]
        sheet = metaball_object(f"MF back hair {side}", resolution=0.005)
        C.clump(sheet, path, 0.052, 0.025, flat=0.6)
        mesh = C.mesh_from_meta(sheet, f"MF back hair {side}", voxel=0.0045, smooth=3, tris=2500)
        C.paint_regions(mesh, lambda c: "hair" if c.z > 1.30 * S else "hair_dark", ["hair", "hair_dark"])
        backs[side] = (path, mesh)
    # The broad pirate hat: wide brim with upturned sides, a crown and a white plume.
    brim = lathe("Hat brim", "hat", [(0.0, -0.004), (0.22, -0.004), (0.23, 0.0), (0.22, 0.006), (0.0, 0.006)], 48, "Z")
    for v in brim.data.vertices:  # turn up the left and right of the brim
        r = math.hypot(v.co.x, v.co.y)
        v.co.z += max(0.0, abs(v.co.x) - 0.08) * 0.55 * (r / 0.23)
    crown = lathe("Hat crown", "hat", [(0.0, 0.0), (0.11, 0.0), (0.104, 0.09), (0.085, 0.13), (0.0, 0.14)], 40, "Z")
    band = lathe("Hat band", "red", [(0.112, 0.008), (0.11, 0.035)], 40, "Z")
    buckle = box("Hat buckle", "brass", (0.03, 0.01, 0.026), (0.0, -0.112, 0.022), 0.003)
    plume = C.ribbon("Plume", [Vector((0.09, 0.0, 0.04)), Vector((0.16, 0.06, 0.12)), Vector((0.20, 0.15, 0.16)), Vector((0.21, 0.24, 0.12))], 0.07, "plume", (0, 0, 1), 0.004, [0.5, 1.0, 0.9, 0.3], bone=False)
    hat = C.join([brim, crown, band, buckle, plume], "Pirate hat")
    C.place(hat, Matrix.Translation(h + Vector((0.0, 0.01, 0.088))) @ Matrix.Rotation(math.radians(8), 4, "Y") @ Matrix.Rotation(math.radians(-6), 4, "X"))
    C.PARTS.append((hat, "head"))
    return backs


def build_flintlock(name):
    """A brass flintlock: grip at the origin (in the fist), long barrel toward -Y, top +Z."""
    parts = [
        cyl("Barrel", "brass", 0.013, 0.26, (0, -0.15, 0.035), C.X90, 16),
        lathe("Muzzle", "brass", [(0.016, -0.275), (0.019, -0.28), (0.019, -0.295), (0.014, -0.30)], 16),
        box("Lock", "brass", (0.03, 0.07, 0.04), (0, -0.01, 0.03), 0.006),
        box("Hammer", "brass", (0.008, 0.02, 0.03), (0, 0.025, 0.055), 0.002, (math.radians(-25), 0, 0)),
        box("Stock", "wood", (0.03, 0.05, 0.12), (0, 0.025, -0.035), 0.012, (math.radians(-20), 0, 0)),
        ball_mesh("Pommel", "brass", (0, 0.045, -0.095), (0.02, 0.022, 0.018), 12, 6),
        box("Forestock", "wood", (0.026, 0.14, 0.022), (0, -0.09, 0.018), 0.006),
        torus("Trigger guard", "brass", 0.015, 0.003, (0, -0.01, -0.005), (0, math.pi / 2, 0), (1, 1, 1), 16),
    ]
    return C.join(parts, name)


def build():
    C.make_joints(scale=S, shoulder_x=0.176, hip_x=0.096)
    materials()
    body = build_body()
    panels = build_clothes()
    backs = build_head()
    C.scale_parts("head", 1.06, C.J["head_bone"])

    muzzles, grips = {}, {}
    for side in ("L", "R"):
        wr, hd = C.J[f"wrist.{side}"], C.J[f"hand.{side}"]
        n = C.hand_normal(side)
        frame = C.frame_along(wr.lerp(hd, 0.55) - n * 0.012, hd - wr, Vector((0, -1, 0)))
        gun = build_flintlock(f"Flintlock {side}")
        C.place(gun, frame)
        C.PARTS.append((gun, f"hand.{side}"))
        muzzles[side] = frame @ Matrix.Translation((0, -0.30, 0.035))
        grips[side] = frame @ Matrix.Translation((0, -0.10, 0.035))
    fx = {}
    for side in ("L", "R"):
        fx[f"fx_flash.{side}"] = (C.fx_flash(f"flash {side}", 0.035, "fire"), muzzles[side], f"hand.{side}")
    for k in range(8):
        fx[f"fx_shot.{k}"] = (C.fx_bolt(f"shot {k}", 0.14, 0.012, "fire"), None, None)
    fx["fx_love"] = (C.fx_flash("love tap", 0.06, "love", 8), None, None)
    fx["fx_ricochet"] = (C.fx_flash("ricochet", 0.05, "fire", 6), None, None)
    fx["fx_rain"] = (C.join([C.fx_bolt(f"rain {k}", 0.18, 0.012, "fire") for k in range(10)], "FX rain"), None, None)
    extra = C.fx_bones(fx, Matrix.Translation(B(0, -0.4, 1.2)))
    # Spread the rain bolts over a circle, pointing down.
    rain = fx["fx_rain"][0]
    chains = C.coat_chains(panels, stiffness=55, gain=0.9, sway=2.0, limit=(45, 25))
    for side, (path, mesh) in backs.items():
        chains.append((f"backhair.{side}", C.resample(path, 3), "head", dict(skin=True, stiffness=55, gain=1.0, sway=3.0, limit=(40, 30))))
        C.SKINNED.append((mesh, ["head"] + [f"backhair.{side}.{i}" for i in range(3)]))
    C.SOCKETS["socket_muzzle"] = ("hand.R", muzzles["R"])
    C.build_rig("MF rig", chains, extra)
    C.bind(body)
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    scatter_rain(rain)
    define_clips(muzzles, grips)


def scatter_rain(rain):
    """Lay the joined rain bolts out over a 1 m circle, falling (-Y of each bolt turned down)."""
    import bmesh

    bm = bmesh.new()
    bm.from_mesh(rain.data)
    islands = []
    seen = set()
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, island = [v], []
        while stack:
            u = stack.pop()
            if u.index in seen:
                continue
            seen.add(u.index)
            island.append(u)
            stack.extend(e.other_vert(u) for e in u.link_edges)
        islands.append(island)
    for k, island in enumerate(islands):
        a = k * 2.399
        r = 0.5 * math.sqrt((k + 0.5) / len(islands))
        centre = sum((u.co for u in island), Vector()) / len(island)
        turn = Matrix.Rotation(math.radians(-90), 3, "X")
        for u in island:
            u.co = turn @ (u.co - centre) + centre + Vector((math.cos(a) * r, math.sin(a) * r, 0.15 * (k % 3)))
    bm.to_mesh(rain.data)
    bm.free()


SHOTS = [f"fx_shot.{k}" for k in range(8)]
FX = ["fx_flash.L", "fx_flash.R", "fx_love", "fx_ricochet", "fx_rain"] + SHOTS


def define_clips(muzzles, grips):
    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def muzzle(side, frame):
        return C.carried(f"hand.{side}", frame, muzzles[side].translation)

    def barrel(side, frame):
        return muzzle(side, frame) - C.carried(f"hand.{side}", frame, grips[side].translation)

    def fire(side, frame, shot, distance=4.0, peak=1.2, direction=None):
        flash(f"fx_flash.{side}", frame, 2, peak)
        C.shoot_from(shot, frame, frame + 5, lambda: muzzle(side, frame), direction or (lambda: barrel(side, frame)), distance)

    def stance(frame, breath=0.0, sway=0.0):
        """Hip-cocked swagger: weight on one leg, right pistol resting on the shoulder."""
        loc("hips", frame, x=0.03 + 0.008 * sway, z=-0.02 - 0.004 * breath)
        rot("hips", frame, y=6 + sway, z=-6)
        rot("spine", frame, x=1 + breath, y=-4, z=3)
        rot("chest", frame, x=-3 + 1.5 * breath, y=-2, z=3 - sway)
        rot("head", frame, x=-3 + breath, y=5 - sway, z=-6 + 2 * sway)
        C.feet(frame, (0.02, 0.03, 0, -14), (-0.05, -0.07, 0, 18))
        fk_arm("R", frame, up=30, swing=-25, bend=140, out=10, twist=-20, hand=-30)
        fk_arm("L", frame, up=12 + 2 * breath, swing=-10, bend=30, out=2, twist=15, hand=-30)
        loc("root", frame)
        rot("root", frame)

    def aim(side, frame, up=0.0, out=-4.0, bend=6):
        fk_arm(side, frame, up=up, swing=-88, bend=bend, out=out, hand=-4)

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
            fk_arm("L", frame, up=12, swing=arc - 8, bend=65, out=2, hand=-25)
            fk_arm("R", frame, up=12, swing=-arc - 8, bend=65, out=2, hand=-25)

        C.run_cycle(upper, scale=S, lean=9, twist=11)
        fx_off(0)

    @clip("AA", 20)
    def attack():
        start()
        aim("R", 4)
        rot("chest", 4, z=12)
        rot("head", 4, y=0, z=-8)
        fire("R", 6, SHOTS[0])
        aim("R", 7, up=14, bend=20)
        aim("R", 9)
        stance(20)

    @clip("P", 22)
    def love_tap():
        start()
        aim("L", 4)
        rot("chest", 4, z=-10)
        fire("L", 6, SHOTS[1])
        aim("L", 7, up=14, bend=20)
        size("fx_love", 10, 0.0)
        C.put("fx_love", 11, B(0.05, -4.0, 1.3))
        size("fx_love", 11, 1.4)
        size("fx_love", 15, 0.0)
        stance(22)

    @clip("Q", 26)
    def double_up():
        start()
        # One shot that ricochets off the first target to a second one behind it.
        aim("R", 5, out=-6)
        rot("chest", 5, z=14)
        rot("head", 5, z=-10)
        fire("R", 7, SHOTS[0], 3.0, 1.6)
        aim("R", 8, up=16, bend=22)
        size("fx_ricochet", 11, 0.0)
        C.put("fx_ricochet", 12, B(-0.25, -3.1, 1.3))
        size("fx_ricochet", 12, 1.5)
        size("fx_ricochet", 16, 0.0)
        C.shoot_from(SHOTS[1], 12, 17, lambda: B(-0.25, -3.1, 1.3), (-0.5, -1, -0.05), 1.6)
        rot("head", 12, y=6, z=-4)  # a wink at the ricochet
        stance(26)

    @clip("W", 32)
    def strut():
        start()
        # A cocky pistol twirl and a hair toss.
        for k, f in enumerate((4, 8, 12, 16)):
            fk_arm("L", f, up=40, swing=-60, bend=90, out=-10, twist=20, hand=-30 + 90 * (k % 2))
        rot("head", 10, x=-12, y=-12, z=12)
        rot("chest", 10, x=-5, z=6)
        rot("head", 18, x=-4, y=6, z=-8)
        stance(32)

    @clip("E", 34)
    def make_it_rain():
        start()
        # Right pistol straight up, three shots into the sky; the rain falls ahead of her.
        fk_arm("R", 5, up=170, swing=-10, bend=10, out=-5, hand=-10)
        rot("chest", 5, x=-6, z=4)
        rot("head", 5, x=-20)
        for k, f in enumerate((7, 10, 13)):
            fire("R", f, SHOTS[k], 2.0, 1.4, direction=(0, 0, 1))
            fk_arm("R", f + 1, up=160, swing=-14, bend=18, out=-5, hand=-10)
        rot("head", 16, x=6)
        size("fx_rain", 15, 0.0)
        C.put("fx_rain", 16, B(0.0, -2.6, 2.4))
        size("fx_rain", 16, 1.0)
        C.put("fx_rain", 26, B(0.0, -2.6, 0.2))
        size("fx_rain", 26, 1.0)
        size("fx_rain", 27, 0.0)
        stance(34)

    @clip("R", 60)
    def bullet_time():
        start()
        # Both pistols forward, alternating fire swept across a cone.
        for side in ("L", "R"):
            aim(side, 6, out=-10)
        C.feet(6, (0.08, -0.10, 0, -15), (-0.08, 0.06, 0, 15))
        loc("hips", 6, z=-0.06)
        k = 0
        for f in range(8, 52, 3):
            side = "R" if k % 2 == 0 else "L"
            sweep = -20 + 40 * (f - 8) / 44
            rot("chest", f, z=sweep * 0.6)
            aim(side, f, out=-6, up=2)
            fire(side, f, SHOTS[k % 8], 4.0, 1.1)
            aim(side, f + 1, up=10, out=-6, bend=14)
            k += 1
        stance(60)

    @clip("Recall", 48, loop=True)
    def recall():
        # Blows the smoke off the right barrel, pistol held up by her face.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.5)
            fk_arm("R", f, up=40, swing=-55, bend=120, out=-30, twist=-30, hand=-50)
            rot("head", f, x=4, z=-14 + 3 * s_)
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        C.fall_back(0, S)
