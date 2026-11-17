"""스틸 여러 장을 한 장의 시트로 붙인다(중간 검수용).

사용: python sheet.py 출력.png 그림1.png 그림2.png … [--cols 4] [--width 360]
그림마다 파일 이름을 왼쪽 위에 적는다. 시트 한 장을 열어 구도·글자·빛을 한꺼번에 본다.
"""
import argparse
import os

from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("images", nargs="+")
ap.add_argument("--cols", type=int, default=4)
ap.add_argument("--width", type=int, default=360, help="그림 한 칸의 폭(픽셀)")
opt = ap.parse_args()

tiles = []
for p in opt.images:
    im = Image.open(p).convert("RGB")
    im = im.resize((opt.width, round(im.height * opt.width / im.width)))
    d = ImageDraw.Draw(im)
    label = os.path.basename(p)
    d.rectangle([0, 0, 8 + 7 * len(label), 18], fill=(0, 0, 0))
    d.text((4, 3), label, fill=(255, 255, 255))
    tiles.append(im)
cols = min(opt.cols, len(tiles))
rows = (len(tiles) + cols - 1) // cols
th = max(t.height for t in tiles)
sheet = Image.new("RGB", (cols * opt.width, rows * th), (24, 24, 24))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % cols) * opt.width, (i // cols) * th))
sheet.save(opt.out)
print("ok", opt.out, sheet.size)
