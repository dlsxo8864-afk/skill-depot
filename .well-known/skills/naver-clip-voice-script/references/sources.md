# 출처와 근거 수준

조사일 2026-11-06. 공식 > 시험 기록 > 실무 글 > 홍보 글 순서로 믿었다. 수치는 시작점이고 들어 보고 정한다.

## 공식 문서

- Gemini 음성 생성: https://aistudio.google.com/docs/speech-generation — 3.8 모델 이름, 목소리 30종, 글 그대로 읽기, style 위치, 꺾쇠 태그, 한국어 글에 영어 태그, 확장 목소리 목록.
- Firebase `SpeechMetadata`: https://github.com/firebase/firebase-ios-sdk/blob/main/FirebaseAI/Sources/Types/Public/SpeechMetadata.swift — TextPart 에 붙는 speaker·style, 글은 그대로 읽음.
- 구글 음성 감독 스킬: https://github.com/GoogleCloudPlatform/genmedia-creative-studio (`genmedia-voice-director`, `references/model-differences.md`) — style 15단어 안쪽, 글 칸에 머리글 금지, 3.1과 3.8 차이, 다시 만들어 듣기.
- 구글 블로그: https://dev.to/googleai/how-to-prompt-gemini-31s-new-text-to-speech-model-24bb — 3.1 프로필·장면·노트 방식. 3.8에서는 쓰지 않는다.
- ElevenLabs 모범 사례: https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices.md — 태그, 말줄임표, 정규화, 목소리와 태그 맞추기.
- ElevenLabs 공식 스킬: https://github.com/elevenlabs/skills (text-to-speech) — v4 설정 칸, language_code, 요청 이어 붙이기.
- ElevenLabs 태그 목록: https://elevenlabs.io/blog/elevenlabs-audio-tags-list — 분류, 쉼표로 묶기, 절마다 태그 하나.

## 시험 기록·개발 글

- LiveKit: https://livekit.com/blog/gemini-3.1-flash-tts-prompting-guide — 머리글을 읽어 버림, 소리를 죽이는 낱말, 쉼표와 마침표 차이. 3.1 기준이라 일부만 썼다.
- Morphic v4 안내: https://morphic.com/resources/how-to/eleven-v4-guide — v4 는 속도·스타일 없음, 언어마다 원어민 억양, 두세 번 만들어 고르기.

## 한국어 실무 글(수치 근거 없음, 저자도 출발점이라고 씀)

- 일레븐랩스 한국어 가이드: https://tilnote.io/pages/69fb2a5e61d4abc7e5bf841f — 한 문장 한 생각, 숫자·약어 풀기, 합니다체에 ~죠 섞기, 숏폼 값, 어려운 문장으로 10초 시험.
- https://carat.im/blog/elevenlabs-usage-guide — 안정성 75, 유사도 85, 표현 20~30(내레이션 기준. 숏폼에는 높다).
- https://www.elancer.co.kr/blog/detail/1047 — 말하기용으로 고치기, 톤 2~3개 비교, 후처리.
- 타입캐스트 쇼츠 문서: https://typecast.ai/docs/ko/cli-reference/use-cases/shorts-generation — 25초에 훅 1, 본문 3, 행동 1.
- 타입캐스트 맛집 크리에이터 소개: https://typecast.ai/kr/learn/the-trending-restaurant-review-creators-from-youtube-shorts/ — 자사 홍보 글. 정보는 화면, 소리는 이야기로 나누는 방식만 참고.
- 고객사 블로그의 "첫 3초 65% 이탈" 같은 수치는 원문을 확인하지 못해 쓰지 않았다.

## 숏폼 구조 스킬

- https://github.com/mohitagw15856/pm-claude-skills (short-form-script) — 0~3초 훅, 왜 볼까, 내용, 행동 하나. 말·화면 글·영상 지시를 칸으로 나누기.
- eddiebelaval/squire reel-script-writer — 내용이 일반론이라 쓰지 않았다.

## 말 속도

- 서울 자유 발화: 쉼 포함 초당 약 4.0~4.2음절, 쉼 제외 약 4.5~4.8음절. 젊을수록 빠름. 한국어 발화 속도 연구 https://scholar.korea.ac.kr/handle/2021.sw.korea/85439 와 검색으로 확인한 논문 요약 기준.
- 이번 실측: 유튜브 한국 맛집 쇼츠 공개 자막(자동 자막 포함). 집계는 `실측` 항목. 자동 자막이 말을 빠뜨리므로 실제보다 조금 낮게 나온다. 상위 조회 영상만 고른 표본이 아니다.

## 실측

**유튜브 한국 맛집 쇼츠 공개 자막(2026-11-06).** 검색어 44개로 75초 이하 영상 221개 메타데이터, 그중 자막을 받은 84개, 말이 영상 대부분을 채운 60개 기준. 영상은 받지 않았고 문장은 옮기지 않았다.

