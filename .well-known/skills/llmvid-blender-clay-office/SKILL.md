---
name: llmvid-blender-clay-office
description: 대본과 음성으로, 점토풍 3D 캐릭터가 등장하는 미니어처 사무실 썰 세로 영상(1080×1920)을 만든다. 영상·이미지 생성 AI 없이 블렌더 기본 도형을 코드로 조립해 EEVEE로 렌더하고 ffmpeg로 자막과 음성을 붙인다. 직장인 썰을 아기자기한 점토 인형극 느낌으로 만들 때 쓴다.
---

# 블렌더 점토풍 사무실극 (llmvid-blender-clay-office)

검증된 예제와 절차를 묶은 팩이다. 버튼 하나로 끝나는 자동 도구가 아니다.
`example/`의 스크립트는 공통 예제 대본 「점심 메뉴 정하는 법」(15초, 360프레임)을 실제로 만든 것이다. 같은 묶음의 다른 팩도 모두 이 대본을 쓰고, 팩마다 화풍과 연출만 다르다.
새 대본에는 `script.json`(대본)을 새로 쓰고 `refinements.py`의 풀이(카메라 표와 동작)를 맞춘다.

세트·인물·소품은 전부 블렌더 기본 도형을 코드로 만든 것이다. 외부 3D 모델이나 텍스처, HDRI, 이미지가 전혀 필요 없으며, 영상 생성 AI나 이미지 생성 AI 없이 블렌더 스크립트와 ffmpeg만으로 끝난다.

```
llmvid-blender-clay-office/
  SKILL.md
  LICENSES.md
  example/
    script.json             대본(모든 팩이 같은 형식). 길이, 구간, 대화 시각, 자막
    SCRIPT.md               예제 대본 설명
    create_office.py        세트·인물·조명을 만들고 .blend 로 저장한다(시작점). 대본을 읽어 장면 구간을 정한다
    refinements.py          create_office.py 가 불러 쓴다. 얼굴·옷·가구 마감, [풀이] 카메라 표(CAMERA_SETUPS)와 동작(bake_story)
    preview_checks.py       저장한 .blend 에서 구간마다 두 장(가운데·끝)을 절반 크기로 뽑는다
    render_final.py         전체 프레임을 PNG 로 뽑는다(끊겨도 이어서 렌더)
    finish.py               프레임 + 음성 + 자막(대본의 subs)을 MP4 로 합친다
    fontfind.py             자막용 한글 글꼴을 찾는다
    sheet.py                그림 여러 장을 한 장 시트로 붙인다(검수용)
```

## 1. 이 스킬이 만드는 것

- 점토 인형 같은 3D 캐릭터(머리가 큰 2~3등신) 3명이 미니어처 사무실 세트(책상, 의자, 프린터, 창, 화분, 책장, 벽시계)에서 움직인다. 구간마다 카메라가 바뀐다.
- 연기는 입을 다문 채 고개 돌리기·끄덕이기·숙이기, 눈썹, 손 들기, 으쓱하기, 일어서기로 전한다. 입 모양 맞춤(립싱크)이나 손가락 관절 연기는 없다.
- 대사는 화면에 글자로 나오지 않는다. 내레이션과 자막, 몸짓으로 전한다.
- 결과: 1080×1920 세로형, 24fps MP4 영상. 예제는 15초(360프레임)다.

예제의 풀이(구간 id 기준)

| 구간 | 인물 | 카메라 |
|---|---|---|
| `hook` | 주인공이 고개를 돌리고 한 손을 들어 묻는다(대본의 내 대화 시각) | 주인공 책상 |
| `ask` | 동료가 돌아보며 으쓱하고, 이어서 팀장이 으쓱한다(각자의 대화 시각) | 내려다본 전경 |
| `wait` | 주인공이 점점 책상에 처진다. 뒤 벽시계가 대본의 `clock.from` → `clock.to` 로 돈다 | 주인공 정면 + 벽시계 |
| `decide` | 팀장이 일어나 한 손을 든다(대화 시각) | 팀장 자리 |
| `punch` | 두 사람이 차례로 끄덕이고, 주인공 책상에 김 나는 냄비가 튀어나온다(도장 시각) | 세 사람 + 냄비 |

