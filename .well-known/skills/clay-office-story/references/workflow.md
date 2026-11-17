# 로컬 제작 방법

Blender 경로는 `BLENDER_BIN` 또는 로컬 설치에서 확인한다. 2026-11-11 제작 PC는 Blender 5.2.3 LTS를 사용했다. FFmpeg/ffprobe, Python/Pillow, Node, Remotion 4.0.540이 이미 설치된 환경에서 실행했다.

작업 폴더에 scripts/, characters.json, episodes.json, remotion/을 준비한다. scripts/는 스킬에 들어 있는 사본, JSON은 assets/에서 복사한다. Remotion 소스와 글꼴은 assets/remotion을 작업 폴더의 remotion으로 복사한다. EP3 재현은 납품 패키지에 포함한 음성·효과음·클립도 함께 복사한다. 패키지는 실행에 필요한 npm 의존성을 package.json에 고정하며 node_modules는 별도 설치한다.

```powershell
& $env:BLENDER_BIN -b --python-exit-code 1 -P scripts/build_clay.py -- --mode catalog --output characters
& $env:BLENDER_BIN -b --python-exit-code 1 -P scripts/build_clay.py -- --mode expressions --character F01 --output expressions
python scripts/prepare_timeline.py
& $env:BLENDER_BIN -b --python-exit-code 1 -P scripts/build_episode.py -- --ep 6 --proofs
& $env:BLENDER_BIN -b episodes/ep6/scene.blend --python-exit-code 1 -P scripts/render_frames.py -- --output episodes/ep6/render --width 1080 --height 1920 --samples 24
python scripts/compose_episode.py --ep 6
```

prepare_timeline.py 입력: episodes/epN/narration.wav, alignment-original.json. EP5의 예제는 원음에 atempo=1.18을 적용했으므로 같은 비율로 정렬 시간을 보정한다. 새 회차에서는 이 수치를 그대로 복사하지 말고 실제 처리값으로 바꾼다.

소품/장소를 추가하면 scripts/build_episode.py의 해당 beat가 실제로 바뀌었는지 확인한다. proof PNG와 영상 파일의 이름만 바꿔서 다른 회차 결과라고 간주하지 않는다.

확정된 음성·타임라인이 있는 회차는 `./scripts/run_episode.ps1 -Episode 6 -BlenderBin "설치경로/blender.exe"`로 프레임 렌더부터 검증된 MP4까지 실행한다. 장면 코드/캐스팅을 바꾸었으면 `-RebuildScene`을 지정하고 새 proof를 확인한다. 이미 저장한 .blend를 직접 편집했을 때는 이 옵션 없이 실행한다. 이 명령은 유료 API를 호출하지 않는다.

원본 참고: 사용자가 제공한 llmvid-blender-clay-office.zip. 외부 모델·텍스처·HDRI 없이 코드 기반 모델링이라는 제작 방향과 프레임 캐시 검수 방식을 참고했다. 참고 팩의 스크립트·라이선스 안내는 제작 패키지 reference/에 보존한다.

