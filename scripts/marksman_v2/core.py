"""Shared Blender (bpy) toolkit for the SharpWR v2 marksman studies.

Every champion module (champions/<id>.py) builds an original stylized character with these
helpers: metaball body sculpted into one skinned mesh with clothing assigned by region, a head
with face features, hair and gear as separate parts, a humanoid rig (leg IK, weapon grip IK,
spring chains for hair, scarves and capes), authored clips, preview renders and a GLB export.

The character faces -Y; its left is +X. Units are metres, 24 fps.
"""

import math
from pathlib import Path

import bpy  # noqa: I001 (bpy first: it provides bmesh and mathutils)
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

FPS = 24
X90 = (math.pi / 2, 0, 0)

scene = None
M = {}  # material slots by key
PARTS = []  # (object, bone) rigid parts that follow one bone
SKINNED = []  # (object, weighting) extra meshes skinned to the rig
CHAINS = {}  # spring chains: name -> dict(bones, points, parent, stiffness, gain, limit, sway)
WEAPON_REST = {}  # weapon bone -> armature-space rest placement of the weapon (grip frame)
SOCKETS = {}  # empty name -> bone (effects attach to these in the app)
DEFORM_LATER = []  # extra bones that deform skinned props (bow strings) but not the body
J = {}  # joint positions
HEAD = Vector()
CLIPS = {}  # name -> (function, frames, loop)
OPTIONS = {}  # build options (e.g. root_motion for preview videos)
LATER = []  # callbacks run after a clip's keys are set (points carried by the final pose)
rig = PB = REST = REST3 = None


def new_scene():
    global scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = FPS
    for store in (M, CLIPS, CHAINS, WEAPON_REST, SOCKETS, J, OPTIONS):
        store.clear()
    PARTS.clear()
    SKINNED.clear()
    DEFORM_LATER.clear()
    return scene


# ---------------------------------------------------------------- materials


def srgb(hex_color):
    """'#rrggbb' to linear RGB."""
    h = hex_color.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i : i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def material(name, color, rough=0.5, metal=0.0, emission=0.0, sss=0.0, sheen=0.0, alpha=1.0):
    if isinstance(color, str):
        color = srgb(color)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if sss:
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = (0.9, 0.35, 0.25)
        p.inputs["Subsurface Scale"].default_value = 0.02
    if sheen:
        p.inputs["Sheen Weight"].default_value = sheen
    if emission:
        p.inputs["Emission Color"].default_value = (*color, 1)
        p.inputs["Emission Strength"].default_value = emission
    if alpha < 1.0:
        p.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    m.diffuse_color = (*color, alpha)
    return m


