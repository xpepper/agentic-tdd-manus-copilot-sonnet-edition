.PHONY: install fmt lint type test dev-run

# Setup
VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
POETRY := poetry

install:
	@echo "Installing dependencies..."
	@$(POETRY) install

# Code Formatting
fmt:
	@echo "Running Black formatter..."
	@$(POETRY) run black .

# Linting
lint:
	@echo "Running Ruff linter..."
	@$(POETRY) run ruff check . --fix

# Type Checking
type:
	@echo "Running MyPy type checker..."
	@$(POETRY) run mypy .

# Testing (for the tool itself, not the kata)
test:
	@echo "Running Pytest..."
	@$(POETRY) run pytest

# Development Run (Example)
dev-run:
	@echo "Running example TDD cycle (requires a dummy kata file and API key set)..."
	@$(POETRY) run agentic-tdd /path/to/your/kata_rules.md \
		--model gpt-4.1-mini \
		--provider openai \
		--work-dir ./test-kata-run \
		--max-cycles 1