- 초당 음절(쉼 포함): 중앙값 4.20, 하위 25% 3.40, 상위 25% 4.76.
- 자막이 없는 영상이 많고(429 제한 57회 포함), 자동 자막은 말을 빠뜨리며, 맛집이 아닌 영상도 일부 섞여 있다. 순서를 정하는 정도로만 쓴다.
- 어절 끝 비율: '~니다' 17%, '~요' 19%. 두 말투가 섞여 쓰인다. 영상별 말투 판정은 오차가 커서 쓰지 않았다.

**Gemini 3.8 실제 시험(2026-11-06, 같은 문장 30자).**

| 조건 | 초당 음절 | 중앙 음높이 | 받아쓰기 일치 |
|---|---|---|---|
| Kore + 예전 지시(담백하게, 감독 노트) | 4.63 | 198Hz | 1.00, 문장부호 없음 |
| Kore + style(찐친) | 4.89 | 232Hz | 1.00, 느낌표·물음표 찍힘 |
| 요리 방송 진행자 9 + style(찐친) | 4.55 | 250Hz | 1.00 |

- 같은 목소리도 style 한 줄로 음이 올라가고 빨라진다. 수치는 참고이고 최종 판단은 사람이 듣는다.
- 한국어 전용 목소리(`ko-kr-*`, 117개)는 `prebuiltVoiceConfig.voiceName` 에 그대로 넣으면 된다. 서울말 103, 부산말 14. 역할·나이·높낮이·성격 설명이 있다. 샘플 주소는 없다.
- 말투가 강하면 '헉!', '아!' 같은 말을 덧붙이는 목소리가 있다(후보 15개 중 4개). 받아쓰기로 잡는다.
- ElevenLabs `eleven_v4` 기본 목소리(Laura)로 한국어 30자: 받아쓰기 1.00, 약 42크레딧.

## 이 프로젝트의 기존 자료

- 업무/15 `인기 클립 카피 패턴 v1.3.md`(네이버 클립 62개), `네이버 클립 맛집 숏폼 리서치.md`, `네이버 클립 영상 길이 조사 v1.0.md`(860클립).
- 쇼츠킷 `docs/SHOPPING_SHORTS_GUIDE.md`: 화면과 말의 역할, 말끝, 행동 하나, 조건 한 줄, 믿지 않은 수치 목록.
- 쇼츠킷 `docs/ELEVENLABS_VOICE_GUIDE.md`.

## 법규(법률 자문 아님)

- 공정위 추천·보증 심사지침 개정, 2026-06-01 시행: AI 가상인물 표시 의무. 표시해도 실제 경험과 다르면 부당 광고가 될 수 있다. https://ditoday.com/?p=146111 , https://www.digitalmarketer.co.kr/insights/ai-ad-labeling-korea-guide
- 내레이션 음성만 AI 인 경우를 직접 정한 조항은 찾지 못했다. 다만 '먹어 봤더니' 같은 체험 대사는 표시와 별개로 고쳐야 한다는 해석이 있다.
- AI 기본법 제31조는 사업자 의무로, AI 소재를 쓴 광고주 전체를 뜻하지 않는다는 해석. 정보통신망법 개정안(의안 2216186)은 미시행. https://www.i-boss.co.kr/ab-74668-5969
- 식품표시광고법 개정으로 AI 가상 전문가 추천 광고 금지, 2026-11-27 시행으로 소개됨. 원문을 확인해야 한다.
- 공정위 AI 표시·광고 가이드라인 초안 의견 수렴 2026-10-22~11-11. 확정 전이다.
- 네이버 클립: 업로드 화면에 AI 활용 설정, 광고·협찬 설정, 장소 태그가 있다(업무/15 리서치).

## 사진 프롬프트(공식, 2026-11-09 확인)

- 여러 장이면 사진마다 앞에 번호를 붙인다, 해상도는 높게: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/image-understanding
- 과제 전에 사진을 먼저 설명하게 하고, 일을 작은 단계로 나눈다: https://aistudio.google.com/docs/files (Prompting with media files)
- 사진 1장 기본 1120토큰(Gemini 3), MEDIUM 560, 부분별 설정은 실험 기능: https://aistudio.google.com/docs/media-resolution

앱 실측(gemini-3.8-flash): 사진 읽기 thinking low 4.4초(기본 8.0초), 판정은 같음. `minimal` 은 400. `responseSchema` 는 다시 쓰기에서 70초 넘게 멈추거나 글이 깨졌다(빼면 4초, 깨끗함).

## 찾지 못한 것

- 한국어 상용 TTS 순위의 믿을 만한 공개 수치.
- 레딧에서 한국어 ElevenLabs 목소리를 직접 비교한 글. 일반 조언만 있었다(v3에서 권장 목소리를 쓰라, stability 를 너무 올리지 말라).
- 맛집 쇼츠 말투를 분석한 공개 연구. 그래서 공개 자막을 직접 쟀다.
