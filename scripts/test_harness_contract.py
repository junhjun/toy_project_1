import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import execute


def _phase(root: Path, *, steps: list[execute.StepData]) -> Path:
    phase_dir = root / "phases" / "0-example"
    phase_dir.mkdir(parents=True)
    (phase_dir / "index.json").write_text(
        json.dumps({"steps": steps}),
        encoding="utf-8",
    )
    return phase_dir


VALID_STEP = "# Step 0\n\n## Acceptance Criteria\n\n```bash\npython3 --version\n```\n"


def test_rejects_phase_path_outside_project(tmp_path: Path) -> None:
    with pytest.raises(execute.HarnessError, match="phase name"):
        execute.StepExecutor("../outside", root=tmp_path)


def test_check_reports_missing_step_file_without_running_codex(tmp_path: Path) -> None:
    _phase(tmp_path, steps=[{"step": 0, "name": "setup", "status": "pending"}])

    executor = execute.StepExecutor("0-example", root=tmp_path)

    with pytest.raises(execute.HarnessError, match="step0.md"):
        executor.check()


def test_codex_command_keeps_approvals_and_sandbox_enabled(tmp_path: Path) -> None:
    phase_dir = _phase(
        tmp_path,
        steps=[{"step": 0, "name": "setup", "status": "pending"}],
    )
    (phase_dir / "step0.md").write_text(VALID_STEP, encoding="utf-8")
    executor = execute.StepExecutor("0-example", root=tmp_path)

    command = executor.build_command("prompt")

    assert command[:3] == ["codex", "exec", "--json"]
    assert command[3:5] == ["--sandbox", "workspace-write"]
    assert "--dangerously-bypass-approvals-and-sandbox" not in command
    assert "--ephemeral" not in command


def test_rejects_symlinked_phase_outside_project(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    phases = tmp_path / "phases"
    phases.mkdir()
    (phases / "0-example").symlink_to(outside, target_is_directory=True)

    with pytest.raises(execute.HarnessError, match="outside"):
        execute.StepExecutor("0-example", root=tmp_path)


def test_rejects_symlinked_phases_directory_outside_project(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "project").mkdir()
    (tmp_path / "project" / "phases").symlink_to(outside, target_is_directory=True)

    with pytest.raises(execute.HarnessError, match="phases directory"):
        execute.StepExecutor("0-example", root=tmp_path / "project")


def test_rejects_non_positive_timeout(tmp_path: Path) -> None:
    with pytest.raises(execute.HarnessError, match="timeout"):
        execute.StepExecutor("0-example", root=tmp_path, timeout_seconds=0)
