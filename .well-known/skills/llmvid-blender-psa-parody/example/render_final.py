"""전체 프레임을 PNG로 뽑는다. 끊겨도 다시 실행하면 있는 프레임은 건너뛴다(열린 .blend 기준).

사용:
  blender --background scene.blend --python-exit-code 1 --python render_final.py -- [프레임 폴더] [--samples 32]

- 해상도·fps·프레임 범위는 .blend 에 든 값(장면 생성 때 timeline.json 에서 온 값)을 그대로 쓴다.
- .blend 가 바뀌면 서명이 달라져 처음부터 다시 뽑는다.
- 끝나면 render-manifest.json 을 남기고 RENDER_COMPLETE 를 출력한다.
"""
import argparse
import hashlib
import json
import os
import struct
import sys
import time

import bpy


def png_ok(path: str, width: int, height: int) -> bool:
    """PNG 서명·크기·끝 표시가 온전한지 본다."""
    if not os.path.isfile(path):
        return False
    with open(path, "rb") as fh:
        data = fh.read()
    return (
        len(data) > 1000
        and data[:8] == b"\x89PNG\r\n\x1a\n"
        and struct.unpack(">II", data[16:24]) == (width, height)
        and data[-8:-4] == b"IEND"
    )


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("frames", nargs="?", default="frames")
    ap.add_argument("--samples", type=int, default=32)
    opt = ap.parse_args(argv)

    scene = bpy.context.scene
    blend = bpy.data.filepath
    base = os.path.dirname(blend) or os.getcwd()
    folder = opt.frames if os.path.isabs(opt.frames) else os.path.join(base, opt.frames)
    os.makedirs(folder, exist_ok=True)

    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 15
    scene.render.use_file_extension = True
    scene.eevee.taa_render_samples = opt.samples
    width, height = scene.render.resolution_x, scene.render.resolution_y
    fps = scene.render.fps

    with open(blend, "rb") as fh:
        blend_hash = hashlib.sha256(fh.read()).hexdigest()
    signature = hashlib.sha256(f"{blend_hash}-{width}x{height}-{fps}fps-{opt.samples}samples".encode()).hexdigest()
    sig_path = os.path.join(folder, "_signature.txt")
    previous = ""
    if os.path.isfile(sig_path):
        with open(sig_path, encoding="utf-8") as fh:
            previous = fh.read().strip()
    fresh = previous != signature
    with open(sig_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(signature + "\n")

    markers = sorted(scene.timeline_markers, key=lambda m: m.frame)
    started = time.monotonic()
    rendered = 0
    for frame in range(scene.frame_start, scene.frame_end + 1):
        path = os.path.join(folder, f"frame_{frame:04d}.png")
        if fresh or not png_ok(path, width, height):
            scene.frame_set(frame)
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            rendered += 1
        if frame % fps == 0 or frame == scene.frame_end:
            progress = {"frame": frame, "total": scene.frame_end, "rendered": rendered,
                        "elapsed_seconds": round(time.monotonic() - started, 2)}
            print("FRAME_PROGRESS " + json.dumps(progress), flush=True)

    missing = [f for f in range(scene.frame_start, scene.frame_end + 1)
               if not png_ok(os.path.join(folder, f"frame_{f:04d}.png"), width, height)]
    if missing:
        raise SystemExit(f"온전하지 않은 프레임 {len(missing)}장: {missing[:10]}")

    manifest = {
        "schema": "llmvid-blender-render/v1",
        "frame_count": scene.frame_end - scene.frame_start + 1,
        "fps": fps,
        "duration_sec": (scene.frame_end - scene.frame_start + 1) / fps,
        "width": width,
        "height": height,
        "samples": opt.samples,
        "signature": signature,
        "rendered_this_run": rendered,
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "markers": [{"name": m.name, "frame": m.frame, "camera": m.camera.name if m.camera else None} for m in markers],
        "renderer": bpy.app.version_string,
    }
    with open(os.path.join(base, "render-manifest.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print("RENDER_COMPLETE " + json.dumps(manifest, ensure_ascii=False), flush=True)


main()
