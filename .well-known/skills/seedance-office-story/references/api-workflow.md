# API 이식 · 현재 구현 계약

현재 검증한 후보는 fal의 `bytedance/seedance-2.5/us/reference-to-video`이며, 사용자가 다른 제공자를 정하면 그 제공자를 우선한다. 스키마 확인일은2026-11-04다. 최신 확인을 대신하는 고정 사양표로 쓰지 않는다.

- `task=reference`, `resolution=1080p`, `aspect_ratio=9:16`, `duration`은문자열`"4"`~`"30"`, `generate_audio=false`, `draft=false`, `codec=H264`를 명시한다. Genspark 기록의`audio_enable`은 이 API의 필드가 아니다.
- `image_urls`의0번째가`@Image1`,1번째가`@Image2`다. 정본 경로/해시/역할과 순서를 보관한다. 로컬파일 경로는 서버가 읽을 수 없으므로 실제 이미지 data URI 또는 외부에서 읽을 수 있는 HTTPS 파일 URL을 쓴다. 로컬 data URI는 제출할 때 파일 내용이 제공자로 전송된다.
- 현재 어댑터는 이 엔드포인트의 이미지 참조 제작을 다룬다. 다른 모델·비디오 편집·음성 참조는 어댑터를 추가하고 공식 스키마를 다시 검증한다. 단순 문자열 교체로 모델을 바꾸지 않는다.
- Codex 대화형 실행에는 연결된 fal MCP를 사용할 수 있다. 독립 CLI/웹 서버는 별도`FAL_KEY` 환경변수가 필요하다. 브라우저에 키를 넣지 않는다. Genspark 크레딧과 API 사용료는 별개다.

## 도구

스킬의`scripts/seedance_runner.py` 또는 프로젝트의`workflows/seedance_runner.py`를 쓴다. Python3.11+ 표준 라이브러리만 사용하며 QC에는 FFmpeg/ffprobe가 필요하다. 프로젝트 예제 경로는`C:/Users/<사용자>/Documents/Codex/toegeungak-studio/workflows/examples`다.

1. `validate PLAN`: 유닛 길이·타임라인·참조 키·@Image번호와 실제 파일 여부를 확인한다. 원문 프롬프트의 모순은 검토할 경고로 남긴다.
2. `prepare PLAN --out REQUEST --data-uris` 또는`--bindings URL_JSON`: 프롬프트와 순서별 참조를 요청 JSON으로 만든다. 자료가 빠지면 실행 가능한 요청을 만들지 않는다. `missing:true`는 가져올 때의 상태이며 실제 정본 파일을 채웠다면 다시 확인한다.
3. `submit REQUEST --unit UNIT --job JOB`: 기본 오프라인. 실제 유료 제출에만`--execute`를 사용한다. 기존 작업 기록은 덮어쓰거나 자동 재제출하지 않는다. 이 플래그 자체가 사용자 승인 대신은 아니다.
4. `status JOB`, `result JOB --out RESULT`: 최초 반환된`request_id`, `status_url`, `response_url`로 같은 작업을 조회한다. 전체 모델 ID 뒤에`/requests`를 붙여 URL을 임의 구성하지 않는다. 완료 응답에 오류가 있으면 실패이며, 정상 완료도 영상 품질 승인은 아니다.
5. `qc VIDEO --out DIR`: 해시·규격·오디오 스트림·새 그리드를 보관한다. 자동 측정과 사람이 판단할 얼굴/기하/글자/동작을 분리한다. scene 점수는 경계 후보이며 컷 정확도를 보장하지 않는다.

API 제출 전 입력 해시와 작업 기록을 저장하고 응답 불명확/타임아웃은`submission_unknown`으로 멈춘다. request ID가 있으면 조회하고 없으면 제공자 작업 기록을 확인한다. 새 파일명으로 다시 제출하는 것 역시 새 유료 요청이므로 기존 작업 존재를 확인한 뒤 결정한다.

현재 구현은 준비·요청·조회·QC CLI다. 대시보드의 실행 버튼, 이미지 생성·TTS·자동 다운로드·유닛 합성·Remotion 렌더까지 연결된 상태는 아니다. 실제 생성 비교 없이 API 품질 재현 완료라고 말하지 않는다.

공식 근거: [모델 API](https://fal.ai/models/bytedance/seedance-2.5/us/reference-to-video/api), [Queue](https://fal.ai/docs/documentation/model-apis/inference/queue).
