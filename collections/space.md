# 인테리어·입체 목업

평면 목업을 360 뷰어와 워크스루로 넓히려고 조사해 추린 스킬·MCP·저장소.
출처: 입체 목업 기획 조사(근거 자료 catalog)에서 추린 색인, 모은 날 2026-11-10

설치 스크립트에 이름을 넘긴다. zip 이 있는 것은 안의 스킬(SKILL.md 가 있는 폴더)을 모두 설치하고,
zip 이 없는 것은 원본 주소를 알려 준다. 라이선스는 쓰기 전에 원문을 다시 확인한다.

## 공통 제작도구

- sp-anthropics-skills-webapp-testing — anthropics/skills — webapp-testing: Python Playwright로 우리 서버를 띄우고 360 뷰어 화면을 자동 캡처·확인 | 라이선스: Apache-2.0(스킬 폴더 LICENSE.txt) | 원본: https://github.com/anthropics/skills/tree/main/skills/webapp-testing
- sp-projects-blender-org-lab-blender-mcp — Blender Lab MCP Server (공식, 소스 projects.blender.org/lab/blender_mcp): 서버 PC Blender 5.2.3으로 장면 프리셋 제작·렌더 확인 | 라이선스: GPL-3.0 | 원본: https://projects.blender.org/lab/blender_mcp
- sp-cloudai-x-threejs-skills — CloudAI-X/threejs-skills: 모든 three.js 개발의 기본기 스킬 세트로 상시 장착(셰이더·텍스처·성능·R3F·glTF 파이프라인) | 라이선스: MIT | 원본: https://github.com/CloudAI-X/threejs-skills
- sp-el4cteo-blender-skills — EL4CTEO/blender-skills: Blender 5.2 모델링·UV·PBR·베이킹·내보내기를 Claude Code 스킬로(장면 사전 제작 자동화) | 라이선스: MIT | 원본: https://github.com/EL4CTEO/blender-skills
- sp-holdmybeer-gg-blenderwright — HoldMyBeer-gg/blenderwright: 용도 (b)(c) 자동화: UV 8종, Cycles 베이크(알베도·노멀·AO·lit), 렌더 패스, glTF 내보내기를 도구 호출로 실행 | 라이선스: MIT | 원본: https://github.com/HoldMyBeer-gg/blenderwright
- sp-microsoft-playwright-mcp — microsoft/playwright-mcp: 에이전트가 브라우저를 직접 조작해 시점 이동·캡처로 결과 확인 | 라이선스: Apache-2.0 | 원본: https://github.com/microsoft/playwright-mcp
- sp-arjun988-blender-skills — arjun988/blender-skills: archviz·materials·uv-workflow·lighting·rendering 스킬을 참고해 공간 프리셋 제작 지침을 만든다 | 라이선스: MIT | 원본: https://github.com/arjun988/blender-skills
- sp-chromedevtools-chrome-devtools-mcp — ChromeDevTools/chrome-devtools-mcp: 프레임 시간·GPU 메모리·텍스처 로딩 성능 트레이스로 태블릿 성능 진단 | 라이선스: Apache-2.0 | 원본: https://github.com/ChromeDevTools/chrome-devtools-mcp
- sp-dmitriygolub-threejs-devtools-mcp — DmitriyGolub/threejs-devtools-mcp: 실행 중인 360/워크스루 장면을 에이전트가 검사·스크린샷·머티리얼 실시간 조정(패턴 스케일 맞추기) | 라이선스: MIT | 원본: https://github.com/DmitriyGolub/threejs-devtools-mcp
- sp-grimashevich-sweethome3d-mcp-server — grimashevich/sweethome3d-mcp-server: 무료 Sweet Home 3D를 Claude로 조작하는 MCP. | 라이선스: GPL-2.0 | 원본: https://github.com/grimashevich/sweethome3d-mcp-server
- sp-majidmanzarpour-threejs-game-skills — majidmanzarpour/threejs-game-skills: qa-release 스킬의 Playwright 캡처·빈 캔버스 검사(inspect-threejs-canvas.mjs)·시각 회귀 기준선 차용 | 라이선스: MIT | 원본: https://github.com/majidmanzarpour/threejs-game-skills
- sp-moh4696-open-3d-skills — Moh4696/open-3d-skills: site-check(빈 캔버스·프레임 시간·드로콜 보고)와 frame-capture(60fps 결정적 녹화)로 360/워크스루 검증·시연 영상 제작 | 라이선스: MIT | 원본: https://github.com/Moh4696/open-3d-skills
- sp-nirholas-blender-mcp — nirholas/blender-mcp (headless): GUI 없이 Blender로 GLB·glTF·FBX·USD 변환과 미리보기 렌더(서비스 배치 경로) | 라이선스: Apache-2.0 | 원본: https://github.com/nirholas/blender-mcp
- sp-pjt222-agent-almanac — pjt222/agent-almanac (create-3d-scene·script-blender-automation 스킬): Claude Code용 bpy 장면·렌더 자동화 SKILL.md 예시(우리 스킬 작성 참고) | 라이선스: MIT | 원본: https://github.com/pjt222/agent-almanac
- sp-r3f-docs-pmnd-rs-llms-txt — pmndrs 문서 MCP + R3F llms.txt: R3F·drei로 만들 때 공식 문서를 에이전트가 직접 조회(HTTP MCP https://docs.pmnd.rs/api/mcp) | 라이선스: MIT(react-three-fiber·drei 저장소) | 원본: https://r3f.docs.pmnd.rs/llms.txt
- sp-roble3-cc-blender-skill — RobLe3/cc-blender-skill: text-to-blender 오케스트레이터와 reference-to-3d 구조를 참고하고, 공식 Blender Lab MCP 연동 예시로 쓴다 | 라이선스: MIT | 원본: https://github.com/RobLe3/cc-blender-skill
- sp-scottstts-threejs-awesome-graphics-agent-skills — scottstts/Threejs-Awesome-Graphics-Agent-Skills: 노출·톤매핑·그림자 품질과 threejs-visual-validation(고정 시점 결정적 캡처·대조표) 방식 차용 | 라이선스: MIT | 원본: https://github.com/scottstts/Threejs-Awesome-Graphics-Agent-Skills
- sp-shi3z-sparkjs-skill — shi3z/sparkjs-skill: Spark 스플랫 렌더 코드 작성 시 Claude Code 참고 스킬 | 라이선스: 없음(GitHub 라이선스 미표기) | 원본: https://github.com/shi3z/sparkjs-skill
- sp-impertio-studio-three-js-claude-skill-package — Three.js Claude Skill Package (Impertio-Studio): Claude Code로 three.js·WebGPU·R3F 셰이더 뷰어를 짤 때 참고할 스킬 묶음(24종) | 라이선스: MIT | 원본: https://github.com/Impertio-Studio/Three.js-Claude-Skill-Package
- sp-tmhsdigital-blender-developer-tools — TMHSDigital/Blender-Developer-Tools: Blender 5.2 LTS·4.5 LTS에서 맞는 bpy 규칙·예제로 API 변경에서 오는 오류를 막는다 (CC BY-NC-ND 4.0 | 라이선스: LICENSE 원문 확인, GitHub… | 원본: https://github.com/TMHSDigital/Blender-Developer-Tools
- sp-upstash-context7 — upstash/context7: three.js·PSV·Spark 등 라이브러리 최신 문서를 대화에 주입 | 라이선스: MIT(MCP 클라이언트 코드) | 원본: https://github.com/upstash/context7
- sp-worldlabsai-skills — worldlabsai/skills (worldlabs·atlas-blender 스킬): Claude Code에서 World Labs API 호출·블렌더 안 스플랫 생성을 자동화 | 라이선스: Apache-2.0 | 원본: https://github.com/worldlabsai/skills
- sp-achimala-dream-loop — achimala/dream-loop: Blender+이미지 생성+비평 서브에이전트 반복 루프(렌더 품질 자동 비평 구조 참고) | 라이선스: MIT | 원본: https://github.com/achimala/dream-loop
- sp-anthropics-skills — anthropics/skills: 공식 스킬 모음. 3D 전용 스킬은 없고 mcp-builder·skill-creator를 우리 Blender 스킬 제작에 쓴다 | 라이선스: 저장소 전체 라이선스 없음(폴더별 상이) | 원본: https://github.com/anthropics/skills
- sp-doc-babylonjs-com-toolsandresources-mcpservers — Babylon.js 공식 MCP 서버(@babylonjs/mcp-servers) + llms.txt: 엔진을 Babylon으로 택할 때 노드 머티리얼(NME) 등을 에이전트가 편집 (Apache-2.0(BabylonJS/Babylon.js 저장소. | 라이선스: 미확인 | 원본: https://doc.babylonjs.com/toolsAndResources/mcpServers
- sp-cesartevisual-threejs-skills — cesartevisual/threejs-skills: three.js·R3F·WebGPU 스킬 24종(CloudAI-X 대체 후보) | 라이선스: MIT | 원본: https://github.com/cesartevisual/threejs-skills
- sp-cl0nazepamm-3dsmax-mcp — cl0nazepamm/3dsmax-mcp: 업계 인테리어 표준인 3ds Max(V-Ray/Corona)를 쓰는 협력사와 연결할 때 참고한다 | 라이선스: MIT | 원본: https://github.com/cl0nazepamm/3dsmax-mcp
- sp-cloudai-x-world-labs-skills — CloudAI-X/world-labs-skills: Claude Code 스킬: World Labs API 생성·내보내기 절차 | 라이선스: 없음 | 원본: https://github.com/CloudAI-X/world-labs-skills
- sp-coding-solo-godot-mcp — Coding-Solo/godot-mcp: Godot 엔진 MCP(참고) | 라이선스: MIT | 원본: https://github.com/Coding-Solo/godot-mcp
- sp-comfy-org-comfy-mcp — Comfy-Org/comfy-mcp: ComfyUI 공식 로컬 MCP(대안) (AGPL-3.0-or-later 또는 Comfy Org 상용 라이선스(…) | 라이선스: 미확인 | 원본: https://github.com/Comfy-Org/comfy-mcp
- sp-dcc-mcp-dcc-asset-gltf-sample-assets — dcc-mcp/dcc-asset-gltf-sample-assets: Khronos glTF 샘플 에셋 검색·다운로드(뷰어 시험용 데이터) | 라이선스: MIT | 원본: https://github.com/dcc-mcp/dcc-asset-gltf-sample-assets
- sp-dcc-mcp-dcc-asset-polyhaven — dcc-mcp/dcc-asset-polyhaven: Poly Haven CC0 HDRI·모델 검색·다운로드(소품·조명 수급) | 라이선스: MIT | 원본: https://github.com/dcc-mcp/dcc-asset-polyhaven
- sp-dcc-mcp-dcc-mcp-core — dcc-mcp/dcc-mcp-core: 여러 DCC를 묶는 게이트웨이(지금은 필요 없음) | 라이선스: MIT | 원본: https://github.com/dcc-mcp/dcc-mcp-core
- sp-dcc-mcp-dcc-mcp-sketchup — dcc-mcp/dcc-mcp-sketchup: SketchUp 모델·재질·태그·장면 검사·편집 MCP 어댑터 | 라이선스: MIT | 원본: https://github.com/dcc-mcp/dcc-mcp-sketchup
- sp-fangdididi-texture-set-intake — fangdididi/texture-set-intake: PBR 텍스처 세트 입고 검사(노멀 규약 등). 패턴 텍스처 팩 검수 규칙 참고 | 라이선스: MIT | 원본: https://github.com/fangdididi/texture-set-intake
- sp-fkrn75-gaussian-splat-to-mesh — fkrn75/gaussian-splat-to-mesh: Claude Code 스킬 + CLI: 스플랫 → 삼각형 메시 변환 | 라이선스: MIT | 원본: https://github.com/fkrn75/gaussian-splat-to-mesh
- sp-flopperam-unreal-engine-mcp — flopperam/unreal-engine-mcp: Unreal Engine 조종 MCP(커뮤니티, 라이선스 없음) | 라이선스: 없음 | 원본: https://github.com/flopperam/unreal-engine-mcp
- sp-freshtechbro-claudedesignskills — freshtechbro/claudedesignskills: three/R3F/Babylon/PlayCanvas/A-Frame 비교 학습용 | 라이선스: MIT | 원본: https://github.com/freshtechbro/claudedesignskills
- sp-gokayfem-gaussian-splat-to-blender-nodes — gaussian-splat-to-blender-nodes (에이전트 스킬): 스플랫을 Blender 메시·셰이더로 재구성 — 스캔 공간을 편집 가능한 장면으로 | 라이선스: MIT | 원본: https://github.com/gokayfem/gaussian-splat-to-blender-nodes
- sp-gokayfem-shader-skills — gokayfem/shader-skills: glslangValidator 컴파일 검사 방식만 차용(우리 합성 셰이더 사전 검사) | 라이선스: MIT | 원본: https://github.com/gokayfem/shader-skills
- sp-hueflowstudio-hueflow-sketchup-mcp — hueflowstudio/hueflow-sketchup-mcp: 한국어 SketchUp(2024~2026) MCP. 협력사가 SketchUp을 쓸 때 참고 | 라이선스: NOASSERTION | 원본: https://github.com/hueflowstudio/hueflow-sketchup-mcp
- sp-instruktlabs-kiln — instruktlabs/kiln: 절차적 3D 에셋을 에이전트로 만들고 GLB 내보내기(소품용) | 라이선스: MIT | 원본: https://github.com/instruktlabs/kiln
- sp-keeno-corp-paprika3d — Keeno-Corp/paprika3d: three.js 페이지 스크린샷·플레이·테스트·프로파일 MCP(360·워크스루 시각 검증) | 라이선스: Apache-2.0 | 원본: https://github.com/Keeno-Corp/paprika3d
- sp-jeremylongshore-tons-of-skills-marketplace-klingai-c — klingai-camera-control 스킬 (jeremylongshore/tons-of-skills-marketplace): Kling API 카메라 제어 호출 예시를 에이전트에 제공 | 라이선스: MIT | 원본: https://github.com/jeremylongshore/tons-of-skills-marketplace/tree/main/plugins/saas-packs/klingai-pack/skills/klingai-camera-control
- sp-laaielichter-threesmith — laaielichter/Threesmith: 에이전트가 쓴 three.js 코드를 버전 고정 기준으로 검토·헤드리스 점검 | 라이선스: MIT | 원본: https://github.com/laaielichter/Threesmith
- sp-laowang-wy-adai-sketchup-skill-mcp — laowang-wy/adai-sketchup-skill-mcp: SketchUp Ruby 트랜잭션·치수 되읽기·원본 이미지 대조 구조를 Blender 검증 설계에 참고한다 (CPAL-1.0 | 라이선스: LICENSE 원문 확인, GitHub 표시는 NOA… | 원본: https://github.com/laowang-wy/adai-sketchup-skill-mcp
- sp-lhlgithub-threejs-architecture-effects — lhlGitHub/threejs-architecture-effects: 건물 외관 조립 연출 참고 | 라이선스: MIT | 원본: https://github.com/lhlGitHub/threejs-architecture-effects
- sp-lichtpfad-gaussian-splat-skill — lichtpfad/gaussian-splat-skill: Claude Code 스킬: 드론 영상 → nerfstudio 스플랫 절차(학습 자동화 스킬 작성 시 참고) | 라이선스: 없음 | 원본: https://github.com/lichtpfad/gaussian-splat-skill
- sp-lusilong-blender-mcp-plus — lusilong/blender-mcp-plus: 공식 Blender Lab 도구에 Poly Haven 에셋을 붙인 변형(소품 수급) | 라이선스: GPL-3.0 | 원본: https://github.com/lusilong/blender-mcp-plus
- sp-lxie-leo-meshify — lxie-leo/meshify: 에이전트용 glTF 최적화(단순화·LOD·압축) 도구. | 라이선스: MIT | 원본: https://github.com/lxie-leo/meshify
- sp-max-786-claude-3d-harness — MAX-786/claude-3d-harness: 여러 Blender 스킬 라이브러리를 버전 고정해 한 입구로 묶는 하네스(자체 스킬 레지스트리 설계 참고) | 라이선스: MIT | 원본: https://github.com/MAX-786/claude-3d-harness
- sp-meshy-dev-meshy-3d-agent — meshy-dev/meshy-3d-agent: Meshy 유료 3D 생성 스킬(소품 한정) | 라이선스: MIT(스킬), 서비스 유료 | 원본: https://github.com/meshy-dev/meshy-3d-agent
- sp-mhyrr-sketchup-mcp — mhyrr/sketchup-mcp: SketchUp 커뮤니티 MCP 원조(참고용) | 라이선스: 없음(LICENSE 파일 없음) | 원본: https://github.com/mhyrr/sketchup-mcp
- sp-mintdotgg-mint-threejs-skills — mintdotgg/mint-threejs-skills: Mint MCP용 three.js 앱 지침 | 라이선스: MIT | 원본: https://github.com/mintdotgg/mint-threejs-skills
- sp-mlolson-blender-orchestrator — mlolson/blender-orchestrator: 공간 추론 도구가 붙은 Blender MCP(배치 정확도 아이디어 참고) | 라이선스: 없음 | 원본: https://github.com/mlolson/blender-orchestrator
- sp-paulodinis-floorplan-to-3d-house — paulodinis/floorplan-to-3d-house: 평면도(PDF·DXF) → 인터랙티브 3D → GLB Claude 플러그인 | 라이선스: MIT | 원본: https://github.com/paulodinis/floorplan-to-3d-house
- sp-samg-coder-threebrowserstudio — SamG-Coder/ThreeBrowserStudio: LLM 우선 three.js WebGPU 장면 편집 MCP 참고 | 라이선스: MIT | 원본: https://github.com/SamG-Coder/ThreeBrowserStudio
- sp-samuelasherrivello-ai-skills-blender — SamuelAsherRivello/ai-skills-blender: Blender Lab MCP 기반 스킬 묶음(공식 MCP를 쓸 때 스킬 참고) | 라이선스: MIT | 원본: https://github.com/SamuelAsherRivello/ai-skills-blender
- sp-scenario-labs-skills — scenario-labs/skills: Scenario MCP 기반 이미지·3D 생성 스킬(Blender·Unreal 워크플로 포함) | 라이선스: MIT(스킬), 서비스 유료 | 원본: https://github.com/scenario-labs/skills
- sp-shattenjagger-sketchup-mcp-bridge — Shattenjagger/sketchup-mcp-bridge: SketchUp Pro 2026 대응 MCP(mhyrr 판 동기화·멈춤 수정) | 라이선스: MIT | 원본: https://github.com/Shattenjagger/sketchup-mcp-bridge
- sp-spaitial-ai-spaitial-ai-plugin — spaitial-ai/spaitial-ai-plugin: Claude에서 Echo 월드 생성·파노라마 편집·메시 내보내기(호스팅 MCP) | 라이선스: 없음 | 원본: https://github.com/spaitial-ai/spaitial-ai-plugin
- sp-starryark-ref2scene — starryark/ref2scene: 참조 사진 → 카메라 정합 Blender 장면(화이트 장면 역생성 참고) | 라이선스: MIT | 원본: https://github.com/starryark/ref2scene
- sp-tallslab-threeforge — tallslab/threeforge: three.js 프레임 예산 진단 CLI·MCP 참고 | 라이선스: MIT | 원본: https://github.com/tallslab/threeforge
- sp-api-sketchup-com-mcp-v1-sketchup-mcp — Trimble SketchUp 공식 커넥터(원격 MCP): 대화로 방·가구 초안을 SketchUp 모델로 만드는 공식 경로(쿠홈 대체 후보 검토) | 라이선스: 상용 서비스 | 원본: https://api.sketchup.com/mcp/v1/sketchup/mcp
- sp-iart-ai-webgl-animation-skills — webgl-animation-skills (iart-ai): GLSL 셰이더·GPU 렌더 문제 해결 스킬 참고 | 라이선스: MIT | 원본: https://github.com/iart-ai/webgl-animation-skills
- sp-dgreenheck-webgpu-claude-skill — webgpu-claude-skill: three.js WebGPU/TSL 셰이더 작성 보조(UV 패스 재합성 셰이더 등) | 라이선스: 없음 | 원본: https://github.com/dgreenheck/webgpu-claude-skill
- sp-zinin-sketchup-mcp2 — zinin/sketchup-mcp2: SketchUp MCP 대안(참고) | 라이선스: MIT | 원본: https://github.com/zinin/sketchup-mcp2
- sp-binomialllc-basis-universal — Basis Universal v2.5 (BinomialLLC/basis_universal): 패턴 텍스처를 KTX2(UASTC LDR 4x4, 8bpp)로 압축해 GPU 메모리 1/4로 전달 | 라이선스: Apache-2.0 | 원본: https://github.com/BinomialLLC/basis_universal
- sp-blender-blender — Blender 본체(GitHub 미러): 장면 모델링·패스 렌더·야간 일괄 렌더의 중심 도구(렌더 결과물은 GPL 대상 아님) | 라이선스: GPL-2.0-or-later | 원본: https://github.com/blender/blender
- sp-colour-science-colour — colour-science/colour: CIEDE2000 색차, 색공간 변환(스캔 원본 vs 결과 색 검수) | 라이선스: BSD-3-Clause | 원본: https://github.com/colour-science/colour
- sp-depthanything-depth-anything-v2 — Depth Anything V2: 목업 이미지의 깊이 맵 추정(패럴랙스·초점 이동·면 평면 추정의 입력) | 라이선스: Small Apache-2.0, Base/Large/Giant CC-B… | 원본: https://github.com/DepthAnything/Depth-Anything-V2
- sp-dingkeyan93-dists — DISTS (dingkeyan93/DISTS): 텍스처 리샘플링에 관대한 구조·질감 지표. '같은 무늬인가'를 판단 | 라이선스: MIT | 원본: https://github.com/dingkeyan93/DISTS
- sp-exiftool-exiftool — exiftool/exiftool: 패턴 EXIF 회전·DPI 일괄 점검표 | 라이선스: Perl과 같은 조건(Artistic 또는 GPL 선택) | 원본: https://github.com/exiftool/exiftool
- sp-cvg-geocalib — GeoCalib (cvg/GeoCalib): AI 이미지 한 장의 초점거리·중력 방향(롤·피치)을 구해 면 호모그래피·바닥 수평·카메라 높이를 맞춘다 | 라이선스: 코드 Apache-2.0, 가중치 CC-BY-4.0 | 원본: https://github.com/cvg/GeoCalib
- sp-gfxdisp-colorvideovdp — gfxdisp/ColorVideoVDP: 화면 크기·해상도·시청 거리를 넣어 1배 대비 1.4·2·3배 확대 자극의 보이는 차이(JOD)를 기기별로 실측 | 라이선스: MIT(LICENSE 원문 확인) | 원본: https://github.com/gfxdisp/ColorVideoVDP
- sp-khronosgroup-ktx-software — KTX-Software (toktx / ktx create): 패턴 1,300종 KTX2 일괄 변환(밉맵 포함) | 라이선스: 주로 Apache-2.0(REUSE 다중 라이선스), external/… | 원본: https://github.com/KhronosGroup/KTX-Software
- sp-cvg-lightglue — LightGlue (cvg/LightGlue): AI 결과와 원본 패턴의 특징점을 대응시켜 휨·늘어남을 측정하고 paste-back 호모그래피를 추정 | 라이선스: Apache-2.0 (코드·LightGlue 가중치), SuperPoi… | 원본: https://github.com/cvg/LightGlue
- sp-lovell-sharp — lovell/sharp (libvips 기반 타일 생성): 8K 파노라마를 다중 해상도 타일 피라미드·AVIF/WebP로 서버 사전 변환 | 라이선스: 코드 Apache-2.0, 함께 배포되는 libvips 바이너리는 LG… | 원본: https://github.com/lovell/sharp
- sp-richzhang-perceptualsimilarity — LPIPS (richzhang/PerceptualSimilarity): 정합한 패치끼리 지각 차이를 재는 지표(충실도 검수) | 라이선스: BSD-2-Clause | 원본: https://github.com/richzhang/PerceptualSimilarity
- sp-prs-eth-marigold — Marigold v1.1 (prs-eth/Marigold) — Depth·Normals·IID Appearance·IID Lighting: AI 목업에서 알베도/음영/비확산 잔차(IID Lighting)를 분리해 음영 레이어에 원본 패턴을 곱해 넣는다 (코드 Apache-2.0 / 모델 RAIL++-M(HF openrail…) | 라이선스: 미확인 | 원본: https://github.com/prs-eth/Marigold
- sp-zeux-meshoptimizer — meshoptimizer (gltfpack): 가구·방 메시 압축·로딩 단축 | 라이선스: MIT | 원본: https://github.com/zeux/meshoptimizer
- sp-microsoft-moge — microsoft/MoGe: 화이트 장면 1장에서 카메라·평면·스케일 추정, Atlas 자동 등록 보조 | 라이선스: 코드 MIT(DINOv2 부분 Apache-2.0), 가중치 Ruich… | 원본: https://github.com/microsoft/MoGe
- sp-mrnerf-lichtfeld-studio — MrNeRF/LichtFeld-Studio: Windows 네이티브 학습·편집·내보내기(PLY/SOG/SPZ/HTML). | 라이선스: GPL-3.0 | 원본: https://github.com/MrNeRF/LichtFeld-Studio
- sp-nerfstudio-project-gsplat — nerfstudio-project/gsplat: 서버(3070 Ti)에서 Blender 렌더 → 스플랫 학습을 파이썬으로 자동화하는 핵심 라이브러리 | 라이선스: Apache-2.0 | 원본: https://github.com/nerfstudio-project/gsplat
- sp-opencv-opencv — OpenCV (SIFT·USAC_MAGSAC·warpPerspective): RootSIFT+MAGSAC++ 정합, 원근 변환(INTER_AREA·LANCZOS4) 계산 합성의 기본기 | 라이선스: Apache-2.0 | 원본: https://github.com/opencv/opencv
- sp-photosynthesis-team-piq — photosynthesis-team/piq: 패턴 불변 검수(LPIPS·DISTS·SSIM). 비상업 pyiqa의 상용 대체 | 라이선스: Apache-2.0 | 원본: https://github.com/photosynthesis-team/piq
- sp-playcanvas-splat-transform — playcanvas/splat-transform: PLY→SOG/Streamed SOG/SPZ 변환, 스플랫 수 줄이기, 여러 스플랫 합치기, 충돌용 collision.glb 생성 (CLI·Node 라이브러리) | 라이선스: MIT | 원본: https://github.com/playcanvas/splat-transform
- sp-playcanvas-supersplat — playcanvas/supersplat (SuperSplat 편집기): 학습된 스플랫의 떠다니는 점 제거·크롭·정렬·패턴 면 영역 삭제·walk mode 미리보기 | 라이선스: MIT | 원본: https://github.com/playcanvas/supersplat
- sp-facebookresearch-sam3 — SAM 3 / SAM 3.1 (facebookresearch/sam3): 'floor', 'cabinet door', 'wall' 같은 글자 프롬프트로 AI 목업·화이트 장면에서 패턴 입힐 면 마스크를 자동으로 뽑는다 | 라이선스: SAM License(2025-11-19 판, 코드+가중치 공통) | 원본: https://github.com/facebookresearch/sam3
- sp-scikit-image-scikit-image — scikit-image: deltaE_ciede2000, GLCM 질감 통계, 리샘플링 (BSD-3-Clause | 라이선스: LICENSE.txt, 일부 파일 MIT 등… | 원본: https://github.com/scikit-image/scikit-image
- sp-sunset1995-py360convert — sunset1995/py360convert / ProGamerGov/pytorch360convert (+ComfyUI_pytorch360convert): 등장방형↔큐브맵↔원근 변환(평면 목업을 ERP에 놓기, 패턴 면을 큐브면에서 계산) | 라이선스: MIT (세 저장소 모두) | 원본: https://github.com/sunset1995/py360convert
- sp-yunfanye-openhouse-3d — yunfanye/openhouse-3d: 사진→bpy 절차 건축(벽·개구부·창호·주방·가구)→Cycles 렌더까지 1인+AI 에이전트가 집을 다시 짓는 실제 작업 방식과 코드 구조의 본보기 | 라이선스: MIT | 원본: https://github.com/yunfanye/openhouse-3d
- sp-academysoftwarefoundation-openexr — AcademySoftwareFoundation/openexr: 베이크 후처리 Python 스크립트에서 EXR → 16비트 PNG·Ultra HDR 변환 | 라이선스: BSD-3-Clause | 원본: https://github.com/AcademySoftwareFoundation/openexr
- sp-adobe-trustmark — adobe/trustmark: 고객용 축소판 텍스처에 고객 ID(100비트)를 보이지 않게 넣어 유출자 추적 (MIT(코드와 첫 사용 시 내려받는 모델 파일 모두, README 명시…) | 라이선스: 미확인 | 원본: https://github.com/adobe/trustmark
- sp-shiaoming-aliked — ALIKED: LightGlue 정합을 상업용으로 쓸 때 SuperPoint(비상업) 대신 쓰는 특징점 추출기(충실도 검수·소급 정합) | 라이선스: BSD-3-Clause | 원본: https://github.com/Shiaoming/ALIKED
- sp-aomediacodec-libavif — AOMediaCodec/libavif: 조명 레이어를 AVIF로 압축해 전송량 절감 (BSD-2-Clause(LICENSE 직접 확인, GitHub 표기 N…) | 라이선스: 미확인 | 원본: https://github.com/AOMediaCodec/libavif
- sp-arthurbrussee-brush — ArthurBrussee/brush: CUDA 없이(WebGPU) 도는 학습기. 설치 없이 브라우저에서 학습하는 시험, 마스크 폴더 지원 | 라이선스: Apache-2.0 | 원본: https://github.com/ArthurBrussee/brush
- sp-blenderkit-blendkit — BlenderKit/Blendkit (구 BlenderKit): 가구·소품 에셋 대량 확보(RF·CC0) | 라이선스: 애드온 GPL-2.0, 에셋은 Royalty Free 또는 CC0 | 원본: https://github.com/BlenderKit/Blendkit
- sp-cesiumgs-webglreport — CesiumGS/webglreport: 기기 측정 페이지(/probe)의 WebGL 항목 참고 | 라이선스: Apache-2.0 | 원본: https://github.com/CesiumGS/webglreport
- sp-contentauth-c2pa-rs — contentauth/c2pa-rs: 고객판 이미지에 출처·저작권 메타(Content Credentials)를 붙이는 표준 구현(TrustMark와 함께) | 라이선스: MIT/Apache-2.0 | 원본: https://github.com/contentauth/c2pa-rs
- sp-cvlab-epfl-disk — DISK: LightGlue 상업 조합용 특징점 추출기(SuperPoint 대체) | 라이선스: Apache-2.0 | 원본: https://github.com/cvlab-epfl/disk
- sp-dlr-rm-blenderproc — DLR-RM/BlenderProc: Blender 배치 렌더 파이프라인(세그멘테이션·깊이·노멀 등 패스 출력) 구조 참고 | 라이선스: GPL-3.0 | 원본: https://github.com/DLR-RM/BlenderProc
- sp-facebookresearch-vggt — facebookresearch/vggt: 영상 프레임 카메라·깊이 추정(평면 추적 합성·스플랫 초기화) | 라이선스: 코드 상업 허용(2025-07-29 변경, 군사 제외) / 원래 체크포… | 원본: https://github.com/facebookresearch/vggt
- sp-fuenwang-equirec2perspec — fuenwang/Equirec2Perspec: 쿠홈 sphere.jpg에서 원하는 시점의 평면 컷을 잘라 원본 스캔과 결 비교(실측 검증) | 라이선스: MIT | 원본: https://github.com/fuenwang/Equirec2Perspec
- sp-guofei9987-blind-watermark — guofei9987/blind_watermark: 가벼운 주파수 영역(DWT-DCT-SVD) 보이지 않는 워터마크 대안 | 라이선스: MIT | 원본: https://github.com/guofei9987/blind_watermark

## V2 평면 확장

- sp-artokun-comfyui-mcp — artokun/comfyui-mcp: 로컬 ComfyUI 워크플로를 LLM이 짜고 돌리게 한다. | 라이선스: MIT | 원본: https://github.com/artokun/comfyui-mcp
- sp-judyzz-threejs-parallax-skill — JudyZZ/threejs-parallax-skill: 투명 PNG 레이어로 2.5D 패럴랙스. V2 평면 목업에 깊이감 부여 | 라이선스: MIT | 원본: https://github.com/JudyZZ/threejs-parallax-skill
- sp-h-canopy-2d-to-3d-web — H-Canopy/2d-to-3d-web: 2D 이미지를 깊이 있는 인터랙티브 웹 장면으로(V2 참고) | 라이선스: MIT | 원본: https://github.com/H-Canopy/2d-to-3d-web
- sp-kpal81xd-spatial-artifacts — kpal81xd/spatial-artifacts: Claude Code에서 3D 목업을 궤도 회전·기즈모로 다루는 방식 참고 | 라이선스: MIT | 원본: https://github.com/kpal81xd/spatial-artifacts
- sp-roeea2-scrolling-web-site-with-vidtsx — roeea2/scrolling-web-site-with-vidtsx (Claude Code 스킬): 스크롤 애니메이션 웹 제작 스킬(참고만) | 라이선스: MIT | 원본: https://github.com/roeea2/scrolling-web-site-with-vidtsx
- sp-annotorious-annotorious — Annotorious v3: 가구·면 위 핫스팟·다각형 주석(패턴명·코드·확대 컷 연결)과 OpenSeadragon 연동 | 라이선스: BSD-3-Clause | 원본: https://github.com/annotorious/annotorious
- sp-huggingface-co-onnx-community-depth-anything-v2-smal — Depth Anything V2 (DepthAnything/Depth-Anything-V2) + onnx-community/depth-anything-v2-small: 브라우저(transformers.js)에서 결과 이미지의 깊이를 즉석 계산해 호버 패럴랙스·2.5D 틸트를 서버 없이 띄운다 | 라이선스: Small(ONNX·원본) Apache-2.0. Base·Large는… | 원본: https://huggingface.co/onnx-community/depth-anything-v2-small
- sp-strawdynamics-drift — Drift (strawdynamics/drift): 마우스를 올리면 옆 창이나 렌즈에 확대 이미지를 띄우는 가벼운 돋보기 | 라이선스: BSD-2-Clause | 원본: https://github.com/strawdynamics/drift
- sp-facebookresearch-sam2 — facebookresearch/sam2: 결과 3,446장과 화이트 장면의 면 마스크 소급 생성 | 라이선스: Apache-2.0(코드·가중치) | 원본: https://github.com/facebookresearch/sam2
- sp-image-js-fast-png — image-js/fast-png: 브라우저에서 16비트 UV PNG를 직접 디코딩해 UnsignedShort/Float 텍스처로 올림 | 라이선스: MIT | 원본: https://github.com/image-js/fast-png
- sp-sneas-img-comparison-slider — img-comparison-slider: 빈 공간 vs 적용, 패턴 A vs B 전후 비교 슬라이더(웹 컴포넌트) | 라이선스: MIT | 원본: https://github.com/sneas/img-comparison-slider
- sp-libvips-libvips — libvips/libvips: 패턴 1,308장·결과 3,446장 DZI 타일 피라미드 사전 생성 | 라이선스: LGPL-2.1 | 원본: https://github.com/libvips/libvips
- sp-openseadragon-openseadragon — OpenSeadragon: V2 평면 목업·패턴 원본의 딥줌(타일 확대) 뷰어 | 라이선스: BSD-3-Clause | 원본: https://github.com/openseadragon/openseadragon
- sp-mrdoob-three-js — three.js r187: 브라우저 합성 셰이더 본체(전체 화면 패스, textureGrad, 비등방 필터)와 EXR·UltraHDR·KTX2 로더 | 라이선스: MIT | 원본: https://github.com/mrdoob/three.js
- sp-annotorious-annotorious-annotorious-openseadragon — @annotorious/openseadragon: OpenSeadragon 위 면 하이라이트·핫스팟 주석의 실제 설치 단위(npm 3.9.5) | 라이선스: BSD-3-Clause | 원본: https://github.com/annotorious/annotorious/tree/main/packages/annotorious-openseadragon
- sp-bytedance-seed-depth-anything-3 — ByteDance-Seed/Depth-Anything-3: 결과 이미지 깊이 추정 → V2 패럴랙스·면 분리 | 라이선스: 코드 Apache-2.0 / 가중치: SMALL·BASE·METRIC-… | 원본: https://github.com/ByteDance-Seed/Depth-Anything-3
- sp-brokensource-depthflow — DepthFlow (BrokenSource/DepthFlow): 결과 이미지+깊이로 GLSL 레이마칭 패럴랙스 영상/루프 생성(목업 공유용 짧은 움직임) | 라이선스: AGPL-3.0 | 원본: https://github.com/BrokenSource/DepthFlow
- sp-google-model-viewer — google/model-viewer: 가구 단품 glTF 회전·근접 확대(V2 가구 3D 미리보기) | 라이선스: Apache-2.0 | 원본: https://github.com/google/model-viewer

## V3 360 뷰어

- sp-ahujasid-mcp-for-blender — ahujasid/mcp-for-blender(옛 blender-mcp): Claude Code로 Blender 5.2 장면 제작·ID/UV/조명 패스 굽기 자동화 | 라이선스: MIT | 원본: https://github.com/ahujasid/mcp-for-blender
- sp-oisinryan-unreal-360-render-skill — oisinryan/unreal-360-render-skill: 공개 스킬 중 유일한 360 등장방형 렌더 스킬(UE). | 라이선스: MIT | 원본: https://github.com/oisinryan/unreal-360-render-skill
- sp-sunset1995-horizonnet — HorizonNet (sunset1995/HorizonNet): 360 화이트 파노라마에서 바닥·천장·벽 경계(맨해튼 방 구조)를 뽑아 각 벽면에 패턴을 정확히 투영 | 라이선스: MIT(코드) | 원본: https://github.com/sunset1995/HorizonNet
- sp-mpetroff-pannellum — Pannellum: 합성이 끝난 등장방형·큐브맵 타일을 보여 주는 가벼운 360 뷰어(multires·핫스팟·투어) | 라이선스: MIT | 원본: https://github.com/mpetroff/pannellum
- sp-mistic100-photo-sphere-viewer — Photo Sphere Viewer: three.js 기반 360 뷰어(플러그인: 마커·가상 투어·타일) — 셰이더 확장이 쉬운 후보 | 라이선스: MIT | 원본: https://github.com/mistic100/Photo-Sphere-Viewer

## V4 워크스루

- sp-img2threejs-plugin-interior — img2threejs/plugin-interior (img2 Interior): 방 사진 1장 → 편집 가능한 .blend + 간접광 구운 GLB + three.js 뷰어. | 라이선스: img2 Interior Free Use, Restricted Comm… | 원본: https://github.com/img2threejs/plugin-interior
- sp-playcanvas-skills — playcanvas/skills v0.6.2: V4 PlayCanvas 경로에서 bake-lighting·verify-pixels·inspect-glb를 그대로 쓰는 공식 스킬 16종 | 라이선스: MIT | 원본: https://github.com/playcanvas/skills
- sp-saad-git-007-claude-skills — saad-git-007/claude-skills → web3d-realism-performance: Cycles 라이트맵(UV2)+반사 프로브+glTF 최적화 참조 파이프라인. | 라이선스: MIT | 원본: https://github.com/saad-git-007/claude-skills
- sp-viettranx-3dviz-pro-max — viettranx/3dviz-pro-max: '건축과 실내' 레시피(가구 배치·일조)와 capture.py 시점별 캡처를 장면 연출 참고로 사용 | 라이선스: MIT | 원본: https://github.com/viettranx/3dviz-pro-max
- sp-gamedev-skills-awesome-gamedev-agent-skills — gamedev-skills/awesome-gamedev-agent-skills: three.js·Godot·Unity 스킬 77종에서 V4 웹 워크스루용 three.js 스킬을 고른다 | 라이선스: Apache-2.0 | 원본: https://github.com/gamedev-skills/awesome-gamedev-agent-skills
- sp-playcanvas-editor-mcp-server — playcanvas/editor-mcp-server: PlayCanvas 클라우드 에디터 자동화 | 라이선스: MIT | 원본: https://github.com/playcanvas/editor-mcp-server
- sp-yomotsu-camera-controls — camera-controls: 지점 이동·'이 가구 보기' 부드러운 카메라 전환 | 라이선스: MIT | 원본: https://github.com/yomotsu/camera-controls
- sp-donmccurdy-gltf-transform — glTF-Transform: V4 장면의 Draco/meshopt·KTX2 압축 자동화(iPhone 크래시·로딩 불만 대책) | 라이선스: MIT | 원본: https://github.com/donmccurdy/glTF-Transform
- sp-khronosgroup-gltf-blender-io — KhronosGroup/glTF-Blender-IO: Blender→glTF/GLB 내보내기(웹 뷰어·워크스루 공통 포맷) | 라이선스: Apache-2.0 | 원본: https://github.com/KhronosGroup/glTF-Blender-IO
- sp-sparkjsdev-spark — sparkjsdev/spark (Spark 2.x): V3·V4 웹 뷰어 본체: 스플랫 배경 + three.js 패턴 메시를 한 화면에 합성 | 라이선스: MIT | 원본: https://github.com/sparkjsdev/spark
- sp-gkjohnson-three-gpu-pathtracer — three-gpu-pathtracer: 카메라가 멈추면 브라우저에서 사진 품질로 다듬기, V2 근접 컷 즉시 생성 | 라이선스: MIT | 원본: https://github.com/gkjohnson/three-gpu-pathtracer
- sp-gkjohnson-three-mesh-bvh — three-mesh-bvh: 클릭 이동·표면 선택용 고속 레이캐스트(경로추적 기반) | 라이선스: MIT | 원본: https://github.com/gkjohnson/three-mesh-bvh
- sp-babylonjs-babylon-js — BabylonJS/Babylon.js: three.js 대안 웹 3D 엔진(라이트맵·PBR·WebGPU 내장 기능 많음) | 라이선스: Apache-2.0 | 원본: https://github.com/BabylonJS/Babylon.js
- sp-pmndrs-drei — drei: R3F 보조(카메라 컨트롤·평면 반사 MeshReflectorMaterial·KTX2 로더 등) | 라이선스: MIT(drei·R3F 모두) | 원본: https://github.com/pmndrs/drei
- sp-google-draco — google/draco: glTF 메시 압축(워크스루 전송량 절감) | 라이선스: Apache-2.0 | 원본: https://github.com/google/draco

## V5 메타버스·AI 직행

- sp-chir24-unreal-mcp — ChiR24/Unreal_mcp: Unreal 에디터를 C++ 자동화 브리지로 제어(V5 참고) | 라이선스: MIT | 원본: https://github.com/ChiR24/Unreal_mcp
- sp-coplaydev-unity-mcp — CoplayDev/unity-mcp: V5에서 게임 엔진을 쓰게 될 때를 대비한 참고(Unity 에디터 제어) | 라이선스: MIT | 원본: https://github.com/CoplayDev/unity-mcp
- sp-danielcanton-webxr-dev-skill — danielcanton/webxr-dev-skill: Claude Code로 three.js WebXR(Quest) 개발할 때 참고 스킬 | 라이선스: MIT | 원본: https://github.com/danielcanton/webxr-dev-skill
- sp-epicgames-unreal-engine-skills-for-claude-code-plugi — EpicGames/unreal-engine-skills-for-claude-code-plugin + Unreal MCP(에디터 내장): V5에서 Unreal을 고를 때 에디터를 LLM으로 조작하는 공식 경로 | 라이선스: MIT(플러그인), 엔진은 Epic EULA | 원본: https://github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin
- sp-ivanmurzak-unity-mcp — IvanMurzak/Unity-MCP: Unity용 스킬·MCP·CLI(참고) | 라이선스: Apache-2.0 | 원본: https://github.com/IvanMurzak/Unity-MCP
- sp-tumourlove-monolith — tumourlove/monolith: UE 5.7·5.8 블루프린트·머티리얼 읽기쓰기 MCP(V5 참고) | 라이선스: MIT | 원본: https://github.com/tumourlove/monolith
- sp-unity-technologies-unity-agent-plugin — Unity-Technologies/unity-agent-plugin (Unity 공식): V5 엔진 후보 비교용. Unity 6 이상 프로젝트를 Unity CLI로 조작하는 스킬 33종 (Unity Companion License(GitHub 표시 NOASS…) | 라이선스: 미확인 | 원본: https://github.com/Unity-Technologies/unity-agent-plugin
