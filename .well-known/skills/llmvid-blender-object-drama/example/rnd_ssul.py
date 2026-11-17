"""사물극 렌더. 작업 폴더에서 실행.

사용: blender -b scene.blend --python-exit-code 1 -P rnd_ssul.py -- 프레임목록 폭 높이 샘플 접두사 [engine]
- 프레임목록: 1,5,9 또는 a-b:step (예: 1-360:2 는 1, 3, 5 … 359)
- 접두사: frames/f 이면 frames/f0001.png 꼴로 저장한다(절대 경로도 된다)
- engine: CYCLES(기본) 또는 BLENDER_EEVEE(카툰판 scene_toon.blend 용)
이미 있는 프레임은 건너뛴다(끊겨도 같은 명령으로 이어서 렌더). 샷 카메라는 plan.py 의 SHOTS 로 고른다.
"""
import os
import sys
import time

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan  # noqa: E402

# [장치] 시험 PC(RTX 3070 Ti 8GB, 드라이버 560)는 OptiX 가 실패해 CUDA 로 고정했다.
#        다른 환경에서는 이 값을 고친다: "OPTIX"(NVIDIA RTX) | "HIP"(AMD) | "ONEAPI"(Intel Arc) | "METAL"(Mac) | "CPU"
#        어떤 장치가 잡히는지는 probe.py 로 먼저 확인한다. CUDA 밖의 값은 이 팩에서 시험하지 못했다(CPU 만 1프레임 확인).
DEVICE = "CUDA"

args = sys.argv[sys.argv.index("--") + 1:]
spec, w, h, samples, prefix = args[0], int(args[1]), int(args[2]), int(args[3]), args[4]
engine = args[5] if len(args) > 5 else "CYCLES"
frames = []
for part in spec.split(","):
    if "-" in part:
        rng, _, step = part.partition(":")
        a, b = map(int, rng.split("-"))
        frames += list(range(a, b + 1, int(step or 1)))
    else:
        frames.append(int(part))

scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = w, h, 100
if engine == "CYCLES":
    scene.render.engine = "CYCLES"
    c = scene.cycles
    if DEVICE == "CPU":
        c.device = "CPU"
    else:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = DEVICE
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == DEVICE
        if not any(d.use for d in prefs.devices):
            raise SystemExit(f"{DEVICE} 장치를 찾지 못했습니다. rnd_ssul.py 의 DEVICE 를 고치세요. 잡힌 장치: {[(d.name, d.type) for d in prefs.devices]}")
        c.device = "GPU"
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.03
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.max_bounces = 6
    c.diffuse_bounces = 3
    c.glossy_bounces = 3
    c.caustics_reflective = False
    c.caustics_refractive = False
else:
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = samples
    scene.eevee.use_raytracing = True
scene.render.use_persistent_data = True
scene.render.image_settings.file_format = "PNG"
t0 = time.time()
n = 0
for f in frames:
    path = os.path.join(os.getcwd(), f"{prefix}{f:04d}.png")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        continue
    scene.frame_set(f)
    name = plan.shot_at(f - 1)
    scene.camera = bpy.data.objects["cam_" + name]
    scene.render.filepath = path
    t1 = time.time()
    bpy.ops.render.render(write_still=True)
    n += 1
    print(f"FRAME {f} {name} {time.time() - t1:.1f}s", flush=True)
print(f"DONE {n} frames {time.time() - t0:.0f}s", flush=True)
