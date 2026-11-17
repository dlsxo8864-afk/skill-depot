# 「대답하지 못한 사람」 — 30s 세로형 한국 심리 드라마

확정일 2026-11-03 · 최종 채택: 1차 렌더

## 이 패키지 구성

```
├── deliverable_no_answer_30s.mp4   ← 최종 영상 (1080x1920, 30.04s, 무음)
├── WORK_PROCESS.md                 ← 8단계 전 과정 + 다음에 쓸 규칙 6개
├── PRODUCTION_REPORT.md            ← 제작 보고서 11장 (샷 구조 3종 비교 포함)
├── STORY_GUIDE.json                ← 대본 정본 (3유닛 · 9샷 · 판정 기준)
├── QC_frame_grid.jpg               ← QC 16프레임 그리드 (검수 증거)
├── prompt_used_U_full.txt          ← 실제 렌더에 쓰인 30초 프롬프트 전문
├── canon/                          ← 정본 이미지 6장
│   ├── A_sheet.jpg                 배우 A 확정 (전신·의상)
│   ├── B_sheet.jpg                 배우 B 확정
│   ├── A_head.jpg                  A 얼굴 크롭 (참조 대안)
│   ├── B_head.jpg                  B 얼굴 크롭
│   ├── plate_corridor.jpg          복도 9:16 무인
│   └── plate_meeting.jpg           회의실 9:16 무인
└── clip_prompts/                   ← 재작업용 3클립 프롬프트
    ├── C1.txt                      9s · 3샷
    ├── C2.txt                      9s · 2샷
    └── C3.txt                      12s · 4샷
```

## 최종 영상 사양

| 항목 | 값 |
|---|---|
| 해상도 | 1080 x 1920 (9:16) |
| 프레임레이트 | 24 fps |
| 길이 | 30.04초 |
| 용량 | 11.2 MB |
| 코덱 | H.264 |
| 오디오 | 스트림 없음 (완전 무음) |

## 먼저 읽을 것

1. `WORK_PROCESS.md` — 무엇을 어떤 순서로 했고 어디서 틀렸는지
2. `PRODUCTION_REPORT.md` 11장 — 미해결 · 불일치 4건
3. `prompt_used_U_full.txt` — 실제로 모델에 들어간 문장

## 중요

- 이 영상에는 **컷 전환이 없다.** 9개 샷 설계가 하나의 연속 클로즈업으로 붕괴한 상태이며, 사용자 컨펌 하에 수용된 결과다.
- 마지막 0.5초 암전과 자막은 최종본에 **없다.**
- 배우 얼굴은 `A_sheet.jpg` / `B_sheet.jpg`가 정답이다. `A_face.jpg` 계열 재생성 얼굴은 채택되지 않았다.
