"""Kai'Sa: an original stylized interpretation (sculpted violet void carapace with glowing seams,
dark ponytail, glowing eyes, articulated shoulder missile pods and an arm cannon)."""

import math

from mathutils import Matrix, Vector

import core as C
from core import M, ball, ball_mesh, box, clip, fk_arm, flash, lathe, loc, material, metaball_object, rot, size, torus

S = 1.03
RIM = (0.8, 0.45, 1.0)
EXPOSURE = -0.1
CLIP_VIEWS = {"Death": dict(angle_deg=40, distance=3.6, height=1.5, target_z=0.55), "Q": dict(angle_deg=28, distance=4.0, height=1.5, target_z=1.0)}


def B(x, y, z):
    return Vector((x, y, z)) * S


def materials():
    M.update(
        skin=material("Skin", "#d4b1ad", rough=0.5, sss=0.2),
        void=material("Void carapace", "#291a43", rough=0.3, metal=0.4),
        violet=material("Violet plates", "#61417d", rough=0.3, metal=0.5),
        lilac=material("Lilac", "#a082c9", rough=0.35, metal=0.3),
        dark=material("Dark shell", "#371e54", rough=0.3, metal=0.6),
        hair=material("Dark hair", (0.02, 0.012, 0.03), rough=0.45),
        hair_dark=material("Deep hair", (0.01, 0.006, 0.02), rough=0.5),
        glow=material("Void glow", "#ca7bff", emission=7.0),
        plasma=material("Plasma", (0.95, 0.5, 1.0), emission=9.0),
        shield=material("Void shield", (0.8, 0.45, 1.0), emission=2.5, alpha=0.3),
    )
    C.face_materials(iris=(0.85, 0.35, 1.0), lash=(0.02, 0.01, 0.03), lip=(0.45, 0.25, 0.32))
    M["iris"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.6


def build_body():
    meta = metaball_object("Kaisa body")
    C.torso_female(meta, S, bust=0.95, hips=0.98, waist=0.9)
    C.limbs(meta, dict(thigh=(0.063, 0.041), calf=(0.041, 0.046, 0.029), arm=(0.043, 0.032), forearm=(0.035, 0.027), palm=0.033), hands="mitten")
    for side in ("L", "R"):
        toe = C.J[f"toe.{side}"]
        ball(meta, toe + Vector((0, 0.012, 0.004)), 0.034 * S, (0.9, 1.3, 0.7))
        knee = C.J[f"knee.{side}"]
        ball(meta, knee + Vector((0, -0.02, 0.0)), 0.04 * S, (1.0, 0.8, 1.2))  # knee carapace
    seams = (0.30, 0.62, 0.92, 1.06, 1.22)
    cuts = [((0, 0, z * S), (0, 0, 1)) for z in seams + (0.305 + 0.0, 0.625, 0.925, 1.065, 1.225, 1.41)]
    for side in ("L", "R"):
        cuts += [C.arm_cut(side, f) for f in (0.35, 0.36, 0.70, 0.71)]

    def region(c):
        x, y, z = c / S
        side = "L" if x > 0 else "R"
        if abs(x) > 0.20 and z > 0.85:
            f = C.arm_fraction(c, side)
            return "glow" if 0.35 < f < 0.36 or 0.70 < f < 0.71 else "violet" if f > 0.71 else "void"
        for lo in seams:
            if lo < z < lo + 0.005:
                return "glow"
        if z > 1.41 and math.hypot(x, y - 0.01) < 0.065:
            return "skin"
        if 0.62 < z < 0.92:
            return "violet"
        return "void"

    return C.body_mesh(meta, "Kaisa body", region, ["skin", "void", "violet", "glow"], cuts)


def build_pod(side):
    """A shoulder missile pod: a carapace shell over glowing launch tubes (opens to fire)."""
    sx = 1 if side == "L" else -1
    shell = [
        lathe("Pod shell", "dark", [(0.0, 0.16), (0.05, 0.15), (0.075, 0.08), (0.07, -0.02), (0.04, -0.08), (0.0, -0.10)], 20),
        C.plate("Pod blade", "violet", [(0.0, 0.14, 0.06), (0.10 * sx, 0.30, 0.10), (0.04 * sx, 0.05, 0.07)], 0.012, 0.0),
        C.plate("Pod blade 2", "lilac", [(0.0, 0.10, 0.02), (0.13 * sx, 0.22, -0.02), (0.05 * sx, 0.0, 0.0)], 0.01, 0.0),
    ]
    tubes = [C.cyl("Launch tube", "glow", 0.012, 0.06, ((k % 3 - 1) * 0.03, -0.04, (k // 3) * 0.03 - 0.015), C.X90, 8) for k in range(6)]
    return C.join(shell, f"Pod shell {side}"), C.join(tubes, f"Pod tubes {side}")


def build_head():
    C.build_head("Kaisa head", jaw=0.95, chin=0.97, nose=0.92)
    C.build_face(eye_size=1.0, lashes="winged", brow_mat="hair", brow_width=0.002, brow_angle=0.14, mouth="flat", mouth_size=0.0018)
    h = C.HEAD
    C.hair_cap("Kaisa hair", "hair", front_y=0.045, front_z=0.055)
    meta = metaball_object("Kaisa fringe", resolution=0.004)
    for sx in (1, -1):
        C.clump(meta, [h + Vector((0.06 * sx, -0.07, 0.09)), h + Vector((0.09 * sx, -0.07, 0.0)), h + Vector((0.09 * sx, -0.05, -0.10))], 0.016, 0.004, flat=0.6)
    fringe = C.mesh_from_meta(meta, "Kaisa fringe", voxel=0.0035, smooth=3, tris=2000)
    fringe.data.materials.append(M["hair"])
    C.PARTS.append((fringe, "head"))
    tie = h + Vector((0, 0.09, 0.05))
    path = [tie, tie + Vector((0, 0.06, -0.04)), tie + Vector((0, 0.08, -0.18)), tie + Vector((0, 0.07, -0.34)), tie + Vector((0, 0.05, -0.48))]
    meta = metaball_object("Kaisa ponytail", resolution=0.0045)
    C.clump(meta, path, 0.034, 0.01)
    pony = C.mesh_from_meta(meta, "Kaisa ponytail", voxel=0.004, smooth=3, tris=2500)
    pony.data.materials.append(M["hair"])
    C.PARTS.append((torus("Hair band", "glow", 0.022, 0.005, tie + Vector((0, 0.01, 0)), (math.radians(70), 0, 0), (1, 1, 1), 16), "head"))
    # A carapace crest over the brow.
    crest = C.plate("Crest", "dark", [(-0.08, 0, 0.0), (0.0, 0, 0.03), (0.08, 0, 0.0), (0.0, 0, 0.06)], 0.01, 0.0)
    C.place(crest, Matrix.Translation(h + Vector((0, -0.07, 0.10))) @ Matrix.Rotation(math.radians(-35), 4, "X"))
    C.PARTS.append((crest, "head"))
    return path, pony


def build():
    C.make_joints(scale=S, shoulder_x=0.178, hip_x=0.093)
    materials()
    body = build_body()
    pony_path, pony = build_head()
    C.scale_parts("head", 1.06, C.J["head_bone"])
    # Shoulder pods (bones pod.L/R on the chest) and an arm cannon on the right forearm.
    pods = {}
    for side, sx in (("L", 1), ("R", -1)):
        shell, tubes = build_pod(side)
        for o in (shell, tubes):
            C.place(o, Matrix.Scale(1.7, 4))
        m = Matrix.Translation(B(0.13 * sx, 0.12, 1.42)) @ Matrix.Rotation(math.radians(-50), 4, "X") @ Matrix.Rotation(math.radians(-30 * sx), 4, "Y")
        C.place(shell, m)
        C.place(tubes, m)
        pods[side] = (m, shell, tubes)
    el, wr = C.J["elbow.R"], C.J["wrist.R"]
    n = C.hand_normal("R")
    G = C.frame_along(wr, wr - el, n)
    cannon = [
        lathe("Arm cannon", "dark", [(0.045, 0.18), (0.05, 0.12), (0.048, 0.02), (0.035, -0.03)], 20),
        lathe("Cannon seam", "glow", [(0.052, 0.10), (0.052, 0.09)], 20),
        C.plate("Cannon fin", "violet", [(0.0, 0.16, 0.04), (0.0, 0.0, 0.08), (0.0, -0.04, 0.05)], 0.012, 0.0),
        ball_mesh("Cannon core", "glow", (0, -0.03, 0.0), (0.02, 0.012, 0.02), 12, 6),
    ]
    for o in cannon:
        C.place(o, G)
        C.PARTS.append((o, "forearm.R"))
    muzzle = G @ Matrix.Translation((0, -0.05, 0.0))
    fx = {
        "fx_flash": (C.fx_flash("plasma flash", 0.035, "plasma"), muzzle, "forearm.R"),
        "fx_bolt": (C.fx_bolt("plasma bolt", 0.18, 0.018, "plasma"), None, None),
        "fx_seeker": (C.fx_bolt("void seeker", 0.6, 0.04, "glow", "plasma", rings=2), None, None),
        "fx_aura": (C.join([C.torus("FX supercharge", "glow", 0.4, 0.008, (0, 0, 0), (math.pi / 2 - 0.4 * k, 0.6 * k, 0), (1, 1, 1), 36) for k in range(3)], "FX supercharge"), Matrix.Translation(B(0, 0, 1.0)), "hips"),
        "fx_shield": (C.fx_orb("killer instinct", 0.55, "shield", 0), Matrix.Translation(B(0, 0, 0.95)), "hips"),
        "fx_burst": (C.fx_flash("plasma burst", 0.08, "plasma", 8), None, None),
    }
    for k in range(8):
        fx[f"fx_missile.{k}"] = (C.fx_bolt(f"missile {k}", 0.12, 0.012, "plasma"), None, None)
    extra = [C.point_bone(f"pod.{side}", m, "chest", 0.08) for side, (m, _, _) in pods.items()]
    extra += C.fx_bones(fx, Matrix.Translation(B(-0.2, -0.4, 1.2)))
    chains = [("pony", C.resample(pony_path, 4), "head", dict(skin=True, stiffness=55, gain=1.1, sway=3.0, limit=(45, 35)))]
    C.SKINNED.append((pony, ["head"] + [f"pony.{i}" for i in range(4)]))
    C.SOCKETS["socket_muzzle"] = ("forearm.R", muzzle)
    C.build_rig("Kaisa rig", chains, extra)
    C.bind(body)
    for side, (m, shell, tubes) in pods.items():
        C.attach(shell, f"pod.{side}")
        C.attach(tubes, f"pod.{side}")
    for name, (obj, _, _) in fx.items():
        C.attach(obj, name)
    define_clips(muzzle, G)


MISSILES = [f"fx_missile.{k}" for k in range(8)]
FX = ["fx_flash", "fx_bolt", "fx_seeker", "fx_aura", "fx_shield", "fx_burst"] + MISSILES


def define_clips(muzzle, G):
    def fx_off(frame):
        for name in FX:
            size(name, frame, 0.0)

    def muzzle_at(frame):
        return C.carried("forearm.R", frame, muzzle.translation)

    def barrel(frame):
        return muzzle_at(frame) - C.carried("forearm.R", frame, G.translation + (G.to_3x3() @ Vector((0, 0.15, 0))))

    def pods(frame, open_=0.0):
        for side in ("L", "R"):
            sx = 1 if side == "L" else -1
            rot(f"pod.{side}", frame, x=-35 * open_, y=-20 * open_ * sx)

    def stance(frame, breath=0.0, sway=0.0):
        """Hunter's ready crouch: arm cannon raised across the body, weight low."""
        loc("hips", frame, x=0.008 * sway, z=-0.06 - 0.005 * breath)
        rot("hips", frame, z=-10 + 2 * sway)
        rot("spine", frame, x=7 + breath, z=5)
        rot("chest", frame, x=2 + 1.5 * breath, z=6 - sway)
        rot("head", frame, x=-6 + breath, z=-4 + 3 * sway)
        C.feet(frame, (0.07, -0.12, 0, -18), (-0.07, 0.10, 0, 24))
        fk_arm("R", frame, up=20, swing=-55, bend=75, out=-10, twist=20, hand=-10)
        fk_arm("L", frame, up=14 + 2 * breath, swing=-20, bend=45, out=0, twist=15, hand=-10)
        pods(frame, 0.0)
        loc("root", frame)
        rot("root", frame)

    def aim(frame, up=0.0, bend=8):
        fk_arm("R", frame, up=up, swing=-88, bend=bend, out=-6, twist=60, hand=-5)

    def fire(frame, name, distance=4.0, peak=1.2):
        flash("fx_flash", frame, 2, peak)
        C.shoot_from(name, frame, frame + 6, lambda: muzzle_at(frame), lambda: barrel(frame), distance)

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
            arc = 34 * (1 if lead == "L" else -1) * phase
            fk_arm("L", frame, up=14, swing=arc, bend=70, out=-4, hand=-10)
            fk_arm("R", frame, up=14, swing=-arc, bend=70, out=-4, hand=-10)
            pods(frame, 0.0)

        C.run_cycle(upper, scale=S, lean=13, twist=10)
        fx_off(0)

    @clip("AA", 18)
    def attack():
        start()
        aim(4)
        rot("chest", 4, z=14)
        fire(6, "fx_bolt")
        aim(7, up=10, bend=16)
        aim(9)
        stance(18)

    @clip("P", 26)
    def second_skin():
        start()
        aim(4)
        for k, f in enumerate((6, 9, 12)):
            fire(f, "fx_bolt", 4.0, 1.0)
            aim(f + 1, up=8, bend=14)
        size("fx_burst", 15, 0.0)
        C.put("fx_burst", 16, B(-0.3, -4.0, 1.3))
        size("fx_burst", 16, 1.6)
        size("fx_burst", 21, 0.0)
        stance(26)

    @clip("Q", 34)
    def icathian_rain():
        start()
        # The pods unfold and loose a swarm of seeking missiles in arcs.
        pods(6, 1.0)
        rot("chest", 6, x=-6)
        rot("head", 6, x=-8)
        for k, name in enumerate(MISSILES):
            side = "L" if k % 2 == 0 else "R"
            sx = 1 if side == "L" else -1
            f0 = 9 + k // 2
            spread = sx * (0.35 + 0.15 * (k // 2))

            def start_at(side=side, f0=f0):
                return C.carried(f"pod.{side}", f0, C.rig.data.bones[f"pod.{side}"].head_local)

            size(name, f0 - 1, 0.0)
            size(name, f0, 1.0)
            size(name, f0 + 12, 1.0)
            size(name, f0 + 13, 0.0)
            C.fly_path(name, [(f0, start_at), (f0 + 4, lambda s=start_at, sp=spread: s() + Vector((sp, 0.2, 0.6))), (f0 + 8, lambda s=start_at, sp=spread: s() + Vector((sp * 1.6, -1.6, 0.5))), (f0 + 12, lambda s=start_at: s() + Vector((0, -3.6, -0.4)))])
        pods(26, 1.0)
        stance(34)

    @clip("W", 34)
    def void_seeker():
        start()
        aim(6, up=2)
        rot("chest", 6, z=16)
        C.feet(6, (0.08, -0.16, 0, -20), (-0.07, 0.12, 0, 28))
        size("fx_flash", 6, 0.0)
        size("fx_flash", 13, 0.8)
        fire(14, "fx_seeker", 5.0, 2.0)
        aim(15, up=14, bend=22)
        rot("chest", 15, x=-4, z=12)
        aim(20)
        stance(34)

    @clip("E", 32)
    def supercharge():
        start()
        loc("hips", 5, z=-0.12)
        rot("spine", 5, x=16)
        pods(6, 0.6)
        size("fx_aura", 5, 0.0)
        size("fx_aura", 9, 1.3)
        for f in range(9, 25, 3):
            rot("fx_aura", f, z=30 * (f - 9))
        size("fx_aura", 24, 0.0)
        pods(24, 0.0)
        stance(32)

    @clip("R", 36)
    def killer_instinct():
        start()
        moving = bool(C.OPTIONS.get("root_motion"))
        reach = -2.0 if moving else 0.0
        # A void dash: crouch, streak forward, land shielded with the cannon raised.
        loc("hips", 4, z=-0.12)
        rot("spine", 4, x=20)
        pods(4, 0.8)
        loc("root", 4)
        loc("root", 10, y=reach, z=0.1)
        rot("spine", 8, x=30)
        for side in ("L", "R"):
            fk_arm(side, 8, up=30, swing=50, bend=40, hand=-10)
        C.feet(8, (0.05, 0.15, 0.15, -40), (-0.05, 0.25, 0.20, -50))
        size("fx_shield", 9, 0.0)
        size("fx_shield", 12, 1.1)
        size("fx_shield", 26, 1.0)
        size("fx_shield", 30, 0.0)
        aim(14)
        stance(36)
        for f in (12, 36):
            loc("root", f, y=reach)

    @clip("Recall", 48, loop=True)
    def recall():
        # Pods flex open and closed, a calm look at the arm cannon.
        for f, s_ in ((0, 0), (12, 1), (24, 0), (36, -1), (48, 0)):
            stance(f, breath=abs(s_), sway=0.3)
            fk_arm("R", f, up=30, swing=-60, bend=110, out=-20, twist=30, hand=-20)
            rot("head", f, x=10, z=-8)
            pods(f, 0.3 + 0.3 * abs(s_))
        fx_off(0)

    @clip("Death", 44)
    def death():
        start()
        C.fall_back(0, S)
