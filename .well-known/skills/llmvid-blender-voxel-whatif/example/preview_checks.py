"""샷마다 스틸을 뽑아 구도·가림·자세를 미리 본다(열린 .blend 기준).

사용:
  blender --background scene.blend --python-exit-code 1 --python preview_checks.py -- [출력 폴더] [--each 3] [--percent 50]

- 샷 구간은 타임라인 마커(샷 id, 카메라 연결)에서 읽는다.
- --each 1 이면 샷 가운데 한 장, 3 이면 앞·가운데·끝 세 장.
- 파일 이름: proof_<샷 순번>_<샷 id>_<프레임>.png
"""
import argparse
import os
import sys

import bpy


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default="previews")
    ap.add_argument("--each", type=int, default=3, choices=(1, 3))
    ap.add_argument("--percent", type=int, default=50)
    ap.add_argument("--samples", type=int, default=16)
    opt = ap.parse_args(argv)

    scene = bpy.context.scene
    base = os.path.dirname(bpy.data.filepath) or os.getcwd()
    out_dir = opt.out if os.path.isabs(opt.out) else os.path.join(base, opt.out)
    os.makedirs(out_dir, exist_ok=True)

    scene.render.resolution_percentage = opt.percent
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.eevee.taa_render_samples = opt.samples

    markers = sorted(scene.timeline_markers, key=lambda m: m.frame)
    if not markers:
        raise SystemExit("타임라인 마커가 없습니다. 장면 생성 스크립트를 먼저 실행하세요.")

    count = 0
    for idx, marker in enumerate(markers):
        first = marker.frame
        last = markers[idx + 1].frame - 1 if idx + 1 < len(markers) else scene.frame_end
        mid = (first + last) // 2
        frames = [mid] if opt.each == 1 else [min(first + 2, last), mid, max(last - 2, first)]
        for frame in frames:
            scene.frame_set(frame)
            if marker.camera is not None:
                scene.camera = marker.camera
            path = os.path.join(out_dir, f"proof_{idx + 1:02d}_{marker.name}_{frame:04d}.png")
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            count += 1
            print(f"PROOF {path}", flush=True)
    print(f"PREVIEW_OK stills={count} dir={out_dir}", flush=True)


main()
