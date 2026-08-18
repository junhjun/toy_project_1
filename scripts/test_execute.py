import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import execute


@pytest.fixture
def phase_root(tmp_path: Path) -> Path:
    phase_dir = tmp_path / "phases" / "0-example"
    phase_dir.mkdir(parents=True)
    (tmp_path / "AGENTS.md").write_text("# Rules\n\n- Keep scope small.\n", encoding="utf-8")
    index = {
        "steps": [{"step": 0, "name": "setup", "status": "pending"}],
    }
    (phase_dir / "index.json").write_text(json.dumps(index), encoding="utf-8")
    (phase_dir / "step0.md").write_text(
        "# Step 0\n\n## Acceptance Criteria\n\n```bash\npython3 --version\n```\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"steps": []}, "steps"),
    ],
)
def test_check_rejects_invalid_index(phase_root: Path, change: dict, message: str) -> None:
    index_file = phase_root / "phases" / "0-example" / "index.json"
    index = json.loads(index_file.read_text(encoding="utf-8"))
    index.update(change)
    index_file.write_text(json.dumps(index), encoding="utf-8")

    with pytest.raises(execute.HarnessError, match=message):
        execute.StepExecutor("0-example", root=phase_root).check()


def test_check_accepts_minimal_index_with_only_steps(phase_root: Path) -> None:
    index = execute.StepExecutor("0-example", root=phase_root).check()

    assert set(index) == {"steps"}


def test_run_records_completed_step(phase_root: Path) -> None:
    executor = execute.StepExecutor("0-example", root=phase_root)

    def complete_step(*args, **kwargs):
        index = executor._read_index()
        index["steps"][0].update({"status": "completed", "summary": "created app"})
        executor._write_index(index)
        return subprocess.CompletedProcess(args[0], 0, '{"type":"turn.completed"}\n', "")

    with patch("subprocess.run", side_effect=complete_step):
        executor.run()

    index = executor._read_index()
    assert index["steps"][0]["status"] == "completed"
    assert "completed_at" in index["steps"][0]
    assert "completed_at" in index


def test_run_streams_codex_output_without_capturing(phase_root: Path) -> None:
    executor = execute.StepExecutor("0-example", root=phase_root)

    def complete_step(*args, **kwargs):
        index = executor._read_index()
        index["steps"][0].update({"status": "completed", "summary": "done"})
        executor._write_index(index)
        return subprocess.CompletedProcess(args[0], 0)

    with patch("subprocess.run", side_effect=complete_step) as run:
        executor.run()

    assert "capture_output" not in run.call_args.kwargs
    assert "stdout" not in run.call_args.kwargs
    assert "stderr" not in run.call_args.kwargs


def test_run_stops_on_codex_failure(phase_root: Path) -> None:
    executor = execute.StepExecutor("0-example", root=phase_root)
    failed = subprocess.CompletedProcess(["codex"], 7, "", "failed")

    with patch("subprocess.run", return_value=failed):
        with pytest.raises(execute.HarnessError, match="code 7"):
            executor.run()

    assert executor._read_index()["steps"][0]["status"] == "error"


def test_run_rejects_nonzero_exit_even_if_step_claims_completion(phase_root: Path) -> None:
    executor = execute.StepExecutor("0-example", root=phase_root)

    def claim_completion(*args, **kwargs):
        index = executor._read_index()
        index["steps"][0].update({"status": "completed", "summary": "not trustworthy"})
        executor._write_index(index)
        return subprocess.CompletedProcess(args[0], 7, "", "failed")

    with patch("subprocess.run", side_effect=claim_completion):
        with pytest.raises(execute.HarnessError, match="code 7"):
            executor.run()

    assert executor._read_index()["steps"][0]["status"] == "error"


def test_check_rejects_missing_acceptance_command(phase_root: Path) -> None:
    step_file = phase_root / "phases" / "0-example" / "step0.md"
    step_file.write_text("# Step 0\n\n## Acceptance Criteria\n", encoding="utf-8")

    with pytest.raises(execute.HarnessError, match="Acceptance Criteria"):
        execute.StepExecutor("0-example", root=phase_root).check()


def test_check_does_not_take_command_from_later_section(phase_root: Path) -> None:
    step_file = phase_root / "phases" / "0-example" / "step0.md"
    step_file.write_text(
        "# Step 0\n\n## Acceptance Criteria\n\n## Notes\n\n```bash\npython3 --version\n```\n",
        encoding="utf-8",
    )

    with pytest.raises(execute.HarnessError, match="Acceptance Criteria"):
        execute.StepExecutor("0-example", root=phase_root).check()


