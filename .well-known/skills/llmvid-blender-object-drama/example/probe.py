"""소재 크기·GPU 확인 전용. 렌더 장치로 무엇이 잡히는지, 소품이 얼마나 큰지 찍는다.

사용: blender -b -P probe.py -- <소재 폴더>
- DEVICES 줄: 장치 종류별로 잡힌 장치. 렌더 스크립트의 DEVICE 를 여기서 실제 GPU 가 보이는 종류로 맞춘다.
- ASSET 줄: 소품마다 삼각형 수·크기(미터)·바닥 좌표·오브젝트 이름. 자리와 크기를 정할 때 본다.
"""
import glob
import os
import sys

import bpy
from mathutils import Vector

root = sys.argv[sys.argv.index("--") + 1]
prefs = bpy.context.preferences.addons["cycles"].preferences
for typ in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
    try:
        prefs.compute_device_type = typ
        prefs.get_devices()
        print("DEVICES", typ, [(d.name, d.type) for d in prefs.devices])
    except Exception as e:
        print("ERR", typ, e)

for path in sorted(glob.glob(os.path.join(root, "models", "*", "*.gltf"))):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    pts = []
    tris = 0
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
            tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    print("ASSET", os.path.basename(path), "objs", len(bpy.context.scene.objects), "tris", tris, "size", [round(hi[i] - lo[i], 3) for i in range(3)], "lo", [round(v, 3) for v in lo], "names", [o.name for o in bpy.context.scene.objects][:6])
