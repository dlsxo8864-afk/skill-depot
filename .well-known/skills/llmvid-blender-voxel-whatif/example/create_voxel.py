# -*- coding: utf-8 -*-
"""
create_voxel.py

타임라인 JSON 명세를 읽어 복셀(블록형) 숏폼 3D 씬을 자동 생성하고 .blend 파일로 저장하는 스크립트.
Blender 4.5 LTS 및 5.x 호환 (action.fcurves 미사용, bpy.ops 메시 루프 호출 최소화, from_pydata 일괄 생성).
"""

import sys
import os
import math
import json
import random
from typing import Dict, List, Tuple, Any, Optional

import bpy
import mathutils

# -----------------------------------------------------------------------------
# 유틸리티: 색상 변환 및 키프레임 보간
# -----------------------------------------------------------------------------

def hex_to_linear_rgb(hex_str: str) -> Tuple[float, float, float, float]:
    """16진수 색상 코드(#RRGGBB)를 선형(Linear) sRGB 튜플 (R, G, B, 1.0)로 변환."""
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) != 6:
        return (1.0, 1.0, 1.0, 1.0)
    r = int(hex_clean[0:2], 16) / 255.0
    g = int(hex_clean[2:4], 16) / 255.0
    b = int(hex_clean[4:6], 16) / 255.0

    def srgb_to_linear(c: float) -> float:
        if c <= 0.04045:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)


def fcurves_of(id_data: Any) -> List[Any]:
    """ID 에 붙은 액션의 F-커브 목록. 4.x(action.fcurves)와 5.x(레이어·스트립·채널백) 둘 다 읽는다."""
    anim = getattr(id_data, "animation_data", None)
    action = anim.action if anim else None
    if action is None:
        return []
    legacy = getattr(action, "fcurves", None)
    if legacy is not None:
        return list(legacy)
    curves: List[Any] = []
    for layer in action.layers:
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []):
                curves.extend(bag.fcurves)
    return curves


def key(target: Any, path: str, frame: float, interp: str = "BEZIER", index: int = -1) -> None:
    """
    키프레임을 넣고 그 키의 보간을 직접 정한다.
    (블렌더 5.x 는 환경 설정의 '새 키 보간'을 keyframe_insert 에 적용하지 않는다 — 실측)
    """
    if index >= 0:
        target.keyframe_insert(data_path=path, index=index, frame=frame)
    else:
        target.keyframe_insert(data_path=path, frame=frame)

    try:
        rna_path = target.path_from_id(path)
    except Exception:
        rna_path = path
    for curve in fcurves_of(target.id_data):
        if curve.data_path != rna_path:
            continue
        if index >= 0 and curve.array_index != index:
            continue
        for point in curve.keyframe_points:
            if abs(point.co[0] - frame) < 0.5:
                point.interpolation = interp


# -----------------------------------------------------------------------------
# 재질(Material) 및 텍스처 생성 헬퍼
# -----------------------------------------------------------------------------

def get_or_create_material(name: str, color_hex: str, roughness: float = 0.8, emission_strength: float = 0.0) -> bpy.types.Material:
    """단색 Principled BSDF 재질 생성 (기존 재질 재사용)"""
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    rgba = hex_to_linear_rgb(color_hex)

    # 베이스 컬러 설정
    if "Base Color" in bsdf.inputs:
        bsdf.inputs["Base Color"].default_value = rgba
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = roughness

    # 발광(Emission) 소켓 호환 처리
    if emission_strength > 0.0:
        emission_socket = None
        if "Emission Color" in bsdf.inputs:
            emission_socket = bsdf.inputs["Emission Color"]
        elif "Emission" in bsdf.inputs:
            emission_socket = bsdf.inputs["Emission"]
        if emission_socket is not None:
            emission_socket.default_value = rgba
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission_strength

    out_node = nodes.new(type="ShaderNodeOutputMaterial")
    out_node.location = (300, 0)
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])
    return mat


def create_pixel_texture_material(name: str, width: int, height: int, pixels: List[float], roughness: float = 0.9) -> bpy.types.Material:
    """Closest 필터링 픽셀 텍스처를 적용한 재질 생성"""
    img = bpy.data.images.new(name=f"Img_{name}", width=width, height=height, alpha=True)
    img.pixels = pixels
    img.pack()

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    tex_node = nodes.new(type="ShaderNodeTexImage")
    tex_node.image = img
    tex_node.interpolation = "Closest"
    tex_node.location = (-300, 0)

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = roughness

    out_node = nodes.new(type="ShaderNodeOutputMaterial")
    out_node.location = (300, 0)

    mat.node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])
    return mat


# -----------------------------------------------------------------------------
# 메시 생성 헬퍼 (from_pydata 일괄 처리)
# -----------------------------------------------------------------------------

def make_box_mesh(name: str, size: Tuple[float, float, float], center: Tuple[float, float, float] = (0.0, 0.0, 0.0)) -> bpy.types.Mesh:
    """기본 박스 메시 및 UV 레이어 생성"""
    dx, dy, dz = size[0] / 2.0, size[1] / 2.0, size[2] / 2.0
    cx, cy, cz = center

    verts = [
        (cx - dx, cy - dy, cz - dz),
        (cx + dx, cy - dy, cz - dz),
        (cx + dx, cy + dy, cz - dz),
        (cx - dx, cy + dy, cz - dz),
        (cx - dx, cy - dy, cz + dz),
        (cx + dx, cy - dy, cz + dz),
        (cx + dx, cy + dy, cz + dz),
        (cx - dx, cy + dy, cz + dz),
    ]
    faces = [
        (0, 1, 2, 3),  # 바닥 (-Z)
        (4, 7, 6, 5),  # 윗면 (+Z)
        (0, 4, 5, 1),  # 앞면 (-Y)
        (1, 5, 6, 2),  # 우측 (+X)
        (2, 6, 7, 3),  # 뒷면 (+Y)
        (3, 7, 4, 0),  # 좌측 (-X)
    ]

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)

    # 각 페이스별 풀 0..1 UV 매핑 생성
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uv_data = uv_layer.data
    loop_idx = 0
    for _ in faces:
        uv_data[loop_idx + 0].uv = (0.0, 0.0)
        uv_data[loop_idx + 1].uv = (1.0, 0.0)
        uv_data[loop_idx + 2].uv = (1.0, 1.0)
        uv_data[loop_idx + 3].uv = (0.0, 1.0)
        loop_idx += 4

    mesh.update()
    return mesh


def make_box_object(name: str, size: Tuple[float, float, float], center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                    material: Optional[bpy.types.Material] = None, collection: Optional[bpy.types.Collection] = None) -> bpy.types.Object:
    """박스 메시를 가진 오브젝트를 생성하고 컬렉션에 링크"""
    mesh = make_box_mesh(f"Mesh_{name}", size, center)
    if material:
        mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    if collection:
        collection.objects.link(obj)
    return obj


def make_plane_mesh(name: str, size_x: float, size_y: float, center: Tuple[float, float, float] = (0.0, 0.0, 0.0)) -> bpy.types.Mesh:
    """XY 평면 메시 및 풀 UV 레이어 생성"""
    dx, dy = size_x / 2.0, size_y / 2.0
    cx, cy, cz = center
    verts = [
        (cx - dx, cy - dy, cz),
        (cx + dx, cy - dy, cz),
        (cx + dx, cy + dy, cz),
        (cx - dx, cy + dy, cz),
    ]
    faces = [(0, 1, 2, 3)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uv_data = uv_layer.data
    uv_data[0].uv = (0.0, 0.0)
    uv_data[1].uv = (1.0, 0.0)
    uv_data[2].uv = (1.0, 1.0)
    uv_data[3].uv = (0.0, 1.0)
    mesh.update()
    return mesh


def combine_boxes_to_single_mesh(name: str, boxes: List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]]) -> bpy.types.Mesh:
    """
    다수의 박스 리스트 ((size_xyz, center_xyz), ...)를 단일 메시로 병합
    """
    all_verts = []
    all_faces = []
    vert_offset = 0

    for size, center in boxes:
        dx, dy, dz = size[0] / 2.0, size[1] / 2.0, size[2] / 2.0
        cx, cy, cz = center
        b_verts = [
            (cx - dx, cy - dy, cz - dz),
            (cx + dx, cy - dy, cz - dz),
            (cx + dx, cy + dy, cz - dz),
            (cx - dx, cy + dy, cz - dz),
            (cx - dx, cy - dy, cz + dz),
            (cx + dx, cy - dy, cz + dz),
            (cx + dx, cy + dy, cz + dz),
            (cx - dx, cy + dy, cz + dz),
        ]
        b_faces = [
            (vert_offset + 0, vert_offset + 1, vert_offset + 2, vert_offset + 3),
            (vert_offset + 4, vert_offset + 7, vert_offset + 6, vert_offset + 5),
            (vert_offset + 0, vert_offset + 4, vert_offset + 5, vert_offset + 1),
            (vert_offset + 1, vert_offset + 5, vert_offset + 6, vert_offset + 2),
            (vert_offset + 2, vert_offset + 6, vert_offset + 7, vert_offset + 3),
            (vert_offset + 3, vert_offset + 7, vert_offset + 4, vert_offset + 0),
        ]
        all_verts.extend(b_verts)
        all_faces.extend(b_faces)
        vert_offset += 8

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(all_verts, [], all_faces)
    mesh.update()
    return mesh


# -----------------------------------------------------------------------------
# 캐릭터 얼굴 텍스처 생성기 (8x8 픽셀)
# -----------------------------------------------------------------------------

VALID_FACES = {"smile", "neutral", "surprised", "sleepy"}

