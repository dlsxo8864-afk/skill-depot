import sys
import os
import math
import json
import argparse
import bpy
import mathutils

# ---------------------------------------------------------------------------
# 점토풍 미니어처 사무실. 세트·인물은 이 파일, 카메라·동작은 refinements.py 가 만든다.
# 장면 수·시각·길이는 대본(script.json)에서 읽는다. 장면 하나가 대본의 구간(beats) 하나다.
# ---------------------------------------------------------------------------

FPS = 24
TOTAL_FRAMES = 360  # main() 이 대본의 frames 로 바꾼다
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920

SCRIPT = {}  # main() 이 script.json 을 읽어 채운다. refinements.py 가 대화 시각을 여기서 읽는다
SHOT_TIMELINES = []  # main() 이 대본의 구간으로 채운다: {"id", "name", "start", "end"}

# ---------------------------------------------------------------------------
# Scene & Collection Utilities
# ---------------------------------------------------------------------------

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for block in bpy.data.meshes:
        bpy.data.meshes.remove(block, do_unlink=True)
    for block in bpy.data.materials:
        bpy.data.materials.remove(block, do_unlink=True)
    for block in bpy.data.cameras:
        bpy.data.cameras.remove(block, do_unlink=True)
    for block in bpy.data.lights:
        bpy.data.lights.remove(block, do_unlink=True)

def get_or_create_collection(name, parent_col=None):
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
    else:
        col = bpy.data.collections.new(name)
        if parent_col:
            parent_col.children.link(col)
        else:
            bpy.context.scene.collection.children.link(col)
    return col

# ---------------------------------------------------------------------------
# Material Library (Matte Toy Aesthetic)
# ---------------------------------------------------------------------------

MATS = {}

def create_matte_material(name, rgba, roughness=0.55, specular=0.25):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = specular
    out = nodes.new(type="ShaderNodeOutputMaterial")
    out.location = (260, 0)
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    MATS[name] = mat
    return mat

def init_materials():
    create_matte_material("Wall", (0.92, 0.90, 0.86, 1.0), roughness=0.8)
    create_matte_material("FloorBoard", (0.82, 0.76, 0.68, 1.0), roughness=0.6)
    create_matte_material("FloorTile", (0.75, 0.70, 0.63, 1.0), roughness=0.65)
    create_matte_material("WalnutWood", (0.32, 0.20, 0.12, 1.0), roughness=0.45)
    create_matte_material("DeskTop", (0.78, 0.65, 0.48, 1.0), roughness=0.4)
    create_matte_material("PrinterIvory", (0.91, 0.90, 0.86, 1.0), roughness=0.35)
    create_matte_material("PrinterDark", (0.22, 0.24, 0.26, 1.0), roughness=0.5)
    create_matte_material("PaperWhite", (0.98, 0.97, 0.94, 1.0), roughness=0.7)
    create_matte_material("ChairSeatNavy", (0.12, 0.18, 0.26, 1.0), roughness=0.6)
    create_matte_material("ChairMetal", (0.35, 0.36, 0.38, 1.0), roughness=0.3)
    create_matte_material("MonitorPlastic", (0.16, 0.17, 0.19, 1.0), roughness=0.4)
    create_matte_material("MonitorScreen", (0.28, 0.36, 0.42, 1.0), roughness=0.2)
    create_matte_material("PlantPot", (0.76, 0.42, 0.30, 1.0), roughness=0.65)
    create_matte_material("PlantLeaf", (0.22, 0.48, 0.26, 1.0), roughness=0.5)
    create_matte_material("WindowFrame", (0.88, 0.86, 0.82, 1.0), roughness=0.4)
    create_matte_material("SkinWarm", (0.94, 0.76, 0.65, 1.0), roughness=0.6)
    create_matte_material("SkinLead", (0.90, 0.73, 0.62, 1.0), roughness=0.6)
    create_matte_material("HairDark", (0.11, 0.09, 0.09, 1.0), roughness=0.5)
    create_matte_material("BlouseTeal", (0.15, 0.46, 0.48, 1.0), roughness=0.55)
    create_matte_material("TrousersDark", (0.14, 0.15, 0.18, 1.0), roughness=0.65)
    create_matte_material("ShirtCoral", (0.84, 0.41, 0.32, 1.0), roughness=0.55)
    create_matte_material("LeadNavy", (0.10, 0.15, 0.28, 1.0), roughness=0.6)
    create_matte_material("GlassesGold", (0.82, 0.68, 0.28, 1.0), roughness=0.25)
    create_matte_material("AccentYellow", (0.92, 0.72, 0.20, 1.0), roughness=0.5)
    create_matte_material("EyeBlack", (0.04, 0.04, 0.05, 1.0), roughness=0.15)
    create_matte_material("MouthRose", (0.75, 0.32, 0.35, 1.0), roughness=0.7)

