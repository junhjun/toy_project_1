# Codex 프로젝트 하네스

이 도구는 앱 자체가 아니라, 작은 프로젝트를 만들 때 반복해서 쓰는 **작업 실행 틀**이다.

쉽게 말하면 다음 일을 한다.

1. 할 일을 작은 step으로 나눈다.
2. 각 step을 새 `codex exec` 세션에 순서대로 맡긴다.
3. 성공·실패·차단 상태와 실행 결과를 파일로 남긴다.

특정 언어나 프레임워크를 강제하지 않는다. Python 앱, 웹 앱, 실험 프로젝트 등에서
같은 구조를 재사용할 수 있다.

## 알아야 할 파일은 세 종류뿐이다

| 위치 | 역할 | 언제 수정하나 |
|---|---|---|
| `AGENTS.md` | 모든 작업이 지켜야 할 프로젝트 규칙 | 프로젝트 시작 시 |
| `docs/PRD.md` | 무엇을 만들고 무엇은 만들지 않을지 | 프로젝트 시작 시 |
| `phases/<이름>/` | 이번에 실행할 작업 목록과 상세 지시 | 기능이나 작업을 시작할 때마다 |

`docs/ARCHITECTURE.md`, `ADR.md`, `UI_GUIDE.md`는 필요할 때만 작성한다. 작은 CLI처럼
해당 문서가 필요 없는 프로젝트에서는 비워 둬도 된다.

## 처음 사용하는 순서

### 1. 프로젝트 방향 적기

먼저 `docs/PRD.md`에서 다음 네 가지만 채운다.

- 해결할 문제
- 주 사용자
- 이번 MVP에서 만들 것
- 이번에는 만들지 않을 것

### 2. 예제 phase 복사하기

프로젝트 루트에서 실행한다.

```bash
cp -R phases/0-example phases/0-mvp
```

`0-mvp`는 원하는 이름으로 바꿔도 된다. 이름에는 소문자, 숫자, 하이픈만 쓴다.

### 3. 작업 목록 적기

`phases/0-mvp/index.json`을 만들 때는 순서와 초기 상태만 적는다. 실행 후에는 하네스가
요약, 사유, 타임스탬프를 같은 파일에 추가한다.

```json
{
  "steps": [
    {"step": 0, "name": "project-setup", "status": "pending"},
    {"step": 1, "name": "core-feature", "status": "pending"}
  ]
}
```

각 항목과 같은 번호의 파일을 만든다.

- step 0 → `step0.md`
- step 1 → `step1.md`

각 step 파일에는 아래 네 가지만 적으면 된다.

````markdown
# Step 0: project setup

## Goal
완료 후 사용자가 확인할 수 있는 결과 한 가지

## Read first
- 먼저 읽어야 할 실제 파일

## Work
- 이번 step에서 할 일
- 이번 step에서 하지 않을 일

## Acceptance Criteria
```bash
python3 -m pytest -q
```
````

### 4. 실행 전 검사하기

```bash
python3 scripts/execute.py 0-mvp --check
```

이 명령은 Codex를 실행하지 않는다. JSON 형식, step 번호, 파일 누락, 경로 안전성,
Acceptance Criteria의 실행 명령 존재 여부를 검사한다. 문제가 있으면 exit code 1과 이유를 출력한다.

### 5. 실행하기

```bash
python3 scripts/execute.py 0-mvp
```

실행기는 첫 번째 `pending` step부터 시작한다. Codex는 Acceptance Criteria를 직접 실행하고
`index.json`에 결과를 기록한다. 성공한 step이 있으면 다음 step으로 넘어간다.

## 실행 후 생기는 것

각 step의 상태는 다음 중 하나다.

| 상태 | 의미 | 추가 필드 |
|---|---|---|
| `pending` | 아직 실행하지 않음 | 없음 |
| `completed` | 검증까지 성공 | `summary`, `completed_at` |
| `blocked` | 비밀키·로그인 등 사용자 작업 필요 | `blocked_reason`, `blocked_at` |
| `error` | 실행 또는 검증 실패 | `error_message`, `failed_at` |

Codex의 진행 출력은 터미널에 실시간으로 표시된다. 상태와 핵심 결과는 `index.json`에 남는다.

## 실패하거나 멈췄을 때

1. `index.json`의 `error_message` 또는 `blocked_reason`을 읽는다.
2. 원인을 해결한다.
3. 해당 step의 `status`를 `pending`으로 되돌린다.
4. 같은 실행 명령을 다시 입력한다.

이미 `completed`인 step은 건너뛰고 이어서 실행한다.

## 하네스 자체 점검

`0-example`은 하네스가 정상인지 확인하는 실제 예제다.

```bash
python3 scripts/execute.py 0-example --check
python3 -m pytest -q scripts/test_execute.py scripts/test_harness_contract.py
PYTHONPYCACHEPREFIX=.cache/pycache python3 -m py_compile scripts/execute.py
```

## 의도적으로 자동화하지 않는 것

- 브랜치 생성
- commit
- push
- 승인과 샌드박스 우회

이 작업들은 사용자 변경을 함께 묶거나 외부 저장소를 바꿀 수 있어 실행기 밖에 둔다.
Codex 실행은 명시적으로 `workspace-write` 샌드박스를 사용한다.
