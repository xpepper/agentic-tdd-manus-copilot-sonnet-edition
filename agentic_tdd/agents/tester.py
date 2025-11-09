from agentic_tdd.agents.base import Agent
from agentic_tdd.utils.git import stage_files, get_status
from agentic_tdd.logger import log_agent_action, log_danger, log_success
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pathlib import Path
import re

class TesterAgent(Agent):
    """
    The Tester agent writes a new failing unit test based on the kata rules.
    It verifies the test fails and stages the test file.
    """

    def run(self, context: dict) -> dict:
        """
        1. Generate a new failing test.
        2. Write the test to the file system.
        3. Run tests to confirm RED state.
        4. Stage the new test file.
        """
        log_agent_action(self.name, "Starting TDD cycle: Write a new failing test.")

        # Get crate name from work directory
        crate_name = self.runner.work_dir.name

        # 1. Generate a new failing test
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt() + f"""
You are the Tester. Your task is to propose the smallest, next logical unit test that WILL FAIL based on the KATA RULES.

CRITICAL RULES:
1. Write ONLY a test file - DO NOT include any implementation code
2. The test MUST call functions/types that don't exist yet in src/ (so it will fail to compile)
3. DO NOT write helper functions or implementations in the test file
4. Import from the crate using: use {crate_name}::{{{{TypeName, function_name}}}};
5. The test file goes in the `tests/` directory (e.g., `tests/test_feature_name.rs`)

Output format:
### tests/test_name.rs
```rust
use {crate_name}::{{{{StructName, function_name}}}};  // These don't exist yet - test will fail

#[test]
fn it_should_do_something() {{{{
    // Call non-existent functions - this will fail
    let result = function_name();
    assert_eq!(result, expected_value);
}}}}
```

CURRENT CODE:
{{{{code_context}}}}

LAST TEST RESULT (if any):
{{{{last_test_result}}}}
"""),
            ("human", "Generate the next failing test file content and path. Remember: ONLY the test, NO implementation code.")
        ])

        chain = prompt | self.llm | StrOutputParser()

        code_context = self._get_code_context(self.runner.get_all_code())

        response = chain.invoke({
            "code_context": code_context,
            "last_test_result": context.get("last_test_result", "No previous test result.")
        })

        # 2. Parse and write the test file
        match = re.search(r"###\s*(?P<path>[^\n]+)\s*\n```rust\n(?P<content>.*?)\n```", response, re.DOTALL)

        if not match:
            log_danger("Tester failed to produce a valid test file output format.")
            return {"status": "error", "message": "Invalid output format from Tester."}

        test_path_str = match.group("path").strip()
        test_content = match.group("content").strip()

        if not test_path_str.startswith("tests/"):
            log_danger(f"Tester proposed an invalid test path: {test_path_str}. Must be in `tests/`.")
            return {"status": "error", "message": "Invalid test path from Tester."}

        test_path = self.runner.work_dir / test_path_str
        test_path.parent.mkdir(parents=True, exist_ok=True)

        with open(test_path, "w") as f:
            f.write(test_content)

        log_agent_action(self.name, f"Wrote new test file: {test_path_str}", "Content written to disk.")

        # 3. Run tests to confirm RED state
        test_result = self.runner.run_tests()

        if test_result.success:
            log_danger("Test unexpectedly passed (GREEN). Implementer may have overshot.")
            # The Supervisor will handle this state
            return {
                "status": "overshot",
                "test_path": test_path_str,
                "test_content": test_content,
                "test_result": test_result
            }

        log_success("Test confirmed to be failing (RED). Proceeding to Implementer.")

        # 4. Stage the new test file
        stage_files(self.runner.work_dir, files=test_path_str)

        return {
            "status": "red",
            "test_path": test_path_str,
            "test_content": test_content,
            "test_result": test_result
        }
