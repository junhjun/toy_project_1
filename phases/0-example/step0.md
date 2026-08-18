# Step 0: verify the harness

## Goal

하네스 자체의 테스트와 문법 검사를 실행해 기본 상태를 확인한다.

## Read first

- `AGENTS.md`
- `docs/PRD.md`
- `scripts/execute.py`
- `scripts/test_execute.py`

## Work

코드를 변경하지 말고 아래 검증 명령만 실행한다.

## Acceptance Criteria

```bash
python3 -m pytest -q scripts/test_execute.py scripts/test_harness_contract.py
PYTHONPYCACHEPREFIX=.cache/pycache python3 -m py_compile scripts/execute.py
```
