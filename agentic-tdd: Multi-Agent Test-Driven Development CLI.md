# agentic-tdd: Multi-Agent Test-Driven Development CLI

**`agentic-tdd`** is a minimal, production-quality Python CLI tool that automates the Test-Driven Development (TDD) cycle for code katas using a team of specialized AI agents. It orchestrates a strict Red-Green-Refactor loop, starting with Rust projects.

## Quickstart

This tool requires Python 3.11+, `git`, and the Rust toolchain (`cargo`) to be installed on your system.

1. **Clone the repository and install dependencies:**

   ```bash
   git clone <repo-url>
   cd agentic-tdd
   poetry install
   ```

2. **Create a dummy kata rules file** (e.g., `mars_rover_rules.md`):

   ```markdown
   # Mars Rover Kata Rules
   
   The goal is to implement a Mars Rover that accepts commands.
   Initial state: (0, 0, N) - North.
   Command 'M' moves one step forward.
   Command 'R' turns right.
   Command 'L' turns left.
   ...
   ```

3. **Run the TDD process:**

   The tool uses an OpenAI-compatible API. Set your API key as an environment variable or pass it via the `--api-key` flag.

   ```bash
   poetry run agentic-tdd mars_rover_rules.md \
     --model gpt-4.1-mini \
     --provider openai \
     --api-key $OPENAI_API_KEY \
     --work-dir ./mars-rover-kata \
     --max-cycles 5
   ```

   This command will:
   1. Create the `./mars-rover-kata` directory.
   2. Initialize a Git repository and a Rust project (`cargo init`).
   3. Run the TDD cycle 5 times, with agents committing changes only when tests are green.

## Agent Architecture

The system is built around four specialized agents orchestrated by the **Supervisor**:

| Agent | Role | TDD Phase | Commit Policy |
| :--- | :--- | :--- | :--- |
| **Tester** | Writes the next **failing** unit test based on the kata rules. | **RED** | Stages the new test file. |
| **Implementer** | Makes the **minimal** change to the source code to make the failing test pass. | **GREEN** | Commits staged test and source code (`feat:` commit). |
| **Refactorer** | Improves code design, readability, and structure without changing behavior. | **REFACTOR** | Commits refactoring changes (`refactor:` commit). |
| **Supervisor** | Orchestrates the Red-Green-Refactor cycles, manages state, and handles errors. | Orchestration | None (manages other agents' commits). |

## LLM Compatibility

The tool is designed to be provider-agnostic, relying on the **OpenAI API specification** for chat completions. This allows for easy switching between various LLM providers.

| Provider | Recommended Model | Typical Base URL | Recommended Env Var | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **OpenAI** | `gpt-4.1-mini`, `gpt-4-turbo` | `https://api.openai.com/v1` | `OPENAI_API_KEY` | The standard, highly reliable for code generation and reasoning. |
| **Perplexity** | `sonar-pro`, `sonar-small` | `https://api.perplexity.ai` | `PERPLEXITY_API_KEY` | Excellent for reasoning; often faster and cheaper than GPT-4. |
| **DeepSeek** | `deepseek-coder` | `https://api.deepseek.com/v1` | `DEEPSEEK_API_KEY` | Specialized in coding tasks; a strong alternative for implementation. |
| **Local/Other** | Varies | Varies | `AGENTIC_TDD_API_KEY` | Use with local servers (e.g., LiteLLM, Ollama) that expose an OpenAI-compatible endpoint. |

## Backlog (TODO)

This is a minimal working implementation (M1). Future development should focus on robustness, efficiency, and extensibility.

- [ ] **Multi-Language Support:** Implement runners for Python (`pytest`), JavaScript (`jest`), and Go.
- [ ] **Cost Control:** Implement token counting and budget limits for the LLM calls.
- [ ] **Improved Error Handling:** More sophisticated handling for stuck states (e.g., Implementer failing to pass tests after 3 tries).
- [ ] **Prompt Optimization:** Refine agent prompts to reduce token usage and improve code quality.
- [ ] **File Management:** Allow agents to propose new files or delete existing ones (currently restricted to modifying existing or creating new test files).
- [ ] **Interactive Mode:** Add a flag to pause the process and allow the user to inspect or modify the code manually.
