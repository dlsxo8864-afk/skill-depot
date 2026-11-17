"""블렌더 사물극: 사람 없이 책상 위 물건(휴대폰·시계·서류·도장)으로 이야기를 찍는다. 작업 폴더에서 실행.

사용: blender -b --python-exit-code 1 -P build_ssul.py -- --assets <Poly Haven 소재 폴더>
- 먼저 screens.py 를 돌려 작업 폴더에 screens/, tex/ 가 있어야 한다.
- --assets 를 안 주면 작업 폴더의 assets/ 를 쓴다. 필요한 소재는 SKILL.md 와 dl_assets.py 참고.
결과: 작업 폴더의 scene.blend

대본에 딸린 프레임(진동·도장·컷·빛·시계)은 전부 plan.py 에서 읽는다. 이 파일에는 장면의 생김새만 있다.
블렌더 프레임은 1부터라서 plan.py 의 프레임(0부터)에 1을 더해 쓴다.
"""
import argparse
import math
import os
import random
import sys

import bpy
from mathutils import Vector

ROOT = os.getcwd()
_argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
_ap = argparse.ArgumentParser(prog="build_ssul.py")
_ap.add_argument("--assets", default=os.path.join(ROOT, "assets"), help="Poly Haven 소재 폴더(models, tex, hdri 가 든 곳)")
AS = os.path.abspath(_ap.parse_args(_argv).assets)
# 이 장면이 읽는 소재 파일(소재 폴더 기준). 소품을 바꾸면 여기와 dl_assets.py 의 MODELS 를 같이 고친다
NEED = [
    "models/desk_lamp_arm_01/desk_lamp_arm_01_1k.gltf",
    "models/classic_laptop/classic_laptop_1k.gltf",
    "models/office_notepads/office_notepads_1k.gltf",
    "models/alarm_clock_01/alarm_clock_01_1k.gltf",
    "tex/wood_table_worn/wood_table_worn_diff_2k.jpg",
    "tex/wood_table_worn/wood_table_worn_rough_2k.jpg",
    "tex/wood_table_worn/wood_table_worn_nor_gl_2k.jpg",
    "tex/painted_plaster_wall/painted_plaster_wall_diff_2k.jpg",
    "tex/painted_plaster_wall/painted_plaster_wall_rough_2k.jpg",
    "tex/painted_plaster_wall/painted_plaster_wall_nor_gl_2k.jpg",
    "hdri/studio_small_09_2k.hdr",
]
_missing = [p for p in NEED if not os.path.isfile(os.path.join(AS, p))]
if not os.path.isfile(os.path.join(ROOT, "screens", "s0001.png")) or not os.path.isfile(os.path.join(ROOT, "tex", "paper.png")):
    raise SystemExit("작업 폴더에 screens/ 와 tex/ 가 없습니다. 먼저 screens.py 를 돌리세요: " + ROOT)
if _missing:
    raise SystemExit("소재가 없습니다(--assets " + AS + "):\n  " + "\n  ".join(_missing))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan  # noqa: E402

random.seed(11)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection
FPS = plan.FPS
TOTAL = plan.TOTAL


def tex(nt, path, non_color=False):
    n = nt.nodes.new("ShaderNodeTexImage")
    n.image = bpy.data.images.load(path)
    if non_color:
        n.image.colorspace_settings.name = "Non-Color"
    return n


