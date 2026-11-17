"""렌더한 프레임 + 화면 위 그림(overlay) + 자막 + (있으면) 음성·효과음으로 MP4 를 만든다. 작업 폴더에서 실행.

사용: python finish.py [프레임폴더] [step] [출력.mp4] [--audio 음성] [--sfx auto|on|off] [--font 글꼴] [--crf 22]
- 프레임폴더: f0001.png 꼴이 든 폴더. 절대 경로도 된다. 기본 frames
- step: 렌더할 때 건너뛴 간격. 1 이면 24fps 그대로, 2 면 12fps 로 뽑은 것을 24fps 로 편다. 기본 1
- --audio: 내레이션(wav/mp3). 없으면 소리 없는 결과(조용한 오디오 트랙)를 만든다
- --sfx: 효과음(전송·알림·도장). auto 는 --audio 가 있을 때만 넣는다
자막·효과음 시각은 script.json(plan.SUBS, plan.SFX), 얹을 그림은 plan.OVERLAYS 에서 읽는다.
작업 폴더에 fonts/, subs.ass 를, step 이 2 이상이면 seq_<프레임폴더 이름>/ 도 만든다.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan  # noqa: E402
from fontfind import find_font, font_family  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("frames", nargs="?", default="frames")
ap.add_argument("step", nargs="?", type=int, default=1)
ap.add_argument("out", nargs="?", default="out.mp4")
ap.add_argument("--audio")
ap.add_argument("--sfx", choices=("auto", "on", "off"), default="auto")
ap.add_argument("--font")
ap.add_argument("--crf", type=int, default=22)
opt = ap.parse_args()
FRAMES, STEP, OUT = os.path.abspath(opt.frames), opt.step, opt.out
if opt.audio and not os.path.isfile(opt.audio):
    raise SystemExit("파일이 없습니다: " + opt.audio)
FPS, TOTAL, DUR = plan.FPS, plan.TOTAL, plan.DUR
SUB_SIZE = getattr(plan, "SUB_SIZE", 74)  # 자막 글자 크기
SUB_TOP = getattr(plan, "SUB_TOP", 1330)  # 자막 윗줄의 높이(위에서부터 픽셀)


def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


want = [os.path.join(FRAMES, f"f{f:04d}.png") for f in range(1, TOTAL + 1, STEP)]
miss = [p for p in want if not os.path.exists(p)]
if miss:
    raise SystemExit(f"프레임이 {len(miss)}장 없습니다. 첫 번째: {miss[0]}")
if STEP == 1:
    pattern = os.path.join(FRAMES, "f%04d.png")
else:  # 빈 번호 없이 다시 센다(ffmpeg 는 이어진 번호만 읽는다)
    seq = os.path.join(os.getcwd(), "seq_" + os.path.basename(FRAMES))
    os.makedirs(seq, exist_ok=True)
    for old in glob.glob(os.path.join(seq, "s[0-9][0-9][0-9][0-9].png")):
        os.remove(old)
    for n, src in enumerate(want, 1):
        shutil.copyfile(src, os.path.join(seq, f"s{n:04d}.png"))
    pattern = os.path.join(seq, "s%04d.png")

inputs = ["-framerate", f"{FPS}/{STEP}", "-start_number", "1", "-i", pattern]
idx = 1
chains = []
# 화면 위 그림: plan.OVERLAYS = [(overlay 폴더 안 파일 이름, 시작 초, 끝 초), …]
last = "[base]"
chains.append(f"[0:v]fps={FPS},scale=1080:1920[base]")
for name, a, b in getattr(plan, "OVERLAYS", []):
    path = os.path.join("overlay", name)
    if not os.path.isfile(path):
        raise SystemExit("얹을 그림이 없습니다(먼저 cards.py): " + path)
    inputs += ["-loop", "1", "-t", str(DUR), "-i", path]
    chains.append(f"{last}[{idx}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[o{idx}]")
    last = f"[o{idx}]"
    idx += 1
if plan.SUBS:
    font = find_font(opt.font)
    family = font_family(font)
    os.makedirs("fonts", exist_ok=True)
    shutil.copyfile(font, os.path.join("fonts", os.path.basename(font)))
    print("subtitle font:", font, "|", family)
    lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "", "[V4+ Styles]", "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding", f"Style: S,{family},{SUB_SIZE},&H00FFFFFF,&H00FFFFFF,&H00181418,&H00000000,1,0,0,0,100,100,0,0,1,7,0,8,90,90,{SUB_TOP},1", "", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
    lines += [f"Dialogue: 0,{ts(a)},{ts(b)},S,,0,0,0,,{t}" for a, b, t in plan.SUBS]
    open("subs.ass", "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    chains.append(f"{last}subtitles=subs.ass:fontsdir=fonts[v]")
else:
    chains.append(f"{last}null[v]")

# 소리: 있는 것만 입력으로 넣고 필터 그래프를 짠다
mix = []
if opt.audio:
    inputs += ["-i", opt.audio]
    chains.append(f"[{idx}:a]aresample=48000,pan=stereo|c0=c0|c1=c0,apad=whole_dur={DUR}[n]")
    mix.append("[n]")
    idx += 1


def sfx(tag, src_args, secs, volume):
    """효과음 한 가지를 secs(초)마다 넣는다."""
    global idx, inputs
    if not secs:
        return
    inputs += src_args
    labels = [f"[{tag}{i}]" for i in range(len(secs))]
    chains.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,volume={volume},asplit={len(secs)}" + "".join(labels))
    for lab, sec in zip(labels, secs):
        ms = round(sec * 1000)
        out = lab[:-1] + "d]"
        chains.append(f"{lab}adelay={ms}|{ms}{out}")
        mix.append(out)
    idx += 1


if opt.sfx == "on" or (opt.sfx == "auto" and opt.audio):
    S = plan.SFX
    sfx("s", ["-f", "lavfi", "-t", "0.2", "-i", "aevalsrc='0.6*sin(2*PI*(700+2600*t)*t)*exp(-22*t)':s=48000"], S.get("send", []), 0.5)  # 전송 '톡'
    sfx("b", ["-f", "lavfi", "-t", "1.3", "-i", "aevalsrc='0.5*sin(2*PI*150*t)*(0.5+0.5*sin(2*PI*20*t))':s=48000"], S.get("buzz", []), 0.5)  # 알림 진동
    sfx("h", ["-f", "lavfi", "-t", "0.5", "-i", "aevalsrc='0.9*sin(2*PI*80*t)*exp(-9*t)+0.5*random(0)*exp(-22*t)':s=48000"], S.get("hit", []), 0.7)  # 도장 '쿵'

n_sfx = len(mix) - (1 if opt.audio else 0)
SILENT = ["-f", "lavfi", "-t", str(DUR), "-i", "anullsrc=r=48000:cl=stereo"]
if mix:
    if not opt.audio:  # 내레이션이 없으면 전체 길이만큼의 조용한 바탕 트랙을 같이 섞어 길이를 맞춘다
        inputs += SILENT
        mix.insert(0, f"[{idx}:a]")
        idx += 1
    norm = "loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000," if opt.audio else ""
    chains.append("".join(mix) + f"amix=inputs={len(mix)}:duration=longest:normalize=0,{norm}atrim=0:{DUR}[a]")
    amap = "[a]"
else:
    inputs += SILENT
    amap = f"{idx}:a"

cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chains),
       "-map", "[v]", "-map", amap, "-t", str(DUR), "-c:v", "libx264", "-crf", str(opt.crf), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", OUT]
subprocess.run(cmd, check=True)
print("ok", OUT, "| frames", len(want), "| overlays", len(getattr(plan, "OVERLAYS", [])), "| narration", bool(opt.audio), "| sfx", n_sfx)
