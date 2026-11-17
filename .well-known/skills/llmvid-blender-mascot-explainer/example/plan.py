"""대본(script.json)을 읽고, 이 팩이 그 대본을 어떻게 풀지(컷 표·소품 시각)를 정한다.

cards.py, create_scene.py, render.py, finish.py 가 모두 이 파일을 읽는다.
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

# ── [풀이] 이 팩이 대본을 그리는 방식 (마스코트 설명 연출) ────────────
SUB_TOP = 1400  # 자막 윗줄 높이(픽셀). 마스코트 몸통 아래쪽에 오게 조금 내린다
# 디자인 색상
ACCENT = (0.098, 0.722, 0.651)  # 청록 (#19B8A6)
ACCENT_HEX = "#19B8A6"
BG_NAVY = (0.02, 0.03, 0.07)  # 짙은 남색 무대
CREAM = (0.95, 0.93, 0.88)  # 마스코트 머리 크림색

# 컷별 카메라 매핑 (wide: 전신 정면, card: 카드 중심, face: 마스코트 얼굴 클로즈업)
BEAT_CAM = {
    "hook": "wide",
    "ask": "card",
    "wait": "card",
    "decide": "face",
    "punch": "wide",
}

# 컷 표: (시작프레임, 끝프레임, 카메라_식별자) - render.py 에서 cam_<이름> 으로 호출
SHOTS = [
    (fr(b["start"]), fr(b["end"]), BEAT_CAM.get(b["id"], "wide"))
    for b in S["beats"]
]


def shot_at(f):
    """프레임 f(0부터)의 카메라 이름."""
    for a, b, s in SHOTS:
        if a <= f < b:
            return s
    return SHOTS[-1][2]


# finish.py 가 상단에 얹을 제목 띠 오버레이 목록: [(파일이름, 시작초, 끝초), …]
OVERLAYS = [
    (f"hdr_{b['id']}.png", float(b["start"]), float(b["end"]))
    for b in S["beats"]
]

# 구간별 마스코트 표정 및 동작 정의
# hook: happy/wave, ask: normal/point_up, wait: sleepy/shrug, decide: surprised/nod, punch: happy/jump
MASCOT_BEAT = {
    "hook": {"expr": "happy", "action": "wave"},
    "ask": {"expr": "normal", "action": "point_up"},
    "wait": {"expr": "sleepy", "action": "shrug"},
    "decide": {"expr": "surprised", "action": "nod"},
    "punch": {"expr": "happy", "action": "jump"},
}

# 구간별 세부 데이터 추출
BEATS_DICT = {b["id"]: b for b in S["beats"]}
HOOK_B = BEATS_DICT.get("hook", {})
ASK_B = BEATS_DICT.get("ask", {})
WAIT_B = BEATS_DICT.get("wait", {})
DECIDE_B = BEATS_DICT.get("decide", {})
PUNCH_B = BEATS_DICT.get("punch", {})

# 대화 목록
HOOK_CHAT = HOOK_B.get("chat", [])
ASK_CHAT = ASK_B.get("chat", [])
DECIDE_CHAT = DECIDE_B.get("chat", [])

# 시계 및 배고픔 게이지
CLOCK_SPEC = WAIT_B.get("clock", {"from": "11:50", "to": "12:20"})
GAUGE_SPEC = WAIT_B.get("gauge", {"label": "배고픔", "from": 0.2, "to": 1.0})


def parse_clock(hhmm_str):
    """'11:50' 형식 문자열을 (시, 분)으로 분해."""
    parts = hhmm_str.split(":")
    return int(parts[0]), int(parts[1])


CLOCK_FROM = parse_clock(CLOCK_SPEC.get("from", "11:50"))
CLOCK_TO = parse_clock(CLOCK_SPEC.get("to", "12:20"))

# 도장 시각 및 문구
IMPACT = fr(STAMP["t"]) if STAMP else None
STAMP_TEXT = STAMP.get("text", "결정") if STAMP else "결정"

if __name__ == "__main__":
    print("script:", SCRIPT_PATH)
    print("title :", S["title"], "|", TOTAL, "frames", DUR, "s")
    print("shots :", SHOTS)
    print("overlays:", OVERLAYS)