def pbr(name, base, scale=1.0, value=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    uv = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])
    d = tex(nt, f"{AS}/tex/{base}/{base}_diff_2k.jpg")
    r = tex(nt, f"{AS}/tex/{base}/{base}_rough_2k.jpg", True)
    n = tex(nt, f"{AS}/tex/{base}/{base}_nor_gl_2k.jpg", True)
    for x in (d, r, n):
        nt.links.new(mp.outputs["Vector"], x.inputs["Vector"])
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Value"].default_value = value
    nt.links.new(d.outputs["Color"], hsv.inputs["Color"])
    nt.links.new(hsv.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(r.outputs["Color"], p.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(n.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
    return m


def flat(name, color, rough=0.4, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    return m


def box(name, size, loc, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    me = o.data
    uvl = me.uv_layers.active or me.uv_layers.new()
    for poly in me.polygons:
        nx, ny, nz = [abs(v) for v in poly.normal]
        for li in poly.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co
            u, v = (c.x, c.y) if nz >= nx and nz >= ny else (c.x, c.z) if ny >= nx else (c.y, c.z)
            uvl.data[li].uv = (u, v)
    me.materials.append(mat)
    if bevel:
        b = o.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = 6
        for p in me.polygons:
            p.use_smooth = True
        o.modifiers.new("wn", "WEIGHTED_NORMAL")
    return o


def imported(name, res, loc, rot_z=0.0, scale=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f"{AS}/models/{name}/{name}_{res}.gltf")
    e = bpy.data.objects.new(name + "_root", None)
    col.objects.link(e)
    for o in bpy.data.objects:
        if o not in before and o.parent is None and o is not e:
            o.parent = e
    e.location = loc
    e.rotation_euler = (0, 0, math.radians(rot_z))
    e.scale = (scale, scale, scale)
    return e


def plane_image(name, img, size, loc, rot, emission=0.0, alpha=False):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0], size[1], 1)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
    if emission:
        nt.links.new(t.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = emission
        p.inputs["Roughness"].default_value = 0.12
    else:
        p.inputs["Roughness"].default_value = 0.72
    if alpha:
        nt.links.new(t.outputs["Alpha"], p.inputs["Alpha"])
    o.data.materials.append(m)
    return o, t


def key_visible(o, ranges):
    """ranges: 보이는 프레임 구간 목록"""
    for f in range(0, TOTAL + 2):
        vis = any(a <= f <= b for a, b in ranges)
        if f == 0 or vis != prev:
            o.hide_render = not vis
            o.hide_viewport = not vis
            o.keyframe_insert("hide_render", frame=f)
            o.keyframe_insert("hide_viewport", frame=f)
        prev = vis


# 책상·벽·소품. 자리는 미터. 소품을 바꾸면 NEED 와 dl_assets.py 의 MODELS 도 고친다
box("table", (2.6, 1.5, 0.05), (0, 0.1, -0.025), pbr("wood", "wood_table_worn", 1.1, 1.0))
box("wall", (4.0, 0.05, 2.5), (0, 0.72, 0.9), pbr("plaster", "painted_plaster_wall", 0.7, 0.9))
imported("desk_lamp_arm_01", "1k", (-0.42, 0.34, 0.0), rot_z=-30)
imported("classic_laptop", "1k", (0.50, 0.50, 0.0), rot_z=205, scale=1.0)
notepads = imported("office_notepads", "1k", (-0.34, 0.10, 0.0), rot_z=18)
for c in list(notepads.children):
    if "note_stack" not in c.name:
        bpy.data.objects.remove(c, do_unlink=True)
imported("alarm_clock_01", "1k", (0.27, 0.02, 0.0), rot_z=-30)

# 유리: 그림자는 통과
for m in bpy.data.materials:
    if m.use_nodes and "glass" in m.name.lower():
        nt = m.node_tree
        pr = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        for name in ("Base Color", "Transmission Weight", "Roughness", "Alpha"):
            for link in list(pr.inputs[name].links):
                nt.links.remove(link)
        pr.inputs["Base Color"].default_value = (1, 1, 1, 1)
        pr.inputs["Transmission Weight"].default_value = 1.0
        pr.inputs["Roughness"].default_value = 0.03
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        lp = nt.nodes.new("ShaderNodeLightPath")
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs["Fac"])
        nt.links.new(pr.outputs[0], mx.inputs[1])
        nt.links.new(tr.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])

# 휴대폰: 코드로 만든 본체 + 화면 이미지 시퀀스
PW, PH = 0.074, 0.160
phone = bpy.data.objects.new("phone", None)
col.objects.link(phone)
body = box("phone_body", (PW, PH, 0.0085), (0, 0, 0.0042), flat("phone_black", (0.012, 0.012, 0.016), 0.28, 0.65), bevel=0.003)
body.parent = phone
img = bpy.data.images.load(os.path.join(ROOT, "screens", "s0001.png"))
img.source = "SEQUENCE"
scr, t = plane_image("screen", img, (PW - 0.006, PH - 0.0062), (0, 0, 0.0088), (0, 0, 0), emission=1.5)
t.image_user.frame_duration = TOTAL
t.image_user.frame_start = 1
t.image_user.frame_offset = 0
t.image_user.use_auto_refresh = True
scr.parent = phone
phone.location = (0.0, -0.06, 0.0)
phone.rotation_euler = (0, 0, math.radians(-4))
base = phone.location.copy()
rot = phone.rotation_euler.copy()


def buzz(start, end):
    r = random.Random(start)
    phone.location = base
    phone.keyframe_insert("location", frame=start - 1)
    for f in range(start, end):
        phone.location = base + Vector((r.uniform(-1, 1) * 0.0011, r.uniform(-1, 1) * 0.0011, 0))
        phone.keyframe_insert("location", frame=f)
    phone.location = base
    phone.keyframe_insert("location", frame=end)


# 휴대폰 진동: 알림이 뜨는 구간(plan.BUZZ)
for _a, _b in plan.BUZZ:
    buzz(_a + 1, _b + 1)

# 품의서·도장
paper_img = bpy.data.images.load(os.path.join(ROOT, "tex", "paper.png"))
paper, _ = plane_image("paper", paper_img, (0.21, 0.297), (0.0, -0.08, 0.0012), (0, 0, math.radians(3)))
mark_img = bpy.data.images.load(os.path.join(ROOT, "tex", "stamp_mark.png"))
mark, _ = plane_image("mark", mark_img, (0.135, 0.063), (0.0, -0.148, 0.0018), (0, 0, math.radians(-7)), alpha=True)
wood_s = flat("stamp_wood", (0.32, 0.14, 0.05), 0.45)
stamp = bpy.data.objects.new("stamp", None)
col.objects.link(stamp)
a = box("stamp_base", (0.16, 0.075, 0.03), (0, 0, 0.015), wood_s, bevel=0.003)
a.parent = stamp
bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.105, vertices=48, location=(0, 0, 0.082))
h = bpy.context.object
h.data.materials.append(wood_s)
h.modifiers.new("b", "BEVEL").width = 0.003
for p in h.data.polygons:
    p.use_smooth = True
h.parent = stamp
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(0, 0, 0.15))
k = bpy.context.object
k.data.materials.append(flat("stamp_knob", (0.05, 0.03, 0.03), 0.35))
for p in k.data.polygons:
    p.use_smooth = True