def generate_face_image_texture(name: str, skin_hex: str, hair_hex: str, face_type: str) -> bpy.types.Material:
    """
    8x8 픽셀 얼굴 텍스처를 동적으로 생성하여 재질 반환
    y=7 (상단): 머리카락 색상
    y=4: 눈 (좌우 동공 및 흰자위)
    y=2: 표정별 입 형태
    """
    if face_type not in VALID_FACES:
        raise ValueError(f"알 수 없는 face 타입: '{face_type}'. 유효한 목록: {list(VALID_FACES)}")

    skin_rgb = hex_to_linear_rgb(skin_hex)
    hair_rgb = hex_to_linear_rgb(hair_hex)
    eye_dark = (0.05, 0.05, 0.06, 1.0)
    eye_white = (0.95, 0.95, 0.95, 1.0)
    mouth_color = (0.45, 0.12, 0.12, 1.0)

    # 8x8 버퍼 초기화 (y: 0~7, x: 0~7)
    grid = [[skin_rgb for _ in range(8)] for _ in range(8)]

    # 1. 상단 헤어라인 (y=7, 6 일부)
    for x in range(8):
        grid[7][x] = hair_rgb
    grid[6][0] = hair_rgb
    grid[6][7] = hair_rgb

    # 2. 눈 배치 (y=4, x=2, 5)
    grid[4][1] = eye_white
    grid[4][2] = eye_dark
    grid[4][5] = eye_dark
    grid[4][6] = eye_white

    # 3. 표정별 입 및 눈 변형
    if face_type == "smile":
        grid[2][2] = mouth_color
        grid[2][3] = mouth_color
        grid[2][4] = mouth_color
        grid[2][5] = mouth_color
        grid[3][1] = mouth_color
        grid[3][6] = mouth_color
    elif face_type == "neutral":
        grid[2][3] = mouth_color
        grid[2][4] = mouth_color
    elif face_type == "surprised":
        grid[2][3] = mouth_color
        grid[2][4] = mouth_color
        grid[1][3] = mouth_color
        grid[1][4] = mouth_color
    elif face_type == "sleepy":
        # 감은 눈 (실눈 형태)
        grid[4][1] = eye_dark
        grid[4][2] = eye_dark
        grid[4][5] = eye_dark
        grid[4][6] = eye_dark
        grid[2][3] = mouth_color
        grid[2][4] = mouth_color

    pixels = []
    for row in grid:
        for px in row:
            pixels.extend(px)

    return create_pixel_texture_material(f"Mat_Face_{name}", 8, 8, pixels, roughness=0.8)


# -----------------------------------------------------------------------------
# 캐릭터 모델링 및 계층 구조 구축
# -----------------------------------------------------------------------------

VALID_HAIR_STYLES = {"short", "long", "bald", "cap"}

def build_character_rig(actor_id: str, cast_spec: Dict[str, Any], collection: bpy.types.Collection) -> Dict[str, bpy.types.Object]:
    """
    캐릭터 계층 구조 생성:
    Park (빈 오브젝트, 쇼트 외 z=-2000 숨김)
      -> Root (위치 및 방향 이동)
           -> Body (상체 상하 바운스/앉기 오프셋)
                -> Torso, Head(neck pivot), Arms(shoulder pivot), Legs(hip pivot)
    """
    skin_hex = cast_spec.get("skin", "#f1c9a2")
    hair_hex = cast_spec.get("hair", "#3a2a1f")
    top_hex = cast_spec.get("top", "#f2c12e")
    bottom_hex = cast_spec.get("bottom", "#34435e")
    shoes_hex = cast_spec.get("shoes", "#333333")
    face_type = cast_spec.get("face", "smile")
    hair_style = cast_spec.get("hair_style", "short")
    extras = cast_spec.get("extras", [])
    unknown_extras = [e for e in extras if e not in ("glasses", "headset")]
    if unknown_extras:
        # 오타나 아직 없는 소품(scarf 등)을 조용히 빼지 않고 멈춘다
        raise ValueError(f"알 수 없는 extras: {unknown_extras}. 유효한 목록: ['glasses', 'headset']")

    if hair_style not in VALID_HAIR_STYLES:
        raise ValueError(f"알 수 없는 hair_style: '{hair_style}'. 유효한 목록: {list(VALID_HAIR_STYLES)}")

    # 재질 캐싱
    mat_skin = get_or_create_material(f"Mat_Skin_{skin_hex}", skin_hex)
    mat_hair = get_or_create_material(f"Mat_Hair_{hair_hex}", hair_hex)
    mat_top = get_or_create_material(f"Mat_Top_{top_hex}", top_hex)
    mat_bottom = get_or_create_material(f"Mat_Bottom_{bottom_hex}", bottom_hex)
    mat_shoes = get_or_create_material(f"Mat_Shoes_{shoes_hex}", shoes_hex)
    # 얼굴 그림 윗줄은 앞머리라 머리색으로 칠한다. 대머리(bald)는 앞머리도 피부색으로 칠한다
    fringe_hex = skin_hex if hair_style == "bald" else hair_hex
    mat_face = generate_face_image_texture(f"{actor_id}_{face_type}", skin_hex, fringe_hex, face_type)

    def make_empty(name: str, parent: Optional[bpy.types.Object] = None, loc: Tuple[float, float, float] = (0.0, 0.0, 0.0)) -> bpy.types.Object:
        emp = bpy.data.objects.new(name, None)
        emp.empty_display_type = "PLAIN_AXES"
        emp.empty_display_size = 0.2
        emp.location = loc
        if parent:
            emp.parent = parent
        collection.objects.link(emp)
        return emp

    park_emp = make_empty(f"{actor_id}_Park")
    root_emp = make_empty(f"{actor_id}_Root", parent=park_emp)
    body_emp = make_empty(f"{actor_id}_Body", parent=root_emp)

    # 1. 몸통 (Torso: 0.5 x 0.26 x 0.66, 중심 z = 0.72 + 0.33 = 1.05)
    torso_obj = make_box_object(f"{actor_id}_Torso", (0.5, 0.26, 0.66), (0.0, 0.0, 1.05), mat_top, collection)
    torso_obj.parent = body_emp

    # 2. 머리 피벗 (neck at z = 1.38)
    neck_emp = make_empty(f"{actor_id}_Neck", parent=body_emp, loc=(0.0, 0.0, 1.38))
    # Head cube (0.5 cube, neck 로컬 z = 0.25)
    head_obj = make_box_object(f"{actor_id}_Head", (0.5, 0.5, 0.5), (0.0, 0.0, 0.25), mat_skin, collection)
    head_obj.parent = neck_emp

    # Face plane (-Y 쪽 0.003 앞, z = 0.25, 0.5 x 0.5 plane 수직 세우기)
    # 평면 메시 만들고 X축 회전 90도
    face_mesh = make_plane_mesh(f"{actor_id}_FaceMesh", 0.5, 0.5, (0.0, 0.0, 0.0))
    face_mesh.materials.append(mat_face)
    face_obj = bpy.data.objects.new(f"{actor_id}_FacePlane", face_mesh)
    face_obj.parent = neck_emp
    face_obj.location = (0.0, -0.253, 0.25)
    face_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    collection.objects.link(face_obj)

    # 헤어 스타일 구축
    if hair_style == "short":
        h_top = make_box_object(f"{actor_id}_HairTop", (0.52, 0.52, 0.12), (0.0, 0.0, 0.51), mat_hair, collection)
        h_top.parent = neck_emp
        h_back = make_box_object(f"{actor_id}_HairBack", (0.52, 0.12, 0.36), (0.0, 0.21, 0.31), mat_hair, collection)
        h_back.parent = neck_emp
    elif hair_style == "long":
        h_top = make_box_object(f"{actor_id}_HairTop", (0.52, 0.52, 0.12), (0.0, 0.0, 0.51), mat_hair, collection)
        h_top.parent = neck_emp
        h_back = make_box_object(f"{actor_id}_HairBack", (0.52, 0.14, 0.75), (0.0, 0.22, 0.15), mat_hair, collection)
        h_back.parent = neck_emp
    elif hair_style == "cap":
        h_cap = make_box_object(f"{actor_id}_CapTop", (0.52, 0.52, 0.16), (0.0, 0.0, 0.49), mat_top, collection)
        h_cap.parent = neck_emp
        h_visor = make_box_object(f"{actor_id}_CapVisor", (0.48, 0.25, 0.04), (0.0, -0.34, 0.42), mat_top, collection)
        h_visor.parent = neck_emp

    # 악세사리 (extras)
    for extra in extras:
        if extra == "glasses":
            g_frame = make_box_object(f"{actor_id}_Glasses", (0.46, 0.04, 0.1), (0.0, -0.26, 0.28),
                                      get_or_create_material("Mat_Glasses", "#111111"), collection)
            g_frame.parent = neck_emp
        elif extra == "headset":
            hs = make_box_object(f"{actor_id}_Headset", (0.56, 0.1, 0.54), (0.0, 0.0, 0.28),
                                get_or_create_material("Mat_Headset", "#222222"), collection)
            hs.parent = neck_emp

    # 3. 팔 (Arms: 0.2 x 0.2 x 0.66, 어깨 피벗 z = 1.35, X = +-0.37)
    # 하단 0.14는 손(skin), 상단 0.52는 소매(top)
    def make_arm(side: str, sign: float) -> Tuple[bpy.types.Object, bpy.types.Object]:
        shoulder = make_empty(f"{actor_id}_Shoulder_{side}", parent=body_emp, loc=(sign * 0.36, 0.0, 1.35))
        # 상완
        sleeve = make_box_object(f"{actor_id}_Sleeve_{side}", (0.2, 0.2, 0.52), (0.0, 0.0, -0.26), mat_top, collection)
        sleeve.parent = shoulder
        # 손
        hand = make_box_object(f"{actor_id}_Hand_{side}", (0.18, 0.18, 0.14), (0.0, 0.0, -0.59), mat_skin, collection)
        hand.parent = shoulder
        return shoulder, sleeve

    shoulder_L, _ = make_arm("L", -1.0)
    shoulder_R, _ = make_arm("R", 1.0)

    # 4. 다리 (Legs: 0.24 x 0.24 x 0.72, 골반 피벗 z = 0.72, X = +-0.13)
    # 하단 0.12는 신발(shoes), 상단 0.60은 바지(bottom)
    def make_leg(side: str, sign: float) -> Tuple[bpy.types.Object, bpy.types.Object]:
        hip = make_empty(f"{actor_id}_Hip_{side}", parent=body_emp, loc=(sign * 0.13, 0.0, 0.72))
        pants = make_box_object(f"{actor_id}_Pants_{side}", (0.23, 0.23, 0.60), (0.0, 0.0, -0.30), mat_bottom, collection)
        pants.parent = hip
        shoe = make_box_object(f"{actor_id}_Shoe_{side}", (0.24, 0.25, 0.12), (0.0, -0.01, -0.66), mat_shoes, collection)
        shoe.parent = hip
        return hip, pants

    hip_L, _ = make_leg("L", -1.0)
    hip_R, _ = make_leg("R", 1.0)

    return {
        "park": park_emp,
        "root": root_emp,
        "body": body_emp,
        "neck": neck_emp,
        "shoulder_L": shoulder_L,
        "shoulder_R": shoulder_R,
        "hip_L": hip_L,
        "hip_R": hip_R,
    }