def striped(name, a, b, scale=110.0, axis="Z"):
    """Stripes along an object axis (world Z by default), e.g. for stockings."""
    a = srgb(a) if isinstance(a, str) else a
    b = srgb(b) if isinstance(b, str) else b
    m = material(name, a, rough=0.6)
    nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = scale
    sine = nt.nodes.new("ShaderNodeMath")
    sine.operation = "SINE"
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].color = (*a, 1)
    ramp.color_ramp.elements[1].position = 0.5
    ramp.color_ramp.elements[1].color = (*b, 1)
    to01 = nt.nodes.new("ShaderNodeMapRange")
    to01.inputs["From Min"].default_value = -1
    nt.links.new(tex.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs[axis], mul.inputs[0])
    nt.links.new(mul.outputs[0], sine.inputs[0])
    nt.links.new(sine.outputs[0], to01.inputs["Value"])
    nt.links.new(to01.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    return m


def face_materials(iris, lash="#050506", lip=(0.55, 0.25, 0.28), brow=None):
    """Eye white, iris, pupil/lash and lip materials shared by the human heads."""
    M.setdefault("white", material("Eye white", (0.92, 0.92, 0.95), rough=0.25))
    M["iris"] = material("Iris", iris, rough=0.2, emission=0.4)
    M["dark"] = material("Pupil and lashes", lash, rough=0.4)
    M["lip"] = material("Lips", lip, rough=0.45)
    if brow:
        M["brow"] = material("Brows", brow, rough=0.5)


# ---------------------------------------------------------------- joints


BASE_JOINTS = {
    "pelvis": (0, 0.0, 0.96),
    "spine": (0, 0.005, 1.10),
    "chest": (0, 0.005, 1.27),
    "neck": (0, 0.015, 1.41),
    "head": (0, 0.012, 1.47),
    # bone layout of the trunk
    "hips_bone": (0, 0, 0.93),
    "spine_bone": (0, 0.004, 1.05),
    "chest_bone": (0, 0.004, 1.20),
    "neck_bone": (0, 0.014, 1.37),
    "head_bone": (0, 0.013, 1.47),
    "head_top": (0, 0.013, 1.70),
}
BASE_SIDE = {
    "hip": (0.094, 0.0, 0.91),
    "knee": (0.100, -0.012, 0.50),
    "ankle": (0.100, 0.016, 0.085),
    "toe": (0.104, -0.135, 0.03),
    "clavicle": (0.03, 0.01, 1.36),
    "shoulder": (0.180, 0.012, 1.355),
    "elbow": (0.345, 0.020, 1.160),
    "wrist": (0.485, 0.008, 0.995),
    "hand": (0.545, -0.004, 0.925),
}
ARM = ("shoulder", "elbow", "wrist", "hand")
LEG = ("hip", "knee", "ankle", "toe")


def make_joints(scale=1.0, shoulder_x=0.180, hip_x=0.094, arm_length=1.0, leg_length=1.0):
    """A-pose joints (the Jinx study's proportions) scaled to a height, with shoulder and hip
    widths and limb length factors. Fills core.J and core.HEAD."""
    global HEAD
    J.clear()
    lift = (leg_length - 1.0) * 0.83  # longer legs raise everything above the hips
    for k, (x, y, z) in BASE_JOINTS.items():
        J[k] = Vector((x, y, z + lift)) * scale
    for side, sx in (("L", 1), ("R", -1)):
        for k, (x, y, z) in BASE_SIDE.items():
            co = Vector((x * sx, y, z))
            if k in ARM:
                co.x += (shoulder_x - 0.180) * sx
                co.z += lift
            elif k in LEG:
                co.x += (hip_x - 0.094) * sx
                co.z = 0.03 + (co.z - 0.03) * leg_length if k != "toe" else co.z
            else:
                co.z += lift
            J[f"{k}.{side}"] = co * scale
        if arm_length != 1.0:
            sh = J[f"shoulder.{side}"]
            for k in ARM[1:]:
                J[f"{k}.{side}"] = sh + (J[f"{k}.{side}"] - sh) * arm_length
    HEAD = Vector((0, 0.010, 1.585 + lift)) * scale
    return J


def side_x(side):
    return 1 if side == "L" else -1


# ---------------------------------------------------------------- metaballs and meshes

GAIN = 1.0 / 0.62  # field radius per visible radius for chained metaballs


def metaball_object(name, resolution=0.008):
    mb = bpy.data.metaballs.new(name)
    mb.resolution = mb.render_resolution = resolution
    mb.threshold = 0.6
    obj = bpy.data.objects.new(name, mb)
    scene.collection.objects.link(obj)
    return obj


def ball(obj, co, r, size=(1, 1, 1), stiffness=2.0, negative=False, rotation=None):
    """A metaball; size makes an ellipsoid, rotation (quaternion) turns its axes."""
    e = obj.data.elements.new()
    e.co = co
    e.radius = r * GAIN
    e.stiffness = stiffness
    e.use_negative = negative
    if tuple(size) != (1, 1, 1):
        e.type = "ELLIPSOID"
        e.size_x, e.size_y, e.size_z = size
    if rotation is not None:
        e.rotation = rotation
    return e


def chain(obj, a, b, ra, rb, step=0.022, depth=1.0, width=1.0):
    """Tapered limb: balls from a to b with linearly changing radius; depth scales Y."""
    a, b = Vector(a), Vector(b)
    count = max(2, int((b - a).length / step) + 1)
    for i in range(count):
        t = i / (count - 1)
        r = ra + (rb - ra) * t
        size = (width, depth, 1)
        ball(obj, a.lerp(b, t), r, size)


def activate(obj):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def apply_modifiers(obj):
    activate(obj)
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def decimate(obj, tris):
    """Collapse-decimate a mesh to about `tris` triangles (no-op when already lighter)."""
    count = triangles(obj)
    if tris and count > tris:
        d = obj.modifiers.new("Decimate", "DECIMATE")
        d.ratio = tris / count
        apply_modifiers(obj)


def triangles(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def smooth_shade(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


def mesh_from_meta(meta, name, voxel=0.004, smooth=4, tris=None):
    activate(meta)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.name = name
    if voxel:
        r = obj.modifiers.new("Remesh", "REMESH")
        r.mode = "VOXEL"
        r.voxel_size = voxel
    if smooth:
        c = obj.modifiers.new("Smooth", "CORRECTIVE_SMOOTH")
        c.iterations = smooth
        c.smooth_type = "LENGTH_WEIGHTED"
        c.use_only_smooth = True
    apply_modifiers(obj)
    decimate(obj, tris)
    smooth_shade(obj)
    return obj


def bisect(obj, cuts):
    """Cut mesh edges along planes (co, normal) so region materials get clean borders."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for co, no in cuts:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no)
    bm.to_mesh(obj.data)
    bm.free()


def paint_regions(obj, region, keys):
    """Assign the material keys returned by region(face_center) to an object's faces."""
    for key in keys:
        obj.data.materials.append(M[key])
    slots = {k: i for i, k in enumerate(keys)}
    for poly in obj.data.polygons:
        poly.material_index = slots[region(Vector(poly.center))]
        poly.use_smooth = True


def delete_faces(obj, test):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    gone = [f for f in bm.faces if test(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=gone, context="FACES")
    bm.to_mesh(obj.data)
    bm.free()


def solidify(obj, thickness, offset=-1.0):
    s = obj.modifiers.new("Thickness", "SOLIDIFY")
    s.thickness = thickness
    s.offset = offset
    apply_modifiers(obj)


def new_obj(name, mat, maker, **kw):
    maker(**kw)
    obj = bpy.context.object
    obj.name = name
    if mat:
        obj.data.materials.append(M[mat])
    smooth_shade(obj)
    return obj


def sphere(name, co, size, mat, bone="head", segments=32, rings=16, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=co, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(M[mat])
    smooth_shade(obj)
    if bone is not False:
        PARTS.append((obj, bone))
    return obj


def tube(name, points, radius, mat, bone="head", taper=None, resolution=12, bevel=4, flat=1.0):
    """Bezier tube through points; taper is a list of radius factors per point; flat < 1
    flattens the section (ribbons, strands of hair)."""
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = radius
    data.bevel_resolution = bevel
    data.resolution_u = resolution
    data.use_fill_caps = True
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for i, (bp, co) in enumerate(zip(spline.bezier_points, points)):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
        bp.radius = taper[i] if taper else 1.0
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.data.materials.append(M[mat])
    activate(obj)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    if flat != 1.0:
        flatten_tube(obj, points, flat)
    smooth_shade(obj)
    if bone is not False:
        PARTS.append((obj, bone))
    return obj


def flatten_tube(obj, points, flat):
    """Squash a tube's cross-section toward the surface normal of a head-like shape: each
    vertex moves toward the curve along the direction away from HEAD."""
    pts = [Vector(p) for p in points]
    for v in obj.data.vertices:
        nearest = min(pts, key=lambda p: (p - v.co).length)
        out = (nearest - HEAD).normalized()
        off = v.co - nearest
        along = off.dot(out)
        v.co -= out * along * (1 - flat)


def cyl(name, mat, radius, depth, loc=(0, 0, 0), rot=(0, 0, 0), vertices=24):
    return new_obj(name, mat, bpy.ops.mesh.primitive_cylinder_add, radius=radius, depth=depth, location=loc, rotation=rot, vertices=vertices)


def box(name, mat, size, loc=(0, 0, 0), bevel=0.01, rot=(0, 0, 0)):
    obj = new_obj(name, mat, bpy.ops.mesh.primitive_cube_add, size=1, location=loc, rotation=rot)
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = obj.modifiers.new("Bevel", "BEVEL")
        b.width = bevel
        b.segments = 3
        apply_modifiers(obj)
    smooth_shade(obj)
    return obj


def cone(name, mat, r1, r2, depth, loc, rot, vertices=8):
    return new_obj(name, mat, bpy.ops.mesh.primitive_cone_add, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot, vertices=vertices)


def torus(name, mat, major, minor, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), segments=32):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, location=loc, rotation=rot, major_segments=segments, minor_segments=10)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(M[mat])
    smooth_shade(obj)
    return obj


def ball_mesh(name, mat, co, size, segments=24, rings=12):
    obj = new_obj(name, mat, bpy.ops.mesh.primitive_uv_sphere_add, segments=segments, ring_count=rings, location=co)
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def plate(name, mat, points, thickness=0.01, offset=0.0):
    """A flat polygon (fins, feathers, blades) given as a loop of points, solidified."""
    data = bpy.data.meshes.new(name)
    data.from_pydata([tuple(p) for p in points], [], [tuple(range(len(points)))])
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    s = obj.modifiers.new("Solid", "SOLIDIFY")
    s.thickness = thickness
    s.offset = offset
    apply_modifiers(obj)
    obj.data.materials.append(M[mat])
    return obj


def lathe(name, mat, profile, segments=24, axis="Y", loc=(0, 0, 0)):
    """Surface of revolution: profile is (radius, position along axis) pairs."""
    verts, faces = [], []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        for r, t in profile:
            if axis == "Y":
                verts.append((math.cos(a) * r + loc[0], t + loc[1], math.sin(a) * r + loc[2]))
            elif axis == "Z":
                verts.append((math.cos(a) * r + loc[0], math.sin(a) * r + loc[1], t + loc[2]))
            else:
                verts.append((t + loc[0], math.cos(a) * r + loc[1], math.sin(a) * r + loc[2]))
    n = len(profile)
    for i in range(segments):
        j = (i + 1) % segments
        for k in range(n - 1):
            faces.append((i * n + k, j * n + k, j * n + k + 1, i * n + k + 1))
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.data.materials.append(M[mat])
    smooth_shade(obj)
    return obj


def join(objects, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    return obj


def place(obj, matrix):
    """Move an object built around the origin (barrel along -Y) to a world placement."""
    obj.matrix_world = matrix @ obj.matrix_world
    activate(obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def unpart(*objects):
    PARTS[:] = [(o, b) for o, b in PARTS if o not in objects]


def catmull(path, steps=10):
    """Densify a polyline with Catmull-Rom so shapes follow a smooth path."""
    path = [Vector(p) for p in path]
    pts = []
    for i in range(len(path) - 1):
        p0, p1, p2, p3 = path[max(i - 1, 0)], path[i], path[i + 1], path[min(i + 2, len(path) - 1)]
        for k in range(steps):
            t = k / steps
            pts.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t**3))
    pts.append(path[-1])
    return pts


def resample(points, count):
    """count + 1 evenly spaced points along a polyline (for a bone chain)."""
    pts = [Vector(p) for p in points]
    lengths = [0.0]
    for a, b in zip(pts, pts[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    out = []
    for i in range(count + 1):
        d = lengths[-1] * i / count
        k = max(j for j in range(len(lengths)) if lengths[j] <= d + 1e-9)
        k = min(k, len(pts) - 2)
        t = (d - lengths[k]) / max(1e-9, lengths[k + 1] - lengths[k])
        out.append(pts[k].lerp(pts[k + 1], t))
    return out


def ribbon(name, points, width, mat, side, thickness=0.006, taper=None, bone="head", steps=6, curl=0.0, curl_dir=(0, -1, 0), across=1):
    """A strip along a path (scarf ends, coat tails, capes, hair locks): its width spans `side`
    (a fixed direction, or a function of the point) across the path; curl bends the edges
    toward curl_dir (a cape wrapping the body), with `across` segments; solidified."""
    pts = catmull(points, steps)
    n = len(pts)
    widths = taper or [1.0] * len(points)
    across = max(1, across if curl else 1)
    verts, faces = [], []
    cols = across + 1
    for i, p in enumerate(pts):
        t = (i / (n - 1)) * (len(widths) - 1)
        k = min(int(t), len(widths) - 2)
        w = width * (widths[k] + (widths[k + 1] - widths[k]) * (t - k)) / 2
        tangent = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        d = Vector(side(p) if callable(side) else side)
        d = (d - tangent * d.dot(tangent)).normalized()
        for j in range(cols):
            u = j / across * 2 - 1
            verts.append(tuple(p + d * w * u + Vector(curl_dir) * curl * u * u * (w / max(width / 2, 1e-6))))
        if i:
            for j in range(across):
                a, b = (i - 1) * cols + j, i * cols + j
                faces.append((a, a + 1, b + 1, b))
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    if thickness:
        solidify(obj, thickness, 0.0)
    obj.data.materials.append(M[mat])
    smooth_shade(obj)
    if bone is not False:
        PARTS.append((obj, bone))
    return obj


def frame_along(origin, forward, up):
    """World matrix whose -Y axis points along `forward` and +Z toward `up` (weapon space)."""
    f = Vector(forward).normalized()
    z = Vector(up)
    z = (z - f * z.dot(f)).normalized()
    y = -f
    x = y.cross(z)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = Vector(origin)
    return m


# ---------------------------------------------------------------- body


def limbs(meta, r=None, arms=True, legs=True, neck=True, hands=True):
    """Neck, legs (thigh, calf bulge, ankle, foot) and arms with radii from r (defaults: the
    Jinx study, scaled with the skeleton)."""
    s = (J["head_top"].z) / 1.70
    d = dict(neck=(0.044, 0.037), thigh=(0.064, 0.041), calf=(0.041, 0.046, 0.028), foot=(0.036, 0.03), arm=(0.044, 0.032), forearm=(0.033, 0.024), palm=0.03)
    d.update(r or {})
    if neck:
        chain(meta, J["chest"] + Vector((0, 0.005, 0.10 * s)), J["head"], *(v * s for v in d["neck"]))
    for side in ("L", "R"):
        if legs:
            hip, knee, ankle, toe = (J[f"{n}.{side}"] for n in LEG)
            chain(meta, hip, knee, *(v * s for v in d["thigh"]))
            calf = knee.lerp(ankle, 0.32) + Vector((0, 0.018 * s, 0))
            chain(meta, knee, calf, d["thigh"][1] * s, d["calf"][1] * s)
            chain(meta, calf, ankle, d["calf"][1] * s, d["calf"][2] * s)
            chain(meta, ankle + Vector((0, 0.02, -0.04)) * s, toe, *(v * s for v in d["foot"]))
        if arms:
            sh, el, wr, hd = (J[f"{n}.{side}"] for n in ARM)
            chain(meta, sh, el, *(v * s for v in d["arm"]))
            chain(meta, el, wr, *(v * s for v in d["forearm"]))
            if hands == "mitten":  # palm, fingers and thumb, flat across the back-of-hand normal
                n = hand_normal(side)
                q = n.to_track_quat("Z", "Y")
                along = (hd - wr).normalized()
                ball(meta, wr.lerp(hd, 0.40), d["palm"] * s, (1.0, 1.15, 0.55), rotation=q)
                ball(meta, hd + along * 0.012 * s, d["palm"] * 0.78 * s, (0.95, 1.15, 0.5), rotation=q)
                thumb = wr.lerp(hd, 0.45) - n * 0.012 * s + Vector((0, -0.022 * s, 0))
                chain(meta, wr.lerp(hd, 0.2) + Vector((0, -0.012 * s, 0)), thumb, 0.012 * s, 0.009 * s, step=0.008)
            elif hands == "flat":  # palm flat across the back-of-hand normal
                ball(meta, wr.lerp(hd, 0.45), d["palm"] * s, (1.05, 1.0, 0.55), rotation=hand_normal(side).to_track_quat("Z", "Y"))
            elif hands:
                ball(meta, wr.lerp(hd, 0.45), d["palm"] * s, (1.0, 0.55, 1.0))


def hand_normal(side):
    """Back-of-hand direction in the A-pose: across the forearm, outward and up."""
    f = (J[f"hand.{side}"] - J[f"wrist.{side}"]).normalized()
    return Vector((-f.z * side_x(side), 0, abs(f.x))).normalized()


def torso_female(meta, s=1.0, bust=1.0, hips=1.0, waist=1.0):
    """Slender female torso (the Jinx study): hips, buttocks, waist, ribcage, chest, bust and
    shoulder line, scaled by s."""

    lift = J["pelvis"].z / s - 0.96  # longer legs raise the torso

    def b(x, y, z):
        return Vector((x, y, z + lift)) * s

    ball(meta, b(0, 0.004, 0.95), 0.13 * s * hips, (1.0, 0.70, 0.62))
    for sx in (1, -1):
        ball(meta, b(0.058 * sx * hips, 0.045, 0.915), 0.07 * s * hips, (1.0, 0.95, 1.05))
    ball(meta, b(0, 0.006, 1.05), 0.10 * s * waist, (1.0, 0.76, 0.8))
    ball(meta, b(0, 0.006, 1.12), 0.093 * s * waist, (1.0, 0.78, 0.8))
    ball(meta, b(0, 0.004, 1.21), 0.118 * s, (1.0, 0.76, 0.9))
    ball(meta, b(0, 0.010, 1.30), 0.13 * s, (1.0, 0.66, 0.6))
    for sx in (1, -1):
        ball(meta, b(0.052 * sx, -0.045, 1.255), 0.05 * s * bust, (1.0, 0.95, 0.92))
        ball(meta, b(0.11 * sx, 0.012, 1.345), 0.05 * s, (1.25, 0.8, 0.6))


def torso_male(meta, s=1.0, chest=1.0, waist=1.0, shoulders=1.0):
    """Lean male torso (the Ezreal study): pelvis, waist, ribcage, chest, pecs, deltoids and
    trapezius, scaled by s; shoulders widens the deltoids for broader builds."""

    lift = J["pelvis"].z / s - 0.96

    def b(x, y, z):
        return Vector((x, y, z + lift)) * s

    ball(meta, b(0, 0.004, 0.95), 0.118 * s, (1.0, 0.74, 0.62))
    for sx in (1, -1):
        ball(meta, b(0.05 * sx, 0.04, 0.915), 0.06 * s)
    ball(meta, b(0, 0.006, 1.04), 0.105 * s * waist, (1.0, 0.76, 0.8))
    ball(meta, b(0, 0.004, 1.12), 0.108 * s * waist, (1.0, 0.76, 0.85))
    ball(meta, b(0, 0.006, 1.21), 0.128 * s * chest, (1.0, 0.74, 0.9))
    ball(meta, b(0, 0.012, 1.30), 0.142 * s * chest, (1.05, 0.68, 0.6))
    for sx in (1, -1):
        ball(meta, b(0.058 * sx * chest, -0.035, 1.265), 0.058 * s * chest, (1.15, 0.7, 0.75))
        ball(meta, b(0.155 * sx * shoulders, 0.012, 1.345), 0.058 * s * shoulders, (1.2, 0.9, 0.75))
        ball(meta, b(0.07 * sx * shoulders, 0.03, 1.375), 0.045 * s, (1.3, 0.9, 0.7))


def body_mesh(meta, name, region, keys, cuts=(), voxel=0.006, tris=20000):
    """Metaballs -> voxel remesh -> smooth -> decimate -> cut along region borders -> paint."""
    obj = mesh_from_meta(meta, name, voxel=voxel, smooth=6, tris=tris)
    bisect(obj, cuts)
    paint_regions(obj, region, keys)
    return obj


def arm_fraction(c, side):
    """How far a point lies along the arm, 0 at the shoulder and 1 at the hand."""
    sh, hd = J[f"shoulder.{side}"], J[f"hand.{side}"]
    axis = hd - sh
    return (Vector(c) - sh).dot(axis.normalized()) / axis.length


def arm_cut(side, fraction):
    sh, hd = J[f"shoulder.{side}"], J[f"hand.{side}"]
    return (sh.lerp(hd, fraction), (hd - sh).normalized())


def leg_fraction(c, side):
    hip, ankle = J[f"hip.{side}"], J[f"ankle.{side}"]
    axis = ankle - hip
    return (Vector(c) - hip).dot(axis.normalized()) / axis.length


# ---------------------------------------------------------------- head and face


def build_head(name="Head", jaw=1.0, chin=1.0, cheek=1.0, nose=1.0, ears=1.0, width=1.0, tris=6000, extra=None):
    """Cranium, cheeks/jaw, chin, nose and ears; extra(meta, h) adds champion-specific balls."""
    meta = metaball_object(name, resolution=0.005)
    h = HEAD
    s = h.z / 1.585
    ball(meta, h + Vector((0, 0.012, 0.012)) * 1, 0.098 * s, (0.93 * width, 1.0, 1.03))
    ball(meta, h + Vector((0, -0.022, -0.045 * jaw)) * 1, 0.074 * s * cheek, (0.92 * width * jaw, 0.86, 0.85 * jaw))
    ball(meta, h + Vector((0, -0.052, -0.088 * jaw)) * 1, 0.030 * s * chin, (1.0 * jaw, 0.9, 0.9))
    ball(meta, h + Vector((0, -0.094, -0.022)), 0.012 * s * nose, (0.8, 1.0, 1.4))
    if ears:
        for sx in (1, -1):
            ball(meta, h + Vector((0.092 * sx * width, 0.012, -0.012)), 0.022 * s * ears, (0.45, 0.8, 1.25))
    if extra:
        extra(meta, h)
    head = mesh_from_meta(meta, name, voxel=0.0035, smooth=4, tris=tris)
    head.data.materials.append(M["skin"])
    PARTS.append((head, "head"))
    bpy.context.view_layer.update()
    return head


def build_face(eye_size=1.0, lashes="winged", brow_mat="dark", brow_width=0.0018, brow_lift=0.0, brow_angle=0.0, mouth="smirk", eye_gap=1.0, eye_y=0.0, mouth_width=1.0, mouth_size=0.0016, mouth_y=0.0):
    """Eyes (white, iris, pupil, catchlight), lash lines, brows and mouth on core.HEAD.
    lashes: winged (feminine liner), soft (thin) or none; brow_angle tilts brows (frown > 0)."""
    h = HEAD
    e = eye_size
    for sx in (1, -1):
        eye = h + Vector((0.037 * sx * eye_gap, -0.079, eye_y))
        sphere("Eye white", eye, (0.022 * e, 0.012, 0.016 * e), "white")
        sphere("Iris", eye + Vector((0.002 * sx, -0.010, -0.001)), (0.0115 * e, 0.004, 0.0125 * e), "iris")
        sphere("Pupil", eye + Vector((0.002 * sx, -0.0135, -0.001)), (0.005 * e, 0.002, 0.0062 * e), "dark")
        sphere("Catchlight", eye + Vector((-0.002 * sx, -0.0152, 0.004 * e)), (0.0022, 0.001, 0.0022), "white")
        if lashes != "none":
            lash = [eye + Vector((x * sx * e, -0.010 + abs(x) * 0.2, (0.011 - (x / 0.026) ** 2 * 0.011) * e)) for x in (-0.024, -0.012, 0.0, 0.013, 0.027)]
            if lashes == "winged":
                lash[-1] += Vector((0.004 * sx, 0, 0.006))
            width = 0.0022 if lashes == "winged" else 0.0014
            tube("Lash line", lash, width, "dark", taper=[0.6, 1.0, 1.2, 1.0, 0.5])
        brow = [
            eye + Vector((x * sx, -0.006, 0.030 * e + brow_lift + 0.004 * (1 - (x / 0.022) ** 2) - brow_angle * x))
            for x in (-0.018, 0.0, 0.022)
        ]
        tube("Brow", brow, brow_width, brow_mat, taper=[0.7, 1.0, 0.5])
    w = mouth_width
    if mouth == "smirk":
        pts = [h + Vector((x * w, -0.088 + abs(x) * 0.25, -0.052 + (0.003 if x > 0.01 else 0))) for x in (-0.016, -0.004, 0.008, 0.019)]
    elif mouth == "smile":
        pts = [h + Vector((x * w, -0.088 + abs(x) * 0.25, -0.052 + (x / 0.02) ** 2 * 0.004)) for x in (-0.018, -0.006, 0.006, 0.018)]
    else:  # flat
        pts = [h + Vector((x * w, -0.088 + abs(x) * 0.25, -0.052)) for x in (-0.016, -0.005, 0.005, 0.016)]
    pts = [p + Vector((0, mouth_y, 0)) for p in pts]
    tube("Mouth", pts, mouth_size, "lip", taper=[0.5, 1, 1, 0.5])


def surface(obj, origin, target, offset=0.0):
    """Where a ray from origin toward target hits a mesh, pushed out along the normal (for
    details that must sit on a sculpted surface: beards, straps, markings)."""
    origin, target = Vector(origin), Vector(target)
    inv = obj.matrix_world.inverted()
    hit, co, normal, _ = obj.ray_cast(inv @ origin, (inv.to_3x3() @ (target - origin)).normalized())
    if not hit:
        return None
    return obj.matrix_world @ (co + normal * offset)


def scale_parts(bone, factor, pivot):
    """Scale every rigid part on a bone about a pivot (e.g. a stylized, larger head)."""
    m = Matrix.Translation(pivot) @ Matrix.Scale(factor, 4) @ Matrix.Translation(-Vector(pivot))
    for obj, b in PARTS:
        if b == bone:
            place(obj, m)


def clump(meta, points, r0, r1, step=0.010, flat=1.0):
    """A tapered hair clump along a smooth path, merged into a metaball hair mass."""
    pts = catmull(points, 8)
    lengths = [0.0]
    for a, b in zip(pts, pts[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    total = lengths[-1]
    d = 0.0
    while d <= total:
        k = max(j for j in range(len(lengths)) if lengths[j] <= d + 1e-9)
        k = min(k, len(pts) - 2)
        t = (d - lengths[k]) / max(1e-9, lengths[k + 1] - lengths[k])
        co = pts[k].lerp(pts[k + 1], t)
        u = d / total
        r = r0 + (r1 - r0) * u
        if flat != 1.0:
            out = (co - HEAD).normalized()
            q = out.to_track_quat("Z", "Y")
            ball(meta, co, r, (1.0, 1.0, flat), rotation=q)
        else:
            ball(meta, co, r)
        d += max(step, r * 0.6)


def braid_lobes(path, mats=("hair", "hair_dark"), radius=0.034, taper=0.55, twist=38, segments=12):
    """A braid: alternating twisted lobes along a smooth path; returns the lobe objects (not
    in PARTS: attach them to a chain with attach_to_chain)."""
    pts = catmull(path)
    lobes = []
    for i in range(2, len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        frac = i / len(pts)
        r = radius * (1 - taper * frac)
        obj = sphere("Braid lobe", (a + b) / 2, (r * 0.85, r * 0.65, (b - a).length * 1.25), mats[i % 2], False, segments=segments, rings=8)
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = (b - a).normalized().to_track_quat("Z", "Y") @ Matrix.Rotation(math.radians(twist if i % 2 else -twist), 4, "Y").to_quaternion()
        lobes.append(obj)
    return lobes


def hair_cap(name, mat, front_y=0.035, front_z=0.055, scale=1.0, back=1.0, tris=2600, thickness=0.006, extra=None):
    """Hair shell over the cranium with the face cut away in front of the hairline."""
    meta = metaball_object(name, resolution=0.005)
    h = HEAD
    ball(meta, h + Vector((0, 0.022, 0.032)), 0.104 * scale, (0.98, 1.0, 1.0))
    ball(meta, h + Vector((0, 0.05, -0.01)), 0.09 * scale * back, (1.0, 0.9, 1.0))
    if extra:
        extra(meta, h)
    cap = mesh_from_meta(meta, name, voxel=0.0045, smooth=3, tris=tris)
    delete_faces(cap, lambda c: c.y < h.y - front_y and c.z < h.z + front_z)
    solidify(cap, thickness)
    cap.data.materials.append(M[mat])
    PARTS.append((cap, "head"))
    return cap


# ---------------------------------------------------------------- shared gear and effects


def coat_panels(specs, mat, s=1.0, thickness=0.009):
    """Coat tails hanging from the waist, each on a spring chain: specs are
    (name, x, y, width, top z, bottom z, flare) in base units; side panels (|x| > 0.1) span
    front-to-back. Returns name -> (points, mesh)."""
    out = {}
    for name, x, y, w, top, bottom, flare in specs:
        sx = 1 if x > 0 else -1
        side = abs(x) > 0.1
        n = 4
        pts = []
        for i in range(n):
            t = i / (n - 1)
            z = top + (bottom - top) * t
            pts.append(Vector((x + flare * t * sx * (1 if side else 0.3), y + (0.05 if not side else 0.01) * t, z)) * s)
        panel = ribbon(f"Coat {name}", pts, w * s, mat, (0, 1, 0) if side else (1, 0, 0), thickness, [1.0, 1.08, 1.15, 1.18], bone=False)
        out[name] = (pts, panel)
    return out


def coat_chains(panels, parent="hips", **options):
    """Spring chains and skinning for coat_panels."""
    opts = dict(skin=True, stiffness=60, gain=0.8, sway=2.0, limit=(40, 20))
    opts.update(options)
    chains = []
    for name, (pts, panel) in panels.items():
        chains.append((name, resample(pts, 3), parent, opts))
        SKINNED.append((panel, [parent] + [f"{name}.{i}" for i in range(3)]))
    return chains


def fx_flash(name, radius, mat, spikes=5):
    """A muzzle flash or burst: a glowing core with spikes thrown forward (-Y)."""
    parts = [ball_mesh(f"FX {name}", mat, (0, 0, 0), (radius, radius * 1.6, radius), 16, 8)]
    for i in range(spikes):
        a = i * 2 * math.pi / spikes
        parts.append(cone("FX spike", mat, radius * 0.35, 0.0, radius * 3.2, (math.cos(a) * radius * 0.8, -radius * 1.8, math.sin(a) * radius * 0.8), (math.pi / 2 + 0.35 * math.sin(a), 0.35 * math.cos(a), 0), 4))
    return join(parts, f"FX {name}")


def fx_bolt(name, length, radius, mat, core_mat=None, rings=0):
    """A projectile along -Y: glowing spindle with a tapering trail behind it."""
    parts = [lathe(f"FX {name}", mat, [(0.0, -length * 0.5), (radius, -length * 0.3), (radius * 0.8, 0.0), (radius * 0.35, length * 0.5), (0.0, length * 0.9)], 16)]
    if core_mat:
        parts.append(ball_mesh("FX core", core_mat, (0, -length * 0.25, 0), (radius * 0.6, length * 0.25, radius * 0.6), 12, 6))
    for k in range(rings):
        parts.append(torus("FX ring", mat, radius * 1.4, radius * 0.12, (0, length * (0.15 + 0.25 * k), 0), (math.pi / 2, 0, 0), (1, 1, 1), 16))
    return join(parts, f"FX {name}")


def fx_beam(name, length, radius, mat, core_mat=None):
    """A straight beam from the origin along -Y."""
    parts = [cyl(f"FX {name}", mat, radius, length, (0, -length / 2, 0), X90, 16)]
    if core_mat:
        parts.append(cyl("FX beam core", core_mat, radius * 0.45, length * 1.01, (0, -length / 2, 0), X90, 10))
    return join(parts, f"FX {name}")


def fx_orb(name, radius, mat, rings=2):
    parts = [ball_mesh(f"FX {name}", mat, (0, 0, 0), (radius, radius, radius), 20, 10)]
    for k in range(rings):
        parts.append(torus("FX orb ring", mat, radius * (1.6 - 0.1 * k), radius * 0.08, (0, 0, 0), (math.pi / 2 - 1.2 * k, 0.4 + 0.8 * k, 0), (1, 1, 1), 24))
    return join(parts, f"FX {name}")


def fx_bones(fx, default):
    """Place effect meshes and return their bones: fx maps bone -> (object, matrix or None,
    parent); a None matrix uses `default` (unparented effects fly in armature space)."""
    rows = []
    for name, (obj, matrix, parent) in fx.items():
        m = matrix if matrix is not None else default
        place(obj, m)
        rows.append(point_bone(name, m, parent))
    return rows


def shoot_from(name, frame_from, frame_to, start, direction=(0, -1, 0), distance=3.0):
    """Show a projectile bone between two frames, flying from start() along a direction; the
    path is solved after the clip's other keys (start may read the final pose)."""
    size(name, frame_from - 1, 0.0)
    size(name, frame_from, 1.0)
    size(name, frame_to, 1.0)
    size(name, frame_to + 1, 0.0)

    def fly():
        co = start()
        d = (direction() if callable(direction) else Vector(direction)).normalized()
        turn = Vector((0, -1, 0)).rotation_difference(d).to_matrix()  # meshes face -Y at rest
        r = turn @ rig.data.bones[name].matrix_local.to_3x3()
        put(name, frame_from, co, r)
        put(name, frame_to, co + d * distance, r)

    LATER.append(fly)


def fly_path(name, keys, axis=(0, 0, 1), turns_per_frame=0.0):
    """Key an unparented effect bone every frame along (frame, point) pairs (a point may be a
    callable read after the clip's keys), spinning about a world axis (thrown blades)."""

    def fly():
        pts = [(f, co() if callable(co) else Vector(co)) for f, co in keys]
        start = pts[0][0]
        rest = rig.data.bones[name].matrix_local.to_3x3()
        pb = PB[name]
        prev = None
        for (f0, a), (f1, b) in zip(pts, pts[1:]):
            for f in range(f0, f1 + 1):
                co = a.lerp(b, (f - f0) / max(1, f1 - f0))
                r = Matrix.Rotation(2 * math.pi * turns_per_frame * (f - start), 3, Vector(axis)) @ rest
                scene.frame_set(f)
                bpy.context.view_layer.update()
                pb.matrix = Matrix.Translation(co) @ r.to_4x4()
                q = pb.rotation_quaternion.copy()
                if prev is not None and prev.dot(q) < 0:
                    q.negate()
                pb.rotation_quaternion = q
                prev = q
                pb.keyframe_insert("location", frame=f)
                pb.keyframe_insert("rotation_quaternion", frame=f)

    LATER.append(fly)


# ---------------------------------------------------------------- rig


def build_rig(name, chains=(), extra=(), arm_iks=()):
    """Humanoid skeleton from core.J with leg IK, plus:
    chains: (chain name, points, parent bone, options) -> bones '<name>.<i>' (spring follow-through)
    extra: (bone, head, tail, parent) non-deforming bones (weapons, grips, flashes, props)
    arm_iks: (side, label, target bone) -> forearm IK constraints 'IK <label>' (influence 0)."""
    global rig, PB, REST, REST3
    data = bpy.data.armatures.new(name)
    rig = bpy.data.objects.new(name, data)
    scene.collection.objects.link(rig)
    activate(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = data.edit_bones

    def bone(bname, head, tail, parent=None, deform=True, roll=0.0):
        b = eb.new(bname)
        b.head, b.tail = Vector(head), Vector(tail)
        b.roll = roll
        b.use_deform = deform
        if parent:
            b.parent = eb[parent]
        return b

    s = J["head_top"].z / 1.70
    bone("root", (0, 0, 0), (0, 0.25 * s, 0), deform=False)
    bone("hips", J["hips_bone"], J["spine_bone"] - Vector((0, 0.004, 0)), "root")
    bone("spine", J["spine_bone"], J["chest_bone"], "hips")
    bone("chest", J["chest_bone"], J["neck_bone"] - Vector((0, 0.006, 0)), "spine")
    bone("neck", J["neck_bone"], J["head_bone"], "chest")
    bone("head", J["head_bone"], J["head_top"], "neck")
    for side, sx in (("L", 1), ("R", -1)):
        bone(f"shoulder.{side}", J[f"clavicle.{side}"], J[f"shoulder.{side}"], "chest")
        bone(f"upper_arm.{side}", J[f"shoulder.{side}"], J[f"elbow.{side}"], f"shoulder.{side}")
        bone(f"forearm.{side}", J[f"elbow.{side}"], J[f"wrist.{side}"], f"upper_arm.{side}")
        bone(f"hand.{side}", J[f"wrist.{side}"], J[f"hand.{side}"], f"forearm.{side}")
        bone(f"thigh.{side}", J[f"hip.{side}"], J[f"knee.{side}"], "hips")
        bone(f"shin.{side}", J[f"knee.{side}"], J[f"ankle.{side}"], f"thigh.{side}")
        bone(f"foot.{side}", J[f"ankle.{side}"], J[f"toe.{side}"], f"shin.{side}")
        # Controls, aligned with the world axes (pointing +Y, no roll) so offsets read as world moves.
        ankle = J[f"ankle.{side}"]
        bone(f"ik_foot.{side}", ankle, ankle + Vector((0, 0.12, 0)), "root", deform=False)
        knee = J[f"knee.{side}"]
        pk = Vector((knee.x * 1.1, -0.55 * s, knee.z))
        bone(f"pole_knee.{side}", pk, pk + Vector((0, 0.12, 0)), "root", deform=False)
        pe = Vector((0.42 * sx * s + (J[f"shoulder.{side}"].x - 0.18 * sx * s), 0.45 * s, J[f"elbow.{side}"].z - 0.06 * s))
        bone(f"pole_elbow.{side}", pe, pe + Vector((0, 0.12, 0)), "root", deform=False)
    for cname, points, parent, options in chains:
        pts = [Vector(p) for p in points]
        names = []
        prev = parent
        for i in range(len(pts) - 1):
            bname = f"{cname}.{i}"
            bone(bname, pts[i], pts[i + 1], prev, deform=options.get("deform", False))
            prev = bname
            names.append(bname)
        CHAINS[cname] = dict(
            bones=names,
            points=pts,
            parent=parent,
            stiffness=options.get("stiffness", 70.0),
            damping=options.get("damping", 7.0),
            gain=options.get("gain", 0.9),
            limit=options.get("limit", (35.0, 25.0)),
            sway=options.get("sway", 0.0),
            scale=options.get("scale", 0.5),
            skin=options.get("skin", False),
        )
    for bname, head, tail, parent in extra:
        bone(bname, head, tail, parent, deform=False)
    bpy.ops.object.mode_set(mode="POSE")
    PB = rig.pose.bones
    for p in PB:
        p.rotation_mode = "QUATERNION"
    for side in ("L", "R"):
        ik = PB[f"shin.{side}"].constraints.new("IK")
        ik.target, ik.subtarget = rig, f"ik_foot.{side}"
        ik.pole_target, ik.pole_subtarget = rig, f"pole_knee.{side}"
        ik.pole_angle = math.radians(-90)
        ik.chain_count = 2
        cr = PB[f"foot.{side}"].constraints.new("COPY_ROTATION")
        cr.target, cr.subtarget = rig, f"ik_foot.{side}"
        cr.mix_mode = "BEFORE"
        cr.target_space = cr.owner_space = "LOCAL"
    for side, label, target in arm_iks:
        ik = PB[f"forearm.{side}"].constraints.new("IK")
        ik.name = f"IK {label}"
        ik.target, ik.subtarget = rig, target
        ik.pole_target, ik.pole_subtarget = rig, f"pole_elbow.{side}"
        ik.pole_angle = math.radians(-90)
        ik.chain_count = 2
        ik.influence = 0.0
    bpy.ops.object.mode_set(mode="OBJECT")
    REST = {b.name: b.matrix_local.to_quaternion() for b in rig.data.bones}
    REST3 = {b.name: b.matrix_local.to_3x3() for b in rig.data.bones}
    return rig


def build_creature_rig(name, bones, legs=(), chains=(), extra=()):
    """A free-form skeleton for creatures (dragons, six-legged beasts):
    bones: (name, head, tail, parent, deform) rows (a root bone is added first);
    legs: (prefix, upper, lower, ankle point, pole point) -> an IK control 'ik_<prefix>' and a
    pole 'pole_<prefix>' (both under root) with a 2-bone 'Leg IK' on the lower bone;
    chains and extra as in build_rig."""
    global rig, PB, REST, REST3
    data = bpy.data.armatures.new(name)
    rig = bpy.data.objects.new(name, data)
    scene.collection.objects.link(rig)
    activate(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = data.edit_bones

    def bone(bname, head, tail, parent=None, deform=True):
        b = eb.new(bname)
        b.head, b.tail = Vector(head), Vector(tail)
        b.use_deform = deform
        if parent:
            b.parent = eb[parent]
        return b

    bone("root", (0, 0, 0), (0, 0.25, 0), deform=False)
    for bname, head, tail, parent, deform in bones:
        bone(bname, head, tail, parent or "root", deform)
    for prefix, upper, lower, ankle, pole in legs:
        ankle, pole = Vector(ankle), Vector(pole)
        bone(f"ik_{prefix}", ankle, ankle + Vector((0, 0.08, 0)), "root", deform=False)
        bone(f"pole_{prefix}", pole, pole + Vector((0, 0.08, 0)), "root", deform=False)
    for cname, points, parent, options in chains:
        pts = [Vector(p) for p in points]
        names, prev = [], parent
        for i in range(len(pts) - 1):
            bname = f"{cname}.{i}"
            bone(bname, pts[i], pts[i + 1], prev, deform=options.get("deform", False))
            prev = bname
            names.append(bname)
        CHAINS[cname] = dict(
            bones=names,
            points=pts,
            parent=parent,
            stiffness=options.get("stiffness", 70.0),
            damping=options.get("damping", 7.0),
            gain=options.get("gain", 0.9),
            limit=options.get("limit", (35.0, 25.0)),
            sway=options.get("sway", 0.0),
            scale=options.get("scale", 0.5),
            skin=options.get("skin", False),
        )
    for bname, head, tail, parent in extra:
        bone(bname, head, tail, parent, deform=False)
    bpy.ops.object.mode_set(mode="POSE")
    PB = rig.pose.bones
    for p in PB:
        p.rotation_mode = "QUATERNION"
    for prefix, upper, lower, ankle, pole in legs:
        ik = PB[lower].constraints.new("IK")
        ik.name = "Leg IK"
        ik.target, ik.subtarget = rig, f"ik_{prefix}"
        ik.pole_target, ik.pole_subtarget = rig, f"pole_{prefix}"
        ik.pole_angle = math.radians(-90)
        ik.chain_count = 2
    bpy.ops.object.mode_set(mode="OBJECT")
    REST = {b.name: b.matrix_local.to_quaternion() for b in rig.data.bones}
    REST3 = {b.name: b.matrix_local.to_3x3() for b in rig.data.bones}
    return rig


def bone_frame(head, direction, length=0.1):
    """(head, tail) for a bone at `head` pointing along a world direction."""
    head = Vector(head)
    return head, head + Vector(direction).normalized() * length


def weapon_bones(weapon, rest, grip=(0, 0, 0), parent="hips", length=0.2):
    """A weapon bone at its rest placement (grip frame, barrel toward -Y in weapon space);
    returns the extra-bone row and registers the rest placement for placement()."""
    WEAPON_REST[weapon] = rest
    co = rest @ Vector(grip)
    return (weapon, co, co + (rest.to_3x3() @ Vector((0, -1, 0))) * length, parent)


def point_bone(name, matrix, parent, length=0.05, direction=(0, -1, 0)):
    co = matrix.to_translation()
    return (name, co, co + (matrix.to_3x3() @ Vector(direction)) * length, parent)


def grip_bone(name, co, parent):
    co = Vector(co)
    return (name, co, co + Vector((0, 0.06, 0)), parent)


def skin_nearest(obj, bones, power=4.0, keep=3):
    """Weights by distance to bone segments (smooth envelope); for clothing panels."""
    segs = []
    for name in bones:
        b = rig.data.bones[name]
        segs.append((name, b.head_local.copy(), b.tail_local.copy()))
    groups = {name: obj.vertex_groups.new(name=name) for name in bones}
    for v in obj.data.vertices:
        co = obj.matrix_world @ v.co
        scores = []
        for name, a, b in segs:
            ab = b - a
            t = max(0.0, min(1.0, (co - a).dot(ab) / max(ab.length_squared, 1e-9)))
            d = (a + ab * t - co).length
            scores.append((1.0 / max(d, 1e-4) ** power, name))
        scores.sort(reverse=True)
        top = scores[:keep]
        total = sum(w for w, _ in top)
        for w, name in top:
            groups[name].add([v.index], w / total, "REPLACE")
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    obj.parent = rig


def skin_custom(obj, weighting):
    groups = {}
    for v in obj.data.vertices:
        for name, w in weighting(obj.matrix_world @ v.co).items():
            if name not in groups:
                groups[name] = obj.vertex_groups.new(name=name)
            groups[name].add([v.index], w, "REPLACE")
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    obj.parent = rig


def bind(body):
    """Skin the body (automatic weights) and extra skinned meshes; parent rigid parts."""
    activate(rig)
    body.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    # Chains that carry skinned cloth deform only after the body has its weights.
    for c in CHAINS.values():
        if c["skin"]:
            for name in c["bones"]:
                rig.data.bones[name].use_deform = True
    for name in DEFORM_LATER:
        rig.data.bones[name].use_deform = True
    for obj, weighting in SKINNED:
        if callable(weighting):  # weighting(world co) -> {bone: weight}
            skin_custom(obj, weighting)
        elif weighting == "auto":
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            rig.select_set(True)
            bpy.context.view_layer.objects.active = rig
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        else:
            skin_nearest(obj, weighting)
    for obj, bone_name in PARTS:
        attach(obj, bone_name or "head")
    for name, (bone_name, matrix) in SOCKETS.items():
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_size = 0.03
        scene.collection.objects.link(empty)
        empty.matrix_world = matrix
        attach(empty, bone_name)


def attach(obj, bone_name):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    obj.matrix_world = world


def attach_to_chain(obj, chain_name):
    """Parent a part to the chain bone nearest to it."""
    c = CHAINS[chain_name]
    pts = c["points"]
    idx = min(range(len(c["bones"])), key=lambda i: (pts[i].lerp(pts[i + 1], 0.5) - obj.matrix_world.translation).length)
    attach(obj, c["bones"][idx])


# ---------------------------------------------------------------- posing


def world_quat(name, x=0.0, y=0.0, z=0.0):
    q_world = Euler((math.radians(x), math.radians(y), math.radians(z)), "XYZ").to_quaternion()
    r = REST[name]
    return r.inverted() @ q_world @ r


def rot(name, frame=None, x=0.0, y=0.0, z=0.0):
    """Rotate a bone about world axes (as seen in the rest pose); key it when frame is given."""
    rotq(name, frame, Euler((math.radians(x), math.radians(y), math.radians(z)), "XYZ").to_quaternion())


def rotq(name, frame, q_world):
    pb = PB[name]
    r = REST[name]
    q = r.inverted() @ q_world @ r
    if pb.rotation_quaternion.dot(q) < 0:
        q.negate()
    pb.rotation_quaternion = q
    if frame is not None:
        pb.keyframe_insert("rotation_quaternion", frame=frame)


def loc(name, frame=None, x=0.0, y=0.0, z=0.0):
    """Move a bone by a world-axis offset from its rest position."""
    pb = PB[name]
    pb.location = REST3[name].inverted() @ Vector((x, y, z))
    if frame is not None:
        pb.keyframe_insert("location", frame=frame)


def size(name, frame=None, value=1.0):
    pb = PB[name]
    pb.scale = (value, value, value)
    if frame is not None:
        pb.keyframe_insert("scale", frame=frame)


def ik(side, label, frame=None, value=1.0):
    c = PB[f"forearm.{side}"].constraints[f"IK {label}"]
    c.influence = value
    if frame is not None:
        c.keyframe_insert("influence", frame=frame)


def iks_off(frame, side=None):
    for s in (side,) if side else ("L", "R"):
        for c in PB[f"forearm.{s}"].constraints:
            if c.name.startswith("IK "):
                c.influence = 0.0
                c.keyframe_insert("influence", frame=frame)


def leg_ik(frame, value=1.0):
    """Blend the leg IK on or off (off: the legs follow the hips in FK, e.g. tucked in a roll)."""
    for pb in PB:
        for c in pb.constraints:
            if c.type == "IK" and (pb.name.startswith("shin") or c.name == "Leg IK"):
                c.influence = value
                c.keyframe_insert("influence", frame=frame)


def spin_about(frame, angle, axis, pivot, offset=(0, 0, 0)):
    """Key the root so the whole character turns by angle (degrees) about an axis through a
    pivot point (e.g. a roll about the hips), plus an extra world offset."""
    q = Quaternion(Vector(axis).normalized(), math.radians(angle))
    pivot = Vector(pivot)
    pb = PB["root"]
    pb.rotation_quaternion = REST["root"].inverted() @ q @ REST["root"]
    pb.keyframe_insert("rotation_quaternion", frame=frame)
    loc("root", frame, *(pivot - q @ pivot + Vector(offset)))


def reset_pose():
    for pb in PB:
        pb.rotation_euler = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
        for c in pb.constraints:
            if c.name.startswith("IK ") and pb.name.startswith("forearm"):
                c.influence = 0.0
            elif c.type == "IK" and (pb.name.startswith("shin") or c.name == "Leg IK"):
                c.influence = 1.0


def fk_arm(side, frame, up=0.0, swing=0.0, bend=0.0, out=0.0, hand=None, twist=0.0):
    """Free arm (IK off): lower it toward the body (up raises it), swing it forward (negative)
    or back (positive) about the shoulder, turn it out, twist it inward about its own axis
    (twist > 0: a bent forearm turns toward the body) and bend the elbow."""
    sx = side_x(side)
    sh, el = J[f"shoulder.{side}"], J[f"elbow.{side}"]
    rest_drop = math.degrees(math.atan2(sh.z - el.z, abs(el.x - sh.x)))
    lower = Quaternion((0, 1, 0), math.radians(sx * (87.76 - rest_drop - up)))  # up=0: arm hangs
    swing_q = Quaternion((1, 0, 0), math.radians(swing))
    out_q = Quaternion((0, 0, 1), math.radians(sx * out))
    arm = (J[f"elbow.{side}"] - J[f"shoulder.{side}"]).normalized()
    twist_q = Quaternion(arm, math.radians(sx * twist))
    rotq(f"upper_arm.{side}", frame, out_q @ swing_q @ lower @ twist_q)
    hinge = arm.cross(Vector((0, -1, 0))).normalized()
    rotq(f"forearm.{side}", frame, Quaternion(hinge, math.radians(bend)))
    rotq(f"hand.{side}", frame, Quaternion(hinge, math.radians(bend * 0.25 if hand is None else hand)))


def weapon_matrix(name, matrix, frame):
    """Key a bone so it sits at an armature-space placement on this frame."""
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    PB[name].matrix = matrix
    bpy.context.view_layer.update()
    PB[name].keyframe_insert("location", frame=frame)
    PB[name].keyframe_insert("rotation_quaternion", frame=frame)


def put(name, frame, co, rotation=None):
    """Key a bone so its head sits at an armature-space point (rest orientation unless given)."""
    r = rotation if rotation is not None else rig.data.bones[name].matrix_local.to_3x3()
    weapon_matrix(name, Matrix.Translation(co) @ r.to_4x4(), frame)


def carried(bone, frame, rest_co):
    """Where a point at rest_co (armature space, rest pose) is carried by a bone at a frame."""
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    return PB[bone].matrix @ (rig.data.bones[bone].matrix_local.inverted() @ Vector(rest_co))


def weapon_frame(weapon, bone_matrix):
    """The weapon's own frame (barrel -Y, up +Z) for a weapon bone placement."""
    return bone_matrix @ rig.data.bones[weapon].matrix_local.inverted() @ WEAPON_REST[weapon]


def weapon_offset(weapon, child, frame, offset):
    """Key a child bone of a weapon (e.g. a bow's nock) shifted by an offset given in the
    weapon's own frame (barrel -Y, up +Z); constant in the parent's space, so it holds
    wherever the weapon is placed."""
    d = WEAPON_REST[weapon].to_3x3() @ Vector(offset)
    loc(child, frame, *d)


def rest_matrix(name):
    return rig.data.bones[name].matrix_local.copy()


def placement(weapon, translation, rx=0.0, ry=0.0, rz=0.0, roll=0.0):
    """Armature-space matrix for a weapon bone that puts the weapon's grip at a point with a
    pitch up (rx), tilt about world Y (ry) and turn (rz) in degrees from facing forward (-Y),
    upright; roll turns the weapon about its own barrel first."""
    turn = (
        Matrix.Rotation(math.radians(rz), 3, "Z")
        @ Matrix.Rotation(math.radians(ry), 3, "Y")
        @ Matrix.Rotation(math.radians(-rx), 3, "X")
        @ Matrix.Rotation(math.radians(roll), 3, "Y")
    )
    rest_bone = rig.data.bones[weapon].matrix_local.to_3x3()
    rest_weapon = WEAPON_REST[weapon].to_3x3()
    rotation = turn @ rest_weapon.inverted() @ rest_bone
    return Matrix.Translation(translation) @ rotation.to_4x4()


def flash(name, frame, length=2, peak=1.0):
    size(name, frame - 1, 0.0)
    size(name, frame, peak)
    size(name, frame + length, 0.0)


def hide(names, frame, value=0.0):
    for n in names:
        size(n, frame, value)


def feet(frame, left=(0, 0, 0, 0), right=(0, 0, 0, 0)):
    """Key both IK feet: (x, y, z offset, turn about Z in degrees)."""
    for side, (x, y, z, turn) in (("L", left), ("R", right)):
        loc(f"ik_foot.{side}", frame, x=x, y=y, z=z)
        rot(f"ik_foot.{side}", frame, z=turn)


# ---------------------------------------------------------------- clips


RUN_LEGS = [
    # frame, (y, z, toe pitch) for the leading foot, then the trailing foot
    (0, (-0.30, 0.02, 10), (0.32, 0.16, -55)),
    (2, (-0.12, 0.0, 0), (0.24, 0.32, -40)),
    (4, (0.06, 0.0, -5), (-0.02, 0.30, -10)),
    (6, (0.24, 0.07, -35), (-0.24, 0.18, 15)),
]
RUN_BOB = {0: -0.05, 2: -0.085, 4: -0.03, 6: 0.0}


def run_cycle(upper, scale=1.0, lean=10.0, twist=10.0, stride=1.0):
    """An 18-frame run loop (contact, down, passing, up, mirrored): legs, hips, spine and head;
    upper(frame, lead_side, phase) keys the arms and anything held (phase: 1 at contact ->
    -0.55 before the next contact)."""
    phases = {0: 1.0, 2: 0.8, 4: 0.1, 6: -0.55}
    for half, (lead, trail) in enumerate((("L", "R"), ("R", "L"))):
        for f, a, b in RUN_LEGS:
            frame = f + 9 * half
            for side, (y, z, toe) in ((lead, a), (trail, b)):
                loc(f"ik_foot.{side}", frame, x=0.02 * side_x(side), y=y * scale * stride, z=z * scale)
                rot(f"ik_foot.{side}", frame, x=toe)
            t = twist if lead == "L" else -twist
            loc("hips", frame, z=RUN_BOB[f] * scale, y=-0.02)
            rot("hips", frame, z=t, y=(3 if lead == "L" else -3))
            rot("spine", frame, x=lean, z=-t * 0.6)
            rot("chest", frame, x=lean * 0.45, z=-t * 0.55)
            rot("head", frame, x=-lean * 0.85 + (2 if f == 2 else 0), z=t * 0.33)
            upper(frame, lead, phases[f])
    # The loop closes on the first key.
    a, b = RUN_LEGS[0][1], RUN_LEGS[0][2]
    loc("ik_foot.L", 18, x=0.02, y=a[0] * scale * stride, z=a[1] * scale)
    rot("ik_foot.L", 18, x=a[2])
    loc("ik_foot.R", 18, x=-0.02, y=b[0] * scale * stride, z=b[1] * scale)
    rot("ik_foot.R", 18, x=b[2])
    loc("hips", 18, z=RUN_BOB[0] * scale, y=-0.02)
    rot("hips", 18, z=twist, y=3)
    rot("spine", 18, x=lean, z=-twist * 0.6)
    rot("chest", 18, x=lean * 0.45, z=-twist * 0.55)
    rot("head", 18, x=-lean * 0.85, z=twist * 0.33)
    upper(18, "L", 1.0)


def fall_back(start_frame=0, scale=1.0, arms=True):
    """Death: hit, stagger, knees give way, fall on the back (from a keyed start pose)."""
    f0 = start_frame
    rot("chest", f0 + 3, x=-14, z=8)
    rot("head", f0 + 3, x=-18, z=-6)
    if arms:
        fk_arm("L", f0 + 6, up=-20, swing=25, bend=40, out=10)
        fk_arm("R", f0 + 6, up=-15, swing=25, bend=50)
    loc("ik_foot.R", f0 + 9, x=-0.04, y=0.22 * scale)
    loc("hips", f0 + 9, y=0.05, z=-0.06 * scale)
    loc("hips", f0 + 16, y=0.08, z=-0.30 * scale)
    rot("spine", f0 + 16, x=14)
    rot("chest", f0 + 16, x=8)
    rot("head", f0 + 16, x=12, z=-10)
    rot("root", f0 + 16)
    rot("root", f0 + 30, x=-88)
    loc("root", f0 + 30, y=0.25 * scale, z=0.12 * scale)
    loc("hips", f0 + 30, z=-0.20 * scale)
    rot("spine", f0 + 30, x=-4)
    rot("chest", f0 + 30, x=-6)
    rot("head", f0 + 33, x=-6, z=-25)
    if arms:
        fk_arm("L", f0 + 30, up=-60, swing=-30, bend=10, out=30)
        fk_arm("R", f0 + 30, up=-50, swing=-20, bend=15, out=-20)
    rot("root", f0 + 34, x=-92)
    rot("root", f0 + 44, x=-90)
    loc("root", f0 + 44, y=0.25 * scale, z=0.12 * scale)


def later(fn):
    """Run fn after the clip's other keys are set (e.g. projectiles leaving a moving muzzle)."""
    LATER.append(fn)
    return fn


def clip(name, frames, loop=False):
    def register(fn):
        CLIPS[name] = (fn, frames, loop)
        return fn

    return register


def follow_through(frames, loop):
    """Damped springs along every chain, driven by the acceleration of the chain's parent bone:
    hair, scarves and capes lag, overshoot and settle instead of moving rigidly."""
    if not CHAINS:
        return
    cycles = 3 if loop else 1
    parents = {c["parent"] for c in CHAINS.values()}
    positions = {p: [] for p in parents}
    for _ in range(cycles):
        for f in range(frames + 1):
            scene.frame_set(f)
            for p in parents:
                positions[p].append((rig.matrix_world @ PB[p].matrix).translation.copy())
    dt = 1 / FPS
    for cname, c in CHAINS.items():
        pos = positions[c["parent"]]
        n = len(c["bones"])
        state = [[0.0, 0.0, 0.0, 0.0] for _ in range(n)]
        result = []
        for i in range(len(pos)):
            prev, cur, nxt = pos[max(i - 1, 0)], pos[i], pos[min(i + 1, len(pos) - 1)]
            acc = (nxt - 2 * cur + prev) / (dt * dt)
            drive_x, drive_y = -acc.y * c["gain"], acc.x * c["gain"]
            angles = []
            for k, seg in enumerate(state):
                stiffness = c["stiffness"] - 5.0 * k * c["stiffness"] / 70.0
                seg[1] += (-stiffness * seg[0] - c["damping"] * seg[1] + drive_x) * dt
                seg[0] += seg[1] * dt
                seg[3] += (-stiffness * seg[2] - c["damping"] * seg[3] + drive_y) * dt
                seg[2] += seg[3] * dt
                drive_x, drive_y = seg[0] * stiffness * 0.55, seg[2] * stiffness * 0.55
                angles.append((math.degrees(seg[0]), math.degrees(seg[2])))
            result.append(angles)
        offset = (cycles - 1) * (frames + 1)
        lx, ly = c["limit"]
        for f in range(frames + 1):
            phase = 2 * math.pi * f / frames if frames else 0.0
            for k, (ax, ay) in enumerate(result[offset + f]):
                # A gentle sway (whole cycles over the clip, so loops stay seamless).
                wave = c["sway"] * math.sin(phase - 0.6 * k) * (k + 1) / n
                ax = max(-lx, min(lx, ax)) * c["scale"] + wave
                ay = max(-ly, min(ly, ay)) * c["scale"] + wave * 0.4
                rot(c["bones"][k], f, x=ax, y=ay)


def complete_channels(action):
    """Give every bone channel and IK influence a key in this action (rest values where the
    clip never set them), so no pose leaks from one clip into the next, in Blender or in the
    app's animation mixer."""
    have = {(fc.data_path, fc.array_index) for fc in action.fcurves}
    for pb in PB:
        base = f'pose.bones["{pb.name}"]'
        rot_path = "rotation_euler" if pb.rotation_mode == "XYZ" else "rotation_quaternion"
        for path, rest in (("location", (0, 0, 0)), (rot_path, (0, 0, 0) if rot_path == "rotation_euler" else (1, 0, 0, 0)), ("scale", (1, 1, 1))):
            for i, value in enumerate(rest):
                if (f"{base}.{path}", i) not in have:
                    fc = action.fcurves.new(f"{base}.{path}", index=i, action_group=pb.name)
                    fc.keyframe_points.insert(0, value)
        for c in pb.constraints:
            if c.type == "IK" or c.name.startswith("IK "):
                path = f'{base}.constraints["{c.name}"].influence'
                if (path, 0) not in have:
                    rest = 1.0 if pb.name.startswith("shin") or c.name == "Leg IK" else 0.0
                    action.fcurves.new(path, index=0, action_group=pb.name).keyframe_points.insert(0, rest)


def build_clips(names=None):
    rig.animation_data_create()
    actions = {}
    for name, (fn, frames, loop) in CLIPS.items():
        if names and name not in names:
            continue
        action = bpy.data.actions.new(name)
        rig.animation_data.action = action
        reset_pose()
        fn()
        for callback in LATER:
            callback()
        LATER.clear()
        follow_through(frames, loop)
        complete_channels(action)
        action.use_frame_range = True
        action.frame_start, action.frame_end = 0, frames
        action.use_fake_user = True
        actions[name] = action
    return actions


# ---------------------------------------------------------------- stage, renders, export


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def stage(rim=(1.0, 0.45, 0.85), height=1.0):
    world = bpy.data.worlds.new("Stage")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.016, 0.026, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "Floor"
    floor.data.materials.append(material("Floor", (0.03, 0.035, 0.045), rough=0.7))
    for name, loc_, energy, size_, color in (
        ("Key", (2.2, -2.6, 3.0), 450, 2.0, (1.0, 0.93, 0.86)),
        ("Fill", (-2.8, -1.5, 1.8), 220, 3.0, (0.65, 0.78, 1.0)),
        ("Rim", (0.4, 2.6, 2.6), 520, 1.5, rim),
    ):
        bpy.ops.object.light_add(type="AREA", location=Vector(loc_) * height)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy * height * height
        light.data.size = size_ * height
        light.data.color = rim if name == "Rim" else color
        look_at(light, (0, 0, 1.0 * height))
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.data.lens = 50
    scene.camera = cam
    return cam


def configure_render(args, exposure=0.0):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = int(args.get("samples", 24))
    scene.cycles.use_denoising = True
    scene.render.resolution_x = int(args.get("width", 420))
    scene.render.resolution_y = int(args.get("height", 560))
    scene.render.threads_mode = "FIXED"
    scene.render.threads = int(args.get("threads", 2))
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = exposure
    if args.get("fast"):
        # Preview video: few bounces, adaptive sampling, cached scene data between frames.
        scene.cycles.max_bounces = 3
        scene.cycles.diffuse_bounces = 2
        scene.cycles.glossy_bounces = 1
        scene.cycles.transmission_bounces = 0
        scene.cycles.transparent_max_bounces = 2
        scene.cycles.caustics_reflective = scene.cycles.caustics_refractive = False
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.05
        scene.render.use_persistent_data = True
        for m in bpy.data.materials:
            if m.use_nodes and "Principled BSDF" in m.node_tree.nodes:
                m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.0


def frame_camera(camera, angle_deg, distance=3.1, height=1.05, target_z=0.9, scale=1.0):
    a = math.radians(angle_deg)
    camera.location = (math.sin(a) * distance * scale, -math.cos(a) * distance * scale, height * scale)
    look_at(camera, (0, 0, target_z * scale))


VIEWS = {
    "front": dict(angle_deg=0),
    "side": dict(angle_deg=90),
    "three_quarter": dict(angle_deg=35),
    "back": dict(angle_deg=180),
    "face": dict(angle_deg=20, distance=0.85, height=1.62, target_z=1.58),
    "face_side": dict(angle_deg=75, distance=0.85, height=1.62, target_z=1.58),
}
CLIP_VIEW = dict(angle_deg=28, distance=3.3, height=1.15, target_z=0.85)


def shoot(camera, path, view, scale=1.0):
    frame_camera(camera, scale=scale, **view)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def render_clip(camera, actions, name, out, view=CLIP_VIEW, every=1, scale=1.0):
    """Render a clip's frames to out/frames/<name>/####.png."""
    action = actions[name]
    rig.animation_data.action = action
    folder = Path(out) / "frames" / name.replace(" ", "_")
    folder.mkdir(parents=True, exist_ok=True)
    for f in range(int(action.frame_start), int(action.frame_end) + 1, every):
        scene.frame_set(f)
        # Follow root motion (preview videos) so the character stays framed.
        follow = PB["root"].head.copy()
        follow.z *= 0.5  # half of any jump, so leaps stay in frame but still read as height
        frame_camera(camera, scale=scale, **view)
        camera.location += follow
        look_at(camera, Vector((0, 0, view.get("target_z", 0.9) * scale)) + follow)
        scene.render.filepath = str(folder / f"{f:04d}.png")
        bpy.ops.render.render(write_still=True)


def stats(label=""):
    meshes = [o for o in rig.children_recursive if o.type == "MESH"]
    total = sum(triangles(o) for o in meshes)
    print(f"STATS {label}: {len(meshes)} meshes, {total} triangles")
    for o in sorted(meshes, key=triangles, reverse=True)[:12]:
        print(f"  {o.name:28s} {triangles(o):7d}")
    return total


def merge_parts():
    """Join the rigid parts that follow the same bone into one mesh (fewer draw calls)."""
    groups = {}
    for o in rig.children:
        if o.type == "MESH" and o.parent_type == "BONE":
            groups.setdefault(o.parent_bone, []).append(o)
    for bone_name, objects in groups.items():
        if len(objects) > 1:
            join(objects, f"{bone_name} parts")


def reduce_to(budget, keep=("body",)):
    """Decimate every mesh except the skinned body by one ratio so the total fits a budget."""
    meshes = [o for o in rig.children_recursive if o.type == "MESH"]
    fixed = sum(triangles(o) for o in meshes if any(k in o.name.lower() for k in keep))
    rest = [o for o in meshes if not any(k in o.name.lower() for k in keep)]
    flexible = sum(triangles(o) for o in rest)
    if flexible and fixed + flexible > budget:
        ratio = max(0.15, (budget - fixed) / flexible)
        for o in rest:
            if triangles(o) > 64:
                decimate_first(o, ratio)


def decimate_first(obj, ratio):
    """Collapse-decimate a mesh's base shape only: the decimation goes first in the stack and
    is the only modifier applied, so a skinned mesh keeps its armature and weights."""
    d = obj.modifiers.new("Decimate", "DECIMATE")
    d.ratio = ratio
    activate(obj)
    bpy.ops.object.modifier_move_to_index(modifier=d.name, index=0)
    bpy.ops.object.modifier_apply(modifier=d.name)


def skin_parts():
    """One skinned mesh for the app: every rigid part (parented to a bone) becomes geometry
    weighted fully to that bone and is joined, with the other skinned meshes, into the body
    (one skin and one draw call per material instead of one per part)."""
    rig.data.pose_position = "REST"
    bpy.context.view_layer.update()
    meshes = [o for o in rig.children_recursive if o.type == "MESH"]
    skinned = [o for o in meshes if any(m.type == "ARMATURE" for m in o.modifiers)]
    body = max(skinned, key=triangles)
    for o in meshes:
        if o.parent_type == "BONE":
            bone, world = o.parent_bone, o.matrix_world.copy()
            o.parent = None
            o.matrix_world = world
            activate(o)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            group = o.vertex_groups.new(name=bone)
            group.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
            rig.data.bones[bone].use_deform = True
    others = [o for o in meshes if o is not body]
    if others:
        body = join([body] + others, body.name)
    body.data.validate()
    rig.data.pose_position = "POSE"
    bpy.context.view_layer.update()


def prune_bones():
    """Remove leaf bones the app never needs (effect, flash and prop helpers): non-deforming,
    childless, carrying no object (sockets) and not an IK target or pole."""
    used = {"root"}
    for pb in rig.pose.bones:
        for c in pb.constraints:
            used.update(n for n in (getattr(c, "subtarget", ""), getattr(c, "pole_subtarget", "")) if n)
    used.update(o.parent_bone for o in rig.children if o.parent_type == "BONE")
    activate(rig)
    bpy.ops.object.mode_set(mode="EDIT")
    bones = rig.data.edit_bones
    pruned = True
    while pruned:
        pruned = False
        for b in list(bones):
            if not b.use_deform and not b.children and b.name not in used:
                bones.remove(b)
                pruned = True
    bpy.ops.object.mode_set(mode="OBJECT")
    names = {b.name for b in rig.data.bones}
    for action in bpy.data.actions:
        for fc in list(action.fcurves):
            if fc.data_path.startswith('pose.bones["') and fc.data_path.split('"')[1] not in names:
                action.fcurves.remove(fc)


def drop_fx():
    """Effect meshes (names starting with 'FX ') are for preview videos; the app draws its own."""
    for o in list(rig.children_recursive):
        if o.name.startswith("FX "):
            bpy.data.objects.remove(o, do_unlink=True)


def export_glb(path, actions, first="Idle"):
    """Rig, its children and every action in one GLB (sampled, deforming bones only)."""
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    for child in rig.children_recursive:
        child.select_set(True)
    bpy.context.view_layer.objects.active = rig
    rig.animation_data.action = actions.get(first)
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_force_sampling=True,
        export_def_bones=False,
        export_optimize_animation_size=True,
        export_skins=True,
        export_yup=True,
        export_cameras=False,
        export_lights=False,
    )
    print("exported", path)