k.parent = stamp
stamp.rotation_euler = (0, 0, math.radians(-7))
# 도장: 서류 컷이 시작하면 떠 있다가 내려찍고 다시 올라간다. 대본에 도장이 없으면 서류·도장을 숨긴다
if plan.STAMP:
    IMPACT = plan.IMPACT + 1
    DOC = [(plan.DOC_FROM + 1, TOTAL + 1)]
    PHONE = [(0, plan.DOC_FROM)]
    for f, z in [(plan.DOC_FROM + 1, 0.42), (IMPACT - 8, 0.42), (IMPACT - 3, 0.30), (IMPACT, 0.0015), (IMPACT + 6, 0.0015), (IMPACT + 16, 0.42)]:
        stamp.location = (0.0, -0.148, z)
        stamp.keyframe_insert("location", frame=f)
else:
    IMPACT = TOTAL + 10
    DOC = []
    PHONE = [(0, TOTAL + 1)]
for o in (paper, stamp, a, h, k):
    key_visible(o, DOC)
key_visible(mark, [(IMPACT + 1, TOTAL + 1)])
for o in (phone, body, scr):
    key_visible(o, PHONE)

# 빛: 창에서 든 햇빛 + 창살 그림자. 세기·색·배경 밝기는 plan.LIGHT 표대로 바뀐다(표 사이는 서서히)
d = Vector((0.72, 0.52, -0.46)).normalized()
sd = bpy.data.lights.new("sun", "SUN")
sd.angle = math.radians(1.4)
sun = bpy.data.objects.new("sun", sd)
col.objects.link(sun)
q = d.to_track_quat("-Z", "Y")
sun.rotation_euler = q.to_euler()
br = sun.rotation_euler.copy()
if plan.CLOCK:  # 시계 컷 동안 해가 돌아 그림자가 움직인다
    sun.keyframe_insert("rotation_euler", frame=plan.CLOCK[0] + 1)
    sun.rotation_euler = (br.x + math.radians(4), br.y, br.z - math.radians(10))
    sun.keyframe_insert("rotation_euler", frame=plan.CLOCK[1])
