import typer
from pathlib import Path
from typing import Optional
from agentic_tdd.config import load_settings
from agentic_tdd.llm.provider import get_llm_client
from agentic_tdd.runners.base import get_runner
from agentic_tdd.agents.supervisor import SupervisorAgent
from agentic_tdd.logger import log_danger, log_info

app = typer.Typer(
    name="agentic-tdd",
    help="Automates multi-agent Test-Driven Development (TDD) for code katas.",
    rich_markup_mode="markdown"
)

@app.command()
def run(
    kata_md_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Path to the kata markdown file containing the rules."
    ),
    model: str = typer.Option(
        "gpt-4.1-mini",
        "--model",
        "-m",
        help="The LLM model to use (e.g., gpt-4.1-mini, sonar-pro)."
    ),
    provider: str = typer.Option(
        "openai",
        "--provider",
        "-p",
        help="The LLM provider (e.g., openai, perplexity, deepseek). Determines API endpoint."
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="API key for the LLM provider. Overrides environment variables."
    ),
    work_dir: Path = typer.Option(
        Path("./agentic-tdd-kata"),
        "--work-dir",
        "-w",
        help="Working directory for the TDD process. A Git repo will be initialized here."
    ),
    max_cycles: int = typer.Option(
        5,
        "--max-cycles",
        help="Maximum number of TDD cycles (Red-Green-Refactor) to run."
    ),
    max_attempts: int = typer.Option(
        5,
        "--max-attempts",
        help="Maximum number of attempts for each agent to produce valid output."
    ),
    language: str = typer.Option(
        "rust",
        "--language",
        "-l",
        help="The target language for the kata. Currently only 'rust' is supported."
    )
):
    """
    Starts the multi-agent TDD process for a given code kata.
    """

    try:
        # 1. Load and validate settings
        settings = load_settings(
            kata_md_path=kata_md_path,
            work_dir=work_dir,
            model=model,
            provider=provider,
            api_key=api_key,
            max_cycles=max_cycles
        )

        # Ensure work directory exists
        settings.work_dir.mkdir(parents=True, exist_ok=True)

        log_info(f"Configuration loaded. Work directory: {settings.work_dir}")
        log_info(f"LLM: {settings.model_name} via {settings.provider_name}")

        # 2. Read Kata Rules
        kata_rules = settings.kata_md_path.read_text()

        # 3. Initialize LLM Client
        llm_client = get_llm_client(settings)

        # 4. Initialize Language Runner
        runner = get_runner(language, settings.work_dir)

        # 5. Initialize and Run Supervisor
        supervisor = SupervisorAgent(
            llm=llm_client,
            runner=runner,
            kata_rules=kata_rules,
            max_cycles=settings.max_cycles,
            max_attempts=max_attempts
        )

        supervisor.run()

    except ValueError as e:
        log_danger(f"Configuration Error: {e}")
        raise typer.Exit(code=1)
    except NotImplementedError as e:
        log_danger(f"Language Runner Error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        import traceback
        log_danger(f"An unexpected error occurred: {e}")
        traceback.print_exc()
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
