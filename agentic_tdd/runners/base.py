from pathlib import Path
from typing import Dict, Optional
from abc import ABC, abstractmethod
from agentic_tdd.utils.shell import CommandResult


class BaseRunner(ABC):
    """Abstract base class for language-specific test runners."""

    def __init__(self, work_dir: Path):
        self.work_dir = Path(work_dir)

    @abstractmethod
    def initialize_project(self):
        """Initialize a new project if needed."""
        pass

    @abstractmethod
    def run_tests(self) -> CommandResult:
        """Run tests and return the result."""
        pass

    @abstractmethod
    def _read_files_in_dir(self, directory: str) -> Dict[Path, str]:
        """Read all relevant source files in a directory."""
        pass

    @abstractmethod
    def get_source_code(self) -> Dict[Path, str]:
        """Returns source code files."""
        pass

    @abstractmethod
    def get_test_code(self) -> Dict[Path, str]:
        """Returns test code files."""
        pass

    @abstractmethod
    def get_all_code(self) -> Dict[Path, str]:
        """Returns all code files (source + test)."""
        pass


def get_runner(language: str, work_dir: Path) -> Optional[BaseRunner]:
    """Factory function to get the appropriate runner for a language."""
    language = language.lower()

    if language == "rust":
        from agentic_tdd.runners.rust import RustRunner
        return RustRunner(work_dir)

    # Add more languages here as needed
    # elif language == "python":
    #     from agentic_tdd.runners.python import PythonRunner
    #     return PythonRunner(work_dir)

    return None
