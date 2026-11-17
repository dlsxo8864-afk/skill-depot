# 템플릿 1 — 직장 썰 썸네일

1080×1920, 세로 9:16. 배경 사진과 글자/효과를 분리한 Remotion 템플릿이다.

## 보관 구조
- public/images/template1/: 글자 없는 원본 사진. 문구 수정 때문에 변경하지 않는다.
- public/fonts/: SB Aggro Bold(제목), Noto Sans KR Black(상단), Noto Sans KR Regular(하단). 공식 배포처와 라이선스를 동봉한다.
- src/ThumbnailTemplate1.tsx: 회차, 제목, 배경, 글자 크기를 받는 재사용 컴포넌트.
- src/thumbnail-template-1.css: 위치, 색상, 그림자, 외곽선, 그라디언트, 배지.
- presets/EP1.json, EP2.json: 회차별 내용과 크기 설정.
- 글자가 포함된 완성 이미지를 AI 재편집 입력으로 반복 사용하지 않는다.

## 설치 및 출력
이 폴더에서 npm ci 후 실행한다.

npx remotion still Template1 EP1.png --props presets/EP1.json --image-format=png
npx remotion still Template1 EP2.png --props presets/EP2.json --image-format=png

투명 글자 레이어는 프리셋에서 backgroundVisible을 false로 바꾸고 별도 파일로 출력한다.
gradientVisible을 true로 두면 글자 뒤 음영까지 투명 PNG에 포함된다.

## 다음 회차
1. 인물/상황에 맞는 새 사진을 글자, 배지, 로고, 워터마크, 인위적 그라디언트 없이 생성한다.
2. 새 PNG를 public/images/template1/에 넣는다.
3. 새 프리셋 JSON을 만들고 episode, line1, line2, backgroundSrc만 바꾼다.
4. 문구가 길면 line1FontSize, line2FontSize, line1ScaleX/Y, line2ScaleX/Y, line1Top, line2Top를 조정하되 줄바꿈과 구도를 먼저 점검한다.
5. PNG를 렌더하고 1080px 원본과 324px 축소본에서 문구와 얼굴이 가려지지 않는지 확인한다.
6. 원본 사진, 투명 레이어, 최종 PNG를 각각 보관한다. 최종 PNG로 원본을 덮어쓰지 않는다.

## 스타일
- 시리즈: 회사에선 말 못 한 썰
- EP 배지: 빨간색, 흰색 이탤릭
- 첫 줄: #FFD245, 얇은 검정 외곽과 부드러운 검정 그림자
- 둘째 줄: #FAFAFA, 부드러운 검정 그림자
- 하단: 사연 재구성
- 그라디언트와 글자 효과는 전부 CSS/Remotion native 레이어.
- 폰트는 로컬 파일 로딩이 끝난 뒤 렌더한다. 폰트 실패 시 조용한 대체 출력 대신 오류로 중단한다.

## 2026-11-04 원본 스타일 보정
- 기본 제목은 어그로체 Bold(headlineFont: aggro). Black Han/Gmarket는 비교용 옵션이며 기본값이 아니다.
- 원본 이미지형 참고: references/style-original-ep1.png, style-original-ep2.png. 사진 수정 입력으로 사용하지 않는다.
- 제목을 세로로 길게, 단어 공백을 좁게 유지한다. 갈색/회색 입체 돌출 효과는 사용하지 않는다.
- 회차별 제목의 크기와 위치는 presets/EP1.json, EP2.json이 기준이다.
