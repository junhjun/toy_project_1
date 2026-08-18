# 프로젝트: Toy Project 1

## 기술 스택
- Python 3.9+
- Codex CLI (`codex exec`)
- JSON phase/step metadata

## 아키텍처 규칙
- CRITICAL: Codex 단계는 `python3 scripts/execute.py <phase-dir>`를 통해 실행한다.
- CRITICAL: 단계 상태는 해당 phase의 `index.json`에 기록하고, 산출물과 함께 검증한다.
- 문서 규칙은 `docs/*.md`, 프로젝트 규칙은 이 파일에서 관리한다.

## 브라우저 작업 정책
- CRITICAL: 인증, 로그인 세션, 클릭·입력·탐색, 스크린샷, UI QA 등 브라우저 기반 작업은 반드시 `aside-browser` 스킬을 사용한다.
- CRITICAL: `aside-browser`를 사용할 수 없으면 다른 브라우저 도구로 우회하지 말고 작업을 `blocked` 처리한다.
- GitHub 저장소 생성·삭제·push 등 CLI/API로 가능한 작업은 브라우저 대신 `gh` CLI 또는 connector를 우선 사용한다.
- Aside 작업은 snapshot으로 상태를 확인하고, 조작 후 새 snapshot으로 결과를 검증한다.

## 개발 프로세스
- CRITICAL: 새 기능 구현 시 반드시 테스트를 먼저 작성하고, 테스트가 통과하는 구현을 작성할 것 (TDD)
- Codex 호출은 `codex exec --json --cd <project-root>` 형식을 사용한다.
- 커밋 메시지는 conventional commits 형식을 따를 것 (feat:, fix:, docs:, refactor:)

## 명령어
python3 -m pytest -q scripts/test_execute.py  # 실행기 테스트
python3 -m py_compile scripts/execute.py       # 문법 검사
python3 scripts/execute.py <phase-dir>         # phase 실행