가장 중요한 한계
- **구간 구성이 다른 대본은 동작을 새로 짜야 한다.** 대화 시각·시계·길이는 `script.json`만 바꾸면 따라오지만, 구간마다 누가 무엇을 하는지는 `refinements.py`의 `bake_story` 안 `if sid == "…"` 블록에 있다.
- **대사가 화면에 보이지 않는다.** 말풍선이나 화면 글자가 없다. 대화 내용은 자막에 담아야 한다.
- 세트는 사무실 한 곳, 인물은 3명이다.

잘 맞는 대본
- 사무실 안에서 벌어지는 직장인 일상 이야기.
- 등장인물 3명(주인공, 동료, 팀장) 구도의 콩트.
- 내레이션과 자막이 끌고 가고, 큼직한 몸짓으로 상황을 보여 주면 되는 이야기.

안 맞는 대본
- **섬세한 표정 변화, 립싱크, 손가락 연기가 필요한 이야기.**
- **장소가 여러 번 바뀌거나 야외·식당 등이 필요한 이야기.**
- 등장인물이 4명 이상인 대본.
- 메신저 화면이나 글자가 중심인 이야기(같은 묶음의 사물극·마스코트 팩이 맞다).

## 2. 입력

| 입력 | 필수 | 설명 |
|---|---|---|
| 대본 | 필수 | 내레이션 문장과 구간별 인물 행동. `script.json` 형식으로 옮긴다 |
| 음성 파일 | 선택 | wav/mp3. 없으면 소리 없는 영상(조용한 오디오 트랙)이 된다 |
| 배경음 파일 | 선택 | wav/mp3. finish.py에 넘기면 음량 0.3으로 섞인다 |
| 자막 타이밍 | 선택 | `script.json`의 `subs` (시작 초, 끝 초, 문구). 없으면 음성의 무음 구간에서 잡는다(5절) |
| 저장 폴더 | 필수 | 작업 폴더. 예제 기준 프레임 PNG 360장이 약 785MB다 |

## 3. 먼저 확인할 환경

작업을 시작하기 전 다음 명령으로 실행 환경을 점검한다.

```bash
blender --version      # 공통 대본 예제는 Blender 5.2.3 에서 전 과정을 확인했다. 이전 예제는 4.5.15 LTS 에서 확인했다(4.5 로는 이번에 다시 돌리지 않았다). PATH 에 없으면 실행 파일 위치를 사용자에게 묻는다
ffmpeg -version        # libx264, libass(자막 필터)가 든 빌드
python --version       # 3.10 이상
python -c "import PIL; print(PIL.__version__)"   # Pillow (sheet.py 검수 시트 제작에 필요)
```

- 없는 도구가 있으면 사용자에게 알리고 설치 여부를 묻는다. 프로그램 설치나 패키지 내려받기는 반드시 사용자의 허가를 받은 뒤에만 진행한다.
- 한글 글꼴: `python scripts/fontfind.py`를 실행해 시스템 글꼴을 확인한다. 스크립트는 Noto Sans KR → 맑은 고딕 순으로 찾는다. 적절한 글꼴을 찾지 못하면 사용자에게 글꼴 파일(.ttf/.otf)을 받아 `--font` 옵션으로 넘긴다.
- 블렌더 EEVEE 엔진은 그래픽 카드를 사용한다. 실측 시험은 Windows 10 + RTX 3070 Ti 8GB 환경에서 수행했다. 그래픽 카드가 없는 PC나 디스플레이가 없는 환경에서는 확인하지 못했다.
- 이 팩은 외부 3D 모델, 외부 텍스처, HDRI 파일을 일체 쓰지 않는다. 외부 에셋 다운로드는 필요하지 않다.

## 4. 절차

작업 폴더를 따로 만들고 그 안에서 모든 명령을 돌린다. 팩 안의 `example/` 폴더는 원본으로 보존하고, 작업 폴더 아래 `scripts/`로 복사해 그 사본을 고쳐서 사용한다.

`preview_checks.py`와 `render_final.py`는 결과물을 작업 폴더 루트가 아니라 **스크립트가 있는 폴더(`scripts/`) 아래**에 만든다.

```
작업 폴더/
  scripts/                    example 사본(script.json, refinements.py 를 여기서 고친다)
    previews/                 2단계 결과(proof_NNNN.png)
    preview-checks.json       2단계 결과
    frames/<서명 16자>/       4단계 결과(frame_0001.png ~)
    render-progress.json      4단계 결과
    render-manifest.json      4단계 결과
  office.blend                1단계 결과
  proofs.png                  3단계 검수 시트
  subs.ass, fonts/            5단계 finish.py 가 만든다
  out.mp4                     최종 결과 영상
```

