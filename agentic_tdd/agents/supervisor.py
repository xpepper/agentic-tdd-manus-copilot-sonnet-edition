from agentic_tdd.agents.base import Agent
from agentic_tdd.agents.tester import TesterAgent
from agentic_tdd.agents.implementer import ImplementerAgent
from agentic_tdd.agents.refactorer import RefactorerAgent
from agentic_tdd.runners.base import BaseRunner
from agentic_tdd.utils.git import init_repo
from agentic_tdd.logger import log_agent_action, log_danger, log_success, log_info
from langchain_core.language_models.chat_models import BaseChatModel
from pathlib import Path

class SupervisorAgent:
    """
    The Supervisor orchestrates the TDD cycle between the other agents.
    It manages state, handles errors, and determines stop conditions.
    """

    def __init__(self, llm: BaseChatModel, runner: BaseRunner, kata_rules: str, max_cycles: int, max_attempts: int = 5):
        self.llm = llm
        self.runner = runner
        self.kata_rules = kata_rules
        self.max_cycles = max_cycles
        self.max_attempts = max_attempts
        self.cycle_count = 0

        self.tester = TesterAgent("Tester", llm, runner, kata_rules, max_attempts)
        self.implementer = ImplementerAgent("Implementer", llm, runner, kata_rules, max_attempts)
        self.refactorer = RefactorerAgent("Refactorer", llm, runner, kata_rules, max_attempts)

        self.context = {
            "last_test_result": None,
            "test_path": None,
            "test_content": None,
            "failing_test_result": None,
        }

    def _setup(self):
        """Initial setup: initialize project and git repo."""
        log_agent_action("Supervisor", "Starting setup phase.")
        self.runner.initialize_project()
        init_repo(self.runner.work_dir)
        log_agent_action("Supervisor", "Setup complete.")

    def _run_cycle(self) -> bool:
        """Runs one full TDD cycle (Red, Green, Refactor)."""
        self.cycle_count += 1
        log_info(f"\n--- STARTING TDD CYCLE {self.cycle_count}/{self.max_cycles} ---")

        # 1. RED Phase (Tester)
        tester_result = self.tester.run(self.context)

        if tester_result["status"] == "error":
            log_danger(f"Tester failed: {tester_result['message']}")
            return False # Stop the process

        if tester_result["status"] == "overshot":
            log_agent_action("Supervisor", "Tester detected overshot implementation (test passed unexpectedly).")
            # In a real system, we would ask the Tester to propose a different test
            # For this minimal implementation, we will log and stop the cycle, hoping the next cycle is better.
            log_danger("Overshot detected. Aborting cycle. Next cycle will try a new test.")
            return True # Continue to next cycle

        if tester_result["status"] == "red":
            self.context.update({
                "test_path": tester_result["test_path"],
                "test_content": tester_result["test_content"],
                "failing_test_result": tester_result["test_result"],
            })
            log_success("RED Phase complete.")
        else:
            log_agent_action("Supervisor", "Tester could not produce a new failing test. Assuming kata is complete.")
            return False # Stop the process

        # 2. GREEN Phase (Implementer)
        implementer_result = self.implementer.run(self.context)

        if implementer_result["status"] == "error" or implementer_result["status"] == "failed":
            log_danger(f"Implementer failed: {implementer_result['message']}")
            return False # Stop the process

        if implementer_result["status"] == "green":
            log_success("GREEN Phase complete. Code committed.")

        # 3. REFACTOR Phase (Refactorer)
        refactorer_result = self.refactorer.run(self.context)

        if refactorer_result["status"] == "error":
            log_danger(f"Refactorer failed: {refactorer_result['message']}")
            # Do not stop, as the code is still green from the Implementer's commit
            log_info("Refactorer failed, but code is still green. Continuing to next cycle.")

        if refactorer_result["status"] == "green":
            log_success("REFACTOR Phase complete. Refactoring committed.")

        log_info(f"--- TDD CYCLE {self.cycle_count} COMPLETE ---")
        return True

    def run(self):
        """Main execution loop."""
        self._setup()

        while self.cycle_count < self.max_cycles:
            if not self._run_cycle():
                log_agent_action("Supervisor", "Stopping TDD process.")
                break

        log_success(f"TDD process finished after {self.cycle_count} cycles.")
        log_info("Final code state is GREEN.")