# -----------------------------------------------------------------------------
# 액션 애니메이션 핸들러 (ACTIONS 레지스트리)
# -----------------------------------------------------------------------------

RAMP_FRAMES = 6  # 자세가 바뀌는 데 걸리는 프레임(24fps 에서 0.25초)


def _hold_pose(obj: bpy.types.Object, path: str, pose: Tuple[float, float, float], f0: float, f1: float,
               act: Dict[str, Any], interp: str = "BEZIER") -> None:
    """t0 부터 t1 까지 pose 를 유지한다(t1 뒤에도 그대로).
    채널에 키가 하나뿐이면 블렌더는 그 값을 샷 처음부터 쓴다. 그래서 t0 가 0 보다 크면
    t0 에 기본 자세(0) 키를 먼저 넣고 RAMP_FRAMES 동안 바꾼다. t0 가 0 이면 샷 처음부터 그 자세다."""
    f_on = f0
    if float(act.get("t0", 0.0)) > 0.0 and f1 > f0:
        setattr(obj, path, (0.0, 0.0, 0.0))
        key(obj, path, f0, interp="BEZIER")
        f_on = min(f0 + RAMP_FRAMES, f1)
    setattr(obj, path, pose)
    key(obj, path, f_on, interp=interp)
    key(obj, path, f1, interp=interp)


def _arm_side(act: Dict[str, Any]) -> str:
    """wave·point 가 쓸 팔. R(기본)은 인물이 카메라를 볼 때(heading 0) 화면 오른쪽 팔, L 은 화면 왼쪽 팔.
    카메라 쪽 팔을 들면 얼굴을 가리고 그늘이 져 검은 덩어리로 보이므로, 옆모습 컷에서는 카메라 반대쪽 팔을 고른다."""
    side = str(act.get("arm", "R")).upper()
    if side not in ("R", "L"):
        raise ValueError(f"알 수 없는 arm: '{act.get('arm')}'. 유효 목록: ['R', 'L']")
    return side


def action_idle(rig: Dict[str, bpy.types.Object], act: Dict[str, Any], f0: float, f1: float, fps: float) -> None:
    """아이들 액션: 부드러운 상하 바운스 및 미세한 머리 회전"""
    frames = range(int(f0), int(f1) + 1, 4)
    for fr in frames:
        t = (fr - f0) / fps
        bob = math.sin(t * 3.0) * 0.02
        rig["body"].location = (0.0, 0.0, bob)
        key(rig["body"], "location", fr, interp="LINEAR")
        head_yaw = math.sin(t * 1.5) * math.radians(4.0)
        rig["neck"].rotation_euler = (0.0, 0.0, head_yaw)
        key(rig["neck"], "rotation_euler", fr, interp="LINEAR")


def action_walk(rig: Dict[str, bpy.types.Object], act: Dict[str, Any], f0: float, f1: float, fps: float) -> None:
    """걷기 액션: 루트 이동 및 팔/다리 전후 스윙"""
    to_xy = act.get("to", [0.0, 0.0])
    # 루트 시작 위치 및 끝 위치
    start_x, start_y = rig["root"].location.x, rig["root"].location.y
    target_x, target_y = float(act.get("_offset_x", 0.0)) + float(to_xy[0]), float(to_xy[1])

    # 이동 방향 각도 계산 (-Y가 0도)
    dx = target_x - start_x
    dy = target_y - start_y
    if math.hypot(dx, dy) > 0.01:
        walk_heading = math.atan2(dx, -dy)
        rig["root"].rotation_euler = (0.0, 0.0, walk_heading)
        key(rig["root"], "rotation_euler", f0, interp="CONSTANT")

    rig["root"].location.x = start_x
    rig["root"].location.y = start_y
    key(rig["root"], "location", f0, interp="LINEAR", index=0)
    key(rig["root"], "location", f0, interp="LINEAR", index=1)

    rig["root"].location.x = target_x
    rig["root"].location.y = target_y
    key(rig["root"], "location", f1, interp="LINEAR", index=0)
    key(rig["root"], "location", f1, interp="LINEAR", index=1)

    # 팔다리 2프레임 단위 스윙 (초당 약 1.8보)
    swing_max = math.radians(35.0)
    step_rate = 1.8 * 2.0 * math.pi

    for fr in range(int(f0), int(f1) + 1, 2):
        t = (fr - f0) / fps
        angle = math.sin(t * step_rate) * swing_max
        rig["hip_L"].rotation_euler = (angle, 0.0, 0.0)
        rig["hip_R"].rotation_euler = (-angle, 0.0, 0.0)
        rig["shoulder_L"].rotation_euler = (-angle * 0.8, 0.0, 0.0)
        rig["shoulder_R"].rotation_euler = (angle * 0.8, 0.0, 0.0)
        for part in ["hip_L", "hip_R", "shoulder_L", "shoulder_R"]:
            key(rig[part], "rotation_euler", fr, interp="LINEAR")

    # 종료 시점 원위치 복귀
    for part in ["hip_L", "hip_R", "shoulder_L", "shoulder_R"]:
        rig[part].rotation_euler = (0.0, 0.0, 0.0)
        key(rig[part], "rotation_euler", f1, interp="LINEAR")


def action_sit(rig: Dict[str, bpy.types.Object], act: Dict[str, Any], f0: float, f1: float, fps: float) -> None:
    """앉기 액션: 골반 회전 90도 앞으로 꺾고 몸통 높이를 의자 높이(0.5m)로 하강.
    t0 가 0 이면 샷 처음부터 앉아 있고, 0 보다 크면 t0 에서 앉는다. 일어나는 동작은 없다."""
    interp = "CONSTANT" if float(act.get("t0", 0.0)) <= 0.0 else "BEZIER"
    # 골반 90도 전방 회전 (-90도 in local X)
    _hold_pose(rig["hip_L"], "rotation_euler", (math.radians(-90.0), 0.0, 0.0), f0, f1, act, interp)
    _hold_pose(rig["hip_R"], "rotation_euler", (math.radians(-90.0), 0.0, 0.0), f0, f1, act, interp)
    # 기본 서있을 때 엉덩이 z=0.72. 의자 시트 z=0.5 -> delta = -0.22
    _hold_pose(rig["body"], "location", (0.0, 0.0, -0.22), f0, f1, act, interp)


def action_nod(rig: Dict[str, bpy.types.Object], act: Dict[str, Any], f0: float, f1: float, fps: float) -> None:
    """고개 끄덕이기 (X축 회전)"""
    for fr in range(int(f0), int(f1) + 1, 2):
        t = (fr - f0) / fps
        pitch = math.sin(t * 7.0) * math.radians(16.0)
        rig["neck"].rotation_euler = (pitch, 0.0, 0.0)
        key(rig["neck"], "rotation_euler", fr, interp="LINEAR")
    rig["neck"].rotation_euler = (0.0, 0.0, 0.0)
    key(rig["neck"], "rotation_euler", f1, interp="LINEAR")


def action_shake(rig: Dict[str, bpy.types.Object], act: Dict[str, Any], f0: float, f1: float, fps: float) -> None:
    """도리도리 (Z축 회전)"""
    for fr in range(int(f0), int(f1) + 1, 2):
        t = (fr - f0) / fps
        yaw = math.sin(t * 9.0) * math.radians(22.0)
        rig["neck"].rotation_euler = (0.0, 0.0, yaw)
        key(rig["neck"], "rotation_euler", fr, interp="LINEAR")
    rig["neck"].rotation_euler = (0.0, 0.0, 0.0)
    key(rig["neck"], "rotation_euler", f1, interp="LINEAR")


