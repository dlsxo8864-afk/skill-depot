"""Reuse the approved EP3 edit, replacing only character footage."""
from pathlib import Path
import json, shutil, subprocess
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'episodes/ep3';out.mkdir(parents=True,exist_ok=True)
render=json.loads((ROOT/'demo/render/render-manifest.json').read_text(encoding='utf-8'))
assert len(render['frames'])==192
video=ROOT/'remotion/public/video';video.mkdir(exist_ok=True)
for name,start,length in [('hook',36,48),('desk',8,43),('reaction',93,100)]:
    subprocess.run(['ffmpeg','-y','-v','error','-framerate','24','-start_number',str(start),'-i',str(ROOT/'demo/render'/render['cache']/'frame_%04d.png'),'-frames:v',str(length),'-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(video/f'{name}.mp4')],check=True)
final=out/'EP3-블렌더-v2.mp4'
subprocess.run(['node',str(ROOT/'remotion/node_modules/@remotion/cli/remotion-cli.js'),'render','src/index.tsx','OfficeStoryEP3Clay',str(final),'--concurrency','2','--codec','h264','--crf','18'],cwd=ROOT/'remotion',check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(final)],text=True))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (v['width'],v['height'],int(v['nb_read_frames']))==(1080,1920,720)
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(final),'-f','null','-'],check=True)
(out/'final-probe.json').write_text(json.dumps(probe,indent=2),encoding='utf-8')
print(json.dumps({'status':'completed','episode':3,'frames':720,'videoSeconds':30}))
