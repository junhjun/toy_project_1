# Project rules

## Harness

- Python 3.9+와 Codex CLI를 사용한다.
- 계획된 자동 작업은 `python3 scripts/execute.py <phase> --check`로 먼저 검증한 뒤 실행한다.
- 각 step은 `phases/<phase>/stepN.md`의 Acceptance Criteria를 직접 실행한다.
- 상태와 한 줄 요약은 같은 phase의 `index.json`에 기록한다.
- 하네스는 브랜치 생성, commit, push를 대신하지 않는다.

## Browser work
- CRITICAL: 인증, 로그인 세션, 클릭·입력·탐색, 스크린샷, UI QA 등 브라우저 기반 작업은 반드시 `aside-browser` 스킬을 사용한다.
- CRITICAL: `aside-browser`를 사용할 수 없으면 다른 브라우저 도구로 우회하지 말고 작업을 `blocked` 처리한다.
- GitHub 저장소 생성·삭제·push 등 CLI/API로 가능한 작업은 브라우저 대신 `gh` CLI 또는 connector를 우선 사용한다.
- Aside 작업은 snapshot으로 상태를 확인하고, 조작 후 새 snapshot으로 결과를 검증한다.

## Development

- 새 동작은 실패 테스트를 먼저 확인하고 최소 구현으로 통과시킨다.
- 범위 밖 리팩터링과 새 의존성은 피한다.
- commit을 만들 때는 conventional commits 형식을 사용한다.

## Commands

```bash
python3 -m pytest -q scripts/test_execute.py scripts/test_harness_contract.py
PYTHONPYCACHEPREFIX=.cache/pycache python3 -m py_compile scripts/execute.py
python3 scripts/execute.py 0-example --check
python3 scripts/execute.py <phase>
```
