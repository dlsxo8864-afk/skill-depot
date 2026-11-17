# 라이선스 정리 — llmvid-blender-toon

확인한 날: 2026-11-10. 조건은 바뀔 수 있으니 게시·판매 전에 각 출처를 다시 본다.

## 1. 팩에 든 것

| 파일 | 내용 | 출처 |
|---|---|---|
| `SKILL.md`, `LICENSES.md` | 절차와 설명 | 이 팩을 만들면서 직접 썼다 |
| `example/*.py` | 썰 EP3를 만든 스크립트의 사본 | 직접 썼다. 다른 사람의 코드를 옮겨 온 것은 없다 |

- 팩 스크립트에 따로 라이선스를 붙이지 않았다. 받은 사람이 자기 영상을 만드는 데 고쳐 쓰라는 용도다.
- `build_ssul.py`, `rnd_ssul.py`, `make_toon.py`, `probe.py`, `listobj.py`는 블렌더 파이썬 API(`bpy`)를 쓴다. 블렌더 재단은 "`bpy`를 쓰는 스크립트를 공개 배포할 때는 GPL 호환 라이선스로 내야 한다"고 안내한다(https://www.blender.org/about/license/ 의 Add-ons 항목). 이 팩을 밖으로 다시 배포할 사람은 이 조건을 확인한다.
- 팩에 넣지 않은 것: 음성, 효과음 파일, 렌더한 프레임, `.blend`, Poly Haven 소재, 글꼴 파일.

## 2. 팩이 쓰는 도구

| 도구 | 라이선스 | 결과물에 미치는 것 |
|---|---|---|
| Blender 5.x | GNU GPL(v3 이상으로 배포) | 블렌더로 만든 그림·영상·`.blend`는 만든 사람 것이다. 상업 이용에 제한이 없다(같은 페이지의 Your Artwork 항목) |
| ffmpeg | 빌드에 따라 LGPL 또는 GPL | 인코딩한 영상의 권리에는 영향이 없다. ffmpeg 실행 파일을 다시 배포할 때만 해당한다 |
| Python | PSF License | 없음 |
| Pillow | MIT-CMU(HPND) | 없음 |

H.264(libx264)·AAC로 인코딩한다. 일반적인 영상 게시에는 문제가 되지 않지만, 인코더를 제품에 넣어 파는 경우는 특허 라이선스를 따로 확인한다.

## 3. 팩이 쓰는 외부 소재(팩에 없음, 따로 받는다)

Poly Haven (https://polyhaven.com/license) — 모든 소재가 **CC0**다. 상업 이용 가능, 출처 표시 의무 없음, 재배포 가능.

| 종류 | 이름 | 해상도 |
|---|---|---|
| 모델 | `desk_lamp_arm_01`, `classic_laptop`, `office_notepads`, `alarm_clock_01` | 1k |
| 텍스처 | `wood_table_worn`, `painted_plaster_wall` | 2k |
| HDRI | `studio_small_09` | 2k |

- `dl_assets.py`는 Poly Haven 공개 API(api.polyhaven.com)로 받는다. API 이용 조건(https://github.com/Poly-Haven/Public-API/blob/master/ToS.md): 무료이고 상업 이용도 된다. 요청에 소프트웨어 이름이 든 User-Agent를 넣어야 한다(스크립트는 `blender-skill-test/1.0`을 넣는다). 서버에 부담을 주는 사용은 금지다.
- 내려받기는 사용자 허가를 받은 뒤에만 한다.
- CC0는 저작권만 다룬다. 소재에 실제 상표나 제품 디자인이 보이면 상표권은 별개다. 예제 장면의 네 모델에 상표가 보이는지는 따로 점검하지 않았다. 게시 전에 렌더를 확대해 확인하고, 소품을 바꿀 때도 같은 확인을 한다(같은 묶음의 책상 인서트 예제에서 쓴 `Camera_01`에는 라이카 상표가 보인다. 게시용이면 쓰지 않는다).

## 4. 글꼴

- 팩에 글꼴 파일은 없다. `fontfind.py`가 PC에서 찾는다: Noto Sans KR → 맑은 고딕 → (macOS) Apple SD Gothic Neo → (리눅스) Noto Sans CJK.
- Noto Sans KR: SIL Open Font License 1.1. 영상에 써도 되고 상업 이용도 된다.
- 맑은 고딕, Apple SD Gothic Neo: 운영체제에 딸린 글꼴이다. 각 회사의 글꼴 라이선스를 따른다. 조건이 분명해야 하는 게시·상업용이면 Noto Sans KR을 설치해 쓰거나 `--font`로 권리가 분명한 글꼴을 넘긴다.
- `finish.py`는 찾은 글꼴 파일을 작업 폴더의 `fonts/`에 복사한다(자막 렌더용). 이 복사본을 다른 사람에게 넘기지 않는다.

## 5. 음성·효과음

- 내레이션 음성은 사용자가 준비한다. TTS로 만든 음성은 그 서비스의 이용 조건(상업 이용, 표시 의무)을 사용자가 확인한다.
- 휴대폰 진동음·도장 소리·기본 전송음은 ffmpeg `aevalsrc`로 그 자리에서 합성한다. 외부 음원이 아니다.
- `--sfx-send`로 넘기는 효과음 파일은 출처와 조건을 사용자가 확인한다.

## 6. 대본

예제 대본(썰 EP3)의 문구는 예시다. 새 영상에는 사용자의 대본을 쓴다.
