---
name: llmvid-blender-toon
description: 대본과 음성으로, 사람 없이 휴대폰 화면·서류·도장 같은 물건만 나오는 카툰풍(단계 명암 + 잉크선) 세로 영상(1080×1920)을 만든다. 영상 생성 AI 없이 블렌더로 책상 장면을 코드로 조립해 EEVEE + Freestyle로 렌더하고 ffmpeg로 음성·자막·효과음을 붙인다. 메신저 대화가 중심인 썰을 만화 느낌으로, 빠르게 만들 때 쓴다.
---

# 블렌더 카툰 사물극 (llmvid-blender-toon)

검증된 예제와 절차를 묶은 팩이다. 버튼 하나로 끝나는 자동 도구가 아니다.
`example/`의 스크립트는 공통 예제 대본 「점심 메뉴 정하는 법」(15초)을 실제로 만든 것이다. 같은 묶음의 다른 팩도 모두 이 대본을 쓰고, 팩마다 화풍과 연출만 다르다. 새 대본에는 `script.json`(대본)과 `plan.py`(풀이)를 고쳐 쓴다.

실사 사물극 팩(`llmvid-blender-object-drama`)과 같은 장면을 쓴다. 다른 점은 두 가지다.
- 조립한 `scene.blend`를 `make_toon.py`로 카툰 질감으로 바꾼다.
- Cycles 대신 EEVEE로 360장을 전부 렌더한다(약 5분 반). 실사판은 180장에 약 23분이다.

이 팩만으로 끝까지 된다. 실사 팩은 없어도 된다.

## 1. 이 스킬이 만드는 것

- 나무 책상 위에 휴대폰이 놓여 있고, 휴대폰 화면에서 메신저 대화가 진행된다. 알림이 오면 휴대폰이 떨리고, 며칠이 지나면 시계 바늘이 돌고, 마지막에 서류 위로 도장이 찍힌다.
- 물건마다 굵은 남색 잉크선이 둘리고, 명암은 3단계로 끊긴다. 책상·벽의 무늬(텍스처)는 남는다. 휴대폰 화면·서류·도장 자국은 그림 그대로 보인다.
- 사람은 나오지 않는다. 이야기는 화면 글자, 물건의 움직임, 빛의 변화, 컷 전환, 내레이션과 자막으로 전한다.
- 결과: 1080×1920, 24fps MP4. 예제는 15초(360프레임).

잘 맞는 대본
- 메신저·문자·알림이 이야기의 중심인 썰(직장 단톡, 가족 톡, 중고 거래 대화 등).
- 가볍고 웃긴 톤. 실사판보다 만화 느낌이 난다.
- 빨리 만들어 보고 고치기를 여러 번 해야 할 때.

안 맞는 대본
- **사람 얼굴·표정·몸짓 연기가 필요한 이야기. 이 방식으로는 안 된다.**
- 장소가 여러 번 바뀌는 이야기. 예제는 책상 한 곳이다.
- 긴 대화. 말풍선은 줄바꿈과 스크롤이 없다. 예제에서 확인한 범위는 한 줄 한글 12자 안팎, 한 화면에 말풍선 3~4개다.
- 손그림 같은 선의 떨림이나 캐릭터 애니메이션을 기대하는 경우. 3D 물건에 선을 두른 그림이다.

## 2. 입력

| 입력 | 필수 | 설명 |
|---|---|---|
| 대본 | 필수 | 내레이션 문장과 화면에 보일 대화 |
| 음성 파일 | 선택 | wav/mp3. 없으면 소리 없는 영상이 된다 |
| 자막 타이밍 | 선택 | (시작 초, 끝 초, 문구). 없으면 음성에서 구간을 잡는다(5절) |
| 전송 효과음 | 선택 | 없으면 코드로 합성한 짧은 소리를 쓴다 |
| 저장 폴더 | 필수 | 작업 폴더. 중간 파일이 0.7GB쯤 생긴다(예제 프레임 PNG 360장 669MB) |

## 3. 먼저 확인할 환경

