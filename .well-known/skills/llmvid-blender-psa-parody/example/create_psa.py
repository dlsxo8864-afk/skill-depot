"""Blender 4.5+ / 5.x 공익광고 패러디 3D 씬 자동 생성 스크립트.

timeline JSON 파일을 읽어 멀티 샷 3D 애니메틱 씬을 구성하고 .blend 파일로 저장합니다.
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

import bmesh
import bpy
import mathutils

# -----------------------------------------------------------------------------
# 글꼴 로더 (fontfind.py 연동)
# -----------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

LOADED_FONT: Optional[bpy.types.VectorFont] = None


def load_font() -> None:
    """팻말 글자용 한글 글꼴을 읽는다. 장면을 비운 뒤(read_factory_settings 뒤)에 불러야 한다."""
    global LOADED_FONT
    LOADED_FONT = None
    try:
        import fontfind  # type: ignore

        font_path = fontfind.find_font(bold=True)
        if font_path and os.path.exists(font_path):
            LOADED_FONT = bpy.data.fonts.load(font_path)
    except Exception as exc:  # 글꼴이 없으면 블렌더 기본 글꼴(한글 미지원)로 넘어간다
        print(f"FONT_WARNING {exc}")
        LOADED_FONT = None


# -----------------------------------------------------------------------------
# 색상 및 보조 유틸리티
# -----------------------------------------------------------------------------
def hex_to_linear(hex_str: str, alpha: float = 1.0) -> Tuple[float, float, float, float]:
    """HEX 색상 문자열(#RRGGBB)을 선형 sRGB 튜플로 변환."""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    if len(hex_str) != 6:
        return (1.0, 1.0, 1.0, alpha)
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0

    def srgb_to_lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return (srgb_to_lin(r), srgb_to_lin(g), srgb_to_lin(b), alpha)


def fcurves_of(id_data: Any) -> list:
    """ID 에 붙은 액션의 F-커브 목록. 4.x(action.fcurves)와 5.x(레이어·스트립·채널백) 둘 다 읽는다."""
    anim = getattr(id_data, "animation_data", None)
    action = anim.action if anim else None
    if action is None:
        return []
    legacy = getattr(action, "fcurves", None)
    if legacy is not None:
        return list(legacy)
    curves: list = []
    for layer in action.layers:
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []):
                curves.extend(bag.fcurves)
    return curves


def key(target: Any, data_path: str, frame: int | float, interp: str = "BEZIER", index: int = -1) -> None:
    """키프레임을 넣고 그 키의 보간을 직접 정한다.

    블렌더 5.x 는 환경 설정의 '새 키 보간'을 keyframe_insert 에 적용하지 않는다(실측).
    """
    if index >= 0:
        target.keyframe_insert(data_path=data_path, index=index, frame=frame)
    else:
        target.keyframe_insert(data_path=data_path, frame=frame)

    try:
        rna_path = target.path_from_id(data_path)
    except Exception:
        rna_path = data_path
    for curve in fcurves_of(target.id_data):
        if curve.data_path != rna_path:
            continue
        if index >= 0 and curve.array_index != index:
            continue
        for point in curve.keyframe_points:
            if abs(point.co[0] - frame) < 0.5:
                point.interpolation = interp


def get_principled_socket(mat: bpy.types.Material, *candidates: str) -> Optional[bpy.types.NodeSocket]:
    """Principled BSDF 노드에서 버전별 소켓 이름 차이를 고려하여 소켓을 반환."""
    if not mat.use_nodes or not mat.node_tree:
        return None
    for node in mat.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            for c in candidates:
                if c in node.inputs:
                    return node.inputs[c]
    return None


