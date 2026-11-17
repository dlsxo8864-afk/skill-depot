#!/usr/bin/env bash
# 스킬 창고 설치 스크립트 (macOS·Linux, bash 3.2 이상)
#
# 사용 예
#   curl -fsSL <주소>/install.sh | bash -s -- <대상> --agent claude --base <주소>
#
# <대상>   list(목록 보기) | 스킬 이름 | pack:<묶음 id>
# --agent  claude(기본) | codex
# --dest   스킬들이 놓일 폴더를 직접 지정(그 아래 <이름>/ 으로 설치)
# --base   사이트 주소. 없으면 환경변수 DEPOT_BASE, 그다음 이 파일에 박힌 주소
#
# curl | bash 로 실행돼도 안전하도록 전부 함수 안에 두고 맨 끝에서 main 을 부른다.

set -euo pipefail

EMBEDDED_BASE="https://dlsxo8864-afk.github.io/skill-depot"

TARGET=""
AGENT="claude"
DEST=""
BASE_URL=""
TMP_DIR=""

say() { printf '%s\n' "$*"; }
warn() { printf '%s\n' "$*" >&2; }

human_size() {
  awk -v b="$1" 'BEGIN { if (b >= 1048576) printf "%.1fMB", b / 1048576; else if (b >= 1024) printf "%.0fKB", b / 1024; else printf "%dB", b }'
}

sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    warn "sha256sum 또는 shasum 이 필요합니다."
    return 1
  fi
}

zip_names() {
  if command -v unzip >/dev/null 2>&1; then
    unzip -Z1 "$1"
  elif command -v python3 >/dev/null 2>&1; then
    python3 -c 'import sys, zipfile; print("\n".join(zipfile.ZipFile(sys.argv[1]).namelist()))' "$1"
  elif command -v bsdtar >/dev/null 2>&1; then
    bsdtar -tf "$1"
  else
    warn "zip 을 다룰 도구가 없습니다. unzip, python3, bsdtar 중 하나를 설치하세요."
    return 1
  fi
}

unzip_to() {
  mkdir -p "$2"
  if command -v unzip >/dev/null 2>&1; then
    unzip -q -o "$1" -d "$2" </dev/null
  elif command -v python3 >/dev/null 2>&1; then
    python3 -m zipfile -e "$1" "$2" </dev/null
  elif command -v bsdtar >/dev/null 2>&1; then
    bsdtar -xf "$1" -C "$2" </dev/null
  else
    return 1
  fi
}

fetch() {
  curl -fsSL "$BASE_URL/$1" -o "$TMP_DIR/$1" || {
    warn "받지 못했습니다: $BASE_URL/$1"
    return 1
  }
}

# 있던 폴더를 옆의 백업 폴더로 옮긴다(지우지 않는다)
move_aside() {
  local target="$1" backup_root="$2" stamp="$3"
  [ -e "$target" ] || return 0
  mkdir -p "$backup_root" || return 1
  mv "$target" "$backup_root/$(basename "$target")-$stamp" || return 1
  say "  있던 폴더는 남겨 둠: $backup_root/$(basename "$target")-$stamp"
}

kind_name() {
  case "$1" in
    skill) printf '스킬' ;;
    command) printf '명령어' ;;
    bundle) printf '스킬 묶음' ;;
    external) printf '원본 설치' ;;
    builtin) printf '앱 기본' ;;
    *) printf '%s' "$1" ;;
  esac
}

show_list() {
  local name kind group zip_path sha bytes title needs how size pid ptitle items count
  say "받을 수 있는 것과 목록만 있는 것"
  while IFS=$'\t' read -r name kind group zip_path sha bytes title needs how || [ -n "${name:-}" ]; do
    [ -z "${name:-}" ] && continue
    size="-"
    [ "$zip_path" != "-" ] && size=$(human_size "$bytes")
    printf '  %-34s %s  %s  %s\n' "$name" "$(kind_name "$kind")" "$size" "$title"
  done < "$TMP_DIR/list.tsv"

  if fetch "packs.tsv" && [ -s "$TMP_DIR/packs.tsv" ]; then
    say ""
    say "묶음"
    while IFS=$'\t' read -r pid ptitle items || [ -n "${pid:-}" ]; do
      [ -z "${pid:-}" ] && continue
      count=$(printf '%s' "$items" | awk -F',' '{print NF}')
      printf '  %-34s %s (%s개)\n' "pack:$pid" "$ptitle" "$count"
    done < "$TMP_DIR/packs.tsv"
  fi
  say ""
  say "설치: 이 스크립트에 이름 또는 pack:<묶음 id> 를 넘깁니다."
}

