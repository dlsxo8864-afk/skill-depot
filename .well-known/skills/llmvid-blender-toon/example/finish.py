"""렌더한 프레임 + (있으면) 음성·효과음 + 자막으로 MP4 를 만든다. 작업 폴더에서 실행.

사용: python finish.py [프레임폴더] [step] [출력.mp4] [--audio 음성] [--sfx-send 효과음] [--sfx auto|on|off]
                       [--font 글꼴] [--grain auto|on|off] [--crf 22]
- 프레임폴더: f0001.png 꼴이 든 폴더. 절대 경로도 된다. 기본 frames
- step: 렌더할 때 건너뛴 간격. 2 면 12fps 로 뽑은 f0001, f0003 … 을 24fps 로 편다. 기본 2
- --audio: 내레이션(wav/mp3). 없으면 소리 없는 결과(조용한 오디오 트랙)를 만든다
- --sfx: 효과음(전송음·진동·도장). auto 는 --audio 가 있을 때만 넣는다
- --sfx-send: 메시지 전송 효과음 파일. 없으면 짧은 소리를 코드로 합성한다
- --grain: 필름 그레인·비네트. auto 는 step 이 2(실사판)일 때만 넣는다
작업 폴더에 seq_<프레임폴더 이름>/, fonts/, subs.ass 를 만든다.
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
ap.add_argument("step", nargs="?", type=int, default=2)
ap.add_argument("out", nargs="?", default="out.mp4")
ap.add_argument("--audio")
ap.add_argument("--sfx-send")
ap.add_argument("--sfx", choices=("auto", "on", "off"), default="auto")
ap.add_argument("--font")
ap.add_argument("--grain", choices=("auto", "on", "off"), default="auto")
ap.add_argument("--crf", type=int, default=22)
opt = ap.parse_args()
FRAMES, STEP, OUT = os.path.abspath(opt.frames), opt.step, opt.out
for p in (opt.audio, opt.sfx_send):
    if p and not os.path.isfile(p):
        raise SystemExit("파일이 없습니다: " + p)

FPS, TOTAL, DUR = plan.FPS, plan.TOTAL, plan.DUR
SUBS = plan.SUBS  # 자막 (시작 초, 끝 초, 문구): script.json 의 subs. 비어 있으면 자막 없이 만든다
# 효과음 시각(밀리초): script.json 의 sfx(초). 화면의 전송·알림·도장과 같은 때다
SEND_MS = [round(t * 1000) for t in plan.SFX.get("send", [])]
BUZZ_MS = [round(t * 1000) for t in plan.SFX.get("buzz", [])]
HIT_MS = [round(t * 1000) for t in plan.SFX.get("hit", [])]


def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


# 프레임을 빈 번호 없이 다시 센다(ffmpeg 는 이어진 번호만 읽는다)
SEQ = os.path.join(os.getcwd(), "seq_" + os.path.basename(FRAMES))
os.makedirs(SEQ, exist_ok=True)
for old in glob.glob(os.path.join(SEQ, "s[0-9][0-9][0-9][0-9].png")):
    os.remove(old)
n = 0
for f in range(1, TOTAL + 1, STEP):
    src = os.path.join(FRAMES, f"f{f:04d}.png")
    if not os.path.exists(src):
        raise SystemExit("missing " + src)
    n += 1
    shutil.copyfile(src, os.path.join(SEQ, f"s{n:04d}.png"))

grain = opt.grain == "on" or (opt.grain == "auto" and STEP == 2)
vf = "[0:v]fps=24," + ("noise=alls=5:allf=t,vignette=PI/6," if grain else "")
if SUBS:
    font = find_font(opt.font)
    family = font_family(font)
    os.makedirs("fonts", exist_ok=True)
    shutil.copyfile(font, os.path.join("fonts", os.path.basename(font)))
    print("subtitle font:", font, "|", family)
    lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "", "[V4+ Styles]", "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding", f"Style: S,{family},74,&H00FFFFFF,&H00FFFFFF,&H00181418,&H00000000,1,0,0,0,100,100,0,0,1,7,0,8,90,90,1290,1", "", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
    lines += [f"Dialogue: 0,{ts(a)},{ts(b)},S,,0,0,0,,{t}" for a, b, t in SUBS]
    open("subs.ass", "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    vf += "subtitles=subs.ass:fontsdir=fonts[v]"
else:
    vf += "null[v]"

# 소리: 있는 것만 입력으로 넣고 필터 그래프를 짠다
inputs = ["-framerate", f"{FPS}/{STEP}", "-i", os.path.join(SEQ, "s%04d.png")]
chains, mix = [], []
idx = 1
if opt.audio:
    inputs += ["-i", opt.audio]
    chains.append(f"[{idx}:a]aresample=48000,pan=stereo|c0=c0|c1=c0,apad=whole_dur={DUR}[n]")
    mix.append("[n]")
    idx += 1


def sfx(tag, src_args, times, volume):
    """효과음 한 가지를 times(밀리초)마다 넣는다."""
    global idx, inputs
    if not times:
        return
    inputs += src_args
    labels = [f"[{tag}{i}]" for i in range(len(times))]
    chains.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,volume={volume},asplit={len(times)}" + "".join(labels))
    for lab, ms in zip(labels, times):
        out = lab[:-1] + "d]"
        chains.append(f"{lab}adelay={ms}|{ms}{out}")
        mix.append(out)
    idx += 1


if opt.sfx == "on" or (opt.sfx == "auto" and opt.audio):
    if opt.sfx_send:
        sfx("s", ["-i", opt.sfx_send], SEND_MS, 0.5)
    else:  # 전송음이 없으면 짧은 '톡' 소리를 합성한다
        sfx("s", ["-f", "lavfi", "-t", "0.2", "-i", "aevalsrc='0.6*sin(2*PI*(700+2600*t)*t)*exp(-22*t)':s=48000"], SEND_MS, 0.5)
    # 휴대폰 진동음은 저음을 코드로 합성한다
    sfx("b", ["-f", "lavfi", "-t", "1.3", "-i", "aevalsrc='0.5*sin(2*PI*150*t)*(0.5+0.5*sin(2*PI*20*t))':s=48000"], BUZZ_MS, 0.5)
    # 도장 찍는 소리: 낮은 '쿵' + 짧은 잡음
    sfx("h", ["-f", "lavfi", "-t", "0.5", "-i", "aevalsrc='0.9*sin(2*PI*80*t)*exp(-9*t)+0.5*random(0)*exp(-22*t)':s=48000"], HIT_MS, 0.7)

n_sfx = len(mix) - (1 if opt.audio else 0)
SILENT = ["-f", "lavfi", "-t", str(DUR), "-i", "anullsrc=r=48000:cl=stereo"]
if mix:
    if not opt.audio:  # 내레이션이 없으면 전체 길이만큼의 조용한 바탕 트랙을 같이 섞어 길이를 맞춘다
        inputs += SILENT
        mix.insert(0, f"[{idx}:a]")
        idx += 1
    # loudnorm 은 내레이션이 있을 때만 건다(효과음만 있으면 지나치게 키운다). loudnorm 뒤에는 48kHz 로 되돌린다
    norm = "loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000," if opt.audio else ""
    chains.append("".join(mix) + f"amix=inputs={len(mix)}:duration=longest:normalize=0,{norm}atrim=0:{DUR}[a]")
    amap = "[a]"
else:  # 소리가 하나도 없으면 조용한 트랙만 넣는다
    inputs += SILENT
    amap = f"{idx}:a"

cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join([vf] + chains),
       "-map", "[v]", "-map", amap, "-t", str(DUR), "-c:v", "libx264", "-crf", str(opt.crf), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", OUT]
subprocess.run(cmd, check=True)
print("ok", OUT, "| frames", n, "| narration", bool(opt.audio), "| sfx", n_sfx)
