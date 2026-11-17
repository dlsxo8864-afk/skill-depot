"""Pillow를 사용해 디오라마 팩의 3D 텍스처(tex/)와 자막 오버레이(overlay/) 이미지를 생성한다.

사용법:
    python cards.py [--font FONT_PATH] [--font-regular FONT_REGULAR_PATH]
"""
import argparse
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fontfind  # noqa: E402
import plan  # noqa: E402

ROOT = os.getcwd()
TEX_DIR = os.path.join(ROOT, "tex")
OVERLAY_DIR = os.path.join(ROOT, "overlay")


def parse_args():
    parser = argparse.ArgumentParser(description="디오라마 팩 텍스처 및 오버레이 생성")
    parser.add_argument("--font", default=None, help="제목/강조용 굵은 글꼴 경로")
    parser.add_argument("--font-regular", default=None, help="본문용 기본 글꼴 경로")
    return parser.parse_args()


def get_font(path, size):
    """지정된 경로 또는 시스템 글꼴을 크기에 맞게 불러온다."""
    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    # 시스템 대표 한글 글꼴 시도
    for fallback in ["malgunbd.ttf", "malgun.ttf", "NanumGothicBold.ttf", "NanumGothic.ttf", "Arial.ttf"]:
        try:
            return ImageFont.truetype(fallback, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_centered_text(draw, center, text, font, fill, shadow_fill=None, offset=(2, 2)):
    """중앙 좌표를 기준으로 텍스트를 그린다."""
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = center[0] - w / 2 - bbox[0]
    y = center[1] - h / 2 - bbox[1]
    if shadow_fill:
        draw.text((x + offset[0], y + offset[1]), text, font=font, fill=shadow_fill)
    draw.text((x, y), text, font=font, fill=fill)


def make_sign_q(font_bold):
    """빈 메뉴 간판에 붙일 '?' 그림 (tex/sign_q.png)"""
    img = Image.new("RGBA", (512, 384), (242, 228, 201, 255))
    draw = ImageDraw.Draw(img)
    # 나무 판자 테두리
    draw.rectangle([8, 8, 503, 375], outline=(140, 95, 50, 255), width=8)
    draw.rectangle([18, 18, 493, 365], outline=(180, 130, 80, 255), width=3)
    # 물음표 텍스트
    f = ImageFont.truetype(font_bold.path, 180) if hasattr(font_bold, "path") else font_bold
    draw_centered_text(draw, (256, 192), "?", f, (90, 50, 20, 255), shadow_fill=(190, 160, 130, 255), offset=(4, 4))
    img.save(os.path.join(TEX_DIR, "sign_q.png"))


def make_note(idx, text, font_bold):
    """간판에 붙을 쪽지 그림 (tex/note_<idx>.png)"""
    # 인덱스마다 약간 다른 파스텔 색조 부여
    colors = [
        ((255, 248, 175, 255), (210, 195, 120, 255)),
        ((215, 245, 255, 255), (150, 190, 215, 255)),
        ((255, 225, 235, 255), (215, 160, 180, 255)),
    ]
    bg, border = colors[idx % len(colors)]
    img = Image.new("RGBA", (420, 240), bg)
    draw = ImageDraw.Draw(img)
    draw.rectangle([4, 4, 415, 235], outline=border, width=4)
    # 상단 핀 표시
    draw.ellipse([200, 12, 220, 32], fill=(210, 50, 50, 255), outline=(130, 20, 20, 255))
    # 대화 문구
    f = ImageFont.truetype(font_bold.path, 52) if hasattr(font_bold, "path") else font_bold
    draw_centered_text(draw, (210, 135), text, f, (45, 45, 45, 255))
    img.save(os.path.join(TEX_DIR, f"note_{idx}.png"))


def make_clock_face(font_bold):
    """시계탑 문자판 그림 (tex/clock_face.png)"""
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 원형 시계 판
    draw.ellipse([16, 16, 496, 496], fill=(250, 248, 240, 255), outline=(60, 45, 35, 255), width=16)
    # 12방향 눈금 및 주요 숫자
    center = (256, 256)
    r = 200
    for i in range(12):
        ang = math.radians(i * 30 - 90)
        x1 = center[0] + (r - 20) * math.cos(ang)
        y1 = center[1] + (r - 20) * math.sin(ang)
        x2 = center[0] + r * math.cos(ang)
        y2 = center[1] + r * math.sin(ang)
        width = 8 if i % 3 == 0 else 4
        draw.line([x1, y1, x2, y2], fill=(60, 45, 35, 255), width=width)
    # 12, 3, 6, 9 표시
    f = ImageFont.truetype(font_bold.path, 48) if hasattr(font_bold, "path") else font_bold
    draw_centered_text(draw, (256, 100), "12", f, (60, 45, 35, 255))
    draw_centered_text(draw, (412, 256), "3", f, (60, 45, 35, 255))
    draw_centered_text(draw, (256, 412), "6", f, (60, 45, 35, 255))
    draw_centered_text(draw, (100, 256), "9", f, (60, 45, 35, 255))
    img.save(os.path.join(TEX_DIR, "clock_face.png"))


def make_flag(text, font_bold):
    """간판 위에 꽂힐 깃발 그림 (tex/flag.png)"""
    img = Image.new("RGBA", (512, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 깃발 바탕 (삼각형/페넌트 형태)
    points = [(10, 20), (490, 128), (10, 236)]
    draw.polygon(points, fill=(235, 65, 55, 255), outline=(170, 30, 20, 255))
    # 결정 텍스트
    f = ImageFont.truetype(font_bold.path, 46) if hasattr(font_bold, "path") else font_bold
    draw_centered_text(draw, (210, 128), text, f, (255, 255, 255, 255), shadow_fill=(130, 20, 15, 255), offset=(2, 2))
    img.save(os.path.join(TEX_DIR, "flag.png"))


def make_shop_sign(result_text, font_bold):
    """완성된 가게 간판 그림 (tex/shop_sign.png)"""
    img = Image.new("RGBA", (512, 256), (40, 32, 28, 255))
    draw = ImageDraw.Draw(img)
    # 금색 테두리
    draw.rectangle([8, 8, 503, 247], outline=(225, 175, 65, 255), width=6)
    draw.rectangle([16, 16, 495, 239], outline=(160, 115, 40, 255), width=2)
    # 메뉴명 텍스트 (result)
    f = ImageFont.truetype(font_bold.path, 76) if hasattr(font_bold, "path") else font_bold
    draw_centered_text(draw, (256, 128), result_text, f, (255, 245, 220, 255), shadow_fill=(180, 50, 40, 255), offset=(3, 3))
    img.save(os.path.join(TEX_DIR, "shop_sign.png"))


def make_stamp(stamp_text, font_bold):
    """도장 자국 그림 (tex/stamp.png)"""
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 원형 인장 테두리
    draw.ellipse([24, 24, 488, 488], outline=(220, 40, 40, 240), width=18)
    draw.ellipse([46, 46, 466, 466], outline=(220, 40, 40, 200), width=4)
    # 도장 글자
    f = ImageFont.truetype(font_bold.path, 150) if hasattr(font_bold, "path") else font_bold
    draw_centered_text(draw, (256, 256), stamp_text, f, (220, 40, 40, 240))
    img.save(os.path.join(TEX_DIR, "stamp.png"))


def make_stage_overlays(font_bold, font_reg):
    """구간별 키워드 오버레이 (overlay/key_<id>.png, 1080x1920)"""
    beats = plan.S["beats"]
    f_key = ImageFont.truetype(font_bold.path, 150) if hasattr(font_bold, "path") else font_bold
    f_stage = ImageFont.truetype(font_reg.path, 50) if hasattr(font_reg, "path") else font_reg

    for idx, b in enumerate(beats):
        b_id = b["id"]
        keyword = b.get("keyword", "")
        if not keyword:
            continue
        img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 왼쪽 위 하늘 자리 (x: 100, y: 330)
        stage_label = f"{idx + 1}단계"
        # 작은 단계 번호
        draw.text((102, 332), stage_label, font=f_stage, fill=(20, 20, 20, 180))
        draw.text((100, 330), stage_label, font=f_stage, fill=(255, 230, 130, 255))

        # 아주 큰 흰 글자 + 얇은 검은 그림자
        draw.text((104, 399), keyword, font=f_key, fill=(10, 10, 10, 220))
        draw.text((100, 395), keyword, font=f_key, fill=(255, 255, 255, 255))

        out_path = os.path.join(OVERLAY_DIR, f"key_{b_id}.png")
        img.save(out_path)


def main():
    args = parse_args()
    os.makedirs(TEX_DIR, exist_ok=True)
    os.makedirs(OVERLAY_DIR, exist_ok=True)

    font_path = args.font or fontfind.find_font(bold=True)
    font_reg_path = args.font_regular or fontfind.find_font(bold=False)

    font_bold = get_font(font_path, 48)
    font_reg = get_font(font_reg_path, 36)

    # 1. tex/ 텍스처 생성
    make_sign_q(font_bold)
    for note in plan.ASK_NOTES:
        make_note(note["idx"], note["text"], font_bold)
    make_clock_face(font_bold)
    make_flag(plan.DECIDE_CHAT["text"], font_bold)
    make_shop_sign(plan.RESULT or "식당", font_bold)
    stamp_txt = plan.STAMP["text"] if plan.STAMP else "결정"
    make_stamp(stamp_txt, font_bold)

    # 2. overlay/ 오버레이 생성
    make_stage_overlays(font_bold, font_reg)
    print("CARDS OK: tex 및 overlay 생성 완료")


if __name__ == "__main__":
    main()
