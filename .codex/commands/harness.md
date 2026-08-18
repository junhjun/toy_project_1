이 프로젝트의 Codex 하네스를 사용해 작업 phase를 준비하라.

1. `AGENTS.md`와 필요한 `docs/*.md`만 읽는다.
2. 구현 전에 사용자와 목표, 제외 범위, 확인 방법을 합의한다.
3. `phases/<phase>/index.json`과 독립 실행 가능한 `stepN.md`를 만든다.
4. 각 step은 한 가지 관찰 가능한 결과와 실행 가능한 Acceptance Criteria를 가진다.
5. `python3 scripts/execute.py <phase> --check`가 통과하는지 확인한다.
6. 승인된 경우에만 `python3 scripts/execute.py <phase>`를 실행한다.

`index.json`에는 실행에 필요한 step만 기록한다:

```json
{
  "steps": [
    {"step": 0, "name": "project-setup", "status": "pending"}
  ]
}
```

상태는 `pending`, `completed`, `blocked`, `error` 중 하나다. 완료 시 `summary`, 차단 시
`blocked_reason`, 실패 시 `error_message`를 기록한다. 브랜치, commit, push는 하네스가
자동화하지 않는다.
