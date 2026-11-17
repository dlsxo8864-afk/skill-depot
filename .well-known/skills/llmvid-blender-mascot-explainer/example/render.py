"""scene.blend 를 EEVEE 로 렌더한다. 작업 폴더에서 실행.

사용: blender -b scene.blend --python-exit-code 1 -P render.py -- 프레임목록 폭 높이 샘플 접두사
- 프레임목록: 1,5,9 또는 a-b:step (예: 1-360 은 전부, 36-360:72 는 구간마다 한 장)
- 접두사: frames/f 이면 frames/f0001.png 꼴로 저장한다(절대 경로도 된다)
이미 있는 프레임은 건너뛴다(끊겨도 같은 명령으로 이어서 렌더). 컷 카메라는 plan.py 의 SHOTS 로 고른다.
"""
import os
import sys
import time

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
spec, w, h, samples, prefix = args[0], int(args[1]), int(args[2]), int(args[3]), args[4]
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
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = samples
scene.render.use_persistent_data = True
scene.render.image_settings.file_format = "PNG"
t0 = time.time()
n = 0
for f in frames:
    path = os.path.join(os.getcwd(), f"{prefix}{f:04d}.png")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        continue
    scene.frame_set(f)
    name = plan.shot_at(min(f - 1, plan.TOTAL - 1))
    scene.camera = bpy.data.objects["cam_" + name]
    scene.render.filepath = path
    t1 = time.time()
    bpy.ops.render.render(write_still=True)
    n += 1
    print(f"FRAME {f} {name} {time.time() - t1:.1f}s", flush=True)
print(f"DONE {n} frames {time.time() - t0:.0f}s", flush=True)
