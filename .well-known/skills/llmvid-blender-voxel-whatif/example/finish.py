"""렌더한 프레임 + (있으면) 음성·배경음 + 제목 카드·자막으로 MP4 를 만든다. 작업 폴더에서 실행.

사용: python finish.py [프레임폴더] [출력.mp4] [--timeline 타임라인.json] [--audio 음성] [--music 배경음] [--font 글꼴] [--crf 20]
- 프레임폴더: frame_0001.png 꼴이 든 폴더(render_final.py 가 만든 폴더). 기본 frames
- --timeline: 장면을 만들 때 쓴 것과 같은 파일. fps·길이·title·captions 를 여기서 읽는다. 기본은 이 스크립트 옆 timeline.example.json
- --audio: 내레이션(wav/mp3). 없으면 조용한 오디오 트랙을 넣는다
- --music: 배경음. 음량 0.3 으로 섞는다
작업 폴더에 fonts/, subs.ass 를 만든다.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fontfind import find_font, font_family  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("frames", nargs="?", default="frames")
ap.add_argument("out", nargs="?", default="out.mp4")
ap.add_argument("--timeline", default=os.path.join(HERE, "timeline.example.json"))
ap.add_argument("--audio")
ap.add_argument("--music")
ap.add_argument("--font")
ap.add_argument("--crf", type=int, default=20)
opt = ap.parse_args()
FRAMES, OUT = os.path.abspath(opt.frames), opt.out
for p in (opt.timeline, opt.audio, opt.music):
    if p and not os.path.isfile(p):
        raise SystemExit("파일이 없습니다: " + p)

with open(opt.timeline, encoding="utf-8") as fh:
    TL = json.load(fh)
FPS: int = int(TL.get("fps", 24))
W: int = int(TL.get("width", 1080))
H: int = int(TL.get("height", 1920))
TOTAL: int = round(max(float(s["end"]) for s in TL["shots"]) * FPS)
DUR: float = TOTAL / FPS
K: float = H / 1920  # 글자 크기·여백은 세로 1920 기준으로 잡고 비율로 맞춘다


def ts(t: float) -> str:
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def px(v: float) -> int:
    return round(v * K)


def clean(text: str) -> str:
    """타임라인 문구를 ASS 한 줄로. 실제 개행은 \\N 으로, 중괄호는 뺀다(ASS 태그로 읽히지 않게)."""
    return text.replace("\r", "").replace("\n", "\\N").replace("{", "").replace("}", "")


for f in range(1, TOTAL + 1):
    src = os.path.join(FRAMES, f"frame_{f:04d}.png")
    if not os.path.exists(src):
        raise SystemExit("missing " + src)

events: list[str] = []
title = TL.get("title") or {}
if title.get("text"):
    a, b = float(title.get("start", 0.0)), float(title.get("end", 2.0))
    events.append(f"Dialogue: 1,{ts(a)},{ts(min(b, DUR))},T,,0,0,0,,{{\\fad(120,220)}}{clean(title['text'])}")
for c in TL.get("captions", []):
    a, b = float(c["start"]), min(float(c["end"]), DUR)
    if b > a and c.get("text"):
        events.append(f"Dialogue: 0,{ts(a)},{ts(b)},S,,0,0,0,,{clean(c['text'])}")

vf = "[0:v]format=yuv420p,"
if events:
    font = find_font(opt.font)
    family = font_family(font)
    os.makedirs("fonts", exist_ok=True)
    shutil.copyfile(font, os.path.join("fonts", os.path.basename(font)))
    print("subtitle font:", os.path.basename(font), "|", family)
    fmt = "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding"
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2", "",
        "[V4+ Styles]", fmt,
        # S: 자막. 흰 굵은 글자 + 검은 외곽선, 화면 아래쪽 가운데(릴스 조작부를 피해 아래에서 430)
        f"Style: S,{family},{px(66)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,{px(6)},0,2,{px(80)},{px(80)},{px(430)},1",
        # T: 제목 카드. 큰 글자, 화면 위쪽 가운데
        f"Style: T,{family},{px(112)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,{px(9)},0,8,{px(60)},{px(60)},{px(360)},1",
        "", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
    ]
    with open("subs.ass", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines + events) + "\n")
    vf += "subtitles=subs.ass:fontsdir=fonts[v]"
else:
    vf += "null[v]"

# 소리: 있는 것만 입력으로 넣는다. 하나도 없으면 조용한 트랙만 넣는다
inputs = ["-framerate", str(FPS), "-start_number", "1", "-i", os.path.join(FRAMES, "frame_%04d.png")]
chains: list[str] = []
mix: list[str] = []
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
print("ok", OUT, "| frames", TOTAL, "| fps", FPS, "| narration", bool(opt.audio), "| music", bool(opt.music))
