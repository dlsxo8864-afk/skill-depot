"""
clay_lib.py - Reusable procedural clay character and studio set library for Blender 5.2+.
Part of the 퇴근각 clay renewal system.
"""

import os
import math
from typing import Dict, Any, Tuple, Optional, List

try:
    import bpy
    import mathutils
    from mathutils import Vector, Quaternion, Euler, Matrix
except ImportError:
    bpy = None
    mathutils = None
    Vector = None
    Quaternion = None
    Euler = None
    Matrix = None


MATERIAL_CACHE: Dict[str, Any] = {}


def ensure_bpy():
    if bpy is None:
        raise RuntimeError("clay_lib must be executed within Blender (bpy is not available).")


def get_or_create_collection(col_name: str, parent_collection: Optional[Any] = None) -> Any:
    ensure_bpy()
    if col_name in bpy.data.collections:
        return bpy.data.collections[col_name]
    col = bpy.data.collections.new(col_name)
    parent = parent_collection if parent_collection is not None else bpy.context.scene.collection
    parent.children.link(col)
    return col


def link_to_collection(obj: Any, target_col: Any):
    for cur_col in list(obj.users_collection):
        cur_col.objects.unlink(obj)
    target_col.objects.link(obj)


def create_clay_material(
    name: str,
    rgba: Tuple[float, float, float, float],
    roughness: float = 0.62,
    specular: float = 0.20,
    subsurface: float = 0.04,
    subsurface_color: Optional[Tuple[float, float, float, float]] = None
) -> Any:
    ensure_bpy()
    if name in MATERIAL_CACHE and MATERIAL_CACHE[name].name in bpy.data.materials:
        mat = MATERIAL_CACHE[name]
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = rgba
            bsdf.inputs["Roughness"].default_value = roughness
        return mat

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.name = "Principled BSDF"
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = roughness

    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = specular

    if subsurface > 0.0:
        if "Subsurface Weight" in bsdf.inputs:
            bsdf.inputs["Subsurface Weight"].default_value = subsurface
            if subsurface_color and "Subsurface Color" in bsdf.inputs:
                bsdf.inputs["Subsurface Color"].default_value = subsurface_color
        elif "Subsurface" in bsdf.inputs:
            bsdf.inputs["Subsurface"].default_value = subsurface
            if subsurface_color and "Subsurface Color" in bsdf.inputs:
                bsdf.inputs["Subsurface Color"].default_value = subsurface_color

    out = nodes.new(type="ShaderNodeOutputMaterial")
    out.location = (260, 0)
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    MATERIAL_CACHE[name] = mat
    return mat


def create_empty(
    name: str,
    location: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    parent: Optional[Any] = None,
    collection: Optional[Any] = None,
    display_type: str = "PLAIN_AXES",
    size: float = 0.08
) -> Any:
    ensure_bpy()
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = display_type
    empty.empty_display_size = size
    empty.location = location
    empty.rotation_euler = rotation
    target_col = collection if collection else bpy.context.scene.collection
    target_col.objects.link(empty)
    if parent:
        empty.parent = parent
    return empty


def create_beveled_box(
    name: str,
    size: Tuple[float, float, float],
    location: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    bevel_width: float = 0.015,
    segments: int = 3,
    material: Optional[Any] = None,
    parent: Optional[Any] = None,
    collection: Optional[Any] = None
) -> Any:
    ensure_bpy()
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.0))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.location = location
    obj.rotation_euler = rotation

    if bevel_width > 0:
        bev = obj.modifiers.new(name="Bevel", type="BEVEL")
        bev.width = bevel_width
        bev.segments = segments
        bev.profile = 0.7

    bpy.ops.object.shade_smooth()
    if material:
        obj.data.materials.append(material)
    if collection:
        link_to_collection(obj, collection)
    if parent:
        obj.parent = parent
    return obj


def create_sphere(
    name: str,
    radius: float,
    location: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    material: Optional[Any] = None,
    parent: Optional[Any] = None,
    collection: Optional[Any] = None,
    segments: int = 24,
    ring_count: int = 16
) -> Any:
    ensure_bpy()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=(0.0, 0.0, 0.0), segments=segments, ring_count=ring_count)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.location = location
    bpy.ops.object.shade_smooth()
    if material:
        obj.data.materials.append(material)
    if collection:
        link_to_collection(obj, collection)
    if parent:
        obj.parent = parent
    return obj


def create_cylinder(
    name: str,
    radius: float,
    depth: float,
    location: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    bevel_width: float = 0.008,
    material: Optional[Any] = None,
    parent: Optional[Any] = None,
    collection: Optional[Any] = None,
    vertices: int = 24
) -> Any:
    ensure_bpy()
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=(0.0, 0.0, 0.0), vertices=vertices)
    obj = bpy.context.active_object
    obj.name = name
    obj.location = location
    obj.rotation_euler = rotation
    if bevel_width > 0:
        bev = obj.modifiers.new(name="Bevel", type="BEVEL")
        bev.width = bevel_width
        bev.segments = 2
    bpy.ops.object.shade_smooth()
    if material:
        obj.data.materials.append(material)
    if collection:
        link_to_collection(obj, collection)
    if parent:
        obj.parent = parent
    return obj


