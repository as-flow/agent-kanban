import shutil
from unittest.mock import patch

from process_env import git_pull_argv, git_subprocess_env


def test_git_subprocess_env_disables_terminal_prompt():
    env = git_subprocess_env()
    assert env["GIT_TERMINAL_PROMPT"] == "0"


def test_git_pull_argv_without_gh():
    with patch("process_env._GH_PATH", None):
        assert git_pull_argv() == ["git", "pull"]


def test_git_pull_argv_with_gh():
    with patch("process_env._GH_PATH", "/usr/bin/gh"):
        assert git_pull_argv() == [
            "git",
            "-c", "credential.helper=",
            "-c", "credential.helper=!gh auth git-credential",
            "pull",
        ]


def test_git_pull_argv_uses_detected_gh_when_present():
    if shutil.which("gh"):
        argv = git_pull_argv()
        assert any("gh auth git-credential" in arg for arg in argv)
    else:
        assert git_pull_argv() == ["git", "pull"]
