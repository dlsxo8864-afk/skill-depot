"""Resumable frame export, preserving earlier render revisions."""
import bpy
import hashlib
import json
import struct
import time
from pathlib import Path

root = Path(__file__).resolve().parent
scene = bpy.context.scene
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.compression = 15
scene.eevee.taa_render_samples = 32
scene.render.use_file_extension = True
blend = Path(bpy.data.filepath)
signature = hashlib.sha256(blend.read_bytes() + b"1080x1920-24fps-32samples-RGB").hexdigest()
folder = root / "frames" / signature[:16]
folder.mkdir(parents=True, exist_ok=True)
progress_path = root / "render-progress.json"
started = time.monotonic()
rows = []
rendered = 0
for frame in range(scene.frame_start, scene.frame_end + 1):
    path = folder / f"frame_{frame:04}.png"
    complete = False
    if path.is_file():
        data = path.read_bytes()
        complete = len(data) > 1000 and data[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", data[16:24]) == (1080, 1920) and data[-8:-4] == b"IEND"
    if not complete:
        scene.frame_set(frame)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered += 1
    data = path.read_bytes()
    rows.append({"frame": frame, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    if frame % 24 == 0 or frame == scene.frame_end:
        progress = {"frame": frame, "total": scene.frame_end, "elapsed_seconds": round(time.monotonic() - started, 2),
                    "rendered": rendered, "folder": str(folder), "signature": signature}
        progress_path.write_text(json.dumps(progress, indent=2), encoding="utf-8")
        print("FRAME_PROGRESS " + json.dumps(progress), flush=True)
manifest = {"schema": "office-blender-render/v1", "frames": rows, "frame_count": len(rows), "fps": scene.render.fps,
            "duration_sec": len(rows) / scene.render.fps, "width": 1080, "height": 1920, "samples": 32,
            "upscaled": False, "audio": False, "frame_directory": str(folder), "blend": str(blend),
            "blend_sha256": hashlib.sha256(blend.read_bytes()).hexdigest(), "signature": signature,
            "elapsed_seconds": round(time.monotonic() - started, 3), "rendered_this_run": rendered,
            "markers": [{"name": m.name, "frame": m.frame, "camera": m.camera.name if m.camera else None} for m in scene.timeline_markers],
            "new_paid_calls": 0, "external_artwork": False, "renderer": bpy.app.version_string}
(root / "render-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("RENDER_COMPLETE " + json.dumps({k: v for k, v in manifest.items() if k != "frames"}), flush=True)
