# 라이선스 (llmvid-remotion-anime)

## 팩에 들어 있는 것

| 파일 | 무엇 | 라이선스 |
|---|---|---|
| `example/src/*`, `example/package.json`, `example/remotion.config.ts`, `example/tsconfig.json` | 쇼츠킷에서 공통 예제 대본(「점심 메뉴 정하는 법」) 를 만들 때 쓴 예제 코드 | 쇼츠킷 'LLM 영상 템플릿' 사용자가 고쳐 쓰라고 넣은 예제다. 따로 오픈소스 라이선스를 붙이지 않았다 |
| `example/public/fonts/BlackHanSans-Regular.ttf` | 제목 글꼴 Black Han Sans | SIL Open Font License 1.1. Copyright 2015 The Black Han Sans Project Authors (https://github.com/zesstype/Black-Han-Sans). 전문은 `example/public/fonts/OFL-BlackHanSans.txt` |

- OFL 글꼴은 영상·인쇄물에 자유롭게 쓸 수 있다. 글꼴 파일을 남에게 넘길 때는 라이선스 문서를 함께 둔다. 글꼴 파일만 따로 파는 것은 안 된다.
- 예제 안의 대본 문구(「점심 메뉴 정하는 법」)는 보기용이다. 새 영상은 자기 대본으로 만든다.

## 팩에 없고, 설치해서 쓰는 것

| 도구 | 라이선스 | 비고 |
|---|---|---|
| Remotion 4.0.540 (`remotion`, `@remotion/cli`, `@remotion/media`, `@remotion/captions`) | Remotion License | 개인, 비영리 단체, 직원 3명 이하 영리 회사는 무료. **직원 4명 이상인 영리 회사는 유료 회사 라이선스가 필요하다.** https://www.remotion.dev/license |
| React 19.3.1, React DOM | MIT | |
| TypeScript 5.9.3 | Apache-2.0 | 타입 검사에만 쓴다 |
| Chrome Headless Shell | Remotion 이 렌더할 때 쓰는 브라우저 | 없으면 Remotion 이 내려받는다 |
| ffmpeg | LGPL/GPL(빌드에 따라 다름) | 효과음 합성과 결과 확인에 쓴다. 영상에 들어가지 않는다 |

## 팩에 없고, 쓰는 사람이 준비하는 것

- **본문 글꼴.** 팩에는 넣지 않았다(Noto Sans KR 파일은 6MB). 렌더할 때 PC에 깔린 글꼴을 쓴다.
  - Noto Sans KR: SIL OFL 1.1. 영상에 써도 된다.
  - 맑은 고딕(Malgun Gothic): Windows 에 딸린 Microsoft 글꼴이다. 글꼴 파일을 복사해 남에게 넘기면 안 된다. 게시용 영상이면 OFL 인 Noto Sans KR 을 깔아 쓰는 쪽이 안전하다.
- **음성.** 팩에 없다. 녹음하거나 TTS 로 만든 음성의 사용 조건은 가져온 사람이 확인한다.
- **효과음.** 팩에 없다. `SKILL.md` 의 ffmpeg 명령으로 직접 합성한 소리는 스스로 만든 것이라 출처 문제가 없다.

## 쓰지 않는 것

영상 생성 AI, 이미지 생성 AI, 유료 API, 외부 그림·영상 소재.
