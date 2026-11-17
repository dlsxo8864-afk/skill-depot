"""마스코트가 띄울 화면 카드와 위쪽 제목 띠를 Pillow 로 그린다. 작업 폴더에서 실행.

사용: python cards.py [--font 굵은글꼴] [--font-regular 본문글꼴]
결과(작업 폴더):
  tex/chip_<구간>.png   구간 키워드 칩          tex/msg.png     첫 구간의 내 메시지 카드
  tex/chat_<n>.png      단톡 카드(대화 n줄째까지) tex/dial.png    시계 문자판(바늘은 3D)
  tex/gauge.png         눈금 카드(막대는 3D)     tex/alert.png   알림 카드
  tex/result.png        결과 카드                tex/stamp.png   도장 자국(투명 바탕)
  overlay/hdr_<구간>.png  1080×1920 투명 바탕의 위쪽 제목 띠
문구는 전부 script.json 에서 읽는다(plan.py). 색은 plan.ACCENT_HEX 하나만 쓴다.
"""
import argparse
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan  # noqa: E402
from fontfind import find_font  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--font")
ap.add_argument("--font-regular")
opt = ap.parse_args()
B = find_font(opt.font, bold=True)
R = find_font(opt.font_regular or opt.font, bold=False)
os.makedirs("tex", exist_ok=True)
os.makedirs("overlay", exist_ok=True)

K = 2  # 그림 배율(카드가 화면에서 흐려지지 않게 크게 그린다)
INK, GREY, PAPER, SOFT = (24, 26, 34), (120, 126, 140), (255, 255, 255), (240, 243, 247)
ACCENT = tuple(int(plan.ACCENT_HEX[i:i + 2], 16) for i in (1, 3, 5))
RED = (214, 44, 66)


def font(size, bold=True):
    return ImageFont.truetype(B if bold else R, size * K)


def card(w, h, radius=40, fill=PAPER, outline=None):
    im = Image.new("RGBA", (w * K, h * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * K - 1, h * K - 1], radius * K, fill=fill, outline=outline, width=6 * K if outline else 0)
    return im, d


def chip(text, name):
    im, d = card(420, 150, 75, PAPER, ACCENT)
    d.text((210 * K, 72 * K), text, font=font(64), fill=INK, anchor="mm")
    im.save(f"tex/{name}")


def bubble(d, x, y, w, name, text, mine=False):
    """이름표 + 말풍선 한 줄. 높이를 돌려준다."""
    if name:
        d.text((x * K, y * K), name, font=font(26), fill=GREY)
        y += 34
    d.rounded_rectangle([x * K, y * K, (x + w) * K, (y + 74) * K], 24 * K, fill=ACCENT if mine else SOFT)
    d.text(((x + 24) * K, (y + 37) * K), text, font=font(36), fill=INK, anchor="lm")
    return (34 if name else 0) + 74 + 22


def header(d, w, text):
    d.ellipse([34 * K, 36 * K, 62 * K, 64 * K], fill=ACCENT)
    d.text((78 * K, 50 * K), text, font=font(34), fill=INK, anchor="lm")
    d.line([34 * K, 92 * K, (w - 34) * K, 92 * K], fill=SOFT, width=3 * K)


# 구간 키워드 칩
for b in plan.S["beats"]:
    if b.get("keyword"):
        chip(b["keyword"], f"chip_{b['id']}.png")

# 첫 구간: 내 메시지 카드
if plan.HOOK_CHAT:
    c = plan.HOOK_CHAT[0]
    im, d = card(640, 250)
    header(d, 640, plan.ROOM)
    bubble(d, 250, 124, 356, "", c["text"], mine=True)
    im.save("tex/msg.png")

