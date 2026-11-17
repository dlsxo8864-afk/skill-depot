"""Blender 5.2.3 EEVEE 디오라마 장면 조립 스크립트.

실행:
    blender -b --python-exit-code 1 -P create_scene.py
"""
import math
import os
import random
import sys
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ROOT = os.getcwd()
TEX_DIR = os.path.join(ROOT, "tex")
if not os.path.isdir(TEX_DIR):
    print("먼저 cards.py")
    sys.exit(1)

import plan  # noqa: E402

# ── 공통 블렌더 초기화 ──────────────────────────────────────────────
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection
TOTAL = plan.TOTAL


# ── 재질 및 기본 도형 헬퍼 (bpy_patterns.py 준수) ───────────────────
def flat(name, color, rough=0.4, metal=0.0, emit=0.0, alpha=1.0):
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


def box(name, size, loc, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    if bevel:
        b = o.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = 4
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def cylinder(name, radius, depth, loc, mat, vertices=16, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, vertices=vertices, location=loc)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    if bevel:  # 알약 모양
        b = o.modifiers.new("b", "BEVEL")
        b.width = bevel
        b.segments = 6
        smooth(o)
    return o


def sphere(name, radius, loc, mat, low=False):
    if low:  # 로우폴리(각진) 구
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=radius, location=loc)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    return o if low else smooth(o)


def cone(name, r1, r2, depth, loc, mat, vertices=12):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=depth, vertices=vertices, location=loc)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    return o


