# 프롬프트 계약 — 고치기 전에 볼 것 (2026-11-09, 11-15 개정)

경로 약어: `BE` = `C:\Users\<사용자>\Desktop\프로그램\27. 쇼츠킷 v1.0`, `S` = `BE/server`, `P` = `S/prompts`.
줄 번호는 11-09 22시 무렵 값이다. 다른 세션이 같은 파일을 고치므로 편집 전에 다시 grep 한다.

## 공통

- `[[TASK:이름]]` 은 **첫 비어 있지 않은 줄**. 모의 제공자가 그 줄로 응답 모양을 고른다(`S/providers/mock.py:42-51`). 사진·영상 틀(photo·photo_recreate·clip·main_cut)은 표시가 없다.
- 치환 엔진 넷:

| 엔진 | 문법 | 주석 | 빈 값 | 쓰는 파일 |
|---|---|---|---|---|
| `load_prompt` | `{{x}}` | **안 지움** | "없음" | `hook_candidates.md` |
| `script._render` | `{{x}}` | **안 지움** | 모르는 자리 그대로 남음 | `script_product.md`·`script_reference.md` |
| `string.Template` | `$x` | `<!-- -->` 지움 | 코드 | `xhs_*`·`photo*`·`clip`·`main_cut`·`product_look`·`cuts_match` |
| 줄 덧붙이기 | 없음 | — | — | `shopping_guide.md`(빈 줄 아닌 모든 줄) |

- `.md` 는 호출마다 다시 읽는다 → **재시작 불필요**(진행 중 작업은 이미 만든 프롬프트로 끝남).
- 파이썬 상수는 **재시작 필요**: `clips_v2.RECREATE_POV*/RECREATE_RULES*/FIXED_PHRASE/_TEMPLATES/MOTION_RULES`, `gemini_video` 고정 문구, `clip_checks.AI_PROMPT_*`, `photos.TEXT_REDO_SUFFIX/PERSON_REDO_SUFFIX/RECREATE_POV_LINES/reference_roles`, `direction.PRODUCT_SPACE_GUARD/MOTION_RULE/PROBLEM_WORDS/ACTION_RULES`, `hooks.PATTERNS/BANNED/script_block`, `affiliate.py` 규칙 A~E·lint, 단가표. 재시작은 `BE/devtools/restart_server.ps1`(실행 중 작업 0 확인).
- 프론트(`Documents\Codex\shorttuber-frontend`)는 새로고침으로 반영.

## 파일별

### `P/hook_candidates.md`
- 첫 줄 `[[TASK:hook_candidates]]`. 줄 머리 라벨 `상품명:`, `확정 제품 이미지 자산 id:`, 사실 줄 `- fact_xx:` 유지(모의 정규식).
- 자리 13개 `{{product_name, option, facts, assets, target, moment, pain, topic, shots, reference, patterns, pattern_focus, examples}}`.
- 스키마 `hooks.SCHEMA`(:50-54) 후보 5개. 필수 `id, pattern_id, opening_voice, opening_visual, promise, body_outline, payoff, status`. 한도 `TEXT_LIMITS`(:47), body_outline 2~5개×80자.
- `PROMPT_VERSION`(:26)은 자동으로 안 오른다. 올리면 `tests/test_shopping_guide.py:91` 같이 수정.
- 시험 `tests/test_shopping_guide.py:88-92`: `첫 화면 시험`, `글자가 없어도`, `로고로 시작`, `{{patterns}}`, `{{examples}}`.

### `P/script_product.md` · `P/script_reference.md`
- 첫 줄 `[[TASK:script]]`. `- 제품명:` 줄, 훅 블록의 `첫 대사:`·`첫 화면:` 라벨 유지(모의).
- 자리 `{{length_sec, product_name, features, price, target, appeal_points, intro_line, extra, topic_name, topic_guide, tone, chars_min, chars_max, lines_min, lines_max, look_hint, affiliate_block}}`. reference 는 `{{reference_text}}`(≤6000자) 추가. `{{affiliate_block}}` 이 비면 그 줄째 삭제.
- `<<<참고 대본 시작>>>`/`<<<참고 대본 끝>>>` 표식 유지, `- 제품명:` 이 블록보다 앞.
- 훅 블록은 `## 출력` 뒤에 붙는다(`S/pipeline/script.py:546`).
- 스키마 `SCRIPT_SCHEMA`(`script.py:61-77`): `titles[1~5], hook_title, lines[1~40]{text, kind, visual}, notes` + affiliate 면 `upload{summary, hashtags≤5}`. 한도: 줄 200자, visual 500, hook_title 40.
- 시험 `tests/test_flow_script_voice.py:224-240`(`120~150자` 문자열 포함), `tests/test_v16_affiliate.py:104-117`, `tests/test_providers.py`.

### `P/shopping_guide.md`
- `[[TASK]]` 없음. **한 항목 한 줄**(줄째 붙음). F.~Y. 글자는 사람용.
- 시험 `tests/test_shopping_guide.py:74-79` 문구 9개: `사람이 겪는 순서`, `행동 변화`, `말로 다시 읽지`, `경험한 척`, `사기 전에 확인할 조건`, `말끝`, `행동 유도는 하나`, `같은 문장을 반복하지`, `글자를 지워도`.
- 규칙 A~E 는 코드(`S/pipeline/affiliate.py:433-446`).

### `P/xhs_scene_recreate.md`
- 첫 줄 `[[TASK:xhs_scene_recreate]]`. 자리 `$coupang_title $product $line_count $line_order $lines $scene_count $scenes`. 주석 제거(시험 `tests/test_recreate_units.py:92` 가 `<!--` 없음 확인).
- 스키마 `analysis.py:287-312`: `scene_id, scene_role(5종), visual_description, face_exposure(4종), target_product(yes|no|unsure), product_box[], screen_text[]≤6, reuse_needed, reuse_reason, line_scores`. temperature 0.0, `confirm_paid` 필수.
- 장면 ID 예시를 쓰지 않는다(코드가 `[이미지 n] SSxx` 생성).

