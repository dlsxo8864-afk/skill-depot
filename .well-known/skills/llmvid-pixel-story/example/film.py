"""픽셀 애니메이션 예제(공통 예제 대본 「점심 메뉴 정하는 법」 15초, 1080x1920). 엔진은 같은 폴더의 pixelvid.py(MIT), 글꼴은 fonts/Galmuri11(OFL).
모든 프레임은 시간 함수다. 대본(길이·대화·시각·자막)은 같은 폴더의 script.json 에서 읽는다. 이 파일에는 그리는 방법만 있다.
- 대본 파일을 바꾸려면 script.json 을 고치거나 환경변수 LLMVID_SCRIPT 로 다른 파일을 준다.
- 장면 함수 하나가 대본의 구간(beats) 하나다. 구간 id(hook, ask, wait, decide, punch)가 달라지면 장면 함수를 맞춰 고친다.
사용: python -X utf8 film.py sheet --out <폴더>   (검수용 접촉 시트 2장)
      python -X utf8 film.py render --out <폴더>  (video_silent.mp4 + music.wav)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from pixelvid import Movie, Song, hrand, seg, ease_out, ease_back, rain  # noqa: E402

INK, PLUM, RED, ORG, YEL, LIME, GRN, TEAL = "#1a1c2c", "#5d275d", "#b13e53", "#ef7d57", "#ffcd75", "#a7f070", "#38b764", "#257179"
NAVY, BLUE, SKY, CYAN, WHITE, G1, G2, G3 = "#29366f", "#3b5dc9", "#41a6f6", "#73eff7", "#f4f4f4", "#94b0c2", "#566c86", "#333c57"
W, H = 180, 320
# 대본
with open(os.environ.get("LLMVID_SCRIPT") or os.path.join(HERE, "script.json"), encoding="utf-8") as _f:
    S = json.load(_f)
B = {b["id"]: b for b in S["beats"]}
DUR = {b["id"]: b["end"] - b["start"] for b in S["beats"]}
NAME = {c["id"]: c["name"] for c in S["cast"]}
ME, LEAD = S["cast"][0]["id"], S["cast"][-1]["id"]  # 첫 인물이 휴대폰 주인, 마지막 인물이 정하는 사람
ME_KIND = "me"  # bust() 의 인물 그림 종류
ROOM = S.get("chat_room", "")
CHAT = sorted((c["t"], c["who"], c["text"]) for b in S["beats"] for c in b.get("chat", []))
SUBS = [tuple(x) for x in S.get("subs", [])]
SFX = S.get("sfx", {})
STAMP = next((b["stamp"] for b in S["beats"] if "stamp" in b), None)
RESULT = next((b["result"] for b in S["beats"] if "result" in b), "")
mv = Movie(W, H, fps=S.get("fps", 24), scale=6, pal="sweetie16", strict_palette=True)

_fonts = {b: ImageFont.truetype(os.path.join(HERE, "fonts", f"Galmuri11{'-Bold' if b else ''}.ttf"), 12) for b in (False, True)}
_cache = {}


def mask(s, bold=False):
    key = (s, bold)
    if key not in _cache:
        f = _fonts[bold]
        w = int(f.getlength(s)) + 2
        im = Image.new("1", (max(w, 1), 16), 0)
        d = ImageDraw.Draw(im)
        d.fontmode = "1"
        d.text((0, 0), s, font=f, fill=1)
        px = im.load()
        pts = [(x, y) for y in range(16) for x in range(im.width) if px[x, y]]
        _cache[key] = (pts, w - 2)
    return _cache[key]


def tw(s, bold=False):
    return mask(s, bold)[1]


def kt(c, s, x, y, col, align="left", outline=None, bold=False):
    pts, w = mask(s, bold)
    x = int(x - (w / 2 if align == "center" else w if align == "right" else 0))
    y = int(y)
    if outline:
        done = set()
        for px, py in pts:
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
                p = (px + dx, py + dy)
                if p not in done:
                    done.add(p)
                    c.px(x + p[0], y + p[1], outline)
    for px, py in pts:
        c.px(x + px, y + py, col)


def bust(c, cx, by, who, expr, T, s=2):
    """인물 상반신. who: me|boss, s: 정수 배율"""
    def R(x, y, w, h, col):
        c.rect(int(cx + x * s), int(by + y * s), int(w * s), int(h * s), col)

    skin, shade = YEL, ORG
    if who == "me":
        R(-17, -14, 34, 14, BLUE)
        R(-5, -14, 10, 5, WHITE)
        R(-4, -18, 8, 5, shade)
        R(-14, -44, 28, 34, PLUM)          # 뒷머리
        R(-11, -40, 22, 24, skin)
        R(-12, -44, 24, 7, PLUM)
        R(-13, -40, 4, 22, PLUM)
        R(9, -40, 4, 22, PLUM)
    else:
        R(-20, -14, 40, 14, NAVY)
        R(-6, -14, 12, 6, WHITE)
        R(-2, -13, 4, 13, RED)
        R(-5, -18, 10, 5, shade)
        R(-13, -44, 26, 28, skin)
        R(-14, -46, 28, 7, G2)
        R(-14, -44, 3, 9, G2)
        R(11, -44, 3, 9, G2)
    blink = hrand("b", int(T * 2)) > 0.82 and (T * 2) % 1 < 0.14
    ey = -31
    if who == "boss":
        for ex in (-10, 2):
            c.rect(int(cx + ex * s), int(by + (ey - 3) * s), int(9 * s), int(7 * s), INK, fill=False)
        R(-1, ey, 2, 1, INK)
        if expr == "angry":
            R(-11, ey - 6, 9, 2, INK)
            R(2, ey - 6, 9, 2, INK)
        else:
            R(-11, ey - 5, 9, 1, INK)
            R(2, ey - 5, 9, 1, INK)
    eh = 1 if blink else (6 if expr in ("shock", "open") else 4)
    for ex in (-8, 5):
        R(ex, ey - eh // 2, 3, eh, INK)
    if who == "me" and expr in ("worry", "shock"):
        R(-9, ey - 6, 5, 1, INK)
        R(4, ey - 6, 5, 1, INK)
    my = -21
    talk = int(T * 9) % 2 == 0
    if expr in ("shock",):
        R(-3, my - 1, 6, 5, RED)
    elif expr == "smile":
        R(-5, my, 10, 1, RED)
        R(-6, my - 1, 2, 1, RED)
        R(4, my - 1, 2, 1, RED)
    elif expr in ("talk", "angry"):
        R(-4, my, 8, 3 if talk else 1, RED if who == "me" else INK)
    else:
        R(-3, my + 1, 6, 1, INK)
    if expr == "worry":
        y = int(by + (-40 + (T * 16) % 8) * s)
        c.rect(int(cx + 14 * s), y, 2 * s, 4 * s, SKY)


def office(c, T, dark=False):
    c.clear(G3 if not dark else INK)
    for x in range(0, W, 30):
        c.rect(x, 0, 1, 170, INK if not dark else NAVY)
    c.rect(18, 26, 62, 76, CYAN if not dark else NAVY)
    c.rect(18, 26, 62, 76, INK, fill=False)
    c.rect(48, 26, 2, 76, INK)
    c.rect(18, 62, 62, 2, INK)
    c.rect(105, 44, 58, 40, G2)
    c.rect(109, 48, 50, 32, TEAL if int(T * 4) % 8 else SKY)
    c.rect(130, 84, 8, 10, G2)
    c.rect(0, 150, W, 170, ORG if not dark else PLUM)
    c.rect(0, 150, W, 3, YEL if not dark else RED)


def chat(c, x0, y0, w, msgs, t):
    """msgs: (등장초, 'in'|'me', 이름, 글)"""
    y = y0
    for at, side, name, text in msgs:
        if t < at:
            continue
        pop = min(1.0, (t - at) / 0.12)
        bw = tw(text) + 10
        bh = 17
        if side == "in":
            c.rect(x0 + 2, y + 1, 13, 13, ORG if name == NAME.get(LEAD) else SKY)
            kt(c, name, x0 + 18, y - 1, G3)
            yb = y + 12
            bx = x0 + 18
            col, tx = WHITE, INK
        else:
            yb = y + 2
            bx = x0 + w - bw - 3
            col, tx = YEL, INK
        if pop >= 1:
            c.rect(bx, yb, bw, bh, col)
            c.rect(bx - 1, yb + 1, bw + 2, bh - 2, col)
            kt(c, text, bx + 5, yb + 2, tx)
        else:
            c.rect(bx + bw // 4, yb + 3, bw // 2, bh - 6, col)
        y += 33 if side == "in" else 23


def phone(c, x, y, w, h):
    c.rect(x - 4, y - 8, w + 8, h + 16, INK)
    c.rect(x - 3, y - 7, w + 6, h + 14, G3)
    c.rect(x, y, w, h, "#94b0c2")
    c.rect(x + w // 2 - 10, y - 5, 20, 2, INK)


def input_bar(c, x, y, w, text, T):
    c.rect(x, y, w, 20, WHITE)
    c.rect(x + w - 19, y + 3, 15, 14, YEL if text else G1)
    kt(c, text, x + 5, y + 4, INK)
    if int(T * 3) % 2 == 0:
        c.rect(x + 6 + tw(text), y + 4, 1, 12, INK)


def type_slice(s, t, a, b):
    n = int(len(s) * max(0.0, min(1.0, (t - a) / max(0.01, b - a))))
    return s[:n]


# ── 대본 풀이 ─────────────────────────────────────────────────────────
# 장면 하나가 대본의 구간 하나다. 길이·문구·시각은 전부 script.json 에서 읽는다(S, BEAT, CHAT …).
# 장면 함수 안의 t 는 그 장면이 시작한 뒤의 초, x.T 는 영상 전체의 초다.
def lt(sec, bid):
    """영상 전체의 초 → 구간 bid 안에서의 초."""
    return sec - B[bid]["start"]


def room(c, t, upto, x):
    """휴대폰 단톡 화면. upto(영상 전체 초)까지 온 대화를 보여 주고, 내 다음 메시지는 보내기 전에 입력창에 쳐진다."""
    c.clear(NAVY)
    phone(c, 10, 22, 160, 248)
    c.rect(10, 22, 160, 22, G2)
    kt(c, ROOM, 90, 26, WHITE, "center")
    msgs = [(at, "me" if who == ME else "in", NAME.get(who, who), text) for at, who, text in CHAT if at <= upto]
    msgs = msgs[-5:]  # 화면에 다섯 줄까지
    chat(c, 16, 52, 148, msgs, x.T)
    nxt = next((m for m in CHAT if m[1] == ME and m[0] > x.T), None)
    typed = type_slice(nxt[2], x.T, nxt[0] - 1.4, nxt[0] - 0.25) if nxt and x.T >= nxt[0] - 1.4 else ""
    input_bar(c, 14, 244, 152, typed, x.T)


def chip(c, text, cx, y, col=YEL):
    w = tw(text, True) + 12
    c.rect(cx - w // 2, y, w, 18, INK)
    c.rect(cx - w // 2 + 1, y + 1, w - 2, 16, col)
    kt(c, text, cx, y + 3, INK, "center", bold=True)


@mv.scene(DUR["hook"], "hook")
def s_hook(c, x):
    """묻기: 단톡에 내 질문을 치고 보낸다."""
    room(c, x.t, x.T, x)
    chip(c, B["hook"].get("keyword", ""), 146, 4)
    sent = next((at for at, who, _ in CHAT if who == ME), None)
    if sent is not None and x.T > sent + 0.2:
        k = int((x.T - sent) * 8) % 2
        kt(c, "?", 150, 150 - k, RED, outline=WHITE, bold=True)


@mv.scene(DUR["ask"], "ask")
def s_ask(c, x):
    """대답: 답이 올 때마다 화면이 살짝 흔들리고 키워드가 튀어나온다."""
    room(c, x.t, x.T, x)
    for at, who, text in CHAT:
        if who != ME and at <= x.T < at + 0.9 and B["ask"]["start"] <= at < B["ask"]["end"]:
            k = ease_back(seg(x.T, at, at + 0.25))
            chip(c, B["ask"].get("keyword", ""), 90, int(206 - 14 * k), ORG if who == LEAD else SKY)


@mv.scene(DUR["wait"], "wait")
def s_wait(c, x):
    """기다림: 시계가 돌고 눈금이 찬다. 나는 지쳐 간다."""
    t, d = x.t, DUR["wait"]
    k = seg(t, 0.2, d - 0.3)
    office(c, x.T, dark=k > 0.7)
    # 시계: 대본의 clock.from → clock.to
    (h0, m0), (h1, m1) = [tuple(int(v) for v in B["wait"]["clock"][key].split(":")) for key in ("from", "to")]
    a0, a1 = h0 % 12 * 60 + m0, h1 % 12 * 60 + m1
    if a1 < a0:
        a1 += 720
    now = a0 + (a1 - a0) * k
    cx, cy, r = 90, 62, 34
    c.circ(cx, cy, r + 3, INK)
    c.circ(cx, cy, r, WHITE)
    for i in range(12):
        a = math.radians(i * 30)
        c.rect(int(cx + math.sin(a) * (r - 4)) - 1, int(cy - math.cos(a) * (r - 4)) - 1, 2, 2, G3)
    for ang, ln, col in ((now / 60 * 2 * math.pi, r - 8, INK), (now / 720 * 2 * math.pi, r - 17, RED)):
        c.line(cx, cy, int(cx + math.sin(ang) * ln), int(cy - math.cos(ang) * ln), col)
    c.rect(cx - 1, cy - 1, 3, 3, INK)
    hh, mm = int(now // 60) % 12 or 12, int(now % 60)
    chip(c, f"{hh}:{mm:02d}", 90, 104, YEL)
    # 눈금: 대본의 gauge.from → gauge.to
    g = B["wait"]["gauge"]
    val = g["from"] + (g["to"] - g["from"]) * k
    kt(c, g.get("label", ""), 24, 128, WHITE, bold=True)
    c.rect(22, 142, 136, 12, INK)
    c.rect(24, 144, int(132 * val), 8, RED if val > 0.8 else ORG)
    kt(c, f"{int(val * 100)}%", 156, 128, WHITE, "right", bold=True)
    shake = (1 if int(x.f / 2) % 2 == 0 else -1) if val > 0.9 else 0
    bust(c, 90 + shake, 250, ME_KIND, "worry" if k > 0.35 else "flat", x.T, 2)
    c.rect(0, 250, W, 70, PLUM if k > 0.7 else ORG)


@mv.scene(DUR["decide"], "decide")
def s_decide(c, x):
    """결정: 알림이 울리고 정하는 사람이 크게 나온다."""
    t = x.t
    alert = next(((at, who, text) for at, who, text in CHAT if B["decide"]["start"] <= at < B["decide"]["end"]), None)
    if alert is None:
        office(c, x.T)
        return
    at = lt(alert[0], "decide")
    if t < at + 1.5:
        office(c, x.T)
        bust(c, 90, 150, ME_KIND, "shock" if t >= at else "worry", x.T, 2)
        c.rect(0, 150, W, 170, ORG)
        c.rect(0, 150, W, 3, YEL)
        if t >= at:
            buzz = (1 if int(x.f / 2) % 2 == 0 else -1) if t < at + 1.1 else 0
            c.rect(30 + buzz, 172, 120, 54, INK)
            c.rect(33 + buzz, 175, 114, 48, WHITE)
            c.rect(38 + buzz, 180, 16, 16, ORG)
            kt(c, NAME.get(alert[1], ""), 58 + buzz, 178, INK, bold=True)
            kt(c, ROOM, 58 + buzz, 191, G2)
            kt(c, alert[2], 38 + buzz, 205, RED, bold=True)
            if t < at + 0.3:
                c.circ(90, 198, int(seg(t, at, at + 0.3) * 80), WHITE, fill=False)
            kt(c, "!", 136, 66, RED, outline=WHITE, bold=True)
    else:
        c.clear(INK)
        hold = t < at + 1.64  # 등장 순간 0.14초 정지
        z = 0.0 if hold else ease_out(seg(t, at + 1.64, at + 2.0))
        bust(c, 90, 276 + int(10 * (1 - z)), "boss", "talk", 0.0 if hold else x.T, 4)
        if t < at + 1.58:
            c.fade(0.8, WHITE)
        chip(c, B["decide"].get("keyword", ""), 90, 18, YEL)


@mv.scene(DUR["punch"], "punch")
def s_punch(c, x):
    """결말: 결과가 적힌 종이에 도장이 찍힌다. 대답은 종이 아래에 한 줄씩 뜬다."""
    t = x.t
    c.clear(TEAL)
    c.rect(24, 34, 132, 190, WHITE)
    c.rect(24, 34, 132, 190, G3, fill=False)
    kt(c, S["title"], 90, 42, INK, "center", bold=True)
    c.rect(34, 60, 112, 1, G3)
    kt(c, RESULT, 90, 68, RED, "center", bold=True)
    # 김 나는 냄비
    for i, sx in enumerate((-14, 0, 14)):
        yy = 96 - int((x.T * 10 + i * 5) % 12)
        c.rect(90 + sx, yy, 2, 5, G1)
    c.rect(52, 116, 76, 30, INK)
    c.rect(56, 146, 68, 6, INK)
    c.rect(44, 120, 8, 6, INK)
    c.rect(128, 120, 8, 6, INK)
    c.rect(56, 112, 68, 8, RED)
    for sx, col in ((-22, WHITE), (-4, GRN), (12, WHITE), (24, ORG)):
        c.rect(90 + sx, 113, 6, 4, col)
    y = 232
    for at, who, text in CHAT:  # 이 구간의 대답
        if B["punch"]["start"] <= at <= x.T:
            kt(c, f"{NAME.get(who, who)}: {text}", 90, y, WHITE, "center", outline=INK)
            y += 14
    if STAMP:
        hit = lt(STAMP["t"], "punch")
        if t < hit - 0.14:
            k = ease_back(seg(t, max(0.0, hit - 1.2), hit - 0.14))
            yy = int(-110 + k * 268)
            c.rect(60, yy - 8, 60, 34, ORG)
            c.rect(84, yy - 50, 12, 44, PLUM)
            c.rect(70, yy - 66, 40, 18, PLUM)
        else:
            c.rect(50, 160, 80, 44, RED, fill=False)
            c.rect(51, 161, 78, 42, RED, fill=False)
            kt(c, STAMP["text"], 90, 175, RED, "center", bold=True)
            if t < hit + 0.08:
                c.fade(0.6, WHITE)
            if t < hit + 0.5:
                c.circ(90, 182, int(seg(t, hit, hit + 0.5) * 120), YEL, fill=False)


def subs(c, T):
    """자막: script.json 의 subs. 줄바꿈(\\N)마다 한 줄."""
    for a, b, text in SUBS:
        if a <= T < b:
            for i, s in enumerate(text.split("\\N")):
                kt(c, s, 90, 268 + i * 14, WHITE, "center", outline=INK, bold=True)


mv.overlay(subs)
# 배경 음악(칩튠)과 효과음. 효과음 시각은 script.json 의 sfx(전송·알림·도장)와 대답이 오는 초다
song = Song(bpm=92, steps_per_beat=4)
song.track("C5 . E5 . G5 . E5 . | A4 . C5 . E5 . C5 . | F4 . A4 . C5 . A4 . | G4 . B4 . D5 . B4 .", wave="square", duty=0.25, vol=0.05, cutoff=2500)
song.track("C3 - . . G2 - . . | A2 - . . E2 - . . | F2 - . . C3 - . . | G2 - . . D3 - . .", wave="triangle", vol=0.16)
song.drums("k . h . s . h . k . h . s . h h", vol=0.09)
for at in SFX.get("send", []):
    song.sfx("select", at=at, vol=0.26)
for at, who, _ in CHAT:
    if who != ME and at not in SFX.get("buzz", []):
        song.sfx("select", at=at, vol=0.18)
for at in SFX.get("buzz", []):
    song.sfx("hurt", at=at, vol=0.26)
for at in SFX.get("hit", []):
    song.sfx("explosion", at=at, vol=0.28)

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="sheet=검수용 접촉 시트, render=무음 영상과 음악")
    ap.add_argument("cmd", choices=["sheet", "render"])
    ap.add_argument("--out", default="out", help="결과 저장 폴더")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    if args.cmd == "sheet":
        # 검수할 시각: 구간마다 앞·가운데·끝 한 장씩
        times = [round(b["start"] + (b["end"] - b["start"]) * k, 2) for b in S["beats"] for k in (0.3, 0.6, 0.93)]
        half = (len(times) + 1) // 2
        mv.stills(times[:half], os.path.join(args.out, "tests_sheet1.png"), cols=half)
        mv.stills(times[half:], os.path.join(args.out, "tests_sheet2.png"), cols=len(times) - half)
    else:
        song.save_wav(os.path.join(args.out, "music.wav"), mv.duration)
        mv.render(os.path.join(args.out, "video_silent.mp4"), crf=16)
