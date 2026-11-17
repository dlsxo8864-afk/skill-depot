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

# ── [풀이] 이 팩이 대본을 그리는 방식 (단계 진화 디오라마) ──────────────
BEATS_MAP = {b["id"]: b for b in S["beats"]}
BEAT_ORDER = [b["id"] for b in S["beats"]]

# 컷 구간 프레임(0부터)
F_HOOK = BEAT.get("hook", (0, fr(3.0)))[0]
F_ASK = BEAT.get("ask", (fr(3.0), fr(6.0)))[0]
F_WAIT = BEAT.get("wait", (fr(6.0), fr(9.0)))[0]
F_DECIDE = BEAT.get("decide", (fr(9.0), fr(12.0)))[0]
F_PUNCH = BEAT.get("punch", (fr(12.0), TOTAL))[0]

# 컷 표: (시작, 끝, 카메라). render.py는 cam_<이름> 카메라를 선택한다.
# 1) 전체 컷 (wide, 서서히 30도 회전)
# 2) 구조물 근접 컷 (close, 시계탑과 게이지, 인물 반응)
# 3) 전경 컷 (punch, 완성된 식당과 축하)
SHOTS = [
    (0, F_WAIT, "wide"),
    (F_WAIT, F_PUNCH, "close"),
    (F_PUNCH, TOTAL + 1, "punch"),
]


def shot_at(f):
    """프레임 f(0부터)의 카메라 이름."""
    for a, b, s in SHOTS:
        if a <= f < b:
            return s
    return SHOTS[-1][2]


# 키워드 오버레이: finish.py가 (파일명, 시작 초, 끝 초) 구간에 얹는다
OVERLAYS = [
    (f"key_{b['id']}.png", b["start"], min(b["end"], b["start"] + 2.0))
    for b in S["beats"]
    if b.get("keyword")
]

# ask 구간 쪽지 목록
ASK_NOTES = []
for idx, c in enumerate(BEATS_MAP.get("ask", {}).get("chat", [])):
    ASK_NOTES.append({
        "idx": idx,
        "t": c["t"],
        "frame": fr(c["t"]),
        "who": c["who"],
        "text": c["text"],
        "tex": f"note_{idx}.png",
    })

# wait 구간 시계 및 게이지
WAIT_BEAT = BEATS_MAP.get("wait", {})
CLOCK_INFO = WAIT_BEAT.get("clock", {"from": "11:50", "to": "12:20"})
GAUGE_INFO = WAIT_BEAT.get("gauge", {"label": "배고픔", "from": 0.2, "to": 1.0})

# decide 구간 깃발/대화
DECIDE_BEAT = BEATS_MAP.get("decide", {})
decide_chats = DECIDE_BEAT.get("chat", [])
DECIDE_CHAT = decide_chats[0] if decide_chats else {"t": DECIDE_BEAT.get("start", 9.0), "text": RESULT, "who": S["cast"][-1]["id"]}

# punch 구간 도장/식당
PUNCH_BEAT = BEATS_MAP.get("punch", {})
STAMP_T = STAMP["t"] if STAMP else PUNCH_BEAT.get("start", 12.0)
STAMP_FRAME = fr(STAMP_T)

# 구조물 단계 진화 표
STAGES = {
    "hook": {
        "start_f": F_HOOK,
        "parts": [{"type": "sign", "frame": F_HOOK, "tex": "sign_q.png"}],
    },
    "ask": {
        "start_f": F_ASK,
        "parts": [{"type": "note", "frame": n["frame"], "idx": n["idx"], "tex": n["tex"]} for n in ASK_NOTES],
    },
    "wait": {
        "start_f": F_WAIT,
        "parts": [
            {"type": "tower", "frame": F_WAIT},
            {"type": "gauge", "frame": F_WAIT},
        ],
    },
    "decide": {
        "start_f": F_DECIDE,
        "parts": [{"type": "flag", "frame": fr(DECIDE_CHAT["t"]), "tex": "flag.png"}],
    },
    "punch": {
        "start_f": F_PUNCH,
        "parts": [
            {"type": "shop", "frame": F_PUNCH, "tex": "shop_sign.png"},
            {"type": "stamp", "frame": STAMP_FRAME, "tex": "stamp.png"},
        ],
    },
}

# 등장인물 및 동작 스케줄
CAST = S["cast"]
LEAD_ID = CAST[-1]["id"]


def get_cast_action_cues():
    """인물별 애니메이션 동작 시점(프레임) 목록을 돌려준다."""
    cues = {
        "hop": [],      # (frame, who_id)
        "slump": [],    # (start_frame, end_frame)
        "walk_to": [],  # (start_frame, end_frame, who_id)
        "cheer": [],    # (frame, who_id)
    }
    # hook 질문 동작
    hook_chats = BEATS_MAP.get("hook", {}).get("chat", [])
    if hook_chats:
        cues["hop"].append((fr(hook_chats[0]["t"]), hook_chats[0]["who"]))
    else:
        cues["hop"].append((F_HOOK, ME))

    # ask 대답 동작
    for n in ASK_NOTES:
        cues["hop"].append((n["frame"], n["who"]))

    # wait 모두 풀죽음
    cues["slump"].append((F_WAIT, F_DECIDE))

    # decide 팀장 전진
    cues["walk_to"].append((F_DECIDE, fr(DECIDE_CHAT["t"]), LEAD_ID))

    # punch 모두 환호
    for c in CAST:
        cues["cheer"].append((F_PUNCH, c["id"]))

    return cues


if __name__ == "__main__":
    print("script:", SCRIPT_PATH)
    print("title :", S["title"], "|", TOTAL, "frames", DUR, "s")
    print("shots :", SHOTS)
    print("overlays:", OVERLAYS)
    print("stages:", list(STAGES.keys()))
