"""마스코트 설명 영상 장면을 조립해 scene.blend 로 저장한다. 작업 폴더에서 실행.

사용: blender -b --python-exit-code 1 -P create_scene.py
- 먼저 cards.py 를 돌려 작업 폴더에 tex/ 가 있어야 한다.
- 어두운 무대, 직접 만든 마스코트, 그 위에 뜨는 화면 카드. 구간마다 표정·동작·카드가 바뀐다.
- 무엇을 언제 보여 줄지는 plan.py(대본 풀이)에서 읽는다. 이 파일에는 생김새와 움직이는 방법만 있다.
블렌더 프레임은 1부터라서 plan 의 프레임(0부터)에 1을 더한다.
"""
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan  # noqa: E402

ROOT = os.getcwd()
if not os.path.isfile(os.path.join(ROOT, "tex", "result.png")):
    raise SystemExit("작업 폴더에 tex/ 가 없습니다. 먼저 cards.py 를 돌리세요: " + ROOT)
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection
TOTAL = plan.TOTAL
BEAT = {k: (a + 1, b) for k, (a, b) in plan.BEAT.items()}  # 구간의 블렌더 프레임 (첫, 끝)
ORDER = [b["id"] for b in plan.S["beats"]]


def F(sec):
    return plan.fr(sec) + 1


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
        b.segments = 8
    if parent is not None:
        o.parent = parent
    return o


def box(name, size, loc, mat, parent=None, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)  # 크기만 굳힌다(자리는 그대로)
    return finish(o, name, mat, parent, bevel)


def cyl(name, radius, depth, loc, mat, parent=None, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, vertices=48, location=loc, rotation=rot)
    return finish(bpy.context.object, name, mat, parent, bevel)


def ball(name, radius, loc, mat, parent=None, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc)
    o = bpy.context.object
    o.scale = scale
    return finish(o, name, mat, parent)


def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    col.objects.link(e)
    e.location = loc
    if parent is not None:
        e.parent = parent
    return e


def card(name, png, width, loc, emission=0.85, alpha=True):
    """그림 한 장을 세운 판. 높이는 그림 비율대로. 앞(-Y)을 본다."""
    img = bpy.data.images.load(os.path.join(ROOT, "tex", png))
    h = width * img.size[1] / img.size[0]
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=(math.pi / 2, 0, 0))
    o = bpy.context.object
    o.name = name
    o.scale = (width, h, 1)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(t.outputs["Color"], p.inputs["Emission Color"])
    p.inputs["Emission Strength"].default_value = emission
    p.inputs["Roughness"].default_value = 0.6
    if alpha:
        nt.links.new(t.outputs["Alpha"], p.inputs["Alpha"])
        m.surface_render_method = "BLENDED"
    o.data.materials.append(m)
    return o


def show(objs, ranges):
    """objs 를 ranges(블렌더 프레임 구간 목록) 동안만 보이게 한다."""
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


def pop(o, frame, out=None):
    """frame 에 통통 튀며 나타나고, out 이 있으면 그때 줄어들며 사라진다."""
    sx, sy, sz = o.scale
    for f, k in ((frame, 0.01), (frame + 5, 1.14), (frame + 8, 0.97), (frame + 10, 1.0)):
        key(o, "scale", f, (sx * k, sy * k, sz * k))
    if out:
        key(o, "scale", out - 5, (sx, sy, sz))
        key(o, "scale", out, (sx * 0.01, sy * 0.01, sz * 0.01))
    show(o, [(frame, out or TOTAL + 1)])


def aim(o, target):
    c = o.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"


