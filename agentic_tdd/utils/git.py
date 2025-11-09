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
    """Commits staged changes. Returns True if commit succeeded, False if nothing to commit."""
    log_agent_action("Git", f"Committing changes: {message}", str(work_dir))

    # Check if there are any staged changes
    try:
        result = run_command("git diff --cached --quiet", work_dir, log_output=False)
        # If exit code is 0, there are no staged changes
        if result.returncode == 0:
            log_agent_action("Git", "No changes to commit. Skipping commit.", str(work_dir))
            return False
    except Exception:
        # If the check fails, try to commit anyway
        pass

    try:
        _git_command(work_dir, f'commit -m "{message}"')
        log_success(f"Commit successful: {message}")
        return True
    except GitError as e:
        # Check if the error is due to nothing to commit
        if "nothing to commit" in str(e).lower() or "working tree clean" in str(e).lower():
            log_agent_action("Git", "No changes to commit. Working tree is clean.", str(work_dir))
            return False
        # Re-raise if it's a different error
        raise

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
    result = run_command("git diff --cached --quiet", work_dir, log_output=False)
    # git diff --quiet returns 1 if there are differences, 0 if none
    return result.returncode != 0

def has_unstaged_changes(work_dir: Path) -> bool:
    """Checks if there are any unstaged changes."""
    result = run_command("git diff --quiet", work_dir, log_output=False)
    # git diff --quiet returns 1 if there are differences, 0 if none
    return result.returncode != 0

def get_status(work_dir: Path) -> str:
    """Gets the status of the repository."""
    result = _git_command(work_dir, "status -s", log_output=False)
    return result.stdout
