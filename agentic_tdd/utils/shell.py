import subprocess
from typing import Tuple, Optional
from pathlib import Path
from agentic_tdd.logger import log_command, log_command_output, log_danger

class CommandResult:
    """A simple class to hold the result of a command execution."""
    def __init__(self, command: str, returncode: int, stdout: str, stderr: str):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.success = returncode == 0

def run_command(
    command: str,
    cwd: Path,
    timeout: Optional[int] = 60,
    log_output: bool = True
) -> CommandResult:
    """
    Runs a shell command and returns the result.

    Args:
        command: The command string to execute.
        cwd: The working directory for the command.
        timeout: Maximum time in seconds to wait for the command.
        log_output: Whether to log the command and its output.

    Returns:
        A CommandResult object.
    """
    if log_output:
        log_command(command, str(cwd))

    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8"
        )

        stdout = process.stdout.strip()
        stderr = process.stderr.strip()

        if log_output:
            if stdout:
                log_command_output(f"STDOUT:\n{stdout}")
            if stderr:
                log_command_output(f"STDERR:\n{stderr}")

        return CommandResult(
            command=command,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )

    except subprocess.TimeoutExpired:
        log_danger(f"Command timed out after {timeout} seconds: {command}")
        return CommandResult(
            command=command,
            returncode=124, # Standard timeout exit code
            stdout="",
            stderr=f"Command timed out after {timeout} seconds."
        )
    except Exception as e:
        log_danger(f"An unexpected error occurred while running command: {e}")
        return CommandResult(
            command=command,
            returncode=1,
            stdout="",
            stderr=f"Unexpected error: {e}"
        )