# ── 무대 ────────────────────────────────────────────────────────────
NAVY = plan.BG_NAVY
box("floor", (40, 40, 0.1), (0, 6, -0.05), flat("floor", (0.03, 0.04, 0.08), rough=0.25))
box("wall", (40, 0.2, 20), (0, 9, 9), flat("wall", (0.025, 0.035, 0.075), rough=0.9))
cyl("podium", 1.25, 0.12, (0, 0, 0.06), flat("podium", (0.06, 0.07, 0.12), rough=0.3))
cyl("podium_ring", 1.3, 0.03, (0, 0, 0.015), flat("ring", plan.ACCENT, emit=2.5))
beam = flat("beam", (1.0, 0.97, 0.9), emit=0.35, alpha=0.02)
for i, x in enumerate((-1.9, 1.9)):  # 빛줄기처럼 보이는 반투명 원뿔
    bpy.ops.mesh.primitive_cone_add(radius1=1.7, radius2=0.08, depth=7.5, vertices=48, location=(x * 0.6, 0.9, 3.75), rotation=(0, math.radians(-12 if x < 0 else 12), 0))
    finish(bpy.context.object, f"beam_{i}", beam)
world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (*NAVY, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6

lookat = empty("light_target", (0, 0, 0.9))


def light(name, kind, loc, energy, color, size=None):
    d = bpy.data.lights.new(name, kind)
    d.energy = energy
    d.color = color
    if kind == "SPOT":
        d.spot_size = math.radians(size or 45)
        d.spot_blend = 0.6
    if kind == "AREA":
        d.size = size or 3
    o = bpy.data.objects.new(name, d)
    col.objects.link(o)
    o.location = loc
    aim(o, lookat)
    return d


WARM = (1.0, 0.93, 0.82)
key_l = light("key", "SPOT", (2.6, -4.5, 6.0), 2600, WARM, 40)
light("fill", "AREA", (-3.5, -4.0, 2.2), 260, (0.75, 0.85, 1.0), 4)
rim = light("rim", "SPOT", (0.0, 4.0, 4.5), 3800, plan.ACCENT, 50)
if "decide" in BEAT:  # 결정 구간에는 조명이 강조색으로 바뀐다
    a, b = BEAT["decide"]
    for f, c in ((a - 1, WARM), (a + 6, tuple(0.45 + 0.55 * v for v in plan.ACCENT)), (b - 4, tuple(0.45 + 0.55 * v for v in plan.ACCENT)), (b + 4, WARM)):
        key(key_l, "color", max(1, f), c)

# ── 마스코트(직접 디자인: 크림색 둥근 머리, 얼굴 화면, 강조색 몸, 떠 있는 손) ──
M = empty("mascot")  # 뛰기·움찔 같은 큰 움직임
B = empty("bob", parent=M)  # 숨쉬기
m_body = flat("m_body", plan.ACCENT, rough=0.35)
m_cream = flat("m_cream", plan.CREAM, rough=0.4)
m_dark = flat("m_dark", (0.02, 0.025, 0.04), rough=0.15)
m_eye = flat("m_eye", (0.75, 1.0, 0.95), emit=4.0)
m_foot = flat("m_foot", tuple(v * 0.55 for v in plan.ACCENT), rough=0.4)
cyl("body", 0.33, 0.52, (0, 0, 0.47), m_body, B, bevel=0.14)
HEAD = empty("head", (0, 0, 0.78), B)  # 고개 축(목)
box("head_box", (1.0, 0.72, 0.74), (0, 0, 0.42), m_cream, HEAD, bevel=0.2)
box("face", (0.76, 0.05, 0.48), (0, -0.355, 0.42), m_dark, HEAD, bevel=0.022)
for sx in (-1, 1):
    cyl(f"ear_{sx}", 0.13, 0.1, (sx * 0.53, 0, 0.42), m_body, HEAD, bevel=0.03, rot=(0, math.pi / 2, 0))
    ball(f"foot_{sx}", 0.14, (sx * 0.17, -0.03, 0.11), m_foot, M, scale=(1, 1.25, 0.7))
HAND = {sx: ball(f"hand_{sx}", 0.115, (sx * 0.52, -0.08, 0.5), m_cream, B) for sx in (-1, 1)}
REST = {sx: (sx * 0.52, -0.08, 0.5) for sx in (-1, 1)}

# 표정: 표정마다 눈·입 도형을 따로 만들어 구간에 맞춰 보이게 한다
EY, EZ, EX = -0.386, 0.46, 0.17  # 얼굴 화면 위 눈 자리
FACES = {"normal": [], "happy": [], "surprised": [], "sleepy": []}
for sx in (-1, 1):
    FACES["normal"].append(box(f"n_eye{sx}", (0.075, 0.012, 0.17), (sx * EX, EY, EZ), m_eye, HEAD, bevel=0.03))
    for k in (-1, 1):  # 웃는 눈: ∧ 모양
        FACES["happy"].append(box(f"h_eye{sx}{k}", (0.105, 0.012, 0.04), (sx * EX + k * 0.036, EY, EZ + 0.01), m_eye, HEAD, bevel=0.015, rot=(0, math.radians(k * 38), 0)))
    FACES["surprised"].append(cyl(f"s_eye{sx}", 0.085, 0.012, (sx * EX, EY, EZ), m_eye, HEAD, rot=(math.pi / 2, 0, 0)))
    FACES["sleepy"].append(box(f"z_eye{sx}", (0.15, 0.012, 0.032), (sx * EX, EY, EZ - 0.02), m_eye, HEAD, bevel=0.012))
for k in (-1, 1):  # 웃는 입: ∨ 모양
    FACES["happy"].append(box(f"h_mouth{k}", (0.085, 0.012, 0.03), (k * 0.032, EY, 0.3), m_eye, HEAD, bevel=0.012, rot=(0, math.radians(k * -28), 0)))
for name in ("normal", "sleepy"):
    FACES[name].append(box(f"{name}_mouth", (0.09, 0.012, 0.028), (0, EY, 0.3), m_eye, HEAD, bevel=0.01))
FACES["surprised"].append(cyl("s_mouth", 0.04, 0.012, (0, EY, 0.29), m_eye, HEAD, rot=(math.pi / 2, 0, 0)))
for name, objs in FACES.items():
    show(objs, [BEAT[b] for b in ORDER if plan.MASCOT_BEAT.get(b, {}).get("expr", "normal") == name])

# 숨쉬기: 내내 위아래로 조금씩
for f in range(1, TOTAL + 1, 6):
    key(B, "location", f, (0, 0, 0.035 * math.sin(f / 24 * 2 * math.pi * 0.55)))


def hands_to(frame, left=None, right=None, hold=None):
    """손을 frame 까지 옮긴다. left/right 는 (x, y, z) 또는 None(쉬는 자리). hold 까지 그 자리에 둔다."""
    for sx, pos in ((-1, left), (1, right)):
        h = HAND[sx]
        key(h, "location", frame - 6, tuple(h.location))
        key(h, "location", frame, pos or REST[sx])
        if hold:
            key(h, "location", hold, pos or REST[sx])


def act(name, a, b, at=None):
    """구간 [a, b] 에 동작을 넣는다. at 은 그 구간의 주요 순간(프레임)."""
    at = at or a + 12
    if name == "wave":  # 한 손을 들어 흔든다
        hands_to(a + 8, right=(0.66, -0.1, 1.2))
        for i, f in enumerate(range(a + 8, b - 8, 5)):
            key(HAND[1], "location", f, (0.66 + (0.1 if i % 2 else -0.06), -0.1, 1.2))
    elif name == "point_up":  # 한 손으로 위의 카드를 가리킨다
        hands_to(a + 8, right=(0.5, 0.05, 1.72), hold=b - 8)
        for f, r in ((a, 0), (a + 8, -10), (b - 8, -10)):
            key(HEAD, "rotation_euler", f, (math.radians(r), 0, 0))
    elif name == "shrug":  # 두 손을 올리고 고개를 기울인다
        hands_to(a + 10, left=(-0.7, -0.05, 0.92), right=(0.7, -0.05, 0.92), hold=b - 8)
        for f, r in ((a, 0), (a + 10, 9), (b - 8, 9)):
            key(HEAD, "rotation_euler", f, (0, math.radians(r), 0))
    elif name == "nod":  # 깜짝 놀라 움찔한 뒤 끄덕인다
        for f, z in ((at - 1, 0), (at + 3, 0.16), (at + 7, 0)):
            key(M, "location", f, (0, 0, z))
        for i, f in enumerate(range(at + 14, b - 6, 7)):
            key(HEAD, "rotation_euler", f, (math.radians(14 if i % 2 == 0 else 0), 0, 0))
    elif name == "jump":  # 두 손을 들고 뛴다
        hands_to(a + 8, left=(-0.66, -0.05, 1.3), right=(0.66, -0.05, 1.3), hold=b)
        for j in (at, at + 16):
            for f, z in ((j - 1, 0), (j + 4, 0.42), (j + 9, 0)):
                key(M, "location", f, (0, 0, z))
    if name != "jump":  # 구간 끝에는 손과 고개를 되돌린다
        hands_to(b)
        key(HEAD, "rotation_euler", b, (0, 0, 0))


MOMENT = {"decide": F(plan.DECIDE_CHAT[0]["t"]) if plan.DECIDE_CHAT else None, "punch": plan.IMPACT + 1 if plan.IMPACT is not None else None}
for bid in ORDER:
    if bid in plan.MASCOT_BEAT:
        act(plan.MASCOT_BEAT[bid]["action"], *BEAT[bid], at=MOMENT.get(bid))

# ── 카드: 마스코트 머리 위 공간(z 1.75~3.9)에 뜬다 ─────────────────────
CY = 0.45  # 카드가 서는 깊이(마스코트보다 조금 뒤)
if "hook" in BEAT:
    a, b = BEAT["hook"]
    pop(card("chip_hook", "chip_hook.png", 1.25, (-0.72, CY, 3.0)), a + 8, b)
    if plan.HOOK_CHAT:
        pop(card("msg", "msg.png", 2.5, (0.2, CY, 2.25)), F(plan.HOOK_CHAT[0]["t"]), b)
if "ask" in BEAT:
    a, b = BEAT["ask"]
    times = [a] + [F(c["t"]) for c in plan.ASK_CHAT] + [b + 1]
    for n in range(len(plan.ASK_CHAT) + 1):  # 대화가 늘 때마다 다음 그림으로 바꾼다
        c = card(f"chat_{n}", f"chat_{n}.png", 2.5, (0, CY + 0.002 * n, 2.75))
        if n == 0:
            pop(c, a, times[1])
        else:
            show(c, [(times[n], times[n + 1] - 1)])
    if plan.ASK_CHAT:
        pop(card("chip_ask", "chip_ask.png", 1.2, (0.72, CY - 0.06, 3.86)), F(plan.ASK_CHAT[-1]["t"]) + 6, b)
if "wait" in BEAT:
    a, b = BEAT["wait"]
    dial = card("dial", "dial.png", 1.55, (-0.42, CY, 3.02))
    pop(dial, a, b)
    (h0, m0), (h1, m1) = plan.CLOCK_FROM, plan.CLOCK_TO
    t0, t1 = h0 % 12 + m0 / 60, h1 % 12 + m1 / 60
    if t1 < t0:
        t1 += 12
    for name, length, width, r0, r1 in (("min", 0.6, 0.045, t0, t1), ("hour", 0.4, 0.07, t0 / 12, t1 / 12)):
        pivot = empty("hand_" + name, (-0.42, CY - 0.03, 3.02))
        hand = box("clock_" + name, (width, 0.02, length), (0, 0, length / 2 - 0.04), m_dark, pivot, bevel=0.012)
        key(pivot, "rotation_euler", a + 6, (0, r0 * math.tau, 0))  # 앞에서 볼 때 +Y 회전이 시계 방향
        key(pivot, "rotation_euler", b - 6, (0, r1 * math.tau, 0))
        show(hand, [(a + 4, b - 3)])
    gauge = card("gauge", "gauge.png", 2.3, (0, CY, 1.93))
    pop(gauge, a + 6, b)
    gw = 2.3 * 588 / 660  # 카드 안 막대 길이
    bar = box("gauge_bar", (1, 0.02, 0.15), (0, CY - 0.03, 1.855), flat("bar", (0.9, 0.16, 0.2), emit=0.25), bevel=0.01)
    for f, g in ((a + 10, plan.GAUGE_SPEC.get("from", 0.2)), (b - 6, plan.GAUGE_SPEC.get("to", 1.0))):
        key(bar, "scale", f, (gw * g, 1, 1))  # 왼쪽 끝을 붙인 채 오른쪽으로 길어진다
        key(bar, "location", f, (-gw / 2 + gw * g / 2, CY - 0.03, 1.855))
    show(bar, [(a + 10, b - 3)])
    pop(card("chip_wait", "chip_wait.png", 1.2, (0.9, CY - 0.06, 3.7)), b - 30, b)
if "decide" in BEAT and plan.DECIDE_CHAT:
    a, b = BEAT["decide"]
    t = F(plan.DECIDE_CHAT[0]["t"])
    alert = card("alert", "alert.png", 1.32, (0, -0.2, 2.2))
    for f, z in ((t, 3.3), (t + 6, 2.12), (t + 9, 2.24), (t + 12, 2.2)):  # 위에서 떨어진다
        key(alert, "location", f, (0, -0.2, z))
    show(alert, [(t, b)])
if "punch" in BEAT:
    a, b = BEAT["punch"]
    pop(card("result", "result.png", 2.55, (0, CY, 2.72)), a + 2)
    if plan.IMPACT is not None:
        hit = plan.IMPACT + 1
        stamp = card("stamp", "stamp.png", 1.05, (0.82, CY - 0.05, 2.2), emission=0.6)
        stamp.rotation_euler = (math.pi / 2, math.radians(-10), 0)
        for f, k in ((hit - 5, 2.6), (hit, 0.9), (hit + 3, 1.08), (hit + 6, 1.0)):  # 크게 날아와 찍힌다
            key(stamp, "scale", f, (1.05 * k, 1.05 * k, 1))
        show(stamp, [(hit - 5, TOTAL + 1)])
        mats = [flat(f"confetti_{i}", c, emit=1.5) for i, c in enumerate([plan.ACCENT, (1.0, 0.82, 0.25), (0.95, 0.3, 0.4), (1, 1, 1), (0.4, 0.6, 1.0)])]
        for i in range(34):  # 색종이
            bpy.ops.mesh.primitive_plane_add(size=0.085, location=(0, 0, 2.6))
            c = bpy.context.object
            c.name = f"confetti_{i}"
            c.data.materials.append(mats[i % len(mats)])
            ang, r = random.uniform(0, math.tau), random.uniform(0.7, 1.9)
            x, z = math.cos(ang) * r, 2.6 + abs(math.sin(ang)) * r * 0.9 + 0.3
            y = random.uniform(-0.9, 0.2)
            key(c, "location", hit, (0.4, 0.2, 2.5))
            key(c, "location", hit + 9, (x, y, z))
            key(c, "location", hit + 46, (x * 1.15, y, z - random.uniform(1.6, 2.6)))
            key(c, "rotation_euler", hit, (0, 0, 0))
            key(c, "rotation_euler", hit + 46, (random.uniform(3, 9), random.uniform(3, 9), random.uniform(0, 6)))
            show(c, [(hit, TOTAL + 1)])

# ── 카메라: 세로 화면이라 가로 화각이 좁다(렌즈 50 에서 약 23도). 컷 안에서 천천히 다가간다 ──
CAMS = {  # 이름: (시작 위치, 끝 위치, 바라볼 점, 렌즈)
    "wide": ((0.0, -9.3, 1.5), (0.0, -8.8, 1.5), (0, 0, 1.36), 50),  # 전신 + 머리 위 카드
    "card": ((0.5, -8.2, 2.4), (0.2, -7.8, 2.4), (0, 0.2, 2.28), 50),  # 카드 중심
    "face": ((-0.5, -4.5, 1.55), (-0.3, -4.1, 1.55), (0, 0, 1.5), 50),  # 얼굴 가까이
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
            key(cam, "location", b, p1)

scene.render.fps = plan.FPS
scene.frame_start, scene.frame_end = 1, TOTAL
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
print("SAVED", len(bpy.data.objects))