# 단톡 카드: 대화가 한 줄씩 는다(chat_0 은 빈 방)
talk = plan.HOOK_CHAT + plan.ASK_CHAT
for n in range(len(plan.ASK_CHAT) + 1):
    im, d = card(700, 520)
    header(d, 700, plan.ROOM)
    y = 116
    for c in talk[: len(plan.HOOK_CHAT) + n]:
        mine = c["who"] == plan.ME
        y += bubble(d, 300 if mine else 34, y, 366, "" if mine else plan.NAME.get(c["who"], c["who"]), c["text"], mine)
    im.save(f"tex/chat_{n}.png")

# 시계 문자판(바늘 없음)
S = 512 * K
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.ellipse([8 * K, 8 * K, S - 8 * K, S - 8 * K], fill=PAPER, outline=ACCENT, width=14 * K)
for i in range(12):
    a = math.radians(i * 30)
    r0, r1 = (198 if i % 3 else 180) * K, 226 * K
    d.line([S / 2 + math.sin(a) * r0, S / 2 - math.cos(a) * r0, S / 2 + math.sin(a) * r1, S / 2 - math.cos(a) * r1], fill=INK if i % 3 == 0 else GREY, width=(10 if i % 3 == 0 else 5) * K)
im.save("tex/dial.png")

# 눈금 카드(막대는 장면에서 3D 로 얹는다)
im, d = card(660, 190)
d.text((36 * K, 50 * K), plan.GAUGE_SPEC.get("label", ""), font=font(38), fill=RED, anchor="lm")
d.rounded_rectangle([36 * K, 96 * K, 624 * K, 156 * K], 30 * K, fill=SOFT)
im.save("tex/gauge.png")

# 알림 카드
if plan.DECIDE_CHAT:
    c = plan.DECIDE_CHAT[0]
    im, d = card(720, 250, 44, PAPER, ACCENT)
    d.rounded_rectangle([36 * K, 40 * K, 106 * K, 110 * K], 20 * K, fill=ACCENT)
    d.text((126 * K, 56 * K), plan.ROOM, font=font(30, False), fill=GREY, anchor="lm")
    d.text((126 * K, 100 * K), plan.NAME.get(c["who"], c["who"]), font=font(36), fill=INK, anchor="lm")
    d.text((40 * K, 184 * K), c["text"], font=font(54), fill=INK, anchor="lm")
    im.save("tex/alert.png")

# 결과 카드
im, d = card(740, 520, 44, PAPER, ACCENT)
header(d, 740, plan.S["title"])
d.rounded_rectangle([40 * K, 124 * K, 700 * K, 480 * K], 30 * K, fill=SOFT)
d.text((370 * K, 300 * K), plan.RESULT, font=font(118), fill=INK, anchor="mm")
im.save("tex/result.png")

# 도장 자국(투명 바탕)
im = Image.new("RGBA", (400 * K, 400 * K), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.ellipse([16 * K, 16 * K, 384 * K, 384 * K], outline=RED + (255,), width=20 * K)
d.ellipse([48 * K, 48 * K, 352 * K, 352 * K], outline=RED + (255,), width=6 * K)
d.text((200 * K, 196 * K), plan.STAMP_TEXT, font=font(120), fill=RED + (255,), anchor="mm")
im.save("tex/stamp.png")

# 위쪽 제목 띠: 첫 구간은 대본 제목, 그 뒤는 구간 키워드
for i, b in enumerate(plan.S["beats"]):
    text = plan.S["title"] if i == 0 else b.get("keyword", "")
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(B, 62)
    w = int(d.textlength(text, font=f)) + 150
    x0 = (1080 - w) // 2
    d.rounded_rectangle([x0, 150, x0 + w, 270], 60, fill=(255, 255, 255, 245))
    d.rounded_rectangle([x0 + 40, 180, x0 + 54, 240], 7, fill=ACCENT + (255,))
    d.text((x0 + 86, 208), text, font=f, fill=INK + (255,), anchor="lm")
    d.text((540, 318), f"{i + 1} / {len(plan.S['beats'])}", font=ImageFont.truetype(B, 30), fill=(255, 255, 255, 200), anchor="mm")
    im.save(f"overlay/hdr_{b['id']}.png")
print("CARDS_OK")