### 0단계. 대본을 `script.json`으로 쓴다

`example/script.json`을 본뜬다. 구간(`beats`)마다 시작·끝 초와 대화(`chat`)를 적고, 자막(`subs`)을 쓴다. 그다음 5절대로 `refinements.py`를 맞춘다.

### 1단계. 장면 만들기

```bash
blender -b --python-exit-code 1 -P scripts/create_office.py -- --output-blend office.blend --frames-dir previews
```

- `--output-blend`와 `--frames-dir`는 필수 인자다. 대본은 스크립트 옆의 `script.json`을 읽는다. 다른 파일은 `--script <경로>`로 준다.
- `--preview-frame N`을 넘기면 `<frames-dir>/preview_NNNN.png` 스틸 한 장을 같이 렌더한다(`--resolution-percentage 50 --samples 16`과 함께 쓰면 빠르다).
- 정상 완료되면 마지막 줄에 `"status": "completed"`가 든 JSON 한 줄이 찍힌다. 예제는 frame_count 360, cameras_count 5, shots 5개다.

### 2단계. 구간마다 스틸 뽑기

```bash
blender -b --python-exit-code 1 office.blend -P scripts/preview_checks.py
```

- 구간마다 가운데와 끝 프레임 두 장을 절반 크기(50%), 16샘플로 뽑는다. 결과는 **`scripts/previews/`** 아래 `proof_NNNN.png`이고 `scripts/preview-checks.json`도 생긴다. 예제는 10장이다.

### 3단계. 검수 시트 만들기

```bash
python scripts/sheet.py proofs.png scripts/previews/proof_*.png --cols 5 --width 300
```

- 셸에서 `*`가 풀리지 않으면(일부 파워셸) 파일 이름을 나열한다.
- `proofs.png`를 직접 열어 6절 기준으로 본다.

### 4단계. 전체 프레임 최종 렌더

검수가 끝나면 원본 크기(1080×1920), 32샘플로 전체를 뽑는다. 2분을 넘으므로 백그라운드로 돌린다.

```bash
blender -b --python-exit-code 1 office.blend -P scripts/render_final.py
```

- 결과는 **`scripts/frames/<서명 16자>/`** 에 `frame_0001.png`부터 저장된다. `.blend` 내용이 바뀌면 새 서명 폴더가 생기고 이전 렌더는 남는다.
- 같은 `.blend`로 다시 실행하면 이미 렌더된 프레임은 건너뛴다.
- 진행은 24프레임마다 찍히는 `FRAME_PROGRESS` 줄로 보고, 끝나면 `RENDER_COMPLETE` 줄이 찍힌다. 프레임 폴더 경로는 그 줄이나 `scripts/render-manifest.json`의 `frame_directory`에 있다.

### 5단계. 합성 (영상 + 음성 + 자막)

```bash
python scripts/finish.py scripts/frames/<서명 16자> out.mp4 --audio narration.wav
```

- 길이와 자막은 스크립트 옆 `script.json`에서 읽는다(다른 파일은 `--script`).
- 음성이 없으면 `--audio`를 뺀다(조용한 트랙이 들어간다). 선택: `--music <배경음>`(음량 0.3), `--font <글꼴>`, `--crf 20`.
- 작업 폴더에 `subs.ass`와 `fonts/`가 생긴다.

### 6단계. 최종 확인

9절 기준으로 `ffprobe`와 자막 스틸을 확인한다.

## 5. 대본에 맞춰 고칠 곳

대본과 풀이를 나눠 두었다.

| 파일 | 담긴 것 | 새 대본에서 |
|---|---|---|
| `script.json` | 대본. 길이(`seconds`, `frames`), 등장인물(`cast`), 구간(`beats`)마다 시작·끝 초와 대화(`chat`: 초, 누구), 시계(`clock`), 도장(`stamp`), 자막(`subs`) | 새로 쓴다 |
| `refinements.py`의 `CAMERA_SETUPS` | [풀이] 구간 id → 카메라 (위치, 바라볼 점, 렌즈 mm). 표에 없는 id 는 `wide` | 구간 id·구도가 달라지면 고친다 |
| `refinements.py`의 `bake_story` | [풀이] 구간마다 인물의 자세. `if sid == "hook":` 같은 블록 | 구간 구성·동작이 달라지면 고친다 |
| `refinements.py`의 `build_story_props` | 벽시계와 냄비 소품 | 소품을 바꿀 때 |
| `create_office.py` | 세트·인물의 생김새 | 세트를 바꿀 때만 |

