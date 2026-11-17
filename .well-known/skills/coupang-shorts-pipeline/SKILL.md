---
name: coupang-shorts-pipeline
description: 쿠팡 파트너스 탭(쇼츠킷 8296, affiliate maker)의 단계별 프롬프트·스킬을 고치거나 새 쿠팡 쇼츠 실행 결과를 검수할 때, 또는 상품 쇼츠 대본·recreate brief·첫 프레임 이미지·영상 프롬프트 품질을 올릴 때 쓴다(쇼츠킷 프롬프트, 쿠팡 쇼츠, affiliate maker, recreate brief).
---

# 쿠팡 쇼츠 파이프라인(쇼츠킷 8296)

## 핵심

결함은 **단계 순서 → 사실 → 프롬프트 → 코드 검사** 순서로 본다. 프롬프트부터 고치지 않는다.
제품 사진과 확인된 사실이 참고 영상보다 항상 우선이다. 글자·없는 부품·없는 빛은 이미지 단계에서 막고, 모든 글자는 합성에서 얹는다.

백엔드 `C:\Users\<사용자>\Desktop\프로그램\27. 쇼츠킷 v1.0`, 화면 `Documents\Codex\shorttuber-frontend`. 결정 문서는 `docs\skills\00~05`.

## 흐름은 하나(2026-11-15 확정)

S1 컷 구성 → H1 훅 → C2 대본(이 화면에서 바로 고침) → V1·V2 음성 → **C3 장면 계획 → I1 컷 이미지 → C4 영상화 금액 → 영상화 → C5** → T1 썸네일 → C6 내보내기.

- 순서는 늘 **이미지 → 영상화**. 이미지를 모두 만든 뒤에만 영상화로 간다. 영상화를 통째로·일부만 건너뛰는 선택(`still`·`fit`·줄 수 상한)은 없다.
- 줄마다 사람이 고르는 것은 둘뿐: **촬영 타입**과 **영상화하지 않음**(`recreate_still`). 끝 화면이 덮는 마지막 줄만 실제 제품 사진(`product_fixed`).
- 촬영 타입(`recreate.SHOT_TYPES`) = 실행 기본값(`shot_type`) + 줄별 바꾸기. 타입이 브리프 `pov` 를 고정하고, 이미지·영상·검사가 그 `pov` 를 읽는다. **얼굴이 보이는 타입은 만들지 않는다.**

| 타입 | pov | 사람 |
|---|---|---|
| `auto` 1인칭 위주(기본) | 모델이 first_person·over_shoulder·tabletop 가운데 고름 | 손·팔뚝만 |
| `product_only` 제품 단독 | tabletop | 없음 |
| `usage_scene` 사용 장면 | back_view | 뒷모습·옆모습(얼굴 fail) |
| `space` 공간 전경 | room_wide | 없음 |

- 진행 화면은 실행 화면(`#/workflow/run/<id>`) 하나다. 다른 제작 화면(`#/workflow/<pid>/…`)으로 보내는 링크·안내를 넣지 않는다. 새로 시작하는 길도 새 흐름 하나(옛 흐름은 지난 작업 보기만).

## 고치는 순서

1. 결함을 층으로 나눈다: 프롬프트(`server/prompts/*.md`, 재시작 불필요) / 코드 상수(재시작 필요) / 화면(새로 고침).
2. 해당 단계 규칙과 등급을 본다 — [evidence-rules.md](references/evidence-rules.md). [A] 고정, [B] 기본값, [C] 방향만.
3. 파일 계약을 지키며 고친다 — [prompt-contracts.md](references/prompt-contracts.md).
4. 시험을 돌린다(계약 문서 끝의 명령). 코드 상수를 바꿨으면 실행 중 작업 0 확인 뒤 `devtools\restart_server.ps1`.
5. 화면을 고쳤으면 임시 서버에서 끝까지 눌러 본다 — `devtools\patches\coupang_simplify_2026-11-15\tools\walk_simplify.py`(모의 제공자·임시 데이터·유료 0).
6. 실제 상품 1건을 끝까지 돌리고 [defect-checklist.md](references/defect-checklist.md) 로 검수한다. 사진·클립·최종 영상을 눈으로 본다.

## 단계별 기준

| 단계 | 기준 | 파일 |
|---|---|---|
| 참고 영상 | 보이는 것만, 글자는 위치만, 무관 영상은 정직하게 `no` | `xhs_scene_recreate.md` |
| 훅 | 불편 하나, 첫 화면에 얼굴 없음, 다른 회사 제품 안 그림 | `hook_candidates.md` |
| 대본 | 문제 줄 1개, 둘째 줄 제품 실물, 장점 1~2개를 행동 변화로, 모르는 사양은 빈칸, 관찰 화법('써 보니' 금지) | `shopping_guide.md` F~Y, `script_product.md` |
| 브리프 | A 시점·타입 / B 제품 사실 / C 글자 없는 화면 / D 한 시퀀스 / E 칸 / F 첫 화면 | `xhs_recreate_brief.md` A~F |
| 첫 프레임 | 무지 소품, 사진에 없는 부품·빛·표시창 금지, 시점 문장은 pov 별 | `photo_recreate.md`, `photos.RECREATE_POV_LINES` |
| 영상 | 움직임만, 동작 1·카메라 고정·끝 hold, 3~5초, Kling 2,500자 이하 | `clips_v2.recreate_prompt`·`_POV_LINES`(코드) |
| 검사 | 글자·사람은 fail. `back_view` 만 뒷모습 허용(얼굴 fail) | `clip_checks.AI_PROMPT_*`·`AI_PERSON_OK_NOTE`(코드) |
| 음성 | 30초 140~170음절, 1.0배속(1.1 상한), 숫자 소리대로 | `elevenlabs.py`·`gemini.py`(코드) |
| 마무리 | 끝 컷은 앞 컷과 같은 톤, 고지 완전 문장 | `shot_plan.composite`·`affiliate.overlay_spec`(코드) |

## 하지 말 것

- `hook_candidates.md`·`script_*.md` 에 `<!-- -->` 주석 넣기(모델에 그대로 간다). 첫 줄 `[[TASK:…]]`·모의가 읽는 줄 머리 라벨 바꾸기.
- 금지어만 나열하기(글자 소품은 대체 소품을 긍정문으로). 같은 규칙을 여러 곳에 다시 쓰기(한 묶음에 한 번만).
- 미검증 수치(조회 배수·완주율)를 프롬프트나 화면에 넣기.
- 모의 실행이나 시험 통과만으로 끝내기. 유료 단계를 자동으로 붙이거나 사람 확인을 기본 체크로 넘기기.
- 화면에 같은 안내를 두 번 쓰기, 기본값으로 갈 설정을 펼쳐 두기.

## 참조

- [prompt-contracts.md](references/prompt-contracts.md) — 파일별 자리표시·`[[TASK:]]`·스키마·시험·재시작 여부, 옛 브리프 규칙 번호(1~17) ↔ 새 묶음(A~F) 대응.
- [defect-checklist.md](references/defect-checklist.md) — 새 실행 검수 항목.
- [evidence-rules.md](references/evidence-rules.md) — 단계별 규칙 요약과 등급.
- 상세 근거(출처 링크): `docs\skills\01~05`.