```
blender --version      # 5.x 에서 만들고 확인했다(5.2.3). PATH 에 없으면 blender 실행 파일 위치를 사용자에게 묻는다
ffmpeg -version        # libx264, libass(subtitles 필터)가 든 빌드
python --version       # 3.10 이상
python -c "import PIL; print(PIL.__version__)"   # Pillow
```

- 없는 것이 있으면 사용자에게 알리고 묻는다. 설치와 내려받기는 허가를 받은 뒤에만 한다.
- 한글 글꼴: `python example/fontfind.py`가 찾은 글꼴을 찍는다. 못 찾으면 사용자에게 글꼴 파일을 받아 `--font`로 넘긴다.
- EEVEE는 그래픽 카드를 쓴다. 시험은 Windows 10 + RTX 3070 Ti에서 `blender -b`(백그라운드)로 했다. 그래픽 카드가 없는 PC나 화면 없는 서버에서는 시험하지 못했다.
- Poly Haven 소재(4절 1단계)가 PC에 있는지 사용자에게 묻는다.

## 4. 절차

작업 폴더를 만들고 그 안에서 모든 명령을 돌린다. 스크립트는 **현재 폴더**에 결과를 쓴다.
팩의 `example/`은 그대로 두고, 작업 폴더의 `scripts/`로 복사해 그 사본을 고친다.

```
작업 폴더/
  scripts/            example 사본(여기서 고친다)
  screens/ tex/       2단계 결과(휴대폰 화면 360장, 서류·도장 그림)
  scene.blend         3단계 결과
  scene_toon.blend    4단계 결과
  tests/              5단계 검수 스틸
  frames_toon/        6단계 최종 프레임
  seq_frames_toon/ fonts/ subs.ass   7단계가 만드는 중간 파일
  out.mp4             결과
```

**0단계. 대본을 `script.json`으로 쓴다.** 문장마다 "화면에 무엇이 보이나(대화 입력, 알림, 시계, 서류)"와 시작·끝 초를 정해 구간(`beats`)으로 적는다. 형식은 `example/script.json`을 본뜬다. 그다음 5절대로 `plan.py`를 맞춘다.

**1단계. 소재를 준비한다.** 책상·벽·소품은 Poly Haven(CC0) 소재다. 팩에는 들어 있지 않다(약 31MB).

| 종류 | 이름 | 해상도 |
|---|---|---|
| 모델(gltf) | `desk_lamp_arm_01`, `classic_laptop`, `office_notepads`, `alarm_clock_01` | 1k |
| 텍스처(jpg: diff, rough, nor_gl) | `wood_table_worn`, `painted_plaster_wall` | 2k |
| HDRI | `studio_small_09` | 2k |

이미 받아 둔 폴더가 있으면 그 폴더를 `--assets`로 넘긴다. 없으면 **사용자 허가를 받은 뒤** 받는다.

```
python scripts/dl_assets.py assets        # api.polyhaven.com 에서 내려받는다. 허가 뒤에만
```

폴더 모양: `assets/models/<이름>/<이름>_1k.gltf`, `assets/tex/<이름>/<이름>_diff_2k.jpg`, `assets/hdri/studio_small_09_2k.hdr`.

**2단계. 휴대폰 화면과 서류 그림을 만든다.**

```
python scripts/screens.py                 # [--font 굵은글꼴] [--font-regular 본문글꼴]
```

`screens/s0001.png`~`s0360.png`(540×1170), `tex/paper.png`, `tex/stamp_mark.png`가 생긴다. 장면마다 한 장씩 열어 글자가 깨지거나 말풍선이 화면 밖으로 나가지 않았는지 본다.

**3단계. 장면을 조립한다.**

```
blender -b --python-exit-code 1 -P scripts/build_ssul.py -- --assets <소재 폴더>
```

`scene.blend`가 생긴다. 소재가 빠져 있으면 없는 파일 이름을 알리고 멈춘다.

**4단계. 카툰 질감으로 바꾼다.**