def test_check_does_not_take_command_from_later_subheading(phase_root: Path) -> None:
    step_file = phase_root / "phases" / "0-example" / "step0.md"
    step_file.write_text(
        "# Step 0\n\n## Acceptance Criteria\n\n### Notes\n\n```bash\npython3 --version\n```\n",
        encoding="utf-8",
    )

    with pytest.raises(execute.HarnessError, match="Acceptance Criteria"):
        execute.StepExecutor("0-example", root=phase_root).check()


def test_check_accepts_shell_comment_in_acceptance_command(phase_root: Path) -> None:
    step_file = phase_root / "phases" / "0-example" / "step0.md"
    step_file.write_text(
        "# Step 0\n\n## Acceptance Criteria\n\n```bash\n# explain\npython3 --version\n```\n",
        encoding="utf-8",
    )

    execute.StepExecutor("0-example", root=phase_root).check()


def test_check_rejects_completed_step_without_summary(phase_root: Path) -> None:
    executor = execute.StepExecutor("0-example", root=phase_root)
    index = executor._read_index()
    index["steps"][0]["status"] = "completed"
    executor._write_index(index)

    with pytest.raises(execute.HarnessError, match="summary"):
        executor.check()


def test_run_records_error_when_codex_does_not_update_status(phase_root: Path) -> None:
    executor = execute.StepExecutor("0-example", root=phase_root)
    unchanged = subprocess.CompletedProcess(["codex"], 0, "{}\n", "")

    with patch("subprocess.run", return_value=unchanged):
        with pytest.raises(execute.HarnessError, match="without updating"):
            executor.run()

    assert executor._read_index()["steps"][0]["status"] == "error"


def test_run_records_error_when_codex_is_missing(phase_root: Path) -> None:
    executor = execute.StepExecutor("0-example", root=phase_root)

    with patch("subprocess.run", side_effect=FileNotFoundError("codex")):
        with pytest.raises(execute.HarnessError, match="not found"):
            executor.run()

    assert executor._read_index()["steps"][0]["status"] == "error"


def test_run_records_error_when_codex_cannot_start(phase_root: Path) -> None:
    executor = execute.StepExecutor("0-example", root=phase_root)

    with patch("subprocess.run", side_effect=PermissionError("denied")):
        with pytest.raises(execute.HarnessError, match="could not start"):
            executor.run()

    assert executor._read_index()["steps"][0]["status"] == "error"


def test_run_records_start_time_for_every_step(phase_root: Path) -> None:
    executor = execute.StepExecutor("0-example", root=phase_root)
    index = executor._read_index()
    index["steps"].append({"step": 1, "name": "finish", "status": "pending"})
    executor._write_index(index)
    (executor.phase_dir / "step1.md").write_text(
        "# Step 1\n\n## Acceptance Criteria\n\n```bash\npython3 --version\n```\n",
        encoding="utf-8",
    )

    def complete_current_step(*args, **kwargs):
        current = executor._read_index()
        pending = next(step for step in current["steps"] if step["status"] == "pending")
        pending.update({"status": "completed", "summary": "done"})
        executor._write_index(current)
        return subprocess.CompletedProcess(args[0], 0, "{}\n", "")

    with patch("subprocess.run", side_effect=complete_current_step):
        executor.run()

    assert all("started_at" in step for step in executor._read_index()["steps"])


def test_run_rejects_changes_to_future_step_status(phase_root: Path) -> None:
    executor = execute.StepExecutor("0-example", root=phase_root)
    index = executor._read_index()
    index["steps"].append({"step": 1, "name": "finish", "status": "pending"})
    executor._write_index(index)
    (executor.phase_dir / "step1.md").write_text(
        "# Step 1\n\n## Acceptance Criteria\n\n```bash\npython3 --version\n```\n",
        encoding="utf-8",
    )

    def change_both_steps(*args, **kwargs):
        current = executor._read_index()
        current["steps"][0].update({"status": "completed", "summary": "claimed"})
        current["steps"][1]["summary"] = "unauthorized change"
        executor._write_index(current)
        return subprocess.CompletedProcess(args[0], 0)

    with patch("subprocess.run", side_effect=change_both_steps):
        with pytest.raises(execute.HarnessError, match="other step"):
            executor.run()

    assert executor._read_index()["steps"][1]["status"] == "pending"
