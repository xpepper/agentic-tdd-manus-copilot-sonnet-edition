# Agentic TDD

An AI-powered CLI tool that uses multiple autonomous agents to complete code katas through Test-Driven Development (TDD). The system orchestrates specialized agents (Tester, Implementer, Refactorer) to iteratively build solutions following the Red-Green-Refactor cycle.

## Features

- 🤖 **Multi-Agent Architecture**: Specialized agents for testing, implementation, and refactoring
- 🔄 **Full TDD Cycle**: Automated Red → Green → Refactor workflow
- 🌐 **Multiple LLM Providers**: Support for OpenAI, Perplexity, DeepSeek, iFlow, and other OpenAI-compatible APIs
- 🦀 **Rust Support**: Built-in Cargo integration (extensible to other languages)
- 📝 **Git Integration**: Automatic commits at each TDD phase with meaningful messages
- ⚙️ **Configurable**: Customizable retry attempts, cycles, and working directories

## Installation

### Prerequisites
- Python 3.12+
- Poetry (for dependency management)
- Rust & Cargo (for Rust katas)

### Setup

**Option 1: Using Poetry (Recommended)**

```bash
poetry install
poetry shell
```

**Option 2: Using venv**

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## Usage

### Basic Example

```bash
agentic-tdd mars-rover-kata.md \
  --provider openai \
  --model gpt-4o-mini \
  --work-dir /tmp/mars-rover
```

With iFlow provider:
```bash
agentic_tdd mars-rover-kata.md \
  -p iflow \
  -m qwen3-coder-plus \
  -w /tmp/mars-rover
```

### Command-Line Options

```bash
agentic-tdd [KATA_FILE] [OPTIONS]

Arguments:
  KATA_FILE                Path to the kata markdown file containing the rules

Options:
  -p, --provider TEXT      LLM provider (openai, perplexity, deepseek, iflow) [default: openai]
  -m, --model TEXT         Model name [default: gpt-4o-mini]
  -k, --api-key TEXT       API key (overrides environment variables)
  -w, --work-dir PATH      Working directory for TDD process [default: ./agentic-tdd-kata]
  -l, --language TEXT      Target language (rust) [default: rust]
  --max-cycles INT         Maximum TDD cycles to run [default: 5]
  --max-attempts INT       Maximum retry attempts per agent [default: 5]
  --help                   Show this message and exit
```

### Configuration

#### Environment Variables

Set API keys using environment variables:

```bash
# Provider-specific (recommended)
export OPENAI_API_KEY="your-key"
export PERPLEXITY_API_KEY="your-key"
export DEEPSEEK_API_KEY="your-key"
export IFLOW_API_KEY="your-key"

# Or use generic key
export AGENTIC_TDD_API_KEY="your-key"
```

#### Supported Providers

| Provider | Base URL | Example Model |
|----------|----------|---------------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini`, `gpt-4o` |
| Perplexity | `https://api.perplexity.ai` | `sonar`, `sonar-pro` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat`, `deepseek-coder` |
| iFlow | `https://apis.iflow.cn/v1/` | `qwen3-coder-plus` |

### Example: Mars Rover Kata

```bash
# Using OpenAI
agentic-tdd mars-rover-kata.md \
  -p openai \
  -m gpt-4o-mini \
  -w /tmp/mars-rover \
  --max-cycles 10

# Using iFlow with custom attempts
agentic-tdd mars-rover-kata.md \
  -p iflow \
  -m qwen3-coder-plus \
  -w /tmp/mars-rover \
  --max-attempts 7

# Using Perplexity with API key inline
agentic-tdd kata.md \
  -p perplexity \
  -m sonar-pro \
  -k "your-api-key"
```

## Architecture

### Agent Flow

```
Supervisor
    ↓
1. Tester → Writes failing test (RED)
    ↓
2. Implementer → Makes test pass (GREEN)
    ↓
3. Refactorer → Improves code (GREEN)
    ↓
Repeat cycle until kata complete or max cycles reached
```

### Agents

- **TesterAgent**: Analyzes kata rules and writes failing tests
- **ImplementerAgent**: Makes minimal code changes to pass tests
- **RefactorerAgent**: Improves code quality while maintaining passing tests
- **SupervisorAgent**: Orchestrates the TDD workflow and manages state

## Project Structure

```
agentic-tdd-manus-copilot-sonnet-edition/
├── agentic_tdd/
│   ├── agents/           # Agent implementations
│   │   ├── base.py       # Abstract Agent base class
│   │   ├── tester.py     # Test generation agent
│   │   ├── implementer.py # Implementation agent
│   │   ├── refactorer.py  # Refactoring agent
│   │   └── supervisor.py  # Orchestration agent
│   ├── llm/              # LLM provider integration
│   │   └── provider.py
│   ├── runners/          # Language-specific runners
│   │   ├── base.py
│   │   └── rust.py
│   ├── utils/            # Utilities
│   │   ├── git.py        # Git operations
│   │   └── shell.py      # Shell command execution
│   ├── cli.py            # CLI interface
│   ├── config.py         # Configuration management
│   └── logger.py         # Logging utilities
├── pyproject.toml        # Poetry configuration
└── README.md
```

## Development

### Running Tests

```bash
pytest
```

### Adding a New Language Runner

1. Create a new runner in `agentic_tdd/runners/`:
```python
from agentic_tdd.runners.base import BaseRunner

class PythonRunner(BaseRunner):
    def initialize_project(self):
        # Setup Python project
        pass

    def run_tests(self):
        # Run pytest
        pass
```

2. Register in `runners/base.py`:
```python
def get_runner(language: str, work_dir: Path) -> BaseRunner:
    runners = {
        "rust": RustRunner,
        "python": PythonRunner,  # Add here
    }
```

### Adding a New LLM Provider

Add the provider configuration in `config.py`:

```python
base_urls = {
    "openai": "https://api.openai.com/v1",
    "your-provider": "https://api.your-provider.com/v1",
}
```

## Troubleshooting

### ModuleNotFoundError: No module named 'agentic_tdd'

This happens when the package isn't installed in the active virtual environment. Solutions:

**If using venv:**
```bash
source .venv/bin/activate
pip install -e .
```

**If using Poetry:**
```bash
poetry install
poetry shell
```

Make sure you activate the environment before running the command.

### TypeError: TyperArgument.make_metavar() error

This is a compatibility issue with older Typer versions. Upgrade to fix:
```bash
pip install --upgrade typer
```

### Agent Fails After Multiple Attempts

- Increase `--max-attempts` (e.g., `--max-attempts 10`)
- Try a more capable model
- Check if kata rules are clear and well-defined

### Git Commit Errors

- Ensure working directory has write permissions
- Check that Git is installed and configured

### API Rate Limits

- Reduce `--max-cycles` or `--max-attempts`
- Switch to a provider with higher rate limits
- Add delays between requests (requires code modification)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request