```
blender -b scene.blend --python-exit-code 1 -P scripts/make_toon.py
```

`scene_toon.blend`가 생긴다. 출력의 `TOON 숫자`는 바꾼 재질 수다(예제 11).

**5단계. 스틸로 검수한다(6절).** 컷마다 한 장씩 낮은 해상도로 뽑는다. 맨 끝 `BLENDER_EEVEE`를 빠뜨리면 Cycles로 렌더된다.

```
blender -b scene_toon.blend --python-exit-code 1 -P scripts/rnd_ssul.py -- 12,60,110,150,214,230,270,316,324,350 540 960 16 tests/t BLENDER_EEVEE
python scripts/sheet.py tests/sheet.png tests/t0012.png tests/t0060.png tests/t0110.png tests/t0150.png tests/t0214.png tests/t0230.png tests/t0270.png tests/t0316.png tests/t0324.png tests/t0350.png --cols 5
```

인자: `프레임목록 폭 높이 샘플 접두사 [engine]`. 프레임목록은 `1,5,9` 또는 `a-b:step`.

**6단계. 최종 렌더.** 360장을 전부 뽑는다. 2분을 넘으므로 백그라운드로 돌린다.

```
blender -b scene_toon.blend --python-exit-code 1 -P scripts/rnd_ssul.py -- 1-360 1080 1920 16 frames_toon/f BLENDER_EEVEE
```

이미 있는 프레임은 건너뛴다. 끊기면 같은 명령을 다시 돌린다. 진행은 출력의 `FRAME 번호 컷 초` 줄로 본다.

**7단계. 음성·자막·효과음을 붙인다.**

```
python scripts/finish.py frames_toon 1 out.mp4 --audio <음성 파일>
```

- 둘째 인자 `1`은 6단계의 step이다(전부 렌더했으므로 1). step이 1이면 필름 그레인·비네트를 넣지 않는다.
- `--audio`를 빼면 소리 없는 영상(조용한 오디오 트랙)이 된다.
- 효과음(전송음·진동·도장)은 `--audio`가 있을 때만 들어간다. `--sfx on`/`off`로 바꿀 수 있다. 전송음 파일이 있으면 `--sfx-send <파일>`.
- 프레임 폴더는 절대 경로로 줘도 된다. `--font`, `--crf`(기본 22), `--grain on|off`도 있다.

**8단계. 확인한다(9절).**

## 5. 대본에 맞춰 고칠 곳

대본과 풀이를 나눠 두었다. 스크립트 안에는 대사도 프레임 번호도 없다.

| 파일 | 담긴 것 | 새 대본에서 |
|---|---|---|
| `script.json` | 대본. 길이(`seconds`, `frames`), 등장인물(`cast`), 단톡방 이름, 구간(`beats`)마다 내레이션·대화(`chat`: 초, 누구, 문구), 자막(`subs`), 효과음 시각(`sfx`), 도장(`stamp`), 결과(`result`) | 새로 쓴다 |
| `plan.py`의 `# [풀이]` 블록 | 이 팩이 대본을 그리는 방식. 컷 표(`SHOTS`), 서류 제목과 표(`DOC_TITLE`, `DOC_ROWS`), 시계 컷(`CLOCK`, `CLOCK_TURNS`, `CLOCK_START`), 빛 표(`LIGHT`), 입력·알림 길이(`TYPE_LEAD`, `BANNER_SEC`) | 구간 구성이 달라지면 고친다 |
| `build_ssul.py` | 장면의 생김새. 소품 자리, 카메라 구도(`CAMS`) | 구도·소품을 바꿀 때만 |
| `make_toon.py` | 카툰 질감. 명암 단계와 그늘 색(`ramp.color_ramp`), 색의 진하기(`Saturation` 1.35, `Value` 1.25), 잉크선 굵기와 색(`line_thickness` 2.4). `SKIP`과 `("screen", …), ("paper", …), ("mark", …)` 표는 `build_ssul.py`의 재질 이름과 맞아야 한다 | 화풍을 바꿀 때만 |