def action_wave(rig: Dict[str, bpy.types.Object], act: Dict[str, Any], f0: float, f1: float, fps: float) -> None:
    """손 흔들기: 한 팔(arm, 기본 R)을 150도 들어올리고 좌우 흔들기.
    t0 에서 내린 팔로 시작해 4프레임 동안 들고, 끝나기 4프레임 전부터 내린다(그 전에는 팔이 내려가 있다)."""
    side = _arm_side(act)
    sh = rig["shoulder_R"] if side == "R" else rig["shoulder_L"]
    lift = math.radians(-150.0) if side == "R" else math.radians(150.0)
    sign = 1.0 if side == "R" else -1.0
    sh.rotation_euler = (0.0, 0.0, 0.0)
    key(sh, "rotation_euler", f0, interp="LINEAR")
    up = min(f0 + 4, f1)
    down = max(f1 - 4, up)
    for fr in range(int(up), int(down) + 1, 2):
        t = (fr - f0) / fps
        wag = math.sin(t * 8.0) * math.radians(15.0)
        sh.rotation_euler = (0.0, lift, sign * wag)
        key(sh, "rotation_euler", fr, interp="LINEAR")
    sh.rotation_euler = (0.0, 0.0, 0.0)
    key(sh, "rotation_euler", f1, interp="LINEAR")


def action_cheer(rig: Dict[str, bpy.types.Object], act: Dict[str, Any], f0: float, f1: float, fps: float) -> None:
    """환호: 양팔 160도 들기 및 2Hz 점프 바운스 (0.12m).
    팔은 t0 에서 내린 채 시작해 4프레임 동안 들고, 끝나기 4프레임 전부터 내린다."""
    for side in ("shoulder_L", "shoulder_R"):
        rig[side].rotation_euler = (0.0, 0.0, 0.0)
        key(rig[side], "rotation_euler", f0, interp="LINEAR")
    up = min(f0 + 4, f1)
    down = max(f1 - 4, up)
    for fr in range(int(f0), int(f1) + 1, 2):
        t = (fr - f0) / fps
        jump = abs(math.sin(t * 2.0 * math.pi * 2.0)) * 0.12
        rig["body"].location = (0.0, 0.0, jump)
        key(rig["body"], "location", fr, interp="LINEAR")
        if up <= fr <= down:
            rig["shoulder_L"].rotation_euler = (0.0, math.radians(160.0), math.sin(t * 8.0) * 0.1)
            rig["shoulder_R"].rotation_euler = (0.0, math.radians(-160.0), -math.sin(t * 8.0) * 0.1)
            key(rig["shoulder_L"], "rotation_euler", fr, interp="LINEAR")
            key(rig["shoulder_R"], "rotation_euler", fr, interp="LINEAR")
    rig["body"].location = (0.0, 0.0, 0.0)
    key(rig["body"], "location", f1, interp="LINEAR")
    rig["shoulder_L"].rotation_euler = (0.0, 0.0, 0.0)
    rig["shoulder_R"].rotation_euler = (0.0, 0.0, 0.0)
    key(rig["shoulder_L"], "rotation_euler", f1, interp="LINEAR")
    key(rig["shoulder_R"], "rotation_euler", f1, interp="LINEAR")


def action_turn_head(rig: Dict[str, bpy.types.Object], act: Dict[str, Any], f0: float, f1: float, fps: float) -> None:
    """머리 방향 회전: t0 부터 angle 도 돌린 채 유지(+는 위에서 볼 때 반시계 = 인물 기준 왼쪽)"""
    angle = float(act.get("angle", 30.0))
    _hold_pose(rig["neck"], "rotation_euler", (0.0, 0.0, math.radians(angle)), f0, f1, act)


def action_point(rig: Dict[str, bpy.types.Object], act: Dict[str, Any], f0: float, f1: float, fps: float) -> None:
    """한 팔(arm, 기본 R) 앞으로 뻗기: t0 부터 뻗은 채 유지"""
    sh = rig["shoulder_R"] if _arm_side(act) == "R" else rig["shoulder_L"]
    _hold_pose(sh, "rotation_euler", (math.radians(-90.0), 0.0, 0.0), f0, f1, act)


ACTIONS = {
    "idle": action_idle,
    "walk": action_walk,
    "sit": action_sit,
    "nod": action_nod,
    "shake": action_shake,
    "wave": action_wave,
    "cheer": action_cheer,
    "turn_head": action_turn_head,
    "point": action_point,
}


# -----------------------------------------------------------------------------
# 세트(SET) 빌더 레지스트리
# -----------------------------------------------------------------------------

def build_set_park(col: bpy.types.Collection, offset_x: float, options: Dict[str, Any], rng: random.Random) -> List[Tuple[bpy.types.Object, float]]:
    """
    공원(Park) 세트 빌더:
    - 60x60 잔디 지면 (120x120 픽셀 지터 텍스처)
    - |y|<1 모래길 및 가로등
    - 지정 영역 나무 배치 및 가을 낙엽 파티클 메시
    """
    lights = []
    season = options.get("season", "autumn")
    if season not in ("spring", "summer", "autumn", "winter"):
        # 오타를 조용히 가을로 바꾸지 않고 멈춘다
        raise ValueError(f"알 수 없는 season: '{season}'. 유효 목록: ['spring', 'summer', 'autumn', 'winter']")
    num_trees = options.get("trees", 16)

    # 1. 잔디 지면 텍스처 (120x120)
    # 가을: 황록색/갈색조, 봄/여름: 밝은 초록, 겨울: 서리빛 옥색
    palette = {
        "spring": ["#5aa846", "#6cc452", "#78cf5d", "#4b9138"],
        "summer": ["#328230", "#3c963a", "#286b26", "#45a842"],
        "autumn": ["#8c8a3e", "#9c9945", "#7a7731", "#a8853b"],
        "winter": ["#8fa196", "#9db3a6", "#7d8c82", "#b0c4b8"],
    }.get(season, ["#8c8a3e", "#9c9945", "#7a7731", "#a8853b"])
    pal_linear = [hex_to_linear_rgb(c) for c in palette]

    grass_pixels = []
    for _ in range(120 * 120):
        base = rng.choice(pal_linear)
        jitter = rng.uniform(-0.03, 0.03)
        grass_pixels.extend([max(0.0, base[0] + jitter), max(0.0, base[1] + jitter), max(0.0, base[2] + jitter), 1.0])

    mat_grass = create_pixel_texture_material(f"Mat_Grass_{season}_{offset_x}", 120, 120, grass_pixels, roughness=0.9)
    ground_mesh = make_plane_mesh("Park_GroundMesh", 60.0, 60.0, (offset_x, 0.0, 0.0))
    ground_mesh.materials.append(mat_grass)
    ground_obj = bpy.data.objects.new("Park_Ground", ground_mesh)
    col.objects.link(ground_obj)

    # 2. 산책로 모래길 (|y| < 1.0, X 길이 60m)
    path_pal = [hex_to_linear_rgb(c) for c in ["#d4b279", "#c9a469", "#deb882"]]
    path_pixels = []
    for _ in range(60 * 4):
        c = rng.choice(path_pal)
        path_pixels.extend(c)
    mat_path = create_pixel_texture_material(f"Mat_Path_{offset_x}", 60, 4, path_pixels, roughness=0.95)
    path_mesh = make_plane_mesh("Park_PathMesh", 60.0, 2.0, (offset_x, 0.0, 0.01))
    path_mesh.materials.append(mat_path)
    col.objects.link(bpy.data.objects.new("Park_Path", path_mesh))

    # 3. 벤치 (1.5, 1.8)
    mat_wood = get_or_create_material("Mat_BenchWood", "#5c3a21", roughness=0.7)
    bench_boxes = [
        ((1.4, 0.45, 0.08), (offset_x + 1.5, 1.8, 0.45)),  # 좌판
        ((1.4, 0.08, 0.45), (offset_x + 1.5, 2.0, 0.70)),  # 등받이
        ((0.08, 0.45, 0.45), (offset_x + 0.9, 1.8, 0.22)), # 좌측 다리
        ((0.08, 0.45, 0.45), (offset_x + 2.1, 1.8, 0.22)), # 우측 다리
    ]
    bench_mesh = combine_boxes_to_single_mesh("Park_BenchMesh", bench_boxes)
    bench_mesh.materials.append(mat_wood)
    col.objects.link(bpy.data.objects.new("Park_Bench", bench_mesh))

    # 4. 가로등 2개 ((-4, 2.2), (6, 2.2))
    mat_lamp_post = get_or_create_material("Mat_LampPost", "#222629")
    mat_lamp_light = get_or_create_material("Mat_LampLight", "#fff3cc", emission_strength=5.0)
    for lp_x in [-4.0, 6.0]:
        # 기둥
        post_obj = make_box_object(f"Park_LampPost_{lp_x}", (0.16, 0.16, 3.2), (offset_x + lp_x, 2.2, 1.6), mat_lamp_post, col)
        # 발광 헤드
        head_obj = make_box_object(f"Park_LampHead_{lp_x}", (0.4, 0.4, 0.3), (offset_x + lp_x, 2.2, 3.2), mat_lamp_light, col)
        # 포인트 라이트
        lp_data = bpy.data.lights.new(f"Park_PL_{lp_x}", "POINT")
        lp_data.energy = 400.0
        lp_data.color = (1.0, 0.9, 0.7)
        lp_obj = bpy.data.objects.new(f"Park_LightObj_{lp_x}", lp_data)
        lp_obj.location = (offset_x + lp_x, 2.2, 3.1)
        col.objects.link(lp_obj)
        lights.append((lp_obj, 400.0))

    # 5. 나무 배치 (단일 메시로 일괄 결합하여 성능 극대화)
    # 규칙: y > 2.5 또는 |x| > 7 (카메라 뷰 복도 유지)
    leaf_colors = {
        "autumn": ["#d9632a", "#e8a02c", "#b8402a", "#f0c040"],
        "spring": ["#71ba58", "#88d96e", "#9fe887", "#e0a6b7"],
        "summer": ["#2d7a2b", "#3a9937", "#45ad42", "#1f571e"],
        "winter": ["#a4b8ab", "#839488", "#d1ded6", "#657369"],
    }.get(season, ["#d9632a", "#e8a02c", "#b8402a", "#f0c040"])
    mat_leaf = get_or_create_material(f"Mat_Leaf_{season}", leaf_colors[0])
    mat_trunk = get_or_create_material("Mat_Trunk", "#4a3319")

    trunk_boxes = []
    leaf_boxes = []
    placed_trees = 0
    attempts = 0
    while placed_trees < num_trees and attempts < 200:
        attempts += 1
        tx = rng.uniform(-25.0, 25.0)
        ty = rng.uniform(-25.0, 25.0)
        if -2.0 <= ty <= 2.5 and abs(tx) <= 7.0:
            continue
        placed_trees += 1
        # 줄기 높이 3~4 블록 (1.5~2.0m)
        h_trunk = rng.randint(3, 4) * 0.5
        trunk_boxes.append(((0.4, 0.4, h_trunk), (offset_x + tx, ty, h_trunk / 2.0)))
        # 잎 블록 6~9개
        for _ in range(rng.randint(6, 9)):
            lx = tx + rng.uniform(-0.9, 0.9)
            ly = ty + rng.uniform(-0.9, 0.9)
            lz = h_trunk + rng.uniform(0.3, 1.6)
            leaf_boxes.append(((rng.uniform(0.8, 1.2), rng.uniform(0.8, 1.2), rng.uniform(0.8, 1.2)), (offset_x + lx, ly, lz)))

    if trunk_boxes:
        t_mesh = combine_boxes_to_single_mesh("Park_Trunks", trunk_boxes)
        t_mesh.materials.append(mat_trunk)
        col.objects.link(bpy.data.objects.new("Park_TrunksObj", t_mesh))
    if leaf_boxes:
        l_mesh = combine_boxes_to_single_mesh("Park_Leaves", leaf_boxes)
        l_mesh.materials.append(mat_leaf)
        col.objects.link(bpy.data.objects.new("Park_LeavesObj", l_mesh))

    # 6. 언덕 링 (반경 28m 블록들)
    hill_boxes = []
    for i in range(24):
        rad = math.radians(i * (360.0 / 24))
        hx = offset_x + math.cos(rad) * 28.0
        hy = math.sin(rad) * 28.0
        hill_boxes.append(((5.0, 5.0, rng.uniform(2.0, 4.5)), (hx, hy, 1.0)))
    hill_mesh = combine_boxes_to_single_mesh("Park_Hills", hill_boxes)
    hill_mesh.materials.append(mat_grass)
    col.objects.link(bpy.data.objects.new("Park_HillsObj", hill_mesh))

    # 7. 가을 낙엽 잔해 (약 150 픽셀 조각)
    if season == "autumn":
        leaf_flake_boxes = []
        for _ in range(150):
            fx = offset_x + rng.uniform(-18.0, 18.0)
            fy = rng.uniform(-18.0, 18.0)
            leaf_flake_boxes.append(((0.18, 0.18, 0.02), (fx, fy, 0.02)))
        flakes_mesh = combine_boxes_to_single_mesh("Park_FallenLeaves", leaf_flake_boxes)
        flakes_mesh.materials.append(mat_leaf)
        col.objects.link(bpy.data.objects.new("Park_FallenLeavesObj", flakes_mesh))

    return lights