def image_plane(name, png, size, loc, rot=(0, 0, 0), emission=0.0, alpha=False):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0], size[1], 1)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(ROOT, "tex", png))
    nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
    if emission:
        nt.links.new(t.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = emission
    if alpha:
        nt.links.new(t.outputs["Alpha"], p.inputs["Alpha"])
        m.surface_render_method = "BLENDED"
    o.data.materials.append(m)
    return o


def key_visible(o, ranges):
    """ranges: 보이는 블렌더 프레임 구간 목록 [(a, b), …]"""
    prev = None
    for f in range(1, TOTAL + 2):
        vis = any(a <= f <= b for a, b in ranges)
        if vis != prev:
            o.hide_render = not vis
            o.hide_viewport = not vis
            o.keyframe_insert("hide_render", frame=f)
            o.keyframe_insert("hide_viewport", frame=f)
        prev = vis


def pop_in(o, frame, scale=1.0):
    base_scale = tuple(o.scale)
    for f, mult in ((frame, 0.001), (frame + 5, 1.15), (frame + 8, 1.0)):
        o.scale = (base_scale[0] * mult, base_scale[1] * mult, base_scale[2] * mult)
        o.keyframe_insert("scale", frame=f)


def camera(name, loc, target, lens=65):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cam = bpy.data.objects.new("cam_" + name, cd)
    col.objects.link(cam)
    cam.location = loc
    t = bpy.data.objects.new(name + "_t", None)
    col.objects.link(t)
    t.location = target
    c = cam.constraints.new("TRACK_TO")
    c.target = t
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return cam, t


# ── 1. 공중에 뜬 둥근 사각 섬(받침) ─────────────────────────────────
mat_grass = flat("m_grass", (0.30, 0.56, 0.24), rough=0.8)
mat_dirt = flat("m_dirt", (0.42, 0.28, 0.18), rough=0.85)
mat_rock = flat("m_rock", (0.32, 0.32, 0.35), rough=0.9)

# 상단 잔디 층
island_top = box("island_top", (6.8, 6.8, 0.5), (0, 0, -0.25), mat_grass, bevel=0.12)
# 중단 흙 층
island_mid = box("island_mid", (6.2, 6.2, 1.0), (0, 0, -1.0), mat_dirt, bevel=0.1)
# 하단 암반 층
island_bot = box("island_bot", (5.0, 5.0, 0.8), (0, 0, -1.9), mat_rock, bevel=0.08)


# ── 2. 둘레 소품(나무, 바위, 울타리) ─────────────────────────────────
random.seed(42)
mat_wood = flat("m_wood", (0.45, 0.30, 0.18), rough=0.8)
mat_leaf1 = flat("m_leaf1", (0.22, 0.52, 0.24), rough=0.6)
mat_leaf2 = flat("m_leaf2", (0.30, 0.60, 0.20), rough=0.6)
mat_leaf3 = flat("m_leaf3", (0.16, 0.44, 0.28), rough=0.6)
leaf_mats = [mat_leaf1, mat_leaf2, mat_leaf3]

# 둘레 나무 10그루
for i in range(10):
    ang = (i / 10.0) * math.tau + random.uniform(-0.15, 0.15)
    dist = random.uniform(2.3, 2.9)
    tx, ty = math.cos(ang) * dist, math.sin(ang) * dist
    # 앞쪽 자막/인물 공간(ty < -1.0 및 |tx| < 1.4)은 피한다
    if ty < -0.8 and abs(tx) < 1.6:
        continue
    trunk = cylinder(f"tree_t_{i}", 0.08, 0.8, (tx, ty, 0.4), mat_wood, vertices=8)
    lmat = leaf_mats[i % len(leaf_mats)]
    if i % 2 == 0:
        cone(f"tree_f_{i}", 0.5, 0.0, 1.1, (tx, ty, 1.1), lmat, vertices=8)
    else:
        sphere(f"tree_f_{i}", 0.5, (tx, ty, 1.0), lmat, low=True)

# 둘레 바위 및 작은 울타리
for i in range(5):
    rx = random.uniform(-2.6, 2.6)
    ry = random.uniform(1.2, 2.7)
    box(f"rock_{i}", (0.35, 0.35, 0.25), (rx, ry, 0.12), mat_rock, bevel=0.05)

# 뒤쪽 작은 울타리 기둥
for idx, px in enumerate((-1.8, -0.9, 0.0, 0.9, 1.8)):
    cylinder(f"fence_{idx}", 0.05, 0.5, (px, 2.8, 0.25), mat_wood, vertices=8)
box("fence_bar", (3.8, 0.04, 0.06), (0.0, 2.8, 0.35), mat_wood)


# ── 3. 인형 인물 3명 ────────────────────────────────────────────────
mat_skin = flat("m_skin", (0.95, 0.82, 0.72), rough=0.5)
mat_eye = flat("m_eye", (0.08, 0.08, 0.08), rough=0.2)

cast_styles = [
    {"mat": flat("m_c0", (0.22, 0.38, 0.65), rough=0.6), "scale": 1.0, "x": -1.0, "y": -1.4},
    {"mat": flat("m_c1", (0.85, 0.65, 0.18), rough=0.6), "scale": 1.0, "x": -0.2, "y": -1.5},
    {"mat": flat("m_c2", (0.85, 0.22, 0.24), rough=0.6), "scale": 1.18, "x": 0.9, "y": -1.3},
]

FIGS = {}
for idx, c in enumerate(plan.CAST):
    cid = c["id"]
    style = cast_styles[idx % len(cast_styles)]
    s = style["scale"]
    loc = (style["x"], style["y"], 0.0)

    # 인물 기준 빈 오브젝트
    root = bpy.data.objects.new(f"fig_{cid}", None)
    col.objects.link(root)
    root.location = loc

    # 알약 몸통
    body = cylinder(f"body_{cid}", 0.18 * s, 0.46 * s, (0, 0, 0.25 * s), style["mat"], vertices=32, bevel=0.07 * s)
    body.parent = root

    # 구 머리
    head = sphere(f"head_{cid}", 0.20 * s, (0, 0, 0.62 * s), mat_skin)
    head.parent = root

    # 점 눈 2개
    eye_l = sphere(f"eye_l_{cid}", 0.03 * s, (-0.06 * s, -0.18 * s, 0.64 * s), mat_eye)
    eye_r = sphere(f"eye_r_{cid}", 0.03 * s, (0.06 * s, -0.18 * s, 0.64 * s), mat_eye)
    eye_l.parent = root
    eye_r.parent = root

    FIGS[cid] = {"root": root, "head": head, "body": body, "base_loc": loc}

# 인물 동작 키프레임 애니메이션
def anim_hop(root, frame, base_z=0.0):
    for offset, dz in ((0, 0.0), (3, 0.32), (6, 0.0)):
        root.location.z = base_z + dz
        root.keyframe_insert("location", frame=frame + offset)


def anim_cheer(root, frame, base_z=0.0):
    for offset, dz in ((0, 0.0), (3, 0.35), (6, 0.0), (9, 0.35), (12, 0.0)):
        root.location.z = base_z + dz
        root.keyframe_insert("location", frame=frame + offset)


def anim_slump(body, f_start, f_end):
    body.rotation_euler.x = 0.0
    body.keyframe_insert("rotation_euler", frame=f_start)
    body.rotation_euler.x = math.radians(-24)
    body.keyframe_insert("rotation_euler", frame=f_start + 10)
    body.keyframe_insert("rotation_euler", frame=f_end - 4)
    body.rotation_euler.x = 0.0
    body.keyframe_insert("rotation_euler", frame=f_end)


cues = plan.get_cast_action_cues()
for f, who in cues["hop"]:
    if who in FIGS:
        anim_hop(FIGS[who]["root"], f + 1, FIGS[who]["base_loc"][2])

for f_start, f_end in cues["slump"]:
    for info in FIGS.values():
        anim_slump(info["body"], f_start + 1, f_end + 1)

for f_start, f_end, who in cues["walk_to"]:
    if who in FIGS:
        r = FIGS[who]["root"]
        r.location = FIGS[who]["base_loc"]
        r.keyframe_insert("location", frame=f_start + 1)
        r.location = (0.55, -0.75, 0.0)  # 간판 앞으로
        r.keyframe_insert("location", frame=f_start + 19)
        FIGS[who]["base_loc"] = (0.55, -0.75, 0.0)
        anim_hop(r, f_start + 22)

for f, who in cues["cheer"]:
    if who in FIGS:
        r = FIGS[who]["root"]
        r.location = FIGS[who]["base_loc"]
        anim_cheer(r, f + 4, 0.0)
        anim_cheer(r, plan.STAMP_FRAME + 4, 0.0)


# ── 4. 가운데 구조물 및 단계별 부품 ──────────────────────────────────
MAT_SIGN_FRAME = flat("m_sign_frame", (0.40, 0.26, 0.15), rough=0.8)
MAT_TOWER = flat("m_tower", (0.80, 0.75, 0.68), rough=0.5)
MAT_ROOF = flat("m_roof", (0.85, 0.25, 0.20), rough=0.6)
MAT_GAUGE = flat("m_gauge", (0.95, 0.35, 0.10), emit=0.35)
MAT_POT = flat("m_pot", (0.15, 0.15, 0.18), metal=0.8, rough=0.3)
MAT_STEAM = flat("m_steam", (0.95, 0.95, 0.95), rough=0.9, alpha=0.75)


def make_sign(stage_info):
    """hook: 빈 메뉴 간판 (기둥 2개 + 물음표 판)"""
    root = bpy.data.objects.new("part_sign", None)
    col.objects.link(root)
    p1 = cylinder("sign_post1", 0.05, 1.4, (-0.75, 0.0, 0.7), MAT_SIGN_FRAME, vertices=8)
    p2 = cylinder("sign_post2", 0.05, 1.4, (0.75, 0.0, 0.7), MAT_SIGN_FRAME, vertices=8)
    board = image_plane("sign_board", stage_info["tex"], (1.5, 1.0), (0.0, -0.02, 1.15), rot=(math.pi / 2, 0, 0))
    p1.parent = root
    p2.parent = root
    board.parent = root
    # punch 구간 전까지 보이다가 식당으로 바뀐다
    key_visible(p1, [(1, plan.F_PUNCH)])
    key_visible(p2, [(1, plan.F_PUNCH)])
    key_visible(board, [(1, plan.F_PUNCH)])
    pop_in(root, stage_info["frame"] + 1)
    return root


def make_note(stage_info):
    """ask: 간판에 붙는 쪽지"""
    idx = stage_info["idx"]
    ox = -0.42 + (idx * 0.42)
    oy = -0.06 - (idx * 0.01)
    oz = 1.15 + ((idx % 2) * 0.15)
    plane = image_plane(f"note_plane_{idx}", stage_info["tex"], (0.42, 0.24), (ox, oy, oz), rot=(math.pi / 2, 0, 0), alpha=True)
    key_visible(plane, [(stage_info["frame"] + 1, plan.F_PUNCH)])
    pop_in(plane, stage_info["frame"] + 1)
    return plane


def make_tower(stage_info):
    """wait: 간판 옆 시계탑"""
    root = bpy.data.objects.new("part_tower", None)
    col.objects.link(root)
    tx, ty = 1.35, 0.15
    base = box("tower_base", (0.6, 0.6, 1.6), (tx, ty, 0.8), MAT_TOWER, bevel=0.03)
    roof = cone("tower_roof", 0.45, 0.0, 0.7, (tx, ty, 1.95), MAT_ROOF, vertices=4)
    dial = image_plane("tower_dial", "clock_face.png", (0.5, 0.5), (tx, ty - 0.31, 1.3), rot=(math.pi / 2, 0, 0), alpha=True)
    f_start = stage_info["frame"] + 1
    f_end = plan.F_DECIDE + 1

    def hm(text):
        h, m = text.split(":")
        return int(h) % 12 + int(m) / 60.0, int(m) / 60.0  # (시침 12시간 기준, 분침 바퀴)

    (h0, m0), (h1, m1) = hm(plan.CLOCK_INFO["from"]), hm(plan.CLOCK_INFO["to"])
    if h1 < h0:
        h1 += 12
    if m1 < m0:
        m1 += 1.0
    hands = []
    for name, length, width, a0, a1 in (("min", 0.20, 0.022, m0, m1), ("hour", 0.13, 0.034, h0 / 12.0, h1 / 12.0)):
        pivot = bpy.data.objects.new("tower_" + name, None)
        col.objects.link(pivot)
        pivot.location = (tx, ty - 0.33, 1.3)
        hand = box("tower_hand_" + name, (width, 0.012, length), (0, 0, length / 2), mat_eye)
        hand.parent = pivot
        pivot.rotation_euler.y = a0 * math.tau  # 앞(-Y)에서 볼 때 +Y 회전이 시계 방향
        pivot.keyframe_insert("rotation_euler", frame=f_start)
        pivot.rotation_euler.y = a1 * math.tau
        pivot.keyframe_insert("rotation_euler", frame=f_end)
        hands.append(pivot)

    base.parent = root
    roof.parent = root
    dial.parent = root
    for hnd in hands:
        hnd.parent = root
    pop_in(root, f_start)
    return root


def make_gauge(stage_info):
    """wait: 배고픔 게이지 기둥"""
    gx, gy = -1.35, 0.15
    frame_box = box("gauge_frame", (0.34, 0.05, 1.5), (gx, gy + 0.12, 0.75), MAT_SIGN_FRAME, bevel=0.02)
    pillar = cylinder("gauge_pillar", 0.10, 1.2, (gx, gy, 0.7), MAT_GAUGE, vertices=24)
    f_start = stage_info["frame"] + 1
    f_end = plan.F_DECIDE + 1
    for f, g in ((f_start, plan.GAUGE_INFO.get("from", 0.2)), (f_end, plan.GAUGE_INFO.get("to", 1.0))):
        pillar.scale = (1.0, 1.0, g)  # 바닥(z=0.1)에 붙은 채 위로 자란다
        pillar.location.z = 0.1 + 0.6 * g
        pillar.keyframe_insert("scale", frame=f)
        pillar.keyframe_insert("location", frame=f)
    key_visible(pillar, [(f_start, TOTAL + 1)])
    pop_in(frame_box, f_start)
    return frame_box


def make_flag(stage_info):
    """decide: 간판 위 꽂히는 깃발"""
    pole = cylinder("flag_pole", 0.03, 0.6, (0.0, 0.0, 1.95), MAT_SIGN_FRAME, vertices=8)
    cloth = image_plane("flag_cloth", stage_info["tex"], (0.8, 0.4), (0.42, 0.0, 0.15), rot=(math.pi / 2, 0, 0), alpha=True)
    cloth.parent = pole
    f_start = stage_info["frame"] + 1
    key_visible(pole, [(f_start, plan.F_PUNCH)])
    key_visible(cloth, [(f_start, plan.F_PUNCH)])
    pop_in(pole, f_start)
    return pole


def make_shop(stage_info):
    """punch: 간판이 큰 식당으로 변신"""
    root = bpy.data.objects.new("part_shop", None)
    col.objects.link(root)
    # 가게 본체 매대
    counter = box("shop_counter", (2.2, 1.4, 0.85), (0.0, 0.2, 0.42), MAT_SIGN_FRAME, bevel=0.04)
    # 차양 지붕
    roof = box("shop_roof", (2.5, 1.7, 0.14), (0.0, 0.2, 1.78), MAT_ROOF, bevel=0.04)
    post1 = cylinder("shop_post1", 0.05, 0.9, (-1.0, -0.4, 1.3), MAT_SIGN_FRAME, vertices=8)
    post2 = cylinder("shop_post2", 0.05, 0.9, (1.0, -0.4, 1.3), MAT_SIGN_FRAME, vertices=8)
    # 식당 간판 (result): 지붕 앞쪽 위에 세운다
    sign = image_plane("shop_sign", stage_info["tex"], (1.9, 0.9), (0.0, -0.55, 2.32), rot=(math.pi / 2, 0, 0))
    # 김 나는 큰 냄비
    pot = cylinder("shop_pot", 0.36, 0.34, (0.0, -0.3, 1.03), MAT_POT, vertices=32, bevel=0.05)
    stew = cylinder("shop_stew", 0.31, 0.02, (0.0, -0.3, 1.21), flat("m_stew", (0.80, 0.16, 0.08), rough=0.4), vertices=32)
    steam1 = sphere("shop_steam1", 0.10, (-0.10, -0.3, 1.40), MAT_STEAM)
    steam2 = sphere("shop_steam2", 0.13, (0.08, -0.3, 1.55), MAT_STEAM)
    for i, st in enumerate((steam1, steam2)):  # 김이 오르내린다
        z0 = st.location.z
        for k in range(0, 80, 12):
            st.location.z = z0 + (0.10 if (k // 12 + i) % 2 else 0.0)
            st.keyframe_insert("location", frame=stage_info["frame"] + 1 + k)
    for extra in (post1, post2, stew):
        extra.parent = root

    counter.parent = root
    roof.parent = root
    sign.parent = root
    pot.parent = root
    steam1.parent = root
    steam2.parent = root

    f_start = stage_info["frame"] + 1
    key_visible(root, [(f_start, TOTAL + 1)])
    pop_in(root, f_start)
    return root


def make_stamp(stage_info):
    """punch: 하늘에서 떨어지는 도장 판"""
    f_hit = stage_info["frame"] + 1
    plane = image_plane("stamp_plane", stage_info["tex"], (0.8, 0.8), (0.98, -0.62, 1.98), rot=(math.pi / 2, math.radians(-10), 0), alpha=True)
    for f, k in ((f_hit - 5, 2.6), (f_hit, 0.92), (f_hit + 3, 1.06), (f_hit + 6, 1.0)):
        plane.scale = (0.8 * k, 0.8 * k, 1)
        plane.keyframe_insert("scale", frame=max(1, f))
    key_visible(plane, [(max(1, f_hit - 5), TOTAL + 1)])
    return plane


PARTS = {
    "sign": make_sign,
    "note": make_note,
    "tower": make_tower,
    "gauge": make_gauge,
    "flag": make_flag,
    "shop": make_shop,
    "stamp": make_stamp,
}

# plan.STAGES 순회하며 부품 생성
for stage_name, stage_data in plan.STAGES.items():
    for part_info in stage_data["parts"]:
        ptype = part_info["type"]
        if ptype in PARTS:
            PARTS[ptype](part_info)


# ── 5. 카메라 3대 (wide, close, punch) ───────────────────────────────
cam_wide, tw = camera("wide", (-2.6, -16.6, 12.6), (0.0, -0.2, -0.3), lens=72)  # 섬 가운데. 천천히 돈다
cam_wide.keyframe_insert("location", frame=1)
cam_wide.location = (2.6, -16.6, 12.6)
cam_wide.keyframe_insert("location", frame=plan.F_WAIT + 1)

cam_close, tc = camera("close", (4.2, -10.4, 6.6), (0.0, 0.0, 1.0), lens=70)  # 구조물 가까이
cam_close.keyframe_insert("location", frame=plan.F_WAIT + 1)
cam_close.location = (3.2, -10.9, 6.4)
cam_close.keyframe_insert("location", frame=plan.F_PUNCH + 1)

cam_punch, tp = camera("punch", (-3.4, -12.4, 8.0), (0.0, -0.1, 1.2), lens=62)  # 마지막 전경
cam_punch.keyframe_insert("location", frame=plan.F_PUNCH + 1)
cam_punch.location = (-2.2, -11.6, 7.4)
cam_punch.keyframe_insert("location", frame=TOTAL)


# ── 6. 햇빛 및 날씨 변화 ───────────────────────────────────────────
sd = bpy.data.lights.new("sun", "SUN")
sd.energy = 4.2
sd.angle = math.radians(4)
sd.color = (1.0, 0.95, 0.88)
sun = bpy.data.objects.new("sun", sd)
col.objects.link(sun)
sun.rotation_euler = Vector((0.5, 0.4, -0.7)).normalized().to_track_quat("-Z", "Y").to_euler()

# wait 구간에서 해가 돌아 그림자가 길어지고 주황빛으로 변화
sd.keyframe_insert("energy", frame=1)
sd.keyframe_insert("color", frame=1)
sun.keyframe_insert("rotation_euler", frame=1)

f_w_start = plan.F_WAIT + 1
f_w_end = plan.F_DECIDE + 1
sd.keyframe_insert("energy", frame=f_w_start)
sd.keyframe_insert("color", frame=f_w_start)
sun.keyframe_insert("rotation_euler", frame=f_w_start)

# 해 회전 및 일몰 주황빛
sun.rotation_euler = Vector((0.85, 0.15, -0.3)).normalized().to_track_quat("-Z", "Y").to_euler()
sd.color = (1.0, 0.62, 0.32)
sd.energy = 3.6
sun.keyframe_insert("rotation_euler", frame=f_w_end)
sd.keyframe_insert("color", frame=f_w_end)
sd.keyframe_insert("energy", frame=f_w_end)

# punch 구간에서 다시 밝고 따뜻한 축하 조명으로 복귀
f_punch = plan.F_PUNCH + 1
sun.rotation_euler = Vector((0.45, 0.45, -0.75)).normalized().to_track_quat("-Z", "Y").to_euler()
sd.color = (1.0, 0.96, 0.90)
sd.energy = 4.4
sun.keyframe_insert("rotation_euler", frame=f_punch)
sd.keyframe_insert("color", frame=f_punch)
sd.keyframe_insert("energy", frame=f_punch)

# 월드 하늘색 배경
world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.42, 0.68, 0.95, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.4


# ── 7. 장면 설정 및 저장 ───────────────────────────────────────────
scene.render.fps = plan.FPS
scene.frame_start, scene.frame_end = 1, TOTAL
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
try:
    scene.view_settings.look = "Medium High Contrast"
except TypeError:
    pass

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
print("SAVED", len(bpy.data.objects))