def make_material(
    name: str,
    color: Tuple[float, float, float, float] | str,
    roughness: float = 0.5,
    metallic: float = 0.0,
    emission_color: Optional[Tuple[float, float, float, float] | str] = None,
    emission_strength: float = 0.0,
) -> bpy.types.Material:
    """표준 Principled BSDF 머티리얼 생성."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    tree = mat.node_tree
    if tree is None:
        return mat
    nodes = tree.nodes
    bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not bsdf:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")

    col_rgba = hex_to_linear(color) if isinstance(color, str) else color
    base_col = get_principled_socket(mat, "Base Color", "BaseColor")
    if base_col:
        base_col.default_value = col_rgba

    rough = get_principled_socket(mat, "Roughness")
    if rough:
        rough.default_value = roughness

    metal = get_principled_socket(mat, "Metallic")
    if metal:
        metal.default_value = metallic

    if emission_color is not None:
        em_rgba = hex_to_linear(emission_color) if isinstance(emission_color, str) else emission_color
        em_sock = get_principled_socket(mat, "Emission Color", "Emission")
        if em_sock:
            em_sock.default_value = em_rgba
        em_str = get_principled_socket(mat, "Emission Strength")
        if em_str:
            em_str.default_value = emission_strength

    return mat


def key_park(park: bpy.types.Object, world_offset_x: float, shot_first: int, shot_last: int) -> None:
    """샷 구간에서만 보이게 한다. 구간 밖에서는 z=-2000 으로 내려 둔다."""
    hidden = (world_offset_x, 0.0, -2000.0)
    shown = (world_offset_x, 0.0, 0.0)
    for frame, loc in ((shot_first - 1, hidden), (shot_first, shown), (shot_last, shown), (shot_last + 1, hidden)):
        park.location = loc
        key(park, "location", frame, "CONSTANT")


def create_empty(
    name: str,
    parent: Optional[bpy.types.Object] = None,
    loc: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    col: Optional[bpy.types.Collection] = None,
) -> bpy.types.Object:
    """위계 구조용 Empty 객체 생성."""
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.2
    empty.location = loc
    if parent:
        empty.parent = parent
    target_col = col if col else bpy.context.scene.collection
    target_col.objects.link(empty)
    return empty


# -----------------------------------------------------------------------------
# bmesh 기반 기본 메쉬 빌더 (bpy.ops 루프 방지)
# -----------------------------------------------------------------------------
def mesh_cube(name: str, size: Tuple[float, float, float] = (1.0, 1.0, 1.0)) -> bpy.types.Mesh:
    """지정된 크기의 육면체 메쉬 생성."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def mesh_rounded_box(name: str, size: Tuple[float, float, float], bevel: float = 0.06, segments: int = 4) -> bpy.types.Mesh:
    """모서리를 둥글린 상자(몸통용). 각진 상자는 빛날 때 납작한 판처럼 보인다."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=segments, profile=0.5, affect="EDGES")
    for f in bm.faces:
        f.smooth = True
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def mesh_uvsphere(name: str, radius: float = 1.0, u_segments: int = 16, v_segments: int = 12) -> bpy.types.Mesh:
    """구형 메쉬 생성 및 부드러운 음영 처리."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u_segments, v_segments=v_segments, radius=radius)
    for f in bm.faces:
        f.smooth = True
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def mesh_hair_cap(name: str, radius: float = 0.12) -> bpy.types.Mesh:
    """머리카락 캡. 구에서 얼굴이 보일 앞쪽 아래(-Y, 눈높이 아래)와 턱 아래를 지운다."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=14, radius=radius)
    drop = [v for v in bm.verts if (v.co.y < -0.02 * radius / 0.12 and v.co.z < 0.045 * radius / 0.12) or v.co.z < -0.085 * radius / 0.12]
    bmesh.ops.delete(bm, geom=drop, context="VERTS")
    for f in bm.faces:
        f.smooth = True
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def mesh_cylinder(name: str, radius: float = 0.5, depth: float = 1.0, segments: int = 16) -> bpy.types.Mesh:
    """원기둥 메쉬 생성."""
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius,
        radius2=radius,
        depth=depth,
    )
    for f in bm.faces:
        if len(f.verts) == 4:
            f.smooth = True
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def mesh_capsule(name: str, radius: float = 0.05, length: float = 0.3, segments: int = 12) -> bpy.types.Mesh:
    """상하 반구가 붙은 캡슐형 사지 메쉬 생성 (중심 기준 z축 배치)."""
    half_len = max(0.0, length - 2.0 * radius) * 0.5

    # 원기둥 하나와 양 끝의 구 두 개를 한 메시에 겹쳐 둔다
    bm_final = bmesh.new()
    bmesh.ops.create_cone(
        bm_final,
        cap_ends=False,
        cap_tris=False,
        segments=segments,
        radius1=radius,
        radius2=radius,
        depth=max(0.001, half_len * 2.0),
    )
    s1 = bmesh.ops.create_uvsphere(bm_final, u_segments=segments, v_segments=segments // 2, radius=radius)
    for v in s1["verts"]:
        v.co.z += half_len
    s2 = bmesh.ops.create_uvsphere(bm_final, u_segments=segments, v_segments=segments // 2, radius=radius)
    for v in s2["verts"]:
        v.co.z -= half_len

    for f in bm_final.faces:
        f.smooth = True

    mesh = bpy.data.meshes.new(name)
    bm_final.to_mesh(mesh)
    bm_final.free()
    return mesh


def create_mesh_object(
    name: str,
    mesh: bpy.types.Mesh,
    col: bpy.types.Collection,
    parent: Optional[bpy.types.Object] = None,
    loc: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    rot: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    mat: Optional[bpy.types.Material] = None,
) -> bpy.types.Object:
    """메쉬와 오브젝트를 연결하고 위치 및 머티리얼을 설정."""
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = rot
    obj.scale = scale
    if parent:
        obj.parent = parent
    if mat:
        obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj


# -----------------------------------------------------------------------------
# 캐릭터 빌더 (마네킹 계층 구조 및 머티리얼 독립 복제)
# -----------------------------------------------------------------------------
VALID_OUTFITS = {"knit", "uniform", "coat", "hoodie"}


class CharacterRig:
    """마네킹 캐릭터 피벗 및 컨트롤러 보관용 컨테이너."""

    def __init__(self) -> None:
        self.park: bpy.types.Object
        self.root: bpy.types.Object
        self.body: bpy.types.Object
        self.spine: bpy.types.Object
        self.neck: bpy.types.Object
        self.shoulder_l: bpy.types.Object
        self.shoulder_r: bpy.types.Object
        self.elbow_l: bpy.types.Object
        self.elbow_r: bpy.types.Object
        self.hip_l: bpy.types.Object
        self.hip_r: bpy.types.Object
        self.knee_l: bpy.types.Object
        self.knee_r: bpy.types.Object
        self.materials: List[bpy.types.Material] = []
        self.glow_light: Optional[bpy.types.Object] = None


def build_character(
    name: str,
    cast_cfg: Dict[str, Any],
    col: bpy.types.Collection,
    shot_first: int,
    shot_last: int,
    world_offset_x: float,
    at: Tuple[float, float, float],
    heading: float,
) -> CharacterRig:
    """마네킹 스타일의 3D 캐릭터 조립 (자체 독립 머티리얼 부여)."""
    outfit = cast_cfg.get("outfit", "knit")
    if outfit not in VALID_OUTFITS:
        raise ValueError(f"알 수 없는 의상 스타일 '{outfit}'. 허용: {sorted(list(VALID_OUTFITS))}")

    skin_col = cast_cfg.get("skin", "#e8bf9a")
    hair_col = cast_cfg.get("hair", "#1c1a19")
    top_col = cast_cfg.get("top", "#1f1f22")
    bot_col = cast_cfg.get("bottom", "#3a3f4a")
    shoe_col = cast_cfg.get("shoes", "#e9e9e9")
    has_eyes = cast_cfg.get("eyes", True)

    # 인스턴스 전용 머티리얼 복제본 생성
    mat_skin = make_material(f"{name}_Skin", skin_col, roughness=0.6)
    mat_hair = make_material(f"{name}_Hair", hair_col, roughness=0.7)
    mat_top = make_material(f"{name}_Top", top_col, roughness=0.7)
    mat_bot = make_material(f"{name}_Bottom", bot_col, roughness=0.8)
    mat_shoes = make_material(f"{name}_Shoes", shoe_col, roughness=0.5)
    mat_eye = make_material(f"{name}_Eye", "#101010", roughness=0.2)

    rig = CharacterRig()
    rig.materials = [mat_skin, mat_hair, mat_top, mat_bot, mat_shoes, mat_eye]

    # 1. Park Empty (샷 범위 외에는 z=-2000으로 숨김 처리)
    park = create_empty(f"{name}_Park", col=col)
    rig.park = park
    key_park(park, world_offset_x, shot_first, shot_last)

    # 2. Root Empty (로컬 좌표 및 헤딩 회전: 0도는 -Y 방향)
    root = create_empty(f"{name}_Root", parent=park, loc=at, col=col)
    root.rotation_euler = (0.0, 0.0, math.radians(heading))
    rig.root = root
    # 샷 첫 프레임에 처음 위치와 방향을 고정한다(walk 가 뒤에서 키를 넣어도 그 전까지 유지)
    key(root, "location", shot_first, "CONSTANT")
    key(root, "rotation_euler", shot_first, "CONSTANT")

    # 3. Body & Pivot Empties
    # 골반 위치 z=0.95 기준
    body = create_empty(f"{name}_Body", parent=root, loc=(0.0, 0.0, 0.95), col=col)
    rig.body = body

    # 골반 상단 spine
    spine = create_empty(f"{name}_Spine", parent=body, loc=(0.0, 0.0, 0.08), col=col)
    rig.spine = spine

    # 토르소 및 목
    neck = create_empty(f"{name}_Neck", parent=spine, loc=(0.0, 0.0, 0.48), col=col)
    rig.neck = neck

    # 어깨
    sh_l = create_empty(f"{name}_Shoulder_L", parent=spine, loc=(0.23, 0.0, 0.42), col=col)
    sh_r = create_empty(f"{name}_Shoulder_R", parent=spine, loc=(-0.23, 0.0, 0.42), col=col)
    rig.shoulder_l = sh_l
    rig.shoulder_r = sh_r

    # 팔꿈치
    el_l = create_empty(f"{name}_Elbow_L", parent=sh_l, loc=(0.0, 0.0, -0.28), col=col)
    el_r = create_empty(f"{name}_Elbow_R", parent=sh_r, loc=(0.0, 0.0, -0.28), col=col)
    rig.elbow_l = el_l
    rig.elbow_r = el_r

    # 엉덩이/고관절
    hip_l = create_empty(f"{name}_Hip_L", parent=body, loc=(0.11, 0.0, -0.06), col=col)
    hip_r = create_empty(f"{name}_Hip_R", parent=body, loc=(-0.11, 0.0, -0.06), col=col)
    rig.hip_l = hip_l
    rig.hip_r = hip_r

    # 무릎
    kn_l = create_empty(f"{name}_Knee_L", parent=hip_l, loc=(0.0, 0.0, -0.42), col=col)
    kn_r = create_empty(f"{name}_Knee_R", parent=hip_r, loc=(0.0, 0.0, -0.42), col=col)
    rig.knee_l = kn_l
    rig.knee_r = kn_r

    # 4. 신체 부위 메쉬 결합
    # (1) 골반
    m_pelvis = mesh_cube(f"{name}_m_pelvis", (0.34, 0.20, 0.16))
    create_mesh_object(f"{name}_Pelvis", m_pelvis, col, parent=body, loc=(0, 0, 0), mat=mat_bot)

    # (2) 몸통 (토르소 0.40 x 0.22 x 0.55)
    m_torso = mesh_rounded_box(f"{name}_m_torso", (0.38, 0.22, 0.48), bevel=0.07)
    create_mesh_object(f"{name}_Torso", m_torso, col, parent=spine, loc=(0, 0, 0.24), mat=mat_top)

    # (3) 목 & 머리
    m_neck = mesh_cylinder(f"{name}_m_neck", radius=0.045, depth=0.10)
    create_mesh_object(f"{name}_NeckMesh", m_neck, col, parent=neck, loc=(0, 0, 0.05), mat=mat_skin)

    m_head = mesh_uvsphere(f"{name}_m_head", radius=0.115)
    create_mesh_object(
        f"{name}_HeadMesh",
        m_head,
        col,
        parent=neck,
        loc=(0, 0, 0.20),
        scale=(1.0, 1.0, 1.15),
        mat=mat_skin,
    )

    # 헤어 캡 (머리보다 약간 큰 구에서 얼굴 쪽 앞·아래를 잘라 낸 모양)
    m_hair = mesh_hair_cap(f"{name}_m_hair", radius=0.12)
    create_mesh_object(
        f"{name}_HairCap",
        m_hair,
        col,
        parent=neck,
        loc=(0, 0.01, 0.22),
        scale=(1.04, 1.02, 1.1),
        mat=mat_hair,
    )

    # 눈 (eyes=True일 때 -Y 방향 전면에 작은 검은 구슬)
    if has_eyes:
        m_eye = mesh_uvsphere(f"{name}_m_eye", radius=0.016)
        create_mesh_object(f"{name}_Eye_L", m_eye, col, parent=neck, loc=(0.045, -0.11, 0.20), mat=mat_eye)
        create_mesh_object(f"{name}_Eye_R", m_eye, col, parent=neck, loc=(-0.045, -0.11, 0.20), mat=mat_eye)

    # (4) 팔 (어깨 -> 팔꿈치 -> 손)
    m_arm_upper = mesh_capsule(f"{name}_m_arm_up", radius=0.045, length=0.28)
    m_arm_lower = mesh_capsule(f"{name}_m_arm_low", radius=0.042, length=0.26)
    m_hand = mesh_uvsphere(f"{name}_m_hand", radius=0.042)

    # 왼팔
    create_mesh_object(f"{name}_ArmUp_L", m_arm_upper, col, parent=sh_l, loc=(0, 0, -0.14), mat=mat_top)
    create_mesh_object(f"{name}_ArmLow_L", m_arm_lower, col, parent=el_l, loc=(0, 0, -0.13), mat=mat_top)
    create_mesh_object(f"{name}_Hand_L", m_hand, col, parent=el_l, loc=(0, 0, -0.27), mat=mat_skin)

    # 오른팔
    create_mesh_object(f"{name}_ArmUp_R", m_arm_upper, col, parent=sh_r, loc=(0, 0, -0.14), mat=mat_top)
    create_mesh_object(f"{name}_ArmLow_R", m_arm_lower, col, parent=el_r, loc=(0, 0, -0.13), mat=mat_top)
    create_mesh_object(f"{name}_Hand_R", m_hand, col, parent=el_r, loc=(0, 0, -0.27), mat=mat_skin)

    # (5) 다리 (고관절 -> 무릎 -> 신발)
    m_leg_upper = mesh_capsule(f"{name}_m_leg_up", radius=0.065, length=0.42)
    m_leg_lower = mesh_capsule(f"{name}_m_leg_low", radius=0.060, length=0.40)
    m_shoe = mesh_cube(f"{name}_m_shoe", (0.12, 0.22, 0.10))

    # 왼다리
    create_mesh_object(f"{name}_LegUp_L", m_leg_upper, col, parent=hip_l, loc=(0, 0, -0.21), mat=mat_bot)
    create_mesh_object(f"{name}_LegLow_L", m_leg_lower, col, parent=kn_l, loc=(0, 0, -0.20), mat=mat_bot)
    create_mesh_object(f"{name}_Shoe_L", m_shoe, col, parent=kn_l, loc=(0, -0.04, -0.42), mat=mat_shoes)

    # 오른다리
    create_mesh_object(f"{name}_LegUp_R", m_leg_upper, col, parent=hip_r, loc=(0, 0, -0.21), mat=mat_bot)
    create_mesh_object(f"{name}_LegLow_R", m_leg_lower, col, parent=kn_r, loc=(0, 0, -0.20), mat=mat_bot)
    create_mesh_object(f"{name}_Shoe_R", m_shoe, col, parent=kn_r, loc=(0, -0.04, -0.42), mat=mat_shoes)

    # (6) 의상별 추가 디테일
    if outfit == "uniform":
        # 정모(모자) 및 챙, 벨트, 견장
        m_cap = mesh_cylinder(f"{name}_m_cap", radius=0.125, depth=0.05)
        create_mesh_object(f"{name}_Cap", m_cap, col, parent=neck, loc=(0, 0.02, 0.31), mat=mat_top)
        m_visor = mesh_cube(f"{name}_m_visor", (0.14, 0.07, 0.015))
        create_mesh_object(
            f"{name}_Visor",
            m_visor,
            col,
            parent=neck,
            loc=(0, -0.10, 0.28),
            rot=(math.radians(15), 0, 0),
            mat=mat_eye,
        )
        m_belt = mesh_cube(f"{name}_m_belt", (0.39, 0.23, 0.05))
        create_mesh_object(f"{name}_Belt", m_belt, col, parent=spine, loc=(0, 0, 0.02), mat=mat_eye)
        # 어깨 견장
        m_bar = mesh_cube(f"{name}_m_bar", (0.08, 0.03, 0.01))
        mat_gold = make_material(f"{name}_Gold", "#ffcc00", roughness=0.3)
        rig.materials.append(mat_gold)
        create_mesh_object(f"{name}_Bar_L", m_bar, col, parent=sh_l, loc=(0, 0, 0.04), mat=mat_gold)
        create_mesh_object(f"{name}_Bar_R", m_bar, col, parent=sh_r, loc=(0, 0, 0.04), mat=mat_gold)
    elif outfit == "coat":
        # 허리부터 무릎까지 내려오는 긴 코트 단
        m_skirt = mesh_cylinder(f"{name}_m_coat", radius=0.22, depth=0.50)
        create_mesh_object(f"{name}_CoatBottom", m_skirt, col, parent=body, loc=(0, 0, -0.25), mat=mat_top)
    elif outfit == "hoodie":
        # 머리 뒤쪽 후드 반구
        m_hood = mesh_uvsphere(f"{name}_m_hood", radius=0.15)
        create_mesh_object(
            f"{name}_Hood",
            m_hood,
            col,
            parent=neck,
            loc=(0, 0.08, 0.16),
            scale=(1.1, 0.9, 1.1),
            mat=mat_top,
        )

    # 자체 발광용 포인트 라이트 (가슴 높이)
    light_data = bpy.data.lights.new(name=f"{name}_GlowLight", type="POINT")
    light_data.energy = 0.0
    # 빛이 몸 안에서 나오므로 그림자를 켜면 몸 틈새로만 새어 바닥에 이상한 무늬가 생긴다
    light_data.use_shadow = False
    light_obj = bpy.data.objects.new(name=f"{name}_GlowLight", object_data=light_data)
    light_obj.location = (0.0, -0.1, 1.25)
    light_obj.parent = root
    col.objects.link(light_obj)
    rig.glow_light = light_obj

    # 내장 점광은 주변만 밝히고 자기 몸은 비추지 않게 한다(라이트 링킹).
    # 몸까지 비추면 광원에 가까운 팔만 하얗게 날아가고 몸통(광원을 품은 쪽)은 칙칙하게 남는다.
    # 라이트 링킹이 없는 버전이면 건너뛴다(그 경우 팔이 조금 더 밝게 보일 뿐 동작은 같다).
    try:
        excl = bpy.data.collections.new(f"{name}_GlowExclude")
        for child in park.children_recursive:
            if child.type == "MESH":
                excl.objects.link(child)
        for entry in excl.collection_objects:
            entry.light_linking.link_state = "EXCLUDE"
        light_obj.light_linking.receiver_collection = excl
    except (AttributeError, TypeError, RuntimeError) as exc:
        print(f"GLOW_LINK_SKIPPED {name}: {exc}")

    return rig


# -----------------------------------------------------------------------------
# 캐릭터 액션 등록 및 애니메이션 적용기
# -----------------------------------------------------------------------------
VALID_ACTIONS = {"idle", "walk", "reach", "bow", "nod", "point", "shrug", "sit", "glow"}


def act_idle(rig: CharacterRig, f0: int, f1: int, fps: float, **kwargs: Any) -> None:
    """호흡에 따른 미세 바운스와 미세 흔들림."""
    for f in range(f0, f1 + 1, 4):
        t = (f - f0) / fps
        bob = math.sin(t * 3.0) * 0.008
        sway = math.sin(t * 1.5) * 0.01
        rig.body.location = (0.0, 0.0, 0.95 + bob)
        key(rig.body, "location", f, "BEZIER", index=2)
        rig.spine.rotation_euler = (0.0, sway, 0.0)
        key(rig.spine, "rotation_euler", f, "BEZIER", index=1)


def act_walk(rig: CharacterRig, f0: int, f1: int, fps: float, to: Tuple[float, float] = (0.0, 0.0), **kwargs: Any) -> None:
    """목표 지점으로 보행 이동 및 양다리/양팔 역위상 보행 사이클 적용."""
    start_pos = (rig.root.location.x, rig.root.location.y, rig.root.location.z)
    end_pos = (float(to[0]), float(to[1]), start_pos[2])

    # 이동 방향에 맞춘 헤딩 자동 갱신
    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    if math.hypot(dx, dy) > 0.001:
        # 0도는 -Y, 90도는 +X
        target_heading = math.degrees(math.atan2(dx, -dy))
        rig.root.rotation_euler = (0.0, 0.0, math.radians(target_heading))
        key(rig.root, "rotation_euler", f0, "CONSTANT", index=2)

    # 루트 선형 이동 키프레임
    rig.root.location = start_pos
    key(rig.root, "location", f0, "LINEAR")
    rig.root.location = end_pos
    key(rig.root, "location", f1, "LINEAR")

    step_freq = 1.8  # 초당 1.8 걸음
    for f in range(f0, f1 + 1, 2):
        t = (f - f0) / fps
        phase = 2.0 * math.pi * step_freq * t
        # 엉덩이 스윙 +-28도
        hip_swing = math.sin(phase) * math.radians(28.0)
        rig.hip_l.rotation_euler = (hip_swing, 0.0, 0.0)
        rig.hip_r.rotation_euler = (-hip_swing, 0.0, 0.0)
        key(rig.hip_l, "rotation_euler", f, "BEZIER", index=0)
        key(rig.hip_r, "rotation_euler", f, "BEZIER", index=0)

        # 무릎 굽힘 (0 ~ 35도)
        knee_l_bend = max(0.0, -math.sin(phase)) * math.radians(35.0)
        knee_r_bend = max(0.0, math.sin(phase)) * math.radians(35.0)
        rig.knee_l.rotation_euler = (knee_l_bend, 0.0, 0.0)
        rig.knee_r.rotation_euler = (knee_r_bend, 0.0, 0.0)
        key(rig.knee_l, "rotation_euler", f, "BEZIER", index=0)
        key(rig.knee_r, "rotation_euler", f, "BEZIER", index=0)

        # 팔 스윙 (다리와 반대 방향)
        arm_swing = -math.sin(phase) * math.radians(24.0)
        rig.shoulder_l.rotation_euler = (arm_swing, 0.0, 0.0)
        rig.shoulder_r.rotation_euler = (-arm_swing, 0.0, 0.0)
        key(rig.shoulder_l, "rotation_euler", f, "BEZIER", index=0)
        key(rig.shoulder_r, "rotation_euler", f, "BEZIER", index=0)

    # 완료 시 기본 서 있는 자세로 복귀
    rig.hip_l.rotation_euler = (0, 0, 0)
    rig.hip_r.rotation_euler = (0, 0, 0)
    rig.knee_l.rotation_euler = (0, 0, 0)
    rig.knee_r.rotation_euler = (0, 0, 0)
    rig.shoulder_l.rotation_euler = (0, 0, 0)
    rig.shoulder_r.rotation_euler = (0, 0, 0)
    for part in (rig.hip_l, rig.hip_r, rig.knee_l, rig.knee_r, rig.shoulder_l, rig.shoulder_r):
        key(part, "rotation_euler", f1, "BEZIER", index=0)


def act_reach(rig: CharacterRig, f0: int, f1: int, fps: float, **kwargs: Any) -> None:
    """오른쪽 어깨 전방 80도, 몸통 앞 기울기 12도."""
    rig.shoulder_r.rotation_euler = (0.0, 0.0, 0.0)
    rig.spine.rotation_euler = (0.0, 0.0, 0.0)
    key(rig.shoulder_r, "rotation_euler", f0, "BEZIER", index=0)
    key(rig.spine, "rotation_euler", f0, "BEZIER", index=0)

    # 앞을 향해 뻗기 (모델 전면이 -Y이므로 회전축 방향 조정)
    rig.shoulder_r.rotation_euler = (math.radians(-80.0), 0.0, 0.0)
    rig.spine.rotation_euler = (math.radians(12.0), 0.0, 0.0)
    key(rig.shoulder_r, "rotation_euler", f1, "BEZIER", index=0)
    key(rig.spine, "rotation_euler", f1, "BEZIER", index=0)


def act_bow(rig: CharacterRig, f0: int, f1: int, fps: float, **kwargs: Any) -> None:
    """허리 숙여 인사 (중간 프레임에서 전방 35도 숙인 뒤 복귀)."""
    f_mid = (f0 + f1) // 2
    rig.spine.rotation_euler = (0.0, 0.0, 0.0)
    key(rig.spine, "rotation_euler", f0, "BEZIER", index=0)

    rig.spine.rotation_euler = (math.radians(35.0), 0.0, 0.0)
    key(rig.spine, "rotation_euler", f_mid, "BEZIER", index=0)

    rig.spine.rotation_euler = (0.0, 0.0, 0.0)
    key(rig.spine, "rotation_euler", f1, "BEZIER", index=0)


def act_nod(rig: CharacterRig, f0: int, f1: int, fps: float, **kwargs: Any) -> None:
    """고개 끄덕임."""
    f_mid = (f0 + f1) // 2
    rig.neck.rotation_euler = (0.0, 0.0, 0.0)
    key(rig.neck, "rotation_euler", f0, "BEZIER", index=0)
    rig.neck.rotation_euler = (math.radians(22.0), 0.0, 0.0)
    key(rig.neck, "rotation_euler", f_mid, "BEZIER", index=0)
    rig.neck.rotation_euler = (0.0, 0.0, 0.0)
    key(rig.neck, "rotation_euler", f1, "BEZIER", index=0)


def act_point(rig: CharacterRig, f0: int, f1: int, fps: float, **kwargs: Any) -> None:
    """오른팔 전방 90도 가리키기."""
    rig.shoulder_r.rotation_euler = (0.0, 0.0, 0.0)
    key(rig.shoulder_r, "rotation_euler", f0, "BEZIER", index=0)
    rig.shoulder_r.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    key(rig.shoulder_r, "rotation_euler", f1, "BEZIER", index=0)


def act_shrug(rig: CharacterRig, f0: int, f1: int, fps: float, **kwargs: Any) -> None:
    """양어깨 으쓱하기."""
    f_mid = (f0 + f1) // 2
    for sh in (rig.shoulder_l, rig.shoulder_r):
        sh.location = (sh.location.x, sh.location.y, 0.42)
        key(sh, "location", f0, "BEZIER", index=2)
        sh.location = (sh.location.x, sh.location.y, 0.48)
        key(sh, "location", f_mid, "BEZIER", index=2)
        sh.location = (sh.location.x, sh.location.y, 0.42)
        key(sh, "location", f1, "BEZIER", index=2)


def act_sit(rig: CharacterRig, f0: int, f1: int, fps: float, **kwargs: Any) -> None:
    """앉는 자세 (엉덩이 90도, 무릎 90도, 바디 하강).
    t0 가 0 이면 샷 처음부터 앉아 있고, 0 보다 크면 t0 에서 6프레임 동안 앉는다. 일어나는 동작은 없다.
    (키가 앉은 자세뿐이면 블렌더가 그 값을 샷 처음부터 쓰므로, t0 > 0 이면 선 자세 키를 먼저 넣는다)"""
    poses = [
        (rig.body, "location", (0.0, 0.0, 0.55), (0.0, 0.0, 0.95)),
        (rig.hip_l, "rotation_euler", (math.radians(-90.0), 0.0, 0.0), (0.0, 0.0, 0.0)),
        (rig.hip_r, "rotation_euler", (math.radians(-90.0), 0.0, 0.0), (0.0, 0.0, 0.0)),
        (rig.knee_l, "rotation_euler", (math.radians(90.0), 0.0, 0.0), (0.0, 0.0, 0.0)),
        (rig.knee_r, "rotation_euler", (math.radians(90.0), 0.0, 0.0), (0.0, 0.0, 0.0)),
    ]
    ease_in = float(kwargs.get("t0", 0.0)) > 0.0 and f1 > f0
    f_on = min(f0 + 6, f1) if ease_in else f0
    for obj, path, pose, rest in poses:
        if ease_in:
            setattr(obj, path, rest)
            key(obj, path, f0, "BEZIER")
        setattr(obj, path, pose)
        key(obj, path, f_on, "BEZIER")
        key(obj, path, f1, "BEZIER")


def act_glow(
    rig: CharacterRig,
    f0: int,
    f1: int,
    fps: float,
    color: str = "#ffe27a",
    strength: float = 25.0,
    **kwargs: Any,
) -> None:
    """캐릭터 인스턴스의 모든 머티리얼 및 내장 라이트 발광 활성화."""
    col_rgba = hex_to_linear(color)
    for mat in rig.materials:
        # 눈과 머리카락은 빛내지 않아야 얼굴이 읽힌다
        if mat.name.endswith(("_Eye", "_Hair")):
            continue
        em_col_sock = get_principled_socket(mat, "Emission Color", "Emission")
        em_str_sock = get_principled_socket(mat, "Emission Strength")
        if em_col_sock:
            em_col_sock.default_value = col_rgba
            key(em_col_sock, "default_value", f0, "CONSTANT")
        if em_str_sock:
            # 몸 재질은 형태와 색이 남을 만큼만 빛내고, 주변을 밝히는 일은 내장 점광이 맡는다
            if f1 > f0:
                em_str_sock.default_value = 0.0
                key(em_str_sock, "default_value", f0, "LINEAR")
            em_str_sock.default_value = float(strength) * 0.08
            key(em_str_sock, "default_value", f1, "LINEAR")

    if rig.glow_light:
        light_data: bpy.types.PointLight = rig.glow_light.data  # type: ignore
        light_data.color = (col_rgba[0], col_rgba[1], col_rgba[2])
        if f1 > f0:
            light_data.energy = 0.0
            key(light_data, "energy", f0, "LINEAR")
        light_data.energy = float(strength) * 30.0
        key(light_data, "energy", f1, "LINEAR")


ACTIONS: Dict[str, Callable[..., None]] = {
    "idle": act_idle,
    "walk": act_walk,
    "reach": act_reach,
    "bow": act_bow,
    "nod": act_nod,
    "point": act_point,
    "shrug": act_shrug,
    "sit": act_sit,
    "glow": act_glow,
}


# -----------------------------------------------------------------------------
# 소품(Props) 빌더
# -----------------------------------------------------------------------------
VALID_PROPS = {"sign", "box", "cone"}


def prop_sign(col: bpy.types.Collection, cfg: Dict[str, Any], shot_first: int, fps: float) -> bpy.types.Object:
    """안내 표지판 (기둥 + 보드 + 텍스트 커브 + 팝업 효과)."""
    at = cfg.get("at", [0.0, 0.0, 0.0])
    heading = cfg.get("heading", 0.0)
    text_content = cfg.get("text", "안내").replace("\\n", "\n")
    board_color = cfg.get("board", "#1f6b3a")
    ink_color = cfg.get("ink", "#ffffff")
    pop_at = cfg.get("pop_at", None)

    root = create_empty("Prop_Sign_Root", loc=tuple(at), col=col)
    root.rotation_euler = (0.0, 0.0, math.radians(heading))

    # 기둥
    m_post = mesh_cylinder("m_sign_post", radius=0.03, depth=1.3)
    mat_post = make_material("Mat_Sign_Post", "#555555", roughness=0.6)
    create_mesh_object("Sign_Post", m_post, col, parent=root, loc=(0.0, 0.0, 0.65), mat=mat_post)

    # 보드 (1.3 x 0.8, 중심 z=1.7)
    m_board = mesh_cube("m_sign_board", (1.3, 0.04, 0.8))
    mat_board = make_material("Mat_Sign_Board", board_color, roughness=0.5)
    create_mesh_object("Sign_Board", m_board, col, parent=root, loc=(0.0, 0.0, 1.7), mat=mat_board)

    # 폰트 텍스트 커브 (보드 전면 -Y 쪽에 0.012 돌출)
    curve_data = bpy.data.curves.new("Sign_Text_Data", type="FONT")
    curve_data.body = text_content
    if LOADED_FONT:
        curve_data.font = LOADED_FONT
    curve_data.align_x = "CENTER"
    curve_data.align_y = "CENTER"

    text_obj = bpy.data.objects.new("Sign_Text", curve_data)
    text_obj.parent = root
    # 앞을 향하도록 x축 90도 회전 (폰트는 XY평면 기본 생성)
    text_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    text_obj.location = (0.0, -0.025, 1.7)

    mat_ink = make_material("Mat_Sign_Ink", ink_color, emission_color=ink_color, emission_strength=1.5)
    text_obj.data.materials.append(mat_ink)
    col.objects.link(text_obj)

    # 보드 규격(85% 폭, 75% 높이) 내에 텍스트 크기 자동 조정
    bpy.context.view_layer.update()
    dim = text_obj.dimensions
    max_w = 1.3 * 0.85
    max_h = 0.8 * 0.75
    # 글자 곡선의 높이는 로컬 Y 다(X 로 90도 세우기 전 기준)
    if dim.x > 0.001 and dim.y > 0.001:
        s = min(max_w / dim.x, max_h / dim.y, 0.35)
        text_obj.scale = (s, s, s)

    # 팝업 스케일 애니메이션
    if pop_at is not None:
        f_pop = shot_first + round(pop_at * fps)
        root.scale = (0.0, 0.0, 0.0)
        key(root, "scale", shot_first, "CONSTANT")
        key(root, "scale", f_pop - 1, "CONSTANT")
        root.scale = (1.12, 1.12, 1.12)
        key(root, "scale", f_pop + 5, "BEZIER")
        root.scale = (1.0, 1.0, 1.0)
        key(root, "scale", f_pop + 8, "BEZIER")

    return root


def prop_box(col: bpy.types.Collection, cfg: Dict[str, Any], shot_first: int, fps: float) -> bpy.types.Object:
    """간이 상자 소품."""
    sz = cfg.get("size", [0.5, 0.5, 0.5])
    c = cfg.get("color", "#8b5a2b")
    at = cfg.get("at", [0.0, 0.0, 0.0])
    m = mesh_cube("m_prop_box", tuple(sz))
    mat = make_material("Mat_Prop_Box", c, roughness=0.6)
    obj = create_mesh_object("Prop_Box", m, col, loc=(at[0], at[1], at[2] + sz[2] * 0.5), mat=mat)
    return obj


def prop_cone(col: bpy.types.Collection, cfg: Dict[str, Any], shot_first: int, fps: float) -> bpy.types.Object:
    """교통 칼라콘 소품."""
    at = cfg.get("at", [0.0, 0.0, 0.0])
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, radius1=0.2, radius2=0.03, depth=0.7, segments=16)
    m = bpy.data.meshes.new("m_prop_cone")
    bm.to_mesh(m)
    bm.free()
    mat = make_material("Mat_Prop_Cone", "#ff5500", roughness=0.4)
    obj = create_mesh_object("Prop_Cone", m, col, loc=(at[0], at[1], at[2] + 0.35), mat=mat)
    return obj


PROPS: Dict[str, Callable[..., bpy.types.Object]] = {
    "sign": prop_sign,
    "box": prop_box,
    "cone": prop_cone,
}


# -----------------------------------------------------------------------------
# 세트(Sets) 빌더
# -----------------------------------------------------------------------------
VALID_SETS = {"room", "street_night"}


def build_room(
    col: bpy.types.Collection, offset_x: float, options: Dict[str, Any], rng: random.Random
) -> List[Tuple[bpy.types.Object, float]]:
    """실내 방 세트 빌드: 바닥, 벽, 천장, 창문, 책상, 모니터, 충전기/케이블, 침대, 조명."""
    lights: List[Tuple[bpy.types.Object, float]] = []
    root = create_empty("Set_Room_Root", loc=(offset_x, 0.0, 0.0), col=col)

    mat_wood = make_material("Room_FloorWood", "#7a4f32", roughness=0.4)
    mat_wall = make_material("Room_Wall", "#e2decb", roughness=0.9)
    mat_white = make_material("Room_White", "#efefef", roughness=0.3)
    mat_desk = make_material("Room_DeskWood", "#3d2817", roughness=0.5)
    mat_metal = make_material("Room_Metal", "#151515", roughness=0.3, metallic=0.9)
    mat_win = make_material("Room_Window", "#0a1020", emission_color="#9cc7ee", emission_strength=0.8)
    mat_led = make_material("Room_GreenLED", "#00ff44", emission_color="#00ff44", emission_strength=20.0)

    # 바닥 (x: -3..3, y: -3..2.8 -> 중심 x=0, y=-0.1, 크기 6 x 5.8)
    m_floor = mesh_cube("m_room_floor", (6.0, 5.8, 0.04))
    create_mesh_object("Room_Floor", m_floor, col, parent=root, loc=(0.0, -0.1, -0.02), mat=mat_wood)

    # 벽 (높이 2.7, 전면 개방)
    # 뒷벽 (y=2.8)
    m_back_wall = mesh_cube("m_room_back_wall", (6.0, 0.1, 2.7))
    create_mesh_object("Room_BackWall", m_back_wall, col, parent=root, loc=(0.0, 2.85, 1.35), mat=mat_wall)
    # 좌측벽 (x=-3)
    m_side_wall = mesh_cube("m_room_side_wall", (0.1, 5.8, 2.7))
    create_mesh_object("Room_LeftWall", m_side_wall, col, parent=root, loc=(-3.05, -0.1, 1.35), mat=mat_wall)
    # 우측벽 (x=3)
    create_mesh_object("Room_RightWall", m_side_wall, col, parent=root, loc=(3.05, -0.1, 1.35), mat=mat_wall)

    # 천장 (아랫면 높이 2.7). 천장이 없으면 화면 위쪽에 하늘(월드 색)이 보여 지붕 없는 방이 된다.
    # 그림자는 만들지 않게 해서 해·하늘 빛은 예전처럼 방 안에 든다. 내려다보는 컷은 set_options.ceiling=false.
    if options.get("ceiling", True):
        m_ceiling = mesh_cube("m_room_ceiling", (6.2, 5.9, 0.1))
        ceiling = create_mesh_object("Room_Ceiling", m_ceiling, col, parent=root, loc=(0.0, -0.05, 2.75), mat=mat_wall)
        ceiling.visible_shadow = False

    # 걸레받이 (Skirting boards)
    m_skirt_back = mesh_cube("m_skirt_b", (6.0, 0.04, 0.12))
    create_mesh_object("Room_SkirtBack", m_skirt_back, col, parent=root, loc=(0.0, 2.78, 0.06), mat=mat_desk)
    m_skirt_side = mesh_cube("m_skirt_s", (0.04, 5.8, 0.12))
    create_mesh_object("Room_SkirtLeft", m_skirt_side, col, parent=root, loc=(-2.98, -0.1, 0.06), mat=mat_desk)
    create_mesh_object("Room_SkirtRight", m_skirt_side, col, parent=root, loc=(2.98, -0.1, 0.06), mat=mat_desk)

    # 뒷벽 창문 (x=1.6, z=1.6, 크기 1.4 x 1.1)
    m_window = mesh_cube("m_room_win", (1.4, 0.08, 1.1))
    create_mesh_object("Room_WindowObj", m_window, col, parent=root, loc=(1.6, 2.81, 1.6), mat=mat_win)

    # 좌측 문 (x=-3, y=0.2, z=1.05)
    m_door = mesh_cube("m_room_door", (0.08, 0.9, 2.1))
    create_mesh_object("Room_Door", m_door, col, parent=root, loc=(-2.98, 0.2, 1.05), mat=mat_desk)
    m_handle = mesh_cylinder("m_door_handle", radius=0.015, depth=0.12)
    create_mesh_object(
        "Room_DoorHandle",
        m_handle,
        col,
        parent=root,
        loc=(-2.92, 0.55, 1.0),
        rot=(0, math.radians(90), 0),
        mat=mat_metal,
    )

    # 책상 (x=-0.6, 상판 z=0.75, 1.4 x 0.6)
    m_desk_top = mesh_cube("m_desk_top", (1.4, 0.6, 0.05))
    create_mesh_object("Room_DeskTop", m_desk_top, col, parent=root, loc=(-0.6, 2.4, 0.725), mat=mat_desk)
    m_leg = mesh_cylinder("m_desk_leg", radius=0.025, depth=0.70)
    for lx, ly in [(-1.25, 2.15), (0.05, 2.15), (-1.25, 2.65), (0.05, 2.65)]:
        create_mesh_object("Room_DeskLeg", m_leg, col, parent=root, loc=(lx, ly, 0.35), mat=mat_metal)

    # 모니터
    m_mon_base = mesh_cube("m_mon_b", (0.24, 0.16, 0.02))
    m_mon_screen = mesh_cube("m_mon_s", (0.65, 0.04, 0.38))
    create_mesh_object("Room_MonBase", m_mon_base, col, parent=root, loc=(-0.6, 2.5, 0.76), mat=mat_metal)
    create_mesh_object("Room_MonScreen", m_mon_screen, col, parent=root, loc=(-0.6, 2.5, 0.98), mat=mat_metal)

    # 휴대폰 (책상 위에 납작하게 누움)
    m_phone = mesh_cube("m_phone", (0.08, 0.16, 0.01))
    create_mesh_object("Room_Phone", m_phone, col, parent=root, loc=(-0.35, 2.3, 0.755), mat=mat_metal)

    # 벽면 콘센트 및 꽂힌 충전기 블록 (z=1.0, 녹색 LED, 얇은 케이블)
    m_outlet = mesh_cube("m_outlet", (0.10, 0.02, 0.10))
    create_mesh_object("Room_OutletPlate", m_outlet, col, parent=root, loc=(-0.6, 2.79, 1.0), mat=mat_white)
    m_charger = mesh_cube("m_charger", (0.05, 0.07, 0.05))
    create_mesh_object("Room_ChargerBlock", m_charger, col, parent=root, loc=(-0.6, 2.75, 1.0), mat=mat_white)
    m_led = mesh_cube("m_led", (0.012, 0.012, 0.012))
    create_mesh_object("Room_ChargerLED", m_led, col, parent=root, loc=(-0.6, 2.71, 1.02), mat=mat_led)

    # 충전기에서 휴대폰으로 이어지는 얇은 케이블 메쉬
    bm_cable = bmesh.new()
    p1 = mathutils.Vector((-0.6, 2.71, 0.98))
    p2 = mathutils.Vector((-0.55, 2.50, 0.76))
    p3 = mathutils.Vector((-0.35, 2.38, 0.755))
    bmesh.ops.create_cone(bm_cable, cap_ends=True, radius1=0.005, radius2=0.005, depth=1.0)
    # 케이블 위치 근사 실린더 변환
    m_cab = bpy.data.meshes.new("m_cable")
    bm_cable.to_mesh(m_cab)
    bm_cable.free()
    create_mesh_object(
        "Room_Cable",
        m_cab,
        col,
        parent=root,
        loc=(-0.48, 2.55, 0.82),
        scale=(0.8, 0.5, 0.4),
        rot=(math.radians(35), 0, math.radians(-20)),
        mat=mat_white,
    )

    # 의자 (0.6, 1.4)
    m_chair_seat = mesh_cube("m_chair_seat", (0.42, 0.42, 0.06))
    create_mesh_object("Room_ChairSeat", m_chair_seat, col, parent=root, loc=(0.6, 1.4, 0.45), mat=mat_desk)
    m_chair_leg = mesh_cylinder("m_chair_leg", radius=0.02, depth=0.45)
    for cx, cy in [(0.43, 1.23), (0.77, 1.23), (0.43, 1.57), (0.77, 1.57)]:
        create_mesh_object("Room_ChairLeg", m_chair_leg, col, parent=root, loc=(cx, cy, 0.225), mat=mat_metal)

    # 침대 (우측 벽면)
    m_bed = mesh_cube("m_bed", (1.2, 2.1, 0.40))
    create_mesh_object("Room_Bed", m_bed, col, parent=root, loc=(2.3, -0.8, 0.20), mat=mat_white)
    m_pillow = mesh_cube("m_pillow", (0.6, 0.35, 0.12))
    create_mesh_object("Room_Pillow", m_pillow, col, parent=root, loc=(2.3, 0.0, 0.45), mat=mat_white)

    # 벽 선반 및 책
    m_shelf = mesh_cube("m_shelf", (1.2, 0.25, 0.04))
    create_mesh_object("Room_WallShelf", m_shelf, col, parent=root, loc=(-1.8, 2.75, 1.6), mat=mat_desk)
    m_book = mesh_cube("m_book", (0.08, 0.2, 0.2))
    mat_book = make_material("Room_BookCover", "#225588", roughness=0.5)
    create_mesh_object("Room_Book1", m_book, col, parent=root, loc=(-1.6, 2.72, 1.72), mat=mat_book)
    create_mesh_object("Room_Book2", m_book, col, parent=root, loc=(-1.7, 2.72, 1.72), mat=mat_white)

    # 플로어 램프 ((2.3, 2.2) 갓 + 포인트 라이트 120W)
    m_fl_post = mesh_cylinder("m_lamp_post", radius=0.02, depth=1.5)
    create_mesh_object("Room_LampPost", m_fl_post, col, parent=root, loc=(2.3, 2.2, 0.75), mat=mat_metal)
    m_fl_shade = mesh_cylinder("m_lamp_shade", radius=0.20, depth=0.25)
    mat_shade = make_material("Room_Shade", "#fff2d0", emission_color="#ffe090", emission_strength=3.0)
    create_mesh_object("Room_LampShade", m_fl_shade, col, parent=root, loc=(2.3, 2.2, 1.55), mat=mat_shade)

    l_floor_data = bpy.data.lights.new(name="Room_Floor_PointLight", type="POINT")
    l_floor_data.energy = 120.0
    l_floor_data.color = (1.0, 0.85, 0.65)
    l_floor_obj = bpy.data.objects.new(name="Room_Floor_PointLight", object_data=l_floor_data)
    l_floor_obj.location = (offset_x + 2.3, 2.2, 1.55)
    col.objects.link(l_floor_obj)
    lights.append((l_floor_obj, 120.0))

    # 천장 조명 ((0, 0, 2.6) 면적 2.0, 500W)
    l_ceil_data = bpy.data.lights.new(name="Room_Ceiling_AreaLight", type="AREA")
    l_ceil_data.shape = "SQUARE"
    l_ceil_data.size = 2.0
    l_ceil_data.energy = 500.0
    l_ceil_data.color = (1.0, 0.95, 0.90)
    l_ceil_obj = bpy.data.objects.new(name="Room_Ceiling_AreaLight", object_data=l_ceil_data)
    l_ceil_obj.location = (offset_x, 0.0, 2.6)
    col.objects.link(l_ceil_obj)
    lights.append((l_ceil_obj, 500.0))

    return lights


def build_street_night(
    col: bpy.types.Collection, offset_x: float, options: Dict[str, Any], rng: random.Random
) -> List[Tuple[bpy.types.Object, float]]:
    """도시 교차로 야경 세트: 아스팔트, 인도, 횡단보도, 차선, 빌딩, 신호등, 차량."""
    lights: List[Tuple[bpy.types.Object, float]] = []
    root = create_empty("Set_Street_Root", loc=(offset_x, 0.0, 0.0), col=col)

    num_cars = int(options.get("cars", 5))

    mat_asphalt = make_material("Street_Asphalt", "#15171b", roughness=0.8)
    mat_sidewalk = make_material("Street_Sidewalk", "#454a52", roughness=0.7)
    mat_stripe = make_material("Street_Stripe", "#e0e2e5", roughness=0.4)
    mat_pole = make_material("Street_Pole", "#22252a", roughness=0.5, metallic=0.7)
    mat_red_light = make_material("Street_RedLight", "#ff1111", emission_color="#ff1111", emission_strength=15.0)
    mat_off_light = make_material("Street_OffLight", "#151515", roughness=0.9)
    mat_headlight = make_material("Car_Headlight", "#ffffff", emission_color="#ffffff", emission_strength=20.0)
    mat_taillight = make_material("Car_Taillight", "#ff2200", emission_color="#ff2200", emission_strength=10.0)

    # 1. 아스팔트 (160 x 160)
    m_asphalt = mesh_cube("m_asphalt", (160.0, 160.0, 0.05))
    create_mesh_object("Street_RoadPlane", m_asphalt, col, parent=root, loc=(0.0, 0.0, -0.025), mat=mat_asphalt)

    # 2. 보도 (4개 코너 블록: |x|>5.5, |y|>5.5, 높이 0.15)
    m_walk = mesh_cube("m_sidewalk", (70.0, 70.0, 0.15))
    for sx in (-1, 1):
        for sy in (-1, 1):
            create_mesh_object(
                f"Street_Sidewalk_{sx}_{sy}",
                m_walk,
                col,
                parent=root,
                loc=(sx * (5.5 + 35.0), sy * (5.5 + 35.0), 0.075),
                mat=mat_sidewalk,
            )

    # 3. 차선 및 횡단보도 (z=0.012)
    m_dash_y = mesh_cube("m_dash_y", (0.2, 2.0, 0.005))
    m_dash_x = mesh_cube("m_dash_x", (2.0, 0.2, 0.005))
    # 남/북 차선
    for y in range(8, 70, 4):
        create_mesh_object(f"Dash_N_{y}", m_dash_y, col, parent=root, loc=(0.0, float(y), 0.012), mat=mat_stripe)
        create_mesh_object(f"Dash_S_{y}", m_dash_y, col, parent=root, loc=(0.0, -float(y), 0.012), mat=mat_stripe)
    # 동/서 차선
    for x in range(8, 70, 4):
        create_mesh_object(f"Dash_E_{x}", m_dash_x, col, parent=root, loc=(float(x), 0.0, 0.012), mat=mat_stripe)
        create_mesh_object(f"Dash_W_{x}", m_dash_x, col, parent=root, loc=(-float(x), 0.0, 0.012), mat=mat_stripe)

    # 횡단보도 줄무늬
    m_cross_v = mesh_cube("m_cross_v", (0.45, 2.5, 0.005))
    m_cross_h = mesh_cube("m_cross_h", (2.5, 0.45, 0.005))
    for i in range(-5, 6):
        # 북측 (y=6.5)
        create_mesh_object(
            f"Cross_N_{i}", m_cross_v, col, parent=root, loc=(i * 0.9, 6.5, 0.012), mat=mat_stripe
        )
        # 남측 (y=-6.5)
        create_mesh_object(
            f"Cross_S_{i}", m_cross_v, col, parent=root, loc=(i * 0.9, -6.5, 0.012), mat=mat_stripe
        )
        # 동측 (x=6.5)
        create_mesh_object(
            f"Cross_E_{i}", m_cross_h, col, parent=root, loc=(6.5, i * 0.9, 0.012), mat=mat_stripe
        )
        # 서측 (x=-6.5)
        create_mesh_object(
            f"Cross_W_{i}", m_cross_h, col, parent=root, loc=(-6.5, i * 0.9, 0.012), mat=mat_stripe
        )

    # 4. 건물 생성 (|x|>=10, |y|>=10, 높이 제한 4 + 0.45*dist <= 30)
    mat_bldg = make_material("Street_BuildingWall", "#0a0d13", roughness=0.8)
    # 창문 격자 그림(8x8 칸)을 상자 투영으로 벽에 입힌다. 옥상은 불을 끈다.
    if mat_bldg.node_tree:
        tree = mat_bldg.node_tree
        cells, cell_px = 8, 8
        size = cells * cell_px
        img = bpy.data.images.new("Street_Windows", width=size, height=size, alpha=False)
        px = [0.0] * (size * size * 4)
        for i in range(3, len(px), 4):
            px[i] = 1.0
        for cell_y in range(cells):
            for cell_x in range(cells):
                roll = rng.random()
                if roll < 0.30:
                    lit = (1.0, 0.78, 0.42)  # 따뜻한 불빛
                elif roll < 0.38:
                    lit = (0.55, 0.72, 1.0)  # 찬 불빛
                else:
                    lit = (0.015, 0.018, 0.025)  # 꺼진 창
                for py in range(2, 7):
                    for pxi in range(2, 6):
                        i = ((cell_y * cell_px + py) * size + cell_x * cell_px + pxi) * 4
                        px[i], px[i + 1], px[i + 2] = lit
        img.pixels.foreach_set(px)
        img.pack()

        n_coord = tree.nodes.new("ShaderNodeTexCoord")
        n_map = tree.nodes.new("ShaderNodeMapping")
        # 창 한 칸: 가로 1.6m, 세로 3m
        n_map.inputs["Scale"].default_value = (1.0 / 12.8, 1.0 / 12.8, 1.0 / 24.0)
        n_img = tree.nodes.new("ShaderNodeTexImage")
        n_img.image = img
        n_img.interpolation = "Closest"
        n_img.projection = "BOX"
        tree.links.new(n_coord.outputs["Object"], n_map.inputs["Vector"])
        tree.links.new(n_map.outputs["Vector"], n_img.inputs["Vector"])

        # 옥상(법선이 위)은 발광 0
        n_geo = tree.nodes.new("ShaderNodeNewGeometry")
        n_sep = tree.nodes.new("ShaderNodeSeparateXYZ")
        n_abs = tree.nodes.new("ShaderNodeMath")
        n_abs.operation = "ABSOLUTE"
        n_side = tree.nodes.new("ShaderNodeMath")
        n_side.operation = "LESS_THAN"
        n_side.inputs[1].default_value = 0.5
        n_gain = tree.nodes.new("ShaderNodeMath")
        n_gain.operation = "MULTIPLY"
        n_gain.inputs[1].default_value = 2.0
        tree.links.new(n_geo.outputs["Normal"], n_sep.inputs[0])
        tree.links.new(n_sep.outputs["Z"], n_abs.inputs[0])
        tree.links.new(n_abs.outputs[0], n_side.inputs[0])
        tree.links.new(n_side.outputs[0], n_gain.inputs[0])

        em_sock = get_principled_socket(mat_bldg, "Emission Color", "Emission")
        em_str = get_principled_socket(mat_bldg, "Emission Strength")
        if em_sock:
            tree.links.new(n_img.outputs["Color"], em_sock)
        if em_str:
            tree.links.new(n_gain.outputs[0], em_str)

    # 건물 안쪽 면이 보도(5.5~10.5)를 덮지 않게 중심 16 이상, 폭 11 이하로 둔다
    for bx in (-46, -30, -16, 16, 30, 46):
        for by in (-46, -30, -16, 16, 30, 46):
            dist = math.hypot(bx, by)
            max_h = min(30.0, 4.0 + 0.45 * dist)
            w = rng.uniform(8.0, 11.0)
            d = rng.uniform(8.0, 11.0)
            h = rng.uniform(max_h * 0.6, max_h)
            m_bldg = mesh_cube(f"m_bldg_{bx}_{by}", (w, d, h))
            create_mesh_object(
                f"Bldg_{bx}_{by}", m_bldg, col, parent=root, loc=(float(bx), float(by), h * 0.5), mat=mat_bldg
            )

    # 5. 신호등 (4개 코너: x=+-6.0, y=+-6.0)
    m_tl_pole = mesh_cylinder("m_tl_pole", radius=0.08, depth=4.5)
    m_tl_box = mesh_cube("m_tl_box", (0.35, 0.35, 0.9))
    m_tl_lamp = mesh_uvsphere("m_tl_lamp", radius=0.09)
    for cx, cy in [(-6.0, -6.0), (6.0, -6.0), (-6.0, 6.0), (6.0, 6.0)]:
        create_mesh_object(
            f"TL_Pole_{cx}_{cy}", m_tl_pole, col, parent=root, loc=(cx, cy, 2.25), mat=mat_pole
        )
        create_mesh_object(
            f"TL_Box_{cx}_{cy}", m_tl_box, col, parent=root, loc=(cx, cy, 4.2), mat=mat_pole
        )
        # 3색등 (빨간불 발광, 황/록색 소등)
        create_mesh_object(
            f"TL_Red_{cx}_{cy}", m_tl_lamp, col, parent=root, loc=(cx, cy - 0.18, 4.45), mat=mat_red_light
        )
        create_mesh_object(
            f"TL_Yel_{cx}_{cy}", m_tl_lamp, col, parent=root, loc=(cx, cy - 0.18, 4.20), mat=mat_off_light
        )
        create_mesh_object(
            f"TL_Grn_{cx}_{cy}", m_tl_lamp, col, parent=root, loc=(cx, cy - 0.18, 3.95), mat=mat_off_light
        )

    # 6. 정차된 차량들 (동/서/북 도로만, 차선 중앙 오프셋 2.75, 원점으로부터 9m 이상, 남쪽은 비움)
    m_car_body = mesh_cube("m_car_body", (1.8, 3.8, 0.7))
    m_car_top = mesh_cube("m_car_top", (1.6, 2.0, 0.55))
    m_head_lamp = mesh_cylinder("m_hl", radius=0.1, depth=0.04)
    m_tail_lamp = mesh_cylinder("m_tl", radius=0.09, depth=0.04)

    # 배치 후보 위치: (lane_x, lane_y, rot_z_deg)
    car_slots: List[Tuple[float, float, float]] = []
    # 북쪽 도로 (정차: 남향 혹은 북향)
    car_slots.extend([(2.75, 12.0, 180), (-2.75, 18.0, 0), (2.75, 24.0, 180), (-2.75, 30.0, 0)])
    # 동쪽 도로
    car_slots.extend([(14.0, 2.75, 90), (22.0, -2.75, 270), (30.0, 2.75, 90)])
    # 서쪽 도로
    car_slots.extend([(-14.0, -2.75, 270), (-22.0, 2.75, 90), (-30.0, -2.75, 270)])
    rng.shuffle(car_slots)

    car_colors = ["#234567", "#882222", "#e0e0e0", "#111111", "#445533", "#888899"]
    for i in range(min(num_cars, len(car_slots))):
        cx, cy, crot = car_slots[i]
        c_root = create_empty(f"Car_{i}_Root", parent=root, loc=(cx, cy, 0.15), col=col)
        c_root.rotation_euler = (0, 0, math.radians(crot))
        mat_car = make_material(f"Mat_Car_{i}", rng.choice(car_colors), roughness=0.3, metallic=0.7)
        create_mesh_object(f"Car_{i}_Body", m_car_body, col, parent=c_root, loc=(0, 0, 0.35), mat=mat_car)
        create_mesh_object(f"Car_{i}_Top", m_car_top, col, parent=c_root, loc=(0, -0.2, 0.90), mat=mat_asphalt)
        # 헤드라이트 (앞쪽: -Y 방향)
        create_mesh_object(
            f"Car_{i}_HL_L",
            m_head_lamp,
            col,
            parent=c_root,
            loc=(0.6, -1.9, 0.35),
            rot=(math.radians(90), 0, 0),
            mat=mat_headlight,
        )
        create_mesh_object(
            f"Car_{i}_HL_R",
            m_head_lamp,
            col,
            parent=c_root,
            loc=(-0.6, -1.9, 0.35),
            rot=(math.radians(90), 0, 0),
            mat=mat_headlight,
        )
        # 테일라이트 (뒤쪽: +Y 방향)
        create_mesh_object(
            f"Car_{i}_TL_L",
            m_tail_lamp,
            col,
            parent=c_root,
            loc=(0.6, 1.9, 0.38),
            rot=(math.radians(90), 0, 0),
            mat=mat_taillight,
        )
        create_mesh_object(
            f"Car_{i}_TL_R",
            m_tail_lamp,
            col,
            parent=c_root,
            loc=(-0.6, 1.9, 0.38),
            rot=(math.radians(90), 0, 0),
            mat=mat_taillight,
        )

    # 7. 교차로 상공 조명 (14m 상공, 크기 12, 베이스 2500W)
    l_soft_data = bpy.data.lights.new(name="Street_Sky_AreaLight", type="AREA")
    l_soft_data.shape = "SQUARE"
    l_soft_data.size = 12.0
    l_soft_data.energy = 2500.0
    l_soft_data.color = (0.85, 0.92, 1.0)
    l_soft_obj = bpy.data.objects.new(name="Street_Sky_AreaLight", object_data=l_soft_data)
    l_soft_obj.location = (offset_x, 0.0, 14.0)
    col.objects.link(l_soft_obj)
    lights.append((l_soft_obj, 2500.0))

    return lights


SETS: Dict[str, Callable[..., List[Tuple[bpy.types.Object, float]]]] = {
    "room": build_room,
    "street_night": build_street_night,
}


# -----------------------------------------------------------------------------
# 메인 파이프라인
# -----------------------------------------------------------------------------
def setup_render_engine(scene: bpy.types.Scene) -> None:
    """EEVEE 차세대 엔진 및 AgX/Filmic 뷰 트랜스폼 설정."""
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        try:
            scene.render.engine = "BLENDER_EEVEE"
        except Exception:
            pass

    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 32

    for vt in ("AgX", "Filmic", "Standard"):
        try:
            scene.view_settings.view_transform = vt
            break
        except Exception:
            continue


def main() -> None:
    """공익광고 패러디 씬 전체 조립 및 저장."""
    # 공장 초기화 빈 씬 생성
    bpy.ops.wm.read_factory_settings(use_empty=True)
    load_font()

    argv = sys.argv
    args_after = argv[argv.index("--") + 1 :] if "--" in argv else []
    timeline_path = (
        args_after[0]
        if len(args_after) > 0
        else os.path.join(SCRIPT_DIR, "timeline.example.json")
    )
    out_path = (
        args_after[1]
        if len(args_after) > 1
        else os.path.join(SCRIPT_DIR, "scene.blend")
    )

    if not os.path.isabs(timeline_path):
        timeline_path = os.path.abspath(timeline_path)
    if not os.path.isabs(out_path):
        out_path = os.path.abspath(out_path)

    with open(timeline_path, "r", encoding="utf-8") as f:
        timeline = json.load(f)

    fps = float(timeline.get("fps", 24))
    width = int(timeline.get("width", 1080))
    height = int(timeline.get("height", 1920))
    shots = timeline.get("shots", [])
    cast_dict = timeline.get("cast", {})

    scene = bpy.context.scene
    setup_render_engine(scene)
    scene.render.fps = round(fps)
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.frame_start = 1

    total_duration = max((s.get("end", 0.0) for s in shots), default=1.0)
    scene.frame_end = max(1, round(total_duration * fps))

    # 1. 단일 월드 및 단일 태양광 (Sun) 셋업
    world = bpy.data.worlds.new("PSA_World")
    world.use_nodes = True
    scene.world = world
    w_tree = world.node_tree
    w_bg = next((n for n in w_tree.nodes if n.type == "BACKGROUND"), None)
    if not w_bg:
        w_bg = w_tree.nodes.new("ShaderNodeBackground")

    sun_data = bpy.data.lights.new(name="PSA_Sun", type="SUN")
    sun_obj = bpy.data.objects.new(name="PSA_Sun", object_data=sun_data)
    scene.collection.objects.link(sun_obj)

    time_presets = {
        "day": {
            "sky": "#9cc7ee",
            "sky_str": 1.0,
            "sun": 4.0,
            "sun_col": (1.0, 1.0, 1.0),
            "sun_rot": (math.radians(45), math.radians(20), math.radians(30)),
        },
        "evening": {
            "sky": "#cfae98",
            "sky_str": 0.4,
            "sun": 1.0,
            "sun_col": (1.0, 0.84, 0.68),
            "sun_rot": (math.radians(60), 0.0, math.radians(40)),
        },
        "night": {
            "sky": "#05070f",
            "sky_str": 0.2,
            "sun": 0.1,
            "sun_col": (0.4, 0.55, 0.9),
            "sun_rot": (math.radians(80), 0.0, 0.0),
        },
    }

    # 2. 세트 빌드 및 재사용 매핑
    built_sets: Dict[str, Dict[str, Any]] = {}
    shot_map: Dict[str, Dict[str, Any]] = {s["id"]: s for s in shots}

    def resolve_set_source(shot_id: str) -> str:
        curr = shot_id
        visited = set()
        while curr in shot_map and curr not in visited:
            visited.add(curr)
            sh = shot_map[curr]
            if "set" in sh:
                return curr
            if "reuse_set" in sh:
                curr = sh["reuse_set"]
            else:
                break
        return curr

    built_set_index = 0
    for s in shots:
        shot_id = s["id"]
        if "set" in s:
            set_name = s["set"]
            if set_name not in SETS:
                raise ValueError(f"알 수 없는 세트 '{set_name}'. 허용: {sorted(list(SETS.keys()))}")
            offset_x = 400.0 * built_set_index
            built_set_index += 1
            col = bpy.data.collections.new(f"Set_{set_name}_{shot_id}")
            scene.collection.children.link(col)
            opts = s.get("set_options", {})
            rng = random.Random(opts.get("seed", 42))
            lamps = SETS[set_name](col, offset_x, opts, rng)
            built_sets[shot_id] = {
                "offset_x": offset_x,
                "lamps": lamps,
                "collection": col,
            }

    # 3. 각 샷별 카메라, 시간대/조명, 캐릭터, 소품 구성
    first_cam: Optional[bpy.types.Object] = None

    for s_idx, s in enumerate(shots):
        shot_id = s["id"]
        t_start = float(s.get("start", 0.0))
        t_end = float(s.get("end", 1.0))
        f_first = round(t_start * fps) + 1
        f_last = round(t_end * fps)

        source_shot_id = resolve_set_source(shot_id)
        if source_shot_id not in built_sets:
            raise ValueError(f"샷 '{shot_id}'의 유효한 세트를 찾을 수 없습니다.")

        set_info = built_sets[source_shot_id]
        world_offset_x = set_info["offset_x"]
        shot_col = bpy.data.collections.new(f"Shot_{shot_id}")
        scene.collection.children.link(shot_col)

        # 시간대 월드/태양광 키프레임 (CONSTANT)
        time_mode = s.get("time", "day")
        if time_mode not in time_presets:
            # 오타(예: "Night")를 조용히 낮으로 바꾸지 않고 멈춘다
            raise ValueError(f"샷 '{shot_id}': 알 수 없는 time '{time_mode}'. 허용: {sorted(time_presets)}")
        preset = time_presets[time_mode]
        sky_rgba = hex_to_linear(preset["sky"])
        w_bg.inputs["Color"].default_value = sky_rgba
        w_bg.inputs["Strength"].default_value = preset["sky_str"]
        key(w_bg.inputs["Color"], "default_value", f_first, "CONSTANT")
        key(w_bg.inputs["Strength"], "default_value", f_first, "CONSTANT")

        sun_data.energy = preset["sun"]
        sun_data.color = preset["sun_col"]
        sun_obj.rotation_euler = preset["sun_rot"]
        key(sun_data, "energy", f_first, "CONSTANT")
        key(sun_data, "color", f_first, "CONSTANT")
        key(sun_obj, "rotation_euler", f_first, "CONSTANT")

        # 세트 램프 디밍 배율 키프레임
        lamp_mult = float(s.get("lamps", 1.0))
        for l_obj, base_energy in set_info["lamps"]:
            l_data: Any = l_obj.data
            l_data.energy = base_energy * lamp_mult
            key(l_data, "energy", f_first, "CONSTANT")

        # 카메라 생성 및 트래킹
        cam_cfg = s.get("camera", {})
        cam_data = bpy.data.cameras.new(f"Cam_{shot_id}")
        cam_data.lens = float(cam_cfg.get("lens", 35))
        cam_data.clip_end = 3000.0
        cam_obj = bpy.data.objects.new(f"Cam_{shot_id}", object_data=cam_data)
        shot_col.objects.link(cam_obj)

        if first_cam is None:
            first_cam = cam_obj

        cam_from = cam_cfg.get("from", [0, -5, 2])
        cam_to = cam_cfg.get("to", cam_from)
        cam_obj.location = (cam_from[0] + world_offset_x, cam_from[1], cam_from[2])
        key(cam_obj, "location", f_first, "BEZIER")
        cam_obj.location = (cam_to[0] + world_offset_x, cam_to[1], cam_to[2])
        key(cam_obj, "location", f_last, "BEZIER")

        # 카메라 LookAt 타겟 Empty 및 제약조건
        look_from = cam_cfg.get("look_from", [0, 0, 1])
        look_to = cam_cfg.get("look_to", look_from)
        target_empty = create_empty(f"CamTarget_{shot_id}", col=shot_col)
        target_empty.location = (look_from[0] + world_offset_x, look_from[1], look_from[2])
        key(target_empty, "location", f_first, "BEZIER")
        target_empty.location = (look_to[0] + world_offset_x, look_to[1], look_to[2])
        key(target_empty, "location", f_last, "BEZIER")

        constraint = cam_obj.constraints.new(type="TRACK_TO")
        constraint.target = target_empty
        constraint.track_axis = "TRACK_NEGATIVE_Z"
        constraint.up_axis = "UP_Y"

        # 타임라인 마커 바인딩
        marker = scene.timeline_markers.new(shot_id, frame=f_first)
        marker.camera = cam_obj

        # 캐릭터 인스턴스 빌드
        actors = s.get("actors", [])
        for a_idx, act_cfg in enumerate(actors):
            who = act_cfg.get("who", "resident")
            if who not in cast_dict:
                raise ValueError(f"캐스트 명단에 '{who}'가 없습니다. 등록된 캐스트: {list(cast_dict.keys())}")
            actor_name = f"Shot_{shot_id}_{who}_{a_idx}"
            at_pos = tuple(act_cfg.get("at", [0.0, 0.0, 0.0]))
            heading = float(act_cfg.get("heading", 0.0))
            rig = build_character(
                actor_name,
                cast_dict[who],
                shot_col,
                f_first,
                f_last,
                world_offset_x,
                at_pos,
                heading,
            )

            # 액션 적용
            actions_list = act_cfg.get("actions", [])
            for a_item in actions_list:
                do_name = a_item.get("do", "idle")
                if do_name not in ACTIONS:
                    raise ValueError(f"알 수 없는 액션 '{do_name}'. 허용: {sorted(list(ACTIONS.keys()))}")
                t0 = float(a_item.get("t0", 0.0))
                # t1 을 빼면 샷 끝까지(복셀 팩과 같은 규칙)
                t1 = float(a_item.get("t1", t_end - t_start))
                act_f0 = f_first + round(t0 * fps)
                act_f1 = f_first + round(t1 * fps)
                ACTIONS[do_name](rig, act_f0, act_f1, fps, **a_item)

        # 소품(Props) 빌드
        props_list = s.get("props", [])
        for p_idx, p_cfg in enumerate(props_list):
            kind = p_cfg.get("kind", "sign")
            if kind not in PROPS:
                raise ValueError(f"알 수 없는 소품 '{kind}'. 허용: {sorted(list(PROPS.keys()))}")
            # 소품도 배우처럼 샷 구간에서만 보이게 Park 아래에 둔다(좌표는 세트 로컬 그대로)
            prop_park = create_empty(f"Shot_{shot_id}_Prop_{p_idx}_Park", col=shot_col)
            key_park(prop_park, world_offset_x, f_first, f_last)
            prop_obj = PROPS[kind](shot_col, dict(p_cfg), f_first, fps)
            if prop_obj is not None:
                prop_obj.parent = prop_park

    # 첫 샷 카메라를 씬 기본 카메라로 설정
    if first_cam:
        scene.camera = first_cam

    # 완료 출력 및 블렌더 파일 저장
    print(f"SCENE_OK frames={scene.frame_end} shots={len(shots)}")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_path)


if __name__ == "__main__":
    main()
