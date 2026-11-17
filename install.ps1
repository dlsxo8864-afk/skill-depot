# 스킬 창고 설치 스크립트 (Windows PowerShell 5.1 이상)
#
# 사용 예
#   iwr <주소>/install.ps1 -OutFile $env:TEMP\depot.ps1
#   powershell -ExecutionPolicy Bypass -File $env:TEMP\depot.ps1 <대상> -Agent claude -Base <주소>
#
# <대상>  list(목록 보기) | 스킬 이름 | pack:<묶음 id>
# -Agent  claude(기본) | codex
# -Dest   스킬들이 놓일 폴더를 직접 지정(그 아래 <이름>\ 으로 설치)
# -Base   사이트 주소. 없으면 환경변수 DEPOT_BASE, 그다음 이 파일에 박힌 주소

[CmdletBinding()]
param(
    [Parameter(Position = 0)][string]$Target = "list",
    [ValidateSet("claude", "codex")][string]$Agent = "claude",
    [string]$Dest = "",
    [string]$Base = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

$EmbeddedBase = "https://dlsxo8864-afk.github.io/skill-depot"

function Say([string]$Message) { [Console]::Out.WriteLine($Message) }
function Warn([string]$Message) { [Console]::Error.WriteLine($Message) }

# 사이트 주소: 인자 > 환경변수 > 박힌 주소(빌드 때 치환되지 않았으면 __ 로 시작한다)
$BaseUrl = ""
if ($Base -ne "") { $BaseUrl = $Base }
elseif ($env:DEPOT_BASE) { $BaseUrl = $env:DEPOT_BASE }
elseif ($EmbeddedBase -ne "" -and $EmbeddedBase -notlike "__*") { $BaseUrl = $EmbeddedBase }
$BaseUrl = $BaseUrl.TrimEnd("/")

$script:WorkDir = Join-Path ([System.IO.Path]::GetTempPath()) ("depot-" + [guid]::NewGuid().ToString("N"))

function Format-Size([long]$Bytes) {
    if ($Bytes -ge 1048576) { return ("{0:N1}MB" -f ($Bytes / 1048576)) }
    if ($Bytes -ge 1024) { return ("{0:N0}KB" -f ($Bytes / 1024)) }
    return ("{0}B" -f $Bytes)
}

# 탭 구분 목록을 받아 줄마다 칸 배열로 돌려준다
function Get-Rows([string]$Name) {
    $path = Join-Path $script:WorkDir $Name
    Invoke-WebRequest -Uri ($BaseUrl + "/" + $Name) -OutFile $path -UseBasicParsing
    $text = [System.Text.Encoding]::UTF8.GetString([System.IO.File]::ReadAllBytes($path))
    $rows = @()
    foreach ($line in ($text -split "`n")) {
        $l = $line.TrimEnd("`r")
        if ($l.Trim() -eq "") { continue }
        $rows += , ($l -split "`t")
    }
    return , $rows
}

# 있던 폴더를 옆의 백업 폴더로 옮긴다(지우지 않는다)
function Move-Aside([string]$Target, [string]$BackupRoot, [string]$Stamp) {
    if (-not (Test-Path -LiteralPath $Target)) { return }
    if (-not (Test-Path -LiteralPath $BackupRoot)) { New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null }
    $bak = Join-Path $BackupRoot ((Split-Path -Leaf $Target) + "-" + $Stamp)
    Move-Item -LiteralPath $Target -Destination $bak
    Say "  있던 폴더는 남겨 둠: $bak"
}

function Show-List($Rows) {
    $kindName = @{ skill = "스킬"; command = "명령어"; bundle = "스킬 묶음"; external = "원본 설치"; builtin = "앱 기본" }
    Say "받을 수 있는 것과 목록만 있는 것"
    foreach ($r in $Rows) {
        $kind = $kindName[$r[1]]
        if ($null -eq $kind) { $kind = $r[1] }
        $size = "-"
        if ($r[3] -ne "-") { $size = Format-Size ([long]$r[5]) }
        Say ("  " + $r[0].PadRight(34) + $kind.PadRight(8) + $size.PadRight(9) + $r[6])
    }
    $packs = Get-Rows "packs.tsv"
    if ($packs.Count -gt 0) {
        Say ""
        Say "묶음"
        foreach ($p in $packs) {
            $count = ($p[2] -split ",").Count
            Say ("  " + ("pack:" + $p[0]).PadRight(34) + $p[1] + " (" + $count + "개)")
        }
    }
    Say ""
    Say "설치: 이 스크립트에 이름 또는 pack:<묶음 id> 를 넘깁니다."
}

function Install-One([string]$Name, $Rows) {
    $row = $null
    foreach ($r in $Rows) { if ($r[0] -eq $Name) { $row = $r; break } }
    if ($null -eq $row) {
        Warn "찾지 못했습니다: ${Name} (list 로 이름을 확인하세요)"
        return $false
    }
    $kind = $row[1]
    $zipPath = $row[3]
    $sha = $row[4]
    $needs = "-"
    if ($row.Length -ge 8) { $needs = $row[7] }
    $how = "-"
    if ($row.Length -ge 9) { $how = $row[8] }

    if ($kind -eq "builtin") {
        Say "${Name}: Claude 앱에 들어 있어 받을 필요가 없습니다."
        return $true
    }
    if ($kind -eq "external") {
        Say "${Name}: 이 창고에는 파일이 없습니다. 원본에서 설치합니다(이 스크립트는 아래 명령을 실행하지 않습니다)."
        if ($how -ne "-" -and $how -ne "") { Say "  $how" }
        return $true
    }
    if ($kind -eq "command" -and $Agent -eq "codex") {
        Say "${Name}: 명령어는 Claude Code 전용이라 건너뜁니다."
        return $true
    }
    if ($kind -eq "command" -and $Dest -ne "") {
        Say "${Name}: -Dest 를 준 경우 명령어는 건너뜁니다."
        return $true
    }

    $root = Join-Path $HOME ("." + $Agent)
    $skillsDir = Join-Path $root "skills"
    if ($Dest -ne "") { $skillsDir = $Dest }
    $commandsDir = Join-Path $root "commands"

    try {
        # 1. 받기
        $zip = Join-Path $script:WorkDir ($Name + ".zip")
        Invoke-WebRequest -Uri ($BaseUrl + "/" + $zipPath) -OutFile $zip -UseBasicParsing

        # 2. 해시 비교
        $got = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLower()
        if ($got -ne $sha.ToLower()) {
            Remove-Item -LiteralPath $zip -Force
            Warn "${Name}: sha256 이 목록과 다릅니다. 설치하지 않습니다. (목록 $sha / 받은 것 $got)"
            return $false
        }

        # 3. zip 안 경로 검사
        $bad = $null
        $arc = [System.IO.Compression.ZipFile]::OpenRead($zip)
        try {
            foreach ($e in $arc.Entries) {
                $n = $e.FullName
                if ($n.Contains("..") -or $n.StartsWith("/") -or $n.StartsWith("\") -or $n -match "^[A-Za-z]:") { $bad = $n; break }
            }
        }
        finally { $arc.Dispose() }
        if ($null -ne $bad) {
            Warn "${Name}: zip 안에 위험한 경로가 있습니다. 설치하지 않습니다. ($bad)"
            return $false
        }

        # 4. 임시 폴더에 풀기
        $ext = Join-Path $script:WorkDir ("x-" + $Name)
        [System.IO.Compression.ZipFile]::ExtractToDirectory($zip, $ext)
        $stamp = (Get-Date).ToString("yyyyMMdd-HHmmss")

        # 5. 있던 것은 옆 폴더에 남기고 설치.
        #    백업을 skills 폴더 안에 두면 같은 이름의 스킬이 둘로 읽히므로 <skills>-backup 에 둔다.
        if ($kind -eq "skill") {
            if (-not (Test-Path -LiteralPath (Join-Path $ext "SKILL.md"))) {
                Warn "${Name}: zip 안에 SKILL.md 가 없습니다. 설치하지 않습니다."
                return $false
            }
            $target = Join-Path $skillsDir $Name
            if (-not (Test-Path -LiteralPath $skillsDir)) { New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null }
            Move-Aside $target ($skillsDir.TrimEnd("\", "/") + "-backup") $stamp
            Copy-Item -LiteralPath $ext -Destination $target -Recurse -Force
            Say "설치됨: $target"
        }
        elseif ($kind -eq "bundle") {
            # 받은 묶음 안에서 SKILL.md 가 있는 폴더를 모두 스킬로 설치한다(얕은 폴더부터)
            if (-not (Test-Path -LiteralPath $skillsDir)) { New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null }
            $bakRoot = $skillsDir.TrimEnd("\", "/") + "-backup"
            $extFull = (Get-Item -LiteralPath $ext).FullName.TrimEnd("\")
            $found = @(Get-ChildItem -LiteralPath $ext -Recurse -File -Filter "SKILL.md" |
                Where-Object { $_.FullName -notmatch "\\node_modules\\" } |
                Sort-Object { $_.FullName.Length })
            if ($found.Count -eq 0) {
                $packRoot = $skillsDir.TrimEnd("\", "/") + "-packs"
                if (-not (Test-Path -LiteralPath $packRoot)) { New-Item -ItemType Directory -Path $packRoot -Force | Out-Null }
                $target = Join-Path $packRoot $Name
                Move-Aside $target $bakRoot $stamp
                Copy-Item -LiteralPath $ext -Destination $target -Recurse -Force
                Say "받음: $target"
                Say "  스킬 형식(SKILL.md)이 아닙니다. 안의 README 를 읽고 따르세요."
            }
            else {
                $done = @{}
                foreach ($f in $found) {
                    $dir = $f.Directory.FullName.TrimEnd("\")
                    $skillName = Split-Path -Leaf $dir
                    if ($dir -eq $extFull) { $skillName = $Name }
                    if ($done.ContainsKey($skillName)) {
                        Say "  이름이 겹쳐 건너뜀: $skillName ($($dir.Substring($extFull.Length).TrimStart('\')))"
                        continue
                    }
                    $done[$skillName] = $true
                    $target = Join-Path $skillsDir $skillName
                    Move-Aside $target $bakRoot $stamp
                    Copy-Item -LiteralPath $dir -Destination $target -Recurse -Force
                    Say "설치됨: $target"
                }
                Say ("  묶음 " + $Name + " 에서 스킬 " + $done.Count + "개를 설치했습니다.")
            }
        }
        else {
            if (-not (Test-Path -LiteralPath $commandsDir)) { New-Item -ItemType Directory -Path $commandsDir -Force | Out-Null }
            foreach ($f in (Get-ChildItem -LiteralPath $ext -File)) {
                $to = Join-Path $commandsDir $f.Name
                if (Test-Path -LiteralPath $to) {
                    $bakRoot = $commandsDir + "-backup"
                    if (-not (Test-Path -LiteralPath $bakRoot)) { New-Item -ItemType Directory -Path $bakRoot -Force | Out-Null }
                    $bak = Join-Path $bakRoot ($f.Name + "." + $stamp)
                    Copy-Item -LiteralPath $to -Destination $bak -Force
                    Say "  있던 파일은 남겨 둠: $bak"
                }
                Copy-Item -LiteralPath $f.FullName -Destination $to -Force
                Say "설치됨: $to"
            }
        }

        # 6. 따로 필요한 것 알림
        if ($needs -ne "-" -and $needs -ne "") { Say "  따로 필요: $needs" }
        return $true
    }
    catch {
        Warn "${Name}: 설치하지 못했습니다 - $($_.Exception.Message)"
        return $false
    }
}

$code = 0
$oldEncoding = $null
try {
    # 다른 프로그램이 출력을 받아 읽을 때 한글이 깨지지 않게 UTF-8 로 내보낸다(끝나면 되돌림)
    $oldEncoding = [Console]::OutputEncoding
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
}
catch { $oldEncoding = $null }

try {
    if ($BaseUrl -eq "") {
        Warn "사이트 주소가 없습니다. -Base <주소> 를 주거나 환경변수 DEPOT_BASE 를 설정하세요."
        $code = 1
    }
    else {
        New-Item -ItemType Directory -Path $script:WorkDir -Force | Out-Null
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $rows = Get-Rows "list.tsv"

        if ($Target -eq "" -or $Target -eq "list") {
            Show-List $rows
        }
        elseif ($Target.StartsWith("pack:")) {
            $packId = $Target.Substring(5)
            $names = $null
            foreach ($p in (Get-Rows "packs.tsv")) {
                if ($p[0] -eq $packId) { $names = $p[2] -split ","; break }
            }
            if ($null -eq $names) {
                Warn "묶음을 찾지 못했습니다: $packId (list 로 확인하세요)"
                $code = 1
            }
            else {
                $failed = @()
                foreach ($n in $names) {
                    $one = $n.Trim()
                    if ($one -eq "") { continue }
                    if (-not (Install-One $one $rows)) { $failed += $one }
                }
                if ($failed.Count -gt 0) {
                    Warn ("설치하지 못한 것: " + ($failed -join ", "))
                    $code = 1
                }
                else {
                    Say ("묶음 " + $packId + " 설치 끝: " + $names.Count + "개")
                }
            }
        }
        else {
            if (-not (Install-One $Target $rows)) { $code = 1 }
        }
    }
}
catch {
    Warn ("오류: " + $_.Exception.Message)
    $code = 1
}
finally {
    if (Test-Path -LiteralPath $script:WorkDir) { Remove-Item -LiteralPath $script:WorkDir -Recurse -Force -ErrorAction SilentlyContinue }
    if ($null -ne $oldEncoding) { try { [Console]::OutputEncoding = $oldEncoding } catch { } }
}
exit $code