install_one() {
  local want="$1"
  local name kind group zip_path sha bytes title needs how
  local found=0
  while IFS=$'\t' read -r name kind group zip_path sha bytes title needs how || [ -n "${name:-}" ]; do
    if [ "${name:-}" = "$want" ]; then
      found=1
      break
    fi
  done < "$TMP_DIR/list.tsv"
  if [ "$found" -eq 0 ]; then
    warn "찾지 못했습니다: $want (list 로 이름을 확인하세요)"
    return 1
  fi
  needs="${needs:--}"
  how="${how:--}"

  if [ "$kind" = "builtin" ]; then
    say "$want: Claude 앱에 들어 있어 받을 필요가 없습니다."
    return 0
  fi
  if [ "$kind" = "external" ]; then
    say "$want: 이 창고에는 파일이 없습니다. 원본에서 설치합니다(이 스크립트는 아래 명령을 실행하지 않습니다)."
    [ "$how" != "-" ] && say "  $how"
    return 0
  fi
  if [ "$kind" = "command" ] && [ "$AGENT" = "codex" ]; then
    say "$want: 명령어는 Claude Code 전용이라 건너뜁니다."
    return 0
  fi
  if [ "$kind" = "command" ] && [ -n "$DEST" ]; then
    say "$want: --dest 를 준 경우 명령어는 건너뜁니다."
    return 0
  fi

  local root="$HOME/.$AGENT"
  local skills_dir="$root/skills"
  [ -n "$DEST" ] && skills_dir="${DEST%/}"
  local commands_dir="$root/commands"

  # 1. 받기
  local zip="$TMP_DIR/$want.zip"
  curl -fsSL "$BASE_URL/$zip_path" -o "$zip" || {
    warn "$want: zip 을 받지 못했습니다. ($BASE_URL/$zip_path)"
    return 1
  }

  # 2. 해시 비교
  local got
  got=$(sha256_of "$zip") || return 1
  if [ "$got" != "$sha" ]; then
    rm -f "$zip"
    warn "$want: sha256 이 목록과 다릅니다. 설치하지 않습니다. (목록 $sha / 받은 것 $got)"
    return 1
  fi

  # 3. zip 안 경로 검사
  local names entry
  names=$(zip_names "$zip") || return 1
  while IFS= read -r entry; do
    case "$entry" in
      *..*|/*|\\*|[A-Za-z]:*)
        warn "$want: zip 안에 위험한 경로가 있습니다. 설치하지 않습니다. ($entry)"
        return 1
        ;;
    esac
  done <<LIST
$names
LIST

  # 4. 임시 폴더에 풀기
  local ext="$TMP_DIR/x-$want"
  rm -rf "$ext"
  unzip_to "$zip" "$ext" || {
    warn "$want: zip 을 풀지 못했습니다."
    return 1
  }
  local stamp
  stamp=$(date +%Y%m%d-%H%M%S)

  # 5. 있던 것은 옆 폴더에 남기고 설치.
  #    백업을 skills 폴더 안에 두면 같은 이름의 스킬이 둘로 읽히므로 <skills>-backup 에 둔다.
  if [ "$kind" = "skill" ]; then
    if [ ! -f "$ext/SKILL.md" ]; then
      warn "$want: zip 안에 SKILL.md 가 없습니다. 설치하지 않습니다."
      return 1
    fi
    mkdir -p "$skills_dir" || return 1
    move_aside "$skills_dir/$want" "${skills_dir}-backup" "$stamp" || return 1
    mv "$ext" "$skills_dir/$want" || return 1
    say "설치됨: $skills_dir/$want"
  elif [ "$kind" = "bundle" ]; then
    # 받은 묶음 안에서 SKILL.md 가 있는 폴더를 모두 스킬로 설치한다(얕은 폴더부터)
    mkdir -p "$skills_dir" || return 1
    local found one dir skill_name seen="|" count=0
    found=$(find "$ext" -type f -name SKILL.md -not -path "*/node_modules/*" | awk '{ print length($0) "\t" $0 }' | sort -n | cut -f2-)
    if [ -z "$found" ]; then
      mkdir -p "${skills_dir}-packs" || return 1
      move_aside "${skills_dir}-packs/$want" "${skills_dir}-backup" "$stamp" || return 1
      mv "$ext" "${skills_dir}-packs/$want" || return 1
      say "받음: ${skills_dir}-packs/$want"
      say "  스킬 형식(SKILL.md)이 아닙니다. 안의 README 를 읽고 따르세요."
    else
      while IFS= read -r one; do
        [ -z "$one" ] && continue
        dir=$(dirname "$one")
        skill_name=$(basename "$dir")
        [ "$dir" = "$ext" ] && skill_name="$want"
        case "$seen" in
          *"|$skill_name|"*)
            say "  이름이 겹쳐 건너뜀: $skill_name (${dir#"$ext"/})"
            continue
            ;;
        esac
        seen="$seen$skill_name|"
        move_aside "$skills_dir/$skill_name" "${skills_dir}-backup" "$stamp" || return 1
        cp -R "$dir" "$skills_dir/$skill_name" || return 1
        say "설치됨: $skills_dir/$skill_name"
        count=$((count + 1))
      done <<FOUND
$found
FOUND
      say "  묶음 $want 에서 스킬 ${count}개를 설치했습니다."
    fi
  else
    mkdir -p "$commands_dir" || return 1
    local f base to
    for f in "$ext"/*; do
      [ -f "$f" ] || continue
      base=$(basename "$f")
      to="$commands_dir/$base"
      if [ -e "$to" ]; then
        mkdir -p "${commands_dir}-backup" || return 1
        cp "$to" "${commands_dir}-backup/$base.$stamp" || return 1
        say "  있던 파일은 남겨 둠: ${commands_dir}-backup/$base.$stamp"
      fi
      cp "$f" "$to" || return 1
      say "설치됨: $to"
    done
  fi

  # 6. 따로 필요한 것 알림
  [ "$needs" != "-" ] && say "  따로 필요: $needs"
  return 0
}

main() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --agent|--dest|--base)
        if [ $# -lt 2 ]; then
          warn "$1 뒤에 값이 필요합니다."
          exit 1
        fi
        case "$1" in
          --agent) AGENT="$2" ;;
          --dest) DEST="$2" ;;
          --base) BASE_URL="$2" ;;
        esac
        shift 2
        ;;
      *)
        if [ -z "$TARGET" ]; then
          TARGET="$1"
          shift
        else
          warn "알 수 없는 인자입니다: $1"
          exit 1
        fi
        ;;
    esac
  done
  [ -z "$TARGET" ] && TARGET="list"

  if [ "$AGENT" != "claude" ] && [ "$AGENT" != "codex" ]; then
    warn "--agent 는 claude 또는 codex 입니다: $AGENT"
    exit 1
  fi

  # 사이트 주소: 인자 > 환경변수 > 박힌 주소(빌드 때 치환되지 않았으면 __ 로 시작한다)
  if [ -z "$BASE_URL" ]; then
    if [ -n "${DEPOT_BASE:-}" ]; then
      BASE_URL="$DEPOT_BASE"
    else
      case "$EMBEDDED_BASE" in
        ""|__*) ;;
        *) BASE_URL="$EMBEDDED_BASE" ;;
      esac
    fi
  fi
  BASE_URL="${BASE_URL%/}"
  if [ -z "$BASE_URL" ]; then
    warn "사이트 주소가 없습니다. --base <주소> 를 주거나 환경변수 DEPOT_BASE 를 설정하세요."
    exit 1
  fi

  command -v curl >/dev/null 2>&1 || {
    warn "curl 이 필요합니다."
    exit 1
  }

  TMP_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t depot)
  trap 'rm -rf "$TMP_DIR"' EXIT

  fetch "list.tsv" || exit 1

  case "$TARGET" in
    list)
      show_list
      ;;
    pack:*)
      local pack_id="${TARGET#pack:}"
      local pid ptitle items names="" failed="" n count=0
      fetch "packs.tsv" || exit 1
      while IFS=$'\t' read -r pid ptitle items || [ -n "${pid:-}" ]; do
        if [ "${pid:-}" = "$pack_id" ]; then
          names="$items"
          break
        fi
      done < "$TMP_DIR/packs.tsv"
      if [ -z "$names" ]; then
        warn "묶음을 찾지 못했습니다: $pack_id (list 로 확인하세요)"
        exit 1
      fi
      local old_ifs="$IFS"
      IFS=','
      set -- $names
      IFS="$old_ifs"
      for n in "$@"; do
        [ -z "$n" ] && continue
        count=$((count + 1))
        if ! install_one "$n"; then
          failed="${failed:+$failed, }$n"
        fi
      done
      if [ -n "$failed" ]; then
        warn "설치하지 못한 것: $failed"
        exit 1
      fi
      say "묶음 $pack_id 설치 끝: ${count}개"
      ;;
    *)
      install_one "$TARGET" || exit 1
      ;;
  esac
}

main "$@"
