param(
  [Parameter(Mandatory=$true)][ValidateSet(4,5,6)][int]$Episode,
  [string]$BlenderBin=$env:BLENDER_BIN,
  [switch]$RebuildScene
)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
if (-not $BlenderBin -or -not (Test-Path -LiteralPath $BlenderBin)) {
  throw 'BLENDER_BIN 또는 -BlenderBin에 설치된 blender.exe의 절대 경로를 지정하세요.'
}
Push-Location $projectRoot
try {
  $episodeDir=Join-Path $projectRoot "episodes/ep$Episode"
  foreach($name in @('narration.wav','timeline.json','captions.json')) {
    if(-not (Test-Path -LiteralPath (Join-Path $episodeDir $name))) { throw "먼저 대본·음성을 확정하고 자막 정렬을 준비하세요: $name" }
  }
  $scene=Join-Path $episodeDir 'scene.blend'
  if($RebuildScene -or -not (Test-Path -LiteralPath $scene)) {
    & $BlenderBin -b --python-exit-code 1 -P scripts/build_episode.py -- --ep $Episode --proofs
    if($LASTEXITCODE -ne 0) { throw '장면 생성 실패' }
  }
  & $BlenderBin -b $scene --python-exit-code 1 -P scripts/render_frames.py -- --output (Join-Path $episodeDir 'render') --width 1080 --height 1920 --samples 24
  if($LASTEXITCODE -ne 0) { throw 'Blender 프레임 렌더 실패. 정상 캐시는 다음 실행에 재사용됩니다.' }
  python -X utf8 scripts/compose_episode.py --ep $Episode
  if($LASTEXITCODE -ne 0) { throw '리모션 합성 또는 최종 검증 실패' }
  Write-Output "완료: $episodeDir/EP$Episode-블렌더-v2.mp4"
} finally { Pop-Location }
