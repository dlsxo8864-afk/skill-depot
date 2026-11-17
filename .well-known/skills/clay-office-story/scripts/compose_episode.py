"""Encode genuine Blender frames and attach measured voice/captions with Remotion."""
import argparse,json,subprocess,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--ep',type=int,choices=[4,5,6],required=True);a=p.parse_args()
folder=ROOT/'episodes'/f'ep{a.ep}';tl=json.loads((folder/'timeline.json').read_text(encoding='utf-8'));render=json.loads((folder/'render/render-manifest.json').read_text(encoding='utf-8'))
assert len(render['frames'])==tl['frames']
assert [x['frame'] for x in render['frames']]==list(range(1,tl['frames']+1))
assert render['blendSha256']==hashlib.sha256((folder/'scene.blend').read_bytes()).hexdigest(), 'Render belongs to an older scene'
public=ROOT/'remotion/public/media';public.mkdir(exist_ok=True)
subprocess.run(['ffmpeg','-y','-v','error','-framerate','24','-start_number','1','-i',str(folder/'render'/render['cache']/'frame_%04d.png'),'-frames:v',str(tl['frames']),'-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(public/f'ep{a.ep}.mp4')],check=True)
shutil.copy2(folder/'narration.wav',public/f'ep{a.ep}.wav')
props={'video':f'media/ep{a.ep}.mp4','audio':f'media/ep{a.ep}.wav','captions':json.loads((folder/'captions.json').read_text(encoding='utf-8')),'frames':tl['frames']}
prop_path=folder/'remotion-props.json';prop_path.write_text(json.dumps(props,ensure_ascii=False),encoding='utf-8')
cmd=['node',str(ROOT/'remotion/node_modules/@remotion/cli/remotion-cli.js'),'render','src/index.tsx','ClayStory',str(folder/f'EP{a.ep}-블렌더-v2.mp4'),'--props',str(prop_path),'--concurrency','2','--codec','h264','--crf','18']
subprocess.run(cmd,cwd=ROOT/'remotion',check=True)
final=folder/f'EP{a.ep}-블렌더-v2.mp4'
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(final)],text=True))
v=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],int(v['nb_read_frames']))==(1080,1920,tl['frames'])
assert v['r_frame_rate']=='24/1' and audio['codec_name']=='aac'
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(final),'-f','null','-'],check=True)
(folder/'final-probe.json').write_text(json.dumps(probe,indent=2),encoding='utf-8')
(folder/'delivery-check.json').write_text(json.dumps({'blendSha256':render['blendSha256'],'videoSha256':hashlib.sha256(final.read_bytes()).hexdigest(),'frames':tl['frames'],'resolution':[1080,1920],'fps':24,'decodePassed':True},indent=2),encoding='utf-8')
print(json.dumps({'status':'completed','episode':a.ep,'file':final.name,'frames':tl['frames'],'duration':v['duration']}))

