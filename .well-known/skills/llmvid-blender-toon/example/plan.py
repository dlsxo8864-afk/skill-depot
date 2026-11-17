"""대본(script.json)을 읽고, 이 팩이 그 대본을 어떻게 풀지(컷 표·소품 시각)를 정한다.

screens.py, build_ssul.py, rnd_ssul.py, finish.py 가 모두 이 파일을 읽는다.
새 대본으로 만들 때 고칠 곳은 두 군데다: script.json(대본) 과 이 파일의 # [풀이] 표시.
- 대본 파일은 이 파일 옆의 script.json 이다. 환경변수 LLMVID_SCRIPT 로 다른 파일을 줄 수 있다.
- 프레임은 0부터 센다(f). 블렌더 프레임은 f + 1 이다.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.environ.get("LLMVID_SCRIPT") or os.path.join(HERE, "script.json")
with open(SCRIPT_PATH, encoding="utf-8") as _f:
    S = json.load(_f)

FPS = S["fps"]
TOTAL = S["frames"]
DUR = TOTAL / FPS


def fr(sec):
    """초 → 프레임(0부터)."""
    return int(round(sec * FPS))


BEAT = {b["id"]: (fr(b["start"]), fr(b["end"])) for b in S["beats"]}
NAME = {c["id"]: c["name"] for c in S["cast"]}
ME = S["cast"][0]["id"]  # 첫 등장인물이 휴대폰 주인이다
ROOM = S.get("chat_room", "단톡방")
# 대화: (초, 누구, 문구) 시간순
CHAT = sorted((c["t"], c["who"], c["text"]) for b in S["beats"] for c in b.get("chat", []))
SUBS = [tuple(x) for x in S.get("subs", [])]
SFX = S.get("sfx", {})
STAMP = next((b["stamp"] for b in S["beats"] if "stamp" in b), None)
RESULT = next((b["result"] for b in S["beats"] if "result" in b), "")

# ── [풀이] 이 팩이 대본을 그리는 방식 ─────────────────────────────
TYPE_LEAD = 1.4  # 내 메시지는 보내기 이 초 전부터 입력창에 한 글자씩 친다
BANNER_SEC = 1.5  # 알림(sfx.buzz) 뒤 이 초 동안 화면 위에 알림 배너가 뜨고 휴대폰이 떤다
BUZZ = [(fr(t), fr(t + BANNER_SEC)) for t in SFX.get("buzz", [])]
IMPACT = fr(STAMP["t"]) if STAMP else None  # 도장이 찍히는 프레임
DOC_FROM = IMPACT - 10 if STAMP else TOTAL  # 서류·도장 컷이 시작하는 프레임
DOC_TITLE = "점심 메뉴 품의서"  # 서류 제목
DOC_ROWS = [("안건", S["title"]), ("의견", "아무거나"), ("결정", RESULT)]  # 서류 표
CLOCK = BEAT.get("wait")  # 시계 컷(시간이 흐르는 구간). 없으면 None
CLOCK_TURNS = (0.5, 1 / 24)  # 시계 컷 동안 분침·시침이 도는 바퀴 수(30분)
CLOCK_START = (0.0, 7 / 12)  # 시작 시각 보정(분침·시침을 시계 방향으로 미리 돌려 둘 바퀴 수). 소재 시계는 4:50 이라 시침만 7시간 돌려 11:50

# 컷 표: (시작, 끝, 카메라). 끝은 포함하지 않는다. 카메라 이름은 build_ssul.py 의 CAMS
SHOTS = [
    (0, 24, "wide"),
    (24, CLOCK[0], "phone"),
    (CLOCK[0], CLOCK[1], "clock"),
    (CLOCK[1], CLOCK[1] + 36, "macro"),
    (CLOCK[1] + 36, DOC_FROM, "phone"),
    (DOC_FROM, TOTAL + 1, "doc"),
]
# 빛: (프레임, 해 세기, 색, 배경 밝기). 따뜻하고 센 빛 = 평온, 차갑고 약한 빛 = 지침. 사이는 서서히 바뀐다
WARM, COLD = (1.0, 0.84, 0.62), (0.75, 0.85, 1.0)
LIGHT = [(0, 11, WARM, 0.42), (CLOCK[0], 11, WARM, 0.42), (CLOCK[1], 6, COLD, 0.3), (DOC_FROM - 12, 6, COLD, 0.3), (DOC_FROM, 10, WARM, 0.42)]


def shot_at(f):
    """프레임 f(0부터)의 카메라 이름."""
    return next(s for a, b, s in SHOTS if a <= f < b)


if __name__ == "__main__":
    print("script:", SCRIPT_PATH)
    print("title :", S["title"], "|", TOTAL, "frames", DUR, "s")
    for t, who, text in CHAT:
        print(f"  chat {t:5.2f}s f{fr(t):3d} {NAME.get(who, who)}: {text}")
    print("buzz", BUZZ, "impact", IMPACT, "doc_from", DOC_FROM)
    print("shots", SHOTS)
