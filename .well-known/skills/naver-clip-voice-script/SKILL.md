---
name: naver-clip-voice-script
description: Use when writing Korean narration for short restaurant or food promo videos (네이버 클립, 쇼츠, 릴스), choosing or directing Korean AI voices (Gemini TTS, ElevenLabs), or when a Korean voiceover sounds flat, robotic or boring (무미건조, 심심함, 말투 어색, AI 티, 재미없음). Also when changing the 쇼츠킷 네이버 클립 식당홍보 tab's script or voice prompts.
---

# 한국어 식당 숏폼 대본·목소리

## 핵심

밋밋한 결과의 원인은 **대본 → 지시 방식 → 목소리** 순서다. 목소리부터 바꾸지 않는다. 사실은 지어내지 않고, 재미는 말의 리듬과 보이는 것의 묘사에서 만든다.

## 순서

1. 사실 자료를 나눈다: 확인된 정보, 사진에 보이는 것, 둘 다 아닌 것(쓰지 않음). 사진은 한 장씩 크게 읽어 보이는 것·할 수 있는 말·가능한 움직임을 먼저 적는다.
2. 대본 형식과 말투를 고른다. 표는 [script-craft.md](references/script-craft.md).
3. 대본을 사진 → 보이는 것 → 말 → 장면 순서로 쓴다. 자막 글(text)과 읽는 글(say)을 나눈다. 숫자는 say 에서 한글로 푼다.
4. 점검한다: 먹어 본 척, 근거 없는 숫자, 뻔한 말, 같은 말끝 세 줄, 첫 줄 길이, 상호 유무, 컷의 사진과 글·제목이 실제로 맞는지.
5. 같은 문장으로 목소리 2~3개를 듣고 고른다. 지시법은 [voice-direction.md](references/voice-direction.md).
6. 받아쓰기로 대본과 맞춰 본다. 상호가 들려야 통과다.

## 빠른 기준

| 항목 | 기준 |
|---|---|
| 말 속도 | 쉼 포함 초당 약 4.2~4.8음절. 15초 약 65음절, 30초 약 135음절 |
| 첫 줄 | 2초 안에 끝. 질문, 반전, 장면 하나. 인사와 상호로 시작하지 않음 |
| 한 줄 | 5~24음절. 한 생각. 짧은 줄과 긴 줄을 섞음 |
| 말끝 | 같은 말끝 두 줄 연속 금지. 이어지는 말(~고요, ~는데)을 섞음 |
| 중간 | 한 번 꺾기(근데요, 진짜는요) |
| 끝 줄 | 상호와 행동 하나 |
| 컷 길이 | 음성 길이로 정함. 장면 길이에 음성을 맞춰 늘이거나 줄이지 않음 |
| Gemini 3.8 | 글은 그대로, 말투는 `speechMetadata.style` 15단어 안쪽. 대본 전체를 이어 읽혀 쉼에서 나눔 |
| ElevenLabs v4 | 줄마다 `previous_text`·`next_text`, 태그는 줄당 하나, stability 0.3~0.5 |

## 하지 말 것

- 먹어 본 척: 먹어 봤는데, 다녀왔어요, 내돈내산, 단골, 인생 맛집, ~더라고요. 근거: [sources.md](references/sources.md) 법규 항목.
- 맛 단정: 맛있어요. 대신 윤기, 김, 두께, 색처럼 보이는 것으로 말한다.
- 지시문에 담백하게, flat, quiet, calm, 속삭임을 쓰는 것. 소리가 죽는다.
- Gemini 3.8 글 칸에 감독 노트를 넣는 것. 글은 그대로 읽는 게 공식 동작이다.
- 줄마다 따로 만들고 앞뒤 문맥을 안 주는 것. 줄 끝마다 말이 끝나서 낭독처럼 들린다.
- 수치(배속표, BPM)를 믿는 것. 들어 보고 정한다.

## 앱에 반영된 곳(같이 고친다)

`27. 쇼츠킷 v1.0/server/`의 `prompts/restaurant_script.md`, `prompts/restaurant_photo_read.md`(사진 읽기), `prompts/restaurant_fit_check.md`(사진·글 검사), `prompts/restaurant_rethink.md`(컷 다시 쓰기, 규칙은 script.md 에서 가져옴), `presets/restaurant_voice.json`, `presets/restaurant_formats.json`, `restaurant_script.py`(읽기 변환·점검), `restaurant_fit.py`(사진·글 맞추기), `restaurant_voice.py`(합성). 지침은 [script-craft.md](references/script-craft.md)의 '사진과 글 맞추기'.