`script.json`에서 이 팩이 읽는 것

- `chat` → 휴대폰 단톡 화면. 첫 등장인물(`cast[0]`)이 휴대폰 주인이다. 그 사람 메시지는 보내기 1.4초 전부터 입력창에 한 글자씩 쳐진다. 마지막 등장인물만 프로필 색이 주황이다.
- `sfx.buzz` → 그 초에 온 메시지가 화면 위 알림 배너로도 뜨고 휴대폰이 1.5초 떤다.
- `stamp` → 그 초에 도장이 찍힌다. 서류 컷은 그 10프레임 전에 시작한다. `stamp`가 없으면 서류와 도장은 나오지 않는다.
- 구간 id `wait` → 시계 컷. 구간 이름을 바꾸면 `plan.py`의 `CLOCK = BEAT.get("wait")`와 `SHOTS`를 고친다.
- `subs`, `sfx.send`, `sfx.hit` → `finish.py`가 붙이는 자막과 효과음.

고치는 순서

1. 음성 길이를 잰다: `ffprobe -v error -show_entries format=duration -of csv=p=0 <음성>`. `seconds` = 올림(초), `frames` = 초 × 24.
2. 구간(`beats`)을 나누고 구간마다 `start`·`end`(초), 내레이션, 화면에 보일 대화(`chat`)를 쓴다.
3. 자막 타이밍이 없으면 음성의 쉬는 곳을 찾는다: `ffmpeg -hide_banner -i <음성> -af silencedetect=noise=-35dB:d=0.25 -f null -`. `silence_end`에서 다음 `silence_start`까지가 말하는 구간이다. 문장을 그 구간에 배정해 `subs`를 쓴다. 한 줄은 12자 안팎, 줄바꿈은 `\\N`.
4. `sfx`(전송·알림·도장 초)와 `stamp`를 대화 시각에 맞춘다.
5. `python scripts/plan.py`를 돌려 읽힌 값(대화 프레임, 진동 구간, 도장 프레임, 컷 표)을 찍어 본다.
6. `plan.py`의 `SHOTS`를 구간에 맞게 고친다. 한 컷은 1초(24프레임) 이상으로 둔다. 서류 문구(`DOC_TITLE`, `DOC_ROWS`)도 대본에 맞게 고친다.

프레임 세는 법: `plan.py`는 0부터 센다(`f=0`이 `s0001.png`). 블렌더는 1부터라서 스크립트가 알아서 1을 더한다.

소재 시계는 4:50을 가리키고 있다. `CLOCK_START`가 바늘을 미리 돌려 시작 시각(예제 11:50)을 맞추고, `CLOCK_TURNS`가 시계 컷 동안 도는 양(예제 30분)이다.

소품을 바꾸려면 `build_ssul.py`의 `imported(...)` 줄과 `NEED`, `dl_assets.py`의 `MODELS`를 같이 고친다. 소품 크기와 오브젝트 이름은 `probe.py`, 조립한 장면 속 자리는 `blender -b scene.blend -P scripts/listobj.py`로 본다.

## 6. 중간 검수

1. 2단계 뒤: 장면마다 `screens/sNNNN.png`를 한 장씩 직접 열어 본다(`sheet.py`로 한 장에 붙여도 된다).
2. 5단계 시트를 직접 열어 본다. 볼 것:
   - 분홍색 면이 있나(텍스처 누락).
   - 잉크선이 물건 윤곽에 둘렸나, 선이 너무 굵거나 지저분하지 않나.
   - 휴대폰 화면·서류 글자가 읽히나.
   - 컷마다 카메라가 의도한 물건을 보나.
   - 서류·도장 컷에서 휴대폰이 사라졌나.
3. 고칠 것이 있으면 스크립트를 고치고 다시 한다. `build_ssul.py`를 고쳤으면 3단계부터, `make_toon.py`만 고쳤으면 4단계부터 한다. `tests/`의 옛 스틸은 지우고 다시 뽑는다(있는 파일은 건너뛰기 때문이다).
4. 7단계 뒤: `ffmpeg -ss <초> -i out.mp4 -frames:v 1 check.png`로 자막이 있는 장면을 두세 장 뽑아 자막 글자와 위치를 본다.

