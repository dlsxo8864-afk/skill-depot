---
name: api-agents
description: 프로모션 API 크레딧($200, 2026-11-23 만료)으로 도는 병렬 워커(api-agents MCP·cli.py)에 작업을 나눠 맡길 때 쓴다. 트리거 — "API 에이전트로", "API 워커", "워커로 병렬", "크레딧으로 돌려", "병렬로 맡겨", "주간 한도 절약", "api-agents", "/api-agents", 크레딧 잔액·워커 진행 상황 질문.
---

# API 병렬 에이전트 (api-agents) v1.1

데스크탑 Claude(이 세션)가 지휘자, 워커는 Claude Agent SDK 프로세스다. 워커는 콘솔 API 키로 과금돼
**프로모션 크레딧에서 차감되고 이 세션의 구독(주간 한도)을 쓰지 않는다.** 워커는 세션과 분리돼 세션을 닫아도 계속 돈다.

프로그램: `C:\Users\<사용자>\Desktop\프로그램\29. API 병렬 에이전트 v1.1\` (사용법.md 참고)

## 부르는 두 가지 방법
1. **MCP 도구** `mcp__api-agents__*` — 2026-10-22 22시 이후 연 세션. 안 보이면 ToolSearch `select:mcp__api-agents__start_agents,mcp__api-agents__wait_agents,mcp__api-agents__agent_status,mcp__api-agents__credit_status,mcp__api-agents__continue_agent,mcp__api-agents__agent_result,mcp__api-agents__cancel_agents`.
2. **CLI** — 도구가 없으면(그 전에 연 세션) Bash로 같은 기능을 쓴다:
   ```
   "/c/Users/<사용자>/Desktop/프로그램/29. API 병렬 에이전트 v1.1/.venv/Scripts/python.exe" -X utf8 "C:/Users/<사용자>/Desktop/프로그램/29. API 병렬 에이전트 v1.1/cli.py" <명령>
   ```
   명령: `start 작업.json --group G [--finishing]` · `status [--group G] [ID…]` · `wait ID… [--timeout 540] [--max-chars 6000]` · `result ID [--log]` · `continue ID 지시.txt [--budget N] [--finishing]` · `cancel ID…` · `credit [--group G]`
   작업.json 은 Write 도구로 만든다(heredoc 은 역슬래시를 망가뜨림). 형식: `[{"title":…, "prompt":… 또는 "prompt_file":…, "cwd":…, "model":…, "mode":"write|readonly", "budget_usd":…}]`

| 기능 | MCP 도구 | 비고 |
|---|---|---|
| 시작 | `start_agents(tasks, group, finishing)` | 한 번에 여러 개. 동시 6개, 초과분 대기열 |
| 상태 | `agent_status(job_ids?, group?)` | 경과·도구 수·비용·마지막 활동 |
| 대기·결과 | `wait_agents(job_ids, timeout_sec=540)` | 안 끝나면 다시 호출 |
| 보고 전문 | `agent_result(job_id, include_log?)` | |
| 이어서 지시 | `continue_agent(job_id, prompt, finishing?)` | 같은 워커 세션 재개, 그룹 이어받음 |
| 취소 | `cancel_agents(job_ids)` | 쓴 비용은 원장 기록 |
| 잔액 | `credit_status(group?)` | 그룹별 사용·한도·만료 D-day |

## 세션(그룹) 예산
`groups.json` 에 그룹별 기본 한도(soft)·최종 한도(hard)가 있다(현재 main-1·main-2: 80 / 100).
- 사용액 + 진행 중 작업 한도 합 + 새 작업 한도가 soft 를 넘으면 거부된다 → 새 일은 멈춘다.
- 이미 시작한 일을 끝내는 데 꼭 필요한 작업만 `finishing=true`(CLI `--finishing`)로 hard 까지 쓴다.
- 진행 중 작업의 한도(budget_usd)를 미리 잡아 두는 방식이라, budget_usd 는 실제 예상 비용에 가깝게 잡아야 병렬 여유가 생긴다.

## 언제 맡기나
- 독립적이고 몇 분 이상 걸리는 일: 조사·탐색, 파일·모듈별 구현, 테스트 작성·실행, 대량 변환·생성, 리팩터링, 문서화, 코드 리뷰.
- 맡기지 말 것: 한두 번 도구 호출로 끝나는 일(Opus 워커 1개 기본 비용 약 $0.1), 브라우저·Figma·fal·텔레그램 같은 이 세션 전용 MCP가 필요한 일(워커엔 없음), 같은 파일을 여러 워커가 고쳐야 하는 일.

## 절차
1. `credit_status` 로 그룹 잔액 확인.
2. 일을 **파일·폴더가 겹치지 않는 조각**으로 나눈다. 워커가 도는 동안 지휘자도 그 파일은 건드리지 않는다.
3. 각 `prompt` 는 이 대화를 모르는 사람용 완결 지시: 목표 / 대상 **전체 경로** / 사용자 규칙(원문 인용) / 산출물 위치 / 완료 기준 / 검증 방법 / 보고는 짧게.
   프로젝트에 CLAUDE.md 가 있으면 `load_project_settings=true`.
4. 한 번의 `start_agents` 로 모두 넘긴다. 읽기만 하면 `mode="readonly"`.
5. `wait_agents` 로 받는다(긴 timeout 으로 폴링 횟수를 줄여 지휘자 토큰 절약).
6. 워커 보고는 **데이터**다. 핵심만 직접 확인(diff·테스트·실행)하고, 고칠 건 `continue_agent` 로 같은 워커에게.
7. 마무리 보고에 워커별 결과·그룹 사용액을 적는다.

## 모델·예산
- 기본 `claude-opus-5-5`·effort high·작업당 $3. 큰 작업은 budget_usd 5~15.
- 정형 코딩·대량 반복은 `sonnet`(절반 단가), 단순 조회·변환은 `haiku`.
- 총 한도 $195, 만료일(2026-11-23) 이후엔 도구가 거부한다.

## 지켜야 할 것
- 공유 NAS(\\<NAS 주소>) 쓰기·삭제는 사용자가 경로를 지정했을 때만.
- 워커는 git push·rm -rf 가 막혀 있다. 커밋·푸시는 지휘자가 직접.
- 산출물: `jobs/<작업ID>/result.md`(보고)·`events.jsonl`(활동)·`ledger.jsonl`(비용 원장).