`script.json`에서 이 팩이 읽는 것

- `beats` → 장면(카메라) 구간. 구간 수는 자유다.
- `cast` → 첫째가 주인공, 마지막이 팀장. 그 사이가 동료다(인물은 3명 고정).
- `chat`의 시각 → 그 인물이 몸짓하는 때. 문구는 화면에 나오지 않는다.
- 구간 id `wait`의 `clock` → 벽시계 바늘.
- `stamp.t` → 냄비가 튀어나오는 때(없으면 마지막 구간 시작).
- `subs` → `finish.py`가 얹는 자막.

동작을 짤 때 쓰는 것(`bake_story` 안)

| 이름 | 뜻 |
|---|---|
| `local_hands(자리, 방향, 높이, 앞)` | 두 손의 기본 자리(타자 치는 자세는 높이 .80) |
| `raised(자리, 방향, 벌림, 앞, 높이)` | 두 손을 든 자리. 으쓱(벌림 .40, 높이 1.0), 한 손 들기(높이 1.2~1.6) |
| `pulse(시각, 시작, 길이)` | 그 시각부터 0 → 1 → 0 으로 한 번 움직이는 값 |
| `smooth(값)` | 0~1 을 부드럽게 |
| `*_head` | 고개 `[숙이기, 0, 돌리기]`(라디안). 숙이기는 +가 아래 |
| `*_hips` | 골반 높이. 앉으면 .54, 서면 .77 |
| `*_yaw` | 몸 방향. 0 이면 -Y(카메라 쪽), π 면 +Y |

### 고치는 순서

1. 음성 길이를 잰다. `ffprobe -v error -show_entries format=duration -of csv=p=0 narration.wav`. `seconds` = 올림(초), `frames` = 초 × 24.
2. 자막 구간을 잡는다. 시각이 따로 없으면 `ffmpeg -i narration.wav -af silencedetect=noise=-35dB:d=0.25 -f null -`의 `silence_end`~다음 `silence_start`가 말하는 구간이다. 문장을 나눠 `subs`에 넣는다. 줄바꿈은 `\\N`.
3. 구간(`beats`)과 대화 시각(`chat`)을 쓴다.
4. `CAMERA_SETUPS`에 구간 id 마다 카메라를 넣고, `bake_story`에 구간 블록을 쓴다.
5. 1~3단계를 돌려 시트를 보고 좌표·렌즈를 고친다. 세트에는 오른쪽 벽과 천장이 없으니 카메라가 그쪽을 비추지 않게 한다.

## 6. 중간 검수

1. **3단계 직후 (`proofs.png`를 직접 연다).** 볼 것:
   - 인물의 머리나 든 손이 화면 밖으로 잘리지 않았는가.
   - 손이 몸이나 책상을 파고들지 않았는가, 발이 바닥에 붙어 있는가.
   - 벽 위쪽의 빈 배경(회색)이 크게 보이지 않는가.
   - 화면 아래 자막 자리에 중요한 동작이 가려지지 않는가.
   - 벽시계 바늘과 냄비가 의도한 때에 보이는가.
2. **고친 뒤.** `create_office.py`, `refinements.py`, `script.json`을 고쳤으면 1단계부터 다시 한다.
3. **5단계 직후.** `ffmpeg -ss <초> -i out.mp4 -frames:v 1 check.png`로 자막이 있는 장면을 두세 장 뽑아 글자와 위치를 본다.

## 7. 함정

실제로 겪은 것만 적는다.

