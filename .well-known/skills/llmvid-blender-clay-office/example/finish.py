"""렌더한 프레임 + (있으면) 음성·배경음 + 자막으로 MP4 를 만든다. 작업 폴더에서 실행.

사용: python finish.py [프레임폴더] [출력.mp4] [--audio 음성] [--music 배경음] [--font 글꼴] [--crf 20] [--script 대본.json]
- 프레임폴더: frame_0001.png 꼴이 든 폴더(render_final.py 가 알려 준 폴더). 절대 경로도 된다. 기본 frames
- --audio: 내레이션(wav/mp3). 없으면 소리 없는 결과(조용한 오디오 트랙)를 만든다
- --music: 배경음. 음량 0.3 으로 섞는다
작업 폴더에 fonts/, subs.ass 를 만든다.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontfind import find_font, font_family  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("frames", nargs="?", default="frames")
ap.add_argument("out", nargs="?", default="out.mp4")
ap.add_argument("--audio")
ap.add_argument("--music")
ap.add_argument("--font")
ap.add_argument("--script", help="대본 JSON. 기본은 이 스크립트 옆의 script.json")
ap.add_argument("--crf", type=int, default=20)
opt = ap.parse_args()
FRAMES, OUT = os.path.abspath(opt.frames), opt.out
for p in (opt.audio, opt.music):
    if p and not os.path.isfile(p):
        raise SystemExit("파일이 없습니다: " + p)

# 길이·자막은 대본(script.json)에서 읽는다. 다른 대본은 --script 로 준다
with open(opt.script or os.path.join(os.path.dirname(os.path.abspath(__file__)), "script.json"), encoding="utf-8") as _f:
    _S = json.load(_f)
FPS = int(_S.get("fps", 24))
TOTAL = int(_S["frames"])
DUR = TOTAL / FPS
SUBS = [tuple(x) for x in _S.get("subs", [])]  # (시작 초, 끝 초, 문구). \\N 은 줄바꿈

def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


for f in range(1, TOTAL + 1):
    src = os.path.join(FRAMES, f"frame_{f:04d}.png")
    if not os.path.exists(src):
        raise SystemExit("missing " + src)

vf = "[0:v]format=yuv420p,"
if SUBS:
    font = find_font(opt.font)
    family = font_family(font)
    os.makedirs("fonts", exist_ok=True)
    shutil.copyfile(font, os.path.join("fonts", os.path.basename(font)))
    print("subtitle font:", font, "|", family)
    lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "", "[V4+ Styles]", "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding", f"Style: S,{family},68,&H00FFFFFF,&H00FFFFFF,&H00241E18,&H00000000,1,0,0,0,100,100,0,0,1,5,1,2,90,90,300,1", "", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
    lines += [f"Dialogue: 0,{ts(a)},{ts(b)},S,,0,0,0,,{t}" for a, b, t in SUBS]
    open("subs.ass", "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    vf += "subtitles=subs.ass:fontsdir=fonts[v]"
else:
    vf += "null[v]"

# 소리: 있는 것만 입력으로 넣는다. 하나도 없으면 조용한 트랙만 넣는다
inputs = ["-framerate", str(FPS), "-start_number", "1", "-i", os.path.join(FRAMES, "frame_%04d.png")]
chains, mix = [], []
idx = 1
if opt.audio:
    inputs += ["-i", opt.audio]
    chains.append(f"[{idx}:a]aresample=48000,pan=stereo|c0=c0|c1=c0,loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000,apad=whole_dur={DUR}[n]")
    mix.append("[n]")
    idx += 1
if opt.music:
    inputs += ["-i", opt.music]
    chains.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.3,apad=whole_dur={DUR}[m]")
    mix.append("[m]")
    idx += 1
if mix:
    chains.append("".join(mix) + f"amix=inputs={len(mix)}:duration=longest:normalize=0,atrim=0:{DUR}[a]")
    amap = "[a]"
else:
    inputs += ["-f", "lavfi", "-t", str(DUR), "-i", "anullsrc=r=48000:cl=stereo"]
    amap = f"{idx}:a"

cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join([vf] + chains),
       "-map", "[v]", "-map", amap, "-frames:v", str(TOTAL), "-t", str(DUR), "-c:v", "libx264", "-crf", str(opt.crf),
       "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k", OUT]
subprocess.run(cmd, check=True)
print("ok", OUT, "| frames", TOTAL, "| narration", bool(opt.audio), "| music", bool(opt.music))
