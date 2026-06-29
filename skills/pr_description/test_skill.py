import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest
from typer.testing import CliRunner
import typer

import skill
from skill import _build_description, _git, run

app = typer.Typer()
app.command()(run)

runner = CliRunner()


# ---------------------------------------------------------------------------
# _build_description
# ---------------------------------------------------------------------------

class TestBuildDescription:
    def test_happy_path(self):
        commits = "Add feature X\nFix bug Y"
        stat = " file1.py | 10 +++++\n file2.py |  5 ---"
        result = _build_description(commits, stat)

        assert "## Resumo\n" in result
        assert "- Add feature X" in result
        assert "- Fix bug Y" in result
        assert "## Arquivos alterados\n" in result
        assert "- file1.py | 10 +++++" in result
        assert "- file2.py |  5 ---" in result

    def test_empty_commits_uses_placeholder(self):
        result = _build_description("", "file.py | 1 +")
        assert "- (sem commits novos)" in result

    def test_empty_stat_uses_placeholder(self):
        result = _build_description("My commit", "")
        assert "- (sem arquivos alterados)" in result

    def test_both_empty_uses_placeholders(self):
        result = _build_description("", "")
        assert "- (sem commits novos)" in result
        assert "- (sem arquivos alterados)" in result

    def test_whitespace_only_commits_uses_placeholder(self):
        result = _build_description("   \n  \n", "file.py | 2 +")
        assert "- (sem commits novos)" in result

    def test_whitespace_only_stat_uses_placeholder(self):
        result = _build_description("Some commit", "   \n  ")
        assert "- (sem arquivos alterados)" in result

    def test_output_structure(self):
        result = _build_description("Commit A", "fileA.py | 3 +++")
        assert result.startswith("## Resumo\n")
        assert "## Arquivos alterados\n" in result

    def test_single_commit_single_file(self):
        result = _build_description("Initial commit", "README.md | 1 +")
        assert "- Initial commit" in result
        assert "- README.md | 1 +" in result

    def test_strips_extra_whitespace_from_stat_lines(self):
        result = _build_description("commit", "   file.py | 1 +   ")
        assert "- file.py | 1 +" in result


# ---------------------------------------------------------------------------
# _git
# ---------------------------------------------------------------------------

