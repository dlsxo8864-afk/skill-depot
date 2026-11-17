# 라이선스 정리 — llmvid-blender-cutaway-explainer

확인한 날: 2026-11-15. 조건은 바뀔 수 있으니 게시·판매 전에 각 출처를 다시 본다.

## 1. 팩에 든 것

| 파일 | 내용 | 출처 |
|---|---|---|
| `SKILL.md`, `LICENSES.md` | 절차와 설명 | 이 팩을 만들면서 직접 썼다 |
| `example/*.py`, `example/script.json` | 공통 예제 대본을 실제로 만든 스크립트와 대본 | 직접 썼다. 다른 사람의 코드·그림을 옮겨 온 것은 없다 |

- 팩 스크립트에 따로 라이선스를 붙이지 않았다. 받은 사람이 자기 영상을 만드는 데 고쳐 쓰라는 용도다.
- `create_scene.py`, `render.py`는 블렌더 파이썬 API(`bpy`)를 쓴다. 블렌더 재단은 "`bpy`를 쓰는 스크립트를 공개 배포할 때는 GPL 호환 라이선스로 내야 한다"고 안내한다(https://www.blender.org/about/license/ 의 Add-ons 항목). 이 팩을 밖으로 다시 배포할 사람은 이 조건을 확인한다.
- 팩에 넣지 않은 것: 음성, 렌더한 프레임, `.blend`, 글꼴 파일.
- 참고한 영상의 소재(캐릭터, 장면, 문구)는 쓰지 않았다. 연출 방식만 참고했다.

## 2. 팩이 쓰는 도구

| 도구 | 라이선스 | 결과물에 미치는 것 |
|---|---|---|
| Blender 5.x | GNU GPL(v3 이상으로 배포) | 블렌더로 만든 그림·영상·`.blend`는 만든 사람 것이다. 상업 이용에 제한이 없다(같은 페이지의 Your Artwork 항목) |
| ffmpeg | 빌드에 따라 LGPL 또는 GPL | 인코딩한 영상의 권리에는 영향이 없다 |
| Python | PSF License | 없음 |
| Pillow | MIT-CMU(HPND) | 없음 |

## 3. 외부 소재

없다. 3D 모델·텍스처·HDRI·그림·음원을 내려받지 않는다. 장면은 블렌더 기본 도형, 그림은 Pillow 코드, 효과음은 ffmpeg `aevalsrc` 합성이다.

## 4. 글꼴

- 팩에 글꼴 파일은 없다. `fontfind.py`가 PC에서 찾는다: Noto Sans KR → 맑은 고딕 → (macOS) Apple SD Gothic Neo → (리눅스) Noto Sans CJK.
- Noto Sans KR: SIL Open Font License 1.1. 영상에 써도 되고 상업 이용도 된다.
- 맑은 고딕, Apple SD Gothic Neo: 운영체제에 딸린 글꼴이다. 각 회사의 글꼴 라이선스를 따른다. 조건이 분명해야 하는 게시·상업용이면 Noto Sans KR을 설치해 쓰거나 `--font`로 권리가 분명한 글꼴을 넘긴다.
- `finish.py`는 찾은 글꼴 파일을 작업 폴더의 `fonts/`에 복사한다(자막 렌더용). 이 복사본을 다른 사람에게 넘기지 않는다.

## 5. 음성

내레이션 음성은 사용자가 준비한다. TTS로 만든 음성은 그 서비스의 이용 조건(상업 이용, 표시 의무)을 사용자가 확인한다.

## 6. 대본

예제 대본 「점심 메뉴 정하는 법」의 문구는 예시다. 새 영상에는 사용자의 대본을 쓴다.