for f, en, co, _s in plan.LIGHT:
    sd.energy = en
    sd.color = co
    sd.keyframe_insert("energy", frame=f)
    sd.keyframe_insert("color", frame=f)

world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
wt = world.node_tree
env = wt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(f"{AS}/hdri/studio_small_09_2k.hdr")
bg = wt.nodes["Background"]
wt.links.new(env.outputs["Color"], bg.inputs["Color"])
for f, _en, _co, s in plan.LIGHT:
    bg.inputs["Strength"].default_value = s
    bg.inputs["Strength"].keyframe_insert("default_value", frame=f)

g = bpy.data.objects.new("gobo", None)
col.objects.link(g)
g.location = Vector((-0.06, -0.02, 0.05)) - d * 2.2
g.rotation_mode = "QUATERNION"
g.rotation_quaternion = q
black = bpy.data.materials.new("b")


def shadow_only(o):
    o.visible_camera = False
    o.visible_diffuse = False
    o.visible_glossy = False
    o.visible_transmission = False
    o.visible_volume_scatter = False


for n, sx, sy, x, y in [("l", 3, 6, -2.12, 0), ("r", 3, 6, 2.12, 0), ("t", 6, 3, 0, 2.22), ("b", 6, 3, 0, -2.22), ("mv", 0.035, 2, 0.02, 0), ("mh", 2, 0.03, 0, 0.1)]:
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    o.name = "g_" + n
    o.scale = (sx, sy, 0.02)
    o.location = (x, y, 0)
    o.parent = g
    o.data.materials.append(black)
    shadow_only(o)

# 시계 바늘: plan.CLOCK_START 만큼 미리 돌려 시작 시각을 맞추고, 시계 컷 동안 plan.CLOCK_TURNS 바퀴만큼 돈다
for (prefix, turns), start in zip((("minute_hand", plan.CLOCK_TURNS[0]), ("houd_hand", plan.CLOCK_TURNS[1])), plan.CLOCK_START):
    hand = next(o for o in bpy.data.objects if o.name.startswith(prefix))
    hand.rotation_mode = "XYZ"
    y0 = hand.rotation_euler.y + start * 2 * math.pi  # 이 소재는 +Y 회전이 시계 방향이다
    hand.rotation_euler.y = y0
    if plan.CLOCK:
        hand.keyframe_insert("rotation_euler", index=1, frame=plan.CLOCK[0] + 1)
        hand.rotation_euler.y = y0 + turns * 2 * math.pi
        hand.keyframe_insert("rotation_euler", index=1, frame=plan.CLOCK[1])

# 카메라는 샷마다 고정한다
# 이름: (위치, 바라볼 점, 렌즈 mm, 조리개, 초점 점). 이름은 plan.py 의 SHOTS 에서 쓴다
CAMS = {
    "phone": ((0.0, -0.17, 0.335), (0.0, -0.062, 0.0), 58, 6.3, (0.0, -0.06, 0.004)),
    "wide": ((-0.05, -0.98, 0.30), (0.0, 0.1, 0.07), 42, 3.5, (0.0, -0.06, 0.004)),
    "macro": ((0.05, -0.36, 0.145), (0.0, -0.045, 0.005), 56, 5.0, (0.0, -0.06, 0.008)),
    "clock": ((-0.005, -0.458, 0.105), (0.27, 0.02, 0.09), 62, 4.0, (0.27, 0.0, 0.09)),
    "doc": ((0.0, -0.40, 0.40), (0.0, -0.08, 0.0), 45, 4.5, (0.0, -0.08, 0.002)),
}
for name, (loc, tgt, lens, fs, focus) in CAMS.items():
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fs
    cam = bpy.data.objects.new("cam_" + name, cd)
    col.objects.link(cam)
    cam.location = loc
    t_ = bpy.data.objects.new(name + "_t", None)
    f_ = bpy.data.objects.new(name + "_f", None)
    col.objects.link(t_)
    col.objects.link(f_)
    t_.location = tgt
    f_.location = focus
    c = cam.constraints.new("TRACK_TO")
    c.target = t_
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    cd.dof.focus_object = f_

scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, TOTAL
scene.render.engine = "CYCLES"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.camera = bpy.data.objects["cam_phone"]
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
print("SAVED", len(bpy.data.objects))