def create_clay_curve(
    name: str,
    points: List[Tuple[float, float, float]],
    thickness: float = 0.01,
    material: Optional[Any] = None,
    parent: Optional[Any] = None,
    collection: Optional[Any] = None,
    cyclic: bool = False,
    resolution: int = 12
) -> Any:
    ensure_bpy()
    curve_data = bpy.data.curves.new(name, type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = resolution
    curve_data.bevel_depth = thickness
    curve_data.bevel_resolution = 3

    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for pt, co in zip(spline.bezier_points, points):
        pt.co = co
        pt.handle_left_type = "AUTO"
        pt.handle_right_type = "AUTO"
    spline.use_cyclic_u = cyclic

    obj = bpy.data.objects.new(name, curve_data)
    target_col = collection if collection else bpy.context.scene.collection
    target_col.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    if parent:
        obj.parent = parent
    return obj


def solve_two_bone(upper: Any, lower: Any, target_world: Any, l1: float, l2: float, bend_axis: Any):
    ensure_bpy()
    bpy.context.view_layer.update()
    origin = upper.matrix_world.translation.copy()
    vector = Vector(target_world) - origin
    dist = max(0.001, min(vector.length, (l1 + l2) - 0.001))
    direction = vector.normalized()

    bend_vec = Vector(bend_axis)
    perp = bend_vec - direction * bend_vec.dot(direction)
    if perp.length < 0.01:
        perp = direction.cross(Vector((0.0, 0.0, 1.0)))
        if perp.length < 0.01:
            perp = direction.cross(Vector((1.0, 0.0, 0.0)))
    perp.normalize()

    along = (l1 * l1 - l2 * l2 + dist * dist) / (2.0 * dist)
    height = math.sqrt(max(0.0, l1 * l1 - along * along))
    joint = origin + direction * along + perp * height

    upper_world_q = (joint - origin).to_track_quat("-Z", "Y")
    if upper.parent:
        upper.rotation_quaternion = upper.parent.matrix_world.to_quaternion().inverted() @ upper_world_q
    else:
        upper.rotation_quaternion = upper_world_q

    bpy.context.view_layer.update()
    lower_target_vec = Vector(target_world) - joint
    lower_world_q = lower_target_vec.to_track_quat("-Z", "Y")
    lower.rotation_quaternion = upper.matrix_world.to_quaternion().inverted() @ lower_world_q


def build_character_mesh(
    char_id: str,
    spec: Dict[str, Any],
    collection: Any
) -> Dict[str, Any]:
    ensure_bpy()
    p = spec["proportions"]
    h_spec = spec["hair"]
    s_spec = spec["skin"]
    o_spec = spec["outfit"]

    skin_mat = create_clay_material(
        f"mat_skin_{char_id}",
        tuple(s_spec["color"]),
        roughness=s_spec.get("roughness", 0.60),
        specular=s_spec.get("specular", 0.22)
    )
    blush_mat = create_clay_material(
        f"mat_blush_{char_id}",
        tuple(s_spec.get("blush_color", [0.86, 0.52, 0.50, 1.0])),
        roughness=0.65,
        specular=0.18
    )
    hair_mat = create_clay_material(
        f"mat_hair_{char_id}",
        tuple(h_spec["color"]),
        roughness=h_spec.get("roughness", 0.66),
        specular=h_spec.get("specular", 0.18)
    )
    top_mat = create_clay_material(
        f"mat_top_{char_id}",
        tuple(o_spec["top_color"]),
        roughness=0.68,
        specular=0.15
    )
    bot_mat = create_clay_material(
        f"mat_bot_{char_id}",
        tuple(o_spec["bottom_color"]),
        roughness=0.70,
        specular=0.14
    )
    shoe_mat = create_clay_material(
        f"mat_shoe_{char_id}",
        tuple(o_spec["shoe_color"]),
        roughness=0.55,
        specular=0.25
    )
    eye_white_mat = create_clay_material(f"mat_eye_white_{char_id}", (0.97, 0.97, 0.96, 1.0), roughness=0.35, specular=0.45)
    eye_pupil_mat = create_clay_material(f"mat_eye_pupil_{char_id}", (0.05, 0.05, 0.06, 1.0), roughness=0.25, specular=0.60)
    eye_high_mat = create_clay_material(f"mat_eye_high_{char_id}", (1.0, 1.0, 1.0, 1.0), roughness=0.10, specular=0.90)
    mouth_mat = create_clay_material(f"mat_mouth_{char_id}", (0.42, 0.14, 0.14, 1.0), roughness=0.50, specular=0.25)

    char_col = get_or_create_collection(f"Char_{char_id}", collection)

    root = create_empty(f"{char_id}_root", location=(0.0, 0.0, 0.0), collection=char_col, display_type="SINGLE_ARROW", size=0.2)

    leg_len = p["leg_length"]
    shoe_h = p["shoe_height"]
    hips_z = leg_len + shoe_h * 0.5 + .05

    hips = create_empty(f"{char_id}_hips", location=(0.0, 0.0, hips_z), parent=root, collection=char_col, display_type="SPHERE", size=0.12)

    pelvis_w = p["shoulder_width"] * 0.78
    pelvis = create_beveled_box(
        f"{char_id}_pelvis",
        size=(pelvis_w, 0.22, 0.18),
        location=(0.0, 0.0, 0.0),
        bevel_width=0.035,
        segments=4,
        material=bot_mat,
        parent=hips,
        collection=char_col
    )

    torso_len = p["torso_length"]
    chest_z = torso_len * 0.75
    chest = create_empty(f"{char_id}_chest", location=(0.0, 0.0, chest_z), parent=hips, collection=char_col, display_type="SPHERE", size=0.10)

    torso = create_beveled_box(
        f"{char_id}_torso",
        size=(p["shoulder_width"], 0.24, torso_len * 0.95),
        location=(0.0, 0.0, torso_len * 0.45),
        bevel_width=0.04,
        segments=4,
        material=top_mat,
        parent=hips,
        collection=char_col
    )

    if o_spec.get("collar_color"):
        collar_mat = create_clay_material(f"mat_collar_{char_id}", tuple(o_spec["collar_color"]), roughness=0.65, specular=0.18)
        create_clay_curve(
            f"{char_id}_collar",
            [(-0.06, -0.11, 0.02), (0.0, -0.13, -0.05), (0.06, -0.11, 0.02)],
            thickness=0.012,
            material=collar_mat,
            parent=chest,
            collection=char_col
        )

    neck_z = torso_len + 0.02
    neck = create_cylinder(
        f"{char_id}_neck",
        radius=0.048,
        depth=0.09,
        location=(0.0, 0.0, neck_z),
        material=skin_mat,
        parent=hips,
        collection=char_col
    )

    head_ctrl = create_empty(f"{char_id}_head", location=(0.0, 0.0, neck_z + 0.025), parent=hips, collection=char_col, display_type="ARROWS", size=0.14)

    head_rx, head_ry, head_rz = p["head_scale"]
    head_mesh = create_sphere(
        f"{char_id}_head_mesh",
        radius=head_rx,
        location=(0.0, 0.0, head_rz * 0.85),
        scale=(1.0, head_ry / head_rx, head_rz / head_rx),
        material=skin_mat,
        parent=head_ctrl,
        collection=char_col
    )

    nose = create_sphere(
        f"{char_id}_nose",
        radius=0.016,
        location=(0.0, -head_ry * 0.98, head_rz * 0.82),
        scale=(0.9, 1.2, 0.9),
        material=skin_mat,
        parent=head_ctrl,
        collection=char_col
    )

    for side, sign in (("L", 1.0), ("R", -1.0)):
        create_sphere(
            f"{char_id}_ear_{side}",
            radius=0.026,
            location=(sign * (head_rx * 0.98), 0.0, head_rz * 0.82),
            scale=(0.4, 0.8, 1.2),
            material=skin_mat,
            parent=head_ctrl,
            collection=char_col
        )
        create_sphere(
            f"{char_id}_blush_{side}",
            radius=0.024,
            location=(sign * (head_rx * 0.52), -head_ry * 0.92, head_rz * 0.72),
            scale=(1.2, 0.3, 0.8),
            material=blush_mat,
            parent=head_ctrl,
            collection=char_col
        )

    eye_spacing = p["eye_spacing"]
    eye_r = p["eye_radius"]
    eye_z = head_rz * 0.85
    eye_y = -head_ry * 0.93

    eyes_rig = {}
    for side, sign in (("L", 1.0), ("R", -1.0)):
        eye_root = create_empty(f"{char_id}_eye_{side}", location=(sign * eye_spacing * 0.5, eye_y, eye_z), parent=head_ctrl, collection=char_col, size=0.03)
        eye_sclera = create_sphere(f"{char_id}_sclera_{side}", radius=eye_r, location=(0.0, 0.0, 0.0), scale=(1.0, 0.5, 1.0), material=eye_white_mat, parent=eye_root, collection=char_col)
        pupil = create_sphere(f"{char_id}_pupil_{side}", radius=eye_r * 0.55, location=(0.0, -eye_r * 0.42, 0.0), scale=(1.0, 0.3, 1.0), material=eye_pupil_mat, parent=eye_root, collection=char_col)
        highlight = create_sphere(f"{char_id}_high_{side}", radius=eye_r * 0.18, location=(0.005, -eye_r * 0.52, 0.005), material=eye_high_mat, parent=eye_root, collection=char_col)

        brow = create_clay_curve(
            f"{char_id}_brow_{side}",
            [(-sign * 0.024, 0.0, -0.004), (0.0, 0.0, 0.004), (sign * 0.024, 0.0, -0.002)],
            thickness=0.0055,
            material=hair_mat,
            parent=head_ctrl,
            collection=char_col
        )
        brow.location = (sign * eye_spacing * 0.5, eye_y - 0.015, eye_z + eye_r * 1.55)
        eyes_rig[f"eye_{side}"] = eye_root
        eyes_rig[f"pupil_{side}"] = pupil
        eyes_rig[f"brow_{side}"] = brow

    mouth = create_clay_curve(
        f"{char_id}_mouth",
        [(-0.028, 0.0, 0.004), (0.0, 0.0, -0.006), (0.028, 0.0, 0.004)],
        thickness=0.006,
        material=mouth_mat,
        parent=head_ctrl,
        collection=char_col
    )
    mouth.location = (0.0, -head_ry * 0.95, head_rz * 0.62)

    build_hair(char_id, spec, head_ctrl, hair_mat, char_col)

    for acc in spec.get("accessories", []):
        if acc["type"] == "glasses":
            build_glasses(char_id, acc, head_ctrl, char_col, p)

    arms_rig = {}
    arm_upper_len = 0.23
    arm_lower_len = 0.23
    for side, sign in (("l", -1.0), ("r", 1.0)):
        side_upper = side.upper()
        sh_x = sign * (p["shoulder_width"] * 0.52)
        sh_z = chest_z + 0.04
        sh = create_empty(f"{char_id}_sh_{side}", location=(sh_x, 0.0, sh_z), parent=hips, collection=char_col, size=0.06)
        sh.rotation_mode = "QUATERNION"

        arm_up = create_cylinder(
            f"{char_id}_arm_up_{side}",
            radius=0.042,
            depth=arm_upper_len,
            location=(0.0, 0.0, -arm_upper_len * 0.5),
            material=top_mat,
            parent=sh,
            collection=char_col
        )

        el = create_empty(f"{char_id}_el_{side}", location=(0.0, 0.0, -arm_upper_len), parent=sh, collection=char_col, size=0.05)
        el.rotation_mode = "QUATERNION"

        arm_low = create_cylinder(
            f"{char_id}_arm_low_{side}",
            radius=0.038,
            depth=arm_lower_len,
            location=(0.0, 0.0, -arm_lower_len * 0.5),
            material=skin_mat if o_spec["type"] in ["blouse_skirt", "shirt_slacks"] else top_mat,
            parent=el,
            collection=char_col
        )

        hand = create_sphere(
            f"{char_id}_hand_{side}",
            radius=0.036,
            location=(0.0, 0.0, -arm_lower_len - 0.02),
            scale=(0.9, 0.6, 1.1),
            material=skin_mat,
            parent=el,
            collection=char_col
        )

        arms_rig[f"sh_{side}"] = sh
        arms_rig[f"el_{side}"] = el
        arms_rig[f"hand_{side}"] = hand

    legs_rig = {}
    thigh_len = p["leg_length"] * 0.46
    shin_len = p["leg_length"] * 0.54
    leg_spacing = pelvis_w * 0.48

    for side, sign in (("l", -1.0), ("r", 1.0)):
        hip_joint = create_empty(f"{char_id}_hip_{side}", location=(sign * leg_spacing, 0.0, -0.05), parent=hips, collection=char_col, size=0.06)
        hip_joint.rotation_mode = "QUATERNION"

        thigh = create_cylinder(
            f"{char_id}_thigh_{side}",
            radius=0.067,
            depth=thigh_len,
            location=(0.0, 0.0, -thigh_len * 0.5),
            material=bot_mat,
            parent=hip_joint,
            collection=char_col
        )

        knee = create_empty(f"{char_id}_kn_{side}", location=(0.0, 0.0, -thigh_len), parent=hip_joint, collection=char_col, size=0.05)
        knee.rotation_mode = "QUATERNION"

        shin = create_cylinder(
            f"{char_id}_shin_{side}",
            radius=0.061,
            depth=shin_len,
            location=(0.0, 0.0, -shin_len * 0.5),
            material=bot_mat,
            parent=knee,
            collection=char_col
        )

        foot = create_beveled_box(
            f"{char_id}_foot_{side}",
            size=(p["shoe_width"], p["shoe_length"], p["shoe_height"]),
            location=(0.0, -p["shoe_length"] * 0.22, -shin_len),
            bevel_width=0.018,
            segments=3,
            material=shoe_mat,
            parent=knee,
            collection=char_col
        )
        foot.rotation_mode = "QUATERNION"

        legs_rig[f"hip_{side}"] = hip_joint
        legs_rig[f"kn_{side}"] = knee
        legs_rig[f"foot_{side}"] = foot

    fig = {
        "id": char_id,
        "root": root,
        "hips": hips,
        "chest": chest,
        "head": head_ctrl,
        "mouth": mouth,
        **eyes_rig,
        **arms_rig,
        **legs_rig,
        "proportions": p,
        "materials": {
            "skin": skin_mat,
            "hair": hair_mat,
            "top": top_mat,
            "bottom": bot_mat,
            "shoe": shoe_mat
        }
    }
    import polish
    polish.character(__import__(__name__), fig, spec, char_col)
    return fig


def build_hair(char_id: str, spec: Dict[str, Any], head_parent: Any, hair_mat: Any, collection: Any):
    ensure_bpy()
    p = spec["proportions"]
    h_style = spec["hair"]["style"]
    rx, ry, rz = p["head_scale"]
    z_center = rz * 0.85

    # Open hair shell: full spheres cover the face. Higher front hairline, longer back.
    verts, faces = [], []
    rings, cols = 16, 64
    for ring in range(rings+1):
        for col in range(cols):
            phi = col*math.tau/cols
            front = max(0., -math.sin(phi))
            theta = (2.05 - 1.05*front**2) * ring/rings
            verts.append((rx*1.065*math.sin(theta)*math.cos(phi), ry*1.065*math.sin(theta)*math.sin(phi), z_center+rz*1.045*math.cos(theta)))
    for ring in range(rings):
        for col in range(cols):
            nxt=(col+1)%cols
            faces.append((ring*cols+col,ring*cols+nxt,(ring+1)*cols+nxt,(ring+1)*cols+col))
    mesh=bpy.data.meshes.new(char_id+"_hair_shell");mesh.from_pydata(verts,[],faces);mesh.update()
    skull_cap=bpy.data.objects.new(char_id+"_hair_skull",mesh);collection.objects.link(skull_cap)
    skull_cap.parent=head_parent;mesh.materials.append(hair_mat)
    for poly in mesh.polygons:poly.use_smooth=True
    solid=skull_cap.modifiers.new("clay_thickness","SOLIDIFY");solid.thickness=.008

    if h_style == "bob":
        for side, sign in (("L", 1.0), ("R", -1.0)):
            create_clay_curve(
                f"{char_id}_bob_side_{side}",
                [
                    (sign * rx * 0.85, -ry * 0.35, z_center + rz * 0.70),
                    (sign * rx * 1.08, -ry * 0.15, z_center + rz * 0.15),
                    (sign * rx * 0.95, -ry * 0.45, z_center - rz * 0.40)
                ],
                thickness=0.038,
                material=hair_mat,
                parent=head_parent,
                collection=collection
            )
        create_clay_curve(
            f"{char_id}_bob_back",
            [
                (-rx * 0.85, ry * 0.65, z_center + rz * 0.35),
                (0.0, ry * 1.05, z_center - rz * 0.25),
                (rx * 0.85, ry * 0.65, z_center + rz * 0.35)
            ],
            thickness=0.055,
            material=hair_mat,
            parent=head_parent,
            collection=collection
        )
        create_clay_curve(
            f"{char_id}_bob_fringe",
            [
                (-rx * 0.65, -ry * 0.82, z_center + rz * 0.68),
                (-rx * 0.15, -ry * 0.92, z_center + rz * 0.60),
                (rx * 0.45, -ry * 0.86, z_center + rz * 0.65)
            ],
            thickness=0.024,
            material=hair_mat,
            parent=head_parent,
            collection=collection
        )

    elif h_style == "ponytail":
        tie_color = spec["hair"].get("tie_color", [0.2, 0.2, 0.25, 1.0])
        tie_mat = create_clay_material(f"mat_tie_{char_id}", tuple(tie_color), roughness=0.55, specular=0.25)
        tie_pos = (0.0, ry * 1.02, z_center + rz * 0.50)
        create_cylinder(
            f"{char_id}_hair_tie",
            radius=0.032,
            depth=0.024,
            location=tie_pos,
            rotation=(1.1, 0.0, 0.0),
            material=tie_mat,
            parent=head_parent,
            collection=collection
        )
        create_clay_curve(
            f"{char_id}_ponytail_tail",
            [
                tie_pos,
                (0.02, ry * 1.35, z_center + rz * 0.55),
                (-0.02, ry * 1.55, z_center + rz * 0.20),
                (0.0, ry * 1.62, z_center - rz * 0.35)
            ],
            thickness=0.042,
            material=hair_mat,
            parent=head_parent,
            collection=collection
        )
        for sign in (-1.0, 1.0):
            create_clay_curve(
                f"{char_id}_ponytail_wisp_{sign}",
                [
                    (sign * rx * 0.70, -ry * 0.65, z_center + rz * 0.45),
                    (sign * rx * 0.92, -ry * 0.45, z_center + rz * 0.05)
                ],
                thickness=0.016,
                material=hair_mat,
                parent=head_parent,
                collection=collection
            )

    elif h_style == "short_wavy":
        waves = [
            ((-0.08, -ry * 0.4, z_center + rz * 0.75), (0.05, 0.04, 0.03)),
            ((0.07, -ry * 0.45, z_center + rz * 0.72), (0.045, 0.04, 0.03)),
            ((-rx * 0.88, ry * 0.1, z_center + rz * 0.4), (0.035, 0.045, 0.06)),
            ((rx * 0.88, ry * 0.1, z_center + rz * 0.4), (0.035, 0.045, 0.06)),
            ((-0.03, ry * 0.85, z_center + rz * 0.35), (0.07, 0.05, 0.06)),
            ((0.05, ry * 0.82, z_center + rz * 0.20), (0.065, 0.05, 0.05))
        ]
        for idx, (loc, radii) in enumerate(waves):
            create_sphere(
                f"{char_id}_wavy_{idx}",
                radius=radii[0],
                location=loc,
                scale=(1.0, radii[1] / radii[0], radii[2] / radii[0]),
                material=hair_mat,
                parent=head_parent,
                collection=collection
            )

    elif h_style == "side_part":
        create_clay_curve(
            f"{char_id}_part_swoop",
            [
                (-rx * 0.62, -ry * 0.65, z_center + rz * 0.75),
                (0.02, -ry * 0.88, z_center + rz * 0.85),
                (rx * 0.75, -ry * 0.62, z_center + rz * 0.60)
            ],
            thickness=0.038,
            material=hair_mat,
            parent=head_parent,
            collection=collection
        )
        create_clay_curve(
            f"{char_id}_part_side_l",
            [
                (-rx * 0.72, -ry * 0.45, z_center + rz * 0.65),
                (-rx * 0.96, ry * 0.15, z_center + rz * 0.20)
            ],
            thickness=0.028,
            material=hair_mat,
            parent=head_parent,
            collection=collection
        )

    elif h_style == "curly":
        curls = [
            ((0.0, -ry * 0.68, z_center + rz * 0.80), 0.034),
            ((-rx * 0.45, -ry * 0.62, z_center + rz * 0.78), 0.032),
            ((rx * 0.45, -ry * 0.62, z_center + rz * 0.78), 0.032),
            ((-rx * 0.85, -ry * 0.15, z_center + rz * 0.50), 0.035),
            ((rx * 0.85, -ry * 0.15, z_center + rz * 0.50), 0.035),
            ((0.0, ry * 0.75, z_center + rz * 0.65), 0.045),
            ((-rx * 0.55, ry * 0.60, z_center + rz * 0.40), 0.038),
            ((rx * 0.55, ry * 0.60, z_center + rz * 0.40), 0.038)
        ]
        for idx, (loc, rad) in enumerate(curls):
            create_sphere(
                f"{char_id}_curl_{idx}",
                radius=rad,
                location=loc,
                scale=(1.1, 0.9, 1.0),
                material=hair_mat,
                parent=head_parent,
                collection=collection
            )

    elif h_style == "swept_silver":
        sweeps = [
            [
                (0.0, -ry * 0.75, z_center + rz * 0.72),
                (0.0, -ry * 0.15, z_center + rz * 1.02),
                (0.0, ry * 0.85, z_center + rz * 0.65)
            ],
            [
                (-rx * 0.45, -ry * 0.68, z_center + rz * 0.68),
                (-rx * 0.45, 0.0, z_center + rz * 0.92),
                (-rx * 0.55, ry * 0.75, z_center + rz * 0.45)
            ],
            [
                (rx * 0.45, -ry * 0.68, z_center + rz * 0.68),
                (rx * 0.45, 0.0, z_center + rz * 0.92),
                (rx * 0.55, ry * 0.75, z_center + rz * 0.45)
            ]
        ]
        for idx, pts in enumerate(sweeps):
            create_clay_curve(
                f"{char_id}_swept_{idx}",
                pts,
                thickness=0.036,
                material=hair_mat,
                parent=head_parent,
                collection=collection
            )


def build_glasses(char_id: str, acc_spec: Dict[str, Any], head_parent: Any, collection: Any, p):
    ensure_bpy()
    frame_color = acc_spec.get("frame_color", [0.12, 0.12, 0.14, 1.0])
    frame_mat = create_clay_material(f"mat_glasses_{char_id}", tuple(frame_color), roughness=0.45, specular=0.40)
    shape = acc_spec.get("frame_shape", "round")
    radius = acc_spec.get("radius", 0.032)
    thick = acc_spec.get("rim_thickness", 0.005)

    rx = p["head_scale"][0]
    eye_z = p["head_scale"][2] * .85
    eye_y = -p["head_scale"][1] * 1.03
    eye_spacing = p["eye_spacing"]
    radius *= 1.28

    create_clay_curve(
        f"{char_id}_glasses_bridge",
        [(-0.018, eye_y, eye_z), (0.0, eye_y - 0.005, eye_z + 0.005), (0.018, eye_y, eye_z)],
        thickness=thick * 0.8,
        material=frame_mat,
        parent=head_parent,
        collection=collection
    )

    for sign in (-1.0, 1.0):
        center_x = sign * (eye_spacing * 0.5)
        if shape == "round":
            pts = [
                (center_x, eye_y, eye_z + radius),
                (center_x + radius, eye_y, eye_z),
                (center_x, eye_y, eye_z - radius),
                (center_x - radius, eye_y, eye_z)
            ]
            create_clay_curve(
                f"{char_id}_glasses_rim_{sign}",
                pts,
                thickness=thick,
                material=frame_mat,
                parent=head_parent,
                collection=collection,
                cyclic=True
            )
        else:
            w = radius * 1.15
            h = radius * 0.85
            pts = [
                (center_x - w, eye_y, eye_z + h),
                (center_x + w, eye_y, eye_z + h),
                (center_x + w, eye_y, eye_z - h),
                (center_x - w, eye_y, eye_z - h)
            ]
            create_clay_curve(
                f"{char_id}_glasses_rim_{sign}",
                pts,
                thickness=thick,
                material=frame_mat,
                parent=head_parent,
                collection=collection,
                cyclic=True
            )

        create_clay_curve(
            f"{char_id}_glasses_temple_{sign}",
            [
                (center_x + sign * radius, eye_y, eye_z),
                (sign * (rx * 0.95), 0.0, eye_z)
            ],
            thickness=thick * 0.8,
            material=frame_mat,
            parent=head_parent,
            collection=collection
        )


def pose_actor(
    fig: Dict[str, Any],
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    yaw: float = 0.0,
    hips_z: Optional[float] = None,
    hand_targets: Optional[List[Tuple[float, float, float]]] = None,
    foot_targets: Optional[List[Tuple[float, float, float]]] = None
):
    ensure_bpy()
    root = fig["root"]
    root.location = position
    root.rotation_euler = (0.0, 0.0, yaw)

    if hips_z is not None:
        fig["hips"].location.z = hips_z

    bpy.context.view_layer.update()
    root_q = root.matrix_world.to_quaternion()
    pos_vec = Vector(position)

    p = fig["proportions"]
    thigh_len = p["leg_length"] * 0.46
    shin_len = p["leg_length"] * 0.54
    shoe_h = p["shoe_height"]

    for idx, (side, sign) in enumerate((("l", -1.0), ("r", 1.0))):
        if foot_targets and idx < len(foot_targets):
            foot_pos = Vector(foot_targets[idx])
        else:
            current_hips_z = fig["hips"].location.z
            forward_offset = -0.28 if current_hips_z < (p["leg_length"] * 0.8) else -0.015
            ground_z = shoe_h * 0.5
            foot_pos = pos_vec + root_q @ Vector((sign * 0.11, forward_offset, ground_z))

        solve_two_bone(
            fig[f"hip_{side}"],
            fig[f"kn_{side}"],
            foot_pos,
            thigh_len,
            shin_len,
            root_q @ Vector((0.0, -1.0, 0.12))
        )
        bpy.context.view_layer.update()
        fig[f"foot_{side}"].rotation_quaternion = fig[f"kn_{side}"].matrix_world.to_quaternion().inverted() @ root_q

    if hand_targets:
        arm_up_len = 0.23
        arm_low_len = 0.23
        for idx, (side, sign) in enumerate((("l", -1.0), ("r", 1.0))):
            target = Vector(hand_targets[idx])
            solve_two_bone(
                fig[f"sh_{side}"],
                fig[f"el_{side}"],
                target,
                arm_up_len,
                arm_low_len,
                root_q @ Vector((sign * 0.8, 0.2, -0.35))
            )


def apply_expression(fig: Dict[str, Any], expr_name: str, expressions_dict: Dict[str, Any]):
    ensure_bpy()
    if expr_name not in expressions_dict:
        expr_name = "neutral"
    data = expressions_dict[expr_name]

    head = fig["head"]
    head.rotation_euler = tuple(data.get("head_tilt", (0.0, 0.0, 0.0)))

    eye_lid_scale = data.get("eye_lid_scale", 1.0)
    glance = data.get("glance", (0.0, 0.0))

    for side in ("L", "R"):
        if f"eye_{side}" in fig:
            fig[f"eye_{side}"].scale.z = eye_lid_scale
        if f"pupil_{side}" in fig:
            pupil = fig[f"pupil_{side}"]
            pupil.location.x = glance[0] * 0.012
            pupil.location.z = glance[1] * 0.012

    for side, sign in (("L", 1.0), ("R", -1.0)):
        key_name = f"brow_{side.lower()}"
        if f"brow_{side}" in fig and key_name in data:
            brow_data = data[key_name]
            brow = fig[f"brow_{side}"]
            brow.location.z = (fig["proportions"]["head_scale"][2] * 0.85 + fig["proportions"]["eye_radius"] * 1.55) + brow_data[0]
            brow.rotation_euler = (0.0, brow_data[2], 0.0)

    mouth = fig.get("mouth")
    if mouth:
        mouth_scale = data.get("mouth_scale", (1.0, 1.0, 1.0))
        mouth.scale = tuple(mouth_scale)
        shape = data.get("mouth_shape", "rest")
        if shape == "down_curve":
            mouth.rotation_euler = (0.0, math.pi, 0.0)
        elif shape == "tight_smile":
            mouth.rotation_euler = (0.0, 0.15, 0.0)
            mouth.scale.z = 0.25
        elif shape in ("rest", "flat_firm"):
            mouth.rotation_euler = (0.0, 0.0, 0.0)
            mouth.scale.z = 0.22 if shape == "rest" else 0.08
        else:
            mouth.rotation_euler = (0.0, 0.0, 0.0)


def setup_studio_environment(collection: Optional[Any] = None) -> Dict[str, Any]:
    ensure_bpy()
    studio_col = get_or_create_collection("Studio_Lighting", collection)

    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("Clay_World")
        bpy.context.scene.world = world
    world.use_nodes = True
    w_nodes = world.node_tree.nodes
    w_nodes.clear()
    w_bg = w_nodes.new(type="ShaderNodeBackground")
    w_bg.inputs["Color"].default_value = (0.95, 0.94, 0.92, 1.0)
    w_bg.inputs["Strength"].default_value = 0.85
    w_out = w_nodes.new(type="ShaderNodeOutputWorld")
    world.node_tree.links.new(w_bg.outputs["Background"], w_out.inputs["Surface"])

    cyc_mat = create_clay_material("mat_cyclorama", (0.92, 0.90, 0.88, 1.0), roughness=0.75, specular=0.10)
    cyc = create_beveled_box(
        "cyclorama_backdrop",
        size=(8.0, 8.0, 0.2),
        location=(0.0, 1.5, -0.1),
        bevel_width=0.4,
        segments=6,
        material=cyc_mat,
        collection=studio_col
    )

    key_data = bpy.data.lights.new("Light_Key", type="AREA")
    key_data.energy = 220.0
    key_data.size = 1.6
    key_data.color = (1.0, 0.96, 0.90)
    key_obj = bpy.data.objects.new("Light_Key", key_data)
    key_obj.location = (-1.8, -2.6, 2.4)
    key_obj.rotation_euler = (0.85, 0.35, -0.65)
    studio_col.objects.link(key_obj)

    fill_data = bpy.data.lights.new("Light_Fill", type="AREA")
    fill_data.energy = 95.0
    fill_data.size = 2.4
    fill_data.color = (0.90, 0.94, 1.0)
    fill_obj = bpy.data.objects.new("Light_Fill", fill_data)
    fill_obj.location = (2.2, -2.2, 1.8)
    fill_obj.rotation_euler = (0.90, -0.30, 0.70)
    studio_col.objects.link(fill_obj)

    rim_data = bpy.data.lights.new("Light_Rim", type="AREA")
    rim_data.energy = 160.0
    rim_data.size = 1.2
    rim_data.color = (1.0, 0.98, 0.92)
    rim_obj = bpy.data.objects.new("Light_Rim", rim_data)
    rim_obj.location = (0.0, 2.4, 2.8)
    rim_obj.rotation_euler = (2.4, 0.0, 0.0)
    studio_col.objects.link(rim_obj)

    for lamp in (key_obj, fill_obj, rim_obj):
        lamp.rotation_euler = (Vector((0,0,.8))-lamp.location).to_track_quat("-Z","Y").to_euler()
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.35
    import polish
    polish.studio(__import__(__name__), studio_col)
    return {
        "key": key_obj,
        "fill": fill_obj,
        "rim": rim_obj,
        "cyclorama": cyc
    }


def build_miniature_office(collection: Optional[Any] = None) -> Dict[str, Any]:
    ensure_bpy()
    office_col = get_or_create_collection("Miniature_Office", collection)

    floor_mat = create_clay_material("mat_office_floor", (0.88, 0.85, 0.80, 1.0), roughness=0.68, specular=0.15)
    wall_mat = create_clay_material("mat_office_wall", (0.94, 0.93, 0.91, 1.0), roughness=0.72, specular=0.12)
    wood_mat = create_clay_material("mat_office_wood", (0.76, 0.58, 0.42, 1.0), roughness=0.55, specular=0.22)
    mat_clay_dark = create_clay_material("mat_dark_clay", (0.22, 0.23, 0.26, 1.0), roughness=0.60, specular=0.20)
    mat_mug = create_clay_material("mat_yellow_mug", (0.92, 0.75, 0.22, 1.0), roughness=0.45, specular=0.35)
    mat_leaf = create_clay_material("mat_succulent", (0.35, 0.55, 0.38, 1.0), roughness=0.62, specular=0.18)

    floor = create_beveled_box("office_floor", size=(5.0, 5.0, 0.1), location=(0.0, 0.0, -0.05), bevel_width=0.04, segments=3, material=floor_mat, collection=office_col)
    wall_back = create_beveled_box("office_wall_back", size=(5.0, 0.1, 3.0), location=(0.0, 1.8, 1.45), bevel_width=0.03, segments=3, material=wall_mat, collection=office_col)
    wall_side = create_beveled_box("office_wall_side", size=(0.1, 5.0, 3.0), location=(-2.45, 0.0, 1.45), bevel_width=0.03, segments=3, material=wall_mat, collection=office_col)

    desk_h = 0.72
    desk_top = create_beveled_box("desk_top", size=(1.25, 0.65, 0.045), location=(0.0, -0.15, desk_h), bevel_width=0.015, segments=3, material=wood_mat, collection=office_col)
    for dx, dy in ((-0.55, -0.25), (0.55, -0.25), (-0.55, 0.25), (0.55, 0.25)):
        create_cylinder(f"desk_leg_{dx}_{dy}", radius=0.024, depth=desk_h - 0.045, location=(dx, -0.15 + dy, (desk_h - 0.045) * 0.5), bevel_width=0.005, material=wood_mat, collection=office_col)

    chair_seat_h = 0.45
    chair_seat = create_beveled_box("chair_seat", size=(0.44, 0.42, 0.05), location=(0.0, 0.40, chair_seat_h), bevel_width=0.02, segments=3, material=mat_clay_dark, collection=office_col)
    chair_back = create_beveled_box("chair_back", size=(0.42, 0.05, 0.42), location=(0.0, 0.60, chair_seat_h + 0.25), bevel_width=0.02, segments=3, material=mat_clay_dark, collection=office_col)
    create_cylinder("chair_stem", radius=0.032, depth=chair_seat_h - 0.05, location=(0.0, 0.40, (chair_seat_h - 0.05) * 0.5), material=mat_clay_dark, collection=office_col)

    laptop_base = create_beveled_box("laptop_base", size=(0.32, 0.22, 0.014), location=(-0.15, -0.10, desk_h + 0.03), bevel_width=0.004, material=mat_clay_dark, collection=office_col)
    laptop_screen = create_beveled_box("laptop_screen", size=(0.32, 0.012, 0.20), location=(-0.15, 0.01, desk_h + 0.13), rotation=(-0.25, 0.0, 0.0), bevel_width=0.004, material=mat_clay_dark, collection=office_col)

    mug = create_cylinder("coffee_mug", radius=0.038, depth=0.075, location=(0.42, -0.10, desk_h + 0.06), bevel_width=0.006, material=mat_mug, collection=office_col)
    create_clay_curve("mug_handle", [(0.46, -0.10, desk_h + 0.08), (0.49, -0.10, desk_h + 0.06), (0.46, -0.10, desk_h + 0.04)], thickness=0.008, material=mat_mug, collection=office_col)

    plant_pot = create_cylinder("plant_pot", radius=0.042, depth=0.065, location=(0.45, 0.12, desk_h + 0.055), bevel_width=0.006, material=mat_clay_dark, collection=office_col)
    for a in range(5):
        ang = a * (2.0 * math.pi / 5.0)
        create_sphere(f"plant_leaf_{a}", radius=0.024, location=(0.45 + math.cos(ang) * 0.026, 0.12 + math.sin(ang) * 0.026, desk_h + 0.09), scale=(1.0, 0.6, 1.4), material=mat_leaf, collection=office_col)

    phone = create_beveled_box("smartphone", size=(0.075, 0.145, 0.010), location=(0.18, -0.22, desk_h + 0.03), bevel_width=0.003, segments=2, material=mat_clay_dark, collection=office_col)

    return {
        "desk_height": desk_h,
        "chair_seat_height": chair_seat_h,
        "smartphone": phone,
        "laptop": laptop_base,
        "mug": mug
    }


def create_camera(
    name: str,
    location: Tuple[float, float, float],
    target: Tuple[float, float, float],
    focal_length: float = 65.0,
    collection: Optional[Any] = None
) -> Any:
    ensure_bpy()
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = focal_length
    cam_obj = bpy.data.objects.new(name, cam_data)
    cam_obj.location = location

    dir_vec = Vector(target) - Vector(location)
    rot_quat = dir_vec.to_track_quat("-Z", "Y")
    cam_obj.rotation_euler = rot_quat.to_euler()

    target_col = collection if collection else bpy.context.scene.collection
    target_col.objects.link(cam_obj)
    return cam_obj


def configure_render_settings(width: int = 900, height: int = 1100, samples: int = 32):
    ensure_bpy()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"

    if hasattr(scene, "eevee"):
        if hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = samples
        elif hasattr(scene.eevee, "render_samples"):
            scene.eevee.render_samples = samples
    if scene.render.engine == "CYCLES":
        scene.cycles.samples = samples


def insert_keyframe(obj: Any, frame: int, data_paths: List[str]):
    for path in data_paths:
        obj.keyframe_insert(data_path=path, frame=frame)


def animate_demo_scene(fig: Dict[str, Any], office: Dict[str, Any], expressions_dict: Dict[str, Any], total_frames: int = 192):
    ensure_bpy()
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = total_frames
    scene.render.fps = 24

    chair_seat_h = office["chair_seat_height"]
    desk_h = office["desk_height"]
    seated_hips_z = chair_seat_h + 0.10

    foot_l = (-0.11, .10, .025)
    foot_r = (0.11, .10, .025)

    phone = office["smartphone"]

    key_channels = ["location", "rotation_euler", "rotation_quaternion"]

    def key_all(frame: int):
        insert_keyframe(fig["root"], frame, ["location", "rotation_euler"])
        insert_keyframe(fig["hips"], frame, ["location", "rotation_euler"])
        insert_keyframe(fig["chest"], frame, ["location", "rotation_euler"])
        insert_keyframe(fig["head"], frame, ["location", "rotation_euler"])
        for s in ("l", "r"):
            insert_keyframe(fig[f"sh_{s}"], frame, key_channels)
            insert_keyframe(fig[f"el_{s}"], frame, key_channels)
            insert_keyframe(fig[f"hip_{s}"], frame, key_channels)
            insert_keyframe(fig[f"kn_{s}"], frame, key_channels)
            insert_keyframe(fig[f"foot_{s}"], frame, key_channels)
        for s in ("L", "R"):
            if f"eye_{s}" in fig:
                insert_keyframe(fig[f"eye_{s}"], frame, ["scale"])
            if f"pupil_{s}" in fig:
                insert_keyframe(fig[f"pupil_{s}"], frame, ["location"])
            if f"brow_{s}" in fig:
                insert_keyframe(fig[f"brow_{s}"], frame, ["location", "rotation_euler"])
        if "mouth" in fig:
            insert_keyframe(fig["mouth"], frame, ["scale", "rotation_euler"])
        insert_keyframe(phone, frame, ["location", "rotation_euler"])

    # Phase 1: Frame 1 - Seated, checking phone
    hand_l_table = (-0.22, .06, desk_h + .04)
    hand_r_phone = (.15, .14, desk_h + .22)

    pose_actor(
        fig,
        position=(0.0, 0.40, 0.0),
        yaw=0.0,
        hips_z=seated_hips_z,
        hand_targets=[hand_l_table, hand_r_phone],
        foot_targets=[foot_l, foot_r]
    )
    apply_expression(fig, "neutral", expressions_dict)
    fig["head"].rotation_euler = (0.22, 0.0, 0.05)
    phone.location = (.15, .12, desk_h + .22)
    phone.rotation_euler = (-0.65, 0.0, 0.12)
    key_all(1)

    # Hold reading
    key_all(35)

    # Phase 2: Frame 60 - Awkward glance sideways
    pose_actor(
        fig,
        position=(0.0, 0.40, 0.0),
        yaw=0.0,
        hips_z=seated_hips_z,
        hand_targets=[hand_l_table, (.15, .14, desk_h + .22)],
        foot_targets=[foot_l, foot_r]
    )
    apply_expression(fig, "awkward", expressions_dict)
    fig["head"].rotation_euler = (0.06, 0.08, -0.28)
    key_all(60)

    # Awkward pause
    key_all(85)

    # Phase 3: Frame 115 - Held torso and brief head lift before sigh
    fig["chest"].location.z = fig["proportions"]["torso_length"] * 0.75
    fig["head"].rotation_euler = (-0.08, 0.02, -0.05)
    key_all(115)

    # Phase 4: Frame 140 - The Sigh & lowering hand to desk
    hand_r_desk = (.19, .05, desk_h + .04)
    phone.location = (.19, .02, desk_h + .02)
    phone.rotation_euler = (0.0, 0.0, 0.35)

    pose_actor(
        fig,
        position=(0.0, 0.40, 0.0),
        yaw=0.0,
        hips_z=seated_hips_z,
        hand_targets=[hand_l_table, hand_r_desk],
        foot_targets=[foot_l, foot_r]
    )
    apply_expression(fig, "ashamed", expressions_dict)
    fig["head"].rotation_euler = (0.28, 0.04, -0.08)
    fig["chest"].location.z = fig["proportions"]["torso_length"] * 0.75
    key_all(140)

    # Phase 5: Frame 170-192 - Settled calm resignation with subtle blink
    apply_expression(fig, "ashamed", expressions_dict)
    fig["head"].rotation_euler = (0.24, 0.02, -0.04)
    for s in ("L", "R"):
        if f"eye_{s}" in fig:
            fig[f"eye_{s}"].scale.z = 0.20
    key_all(170)

    for s in ("L", "R"):
        if f"eye_{s}" in fig:
            fig[f"eye_{s}"].scale.z = 0.90
    key_all(178)
    key_all(total_frames)