## 7. 함정

실제로 겪은 것만 적는다.

- **사람 연기는 안 된다.** 대본을 물건으로 푸는 설계부터 한다.
- **`BLENDER_EEVEE` 인자.** `rnd_ssul.py`의 여섯째 인자를 빠뜨리면 Cycles로 렌더된다. 카툰 재질은 EEVEE용이다.
- **렌더 로그의 `strokes set empty`.** 720장 렌더 로그에 찍혔지만 결과 그림에는 문제가 없었다. 무해하다.
- **Cycles로 돌릴 때의 장치.** 이 팩의 최종 렌더는 EEVEE라 해당이 없지만, `rnd_ssul.py`를 Cycles로 돌리면 `DEVICE = "CUDA"` 고정이다(시험 PC에서 OptiX가 실패했다). 다른 장치에서는 그 값을 고친다.
- **블렌더는 스크립트가 예외로 멈춰도 종료 코드 0으로 끝난다.** 명령에 `--python-exit-code 1`을 붙여야 실패가 종료 코드 1로 나온다.
- **loudnorm 뒤 샘플레이트.** `loudnorm`만 걸면 소리가 96kHz로 나온다. `finish.py`는 뒤에 `aresample=48000`을 둔다.
- **이어 렌더.** 있는 프레임은 건너뛴다. 장면을 고친 뒤에는 `frames_toon/`과 `tests/`의 옛 파일을 지워야 새로 렌더된다.
- **작업 폴더에서 돌린다.** 스크립트는 현재 폴더의 `screens/`, `tex/`, `scene.blend`, `scene_toon.blend`, `subs.ass`, `fonts/`를 읽고 쓴다.

## 8. 실측 시간

시험 환경: RTX 3070 Ti 8GB, 드라이버 560, Windows 10, 블렌더 5.2.3, 공통 예제 대본(15초, 360프레임).

| 단계 | 시간 |
|---|---|
| `screens.py` 360장 | 약 3초 |
| `build_ssul.py` | 1~5초 |
| `make_toon.py` | 약 1초 |
| 검수 스틸 540×960, EEVEE 16샘플 | 장당 1초 안팎(첫 장은 2초쯤) |
| 최종 렌더 1080×1920, EEVEE + Freestyle, 360장 | 328초(장당 약 0.9초) |
| `finish.py`(360장 → 15초 MP4) | 약 4초 |

## 9. 완료 기준

```
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,duration,sample_rate -of compact out.mp4
```

- 영상 1080×1920, 24fps, 길이 = `TOTAL` ÷ 24초.
- 오디오 트랙이 있고(`--audio`를 줬으면 소리가 난다), 길이가 영상과 같다.
- 자막 스틸을 눈으로 확인했다.
- 사용자에게 알린다: 결과 파일 경로, 걸린 시간, 남은 문제(시험하지 못한 것, 어색한 컷).

## 10. 라이선스

자세한 것은 `LICENSES.md`.
- 블렌더로 만든 영상은 만든 사람 것이다. 상업 이용에 제한이 없다.
- Poly Haven 소재는 CC0다. 팩에는 들어 있지 않다.
- 글꼴은 팩에 없고 PC의 글꼴을 쓴다. 게시용이면 Noto Sans KR(OFL)을 권한다.
- 음성·효과음은 팩에 없다. 넣는 파일의 권리는 사용자가 확인한다.
- `bpy`를 쓰는 스크립트를 밖으로 배포하려면 GPL 호환 조건이어야 한다는 것이 블렌더 재단의 안내다.

## 11. 쓰지 않는 것

영상 생성 AI, 이미지 생성 AI, 유료 API를 쓰지 않는다. 휴대폰 화면·서류·도장 그림은 Pillow 코드로 그리고, 진동·도장 소리는 ffmpeg `aevalsrc`로 합성한다.
