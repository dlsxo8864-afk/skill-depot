"""한글 글꼴 찾기. 글꼴 절대 경로를 스크립트에 박지 않고 후보를 차례로 찾는다.

find_font(override, bold) -> 글꼴 파일 경로. 못 찾으면 찾아본 후보를 알리고 멈춘다.
font_family(path)         -> ASS 자막 Style 의 Fontname 에 넣을 패밀리 이름.
"""
import os

_LOCAL = os.environ.get("LOCALAPPDATA", "")
_USER = os.path.join(_LOCAL, "Microsoft", "Windows", "Fonts") if _LOCAL else ""


def _win(name):
    out = ["C:/Windows/Fonts/" + name]
    if _USER:
        out.append(os.path.join(_USER, name))
    return out


BOLD = (
    _win("NotoSansKR-Bold.ttf")
    + ["C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf"]
    + ["/System/Library/Fonts/AppleSDGothicNeo.ttc"]
    + [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
)
REGULAR = (
    _win("NotoSansKR-Medium.ttf")
    + _win("NotoSansKR-Regular.ttf")
    + ["C:/Windows/Fonts/malgun.ttf"]
    + ["/System/Library/Fonts/AppleSDGothicNeo.ttc"]
    + [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
)


def find_font(override=None, bold=True):
    """override(--font 인자)가 있으면 그것만 본다. 없으면 후보를 차례로 찾는다."""
    if override:
        if os.path.isfile(override):
            return override
        raise SystemExit("글꼴 파일이 없습니다: " + override)
    cands = BOLD if bold else REGULAR + BOLD
    for p in cands:
        if os.path.isfile(p):
            return p
    raise SystemExit(
        "한글 글꼴을 찾지 못했습니다. --font 로 글꼴 파일(.ttf/.otf/.ttc)을 넘겨 주세요.\n찾아본 곳:\n  " + "\n  ".join(cands)
    )


_BY_FILE = {"notosanskr": "Noto Sans KR", "malgun": "Malgun Gothic", "applesdgothicneo": "Apple SD Gothic Neo", "notosanscjk": "Noto Sans CJK KR"}


def font_family(path):
    """글꼴 파일의 패밀리 이름. Pillow 로 읽고, 안 되면 파일 이름으로 짐작한다."""
    try:
        from PIL import ImageFont

        name = ImageFont.truetype(path, 20).getname()[0]
        if name:
            return name
    except Exception:
        pass
    base = os.path.basename(path).lower()
    for key, fam in _BY_FILE.items():
        if base.startswith(key):
            return fam
    return os.path.splitext(os.path.basename(path))[0]


if __name__ == "__main__":
    for b in (True, False):
        p = find_font(bold=b)
        print("bold" if b else "regular", p, "|", font_family(p))