- **블렌더는 `-P` 스크립트가 예외로 멈춰도 종료 코드 0으로 끝난다.** `--python-exit-code 1`을 붙인다. 로그 끝에 `Traceback`이 없는지, 완료 JSON이 찍혔는지도 본다.
- **세로 화면의 위아래 화각.** 세트에는 천장과 오른쪽 벽이 없다. 낮은 카메라에서 벽(높이 3.4) 위로 회색 배경이 화면의 3분의 1을 차지했다. 뒤벽과 왼쪽 벽을 위로 이어 붙였고(`WallBackUpper`, `WallLeftUpper`), 넓은 컷은 높은 곳에서 내려다보게 했다. 오른쪽(x > 3)을 비추는 구도는 여전히 빈 배경이 보인다.
- **든 손이 머리에 붙는다.** 팔 길이가 짧아(위팔·아래팔 각 0.23) 손 목표를 머리 옆에 두면 머리를 긁는 것처럼 보였다. 목표를 바깥·앞·위(벌림 .40, 앞 -.26, 높이 1.58)로 두었다.
- **스크립트 폴더 아래에 파일이 생긴다.** `preview_checks.py`와 `render_final.py`의 결과는 `scripts/previews/`, `scripts/frames/<서명 16자>/`에 생긴다.
- **JSON 안의 절대 경로.** `render-manifest.json`, `render-progress.json`, `preview-checks.json`에는 PC의 절대 경로가 적힌다. 남에게 넘길 때는 뺀다.
- **서명 폴더가 쌓인다.** 장면을 고칠 때마다 새 서명 폴더에 전체 프레임이 다시 렌더된다. 공간이 모자라면 옛 폴더를 지운다.
- 로그의 `World.use_nodes` DeprecationWarning은 무해하다.

## 8. 실측 시간

시험 환경: Windows 10, RTX 3070 Ti 8GB, 드라이버 560, Blender 5.2.3, 공통 예제 대본(1080×1920, 24fps, 15초, 360프레임).

| 단계 | 소요 시간 |
|---|---|
| 장면 만들기(`.blend` 저장) | 10초 안팎 |
| 구간 스틸 10장(`preview_checks.py`) | 10초 안팎 |
| 전체 360프레임 렌더(1080×1920, 32샘플) | 182초 (장당 약 0.5초) |
| 합성(`finish.py`, 음성 없음) | 몇 초 |

- 결과: H.264 1080×1920 360프레임 + AAC(무음), 15.000초, 약 3.6MB. 프레임 PNG 360장은 약 785MB.
- 이전 예제(28초, 672프레임)는 Blender 4.5.15 LTS에서 413초였다.

확인하지 못한 것
- Blender 4.5 LTS에서 이번 공통 대본 예제의 실행.
- 음성을 넣은 합성(새 대본의 음성을 만들지 않았다).
- macOS·리눅스, 그래픽 카드 없는 PC.
- 구간 구성이 다른 대본으로 동작을 새로 짠 결과.

## 9. 완료 기준

```bash
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,duration,sample_rate -of compact out.mp4
```

- 영상 1080×1920, 24fps, h264. 길이 = 대본의 `frames` ÷ 24(예제 15.000초).
- 오디오 스트림(aac)이 있고 길이가 영상과 같다.
- 시트(`proofs.png`)와 자막 스틸을 눈으로 확인했다.
- 사용자에게 알린다: 결과 파일 경로, 걸린 시간, 확인하지 못한 것, 어색한 컷.

## 10. 라이선스

자세한 내용은 함께 제공되는 `LICENSES.md`를 참고한다.

- 블렌더로 만든 그림·영상·`.blend` 파일은 만든 사람의 것이다.
- 외부 3D 모델, 텍스처, HDRI 등 외부 에셋은 전혀 사용하지 않았으며, 모든 객체는 블렌더 코드로 생성된 절차적 도형이다.
- 팩 안에는 글꼴 파일이 포함되어 있지 않으며 사용자의 PC 시스템 글꼴을 활용한다. Noto Sans KR은 SIL OFL 1.1, 맑은 고딕은 Windows 글꼴 라이선스를 따른다. 조건이 분명해야 하면 `--font`로 권리가 분명한 글꼴을 넘긴다.
- 내레이션 음성과 배경음 파일은 팩에 동봉되지 않는다. 사용자가 직접 준비하며 해당 음원의 사용 권리와 라이선스를 직접 확인해야 한다.
- 블렌더 파이썬 API(`bpy`)를 사용하는 스크립트를 외부에 공개 배포할 때는 GNU GPL 호환 라이선스를 따라야 한다는 것이 블렌더 재단의 공식 지침이다.

## 11. 쓰지 않는 것

영상 생성 AI, 이미지 생성 AI, 외부 상용 API를 일체 사용하지 않는다. 또한 다운로드해야 하는 외부 3D 에셋이나 상용 텍스처를 일절 쓰지 않으며, 모든 형상과 재질은 블렌더 내장 파이썬 코드로 조합하고 ffmpeg를 통해 완성한다.