def build_set_room(col: bpy.types.Collection, offset_x: float, options: Dict[str, Any], rng: random.Random) -> List[Tuple[bpy.types.Object, float]]:
    """
    방(Room) 세트 빌더:
    - 8x8 바닥 (나무 판자 질감), 뒷벽 및 좌우벽, 천장 (앞벽 없음. 천장이 있어 위에서 내려다보는 구도는 안 된다)
    - 중앙 테이블 및 양옆 의자, 책장, 창문, 화분, 플로어 램프
    """
    lights = []

    # 1. 나무 바닥 (x: -4..4, y: -5..3)
    wood_palette = [hex_to_linear_rgb(c) for c in ["#8c5835", "#9e643c", "#7a4c2d", "#aa6e44"]]
    floor_pixels = []
    for _ in range(64 * 64):
        floor_pixels.extend(rng.choice(wood_palette))
    mat_wood_floor = create_pixel_texture_material(f"Mat_RoomFloor_{offset_x}", 64, 64, floor_pixels, roughness=0.6)
    floor_mesh = make_plane_mesh("Room_FloorMesh", 8.0, 8.0, (offset_x, -1.0, 0.0))
    floor_mesh.materials.append(mat_wood_floor)
    col.objects.link(bpy.data.objects.new("Room_Floor", floor_mesh))

    # 2. 벽면 (뒷벽 y=3, 좌벽 x=-4, 우벽 x=4, 높이 3.2m)
    wall_palette = [hex_to_linear_rgb(c) for c in ["#eae4d8", "#dfd7c7", "#e4ddd0"]]
    wall_pixels = []
    for _ in range(32 * 32):
        wall_pixels.extend(rng.choice(wall_palette))
    mat_wall = create_pixel_texture_material(f"Mat_RoomWall_{offset_x}", 32, 32, wall_pixels, roughness=0.85)

    # 뒷벽 (두께 0.2, 폭 8.0, 높이 3.2)
    back_wall = make_box_object("Room_BackWall", (8.0, 0.2, 3.2), (offset_x, 3.1, 1.6), mat_wall, col)
    # 좌벽
    left_wall = make_box_object("Room_LeftWall", (0.2, 8.0, 3.2), (offset_x - 4.1, -1.0, 1.6), mat_wall, col)
    # 우벽
    right_wall = make_box_object("Room_RightWall", (0.2, 8.0, 3.2), (offset_x + 4.1, -1.0, 1.6), mat_wall, col)

    # 3. 창문 (뒷벽 중앙 z=2.0, 발광 유리창)
    mat_window = get_or_create_material("Mat_WindowPane", "#9fc4e8", emission_strength=0.5)
    window_frame = make_box_object("Room_Window", (2.0, 0.08, 1.4), (offset_x, 3.02, 2.0), mat_window, col)
    # 천장: 낮은 카메라에서 벽 위가 검게 비지 않게 덮는다(위에서 내려다보는 구도는 이 세트에서 쓰지 않는다)
    make_box_object("Room_Ceiling", (8.4, 8.0, 0.2), (offset_x, -1.0, 3.3), mat_wall, col)

    # 4. 가구 (테이블, 의자 2개)
    mat_furniture = get_or_create_material("Mat_Furniture", "#452f1e", roughness=0.5)
    table_boxes = [
        ((1.2, 0.8, 0.06), (offset_x, 0.5, 0.72)),          # 상판 z=0.75
        ((0.08, 0.08, 0.70), (offset_x - 0.52, 0.82, 0.35)), # 다리 4개
        ((0.08, 0.08, 0.70), (offset_x + 0.52, 0.82, 0.35)),
        ((0.08, 0.08, 0.70), (offset_x - 0.52, 0.18, 0.35)),
        ((0.08, 0.08, 0.70), (offset_x + 0.52, 0.18, 0.35)),
    ]
    # 의자 좌/우 (seat z=0.5)
    chair_L = [
        ((0.45, 0.45, 0.06), (offset_x - 0.95, 0.5, 0.47)),  # 시트
        ((0.06, 0.45, 0.45), (offset_x - 1.15, 0.5, 0.70)),  # 등받이
        ((0.06, 0.06, 0.45), (offset_x - 1.12, 0.68, 0.23)), # 다리
        ((0.06, 0.06, 0.45), (offset_x - 0.78, 0.68, 0.23)),
        ((0.06, 0.06, 0.45), (offset_x - 1.12, 0.32, 0.23)),
        ((0.06, 0.06, 0.45), (offset_x - 0.78, 0.32, 0.23)),
    ]
    chair_R = [
        ((0.45, 0.45, 0.06), (offset_x + 0.95, 0.5, 0.47)),
        ((0.06, 0.45, 0.45), (offset_x + 1.15, 0.5, 0.70)),
        ((0.06, 0.06, 0.45), (offset_x + 1.12, 0.68, 0.23)),
        ((0.06, 0.06, 0.45), (offset_x + 0.78, 0.68, 0.23)),
        ((0.06, 0.06, 0.45), (offset_x + 1.12, 0.32, 0.23)),
        ((0.06, 0.06, 0.45), (offset_x + 0.78, 0.32, 0.23)),
    ]
    all_furn = table_boxes + chair_L + chair_R
    furn_mesh = combine_boxes_to_single_mesh("Room_FurnitureMesh", all_furn)
    furn_mesh.materials.append(mat_furniture)
    col.objects.link(bpy.data.objects.new("Room_Furniture", furn_mesh))

    # 소품: 찻잔과 접시
    mat_dish = get_or_create_material("Mat_Dish", "#f0efe8")
    dish_boxes = [
        ((0.14, 0.14, 0.02), (offset_x - 0.25, 0.5, 0.76)),
        ((0.08, 0.08, 0.08), (offset_x - 0.25, 0.5, 0.81)),
        ((0.14, 0.14, 0.02), (offset_x + 0.25, 0.5, 0.76)),
        ((0.08, 0.08, 0.08), (offset_x + 0.25, 0.5, 0.81)),
    ]
    dishes_mesh = combine_boxes_to_single_mesh("Room_DishesMesh", dish_boxes)
    dishes_mesh.materials.append(mat_dish)
    col.objects.link(bpy.data.objects.new("Room_Dishes", dishes_mesh))

    # 플로어 램프 (코너 발광체 + 포인트 라이트)
    mat_lamp_shade = get_or_create_material("Mat_RoomLampShade", "#fff6d6", emission_strength=4.0)
    lamp_boxes = [
        ((0.08, 0.08, 1.8), (offset_x + 3.2, 2.2, 0.9)),
        ((0.4, 0.4, 0.35), (offset_x + 3.2, 2.2, 1.9)),
    ]
    lamp_mesh = combine_boxes_to_single_mesh("Room_FloorLampMesh", lamp_boxes)
    lamp_mesh.materials.append(mat_lamp_shade)
    col.objects.link(bpy.data.objects.new("Room_FloorLamp", lamp_mesh))

    # 5. 조명 설정: 천장 웜 포인트 라이트 (600W), 플로어 램프 (150W)
    ceil_light_data = bpy.data.lights.new("Room_CeilingLightData", "POINT")
    ceil_light_data.energy = 600.0
    ceil_light_data.color = (1.0, 0.88, 0.75)
    ceil_light_obj = bpy.data.objects.new("Room_CeilingLight", ceil_light_data)
    ceil_light_obj.location = (offset_x, 0.0, 2.9)
    col.objects.link(ceil_light_obj)
    lights.append((ceil_light_obj, 600.0))

    flamp_data = bpy.data.lights.new("Room_LampLightData", "POINT")
    flamp_data.energy = 150.0
    flamp_data.color = (1.0, 0.92, 0.80)
    flamp_obj = bpy.data.objects.new("Room_FloorLampLight", flamp_data)
    flamp_obj.location = (offset_x + 3.2, 2.2, 1.9)
    col.objects.link(flamp_obj)
    lights.append((flamp_obj, 150.0))

    return lights


