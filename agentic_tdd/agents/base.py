from abc import ABC, abstractmethod
from langchain_core.language_models.chat_models import BaseChatModel
from pathlib import Path
from typing import Dict


class Agent(ABC):
    """Abstract base class for all TDD agents."""

    def __init__(self, name: str, llm: BaseChatModel, runner, kata_rules: str, max_attempts: int = 5):
        self.name = name
        self.llm = llm
        self.runner = runner
        self.kata_rules = kata_rules
        self.max_attempts = max_attempts
        self.work_dir = runner.work_dir

    @abstractmethod
    def run(self, context: dict) -> dict:
        """Execute the agent's task and return updated context."""
        pass

    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        # Escape curly braces in kata rules so LangChain doesn't treat them as template variables
        escaped_kata_rules = self.kata_rules.replace('{', '{{').replace('}', '}}')
        return f"""You are the {self.name} agent in a TDD workflow.

KATA RULES:
{escaped_kata_rules}

Follow these rules strictly when generating code and tests."""

    def _get_code_context(self, files: Dict[Path, str]) -> str:
        """Format code files into a readable context string for the LLM."""
        if not files:
            return "No code files present yet."

        context_parts = []
        for file_path, content in files.items():
            context_parts.append(f"### {file_path}")
            context_parts.append(f"```rust\n{content}\n```")

        return "\n\n".join(context_parts)
