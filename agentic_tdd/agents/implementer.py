from agentic_tdd.agents.base import Agent
from agentic_tdd.utils.git import stage_files, commit, get_diff
from agentic_tdd.logger import log_agent_action, log_danger, log_success
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pathlib import Path
import re

class ImplementerAgent(Agent):
    """
    The Implementer agent makes the minimal change to make the failing test pass.
    It runs tests until green and then commits the changes.
    """

    def run(self, context: dict) -> dict:
        """
        1. Analyze the failing test result.
        2. Generate minimal code changes.
        3. Apply changes to the file system.
        4. Run tests until GREEN (max attempts configurable).
        5. Commit the changes.
        """
        log_agent_action(self.name, "Starting TDD cycle: Make the test pass (RED -> GREEN).")

        failing_test_result = context["failing_test_result"]

        for attempt in range(1, self.max_attempts + 1):
            log_agent_action(self.name, f"Attempt {attempt}/{self.max_attempts}: Generating implementation code.")

            # 1. Analyze and generate changes
            prompt = ChatPromptTemplate.from_messages([
                ("system", self._get_system_prompt() + """
You are the Implementer. Your task is to make the minimal change to the source code to make the failing test pass.

CRITICAL RULES:
1. Only modify source code in the `src/` directory (e.g., src/lib.rs)
2. DO NOT include any `#[cfg(test)]` or test modules in your implementation
3. DO NOT include example/default tests like `fn it_works()` or `fn add()`
4. Only write the public API (functions, structs, enums) needed for the external tests to pass
5. Output the full file content in a markdown code block

CURRENT CODE:
{code_context}

LAST FAILING TEST OUTPUT:
{test_output}

Remember: Write ONLY production code, NO test code or test modules.
"""),
                ("human", "Generate the full content of src/lib.rs to make the test pass. NO TEST CODE.")
            ])

            chain = prompt | self.llm | StrOutputParser()
            response = chain.invoke({
                "code_context": self._get_code_context(self.runner.get_source_code()),
                "test_output": f"{failing_test_result.stdout}\n{failing_test_result.stderr}"
            })

            # 2. Parse and apply changes
            # Try multiple regex patterns to handle different LLM output formats
            file_blocks = re.findall(r"###\s*(?P<path>[^\n]+)\s*\n```rust\n(?P<content>.*?)\n```", response, re.DOTALL)

            # Try alternative format: path on its own line, then code block
            if not file_blocks:
                file_blocks = re.findall(r"(?:^|\n)(src/[^\n]+\.rs)\s*\n```rust\n(.*?)\n```", response, re.DOTALL)

            # Try alternative format: File: path followed by code block
            if not file_blocks:
                file_blocks = re.findall(r"(?:File:|file:)\s*(src/[^\n]+\.rs)\s*\n```(?:rust)?\n(.*?)\n```", response, re.DOTALL | re.IGNORECASE)

            # Try with optional closing fence (handles truncated responses)
            if not file_blocks:
                file_blocks = re.findall(r"###\s*([^\n]+)\s*\n```(?:rust)?\n(.*?)(?:\n```|$)", response, re.DOTALL)

            # Try simple format: src/file.rs followed by code block (optional closing)
            if not file_blocks:
                file_blocks = re.findall(r"(src/[^\n]+\.rs)\s*\n```(?:rust)?\n(.*?)(?:\n```|$)", response, re.DOTALL)

            # Last resort: If there's just a code block without a path, assume src/lib.rs
            if not file_blocks:
                code_match = re.search(r"```(?:rust)?\n(.*?)(?:\n```|$)", response, re.DOTALL)
                if code_match:
                    log_agent_action(self.name, "No file path found in LLM response, defaulting to src/lib.rs")
                    file_blocks = [("src/lib.rs", code_match.group(1))]

            if not file_blocks:
                log_danger("Implementer failed to produce a valid file output format.")
                log_danger(f"LLM Response length: {len(response)} chars")
                log_danger(f"LLM Response (last 300 chars):\n...{response[-300:]}")
                return {"status": "error", "message": "Invalid output format from Implementer."}

            modified_files = []
            for path_str, content in file_blocks:
                path_str = path_str.strip()
                content = content.strip()

                if not path_str.startswith("src/"):
                    log_danger(f"Implementer attempted to modify a non-source file: {path_str}. Only `src/` is allowed.")
                    continue

                file_path = self.runner.work_dir / path_str
                file_path.parent.mkdir(parents=True, exist_ok=True)

                with open(file_path, "w") as f:
                    f.write(content)
                modified_files.append(path_str)
                log_agent_action(self.name, f"Modified source file: {path_str}")

            if not modified_files:
                log_danger("Implementer failed to make any valid modifications.")
                return {"status": "error", "message": "No valid source file modifications made."}

            # 3. Run tests
            test_result = self.runner.run_tests()

            if test_result.success:
                log_success("Tests are now GREEN. Implementation successful.")

                # 4. Stage and Commit
                stage_files(self.runner.work_dir, files=".") # Stage all modified files (test + source)
                commit_message = f"feat: Implement code to pass new test for {context['test_path']}"
                commit(self.runner.work_dir, commit_message)

                return {"status": "green", "commit_message": commit_message}
            else:
                log_agent_action(self.name, f"Tests still failing (RED). Retrying. Output:\n{test_result.stderr}")
                failing_test_result = test_result # Update context for next attempt

        log_danger(f"Implementer failed to make tests pass after {self.max_attempts} attempts.")
        return {"status": "failed", "message": "Implementer failed to achieve GREEN state."}