def build_set_stadium(col: bpy.types.Collection, offset_x: float, options: Dict[str, Any], rng: random.Random) -> List[Tuple[bpy.types.Object, float]]:
    """
    스타디움(Stadium) 콘서트 세트 빌더:
    - 300x300 대형 바닥, 무대(Stage) 및 초대형 LED 전광판 (자체 발광 패턴)
    - 스피커 타워, 트러스 조명 (스포트라이트 6개 + 에어리어 라이트 1개)
    - 단일 메시 군중 (정점 컬러 속성 'Col' 부여)
    - 발광 응원봉 단일 메시, 원경 빌딩 군 단일 메시
    """
    lights = []
    crowd_target = options.get("crowd", 3000)

    # 1. 300x300 어두운 지면
    mat_stadium_ground = get_or_create_material("Mat_StadiumGround", "#0a0c10", roughness=0.9)
    ground_mesh = make_plane_mesh("Stadium_GroundMesh", 300.0, 300.0, (offset_x, 0.0, 0.0))
    ground_mesh.materials.append(mat_stadium_ground)
    col.objects.link(bpy.data.objects.new("Stadium_Ground", ground_mesh))

    # 2. 무대 (Stage: x -9..9, y 26..34, 상단 z=1.5)
    mat_stage = get_or_create_material("Mat_Stage", "#181a20", roughness=0.4)
    stage_obj = make_box_object("Stadium_Stage", (18.0, 8.0, 1.5), (offset_x, 30.0, 0.75), mat_stage, col)

    # 3. LED 전광판 (y=34, 폭 18m x 높이 9m, emissive pattern strength=3.0)
    led_palette = [hex_to_linear_rgb(c) for c in ["#ff0055", "#7a00ff", "#00e5ff", "#ffe600", "#110022"]]
    led_pixels = []
    for _ in range(64 * 32):
        led_pixels.extend(rng.choice(led_palette))
    mat_led = create_pixel_texture_material(f"Mat_StadiumLED_{offset_x}", 64, 32, led_pixels, roughness=0.3)
    # Emission 강도 3.0 보강
    bsdf_node = next((n for n in mat_led.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf_node:
        tex_node = next((n for n in mat_led.node_tree.nodes if n.type == "TEX_IMAGE"), None)
        if tex_node:
            em_socket = bsdf_node.inputs.get("Emission Color") or bsdf_node.inputs.get("Emission")
            if em_socket:
                mat_led.node_tree.links.new(tex_node.outputs["Color"], em_socket)
            if "Emission Strength" in bsdf_node.inputs:
                bsdf_node.inputs["Emission Strength"].default_value = 3.0

    led_mesh = make_plane_mesh("Stadium_LEDMesh", 18.0, 9.0, (0.0, 0.0, 0.0))
    led_mesh.materials.append(mat_led)
    led_obj = bpy.data.objects.new("Stadium_LEDWall", led_mesh)
    led_obj.location = (offset_x, 33.95, 6.0)
    led_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    col.objects.link(led_obj)

    # 4. 스피커 타워 (무대 4개 모퉁이)
    mat_speaker = get_or_create_material("Mat_Speaker", "#111114")
    spk_boxes = [
        ((1.4, 1.4, 8.0), (offset_x - 9.5, 26.5, 4.0)),
        ((1.4, 1.4, 8.0), (offset_x + 9.5, 26.5, 4.0)),
        ((1.4, 1.4, 8.0), (offset_x - 9.5, 33.5, 4.0)),
        ((1.4, 1.4, 8.0), (offset_x + 9.5, 33.5, 4.0)),
    ]
    spk_mesh = combine_boxes_to_single_mesh("Stadium_Speakers", spk_boxes)
    spk_mesh.materials.append(mat_speaker)
    col.objects.link(bpy.data.objects.new("Stadium_SpeakersObj", spk_mesh))

    # 5. 조명 트러스 및 스포트라이트 6개 (6000W), 무대 에어리어 라이트 (1500W)
    spot_colors = [
        (1.0, 0.2, 0.4), (0.2, 0.4, 1.0), (0.9, 0.1, 1.0),
        (0.1, 1.0, 0.8), (1.0, 0.8, 0.1), (0.2, 0.8, 1.0)
    ]
    for i in range(6):
        tx = -7.5 + i * 3.0
        sp_data = bpy.data.lights.new(f"Stadium_Spot_{i}", "SPOT")
        sp_data.energy = 6000.0
        sp_data.spot_size = math.radians(45.0)
        sp_data.spot_blend = 0.3
        sp_data.color = spot_colors[i]
        sp_obj = bpy.data.objects.new(f"Stadium_SpotObj_{i}", sp_data)
        sp_obj.location = (offset_x + tx, 26.0, 8.5)
        # 객석(-Y 방향, 하향)을 향하도록 회전
        sp_obj.rotation_euler = (math.radians(-50.0), 0.0, math.radians(tx * 2.0))
        col.objects.link(sp_obj)
        lights.append((sp_obj, 6000.0))

    stage_light_data = bpy.data.lights.new("Stadium_StageAreaLight", "AREA")
    stage_light_data.energy = 1500.0
    stage_light_data.size = 14.0
    stage_light_data.color = (1.0, 0.95, 0.9)
    stage_area_obj = bpy.data.objects.new("Stadium_StageAreaObj", stage_light_data)
    stage_area_obj.location = (offset_x, 30.0, 7.5)
    stage_area_obj.rotation_euler = (0.0, 0.0, 0.0)
    col.objects.link(stage_area_obj)
    lights.append((stage_area_obj, 1500.0))

    # 6. 군중(Crowd) 단일 메시 빌드
    # 각 관객: 몸통 (0.5 x 0.3 x 1.2) + 머리 (0.4 cube), 색상 속성 'Col'
    field_count = int(crowd_target * 0.40)
    stands_count = int(crowd_target * 0.60)

    # 셔츠 색상 팔레트
    shirt_colors = [hex_to_linear_rgb(c) for c in ["#e63946", "#457b9d", "#f4a261", "#2a9d8f", "#e76f51", "#a8dadc", "#ffffff", "#222222"]]
    skin_colors = [hex_to_linear_rgb(c) for c in ["#f1c9a2", "#e9b98f", "#d29a6e", "#8d5524"]]

    crowd_verts = []
    crowd_faces = []
    crowd_vert_colors = []  # 정점별 색상 저장
    lightstick_boxes = []

    def add_person_voxels(px: float, py: float, pz: float, shirt_col: Tuple[float, float, float, float], skin_col: Tuple[float, float, float, float], has_stick: bool) -> None:
        base_idx = len(crowd_verts)
        # 몸통 (0.5 x 0.3 x 1.2, 중심 z = pz + 0.6)
        bdx, bdy, bdz = 0.25, 0.15, 0.60
        bcz = pz + 0.60
        body_v = [
            (px - bdx, py - bdy, bcz - bdz), (px + bdx, py - bdy, bcz - bdz),
            (px + bdx, py + bdy, bcz - bdz), (px - bdx, py + bdy, bcz - bdz),
            (px - bdx, py - bdy, bcz + bdz), (px + bdx, py - bdy, bcz + bdz),
            (px + bdx, py + bdy, bcz + bdz), (px - bdx, py + bdy, bcz + bdz),
        ]
        # 머리 (0.4 x 0.4 x 0.4, 중심 z = pz + 1.2 + 0.2 = pz + 1.4)
        hdx, hdy, hdz = 0.20, 0.20, 0.20
        hcz = pz + 1.40
        head_v = [
            (px - hdx, py - hdy, hcz - hdz), (px + hdx, py - hdy, hcz - hdz),
            (px + hdx, py + hdy, hcz - hdz), (px - hdx, py + hdy, hcz - hdz),
            (px - hdx, py - hdy, hcz + hdz), (px + hdx, py - hdy, hcz + hdz),
            (px + hdx, py + hdy, hcz + hdz), (px - hdx, py + hdy, hcz + hdz),
        ]

        crowd_verts.extend(body_v)
        crowd_verts.extend(head_v)
        crowd_vert_colors.extend([shirt_col] * 8)
        crowd_vert_colors.extend([skin_col] * 8)

        box_f_offsets = [
            (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
            (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)
        ]
        for f in box_f_offsets:
            crowd_faces.append((base_idx + f[0], base_idx + f[1], base_idx + f[2], base_idx + f[3]))
        for f in box_f_offsets:
            crowd_faces.append((base_idx + 8 + f[0], base_idx + 8 + f[1], base_idx + 8 + f[2], base_idx + 8 + f[3]))

        if has_stick:
            # 오른손 높이 발광봉 (0.06 x 0.06 x 0.40)
            lightstick_boxes.append(((0.06, 0.06, 0.40), (px + 0.28, py - 0.1, pz + 1.15)))

    # 필드 관객 생성 (x -22..22, y -24..22 지터 그리드)
    for _ in range(field_count):
        px = offset_x + rng.uniform(-22.0, 22.0)
        py = rng.uniform(-24.0, 22.0)
        pz = 0.0
        s_col = rng.choice(shirt_colors)
        sk_col = rng.choice(skin_colors)
        stick = (rng.random() < 0.08)
        add_person_voxels(px, py, pz, s_col, sk_col, stick)

    # 관중석 스탠드 관객 (서쪽 x<-28, 동쪽 x>28, 남쪽 y<-30)
    for _ in range(stands_count):
        region = rng.choice(["W", "E", "S"])
        if region == "W":
            tier = rng.randint(0, 12)
            px = offset_x - (28.5 + tier * 1.5)
            py = rng.uniform(-40.0, 20.0)
            pz = tier * 1.2
        elif region == "E":
            tier = rng.randint(0, 12)
            px = offset_x + (28.5 + tier * 1.5)
            py = rng.uniform(-40.0, 20.0)
            pz = tier * 1.2
        else:
            tier = rng.randint(0, 15)
            px = offset_x + rng.uniform(-35.0, 35.0)
            py = -(30.5 + tier * 1.5)
            pz = tier * 1.2

        s_col = rng.choice(shirt_colors)
        sk_col = rng.choice(skin_colors)
        stick = (rng.random() < 0.08)
        add_person_voxels(px, py, pz, s_col, sk_col, stick)

    # 군중 메시 객체 조립
    crowd_mesh = bpy.data.meshes.new("Stadium_CrowdMesh")
    crowd_mesh.from_pydata(crowd_verts, [], crowd_faces)
    crowd_mesh.update()

    # 정점 컬러 속성 'Col' 생성
    color_attr = crowd_mesh.color_attributes.new(name="Col", type="FLOAT_COLOR", domain="POINT")
    for i, col_val in enumerate(crowd_vert_colors):
        color_attr.data[i].color = col_val

    # 군중 셰이더 (Attribute 'Col' -> Base Color + Emission 강도 0.25)
    mat_crowd = bpy.data.materials.new(name="Mat_Crowd")
    mat_crowd.use_nodes = True
    c_nodes = mat_crowd.node_tree.nodes
    c_nodes.clear()
    attr_node = c_nodes.new(type="ShaderNodeAttribute")
    attr_node.attribute_name = "Col"
    attr_node.location = (-300, 0)
    c_bsdf = c_nodes.new(type="ShaderNodeBsdfPrincipled")
    c_bsdf.location = (0, 0)
    c_out = c_nodes.new(type="ShaderNodeOutputMaterial")
    c_out.location = (300, 0)

    mat_crowd.node_tree.links.new(attr_node.outputs["Color"], c_bsdf.inputs["Base Color"])
    em_socket = c_bsdf.inputs.get("Emission Color") or c_bsdf.inputs.get("Emission")
    if em_socket:
        mat_crowd.node_tree.links.new(attr_node.outputs["Color"], em_socket)
    if "Emission Strength" in c_bsdf.inputs:
        c_bsdf.inputs["Emission Strength"].default_value = 0.25
    mat_crowd.node_tree.links.new(c_bsdf.outputs["BSDF"], c_out.inputs["Surface"])

    crowd_mesh.materials.append(mat_crowd)
    col.objects.link(bpy.data.objects.new("Stadium_Crowd", crowd_mesh))

    # 응원봉 단일 메시
    if lightstick_boxes:
        ls_mesh = combine_boxes_to_single_mesh("Stadium_Lightsticks", lightstick_boxes)
        mat_ls = get_or_create_material("Mat_LightStick", "#00ffc8", emission_strength=8.0)
        ls_mesh.materials.append(mat_ls)
        col.objects.link(bpy.data.objects.new("Stadium_LightsticksObj", ls_mesh))

    # 7. 원경 도시 (거리 90..140m 사이 60개 어두운 빌딩 + 300개 발광 창문)
    bldg_boxes = []
    window_boxes = []
    for _ in range(60):
        angle = rng.uniform(0, 2 * math.pi)
        dist = rng.uniform(90.0, 140.0)
        bx = offset_x + math.cos(angle) * dist
        by = math.sin(angle) * dist
        bw = rng.uniform(10.0, 22.0)
        bd = rng.uniform(10.0, 22.0)
        bh = rng.uniform(25.0, 75.0)
        bldg_boxes.append(((bw, bd, bh), (bx, by, bh / 2.0)))
        # 창문 5개 배치
        for _ in range(5):
            wx = bx + rng.uniform(-bw * 0.4, bw * 0.4)
            wy = by - (bd / 2.0 + 0.1)
            wz = rng.uniform(10.0, bh - 5.0)
            window_boxes.append(((1.2, 0.2, 1.8), (wx, wy, wz)))

    mat_bldg = get_or_create_material("Mat_CityBldg", "#08090d", roughness=0.9)
    bldg_mesh = combine_boxes_to_single_mesh("Stadium_CityBldgs", bldg_boxes)
    bldg_mesh.materials.append(mat_bldg)
    col.objects.link(bpy.data.objects.new("Stadium_CityBldgsObj", bldg_mesh))

    mat_bldg_win = get_or_create_material("Mat_CityWin", "#ffeaa7", emission_strength=4.0)
    win_mesh = combine_boxes_to_single_mesh("Stadium_CityWins", window_boxes)
    win_mesh.materials.append(mat_bldg_win)
    col.objects.link(bpy.data.objects.new("Stadium_CityWinsObj", win_mesh))

    return lights


SETS = {
    "park": build_set_park,
    "room": build_set_room,
    "stadium": build_set_stadium,
}


# -----------------------------------------------------------------------------
# 환경 설정 (월드, 태양광 및 쇼트 보간)
# -----------------------------------------------------------------------------

TIME_PRESETS = {
    "day": {
        "sky": "#8ec9f0",
        "sky_strength": 1.0,
        "sun_energy": 4.0,
        "sun_color": (1.0, 0.98, 0.92),
        "sun_rot": (math.radians(45.0), math.radians(20.0), math.radians(30.0)),
    },
    "evening": {
        "sky": "#e79a63",
        "sky_strength": 0.6,
        "sun_energy": 2.0,
        "sun_color": (1.0, 0.55, 0.2),
        "sun_rot": (math.radians(15.0), math.radians(10.0), math.radians(65.0)),
    },
    "night": {
        "sky": "#060a18",
        "sky_strength": 0.25,
        "sun_energy": 0.15,
        "sun_color": (0.4, 0.5, 0.8),
        "sun_rot": (math.radians(60.0), math.radians(0.0), math.radians(120.0)),
    },
}

def setup_world_and_sun(scene: bpy.types.Scene) -> Tuple[bpy.types.World, bpy.types.Object, bpy.types.Node]:
    """단일 World 및 Sun 오브젝트를 구성"""
    world = bpy.data.worlds.new("VoxelWorld")
    world.use_nodes = True
    scene.world = world

    w_nodes = world.node_tree.nodes
    w_nodes.clear()
    bg_node = w_nodes.new(type="ShaderNodeBackground")
    bg_node.location = (0, 0)
    out_node = w_nodes.new(type="ShaderNodeOutputWorld")
    out_node.location = (300, 0)
    world.node_tree.links.new(bg_node.outputs["Background"], out_node.inputs["Surface"])

    sun_data = bpy.data.lights.new("VoxelSunData", "SUN")
    sun_obj = bpy.data.objects.new("VoxelSun", sun_data)
    scene.collection.objects.link(sun_obj)

    return world, sun_obj, bg_node


# -----------------------------------------------------------------------------
# 메인 파이프라인
# -----------------------------------------------------------------------------

def main() -> None:
    # 1. 커맨드라인 인자 파싱 (CLI `--` 이후의 인자 추출)
    args = sys.argv
    timeline_path = "timeline.example.json"
    blend_out_path = "scene.blend"

    if "--" in args:
        custom_args = args[args.index("--") + 1:]
        if len(custom_args) >= 1:
            timeline_path = custom_args[0]
        if len(custom_args) >= 2:
            blend_out_path = custom_args[1]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(timeline_path):
        timeline_path = os.path.join(script_dir, timeline_path)
    if not os.path.isabs(blend_out_path):
        blend_out_path = os.path.join(script_dir, blend_out_path)

    if not os.path.exists(timeline_path):
        raise FileNotFoundError(f"타임라인 JSON 파일을 찾을 수 없습니다: {timeline_path}")

    with open(timeline_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. Blender 공장 초기화
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # 3. 렌더러 설정 (Blender 4.5/5.x 호환 EEVEE 엔진 설정)
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        scene.render.engine = "BLENDER_EEVEE"

    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 32

    if hasattr(scene.display_settings, "display_device"):
        scene.view_settings.view_transform = "Standard"

    # 4. 해상도 및 프레임 범위 설정
    fps = int(data.get("fps", 24))
    width = int(data.get("width", 1080))
    height = int(data.get("height", 1920))
    scene.render.fps = fps
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.frame_start = 1

    shots = data.get("shots", [])
    if not shots:
        raise ValueError("타임라인에 shots가 비어있습니다.")

    total_end_sec = max(shot.get("end", 0.0) for shot in shots)
    scene.frame_end = max(1, round(total_end_sec * fps))

    # 5. 환경(World 및 Sun) 초기화
    world, sun_obj, bg_node = setup_world_and_sun(scene)

    # 6. 세트 빌드 및 세트 인스턴스/오프셋 캐싱
    # {set_id: (offset_x, lights_list)}
    built_sets: Dict[str, Tuple[float, List[Tuple[bpy.types.Object, float]]]] = {}
    built_set_count = 0

    # reuse_set 체인 해석 함수
    def resolve_set_shot_id(s_id: str) -> str:
        visited = set()
        curr_id = s_id
        while curr_id in shot_map and "reuse_set" in shot_map[curr_id]:
            if curr_id in visited:
                raise ValueError(f"reuse_set 순환 참조 감지: {curr_id}")
            visited.add(curr_id)
            curr_id = shot_map[curr_id]["reuse_set"]
        return curr_id

    shot_map = {s["id"]: s for s in shots}

    for shot in shots:
        shot_id = shot["id"]
        if "set" in shot:
            set_name = shot["set"]
            if set_name not in SETS:
                raise ValueError(f"알 수 없는 set: '{set_name}'. 유효한 세트 목록: {list(SETS.keys())}")
            offset_x = 400.0 * built_set_count
            built_set_count += 1

            # 세트 컬렉션 생성
            set_col = bpy.data.collections.new(f"Set_{shot_id}_{set_name}")
            scene.collection.children.link(set_col)

            options = shot.get("set_options", {})
            rng = random.Random(options.get("seed", 42))
            created_lights = SETS[set_name](set_col, offset_x, options, rng)
            built_sets[shot_id] = (offset_x, created_lights)

    # 7. 쇼트별 카메라, 조명, 액터 구축 및 애니메이션
    cast_specs = data.get("cast", {})
    first_shot_cam = None

    for shot in shots:
        shot_id = shot["id"]
        start_sec = float(shot.get("start", 0.0))
        end_sec = float(shot.get("end", start_sec + 1.0))
        f_first = round(start_sec * fps) + 1
        f_last = round(end_sec * fps)

        # 세트 오프셋 및 조명 참조
        resolved_shot_id = resolve_set_shot_id(shot_id)
        if resolved_shot_id not in built_sets:
            raise ValueError(f"쇼트 '{shot_id}'의 세트를 찾을 수 없습니다 (resolved: '{resolved_shot_id}')")
        offset_x, set_lights = built_sets[resolved_shot_id]

        # 월드 및 썬 조명 키프레임 (CONSTANT)
        time_preset_key = shot.get("time", "day")
        if time_preset_key not in TIME_PRESETS:
            raise ValueError(f"알 수 없는 time 프리셋: '{time_preset_key}'. 유효 목록: {list(TIME_PRESETS.keys())}")
        t_info = TIME_PRESETS[time_preset_key]

        bg_node.inputs["Color"].default_value = hex_to_linear_rgb(t_info["sky"])
        bg_node.inputs["Strength"].default_value = t_info["sky_strength"]
        key(bg_node.inputs["Color"], "default_value", f_first, interp="CONSTANT")
        key(bg_node.inputs["Strength"], "default_value", f_first, interp="CONSTANT")

        sun_obj.data.energy = t_info["sun_energy"]
        sun_obj.data.color = t_info["sun_color"]
        sun_obj.rotation_euler = t_info["sun_rot"]
        key(sun_obj.data, "energy", f_first, interp="CONSTANT")
        key(sun_obj.data, "color", f_first, interp="CONSTANT")
        key(sun_obj, "rotation_euler", f_first, interp="CONSTANT")

        # 세트 내부 램프 밝기 키프레임
        lamp_scale = float(shot.get("lamps", 1.0))
        for light_obj, base_energy in set_lights:
            light_obj.data.energy = base_energy * lamp_scale
            key(light_obj.data, "energy", f_first, interp="CONSTANT")

        # 카메라 및 트랙 대상 Empty 구축
        cam_spec = shot.get("camera", {})
        cam_from = cam_spec.get("from", [0, -10, 3])
        cam_to = cam_spec.get("to", cam_from)
        look_from = cam_spec.get("look_from", [0, 0, 1])
        look_to = cam_spec.get("look_to", look_from)
        lens = float(cam_spec.get("lens", 35.0))

        cam_data = bpy.data.cameras.new(f"CamData_{shot_id}")
        cam_data.lens = lens
        cam_data.clip_end = 3000.0
        cam_obj = bpy.data.objects.new(f"Camera_{shot_id}", cam_data)
        scene.collection.objects.link(cam_obj)

        if first_shot_cam is None:
            first_shot_cam = cam_obj

        # 타임라인 마커에 카메라 바인딩
        marker = scene.timeline_markers.new(shot_id, frame=f_first)
        marker.camera = cam_obj

        # Look Empty 생성
        look_obj = bpy.data.objects.new(f"Look_{shot_id}", None)
        look_obj.empty_display_type = "PLAIN_AXES"
        scene.collection.objects.link(look_obj)

        # Track To 제약조건 설정 (TRACK_NEGATIVE_Z, UP_Y)
        c_track = cam_obj.constraints.new(type="TRACK_TO")
        c_track.target = look_obj
        c_track.track_axis = "TRACK_NEGATIVE_Z"
        c_track.up_axis = "UP_Y"

        # 카메라 및 Look 대상 위치 키프레임 (BEZIER 보간)
        cam_obj.location = (offset_x + cam_from[0], cam_from[1], cam_from[2])
        key(cam_obj, "location", f_first, interp="BEZIER")
        cam_obj.location = (offset_x + cam_to[0], cam_to[1], cam_to[2])
        key(cam_obj, "location", f_last, interp="BEZIER")

        look_obj.location = (offset_x + look_from[0], look_from[1], look_from[2])
        key(look_obj, "location", f_first, interp="BEZIER")
        look_obj.location = (offset_x + look_to[0], look_to[1], look_to[2])
        key(look_obj, "location", f_last, interp="BEZIER")

        # 쇼트별 액터 인스턴스 생성
        shot_actors = shot.get("actors", [])
        actor_col = bpy.data.collections.new(f"Actors_{shot_id}")
        scene.collection.children.link(actor_col)

        for actor_entry in shot_actors:
            who = actor_entry["who"]
            if who not in cast_specs:
                raise ValueError(f"캐스트 명단에 없는 액터: '{who}'. 캐스트 목록: {list(cast_specs.keys())}")
            cast_info = cast_specs[who]
            actor_rig = build_character_rig(f"{shot_id}_{who}", cast_info, actor_col)

            # Park Empty 숨김 처리 키프레임 (쇼트 범위 외에는 z = -2000, 쇼트 내부 z = 0)
            rig_park = actor_rig["park"]
            rig_park.location = (0.0, 0.0, -2000.0)
            key(rig_park, "location", 1, interp="CONSTANT")
            if f_first > 1:
                key(rig_park, "location", f_first - 1, interp="CONSTANT")
            rig_park.location = (0.0, 0.0, 0.0)
            key(rig_park, "location", f_first, interp="CONSTANT")
            if f_last < scene.frame_end:
                rig_park.location = (0.0, 0.0, -2000.0)
                key(rig_park, "location", f_last + 1, interp="CONSTANT")

            # 초기 위치 및 회전 (heading degrees -> Root rotation_z = radians(heading))
            at_loc = actor_entry.get("at", [0.0, 0.0, 0.0])
            heading = float(actor_entry.get("heading", 0.0))
            rig_root = actor_rig["root"]
            rig_root.location = (offset_x + at_loc[0], at_loc[1], at_loc[2])
            rig_root.rotation_euler = (0.0, 0.0, math.radians(heading))
            key(rig_root, "location", f_first, interp="CONSTANT")
            key(rig_root, "rotation_euler", f_first, interp="CONSTANT")

            # 액터 액션 애니메이션 수행
            actions_list = actor_entry.get("actions", [])
            for act in actions_list:
                do_action = act.get("do", "idle")
                if do_action not in ACTIONS:
                    raise ValueError(f"알 수 없는 액션: '{do_action}'. 유효한 액션 목록: {list(ACTIONS.keys())}")
                act_t0 = float(act.get("t0", 0.0))
                act_t1 = float(act.get("t1", end_sec - start_sec))
                act_f0 = f_first + round(act_t0 * fps)
                act_f1 = f_first + round(act_t1 * fps)
                # 타임라인 좌표는 세트 로컬이라, 이동 목적지에 더할 세트 오프셋을 함께 넘긴다
                act_with_offset = dict(act)
                act_with_offset["_offset_x"] = offset_x
                ACTIONS[do_action](actor_rig, act_with_offset, act_f0, act_f1, float(fps))

    # 첫 번째 쇼트 카메라 활성화
    if first_shot_cam:
        scene.camera = first_shot_cam

    # 8. 파일 저장 및 완료 메시지 출력
    out_dir = os.path.dirname(blend_out_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=blend_out_path)
    print(f"SCENE_OK frames={scene.frame_end} shots={len(shots)}")


if __name__ == "__main__":
    main()