# ---------------------------------------------------------------------------
# Mesh Helpers (Toy / Beveled Geometry)
# ---------------------------------------------------------------------------

def add_beveled_box(name, size, location, material=None, bevel_width=0.015, segments=2, collection=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel_width > 0:
        bev = obj.modifiers.new(name="Bevel", type="BEVEL")
        bev.width = bevel_width
        bev.segments = segments
    if material:
        obj.data.materials.append(material)
    if collection:
        for cur_col in obj.users_collection:
            cur_col.objects.unlink(obj)
        collection.objects.link(obj)
    return obj

def add_cylinder(name, radius, depth, location, rotation=(0, 0, 0), material=None, collection=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation, vertices=20)
    obj = bpy.context.active_object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    if collection:
        for cur_col in obj.users_collection:
            cur_col.objects.unlink(obj)
        collection.objects.link(obj)
    return obj

def add_sphere(name, radius, location, material=None, collection=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=20, ring_count=14)
    obj = bpy.context.active_object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    if collection:
        for cur_col in obj.users_collection:
            cur_col.objects.unlink(obj)
        collection.objects.link(obj)
    return obj

def create_empty(name, location, collection=None):
    empty = bpy.data.objects.new(name, None)
    empty.location = location
    empty.empty_display_type = "ARROWS"
    empty.empty_display_size = 0.12
    target_col = collection if collection else bpy.context.scene.collection
    target_col.objects.link(empty)
    return empty

# ---------------------------------------------------------------------------
# Set Construction (Miniature Office)
# ---------------------------------------------------------------------------

def build_office_set(set_col, props_col):
    # Floor (plank / seam look)
    floor = add_beveled_box("FloorBase", (6.0, 7.0, 0.1), (0.0, 0.5, -0.05), material=MATS["FloorTile"], collection=set_col)
    for i in range(-5, 6):
        add_beveled_box(f"FloorSeam_{i}", (0.015, 6.8, 0.02), (i * 0.55, 0.5, 0.005), material=MATS["FloorBoard"], bevel_width=0, collection=set_col)

    # Back Wall & Left Window Wall
    add_beveled_box("WallBack", (6.0, 0.15, 3.4), (0.0, 3.9, 1.7), material=MATS["Wall"], bevel_width=0.02, collection=set_col)
    add_beveled_box("WallLeft", (0.15, 7.0, 3.4), (-3.0, 0.5, 1.7), material=MATS["Wall"], bevel_width=0.02, collection=set_col)
    add_beveled_box("BaseboardBack", (6.0, 0.05, 0.12), (0.0, 3.8, 0.06), material=MATS["WalnutWood"], bevel_width=0.005, collection=set_col)

    # Window & Blinds on left wall
    win_frame = add_beveled_box("WindowFrame", (0.18, 2.4, 2.0), (-2.95, 0.8, 1.8), material=MATS["WindowFrame"], bevel_width=0.03, collection=set_col)
    for b in range(10):
        add_beveled_box(f"BlindSlat_{b}", (0.02, 2.2, 0.08), (-2.88, 0.8, 0.95 + b * 0.17), material=MATS["PaperWhite"], bevel_width=0.005, collection=set_col)

    # Bookshelf at back corner
    shelf = add_beveled_box("Bookshelf", (1.6, 0.45, 2.4), (2.0, 3.6, 1.2), material=MATS["WalnutWood"], bevel_width=0.02, collection=props_col)
    book_colors = ["ShirtCoral", "BlouseTeal", "AccentYellow", "LeadNavy", "DeskTop"]
    for r in range(3):
        shelf_z = 0.5 + r * 0.7
        for b_idx in range(6):
            mat = MATS[book_colors[(r + b_idx) % len(book_colors)]]
            add_beveled_box(f"Book_{r}_{b_idx}", (0.08, 0.32, 0.42), (1.45 + b_idx * 0.16, 3.6, shelf_z), material=mat, bevel_width=0.008, collection=props_col)

    # Desks
    def build_desk(name_prefix, pos, rot_z=0.0):
        empty = create_empty(f"{name_prefix}_Root", pos, collection=props_col)
        empty.rotation_euler[2] = rot_z
        top = add_beveled_box(f"{name_prefix}_Top", (1.5, 0.85, 0.07), (0, 0, 0.75), material=MATS["DeskTop"], bevel_width=0.02, collection=props_col)
        top.parent = empty
        leg_mat = MATS["WalnutWood"]
        for dx, dy in [(-0.68, -0.36), (0.68, -0.36), (-0.68, 0.36), (0.68, 0.36)]:
            leg = add_beveled_box(f"{name_prefix}_Leg", (0.07, 0.07, 0.72), (dx, dy, 0.36), material=leg_mat, bevel_width=0.01, collection=props_col)
            leg.parent = empty
        # 책상 위 물건: 모니터, 키보드, 마우스
        mon_base = add_cylinder(f"{name_prefix}_MonBase", 0.12, 0.02, (0, 0.18, 0.80), material=MATS["MonitorPlastic"], collection=props_col)
        mon_base.parent = empty
        mon_stand = add_cylinder(f"{name_prefix}_MonStand", 0.025, 0.24, (0, 0.18, 0.92), material=MATS["MonitorPlastic"], collection=props_col)
        mon_stand.parent = empty
        mon_body = add_beveled_box(f"{name_prefix}_MonBody", (0.65, 0.06, 0.42), (0, 0.18, 1.15), material=MATS["MonitorPlastic"], bevel_width=0.01, collection=props_col)
        mon_body.parent = empty
        screen = add_beveled_box(f"{name_prefix}_Screen", (0.60, 0.01, 0.37), (0, 0.145, 1.15), material=MATS["MonitorScreen"], bevel_width=0.005, collection=props_col)
        screen.parent = empty
        # Keyboard
        kb = add_beveled_box(f"{name_prefix}_Keyboard", (0.42, 0.16, 0.02), (0, -0.15, 0.80), material=MATS["PrinterDark"], bevel_width=0.005, collection=props_col)
        kb.parent = empty
        return empty

    # Desk 1: Protagonist Desk (Left/Foreground)
    d1 = build_desk("Desk_Protagonist", (-0.85, -0.4, 0.0))
    # Desk 2: Newcomer Desk (Right/Midground, spacious walkway in between)
    d2 = build_desk("Desk_Newcomer", (1.35, -0.2, 0.0))
    # Desk 3: Manager / Team Lead Desk (Rear center/right)
    d3 = build_desk("Desk_Lead", (0.5, 2.2, 0.0))

    # Office Swivel Chairs
    def build_chair(name_prefix, pos, rot_z=0.0):
        empty = create_empty(f"{name_prefix}_Root", pos, collection=props_col)
        empty.rotation_euler[2] = rot_z
        base = add_cylinder(f"{name_prefix}_Base", 0.28, 0.04, (0, 0, 0.12), material=MATS["ChairMetal"], collection=props_col)
        base.parent = empty
        stem = add_cylinder(f"{name_prefix}_Stem", 0.035, 0.36, (0, 0, 0.28), material=MATS["ChairMetal"], collection=props_col)
        stem.parent = empty
        seat = add_beveled_box(f"{name_prefix}_Seat", (0.48, 0.46, 0.09), (0, 0, 0.50), material=MATS["ChairSeatNavy"], bevel_width=0.03, collection=props_col)
        seat.parent = empty
        back = add_beveled_box(f"{name_prefix}_Back", (0.44, 0.08, 0.50), (0, -0.21, 0.77), material=MATS["ChairSeatNavy"], bevel_width=0.03, collection=props_col)
        back.parent = empty
        return empty

    build_chair("Chair_Protagonist", (-0.85, -1.0, 0.0))
    build_chair("Chair_Newcomer", (1.35, -0.8, 0.0))
    build_chair("Chair_Lead", (0.5, 1.6, math.pi))

    # Potted Plant beside window
    pot = add_cylinder("PlantPot", 0.24, 0.42, (-2.4, 2.4, 0.21), material=MATS["PlantPot"], collection=props_col)
    for leaf_i in range(5):
        ang = leaf_i * (2.0 * math.pi / 5)
        leaf = add_beveled_box(f"PlantLeaf_{leaf_i}", (0.12, 0.36, 0.02), (-2.4 + math.cos(ang) * 0.14, 2.4 + math.sin(ang) * 0.14, 0.52), material=MATS["PlantLeaf"], bevel_width=0.01, collection=props_col)
        leaf.rotation_euler = (0.35 * math.sin(ang), 0.35 * math.cos(ang), ang)

    # Floor path indicator / runner line for spacious newcomer walk path
    add_beveled_box("WalkPathFloor", (0.9, 3.2, 0.005), (0.25, 0.6, 0.005), material=MATS["FloorBoard"], bevel_width=0, collection=set_col)

# ---------------------------------------------------------------------------
# Printer & Paper Prop System
# ---------------------------------------------------------------------------

def build_printer_system(props_col):
    # Printer sits right beside protagonist desk: X: -1.85, Y: -0.4, Z: 0.0 (on low stand)
    printer_root = create_empty("Printer_Root", (-1.85, -0.35, 0.0), collection=props_col)
    stand = add_beveled_box("PrinterStand", (0.60, 0.60, 0.52), (0, 0, 0.26), material=MATS["WalnutWood"], bevel_width=0.015, collection=props_col)
    stand.parent = printer_root

    body = add_beveled_box("PrinterBody", (0.54, 0.50, 0.34), (0, 0, 0.69), material=MATS["PrinterIvory"], bevel_width=0.025, collection=props_col)
    body.parent = printer_root

    slot = add_beveled_box("PrinterSlot", (0.34, 0.12, 0.03), (0, -0.22, 0.75), material=MATS["PrinterDark"], bevel_width=0.005, collection=props_col)
    slot.parent = printer_root

    tray = add_beveled_box("PrinterTray", (0.30, 0.28, 0.02), (0, -0.32, 0.68), material=MATS["PrinterDark"], bevel_width=0.005, collection=props_col)
    tray.parent = printer_root

    panel = add_beveled_box("PrinterPanel", (0.16, 0.08, 0.02), (0.16, -0.18, 0.86), material=MATS["ChairSeatNavy"], bevel_width=0.004, collection=props_col)
    panel.parent = printer_root

    # Paper stack inside tray
    for p in range(2):
        st = add_beveled_box(f"PaperStack_{p}", (0.24, 0.32, 0.004), (0, -0.30, 0.692 + p * 0.005), material=MATS["PaperWhite"], bevel_width=0.001, collection=props_col)
        st.parent = printer_root

    # Active Printing Paper (slides out in Shot 1, picked up in Shot 6)
    active_paper = add_beveled_box("ActivePrintPaper", (0.22, 0.30, 0.003), (-1.85, -0.58, 0.70), material=MATS["PaperWhite"], bevel_width=0.001, collection=props_col)

    # Flashback Paper (carried by protagonist in Shot 2)
    fb_paper = add_beveled_box("FlashbackPaper", (0.22, 0.30, 0.004), (-0.85, -0.5, 0.80), material=MATS["PaperWhite"], bevel_width=0.001, collection=props_col)
    fb_paper.hide_render = False

    return active_paper, fb_paper

# ---------------------------------------------------------------------------
# Articulated Chibi Figures (Elbows/Shoulders/Hips/Knees Hierarchies)
# ---------------------------------------------------------------------------

def build_chibi_figure(name, base_pos, palette, col):
    fig_root = create_empty(f"{name}_Root", base_pos, collection=col)
    hips = create_empty(f"{name}_Hips", (0, 0, 0.62), collection=col)
    hips.parent = fig_root

    # Pelvis / Lower Torso
    pelvis = add_beveled_box(f"{name}_Pelvis", (0.34, 0.22, 0.16), (0, 0, 0.0), material=palette["pants"], bevel_width=0.02, collection=col)
    pelvis.parent = hips

    # Torso (Chest)
    chest = add_beveled_box(f"{name}_Chest", (0.36, 0.24, 0.32), (0, 0, 0.24), material=palette["shirt"], bevel_width=0.03, collection=col)
    chest.parent = hips

    # Shirt buttons / details
    if "button" in palette:
        for b_i in range(2):
            btn = add_sphere(f"{name}_Btn_{b_i}", 0.015, (0.0, -0.125, 0.20 + b_i * 0.08), material=palette["button"], collection=col)
            btn.parent = chest

    # Neck & Head (Chibi: ~1/3 total height, big expressive head)
    head_root = create_empty(f"{name}_Head", (0, 0, 0.44), collection=col)
    head_root.parent = hips

    neck = add_cylinder(f"{name}_Neck", 0.06, 0.08, (0, 0, -0.04), material=palette["skin"], collection=col)
    neck.parent = head_root

    head = add_beveled_box(f"{name}_HeadMesh", (0.42, 0.38, 0.40), (0, 0, 0.18), material=palette["skin"], bevel_width=0.06, collection=col)
    head.parent = head_root

    # Face Features: Eyes, Pupils, Nose, Mouth curve, Eyebrows
    eye_l = add_sphere(f"{name}_Eye_L", 0.032, (-0.11, -0.19, 0.18), material=MATS["EyeBlack"], collection=col)
    eye_l.parent = head_root
    eye_r = add_sphere(f"{name}_Eye_R", 0.032, (0.11, -0.19, 0.18), material=MATS["EyeBlack"], collection=col)
    eye_r.parent = head_root

    brow_l = add_beveled_box(f"{name}_Brow_L", (0.07, 0.015, 0.02), (-0.11, -0.20, 0.24), material=palette["hair"], bevel_width=0.003, collection=col)
    brow_l.parent = head_root
    brow_r = add_beveled_box(f"{name}_Brow_R", (0.07, 0.015, 0.02), (0.11, -0.20, 0.24), material=palette["hair"], bevel_width=0.003, collection=col)
    brow_r.parent = head_root

    nose = add_beveled_box(f"{name}_Nose", (0.04, 0.04, 0.05), (0, -0.20, 0.15), material=palette["skin"], bevel_width=0.01, collection=col)
    nose.parent = head_root

    mouth = add_beveled_box(f"{name}_Mouth", (0.08, 0.01, 0.015), (0, -0.192, 0.09), material=MATS["MouthRose"], bevel_width=0.002, collection=col)
    mouth.parent = head_root

    # Hair Pieces (layered bob or round hair)
    if palette.get("is_bob", False):
        # Protagonist Bob Hairstyle
        hair_top = add_beveled_box(f"{name}_HairTop", (0.46, 0.42, 0.18), (0, 0.02, 0.35), material=palette["hair"], bevel_width=0.05, collection=col)
        hair_top.parent = head_root
        hair_l = add_beveled_box(f"{name}_Hair_L", (0.10, 0.40, 0.36), (-0.21, 0.02, 0.16), material=palette["hair"], bevel_width=0.04, collection=col)
        hair_l.parent = head_root
        hair_r = add_beveled_box(f"{name}_Hair_R", (0.10, 0.40, 0.36), (0.21, 0.02, 0.16), material=palette["hair"], bevel_width=0.04, collection=col)
        hair_r.parent = head_root
        hair_back = add_beveled_box(f"{name}_HairBack", (0.44, 0.14, 0.38), (0, 0.17, 0.15), material=palette["hair"], bevel_width=0.04, collection=col)
        hair_back.parent = head_root
    else:
        # Round / Short Hair
        hair_dome = add_beveled_box(f"{name}_HairDome", (0.46, 0.42, 0.24), (0, 0.02, 0.32), material=palette["hair"], bevel_width=0.07, collection=col)
        hair_dome.parent = head_root

    # Glasses for Team Lead
    if palette.get("glasses", False):
        g_frame = add_beveled_box(f"{name}_Glasses", (0.34, 0.02, 0.08), (0, -0.21, 0.18), material=MATS["GlassesGold"], bevel_width=0.004, collection=col)
        g_frame.parent = head_root

    # Articulated Limbs with Parent Empties
    def build_arm(side, x_sign):
        sh_empty = create_empty(f"{name}_Shoulder_{side}", (x_sign * 0.22, 0, 0.34), collection=col)
        sh_empty.parent = hips
        u_arm = add_cylinder(f"{name}_UpperArm_{side}", 0.04, 0.18, (0, 0, -0.09), material=palette["shirt"], collection=col)
        u_arm.parent = sh_empty
        el_empty = create_empty(f"{name}_Elbow_{side}", (0, 0, -0.18), collection=col)
        el_empty.parent = sh_empty
        l_arm = add_cylinder(f"{name}_Forearm_{side}", 0.035, 0.16, (0, 0, -0.08), material=palette["skin"], collection=col)
        l_arm.parent = el_empty
        hand = add_sphere(f"{name}_Hand_{side}", 0.042, (0, 0, -0.18), material=palette["skin"], collection=col)
        hand.parent = el_empty
        return sh_empty, el_empty

    def build_leg(side, x_sign):
        hip_empty = create_empty(f"{name}_HipJoint_{side}", (x_sign * 0.11, 0, -0.06), collection=col)
        hip_empty.parent = hips
        thigh = add_cylinder(f"{name}_Thigh_{side}", 0.05, 0.24, (0, 0, -0.12), material=palette["pants"], collection=col)
        thigh.parent = hip_empty
        knee_empty = create_empty(f"{name}_Knee_{side}", (0, 0, -0.24), collection=col)
        knee_empty.parent = hip_empty
        calf = add_cylinder(f"{name}_Calf_{side}", 0.045, 0.24, (0, 0, -0.12), material=palette["pants"], collection=col)
        calf.parent = knee_empty
        foot = add_beveled_box(f"{name}_Foot_{side}", (0.09, 0.16, 0.07), (0, -0.04, -0.26), material=MATS["HairDark"], bevel_width=0.015, collection=col)
        foot.parent = knee_empty
        return hip_empty, knee_empty

    sh_l, el_l = build_arm("L", -1)
    sh_r, el_r = build_arm("R", 1)
    hip_l, kn_l = build_leg("L", -1)
    hip_r, kn_r = build_leg("R", 1)

    return {
        "root": fig_root,
        "hips": hips,
        "head": head_root,
        "brow_l": brow_l,
        "brow_r": brow_r,
        "sh_l": sh_l,
        "el_l": el_l,
        "sh_r": sh_r,
        "el_r": el_r,
        "hip_l": hip_l,
        "kn_l": kn_l,
        "hip_r": hip_r,
        "kn_r": kn_r,
    }

# ---------------------------------------------------------------------------
# Lighting Setup
# ---------------------------------------------------------------------------

def setup_lighting(light_col):
    # Warm key light through window
    key_data = bpy.data.lights.new(name="Key_Daylight", type="AREA")
    key_data.energy = 450.0
    key_data.size = 2.4
    key_data.color = (1.0, 0.94, 0.86)
    key_obj = bpy.data.objects.new("Key_Daylight", key_data)
    key_obj.location = (-4.0, 0.8, 3.2)
    key_obj.rotation_euler = (math.radians(35), math.radians(45), math.radians(-70))
    light_col.objects.link(key_obj)

    # Soft warm fill
    fill_data = bpy.data.lights.new(name="Fill_Warm", type="AREA")
    fill_data.energy = 180.0
    fill_data.size = 3.0
    fill_data.color = (0.95, 0.96, 1.0)
    fill_obj = bpy.data.objects.new("Fill_Warm", fill_data)
    fill_obj.location = (2.5, -2.5, 3.0)
    fill_obj.rotation_euler = (math.radians(45), 0, math.radians(35))
    light_col.objects.link(fill_obj)

    # Rim / Hair accent light
    rim_data = bpy.data.lights.new(name="Rim_Accent", type="AREA")
    rim_data.energy = 220.0
    rim_data.size = 1.8
    rim_data.color = (1.0, 0.88, 0.72)
    rim_obj = bpy.data.objects.new("Rim_Accent", rim_data)
    rim_obj.location = (-0.5, 3.2, 2.8)
    rim_obj.rotation_euler = (math.radians(-40), math.radians(20), math.radians(160))
    light_col.objects.link(rim_obj)

    # Ambient World
    if bpy.context.scene.world is None:
        bpy.context.scene.world = bpy.data.worlds.new("Office_Daylight")
    bpy.context.scene.world.use_nodes = True
    bg = bpy.context.scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.86, 0.84, 0.80, 1.0)
        bg.inputs["Strength"].default_value = 0.25

