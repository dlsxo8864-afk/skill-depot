"""휴대폰 화면(프레임마다 한 장)과 서류·도장 그림을 코드로 만든다. 작업 폴더에서 실행.

사용: python screens.py [--font 굵은글꼴] [--font-regular 본문글꼴]
결과: 작업 폴더의 screens/s0001.png …, tex/paper.png, tex/stamp_mark.png

대화 내용과 시각은 script.json 에서 읽는다(plan.py). 이 파일에는 대본 문구가 없다.
- 내 메시지는 보내기 전에 입력창에 한 글자씩 쳐진다.
- 알림 시각(sfx.buzz)에 온 메시지는 화면 위 알림 배너로도 뜬다.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan  # noqa: E402
from fontfind import find_font  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--font", help="굵은 한글 글꼴 파일. 없으면 시스템에서 찾는다")
ap.add_argument("--font-regular", help="본문 한글 글꼴 파일. 없으면 시스템에서 찾는다")
opt = ap.parse_args()

os.makedirs("screens", exist_ok=True)
os.makedirs("tex", exist_ok=True)
B = find_font(opt.font, bold=True)
R = find_font(opt.font_regular or opt.font, bold=False)
print("font bold   :", B)
print("font regular:", R)
F = {s: ImageFont.truetype(R, s) for s in (30, 44)}
FB = {s: ImageFont.truetype(B, s) for s in (34, 36, 40, 46, 72, 150)}
W, H = 540, 1170
INK = (26, 24, 36)
FPS, TOTAL = plan.FPS, plan.TOTAL
LEAD_COLOR, PEER_COLOR = (239, 143, 95), (106, 176, 239)  # 맨 끝 등장인물(정하는 사람)만 주황


def avatar(who):
    return LEAD_COLOR if who == plan.S["cast"][-1]["id"] else PEER_COLOR


def bubble(d, x, y, text, me):
    w = d.textlength(text, font=F[44]) + 48
    if me:
        x = W - 30 - w
    d.rounded_rectangle([x, y, x + w, y + 92], 28, fill=(255, 226, 90) if me else (255, 255, 255))
    d.text((x + 24, y + 14), text, font=F[44], fill=INK)
    return 92


def height(msg):
    return 120 if msg[1] == plan.ME else 156


def screen(msgs, typed, f, banner=None):
    im = Image.new("RGB", (W, H), (178, 199, 218))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 110], fill=(84, 104, 138))
    d.text((W / 2, 68), plan.ROOM, font=FB[34], fill=(255, 255, 255), anchor="mm")
    while sum(height(m) for m in msgs) > H - 110 - 140 - 10:  # 넘치면 오래된 말풍선부터 뺀다
        msgs = msgs[1:]
    y = 140
    for _, who, text in msgs:
        if who == plan.ME:
            y += bubble(d, 0, y, text, True) + 28
        else:
            d.rounded_rectangle([24, y, 92, y + 68], 24, fill=avatar(who))
            d.text((106, y - 8), plan.NAME.get(who, who), font=F[30], fill=(60, 66, 90))
            y += 36
            y += bubble(d, 106, y, text, False) + 28
    d.rectangle([0, H - 110, W, H], fill=(255, 255, 255))
    d.text((30, H - 86), typed, font=F[44], fill=INK)
    if f % 16 < 8:
        cx = 34 + d.textlength(typed, font=F[44])
        d.rectangle([cx, H - 82, cx + 4, H - 24], fill=INK)
    d.rounded_rectangle([W - 96, H - 92, W - 26, H - 22], 22, fill=(255, 226, 90) if typed else (216, 220, 228))
    if banner:
        who, text = banner
        d.rounded_rectangle([18, 22, W - 18, 196], 34, fill=(255, 255, 255))
        d.rounded_rectangle([36, 66, 112, 142], 24, fill=avatar(who))
        d.text((128, 58), plan.NAME.get(who, who), font=FB[34], fill=INK)
        d.text((128, 112), text, font=FB[36], fill=(182, 58, 78))
    return im


for f in range(TOTAL):
    t = f / FPS
    shown = [m for m in plan.CHAT if m[0] <= t]
    typed = ""
    nxt = next((m for m in plan.CHAT if m[1] == plan.ME and m[0] > t), None)
    if nxt and t >= nxt[0] - plan.TYPE_LEAD:  # 보내기 전: 0.25초를 남기고 다 친다
        k = (t - (nxt[0] - plan.TYPE_LEAD)) / max(0.1, plan.TYPE_LEAD - 0.25)
        typed = nxt[2][: int(len(nxt[2]) * max(0.0, min(1.0, k)) + 0.999)]
    banner = None
    for a, b in plan.BUZZ:
        if a <= f < b:
            m = next((m for m in plan.CHAT if plan.fr(m[0]) == a and m[1] != plan.ME), None)
            if m:
                banner = (m[1], m[2])
    screen(shown, typed, f, banner).save(f"screens/s{f + 1:04d}.png", compress_level=1)

# 서류: 제목 + 표 + 결과 그림(끓는 찌개 냄비)
paper = Image.new("RGB", (1240, 1754), (246, 241, 228))
d = ImageDraw.Draw(paper)
d.text((620, 170), plan.DOC_TITLE, font=FB[72], fill=INK, anchor="mm")
d.line([120, 260, 1120, 260], fill=INK, width=5)
for i, (a, b) in enumerate(plan.DOC_ROWS):
    y = 310 + i * 96
    d.rectangle([120, y, 1120, y + 96], outline=INK, width=3)
    d.line([380, y, 380, y + 96], fill=INK, width=3)
    d.text((250, y + 48), a, font=FB[40], fill=INK, anchor="mm")
    d.text((750, y + 48), b, font=FB[40], fill=INK, anchor="mm")
cx, cy, k = 620, 900, 0.62  # 냄비 자리와 크기. 도장 자국(서류 아래쪽)과 겹치지 않게 위에 둔다


def P(x0, y0, x1, y1):
    return [cx + x0 * k, cy + y0 * k, cx + x1 * k, cy + y1 * k]


for i, dx in enumerate((-150, 0, 150)):  # 김
    d.arc(P(dx - 50, -430, dx + 50, -250), 100 if i % 2 else 280, 260 if i % 2 else 80, fill=(150, 150, 160), width=10)
d.rounded_rectangle(P(-380, -60, -290, 10), 18, fill=INK)  # 손잡이
d.rounded_rectangle(P(290, -60, 380, 10), 18, fill=INK)
d.pieslice(P(-310, -330, 310, 290), 0, 180, fill=(40, 38, 46))  # 냄비 몸통
d.ellipse(P(-310, -110, 310, 70), fill=(40, 38, 46))
d.ellipse(P(-270, -90, 270, 50), fill=(206, 62, 40))  # 국물
for dx, dy, c in [(-120, -30, (250, 244, 228)), (40, -10, (250, 244, 228)), (140, -40, (250, 244, 228)), (-30, -55, (88, 150, 70)), (90, 10, (88, 150, 70)), (-170, 0, (232, 150, 60))]:
    d.rounded_rectangle(P(dx - 34, dy - 20, dx + 34, dy + 20), 5, fill=c)  # 두부·파·김치
paper.save("tex/paper.png")

# 도장 자국
mark = Image.new("RGBA", (900, 420), (0, 0, 0, 0))
d = ImageDraw.Draw(mark)
RED = (205, 40, 60, 255)
d.rounded_rectangle([20, 20, 880, 400], 40, outline=RED, width=26)
d.text((450, 208), plan.STAMP["text"] if plan.STAMP else "", font=FB[150], fill=RED, anchor="mm")
mark.save("tex/stamp_mark.png")
print("ok", TOTAL, "screens")
