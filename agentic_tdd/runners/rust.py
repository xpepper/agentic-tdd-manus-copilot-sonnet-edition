import os
from pathlib import Path
from typing import Dict, List
from agentic_tdd.runners.base import BaseRunner
from agentic_tdd.utils.shell import run_command, CommandResult
from agentic_tdd.logger import log_agent_action, log_danger

class RustRunner(BaseRunner):
    """Runner for Rust projects using Cargo."""

    def initialize_project(self):
        """Initializes a new Rust library project if `Cargo.toml` is missing."""
        if not (self.work_dir / "Cargo.toml").exists():
            log_agent_action("RustRunner", "Initializing new Rust library project.", str(self.work_dir))
            # Use `cargo init --lib` to create a library project
            result = run_command("cargo init --lib", self.work_dir)
            if not result.success:
                log_danger(f"Failed to initialize Rust project: {result.stderr}")
                raise Exception("Rust project initialization failed.")
            log_agent_action("RustRunner", "Project initialized successfully.")
        else:
            log_agent_action("RustRunner", "Rust project already initialized.")

    def run_tests(self) -> CommandResult:
        """Executes `cargo test`."""
        log_agent_action("RustRunner", "Running tests with `cargo test`.")
        # Use --no-fail-fast to get all test results
        return run_command("cargo test --no-fail-fast", self.work_dir, timeout=120)

    def _read_files_in_dir(self, directory: str) -> Dict[Path, str]:
        """Helper to read all .rs files in a given subdirectory."""
        code_files = {}
        target_dir = self.work_dir / directory
        if target_dir.exists():
            for file_path in target_dir.rglob("*.rs"):
                # Ensure the path is relative to the work_dir for context
                relative_path = file_path.relative_to(self.work_dir)
                try:
                    with open(file_path, 'r') as f:
                        code_files[relative_path] = f.read()
                except Exception as e:
                    log_danger(f"Could not read file {relative_path}: {e}")
        return code_files

    def get_source_code(self) -> Dict[Path, str]:
        """Returns source code from the `src` directory."""
        return self._read_files_in_dir("src")

    def get_test_code(self) -> Dict[Path, str]:
        """Returns test code from the `tests` directory."""
        # Rust tests can be in `src` or `tests`. We'll focus on `tests` for external tests
        # and rely on the LLM to understand the context of `src/lib.rs` for inline tests.
        # For simplicity in M1, we'll just return the contents of `src` and let the agent figure it out.
        # A more robust solution would parse `Cargo.toml` and the files themselves.
        # For now, we return all .rs files in src and tests.
        return self._read_files_in_dir("tests")

    def get_all_code(self) -> Dict[Path, str]:
        """Returns a dictionary of all relevant code (source + test)."""
        # In Rust, the distinction is often blurred. We'll provide all .rs files.
        src_code = self.get_source_code()
        test_code = self.get_test_code()
        return {**src_code, **test_code}
