"""저장한 .blend 에서 구간(장면)마다 가운데 프레임을 한 장씩 뽑는다. 결과는 이 스크립트 옆 previews/ 에 생긴다.

사용: blender --background <scene.blend> --python-exit-code 1 --python preview_checks.py
"""
import bpy
import json
import time
from pathlib import Path

root = Path(__file__).resolve().parent
scene = bpy.context.scene
scene.render.resolution_percentage = 50
scene.eevee.taa_render_samples = 16
marks = sorted(scene.timeline_markers, key=lambda m: m.frame)
frames = []
for i, m in enumerate(marks):
    end = marks[i + 1].frame - 1 if i + 1 < len(marks) else scene.frame_end
    frames += [(m.frame + end) // 2, max(m.frame, end - 3)]  # 가운데와 끝
proofs = []
for frame in frames:
    scene.frame_set(frame)
    output = root / "previews" / f"proof_{frame:04}.png"
    scene.render.filepath = str(output)
    before = time.monotonic()
    bpy.ops.render.render(write_still=True)
    proofs.append({"frame": frame, "camera": scene.camera.name, "render_seconds": round(time.monotonic() - before, 3), "path": str(output)})
(root / "preview-checks.json").write_text(json.dumps(proofs, indent=2), encoding="utf-8")
print(json.dumps(proofs))
