import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Settings(BaseModel):
    """Application settings loaded from environment variables and CLI."""

    # Core CLI arguments
    kata_md_path: Path = Field(..., description="Path to the kata markdown file.")
    work_dir: Path = Field(..., description="Working directory for the TDD process.")
    max_cycles: int = Field(5, description="Maximum number of TDD cycles to run.")

    # LLM Configuration
    model_name: str = Field("gpt-4.1-mini", description="The LLM model to use.")
    provider_name: str = Field("openai", description="The LLM provider (e.g., openai, perplexity).")
    api_key: Optional[str] = Field(None, description="API key for the LLM provider.")
    base_url: Optional[str] = Field(None, description="Base URL for the OpenAI-compatible API.")

    class Config:
        env_prefix = 'AGENTIC_TDD_'
        case_sensitive = False

def get_llm_config(provider: str) -> tuple[Optional[str], Optional[str]]:
    """
    Determines the base_url and api_key based on the provider name.
    This implements the priority: CLI --api-key > provider-specific env var > generic AGENTIC_TDD_API_KEY.
    """

    # 1. Provider-specific environment variable (e.g., OPENAI_API_KEY)
    provider_env_key = f"{provider.upper()}_API_KEY"
    env_api_key = os.getenv(provider_env_key)

    # 2. Generic AGENTIC_TDD_API_KEY (handled by Pydantic's env_prefix)
    generic_api_key = os.getenv("AGENTIC_TDD_API_KEY")

    # Determine the base URL based on common providers
    base_urls = {
        "openai": "https://api.openai.com/v1",
        "perplexity": "https://api.perplexity.ai",
        "deepseek": "https://api.deepseek.com/v1",
        "iflow": "https://apis.iflow.cn/v1/",
        # Add more providers here
    }

    base_url = base_urls.get(provider.lower())

    return base_url, env_api_key or generic_api_key

def load_settings(
    kata_md_path: Path,
    work_dir: Path,
    model: str,
    provider: str,
    api_key: Optional[str],
    max_cycles: int
) -> Settings:
    """Loads and validates settings, merging CLI args with environment variables."""

    # Get base URL and potential API key from provider-specific logic
    base_url, env_api_key = get_llm_config(provider)

    # CLI-provided API key takes highest precedence
    final_api_key = api_key or env_api_key

    if not final_api_key:
        raise ValueError(f"API key not found. Please provide it via --api-key or set a relevant environment variable (e.g., {provider.upper()}_API_KEY or AGENTIC_TDD_API_KEY).")

    # Create the settings object
    settings = Settings(
        kata_md_path=kata_md_path,
        work_dir=work_dir,
        model_name=model,
        provider_name=provider,
        api_key=final_api_key,
        base_url=base_url,
        max_cycles=max_cycles
    )

    return settings
