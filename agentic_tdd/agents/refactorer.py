from agentic_tdd.agents.base import Agent
from agentic_tdd.utils.git import commit, revert_changes, stage_files
from agentic_tdd.logger import log_agent_action, log_danger, log_success
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re

class RefactorerAgent(Agent):
    """
    The Refactorer agent improves design/readability without changing behavior.
    It ensures tests still pass and commits the changes. Reverts on failure.
    """

    def run(self, context: dict) -> dict:
        """
        1. Analyze current code and propose refactoring.
        2. Apply changes to the file system.
        3. Run tests. Revert and retry on failure (max attempts configurable).
        4. Commit the changes.
        """
        log_agent_action(self.name, "Starting TDD cycle: Refactor (GREEN -> GREEN).")

        for attempt in range(1, self.max_attempts + 1):
            log_agent_action(self.name, f"Attempt {attempt}/{self.max_attempts}: Generating refactoring changes.")

            # 1. Analyze and generate changes
            prompt = ChatPromptTemplate.from_messages([
                ("system", self._get_system_prompt() + """
You are the Refactorer. Your task is to improve the design, readability, or structure of the source code without changing its external behavior.
You must ensure all existing tests continue to pass.
You must only output the full content of the file(s) you are modifying, enclosed in a single markdown code block with the file path as the title.
Do NOT output diffs. Output the full, corrected file content.

CURRENT CODE:
{code_context}
"""),
                ("human", "Propose a safe refactoring. Output the full content of the modified file(s). If no refactoring is needed, output: 'NO_REFACTOR_NEEDED'")
            ])

            chain = prompt | self.llm | StrOutputParser()
            response = chain.invoke({
                "code_context": self._get_code_context(self.runner.get_all_code())
            })

            if "NO_REFACTOR_NEEDED" in response.upper():
                log_agent_action(self.name, "No refactoring proposed or needed.")
                return {"status": "skipped", "message": "No refactoring proposed."}

            # 2. Parse and apply changes
            # Try multiple regex patterns to handle different LLM output formats
            file_blocks = re.findall(r"###\s*(?P<path>[^\n]+)\s*\n```rust\n(?P<content>.*?)\n```", response, re.DOTALL)

            # Try alternative formats
            if not file_blocks:
                file_blocks = re.findall(r"(?:^|\n)([^\n]+\.rs)\s*\n```rust\n(.*?)\n```", response, re.DOTALL)

            if not file_blocks:
                file_blocks = re.findall(r"(?:File:|file:)\s*([^\n]+\.rs)\s*\n```(?:rust)?\n(.*?)\n```", response, re.DOTALL | re.IGNORECASE)

            # Try with optional closing fence (handles truncated responses)
            if not file_blocks:
                file_blocks = re.findall(r"###\s*([^\n]+)\s*\n```(?:rust)?\n(.*?)(?:\n```|$)", response, re.DOTALL)

            # Try simple format with optional closing
            if not file_blocks:
                file_blocks = re.findall(r"([^\n]+\.rs)\s*\n```(?:rust)?\n(.*?)(?:\n```|$)", response, re.DOTALL)

            # Last resort: If there's just a code block without a path, assume src/lib.rs
            if not file_blocks:
                code_match = re.search(r"```(?:rust)?\n(.*?)(?:\n```|$)", response, re.DOTALL)
                if code_match:
                    log_agent_action(self.name, "No file path found in LLM response, defaulting to src/lib.rs")
                    file_blocks = [("src/lib.rs", code_match.group(1))]

            if not file_blocks:
                log_danger("Refactorer failed to produce a valid file output format.")
                # Revert any potential partial changes before erroring out
                revert_changes(self.runner.work_dir)
                return {"status": "error", "message": "Invalid output format from Refactorer."}

            modified_files = []
            for path_str, content in file_blocks:
                path_str = path_str.strip()
                content = content.strip()

                file_path = self.runner.work_dir / path_str
                file_path.parent.mkdir(parents=True, exist_ok=True)

                with open(file_path, "w") as f:
                    f.write(content)
                modified_files.append(path_str)
                log_agent_action(self.name, f"Modified file for refactoring: {path_str}")

            # 3. Run tests
            test_result = self.runner.run_tests()

            if test_result.success:
                log_success("Tests still GREEN after refactoring. Refactoring successful.")

                # 4. Stage and Commit
                stage_files(self.runner.work_dir, files=".")
                commit_message = "refactor: Code cleanup and design improvement"
                commit(self.runner.work_dir, commit_message)

                return {"status": "green", "commit_message": commit_message}
            else:
                log_agent_action(self.name, "Tests failed after refactoring (RED). Reverting changes and retrying.")
                revert_changes(self.runner.work_dir)

        log_danger(f"Refactorer failed to maintain GREEN state after {self.max_attempts} attempts. Aborting refactoring for this cycle.")
        return {"status": "failed", "message": "Refactorer failed to maintain GREEN state."}
