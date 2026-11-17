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

# ── [풀이] 이 팩이 대본을 그리는 방식(작동 원리 해부) ─────────────────
# 대본의 흐름을 가상의 장치로 옮긴다: 투입(묻기) → 쌓임(대답) → 압력(기다림) → 밸브(결정) → 배출(결과)
ACCENT_HEX = "#F2622E"
ACCENT = tuple(int(ACCENT_HEX[i:i + 2], 16) / 255 for i in (1, 3, 5))
SUB_TOP = 1400  # 자막 윗줄 높이(픽셀)
B = {b["id"]: b for b in S["beats"]}
ORDER = [b["id"] for b in S["beats"]]
LEAD = S["cast"][-1]["id"]  # 마지막 등장인물이 밸브를 여는 사람
WAIT = B.get("wait", {})
CLOCK = WAIT.get("clock", {"from": "", "to": ""})
GAUGE = WAIT.get("gauge", {"label": "", "from": 0.2, "to": 1.0})
IMPACT = fr(STAMP["t"]) if STAMP else None

# 구슬: 저장통에 쌓이기 전(밸브가 열리기 전)의 대화 하나가 구슬 하나. (프레임, 누구)
VALVE_AT = fr(B["decide"]["chat"][0]["t"]) if B.get("decide", {}).get("chat") else BEAT.get("decide", (TOTAL, TOTAL))[0]
BALLS = [(fr(t), who) for t, who, _ in CHAT if fr(t) < VALVE_AT]

# 이름표: 부품 → 문구. 문구는 대본에서 만든다
TAGS = {
    "machine": S["title"],
    "tank": B.get("ask", {}).get("keyword", "") + " 저장통",
    "gauge": GAUGE.get("label", "") + " 압력",
    "valve": NAME.get(LEAD, "") + " 밸브",
    "out": RESULT,
}
# 구간마다: (카메라, 보여 줄 이름표). 카메라 이름은 create_scene.py 의 CAMS
FLOW = {
    "hook": ("outer", ["machine"]),
    "ask": ("front", ["tank"]),
    "wait": ("gauge", ["gauge"]),
    "decide": ("valve", ["valve"]),
    "punch": ("outlet", ["out"]),
}
# 컷 표: 구간마다 한 컷. 마지막 구간은 도장이 찍힌 뒤 위에서 본 전체로 넘어간다
SHOTS = []
for bid in ORDER:
    a, b = BEAT[bid]
    cam = FLOW.get(bid, ("outer", []))[0]
    if bid == ORDER[-1] and IMPACT is not None and IMPACT + 16 < b:
        SHOTS += [(a, IMPACT + 16, cam), (IMPACT + 16, TOTAL + 1, "top")]
    else:
        SHOTS.append((a, b if bid != ORDER[-1] else TOTAL + 1, cam))


def shot_at(f):
    """프레임 f(0부터)의 카메라 이름."""
    return next((s for a, b, s in SHOTS if a <= f < b), SHOTS[-1][2])


# 화면 위 단계 표시: (overlay 폴더 안 파일 이름, 시작 초, 끝 초)
OVERLAYS = [(f"step_{b['id']}.png", float(b["start"]), float(b["end"])) for b in S["beats"]]

if __name__ == "__main__":
    print("script:", SCRIPT_PATH)
    print("title :", S["title"], "|", TOTAL, "frames", DUR, "s")
    print("balls :", BALLS, "valve", VALVE_AT, "impact", IMPACT)
    print("shots :", SHOTS)
    print("tags  :", TAGS)
