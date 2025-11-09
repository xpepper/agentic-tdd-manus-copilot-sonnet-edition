import os
from pathlib import Path
from typing import Optional
from agentic_tdd.logger import log_agent_action, log_danger, log_success
from agentic_tdd.utils.shell import run_command, CommandResult

class GitError(Exception):
    """Custom exception for Git operations."""
    pass

def _git_command(
    work_dir: Path,
    args: str,
    log_output: bool = True
) -> CommandResult:
    """Internal helper to run a git command."""
    command = f"git {args}"
    result = run_command(command, work_dir, log_output=log_output)
    if not result.success:
        log_danger(f"Git command failed: {command}")
        log_danger(result.stderr)
        raise GitError(f"Git command failed: {result.stderr}")
    return result

def init_repo(work_dir: Path):
    """Initializes a new Git repository in the working directory."""
    if (work_dir / ".git").exists():
        log_agent_action("Git", "Repository already initialized.", str(work_dir))
        return

    log_agent_action("Git", "Initializing new Git repository.", str(work_dir))
    _git_command(work_dir, "init -b main")
    log_success("Git repository initialized.")

def stage_files(work_dir: Path, files: str = "."):
    """Stages files for commit."""
    log_agent_action("Git", f"Staging files: {files}", str(work_dir))
    _git_command(work_dir, f"add {files}")
    log_success("Files staged.")

def commit(work_dir: Path, message: str):
    """Commits staged changes."""
    log_agent_action("Git", f"Committing changes: {message}", str(work_dir))
    _git_command(work_dir, f'commit -m "{message}"')
    log_success(f"Commit successful: {message}")

def revert_changes(work_dir: Path, files: str = "."):
    """Reverts unstaged and staged changes in files."""
    log_agent_action("Git", f"Reverting changes in: {files}", str(work_dir))
    # Unstage changes
    _git_command(work_dir, f"reset HEAD -- {files}", log_output=False)
    # Discard unstaged changes
    _git_command(work_dir, f"checkout -- {files}")
    log_success("Changes reverted.")

def get_diff(work_dir: Path, cached: bool = False) -> str:
    """Gets the diff of staged or unstaged changes."""
    args = "diff --cached" if cached else "diff"
    result = _git_command(work_dir, args, log_output=False)
    return result.stdout

def has_staged_changes(work_dir: Path) -> bool:
    """Checks if there are any staged changes."""
    result = _git_command(work_dir, "diff --cached --quiet", log_output=False)
    return result.returncode != 0

def has_unstaged_changes(work_dir: Path) -> bool:
    """Checks if there are any unstaged changes."""
    result = _git_command(work_dir, "diff --quiet", log_output=False)
    return result.returncode != 0

def get_status(work_dir: Path) -> str:
    """Gets the status of the repository."""
    result = _git_command(work_dir, "status -s", log_output=False)
    return result.stdout