### `P/xhs_recreate_brief.md`
- 첫 줄 `[[TASK:xhs_recreate_brief]]`. 자리 `$product $product_images $lines $line_count $image_list`. 끝에 코드가 `PRODUCT_SPACE_GUARD` 를 붙임.
- 스키마 `recreate.py:401-415`(모두 필수): `line_id, pov, shot, setting_en, start_pose_en, action_en, end_state_en, image_prompt_en, motion_beats_en[3], image_prompt_ko, motion_beats_ko[3], props_en, still_ok, reuse_needed, script_mismatch, product_in_shot, notes_ko, purpose(7종), must_show_action, message_ko, must_show_ko, start_ko, end_ko, gaze_ko, continuity_ko, unverified_mechanism`.
- **2026-11-15 정리**: 규칙 17개를 A~F 여섯 묶음으로 합쳤다(금지 내용은 그대로). E5 의 `image_prompt_ko`·`motion_beats_ko` 번역 지시 유지. 시험이 보는 문구: `image_prompt_ko and motion_beats_ko`, `keyboards with printed keys`, `no more than two consecutive lines`, `Never dramatise invisible functions`.
- 옛 번호 → 새 묶음: 1·2→A1(+A3), 3→E1, 4→B1·B2, 5→C2·D1, 6→C1, 7→E2, 8→E3, 9·12·16→E4, 10→E5, 11→F, 13→D2, 14→B3, 15→B2·B3, 17→D1·E5. 새 규칙 A2 = 촬영 타입.
- **촬영 타입**: 줄에 `shot type (required): PRODUCT ONLY|USAGE SCENE|SPACE VIEW - …` 가 붙으면(코드 `recreate.build_brief_prompt`, 값 `recreate.SHOT_TYPES`) 모델 답과 상관없이 코드가 `pov` 를 `tabletop|back_view|room_wide` 로 고정한다. 줄 머리 `shot type (required):` 와 대문자 이름은 모의 제공자가 읽으므로 바꾸지 않는다. `auto` 줄에는 아무것도 붙지 않아 예전 프롬프트와 같다(브리프 지문도 같다).
- 한도 `LIMITS`(:52-54): `image_prompt_en` 700, 박자 160. 한자·가나는 `_no_cjk` 로 제거.
- 쓰임: `image_prompt_en` → `photo_recreate.md $description`, `motion_beats_en` → `clips_v2` 박자, `pov` → 사진·영상 시점 문장(11-09부터). `setting_en` 등 일부 칸은 어디에도 안 들어간다. `unverified_mechanism` → `script_mismatch` 강제 → C3 자동 통과 끔.

### `P/photo_recreate.md`
- `[[TASK]]` 없음, 영어만. 자리 `$description $look_line $frame $rules_line $pov_line $start_line`.
- 코드가 끝에 GUARD·`reference_roles`·재생성 접미사를 덧붙인다.
- 시험 `tests/test_recreate_units.py:191-197`: `first-person`·`Absolutely no text`·`Fill the whole frame` 있음, `leave calm space`·`$`·`<!--`·한글 없음. `tests/test_partner_direction_20261103.py:28-33`: GUARD 포함.

### `S/pipeline/clips_v2.py` `recreate_prompt`(코드)
- Omni 순서 `[FIRST_FRAME_TAG, pov_line, GUARD, motion, extra, rules_line, look, OMNI_FIXED]`, 최대 5,500자.
- Kling: `allowance = 2500 - fixed - extra - 10`. **2,500자 초과면 작업 전체 실패.**
- `RECREATE_MARK` 문장이 `RECREATE_FIXED_PHRASE` 안에 남아 있어야 Omni 가 '로고 유지' 문구를 다시 붙이지 않는다.
- 모든 조각 `_en_only`. 시험 `tests/test_recreate_units.py:274-291`(`first-person point of view, camera locked`, `[0-0.5s] …`, `then hold still.`, `No on-screen text`).

### 그 밖
- `P/xhs_recreate_revise.md`(문제 반영)는 줄마다 `viewpoint: <pov>` 를 받고 규칙 4 가 그 시점을 지키게 한다(11-15). `P/xhs_recreate_translate.md` 는 번역만.
- 시점 문장(코드, 재시작 필요): `photos.RECREATE_POV_LINES`(이미지), `clips_v2._POV_LINES`(영상), `clip_checks.AI_PERSON_OK_NOTE`(back_view 판정).
- `P/clip.md`·`P/main_cut.md`·`P/cuts_match.md` 는 쿠팡 재현 경로에서 안 쓴다(고쳐도 이번 결함에 영향 없음).

## 회귀 시험

```
cd "C:\Users\<사용자>\Desktop\프로그램\27. 쇼츠킷 v1.0"
python -m pytest tests/test_shopping_guide.py tests/test_v16_affiliate.py tests/test_flow_script_voice.py tests/test_photofix_rules.py tests/test_recreate_units.py tests/test_partner_direction_20261103.py tests/test_affiliate_maker_recreate.py tests/test_recreate_fix_20261030.py tests/test_providers.py tests/test_skill_upgrade_20261109.py tests/test_affmaker_simplify_20261115.py -q
```

11-09 기준 알려진 실패 1건: `test_recreate_fix_20261030::test_clip_ready_excludes_recreate_hard_fail_regardless_of_accept_setting`(모양 fail + 사람 승인 정책 — 사용자 결정 대기, 프롬프트 무관).
