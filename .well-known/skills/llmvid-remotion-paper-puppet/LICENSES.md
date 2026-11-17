# 라이선스 (llmvid-remotion-paper-puppet)

확인한 날: 2026-11-10

## 팩에 들어 있는 것

| 파일 / 폴더 | 내용 | 라이선스 |
|---|---|---|
| `example/src/*`, `example/package.json`, `example/remotion.config.ts`, `example/tsconfig.json`, `example/public/README.txt` | 관절 종이인형풍 사무실 썰(프린터 옆자리)을 만들기 위해 작성된 Remotion 예제 코드 전체 | 이 프로젝트에서 LLM으로 직접 작성한 코드다. 외부 그림·소리·글꼴이 들어 있지 않으며, `package.json`의 license는 UNLICENSED로 따로 라이선스를 붙이지 않았다 |

- 예제 안의 대본 문구(「점심 메뉴 정하는 법」)는 예시용 데이터다. 실제 영상 제작 시에는 사용자의 대본으로 교체하여 사용한다.

## 팩에 없고, 설치해서 쓰는 것

| 도구 / 라이브러리 | 버전 | 라이선스 | 비고 |
|---|---|---|---|
| Remotion (`remotion`, `@remotion/cli`, `@remotion/media`, `@remotion/captions`) | 4.0.542 | Remotion License | 개인, 비영리 단체, 직원 3명 이하 영리 회사는 무료. **직원 4명 이상인 영리 회사는 상용 유료 라이선스가 필요하다.** (https://www.remotion.dev/docs/license) |
| React, React DOM | 19.3.1 | MIT | 리액트 라이브러리 |
| TypeScript | 5.9.3 | Apache-2.0 | 정적 타입 검사에만 쓴다 |
| Chrome Headless Shell | - | - | Remotion이 렌더할 때 쓰는 브라우저다. 없으면 Remotion이 내려받는다(사용자 허락 대상). 라이선스는 확인하지 못했다 |
| ffmpeg · ffprobe | 시스템 설치본 | LGPL 또는 GPL (빌드 구성에 따라 다름) | 음성 구간 감지 및 렌더 결과 검증에 사용한다. 영상 파일 내부에 코드가 포함되지 않는다 |

## 팩에 없고, 쓰는 사람이 준비하는 것

- **자막 글꼴**: 팩에는 글꼴 파일이 포함되어 있지 않다. 렌더 시 `public/fonts/CaptionKR-Bold.ttf`가 없으면 시스템에 설치된 Noto Sans KR → 맑은 고딕 순으로 글꼴을 찾는다.
  - Noto Sans KR: SIL Open Font License 1.1.
  - 맑은 고딕: Windows에 딸린 글꼴이다. Windows 글꼴 라이선스를 따른다.
  - 별도 글꼴 파일을 `public/fonts/`에 추가하여 배포할 경우 해당 폰트의 라이선스를 직접 확인해야 한다.
- **음성(나레이션)**: 팩에 포함되어 있지 않다. 사용자가 직접 녹음하거나 TTS 도구로 생성하여 `public/audio/`에 배치하며, 사용 권리는 사용자가 직접 확인한다.
- **배경음(BGM)**: 팩에 포함되어 있지 않다. 배경음을 넣을 경우 상업적 이용 및 저작권 조건을 사용자가 확인해야 한다.

## 쓰지 않는 것

영상 생성 AI, 이미지 생성 AI, 유료 API, 외부 이미지·동영상 에셋.
