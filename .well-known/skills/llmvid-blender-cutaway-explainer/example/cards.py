"""장치에 붙일 이름표·계기판 그림과 화면 위 단계 표시를 Pillow 로 그린다. 작업 폴더에서 실행.

사용: python cards.py [--font 굵은글꼴]
결과(작업 폴더):
  tex/tag_<부품>.png     이름표(plan.TAGS)         tex/funnel_<인물>.png  투입구 이름표
  tex/clock_from.png, clock_to.png  시계 창        tex/dial.png           압력계 문자판(바늘은 3D)
  tex/ruler.png          눈금자                    tex/stamp.png          도장 자국(투명 바탕)
  overlay/step_<구간>.png  1080×1920 투명 바탕의 단계 표시
문구는 전부 script.json 에서 읽는다(plan.py).
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
opt = ap.parse_args()
B = find_font(opt.font, bold=True)
os.makedirs("tex", exist_ok=True)
os.makedirs("overlay", exist_ok=True)

K = 2
INK, GREY, PAPER = (26, 28, 36), (120, 126, 140), (255, 255, 255)
ACCENT = tuple(int(plan.ACCENT_HEX[i:i + 2], 16) for i in (1, 3, 5))
RED = (214, 44, 66)


def font(size):
    return ImageFont.truetype(B, size * K)


def tag(text, name, size=56):
    """흰 판 + 왼쪽 강조색 막대 + 굵은 글자. 글자 길이에 맞춰 폭이 정해진다."""
    f = font(size)
    w = int(ImageDraw.Draw(Image.new("RGB", (8, 8))).textlength(text, font=f) / K) + 110
    im = Image.new("RGBA", (w * K, 120 * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * K - 1, 120 * K - 1], 26 * K, fill=PAPER, outline=INK, width=4 * K)
    d.rounded_rectangle([24 * K, 24 * K, 40 * K, 96 * K], 8 * K, fill=ACCENT)
    d.text((64 * K, 58 * K), text, font=f, fill=INK, anchor="lm")
    im.save(f"tex/{name}")


for key, text in plan.TAGS.items():
    tag(text, f"tag_{key}.png")
for c in plan.S["cast"]:
    tag(c["name"], f"funnel_{c['id']}.png", 60)

# 시계 창
for key in ("from", "to"):
    im = Image.new("RGBA", (360 * K, 150 * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 360 * K - 1, 150 * K - 1], 24 * K, fill=(16, 20, 26), outline=(70, 76, 90), width=6 * K)
    d.text((180 * K, 72 * K), plan.CLOCK.get(key, ""), font=font(96), fill=(255, 190, 90), anchor="mm")
    im.save(f"tex/clock_{key}.png")

# 압력계 문자판: 0(왼쪽 아래 -135도) → 100(오른쪽 아래 +135도), 80 부터 빨간 구간
S = 512 * K
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.ellipse([6 * K, 6 * K, S - 6 * K, S - 6 * K], fill=PAPER, outline=INK, width=16 * K)
d.arc([52 * K, 52 * K, S - 52 * K, S - 52 * K], -90 + 81, -90 + 135, fill=RED, width=22 * K)
for v in range(0, 101, 5):
    a = math.radians(-135 + 270 * v / 100)
    r0, r1 = (180 if v % 20 == 0 else 196) * K, 214 * K
    d.line([S / 2 + math.sin(a) * r0, S / 2 - math.cos(a) * r0, S / 2 + math.sin(a) * r1, S / 2 - math.cos(a) * r1], fill=INK, width=(8 if v % 20 == 0 else 4) * K)
    if v % 20 == 0:
        d.text((S / 2 + math.sin(a) * 148 * K, S / 2 - math.cos(a) * 148 * K), str(v), font=font(34), fill=INK, anchor="mm")
d.text((S / 2, S / 2 + 120 * K), plan.GAUGE.get("label", ""), font=font(40), fill=GREY, anchor="mm")
im.save("tex/dial.png")

# 눈금자: 아래 0 → 위 100
im = Image.new("RGBA", (150 * K, 640 * K), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.rounded_rectangle([0, 0, 150 * K - 1, 640 * K - 1], 14 * K, fill=PAPER, outline=INK, width=4 * K)
for v in range(0, 101, 5):
    y = (600 - 560 * v / 100) * K
    d.line([14 * K, y, (62 if v % 10 == 0 else 40) * K, y], fill=INK, width=(5 if v % 10 == 0 else 3) * K)
    if v % 20 == 0:
        d.text((76 * K, y), str(v), font=font(30), fill=INK, anchor="lm")
im.save("tex/ruler.png")

# 도장 자국(투명 바탕)
im = Image.new("RGBA", (400 * K, 400 * K), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.ellipse([16 * K, 16 * K, 384 * K, 384 * K], outline=RED + (255,), width=20 * K)
d.ellipse([48 * K, 48 * K, 352 * K, 352 * K], outline=RED + (255,), width=6 * K)
d.text((200 * K, 196 * K), plan.STAMP["text"] if plan.STAMP else "", font=font(120), fill=RED + (255,), anchor="mm")
im.save("tex/stamp.png")

# 화면 위 단계 표시: 왼쪽 위 알약 "n/5 키워드"
n = len(plan.S["beats"])
for i, b in enumerate(plan.S["beats"]):
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f1, f2 = ImageFont.truetype(B, 40), ImageFont.truetype(B, 56)
    num, word = f"{i + 1}/{n}", b.get("keyword", "")
    w = int(d.textlength(num, font=f1) + d.textlength(word, font=f2)) + 110
    d.rounded_rectangle([60, 160, 60 + w, 260], 50, fill=(30, 34, 44, 235))
    d.text((92, 212), num, font=f1, fill=ACCENT + (255,), anchor="lm")
    d.text((92 + d.textlength(num, font=f1) + 22, 210), word, font=f2, fill=(255, 255, 255, 255), anchor="lm")
    im.save(f"overlay/step_{b['id']}.png")
print("CARDS_OK")
