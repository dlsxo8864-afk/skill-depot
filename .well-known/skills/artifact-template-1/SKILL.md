---
name: artifact-template-1
description: "직장 썰 썸네일 템플릿 1. Use when the user selects this template, names 템플릿 1 or 템플릿1, or invokes $artifact-template-1. Generate photographs separately without text; compose all typography and effects with the retained Remotion template."
---

# 템플릿 1 — 직장 썰 썸네일

사진 원본과 글자/효과를 분리해 반복 사용한다. 완성 썸네일을 AI로 통째로 다시 편집하지 않는다.

## 먼저 읽을 파일
1. `artifact-template.json`의 경로는 이 스킬 폴더 기준으로 해석한다.
2. `assets/reference.png`와 `assets/preview.png`는 구도·색상·서체를 확인하는 완성형 참고 이미지다. 두 파일은 수정하지 않는다. 이 PNG들을 글자 수정용 AI 편집 입력으로 보내지 않는다.
3. 구현의 기준은 `assets/template-1/remotion/src/ThumbnailTemplate1.tsx` 및 `thumbnail-template-1.css`다.
4. `assets/template-1/WORKFLOW.md`, `style.json`, `manifest.json`을 확인한다. 원래 이미지형 스타일은 `assets/template-1/references/style-original-ep1.png` 및 `style-original-ep2.png`로 확인한다. 이 파일은 외형 비교용이며 이미지 편집 입력으로 보내지 않는다.

## 제작 절차
1. 회차, 제목 두 줄, 인물·장면, 참고 얼굴을 사용자의 요청과 현재 대화에서 확보한다. 근거 없는 사건을 추가하지 않는다.
2. 이 스킬의 `assets/template-1/remotion` 폴더를 새 작업 폴더로 복사한다. 스킬 원본에서 npm 설치나 렌더를 실행하지 않는다. node_modules와 비밀 파일은 보관하지 않는다.
3. 사진 변경이 요청된 경우에만 imagegen 스킬 또는 사용자가 지정한 제공자를 사용해 새 사진을 생성한다. 사진에는 글자·숫자·로고·워터마크·배지·인위적인 그라디언트가 없어야 한다. 인물 원본은 `assets/template-1/references`, 글자 없는 승인 사진은 `assets/template-1/backgrounds`에서 찾는다. 기존 완성 PNG와 그 파생본을 반복 재편집하지 않는다.
4. 새 배경 PNG를 작업 폴더의 `public/images/template1`에 저장한다. 원본을 그대로 보관한다. 문구·EP·색상·효과 변경 요청에는 기존 배경 PNG를 재생성하거나 덮어쓰지 않는다.
5. `presets/EP1.json` 또는 `EP2.json`을 복사해 episode, line1, line2, backgroundSrc를 바꾼다. 시리즈명과 기본 하단은 각각 ‘회사에선 말 못 한 썰’, ‘사연 재구성’이다. 두 줄이 길면 line1FontSize, line2FontSize, line1ScaleX/Y, line2ScaleX/Y, line1Top, line2Top를 조정하며 글자와 인물이 잘리지 않게 한다.
6. Remotion 스킬을 따르고, 폰트가 로딩된 후 native CSS/Remotion 레이어로 합성한다. 배지, 외곽선, 입체 그림자, 그라디언트, 작은 구분선도 모두 코드 레이어다. AI가 포함한 글자를 사진에 구워 넣지 않는다.
7. npm ci 후 `npx remotion still Template1 final.png --props presets/EP2.json --image-format=png` 형식으로 출력한다. 프리셋의 backgroundVisible을 false로 복사한 별도 JSON으로 투명 오버레이도 렌더한다.
8. 1080×1920 PNG와 약 324px 폭 축소본을 확인한다. 한글 오탈자, 여백, 얼굴 가림, 선명도, 투명 오버레이의 alpha를 검수한다. 사진 수정이 없는 작업에서는 배경 SHA256이 바뀌지 않았는지 확인한다.
9. 글자 없는 사진, 투명 글자/효과 PNG, 최종 합성 PNG, 사용한 props JSON, 소스/폰트와 라이선스를 별도로 보관한다. 최종 합성 PNG는 최종 업로드용 산출물이며 다음 변경의 편집 원본은 아니다.

## 고정 스타일
- 1080×1920, 세로 9:16
- 노란 제목 #FFD245 / 흰 반전 문구 #FAFAFA / 차콜 #07090E / 빨간 EP 배지
- 사진의 얼굴은 상·중단, 제목은 하단 두 줄
- 큰 글자 SB Aggro Bold, 상단 Noto Sans KR Black 이탤릭, 하단 Noto Sans KR Regular. 각 폰트와 공식 라이선스 동봉
- 하단 ‘사연 재구성’
- 제목은 세로로 길고 단어 공백이 좁은 비율을 유지한다. 기본 headlineFont는 aggro다. 갈색/회색의 다층 입체 그림자 대신 얇은 검정 외곽과 부드러운 검정 그림자를 쓴다.
- 회차별 크기·위치는 최신 presets/EP1.json 및 EP2.json을 기준으로 한다.
- 사용자 요청 없이 구도·글꼴·배지 위치를 바꾸지 않는다. 새로운 디자인이 요청되면 다른 템플릿 번호로 보관한다.

## 유지보수
개인 템플릿 갱신 스크립트는 기본 imagegen 워크플로를 다시 쓸 수 있다. 갱신 뒤에는 이 파일의 ‘사진 생성 → native 텍스트 합성’ 절차를 다시 적용하고 단일 합성 이미지 재편집 단계가 되살아나지 않았는지 확인한다.
