#!/usr/bin/env python3

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Final, TypedDict

DEFAULT_ROOT: Final = Path(__file__).resolve().parent.parent
NAME_PATTERN: Final = re.compile(r"^[a-z0-9][a-z0-9-]*$")
VALID_STATUSES: Final = {"pending", "completed", "blocked", "error"}
ACCEPTANCE_PATTERN: Final = re.compile(
    r"(?ms)^## Acceptance Criteria[ \t]*$\n(?:[ \t]*\n)*"
    r"^```(?:bash|sh)[ \t]*$\n(?P<commands>.*?)^```[ \t]*$"
)


class StepData(TypedDict, total=False):
    step: int
    name: str
    status: str
    summary: str
    blocked_reason: str
    error_message: str
    started_at: str
    completed_at: str
    failed_at: str
    blocked_at: str


class PhaseIndex(TypedDict, total=False):
    steps: list[StepData]
    completed_at: str


class HarnessError(RuntimeError):
    pass


class StepExecutor:
    def __init__(
        self,
        phase_name: str,
        *,
        root: Path = DEFAULT_ROOT,
        timeout_seconds: int = 1800,
    ) -> None:
        if not NAME_PATTERN.fullmatch(phase_name):
            raise HarnessError("phase name must use lowercase letters, numbers, and hyphens")
        if timeout_seconds <= 0:
            raise HarnessError("timeout must be greater than zero")
        self.root = root.resolve()
        phases_dir = (self.root / "phases").resolve()
        try:
            phases_dir.relative_to(self.root)
        except ValueError as error:
            raise HarnessError("phases directory resolves outside the project") from error
        self.phase_dir = (phases_dir / phase_name).resolve()
        try:
            self.phase_dir.relative_to(phases_dir)
        except ValueError as error:
            raise HarnessError("phase path resolves outside the project") from error
        self.index_file = self.phase_dir / "index.json"
        self.timeout_seconds = timeout_seconds

    def _safe_path(self, path: Path) -> Path:
        resolved = path.resolve()
        try:
            resolved.relative_to(self.phase_dir)
        except ValueError as error:
            raise HarnessError(f"path resolves outside the phase: {path}") from error
        return resolved

    def _read_index(self) -> PhaseIndex:
        index_file = self._safe_path(self.index_file)
        if not index_file.is_file():
            raise HarnessError(f"missing phase index: {self.index_file}")
        try:
            value = json.loads(index_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise HarnessError(f"invalid JSON in {self.index_file}: {error.msg}") from error
        if not isinstance(value, dict):
            raise HarnessError("phase index must be a JSON object")
        return value

    def _write_index(self, index: PhaseIndex) -> None:
        index_file = self._safe_path(self.index_file)
        temporary = self._safe_path(index_file.with_suffix(".json.tmp"))
        temporary.write_text(
            json.dumps(index, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(index_file)

    def check(self) -> PhaseIndex:
        index = self._read_index()
        steps = index.get("steps")
        if not isinstance(steps, list) or not steps:
            raise HarnessError("steps must be a non-empty array")
        for position, step in enumerate(steps):
            if not isinstance(step, dict):
                raise HarnessError(f"step {position} must be a JSON object")
            if step.get("step") != position:
                raise HarnessError("step numbers must be contiguous and start at 0")
            name = step.get("name")
            if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
                raise HarnessError(f"step {position} name must be lowercase kebab-case")
            if step.get("status") not in VALID_STATUSES:
                raise HarnessError(f"step {position} has an invalid status")
            status = step["status"]
            summary = step.get("summary")
            blocked_reason = step.get("blocked_reason")
            error_message = step.get("error_message")
            if status == "completed" and (not isinstance(summary, str) or not summary.strip()):
                raise HarnessError(f"step {position} completed without a summary")
            if status == "blocked" and (
                not isinstance(blocked_reason, str) or not blocked_reason.strip()
            ):
                raise HarnessError(f"step {position} blocked without a reason")
            if status == "error" and (
                not isinstance(error_message, str) or not error_message.strip()
            ):
                raise HarnessError(f"step {position} failed without an error message")
            step_file = self.phase_dir / f"step{position}.md"
            safe_step_file = self._safe_path(step_file)
            if not safe_step_file.is_file():
                raise HarnessError(f"missing step file: {step_file}")
            instructions = safe_step_file.read_text(encoding="utf-8")
            command = ACCEPTANCE_PATTERN.search(instructions)
            if command is None or not command.group("commands").strip():
                raise HarnessError(f"step {position} needs an Acceptance Criteria command")
        return index

    def build_command(self, prompt: str) -> list[str]:
        return [
            "codex", "exec", "--json", "--sandbox", "workspace-write",
            "--cd", str(self.root), prompt,
        ]

    def _build_prompt(self, index: PhaseIndex, step: StepData) -> str:
        rules_file = self.root / "AGENTS.md"
        rules = rules_file.read_text(encoding="utf-8") if rules_file.is_file() else ""
        step_number = step["step"]
        step_file = self._safe_path(self.phase_dir / f"step{step_number}.md")
        instructions = step_file.read_text(encoding="utf-8")
        return (
            f"# 프로젝트 규칙\n\n{rules}\n\n"
            f"# 현재 단계\n\n{instructions}\n\n"
            "# 완료 계약\n\n"
            "Acceptance Criteria를 직접 실행하라. 성공하면 현재 step의 status를 "
            '"completed"로 바꾸고 summary를 기록하라. 사용자 개입이 필요하면 '
            '"blocked"와 blocked_reason을 기록하라. 실패하면 "error"와 '
            "error_message를 기록하라. 다른 step의 상태는 수정하지 마라."
        )

    def _stamp(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _record_error(self, index: PhaseIndex, step_number: int, message: str) -> None:
        step = index["steps"][step_number]
        step["status"] = "error"
        step["error_message"] = message
        step["failed_at"] = self._stamp()
        self._write_index(index)

    def _run_step(self, index: PhaseIndex, step: StepData) -> None:
        step_number = step["step"]
        step["started_at"] = self._stamp()
        self._write_index(index)
        try:
            result = subprocess.run(
                self.build_command(self._build_prompt(index, step)),
                cwd=self.root,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            message = f"Codex timed out after {self.timeout_seconds} seconds"
            self._record_error(index, step_number, message)
            raise HarnessError(message) from error
        except FileNotFoundError as error:
            message = "Codex CLI executable was not found"
            self._record_error(index, step_number, message)
            raise HarnessError(message) from error
        except OSError as error:
            message = f"Codex CLI could not start: {error}"
            self._record_error(index, step_number, message)
            raise HarnessError(message) from error
        try:
            current = self.check()
        except HarnessError as error:
            message = f"Codex wrote invalid phase state: {error}"
            self._record_error(index, step_number, message)
            raise HarnessError(message) from error
        changed_other_step = len(current["steps"]) != len(index["steps"]) or any(
            current_item.get("name") != original.get("name")
            or (
                position != step_number
                and current_item != original
            )
            for position, (original, current_item) in enumerate(
                zip(index["steps"], current["steps"])
            )
        )
        if changed_other_step:
            message = "Codex changed another step or a step identity"
            restored = index
            self._record_error(restored, step_number, message)
            raise HarnessError(message)
        current_step = current["steps"][step_number]
        status = current_step["status"]
        if result.returncode != 0:
            message = f"Codex exited with code {result.returncode}"
            self._record_error(current, step_number, message)
            raise HarnessError(message)
        if status == "pending":
            message = f"step {step_number} finished without updating its status"
            self._record_error(current, step_number, message)
            raise HarnessError(message)
        if status == "blocked":
            current_step["blocked_at"] = self._stamp()
            self._write_index(current)
            reason = current_step.get("blocked_reason", "unknown")
            raise HarnessError(f"step {step_number} blocked: {reason}")
        if status == "error":
            current_step["failed_at"] = self._stamp()
            self._write_index(current)
            message = current_step.get("error_message", "unknown")
            raise HarnessError(f"step {step_number} failed: {message}")
        current_step["completed_at"] = self._stamp()
        self._write_index(current)

    def run(self) -> None:
        while True:
            index = self.check()
            blocking = next(
                (step for step in index["steps"] if step["status"] in {"blocked", "error"}),
                None,
            )
            if blocking is not None:
                status = blocking["status"]
                raise HarnessError(f"reset step {blocking['step']} to pending after resolving {status}")
            step = next((item for item in index["steps"] if item["status"] == "pending"), None)
            if step is None:
                break
            self._run_step(index, step)
        index["completed_at"] = self._stamp()
        self._write_index(index)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Codex phase from phases/<name>")
    parser.add_argument("phase", help="phase directory name")
    parser.add_argument("--check", action="store_true", help="validate files without running Codex")
    parser.add_argument("--timeout", type=int, default=1800, help="seconds allowed per step")
    args = parser.parse_args()
    try:
        executor = StepExecutor(args.phase, timeout_seconds=args.timeout)
        executor.check() if args.check else executor.run()
    except HarnessError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    message = f"Phase '{args.phase}' is valid." if args.check else f"Phase '{args.phase}' completed."
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
