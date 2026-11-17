"""작동 원리 해부 장면(가상의 장치)을 조립해 scene.blend 로 저장한다. 작업 폴더에서 실행.

사용: blender -b --python-exit-code 1 -P create_scene.py
- 먼저 cards.py 를 돌려 작업 폴더에 tex/ 가 있어야 한다.
- 장치: 투입구(등장인물마다 하나) → 저장통 → 밸브 → 배출구. 옆에 시계 창·압력계, 저장통 옆에 눈금자.
- 겉을 보여 준 뒤 앞판이 투명해지고, 구간마다 속에서 일이 벌어진다. 무엇이 언제 일어나는지는 plan.py 에서 읽는다.
블렌더 프레임은 1부터라서 plan 의 프레임(0부터)에 1을 더한다.
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan  # noqa: E402

ROOT = os.getcwd()
if not os.path.isfile(os.path.join(ROOT, "tex", "dial.png")):
    raise SystemExit("작업 폴더에 tex/ 가 없습니다. 먼저 cards.py 를 돌리세요: " + ROOT)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection
TOTAL = plan.TOTAL
BEAT = {k: (a + 1, b) for k, (a, b) in plan.BEAT.items()}  # 구간의 블렌더 프레임 (첫, 끝)
CAST = [c["id"] for c in plan.S["cast"]]


# ── 도구 ────────────────────────────────────────────────────────────
def flat(name, color, rough=0.5, emit=0.0, alpha=1.0, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if emit:
        p.inputs["Emission Color"].default_value = (*color, 1)
        p.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        p.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    return m


def finish(o, name, mat, parent=None, bevel=0.0):
    o.name = name
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    if bevel:
        b = o.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = 6
    if parent is not None:
        o.parent = parent
    return o


def box(name, size, loc, mat, parent=None, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)  # 크기만 굳힌다
    return finish(o, name, mat, parent, bevel)


def cyl(name, radius, depth, loc, mat, parent=None, bevel=0.0, rot=(0, 0, 0), r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, vertices=48, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(radius1=radius, radius2=r2, depth=depth, vertices=48, location=loc, rotation=rot)
    return finish(bpy.context.object, name, mat, parent, bevel)


def ball(name, radius, loc, mat, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc)
    return finish(bpy.context.object, name, mat, parent)


def pipe(name, p0, p1, radius, mat):
    """두 점을 잇는 관."""
    dx, dy, dz = (p1[i] - p0[i] for i in range(3))
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    o = cyl(name, radius, length, tuple((p0[i] + p1[i]) / 2 for i in range(3)), mat)
    o.rotation_euler = (0, math.acos(dz / length), math.atan2(dy, dx))
    return o


def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    col.objects.link(e)
    e.location = loc
    if parent is not None:
        e.parent = parent
    return e


def picture(name, png, height, loc, emission=0.6, width=None):
    """그림 한 장을 세운 판(앞 -Y 를 본다). height 를 주면 폭은 그림 비율대로."""
    img = bpy.data.images.load(os.path.join(ROOT, "tex", png))
    w = width or height * img.size[0] / img.size[1]
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=(math.pi / 2, 0, 0))
    o = bpy.context.object
    o.name = name
    o.scale = (w, height, 1)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(t.outputs["Color"], p.inputs["Emission Color"])
    p.inputs["Emission Strength"].default_value = emission
    nt.links.new(t.outputs["Alpha"], p.inputs["Alpha"])
    m.surface_render_method = "BLENDED"
    o.data.materials.append(m)
    return o


def show(objs, ranges):
    for o in objs if isinstance(objs, (list, tuple)) else [objs]:
        prev = None
        for f in range(0, TOTAL + 2):
            vis = any(a <= f <= b for a, b in ranges)
            if vis != prev:
                o.hide_render = not vis
                o.hide_viewport = not vis
                o.keyframe_insert("hide_render", frame=f)
                o.keyframe_insert("hide_viewport", frame=f)
            prev = vis


def key(o, attr, frame, value):
    setattr(o, attr, value)
    o.keyframe_insert(attr, frame=frame)


def aim(o, target):
    c = o.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"


# ── 작업장 ──────────────────────────────────────────────────────────
box("floor", (30, 30, 0.1), (0, 4, -0.05), flat("floor", (0.42, 0.45, 0.50), rough=0.7))
box("wall", (30, 0.2, 14), (0, 3.2, 7), flat("wall", (0.50, 0.54, 0.60), rough=0.9))
world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.78, 0.82, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.22
center = empty("light_target", (0, 0, 1.2))
for name, kind, loc, energy, size in (("key", "AREA", (-2.6, -4.2, 4.2), 230, 3.5), ("fill", "AREA", (3.2, -3.4, 2.4), 80, 3.0), ("back", "AREA", (0.5, 2.2, 3.4), 90, 2.5)):
    d = bpy.data.lights.new(name, kind)
    d.energy = energy
    d.size = size
    o = bpy.data.objects.new(name, d)
    col.objects.link(o)
    o.location = loc
    aim(o, center)

# ── 재질 ────────────────────────────────────────────────────────────
A = plan.ACCENT
m_shell = flat("shell", (0.80, 0.82, 0.85), rough=0.45)
m_inside = flat("inside", (0.10, 0.13, 0.19), rough=0.8)
m_accent = flat("accent", A, rough=0.4)
m_metal = flat("metal", (0.55, 0.58, 0.62), rough=0.3, metal=0.8)
m_glass = flat("glass", (0.70, 0.88, 1.0), rough=0.05, alpha=0.2)
m_dark = flat("dark", (0.04, 0.05, 0.07), rough=0.4)
m_grey = flat("ball_grey", (0.72, 0.74, 0.78), rough=0.35)
m_me = flat("ball_me", A, rough=0.35, emit=0.5)
m_flow = flat("flow", (0.25, 0.75, 1.0), emit=5.0)

# ── 장치 몸통: 폭 1.3 × 깊이 0.9 × 높이 1.9, 다리 위에 선다 ──────────────
W, D, Z0, Z1 = 1.3, 0.9, 0.3, 2.2
box("back", (W, 0.04, Z1 - Z0), (0, D / 2, (Z0 + Z1) / 2), m_inside)
for sx in (-1, 1):
    box(f"side_{sx}", (0.04, D, Z1 - Z0), (sx * W / 2, 0, (Z0 + Z1) / 2), m_shell)
    for sy in (-1, 1):
        cyl(f"leg_{sx}{sy}", 0.04, Z0, (sx * (W / 2 - 0.08), sy * (D / 2 - 0.08), Z0 / 2), m_metal)
box("top", (W + 0.04, D + 0.04, 0.05), (0, 0, Z1), m_shell, bevel=0.012)
box("bottom", (W + 0.04, D + 0.04, 0.05), (0, 0, Z0), m_shell, bevel=0.012)
front_mat = flat("front", (0.80, 0.82, 0.85), rough=0.45, alpha=0.999)  # 앞판: 속을 볼 때 투명해진다
front = box("front", (W, 0.03, Z1 - Z0), (0, -D / 2, (Z0 + Z1) / 2), front_mat)
stripe_mat = flat("stripe", A, rough=0.4, alpha=0.999)
box("stripe", (W, 0.034, 0.16), (0, -D / 2 - 0.002, 1.86), stripe_mat)
OPEN = BEAT[plan.ORDER[1]][0] if len(plan.ORDER) > 1 else TOTAL  # 둘째 구간이 시작할 때 연다
for m, lo in ((front_mat, 0.07), (stripe_mat, 0.18)):
    sock = m.node_tree.nodes["Principled BSDF"].inputs["Alpha"]
    for f, v in ((1, 0.999), (OPEN - 2, 0.999), (OPEN + 12, lo)):
        sock.default_value = v
        sock.keyframe_insert("default_value", frame=f)

# 투입구: 등장인물마다 깔때기 하나 + 이름표
FX = {cid: (i - (len(CAST) - 1) / 2) * 0.42 for i, cid in enumerate(CAST)}
funnel_tags = []
for cid, x in FX.items():
    cyl(f"funnel_{cid}", 0.06, 0.26, (x, 0, Z1 + 0.15), m_metal, r2=0.17)
    pipe(f"drop_{cid}", (x, 0, Z1 + 0.03), (x * 0.45, 0, 1.76), 0.03, m_metal)
    funnel_tags.append(picture(f"funnel_tag_{cid}", f"funnel_{cid}.png", 0.15, (x, -0.02, Z1 + 0.5)))
show(funnel_tags, [(1, BEAT[plan.ORDER[1]][1] if len(plan.ORDER) > 1 else TOTAL)])

# 저장통(유리) + 눈금자 + 높이 화살표
TZ0, TZ1, TR = 1.0, 1.76, 0.36
cyl("tank", TR, TZ1 - TZ0, (0, 0, (TZ0 + TZ1) / 2), m_glass)
for z in (TZ0, TZ1):
    cyl(f"tank_ring_{z}", TR + 0.015, 0.035, (0, 0, z), m_metal)
ruler = picture("ruler", "ruler.png", TZ1 - TZ0, (TR + 0.16, -0.05, (TZ0 + TZ1) / 2), width=0.18)
arrow = cyl("ruler_arrow", 0.05, 0.1, (TR + 0.03, -0.06, TZ0), m_accent, rot=(0, math.pi / 2, 0), r2=0.0)

# 구슬: 대화 하나가 구슬 하나. 깔때기에서 떨어져 저장통에 차례로 쌓인다
R = 0.085
SPOTS = [(-0.17, TZ0 + R + 0.02), (0.01, TZ0 + R + 0.02), (0.19, TZ0 + R + 0.02), (-0.08, TZ0 + 2.7 * R), (0.10, TZ0 + 2.7 * R), (0.01, TZ0 + 4.4 * R)]
balls = []
for i, (f0, who) in enumerate(plan.BALLS[: len(SPOTS)]):
    f = f0 + 1
    x0, (x1, z1) = FX.get(who, 0), SPOTS[i]
    b = ball(f"ball_{i}", R, (x0, 0, Z1 + 0.6), m_me if who == plan.ME else m_grey)
    for ff, pos in ((f - 5, (x0, 0, Z1 + 0.6)), (f, (x0, 0, Z1 + 0.12)), (f + 5, (x0 * 0.45, 0, 1.7)), (f + 9, (x1, 0, z1)), (f + 11, (x1, 0, z1 + 0.035)), (f + 13, (x1, 0, z1))):
        key(b, "location", ff, pos)
    balls.append((b, f - 5, x1, z1))

# 옆 계기 기둥: 시계 창 + 압력계
PX = W / 2 + 0.42
cyl("post", 0.03, 2.3, (PX, 0.05, 1.15), m_metal)
cyl("post_base", 0.16, 0.04, (PX, 0.05, 0.02), m_metal)
box("clock_case", (0.52, 0.08, 0.26), (PX, 0, 2.1), m_dark, bevel=0.02)
clock = {k: picture(f"clock_{k}", f"clock_{k}.png", 0.2, (PX, -0.045, 2.1), emission=1.2) for k in ("from", "to")}
cyl("gauge_case", 0.27, 0.07, (PX, 0, 1.52), m_dark, rot=(math.pi / 2, 0, 0))
picture("dial", "dial.png", 0.5, (PX, -0.04, 1.52))
needle_pivot = empty("needle", (PX, -0.05, 1.52))
box("needle_box", (0.022, 0.012, 0.21), (0, 0, 0.085), flat("needle", (0.85, 0.1, 0.12), emit=0.5), needle_pivot)
cyl("needle_hub", 0.03, 0.02, (PX, -0.055, 1.52), m_dark, rot=(math.pi / 2, 0, 0))


def needle_angle(g):
    return math.radians(-135 + 270 * g)  # 앞에서 볼 때 +Y 회전이 시계 방향


g0, g1 = plan.GAUGE.get("from", 0.2), plan.GAUGE.get("to", 1.0)
if "wait" in BEAT:
    a, b = BEAT["wait"]
    key(needle_pivot, "rotation_euler", a, (0, needle_angle(g0), 0))
    key(needle_pivot, "rotation_euler", b - 8, (0, needle_angle(g1), 0))
    for f in range(b - 8, b + 1, 2):  # 끝까지 차면 바늘이 떤다
        key(needle_pivot, "rotation_euler", f, (0, needle_angle(g1) + math.radians(3 if f % 4 else -3), 0))
    key(arrow, "location", a, (TR + 0.03, -0.06, TZ0 + (TZ1 - TZ0) * g0))
    key(arrow, "location", b - 8, (TR + 0.03, -0.06, TZ0 + (TZ1 - TZ0) * g1))
    mid = (a + b) // 2  # 가운데에서 시계 창이 바뀐다
    show(clock["from"], [(1, mid)])
    show(clock["to"], [(mid + 1, TOTAL + 1)])
else:
    needle_pivot.rotation_euler = (0, needle_angle(g0), 0)
    arrow.location = (TR + 0.03, -0.06, TZ0 + (TZ1 - TZ0) * g0)
    show(clock["to"], [])

# 밸브와 배출: 저장통 아래 → 밸브 → 배출구(앞쪽)
VZ = 0.74
pipe("down", (0, 0, TZ0), (0, 0, VZ + 0.1), 0.045, m_metal)
ball("valve_body", 0.11, (0, 0, VZ), m_metal)
lever_pivot = empty("lever", (0, -0.1, VZ))
box("lever_arm", (0.05, 0.05, 0.36), (0, -0.03, 0.17), m_accent, lever_pivot, bevel=0.015)
ball("lever_knob", 0.055, (0, -0.03, 0.36), m_accent, lever_pivot)
OUT = (0, -D / 2 - 0.16, 0.46)  # 배출구 끝
pipe("out_a", (0, 0, VZ - 0.08), (0, 0, 0.5), 0.045, m_metal)
pipe("out_b", (0, 0, 0.5), OUT, 0.045, m_metal)
cyl("out_mouth", 0.07, 0.05, OUT, m_accent, rot=(math.pi / 2, 0, 0))
box("tray", (0.7, 0.5, 0.03), (0, -D / 2 - 0.42, 0.26), m_shell, bevel=0.01)
for sx in (-1, 1):
    cyl(f"tray_leg_{sx}", 0.025, 0.25, (sx * 0.28, -D / 2 - 0.42, 0.125), m_metal)
VALVE = plan.VALVE_AT + 1
key(lever_pivot, "rotation_euler", VALVE - 1, (0, 0, 0))
key(lever_pivot, "rotation_euler", VALVE + 8, (0, math.radians(-82), 0))  # 레버가 옆으로 눕는다
PATH = [(0, 0, TZ0 - 0.02), (0, 0, VZ), (0, 0, 0.5), OUT]
for i in range(7):  # 관 속을 흐르는 빛나는 구
    s = ball(f"flow_{i}", 0.032, PATH[0], m_flow)
    f = VALVE + 8 + i * 6
    for j, pos in enumerate(PATH):
        key(s, "location", f + j * 7, pos)
    show(s, [(f, f + 7 * (len(PATH) - 1))])
for b, f_in, x1, z1 in balls:  # 밸브가 열리면 쌓인 구슬이 내려가 사라진다
    key(b, "location", VALVE + 10, (x1, 0, z1))
    key(b, "location", VALVE + 30, (0, 0, TZ0 - 0.05))
    key(b, "scale", VALVE + 18, (1, 1, 1))
    key(b, "scale", VALVE + 30, (0.3, 0.3, 0.3))
    show(b, [(f_in, VALVE + 30)])

# 결과물: 배출구에서 냄비(검은 몸통 + 빨간 국물 + 손잡이 + 김)가 나와 받침에 놓인다
if "punch" in BEAT:
    a, b = BEAT["punch"]
    pot = empty("pot", OUT)
    cyl("pot_body", 0.2, 0.15, (0, 0, 0.075), m_dark, pot, bevel=0.03)
    cyl("pot_stew", 0.17, 0.012, (0, 0, 0.152), flat("stew", (0.78, 0.14, 0.07), rough=0.35), pot)
    parts = [o for o in bpy.data.objects if o.parent is pot]
    for sx in (-1, 1):
        parts.append(box(f"pot_handle_{sx}", (0.08, 0.04, 0.025), (sx * 0.23, 0, 0.12), m_dark, pot, bevel=0.008))
    steam = flat("steam", (1, 1, 1), rough=0.9, alpha=0.55)
    for i, (x, z, r) in enumerate(((-0.06, 0.26, 0.045), (0.04, 0.34, 0.055), (-0.01, 0.44, 0.04))):
        s = ball(f"steam_{i}", r, (x, 0, z), steam, pot)
        for k in range(0, TOTAL - a, 10):
            key(s, "location", a + 12 + k, (x, 0, z + (0.05 if (k // 10 + i) % 2 else 0)))
        parts.append(s)
    rest = (0, -D / 2 - 0.42, 0.275)
    for f, pos, sc in ((a, OUT, 0.15), (a + 10, rest, 1.1), (a + 14, rest, 1.0)):
        key(pot, "location", f, pos)
        key(pot, "scale", f, (sc, sc, sc))
    show(parts, [(a, TOTAL + 1)])
    if plan.IMPACT is not None:  # 도장: 결과 이름표 위에 크게 찍힌다
        hit = plan.IMPACT + 1
        stamp = picture("stamp", "stamp.png", 0.36, (0.42, -D / 2 - 0.5, 0.72), emission=0.4)
        stamp.rotation_euler = (math.pi / 2, math.radians(-10), 0)
        for f, k in ((hit - 5, 2.6), (hit, 0.9), (hit + 3, 1.08), (hit + 6, 1.0)):
            key(stamp, "scale", f, (0.36 * k, 0.36 * k, 1))
        show(stamp, [(hit - 5, TOTAL + 1)])

# ── 이름표 + 지시선: 그 구간에만 보인다 ─────────────────────────────────
m_line = flat("line", (0.05, 0.05, 0.06), rough=0.6)
TAG_AT = {  # 부품: (이름표 자리, 지시선이 닿는 점)
    "machine": ((0, -D / 2 - 0.03, 1.5), None),
    "tank": ((-0.28, -D / 2 - 0.06, 1.93), (-0.22, -0.1, 1.6)),
    "gauge": ((PX - 0.1, -0.2, 1.08), (PX, -0.06, 1.3)),
    "valve": ((0.4, -0.5, 1.06), (0.1, -0.12, VZ + 0.05)),
    "out": ((0.0, -D / 2 - 0.46, 0.78), (0.0, -D / 2 - 0.42, 0.5)),
}
for bid, (_cam, names) in plan.FLOW.items():
    if bid not in BEAT:
        continue
    a, b = BEAT[bid]
    for n in names:
        pos, tip = TAG_AT[n]
        t = picture(f"tag_{n}", f"tag_{n}.png", 0.17, pos)
        objs = [t]
        if tip:
            objs.append(pipe(f"line_{n}", pos, tip, 0.006, m_line))
        show(objs, [(a + 8, b if bid != plan.ORDER[-1] else TOTAL + 1)])
        w, h = t.scale[0], t.scale[1]
        for f, k in ((a + 8, 0.01), (a + 13, 1.12), (a + 16, 1.0)):  # 통통 튀며 나타난다
            key(t, "scale", f, (w * k, h * k, 1))

# ── 카메라: 세로 화면이라 가로 화각이 좁다(렌즈 50 에서 약 23도). 컷 안에서 천천히 다가간다 ──
CAMS = {  # 이름: (시작 위치, 끝 위치, 바라볼 점, 렌즈)
    "outer": ((2.3, -6.4, 1.0), (1.9, -5.8, 1.1), (0.15, 0, 1.3), 50),  # 낮은 각도의 겉모습
    "front": ((0.3, -5.0, 1.9), (0.15, -4.5, 1.9), (0.0, 0, 1.72), 50),  # 정면 단면(투입구~저장통)
    "gauge": ((0.9, -4.1, 1.75), (0.8, -3.7, 1.75), (0.62, 0, 1.62), 50),  # 눈금자·압력계·시계 창
    "valve": ((-0.9, -3.6, 1.15), (-0.7, -3.2, 1.1), (0.05, -0.2, 0.86), 50),  # 밸브와 관
    "outlet": ((0.9, -4.3, 1.25), (0.7, -3.9, 1.2), (0.05, -0.75, 0.62), 50),  # 배출구와 결과물
    "top": ((2.0, -4.9, 3.9), (1.8, -4.5, 3.6), (0.15, -0.25, 1.15), 50),  # 위에서 본 전체
}
for name, (p0, p1, target, lens) in CAMS.items():
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cam = bpy.data.objects.new("cam_" + name, cd)
    col.objects.link(cam)
    aim(cam, empty(name + "_t", target))
    cam.location = p0
    for a, b, s in plan.SHOTS:
        if s == name:
            key(cam, "location", a + 1, p0)
            key(cam, "location", min(b, TOTAL), p1)

scene.render.fps = plan.FPS
scene.frame_start, scene.frame_end = 1, TOTAL
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
print("SAVED", len(bpy.data.objects))