class TestGitHelper:
    def test_returns_stdout_on_success(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "some output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            output = _git(["log", "--oneline"])

        assert output == "some output"

    def test_raises_exit_on_nonzero_returncode(self):
        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_result.stdout = ""
        mock_result.stderr = "fatal: not a git repository"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(typer.Exit):
                _git(["log"])

    def test_echoes_stderr_on_failure(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"

        with patch("subprocess.run", return_value=mock_result), \
             patch("typer.echo") as mock_echo:
            with pytest.raises(typer.Exit):
                _git(["status"])

            mock_echo.assert_called_once_with("error message", err=True)

    def test_passes_git_prefix_to_subprocess(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            _git(["diff", "--stat"])

        args_used = mock_run.call_args[0][0]
        assert args_used[0] == "git"
        assert "diff" in args_used
        assert "--stat" in args_used

    def test_called_with_capture_output_and_text(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            _git(["log"])

        _, kwargs = mock_run.call_args
        assert kwargs.get("capture_output") is True
        assert kwargs.get("text") is True


# ---------------------------------------------------------------------------
# run (via CLI)
# ---------------------------------------------------------------------------

class TestRunCommand:
    def _make_git_side_effect(self, commits_output: str, stat_output: str):
        """Returns a side_effect function that alternates between commits and stat."""
        responses = [commits_output, stat_output]
        call_count = {"n": 0}

        def side_effect(args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            result.stdout = responses[call_count["n"] % len(responses)]
            call_count["n"] += 1
            return result

        return side_effect

    def test_happy_path_prints_description(self):
        side_effect = self._make_git_side_effect(
            "Add feature\nFix bug",
            "file.py | 5 +++++",
        )

        with patch("subprocess.run", side_effect=side_effect):
            result = runner.invoke(app, ["--base", "main"])

        assert result.exit_code == 0
        assert "## Resumo" in result.output
        assert "- Add feature" in result.output
        assert "## Arquivos alterados" in result.output

    def test_no_diff_exits_with_code_1(self):
        side_effect = self._make_git_side_effect("", "")

        with patch("subprocess.run", side_effect=side_effect):
            result = runner.invoke(app, ["--base", "main"])

        assert result.exit_code == 1
        assert "Nenhuma diferença encontrada" in result.output

    def test_no_diff_message_contains_base_branch(self):
        side_effect = self._make_git_side_effect("", "")

        with patch("subprocess.run", side_effect=side_effect):
            result = runner.invoke(app, ["--base", "develop"])

        assert "develop" in result.output

    def test_output_flag_writes_file(self, tmp_path):
        output_file = tmp_path / "pr_description.md"
        side_effect = self._make_git_side_effect(
            "My commit",
            "README.md | 2 ++",
        )

        with patch("subprocess.run", side_effect=side_effect):
            result = runner.invoke(app, ["--base", "main", "--output", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "## Resumo" in content
        assert "- My commit" in content

    def test_output_flag_echoes_saved_message(self, tmp_path):
        output_file = tmp_path / "out.md"
        side_effect = self._make_git_side_effect("commit msg", "file.py | 1 +")

        with patch("subprocess.run", side_effect=side_effect):
            result = runner.invoke(app, ["--output", str(output_file)])

        assert f"Descrição salva em {output_file}" in result.output

    def test_default_base_is_main(self):
        captured_args = []

        def side_effect(args, **kwargs):
            captured_args.append(args)
            result = MagicMock()
            result.returncode = 0
            result.stdout = "commit" if "log" in args else "file.py | 1 +"
            return result

        with patch("subprocess.run", side_effect=side_effect):
            runner.invoke(app, [])

        log_call = next(a for a in captured_args if "log" in a)
        assert "main..HEAD" in log_call

    def test_custom_base_branch(self):
        captured_args = []

        def side_effect(args, **kwargs):
            captured_args.append(args)
            result = MagicMock()
            result.returncode = 0
            result.stdout = "commit" if "log" in args else "file.py | 1 +"
            return result

        with patch("subprocess.run", side_effect=side_effect):
            runner.invoke(app, ["--base", "develop"])

        log_call = next(a for a in captured_args if "log" in a)
        assert "develop..HEAD" in log_call

    def test_git_failure_exits_with_code_1(self):
        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_result.stdout = ""
        mock_result.stderr = "fatal: not a git repository"

        with patch("subprocess.run", return_value=mock_result):
            result = runner.invoke(app, [])

        assert result.exit_code == 1

    def test_short_flag_b_for_base(self):
        captured_args = []

        def side_effect(args, **kwargs):
            captured_args.append(args)
            result = MagicMock()
            result.returncode = 0
            result.stdout = "commit" if "log" in args else "file.py | 1 +"
            return result

        with patch("subprocess.run", side_effect=side_effect):
            runner.invoke(app, ["-b", "release"])

        log_call = next(a for a in captured_args if "log" in a)
        assert "release..HEAD" in log_call

    def test_short_flag_o_for_output(self, tmp_path):
        output_file = tmp_path / "out.md"
        side_effect = self._make_git_side_effect("commit msg", "file.py | 1 +")

        with patch("subprocess.run", side_effect=side_effect):
            result = runner.invoke(app, ["-o", str(output_file)])

        assert output_file.exists()
        assert result.exit_code == 0

    def test_whitespace_only_output_treated_as_no_diff(self):
        side_effect = self._make_git_side_effect("   \n  ", "   ")

        with patch("subprocess.run", side_effect=side_effect):
            result = runner.invoke(app, [])

        assert result.exit_code == 1
        assert "Nenhuma diferença encontrada" in result.output