# 카메라와 동작은 refinements.py 의 setup_cameras, bake_story 가 만든다.

# ---------------------------------------------------------------------------
# Render & EEVEE Configuration (Blender 4.5+ / EEVEE_NEXT)
# ---------------------------------------------------------------------------

def configure_render_settings(scene, args):
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"  # Blender 5.x 는 엔진 식별자가 다르다
    scene.render.resolution_x = DEFAULT_WIDTH
    scene.render.resolution_y = DEFAULT_HEIGHT
    scene.render.resolution_percentage = args.resolution_percentage
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False

    # Color Management (AgX / Filmic warm diorama)
    if hasattr(scene.display_settings, "display_device"):
        scene.display_settings.display_device = "sRGB"
    if hasattr(scene.view_settings, "view_transform"):
        valid_transforms = [e.identifier for e in scene.view_settings.bl_rna.properties["view_transform"].enum_items]
        if "AgX" in valid_transforms:
            scene.view_settings.view_transform = "AgX"
        elif "Filmic" in valid_transforms:
            scene.view_settings.view_transform = "Filmic"
    if hasattr(scene.view_settings, "look"):
        scene.view_settings.look = "AgX - Medium High Contrast"

    # EEVEE-Next specific attributes (safe assignment)
    eevee = scene.eevee
    if hasattr(eevee, "taa_render_samples"):
        eevee.taa_render_samples = args.samples
    if hasattr(eevee, "shadow_pool_size"):
        try:
            eevee.shadow_pool_size = "256"
        except TypeError:
            pass
    if hasattr(eevee, "shadow_ray_count"):
        eevee.shadow_ray_count = 1
    if hasattr(eevee, "shadow_step_count"):
        eevee.shadow_step_count = 4
    if hasattr(eevee, "shadow_resolution_scale"):
        eevee.shadow_resolution_scale = 0.5
    if hasattr(eevee, "use_raytracing"):
        eevee.use_raytracing = False

