"""CLI tests using Typer's CliRunner.

The CLI's `_store()` constructs `Store()` with the default root, so we
monkeypatch `store.DEFAULT_DIR` to point at `tmp_path` before each test.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from caregiver_os import cli as cli_module
from caregiver_os.cli import app
from caregiver_os.store import Store


@pytest.fixture
def runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    # cli._store() returns Store() with the default root. Default args
    # bind at function-definition time, so patching DEFAULT_DIR doesn't
    # help. Replace _store() itself with a tmp_path-bound factory.
    monkeypatch.setattr(cli_module, "_store", lambda: Store(root=tmp_path))
    return CliRunner()


def test_init_writes_recipient(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--care-recipient", "Maria"])
    assert result.exit_code == 0, result.output
    assert "Initialized" in result.output
    # File persisted
    assert (tmp_path / "recipient.json").exists()


def test_meds_add_adds_med(runner: CliRunner) -> None:
    runner.invoke(app, ["init", "--care-recipient", "Maria"])
    result = runner.invoke(
        app,
        ["meds", "add", "--name", "Atorvastatin", "--dose", "20mg", "--times", "09:00,21:00"],
    )
    assert result.exit_code == 0, result.output
    assert "Added: Atorvastatin" in result.output

    listed = runner.invoke(app, ["meds", "list"])
    assert "Atorvastatin" in listed.output


def test_today_shows_med(runner: CliRunner) -> None:
    runner.invoke(app, ["init", "--care-recipient", "Maria"])
    runner.invoke(
        app,
        ["meds", "add", "--name", "Atorvastatin", "--dose", "20mg", "--times", "09:00"],
    )
    result = runner.invoke(app, ["today"])
    assert result.exit_code == 0, result.output
    assert "Atorvastatin" in result.output
    assert "Recipient: Maria" in result.output


def test_handoff_lifecycle(runner: CliRunner) -> None:
    runner.invoke(app, ["init", "--care-recipient", "Maria"])
    start = runner.invoke(app, ["handoff", "start", "--caregiver", "Alice"])
    assert start.exit_code == 0, start.output
    assert "Started handoff" in start.output

    log = runner.invoke(app, ["handoff", "log", "--vitals", "BP 120/80"])
    assert log.exit_code == 0, log.output
    assert "Logged" in log.output

    end = runner.invoke(app, ["handoff", "end"])
    assert end.exit_code == 0, end.output
    assert "Closed handoff" in end.output

    # After end, today shows no open handoff
    today_out = runner.invoke(app, ["today"])
    assert "Open handoff: no" in today_out.output


def test_meds_add_before_init_errors(runner: CliRunner) -> None:
    result = runner.invoke(
        app,
        ["meds", "add", "--name", "X", "--dose", "1mg", "--times", "09:00"],
    )
    assert result.exit_code != 0
    # The error should mention recipient setup, surfaced via RuntimeError
    msg = (result.output or "") + (str(result.exception) if result.exception else "")
    assert "recipient" in msg.lower()


def test_handoff_log_without_open_errors(runner: CliRunner) -> None:
    runner.invoke(app, ["init", "--care-recipient", "Maria"])
    result = runner.invoke(app, ["handoff", "log", "--vitals", "BP 120/80"])
    assert result.exit_code == 1
    assert "No open handoff" in result.output
