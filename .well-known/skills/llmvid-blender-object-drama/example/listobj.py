"""장면 안 메시의 이름·자리(최소, 최대 좌표)·재질을 찍는다. 카메라나 소품 자리를 고칠 때 쓴다.

사용: blender -b scene.blend -P listobj.py
"""
import bpy
from mathutils import Vector

for o in bpy.data.objects:
    if o.type != "MESH" or o.name.startswith("g_"):
        continue
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    print("OBJ", o.name, [round(v, 2) for v in lo], [round(v, 2) for v in hi], [m.name for m in o.data.materials])