# ---------------------------------------------------------------------------
# CLI & Main Entry Point
# ---------------------------------------------------------------------------

def parse_args():
    raw_args = sys.argv
    if "--" in raw_args:
        script_args = raw_args[raw_args.index("--") + 1 :]
    else:
        script_args = []

    parser = argparse.ArgumentParser(description="Procedural Blender Short Film Builder")
    parser.add_argument("--output-blend", type=str, required=True, help="Absolute path to output .blend file")
    parser.add_argument("--frames-dir", type=str, required=True, help="Directory for rendered PNG frames")
    parser.add_argument("--script", type=str, default=None, help="대본 JSON. 기본은 이 스크립트 옆의 script.json")
    parser.add_argument("--preview-frame", type=int, default=None, help="Optional single frame index to render preview")
    parser.add_argument("--resolution-percentage", type=int, default=100, help="Resolution percentage (e.g. 50 or 100)")
    parser.add_argument("--samples", type=int, default=16, help="EEVEE TAA render samples")
    parser.add_argument("--render-animation", action="store_true", help="Flag to trigger complete sequence render")
    return parser.parse_args(script_args)

def main():
    args = parse_args()

    # Ensure destination directories exist
    blend_dir = os.path.dirname(os.path.abspath(args.output_blend))
    if blend_dir and not os.path.exists(blend_dir):
        os.makedirs(blend_dir, exist_ok=True)
    frames_dir = os.path.abspath(args.frames_dir)
    if not os.path.exists(frames_dir):
        os.makedirs(frames_dir, exist_ok=True)

    # 대본을 읽는다: 길이, 구간(장면), 대화 시각
    global SCRIPT, SHOT_TIMELINES, TOTAL_FRAMES, FPS
    script_path = args.script or os.path.join(os.path.dirname(os.path.abspath(__file__)), "script.json")
    with open(script_path, "r", encoding="utf-8") as f:
        SCRIPT = json.load(f)
    FPS = int(SCRIPT.get("fps", 24))
    TOTAL_FRAMES = int(SCRIPT["frames"])
    SHOT_TIMELINES = [{"id": b["id"], "name": f"{i + 1:02d}_{b['id']}", "start": float(b["start"]), "end": float(b["end"])}
                      for i, b in enumerate(SCRIPT["beats"])]
    SHOT_TIMELINES[-1]["end"] = TOTAL_FRAMES / FPS

    # Reset factory scene
    reset_scene()
    scene = bpy.context.scene

    # Build collections hierarchy
    set_col = get_or_create_collection("Set")
    chars_col = get_or_create_collection("Characters")
    props_col = get_or_create_collection("Props")
    cams_col = get_or_create_collection("Cameras")
    lights_col = get_or_create_collection("Lights")

    # 1. Initialize Materials
    init_materials()

    # 2. Build Set & Props
    build_office_set(set_col, props_col)
    active_paper, fb_paper = build_printer_system(props_col)

    # 3. Build Characters
    protagonist_palette = {
        "skin": MATS["SkinWarm"],
        "hair": MATS["HairDark"],
        "shirt": MATS["BlouseTeal"],
        "pants": MATS["TrousersDark"],
        "button": MATS["PaperWhite"],
        "is_bob": True,
    }
    newcomer_palette = {
        "skin": MATS["SkinWarm"],
        "hair": MATS["HairDark"],
        "shirt": MATS["ShirtCoral"],
        "pants": MATS["ChairSeatNavy"],
        "is_bob": False,
    }
    lead_palette = {
        "skin": MATS["SkinLead"],
        "hair": MATS["HairDark"],
        "shirt": MATS["LeadNavy"],
        "pants": MATS["TrousersDark"],
        "glasses": True,
        "is_bob": False,
    }

    protagonist = build_chibi_figure("Protagonist", (-0.85, -0.9, 0.0), protagonist_palette, chars_col)
    newcomer = build_chibi_figure("Newcomer", (1.35, -0.7, 0.0), newcomer_palette, chars_col)
    lead = build_chibi_figure("TeamLead", (0.5, 2.7, 0.0), lead_palette, chars_col)
    lead["root"].rotation_euler[2] = math.pi

    # Reviewed foundation plus main-agent mesh, composition and articulation finishing.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import refinements
    this = sys.modules[__name__]
    refinements.enhance_characters(this, (protagonist, newcomer, lead))

    # 4. Setup Lighting
    setup_lighting(lights_col)
    refinements.enhance_set(this)

    # 5. Setup Cameras & Timeline Markers
    cameras = refinements.setup_cameras(this, cams_col)
    scene.camera = cameras[SHOT_TIMELINES[0]["id"]]

    # 6. Author Animation & Keyframes
    refinements.bake_story(this, (protagonist, newcomer, lead), active_paper, fb_paper, cameras)

    # 7. Configure Render Properties
    configure_render_settings(scene, args)

    # Always save the editable .blend file
    output_blend_path = os.path.abspath(args.output_blend)
    bpy.ops.wm.save_as_mainfile(filepath=output_blend_path)

    # Optional Preview or Full Render
    if args.preview_frame is not None:
        scene.frame_set(args.preview_frame)
        preview_path = os.path.join(frames_dir, f"preview_{args.preview_frame:04d}.png")
        scene.render.filepath = preview_path
        bpy.ops.render.render(write_still=True)

    if args.render_animation:
        scene.render.filepath = os.path.join(frames_dir, "frame_####.png")
        bpy.ops.render.render(animation=True)

    # Print compact JSON metadata for bridge runner
    metadata = {
        "blend_path": output_blend_path,
        "frames_dir": frames_dir,
        "frame_count": TOTAL_FRAMES,
        "fps": FPS,
        "resolution": [DEFAULT_WIDTH, DEFAULT_HEIGHT],
        "resolution_percentage": args.resolution_percentage,
        "shots": [s["id"] for s in SHOT_TIMELINES],
        "cameras_count": len(cameras),
        "status": "completed"
    }
    print(json.dumps(metadata))

if __name__ == "__main__":
    main()
