"""Render a saved scene with resumable, content-addressed frame caches."""
import argparse, hashlib, json, struct, sys, time
from pathlib import Path
import bpy

p = argparse.ArgumentParser()
p.add_argument('--output', required=True)
p.add_argument('--width', type=int, default=1080)
p.add_argument('--height', type=int, default=1920)
p.add_argument('--samples', type=int, default=24)
p.add_argument('--frames', default='')
a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
s = bpy.context.scene
s.render.resolution_x, s.render.resolution_y = a.width, a.height
s.render.resolution_percentage = 100
s.render.image_settings.file_format = 'PNG'
s.render.image_settings.color_mode = 'RGB'
s.render.image_settings.compression = 15
if hasattr(s, 'eevee'): s.eevee.taa_render_samples = a.samples
blend = Path(bpy.data.filepath)
signature = hashlib.sha256(blend.read_bytes()+f'{a.width}:{a.height}:{a.samples}'.encode()).hexdigest()
out = Path(a.output).resolve(); out.mkdir(parents=True, exist_ok=True)
folder = out/signature[:16];folder.mkdir(exist_ok=True)
frames = [int(x) for x in a.frames.split(',')] if a.frames else range(s.frame_start,s.frame_end+1)
start=time.monotonic(); rows=[]
for frame in frames:
    assert s.frame_start <= frame <= s.frame_end
    target=folder/f'frame_{frame:04d}.png'
    data=target.read_bytes() if target.exists() else b''
    valid=len(data)>1000 and data[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',data[16:24])==(a.width,a.height) and data[-8:-4]==b'IEND'
    if not valid:
        s.frame_set(frame);s.render.filepath=str(target);bpy.ops.render.render(write_still=True)
    rows.append({'frame':frame,'bytes':target.stat().st_size})
    if frame%24==0:
        (out/'progress.json').write_text(json.dumps({'frame':frame,'end':s.frame_end,'seconds':round(time.monotonic()-start,1)}))
manifest={'status':'completed','cache':signature[:16],'blend':blend.name,'blendSha256':hashlib.sha256(blend.read_bytes()).hexdigest(),'width':a.width,'height':a.height,'fps':s.render.fps,'samples':a.samples,'frames':rows,'durationSeconds':(s.frame_end-s.frame_start+1)/s.render.fps,'elapsedSeconds':round(time.monotonic()-start,2)}
(out/('proof-manifest.json' if a.frames else 'render-manifest.json')).write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('RENDER_COMPLETE '+json.dumps({k:v for k,v in manifest.items() if k!='frames'}),flush=True)
